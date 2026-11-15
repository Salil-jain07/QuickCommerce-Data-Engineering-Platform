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
    f"gcs://{GCS_BUCKET_NAME}/bronze/generated/products/*.parquet"
)

con.execute(f"""
    CREATE OR REPLACE TABLE bronze_products AS
    SELECT *
    FROM read_parquet('{source_path}')
""")

total_rows = con.execute("""
    SELECT COUNT(*) FROM bronze_products
""").fetchone()[0]

duplicate_ids = con.execute("""
    SELECT COUNT(*)
    FROM (
        SELECT product_id
        FROM bronze_products
        GROUP BY product_id
        HAVING COUNT(*) > 1
    )
""").fetchone()[0]

missing_values = con.execute("""
    SELECT COUNT(*)
    FROM bronze_products
    WHERE product_id IS NULL
       OR product_name IS NULL
       OR category IS NULL
       OR brand IS NULL
       OR selling_price IS NULL
       OR mrp IS NULL
""").fetchone()[0]

invalid_prices = con.execute("""
    SELECT COUNT(*)
    FROM bronze_products
    WHERE mrp <= 0
       OR selling_price <= 0
       OR selling_price > mrp
""").fetchone()[0]

print("PRODUCT DATA QUALITY REPORT")
print("Total rows:", total_rows)
print("Duplicate product IDs:", duplicate_ids)
print("Rows with missing values:", missing_values)
print("Invalid prices:", invalid_prices)

con.execute("""
    CREATE OR REPLACE TABLE silver_products AS
    SELECT
        TRIM(product_id) AS product_id,
        TRIM(product_name) AS product_name,
        TRIM(category) AS category,
        TRIM(brand) AS brand,
        unit_weight,
        mrp,
        selling_price,
        discount_percentage,
        TRIM(data_origin) AS data_origin
    FROM bronze_products
    QUALIFY ROW_NUMBER() OVER (
        PARTITION BY product_id
        ORDER BY product_id
    ) = 1
""")

local_file = OUTPUT_DIR / "products.parquet"

con.execute(f"""
    COPY silver_products
    TO '{local_file.as_posix()}'
    (FORMAT PARQUET, COMPRESSION ZSTD)
""")

silver_rows = con.execute("""
    SELECT COUNT(*) FROM silver_products
""").fetchone()[0]

print("\nSILVER PRODUCT DATA")
print("Rows:", silver_rows)
print("Local file:", local_file)

gcs.put(
    str(local_file),
    f"{GCS_BUCKET_NAME}/silver/products/products.parquet"
)

print("\nUploaded to GCS: silver/products/products.parquet")

con.close()
