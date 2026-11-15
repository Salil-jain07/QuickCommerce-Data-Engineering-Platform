
from datetime import datetime, timedelta
from pathlib import Path
import os
import subprocess
import sys

from airflow.sdk import DAG, task

PROJECT_ROOT = Path(
    os.environ.get(
        "QUICKCOMMERCE_PROJECT_ROOT",
        "/opt/quickcommerce"
    )
)

TRANSFORMATIONS_DIR = PROJECT_ROOT / "backend" / "transformations"

ENV = os.environ.copy()
ENV["PYTHONPATH"] = str(PROJECT_ROOT)


def run_script(script_name):
    script_path = TRANSFORMATIONS_DIR / script_name

    subprocess.run(
        [sys.executable, str(script_path)],
        cwd=str(TRANSFORMATIONS_DIR),
        env=ENV,
        check=True
    )


with DAG(
    dag_id="quickcommerce_etl_pipeline",
    description="QuickCommerce Bronze to Silver to Gold ETL pipeline",
    start_date=datetime(2026, 11, 13),
    schedule=None,
    catchup=False,
    default_args={
        "owner": "quickcommerce",
        "retries": 1,
        "retry_delay": timedelta(minutes=5),
    },
    tags=["quickcommerce", "etl", "duckdb", "gcs"],
) as dag:

    @task
    def transform_customers():
        run_script("bronze_to_silver.py")

    @task
    def transform_orders():
        run_script("orders_to_silver.py")

    @task
    def transform_products():
        run_script("products_to_silver.py")

    @task
    def transform_stores():
        run_script("stores_to_silver.py")

    @task
    def transform_order_items():
        run_script("order_items_to_silver.py")

    @task
    def transform_payments():
        run_script("payments_to_silver.py")

    @task
    def transform_deliveries():
        run_script("deliveries_to_silver.py")

    @task
    def verify_silver():
        run_script("verify_silver.py")

    @task
    def transform_gold_orders():
        run_script("orders_to_gold.py")

    @task
    def transform_gold_sales():
        run_script("sales_to_gold.py")

    @task
    def transform_gold_payments():
        run_script("payments_to_gold.py")

    @task
    def transform_gold_deliveries():
        run_script("deliveries_to_gold.py")

    @task
    def verify_gold():
        run_script("verify_gold.py")

    customers = transform_customers()
    orders = transform_orders()
    products = transform_products()
    stores = transform_stores()
    order_items = transform_order_items()
    payments = transform_payments()
    deliveries = transform_deliveries()

    silver_check = verify_silver()

    gold_orders = transform_gold_orders()

    gold_sales = transform_gold_sales()
    gold_payments = transform_gold_payments()
    gold_deliveries = transform_gold_deliveries()

    gold_check = verify_gold()

    customers >> orders >> products >> stores
    stores >> order_items >> payments >> deliveries

    deliveries >> silver_check >> gold_orders

    gold_orders >> gold_sales >> gold_payments >> gold_deliveries >> gold_check
