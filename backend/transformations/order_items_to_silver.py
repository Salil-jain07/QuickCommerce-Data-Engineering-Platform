
import duckdb
from fsspec import filesystem
from pathlib import Path
from backend.config.config import GCS_BUCKET_NAME

PROJECT_ROOT = Path(__file__).resolve().parents[2]
OUTPUT_DIR = PROJECT_ROOT / "datasets" / "processed" / "silver"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

gcs = filesystem("gcs", token="google_default")
con = duckdb.connect("quickcommerce.duckdb")
con.register_filesystem(gcs)

print("Reading Bronze Order Items from GCS...")

con.execute(f"""
CREATE OR REPLACE VIEW bronze_order_items AS
SELECT *
FROM read_parquet(
    'gcs://{GCS_BUCKET_NAME}/bronze/generated/order_items/*.parquet'
)
""")

total_rows = con.execute("""
SELECT COUNT(*) FROM bronze_order_items
""").fetchone()[0]

duplicate_ids = con.execute("""
SELECT COUNT(*)
FROM (
    SELECT order_item_id
    FROM bronze_order_items
    GROUP BY order_item_id
    HAVING COUNT(*) > 1
)
""").fetchone()[0]

missing_values = con.execute("""
SELECT COUNT(*)
FROM bronze_order_items
WHERE order_item_id IS NULL
   OR order_id IS NULL
   OR product_id IS NULL
   OR quantity IS NULL
   OR unit_price IS NULL
   OR sales_amount IS NULL
   OR data_origin IS NULL
""").fetchone()[0]

invalid_quantities = con.execute("""
SELECT COUNT(*)
FROM bronze_order_items
WHERE quantity <= 0
""").fetchone()[0]

invalid_amounts = con.execute("""
SELECT COUNT(*)
FROM bronze_order_items
WHERE unit_price <= 0
   OR sales_amount <= 0
   OR ABS(sales_amount - quantity * unit_price) > 0.01
""").fetchone()[0]

print("\nORDER ITEM DATA QUALITY REPORT")
print("Total rows:", total_rows)
print("Duplicate order item IDs:", duplicate_ids)
print("Rows with missing values:", missing_values)
print("Invalid quantities:", invalid_quantities)
print("Invalid amounts:", invalid_amounts)

print("\nCreating Silver Order Items...")

con.execute("""
CREATE OR REPLACE TABLE silver_order_items AS
SELECT
    TRIM(order_item_id) AS order_item_id,
    TRIM(order_id) AS order_id,
    TRIM(product_id) AS product_id,
    quantity,
    unit_price,
    sales_amount,
    TRIM(data_origin) AS data_origin
FROM bronze_order_items
QUALIFY ROW_NUMBER() OVER (
    PARTITION BY order_item_id
    ORDER BY order_item_id
) = 1
""")

silver_count = con.execute("""
SELECT COUNT(*) FROM silver_order_items
""").fetchone()[0]

print("\nSILVER ORDER ITEMS")
print("Rows:", silver_count)

output_file = OUTPUT_DIR / "order_items.parquet"

con.execute(f"""
COPY silver_order_items
TO '{output_file.as_posix()}'
(FORMAT PARQUET, COMPRESSION ZSTD)
""")

print("Local file:", output_file)

gcs.put(
    str(output_file),
    f"{GCS_BUCKET_NAME}/silver/order_items/order_items.parquet"
)

print("Uploaded to GCS: silver/order_items/order_items.parquet")

con.close()
