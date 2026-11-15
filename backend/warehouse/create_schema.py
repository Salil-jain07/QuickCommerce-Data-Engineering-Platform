
import os
from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(PROJECT_ROOT / ".env")

engine = create_engine(os.getenv("DATABASE_URL"))

with engine.begin() as connection:
    connection.execute(text("CREATE SCHEMA IF NOT EXISTS quickcommerce"))

print("QuickCommerce schema created successfully")

engine.dispose()
