
import traceback
import duckdb
from fsspec import filesystem
from pathlib import Path
from backend.config.config import GCS_BUCKET_NAME

PROJECT_ROOT = Path(__file__).resolve().parents[2]
OUTPUT_DIR = PROJECT_ROOT / "datasets" / "processed" / "silver"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

con = None

try:
    gcs = filesystem("gcs", token="google_default")
    con = duckdb.connect("quickcommerce.duckdb")
    con.register_filesystem(gcs)

    print("Reading Bronze Deliveries from GCS...")

    con.execute(f"""
    CREATE OR REPLACE VIEW bronze_deliveries AS
    SELECT *
    FROM read_parquet(
        'gcs://{GCS_BUCKET_NAME}/bronze/generated/deliveries/*.parquet'
    )
    """)

    total_rows = con.execute("""
    SELECT COUNT(*) FROM bronze_deliveries
    """).fetchone()[0]

    duplicate_ids = con.execute("""
    SELECT COUNT(*)
    FROM (
        SELECT delivery_id
        FROM bronze_deliveries
        GROUP BY delivery_id
        HAVING COUNT(*) > 1
    )
    """).fetchone()[0]

    missing_values = con.execute("""
    SELECT COUNT(*)
    FROM bronze_deliveries
    WHERE delivery_id IS NULL
       OR order_id IS NULL
       OR delivery_partner_id IS NULL
       OR distance_km IS NULL
       OR weather_condition IS NULL
       OR traffic_condition IS NULL
       OR vehicle_type IS NULL
       OR estimated_delivery_datetime IS NULL
       OR delivery_status IS NULL
       OR data_origin IS NULL
    """).fetchone()[0]

    invalid_distances = con.execute("""
    SELECT COUNT(*)
    FROM bronze_deliveries
    WHERE distance_km <= 0
    """).fetchone()[0]

    invalid_durations = con.execute("""
    SELECT COUNT(*)
    FROM bronze_deliveries
    WHERE delivery_duration_minutes < 0
    """).fetchone()[0]

    print("\nDELIVERY DATA QUALITY REPORT")
    print("Total rows:", total_rows)
    print("Duplicate delivery IDs:", duplicate_ids)
    print("Rows with missing required values:", missing_values)
    print("Invalid distances:", invalid_distances)
    print("Invalid durations:", invalid_durations)

    print("\nDelivery status distribution:")

    statuses = con.execute("""
    SELECT delivery_status, COUNT(*)
    FROM bronze_deliveries
    GROUP BY delivery_status
    ORDER BY COUNT(*) DESC
    """).fetchall()

    for status, count in statuses:
        print(status, count)

    print("\nCreating Silver Deliveries...")

    con.execute("""
    CREATE OR REPLACE TABLE silver_deliveries AS
    SELECT
        TRIM(delivery_id) AS delivery_id,
        TRIM(order_id) AS order_id,
        TRIM(delivery_partner_id) AS delivery_partner_id,
        distance_km,
        TRIM(weather_condition) AS weather_condition,
        TRIM(traffic_condition) AS traffic_condition,
        TRIM(vehicle_type) AS vehicle_type,
        CAST(estimated_delivery_datetime AS TIMESTAMP) AS estimated_delivery_datetime,
        CAST(actual_delivery_datetime AS TIMESTAMP) AS actual_delivery_datetime,
        delivery_duration_minutes,
        TRIM(delivery_status) AS delivery_status,
        TRIM(data_origin) AS data_origin
    FROM bronze_deliveries
    QUALIFY ROW_NUMBER() OVER (
        PARTITION BY delivery_id
        ORDER BY estimated_delivery_datetime DESC
    ) = 1
    """)

    silver_count = con.execute("""
    SELECT COUNT(*) FROM silver_deliveries
    """).fetchone()[0]

    print("\nSILVER DELIVERIES")
    print("Rows:", silver_count)

    output_file = OUTPUT_DIR / "deliveries.parquet"

    con.execute(f"""
    COPY silver_deliveries
    TO '{output_file.as_posix()}'
    (FORMAT PARQUET, COMPRESSION ZSTD)
    """)

    print("Local file:", output_file)

    gcs.put(
        str(output_file),
        f"{GCS_BUCKET_NAME}/silver/deliveries/deliveries.parquet"
    )

    print("Uploaded to GCS: silver/deliveries/deliveries.parquet")

except Exception:
    print("\nDELIVERIES TRANSFORMATION FAILED")
    traceback.print_exc()
    raise
finally:
    if con is not None:
        con.close()
