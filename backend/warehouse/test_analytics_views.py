
import os
from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(PROJECT_ROOT / ".env")

engine = create_engine(os.getenv("DATABASE_URL"))

views = [
    "v_sales_kpis",
    "v_daily_sales_trend",
    "v_payment_method_performance",
    "v_delivery_city_performance",
    "v_delivery_condition_performance"
]

with engine.connect() as connection:

    for view in views:
        print(f"\n{'=' * 50}")
        print(view.upper())
        print("=" * 50)

        result = connection.execute(
            text(f"SELECT * FROM quickcommerce.{view} LIMIT 5")
        )

        for row in result:
            print(row)

engine.dispose()

print("\nALL ANALYTICS VIEWS TESTED")
