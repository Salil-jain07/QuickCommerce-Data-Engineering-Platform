
import os
from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(PROJECT_ROOT / ".env")

engine = create_engine(os.getenv("DATABASE_URL"))

tables = [
    "gold_sales_summary",
    "gold_payment_summary",
    "gold_delivery_summary"
]

with engine.connect() as connection:
    print("\nNEON WAREHOUSE VERIFICATION")

    for table in tables:
        result = connection.execute(
            text(f"SELECT COUNT(*) FROM quickcommerce.{table}")
        )
        count = result.scalar()

        print(f"{table}: {count:,} rows")

engine.dispose()
