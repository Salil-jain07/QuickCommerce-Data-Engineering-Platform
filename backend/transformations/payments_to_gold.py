
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

    print("Creating Gold Payment Summary...")

    con.execute("""
    CREATE OR REPLACE TABLE gold_payment_summary AS
    SELECT
        CAST(order_datetime AS DATE) AS payment_date,
        platform,
        city,
        payment_method,
        COUNT(*) AS total_transactions,
        COUNT(*) FILTER (
            WHERE payment_status = 'Successful'
        ) AS successful_payments,
        COUNT(*) FILTER (
            WHERE payment_status = 'Refunded'
        ) AS refunded_payments,
        COUNT(*) FILTER (
            WHERE payment_status = 'Pending'
        ) AS pending_payments,
        SUM(
            CASE
                WHEN payment_status = 'Successful'
                THEN payment_amount
                ELSE 0
            END
        ) AS successful_payment_amount,
        SUM(
            CASE
                WHEN payment_status = 'Refunded'
                THEN payment_amount
                ELSE 0
            END
        ) AS refunded_amount
    FROM src_gold_orders
    GROUP BY
        CAST(order_datetime AS DATE),
        platform,
        city,
        payment_method
    """)

    total_rows = con.execute("""
    SELECT COUNT(*) FROM gold_payment_summary
    """).fetchone()[0]

    print("\nGOLD PAYMENT SUMMARY")
    print("Total rows:", total_rows)

    print("\nSample records:")

    records = con.execute("""
    SELECT *
    FROM gold_payment_summary
    LIMIT 5
    """).fetchall()

    for record in records:
        print(record)

    output_file = GOLD_DIR / "gold_payment_summary.parquet"

    con.execute(f"""
    COPY gold_payment_summary
    TO '{output_file.as_posix()}'
    (FORMAT PARQUET, COMPRESSION ZSTD)
    """)

    print("\nLocal file:", output_file)

    gcs = filesystem("gcs", token="google_default")

    gcs.put(
        str(output_file),
        f"{GCS_BUCKET_NAME}/gold/gold_payment_summary.parquet"
    )

    print("Uploaded to GCS: gold/gold_payment_summary.parquet")

except Exception:
    import traceback
    traceback.print_exc()
    raise
finally:
    con.close()
