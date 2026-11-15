
import os
from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(PROJECT_ROOT / ".env")

engine = create_engine(os.getenv("DATABASE_URL"))

query = """
SELECT
    relname AS table_name,
    pg_size_pretty(pg_total_relation_size(relid)) AS total_size,
    pg_total_relation_size(relid) AS size_bytes
FROM pg_catalog.pg_statio_user_tables
WHERE schemaname = 'quickcommerce'
ORDER BY pg_total_relation_size(relid) DESC
"""

with engine.connect() as connection:
    print("\nWAREHOUSE TABLE STORAGE")

    results = connection.execute(text(query))

    for row in results:
        print(f"{row.table_name}: {row.total_size}")

    database_size = connection.execute(
        text("SELECT pg_size_pretty(pg_database_size(current_database()))")
    ).scalar()

    print("\nTotal database size:", database_size)

engine.dispose()
