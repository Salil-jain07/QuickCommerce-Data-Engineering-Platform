from backend.config.config import GCS_BUCKET_NAME

import duckdb
from fsspec import filesystem
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
OUTPUT_DIR = PROJECT_ROOT / "datasets" / "processed" / "silver"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

gcs = filesystem("gcs", token="google_default")

con = duckdb.connect("quickcommerce.duckdb")
con.register_filesystem(gcs)

source_path = (
    f"gcs://{GCS_BUCKET_NAME}/bronze/generated/orders/*.parquet"
)

con.execute(f"""
    CREATE OR REPLACE TABLE bronze_orders AS
    SELECT *
    FROM read_parquet('{source_path}')
""")

total_rows = con.execute("""
    SELECT COUNT(*) FROM bronze_orders
""").fetchone()[0]

duplicate_ids = con.execute("""
    SELECT COUNT(*)
    FROM (
        SELECT order_id
        FROM bronze_orders
        GROUP BY order_id
        HAVING COUNT(*) > 1
    )
""").fetchone()[0]

missing_values = con.execute("""
    SELECT COUNT(*)
    FROM bronze_orders
    WHERE order_id IS NULL
       OR customer_id IS NULL
       OR store_id IS NULL
       OR platform IS NULL
       OR city IS NULL
       OR order_datetime IS NULL
       OR payment_method IS NULL
       OR order_status IS NULL
""").fetchone()[0]

invalid_status = con.execute("""
    SELECT COUNT(*)
    FROM bronze_orders
    WHERE order_status NOT IN ('Delivered', 'Cancelled', 'Processing')
""").fetchone()[0]

print("ORDER DATA QUALITY REPORT")
print("Total rows:", total_rows)
print("Duplicate order IDs:", duplicate_ids)
print("Rows with missing values:", missing_values)
print("Invalid order statuses:", invalid_status)

con.execute("""
    CREATE OR REPLACE TABLE silver_orders AS
    SELECT
        TRIM(order_id) AS order_id,
        TRIM(customer_id) AS customer_id,
        TRIM(store_id) AS store_id,
        TRIM(platform) AS platform,
        TRIM(city) AS city,
        CAST(order_datetime AS TIMESTAMP) AS order_datetime,
        TRIM(payment_method) AS payment_method,
        TRIM(order_status) AS order_status,
        TRIM(data_origin) AS data_origin
    FROM bronze_orders
    QUALIFY ROW_NUMBER() OVER (
        PARTITION BY order_id
        ORDER BY order_datetime DESC
    ) = 1
""")

local_file = OUTPUT_DIR / "orders.parquet"

con.execute(f"""
    COPY silver_orders    TO '{local_file.as_posix()}'
    (FORMAT PARQUET, COMPRESSION ZSTD)
""")

silver_rows = con.execute("""
    SELECT COUNT(*) FROM silver_orders""").fetchone()[0]

print("\nSILVER ORDER DATA")
print("Rows:", silver_rows)
print("Local file:", local_file)

gcs.put(
    str(local_file),
    f"{GCS_BUCKET_NAME}/silver/orders/orders.parquet"
)

print("\nUploaded to GCS: silver/orders/orders.parquet")

con.close()
