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
    f"gcs://{GCS_BUCKET_NAME}/bronze/generated/stores/*.parquet"
)

con.execute(f"""
    CREATE OR REPLACE TABLE bronze_stores AS
    SELECT *
    FROM read_parquet('{source_path}')
""")

total_rows = con.execute("""
    SELECT COUNT(*) FROM bronze_stores
""").fetchone()[0]

duplicate_ids = con.execute("""
    SELECT COUNT(*)
    FROM (
        SELECT store_id
        FROM bronze_stores
        GROUP BY store_id
        HAVING COUNT(*) > 1
    )
""").fetchone()[0]

missing_values = con.execute("""
    SELECT COUNT(*)
    FROM bronze_stores
    WHERE store_id IS NULL
       OR store_name IS NULL
       OR platform IS NULL
       OR city IS NULL
       OR store_type IS NULL
""").fetchone()[0]

print("STORE DATA QUALITY REPORT")
print("Total rows:", total_rows)
print("Duplicate store IDs:", duplicate_ids)
print("Rows with missing values:", missing_values)

con.execute("""
    CREATE OR REPLACE TABLE silver_stores AS
    SELECT
        TRIM(store_id) AS store_id,
        TRIM(store_name) AS store_name,
        TRIM(platform) AS platform,
        TRIM(city) AS city,
        TRIM(store_type) AS store_type,
        capacity_sqft,
        is_active,
        TRIM(data_origin) AS data_origin
    FROM bronze_stores
    QUALIFY ROW_NUMBER() OVER (
        PARTITION BY store_id
        ORDER BY store_id
    ) = 1
""")

local_file = OUTPUT_DIR / "stores.parquet"

con.execute(f"""
    COPY silver_stores
    TO '{local_file.as_posix()}'
    (FORMAT PARQUET, COMPRESSION ZSTD)
""")

silver_rows = con.execute("""
    SELECT COUNT(*) FROM silver_stores
""").fetchone()[0]

print("\nSILVER STORE DATA")
print("Rows:", silver_rows)
print("Local file:", local_file)

gcs.put(
    str(local_file),
    f"{GCS_BUCKET_NAME}/silver/stores/stores.parquet"
)

print("\nUploaded to GCS: silver/stores/stores.parquet")

con.close()
