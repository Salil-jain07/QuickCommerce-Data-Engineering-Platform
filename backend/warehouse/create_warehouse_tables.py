
import os
from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(PROJECT_ROOT / ".env")

engine = create_engine(os.getenv("DATABASE_URL"))

tables = {
    "gold_sales_summary": """
        CREATE TABLE IF NOT EXISTS quickcommerce.gold_sales_summary (
            order_date DATE,
            platform VARCHAR,
            city VARCHAR,
            total_orders BIGINT,
            delivered_orders BIGINT,
            cancelled_orders BIGINT,
            processing_orders BIGINT,
            total_revenue DOUBLE PRECISION,
            average_order_value DOUBLE PRECISION
        )
    """,

    "gold_payment_summary": """
        CREATE TABLE IF NOT EXISTS quickcommerce.gold_payment_summary (
            payment_date DATE,
            platform VARCHAR,
            city VARCHAR,
            payment_method VARCHAR,
            total_transactions BIGINT,
            successful_payments BIGINT,
            refunded_payments BIGINT,
            pending_payments BIGINT,
            successful_payment_amount DOUBLE PRECISION,
            refunded_amount DOUBLE PRECISION
        )
    """,

    "gold_delivery_summary": """
        CREATE TABLE IF NOT EXISTS quickcommerce.gold_delivery_summary (
            delivery_date DATE,
            platform VARCHAR,
            city VARCHAR,
            traffic_condition VARCHAR,
            weather_condition VARCHAR,
            vehicle_type VARCHAR,
            total_orders BIGINT,
            delivered_orders BIGINT,
            completed_deliveries BIGINT,
            average_delivery_minutes DOUBLE PRECISION,
            average_distance_km DOUBLE PRECISION
        )
    """
}

with engine.begin() as connection:
    connection.execute(text("CREATE SCHEMA IF NOT EXISTS quickcommerce"))

    for table_name, query in tables.items():
        connection.execute(text(query))
        print(f"Created table: {table_name}")

print("\nAll warehouse tables created successfully")

engine.dispose()
