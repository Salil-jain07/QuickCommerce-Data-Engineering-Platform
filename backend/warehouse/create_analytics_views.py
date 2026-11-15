
import os
from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(PROJECT_ROOT / ".env")

engine = create_engine(os.getenv("DATABASE_URL"))

views = {
    "v_sales_kpis": """
        CREATE OR REPLACE VIEW quickcommerce.v_sales_kpis AS
        SELECT
            SUM(total_orders) AS total_orders,
            SUM(delivered_orders) AS delivered_orders,
            SUM(cancelled_orders) AS cancelled_orders,
            SUM(processing_orders) AS processing_orders,
            SUM(total_revenue) AS total_revenue,
            SUM(total_revenue) / NULLIF(SUM(delivered_orders), 0)
                AS average_order_value
        FROM quickcommerce.gold_sales_summary
    """,

    "v_daily_sales_trend": """
        CREATE OR REPLACE VIEW quickcommerce.v_daily_sales_trend AS
        SELECT
            order_date,
            SUM(total_orders) AS total_orders,
            SUM(delivered_orders) AS delivered_orders,
            SUM(total_revenue) AS total_revenue
        FROM quickcommerce.gold_sales_summary
        GROUP BY order_date
    """,

    "v_payment_method_performance": """
        CREATE OR REPLACE VIEW quickcommerce.v_payment_method_performance AS
        SELECT
            payment_method,
            SUM(total_transactions) AS total_transactions,
            SUM(successful_payments) AS successful_payments,
            SUM(refunded_payments) AS refunded_payments,
            SUM(pending_payments) AS pending_payments,
            SUM(successful_payment_amount) AS successful_amount,
            SUM(refunded_amount) AS refunded_amount
        FROM quickcommerce.gold_payment_summary
        GROUP BY payment_method
    """,

    "v_delivery_city_performance": """
        CREATE OR REPLACE VIEW quickcommerce.v_delivery_city_performance AS
        SELECT
            city,
            SUM(total_orders) AS total_orders,
            SUM(delivered_orders) AS delivered_orders,
            SUM(completed_deliveries) AS completed_deliveries,
            SUM(average_delivery_minutes * completed_deliveries)
                / NULLIF(SUM(completed_deliveries), 0)
                AS average_delivery_minutes
        FROM quickcommerce.gold_delivery_summary
        GROUP BY city
    """,

    "v_delivery_condition_performance": """
        CREATE OR REPLACE VIEW quickcommerce.v_delivery_condition_performance AS
        SELECT
            traffic_condition,
            weather_condition,
            SUM(completed_deliveries) AS completed_deliveries,
            SUM(average_delivery_minutes * completed_deliveries)
                / NULLIF(SUM(completed_deliveries), 0)
                AS average_delivery_minutes
        FROM quickcommerce.gold_delivery_summary
        GROUP BY traffic_condition, weather_condition
    """
}

with engine.begin() as connection:
    for view_name, query in views.items():
        connection.execute(text(query))
        print(f"Created view: {view_name}")

print("\nAll analytics views created successfully")

engine.dispose()
