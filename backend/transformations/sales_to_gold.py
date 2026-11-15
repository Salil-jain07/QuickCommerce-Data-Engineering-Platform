
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

    print("Creating Gold Sales Summary...")

    con.execute("""
    CREATE OR REPLACE TABLE gold_sales_summary AS
    SELECT
        CAST(order_datetime AS DATE) AS order_date,
        platform,
        city,
        COUNT(*) AS total_orders,
        COUNT(*) FILTER (
            WHERE order_status = 'Delivered'
        ) AS delivered_orders,
        COUNT(*) FILTER (
            WHERE order_status = 'Cancelled'
        ) AS cancelled_orders,
        COUNT(*) FILTER (
            WHERE order_status = 'Processing'
        ) AS processing_orders,
        SUM(
            CASE
                WHEN order_status = 'Delivered'
                THEN item_sales_amount
                ELSE 0
            END
        ) AS total_revenue,
        AVG(
            CASE
                WHEN order_status = 'Delivered'
                THEN item_sales_amount
            END
        ) AS average_order_value
    FROM src_gold_orders
    GROUP BY
        CAST(order_datetime AS DATE),
        platform,
        city
    """)

    total_rows = con.execute("""
    SELECT COUNT(*) FROM gold_sales_summary
    """).fetchone()[0]

    print("\nGOLD SALES SUMMARY")
    print("Total rows:", total_rows)

    print("\nSample records:")

    records = con.execute("""
    SELECT *
    FROM gold_sales_summary
    ORDER BY order_date
    LIMIT 5
    """).fetchall()

    for record in records:
        print(record)

    output_file = GOLD_DIR / "gold_sales_summary.parquet"

    con.execute(f"""
    COPY gold_sales_summary
    TO '{output_file.as_posix()}'
    (FORMAT PARQUET, COMPRESSION ZSTD)
    """)

    print("\nLocal file:", output_file)

    gcs = filesystem("gcs", token="google_default")

    gcs.put(
        str(output_file),
        f"{GCS_BUCKET_NAME}/gold/gold_sales_summary.parquet"
    )

    print("Uploaded to GCS: gold/gold_sales_summary.parquet")

except Exception:
    import traceback
    traceback.print_exc()
    raise
finally:
    con.close()
