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
    f"gcs://{GCS_BUCKET_NAME}/bronze/generated/customers/*.parquet"
)

con.execute(f"""
    CREATE OR REPLACE TABLE bronze_customers AS
    SELECT *
    FROM read_parquet('{source_path}')
""")

total_rows = con.execute("""
    SELECT COUNT(*) FROM bronze_customers
""").fetchone()[0]

duplicate_ids = con.execute("""
    SELECT COUNT(*)
    FROM (
        SELECT customer_id
        FROM bronze_customers
        GROUP BY customer_id
        HAVING COUNT(*) > 1
    )
""").fetchone()[0]

missing_values = con.execute("""
    SELECT COUNT(*)
    FROM bronze_customers
    WHERE customer_id IS NULL
       OR customer_name IS NULL
       OR age IS NULL
       OR gender IS NULL
       OR city IS NULL
       OR signup_date IS NULL
       OR loyalty_tier IS NULL
""").fetchone()[0]

invalid_ages = con.execute("""
    SELECT COUNT(*)
    FROM bronze_customers
    WHERE age < 18 OR age > 75
""").fetchone()[0]

print("CUSTOMER DATA QUALITY REPORT")
print("Total rows:", total_rows)
print("Duplicate customer IDs:", duplicate_ids)
print("Rows with missing values:", missing_values)
print("Invalid ages:", invalid_ages)

con.execute("""
    CREATE OR REPLACE TABLE silver_customers AS
    SELECT
        TRIM(customer_id) AS customer_id,
        TRIM(customer_name) AS customer_name,
        age,
        TRIM(gender) AS gender,
        TRIM(city) AS city,
        CAST(signup_date AS DATE) AS signup_date,
        TRIM(loyalty_tier) AS loyalty_tier
    FROM bronze_customers
    QUALIFY ROW_NUMBER() OVER (
        PARTITION BY customer_id
        ORDER BY signup_date DESC
    ) = 1
""")

local_file = OUTPUT_DIR / "customers.parquet"

con.execute(f"""
    COPY silver_customers    TO '{local_file.as_posix()}'
    (FORMAT PARQUET, COMPRESSION ZSTD)
""")

silver_rows = con.execute("""
    SELECT COUNT(*) FROM silver_customers""").fetchone()[0]

print("\nSILVER CUSTOMER DATA")
print("Rows:", silver_rows)
print("Local file:", local_file)

gcs_path = (
    f"bronze/generated/customers/customers_batch_001.parquet"
)

silver_gcs_path = (
    f"silver/customers/customers.parquet"
)

gcs.put(str(local_file), f"{GCS_BUCKET_NAME}/{silver_gcs_path}")

print("\nUploaded to GCS:", silver_gcs_path)

con.close()
