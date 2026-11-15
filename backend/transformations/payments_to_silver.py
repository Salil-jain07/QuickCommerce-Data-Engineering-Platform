
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

print("Reading Bronze Payments from GCS...")

con.execute(f"""
CREATE OR REPLACE VIEW bronze_payments AS
SELECT *
FROM read_parquet(
    'gcs://{GCS_BUCKET_NAME}/bronze/generated/payments/*.parquet'
)
""")

total_rows = con.execute("""
SELECT COUNT(*) FROM bronze_payments
""").fetchone()[0]

duplicate_ids = con.execute("""
SELECT COUNT(*)
FROM (
    SELECT payment_id
    FROM bronze_payments
    GROUP BY payment_id
    HAVING COUNT(*) > 1
)
""").fetchone()[0]

missing_values = con.execute("""
SELECT COUNT(*)
FROM bronze_payments
WHERE payment_id IS NULL
   OR order_id IS NULL
   OR payment_method IS NULL
   OR payment_amount IS NULL
   OR payment_status IS NULL
   OR payment_datetime IS NULL
   OR data_origin IS NULL
""").fetchone()[0]

invalid_amounts = con.execute("""
SELECT COUNT(*)
FROM bronze_payments
WHERE payment_amount <= 0
""").fetchone()[0]

invalid_statuses = con.execute("""
SELECT COUNT(*)
FROM bronze_payments
WHERE payment_status NOT IN ('Successful', 'Refunded', 'Pending')
""").fetchone()[0]

print("\nPAYMENT DATA QUALITY REPORT")
print("Total rows:", total_rows)
print("Duplicate payment IDs:", duplicate_ids)
print("Rows with missing values:", missing_values)
print("Invalid payment amounts:", invalid_amounts)
print("Invalid payment statuses:", invalid_statuses)

print("\nCreating Silver Payments...")

con.execute("""
CREATE OR REPLACE TABLE silver_payments AS
SELECT
    TRIM(payment_id) AS payment_id,
    TRIM(order_id) AS order_id,
    TRIM(payment_method) AS payment_method,
    payment_amount,
    TRIM(payment_status) AS payment_status,
    CAST(payment_datetime AS TIMESTAMP) AS payment_datetime,
    TRIM(data_origin) AS data_origin
FROM bronze_payments
QUALIFY ROW_NUMBER() OVER (
    PARTITION BY payment_id
    ORDER BY payment_datetime DESC
) = 1
""")

silver_count = con.execute("""
SELECT COUNT(*) FROM silver_payments
""").fetchone()[0]

print("\nSILVER PAYMENTS")
print("Rows:", silver_count)

output_file = OUTPUT_DIR / "payments.parquet"

con.execute(f"""
COPY silver_payments
TO '{output_file.as_posix()}'
(FORMAT PARQUET, COMPRESSION ZSTD)
""")

print("Local file:", output_file)

gcs.put(
    str(output_file),
    f"{GCS_BUCKET_NAME}/silver/payments/payments.parquet"
)

print("Uploaded to GCS: silver/payments/payments.parquet")

con.close()
