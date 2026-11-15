
import duckdb
from pathlib import Path
from fsspec import filesystem
from backend.config.config import GCS_BUCKET_NAME

PROJECT_ROOT = Path(__file__).resolve().parents[2]
GOLD_DIR = PROJECT_ROOT / "datasets" / "processed" / "gold"
GOLD_DIR.mkdir(parents=True, exist_ok=True)

con = duckdb.connect("quickcommerce.duckdb")

try:
    print("Reading Gold Order Summary...")

    con.execute(f"""
    CREATE OR REPLACE VIEW src_gold_orders AS
    SELECT *
    FROM read_parquet(
        '{(GOLD_DIR / "gold_order_summary.parquet").as_posix()}'
    )
    """)

    print("Creating Gold Delivery Summary...")

    con.execute("""
    CREATE OR REPLACE TABLE gold_delivery_summary AS
    SELECT
        CAST(order_datetime AS DATE) AS delivery_date,
        platform,
        city,
        traffic_condition,
        weather_condition,
        vehicle_type,
        COUNT(*) AS total_orders,
        COUNT(*) FILTER (
            WHERE delivery_status = 'Delivered'
        ) AS delivered_orders,
        COUNT(*) FILTER (
            WHERE delivery_duration_minutes IS NOT NULL
        ) AS completed_deliveries,
        ROUND(AVG(delivery_duration_minutes), 2) AS average_delivery_minutes,
        ROUND(AVG(distance_km), 2) AS average_distance_km
    FROM src_gold_orders
    WHERE delivery_status IS NOT NULL
    GROUP BY
        CAST(order_datetime AS DATE),
        platform,
        city,
        traffic_condition,
        weather_condition,
        vehicle_type
    """)

    total_rows = con.execute("""
    SELECT COUNT(*) FROM gold_delivery_summary
    """).fetchone()[0]

    print("\nGOLD DELIVERY SUMMARY")
    print("Total rows:", total_rows)

    print("\nSample records:")

    records = con.execute("""
    SELECT *
    FROM gold_delivery_summary
    LIMIT 5
    """).fetchall()

    for record in records:
        print(record)

    output_file = GOLD_DIR / "gold_delivery_summary.parquet"

    con.execute(f"""
    COPY gold_delivery_summary
    TO '{output_file.as_posix()}'
    (FORMAT PARQUET, COMPRESSION ZSTD)
    """)

    print("\nLocal file:", output_file)

    gcs = filesystem("gcs", token="google_default")

    gcs.put(
        str(output_file),
        f"{GCS_BUCKET_NAME}/gold/gold_delivery_summary.parquet"
    )

    print("Uploaded to GCS: gold/gold_delivery_summary.parquet")

except Exception:
    import traceback
    traceback.print_exc()
    raise
finally:
    con.close()
