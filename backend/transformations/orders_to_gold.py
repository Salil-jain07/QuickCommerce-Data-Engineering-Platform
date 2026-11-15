
import duckdb
from pathlib import Path
from fsspec import filesystem
from backend.config.config import GCS_BUCKET_NAME

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SILVER_DIR = PROJECT_ROOT / "datasets" / "processed" / "silver"
GOLD_DIR = PROJECT_ROOT / "datasets" / "processed" / "gold"
GOLD_DIR.mkdir(parents=True, exist_ok=True)

TEMP_DIR = Path.home() / "duckdb_temp"
TEMP_DIR.mkdir(parents=True, exist_ok=True)

con = duckdb.connect(
    "quickcommerce.duckdb",
    config={
        "memory_limit": "3GB",
        "threads": 4,
        "temp_directory": str(TEMP_DIR),
        "max_temp_directory_size": "100GB"
    }
)

try:
    print("Reading Silver datasets...")

    con.execute(f"""
    CREATE OR REPLACE VIEW src_orders AS
    SELECT * FROM read_parquet('{(SILVER_DIR / "orders.parquet").as_posix()}')
    """)

    con.execute(f"""
    CREATE OR REPLACE VIEW src_customers AS
    SELECT * FROM read_parquet('{(SILVER_DIR / "customers.parquet").as_posix()}')
    """)

    con.execute(f"""
    CREATE OR REPLACE VIEW src_stores AS
    SELECT * FROM read_parquet('{(SILVER_DIR / "stores.parquet").as_posix()}')
    """)

    con.execute(f"""
    CREATE OR REPLACE VIEW src_order_items AS
    SELECT * FROM read_parquet('{(SILVER_DIR / "order_items.parquet").as_posix()}')
    """)

    con.execute(f"""
    CREATE OR REPLACE VIEW src_payments AS
    SELECT * FROM read_parquet('{(SILVER_DIR / "payments.parquet").as_posix()}')
    """)

    con.execute(f"""
    CREATE OR REPLACE VIEW src_deliveries AS
    SELECT * FROM read_parquet('{(SILVER_DIR / "deliveries.parquet").as_posix()}')
    """)

    print("Creating Gold Order Summary...")

    con.execute("""
    CREATE OR REPLACE TABLE gold_order_summary AS

    WITH item_summary AS (
        SELECT
            order_id,
            COUNT(*) AS total_items,
            SUM(quantity) AS total_quantity,
            SUM(sales_amount) AS item_sales_amount
        FROM src_order_items
        GROUP BY order_id
    )

    SELECT
        o.order_id,
        o.customer_id,
        c.customer_name,
        c.loyalty_tier,
        o.store_id,
        s.store_name,
        s.store_type,
        o.platform,
        o.city,
        o.order_datetime,
        o.payment_method,
        o.order_status,
        COALESCE(i.total_items, 0) AS total_items,
        COALESCE(i.total_quantity, 0) AS total_quantity,
        COALESCE(i.item_sales_amount, 0) AS item_sales_amount,
        p.payment_amount,
        p.payment_status,
        d.distance_km,
        d.weather_condition,
        d.traffic_condition,
        d.vehicle_type,
        d.delivery_duration_minutes,
        d.delivery_status
    FROM src_orders o
    LEFT JOIN src_customers c
        ON o.customer_id = c.customer_id
    LEFT JOIN src_stores s
        ON o.store_id = s.store_id
    LEFT JOIN item_summary i
        ON o.order_id = i.order_id
    LEFT JOIN src_payments p
        ON o.order_id = p.order_id
    LEFT JOIN src_deliveries d
        ON o.order_id = d.order_id
    """)

    total_rows = con.execute("""
    SELECT COUNT(*) FROM gold_order_summary
    """).fetchone()[0]

    duplicate_orders = con.execute("""
    SELECT COUNT(*)
    FROM (
        SELECT order_id
        FROM gold_order_summary
        GROUP BY order_id
        HAVING COUNT(*) > 1
    )
    """).fetchone()[0]

    print("\nGOLD ORDER SUMMARY")
    print("Total rows:", total_rows)
    print("Duplicate orders:", duplicate_orders)

    output_file = GOLD_DIR / "gold_order_summary.parquet"

    con.execute(f"""
    COPY (
        SELECT *
        FROM gold_order_summary
        ORDER BY order_id
    )
    TO '{output_file.as_posix()}'
    (FORMAT PARQUET, COMPRESSION ZSTD, ROW_GROUP_SIZE 122880)
    """)

    print("Local file:", output_file)

    gcs = filesystem("gcs", token="google_default")

    gcs.put(
        str(output_file),
        f"{GCS_BUCKET_NAME}/gold/gold_order_summary.parquet"
    )

    print("Uploaded to GCS: gold/gold_order_summary.parquet")

    filter_file = GOLD_DIR / "gold_order_filters.parquet"

    con.execute(f"""
            COPY (
                SELECT DISTINCT city, platform, order_status
                FROM gold_order_summary
            )
            TO '{filter_file.as_posix()}'
            (FORMAT PARQUET, COMPRESSION ZSTD)
        """)

    gcs.put(
        str(filter_file),
        f"{GCS_BUCKET_NAME}/gold/gold_order_filters.parquet"
    )

    print("Uploaded to GCS: gold/gold_order_filters.parquet")
except Exception:
    import traceback
    traceback.print_exc()
    raise
finally:
    con.close()
