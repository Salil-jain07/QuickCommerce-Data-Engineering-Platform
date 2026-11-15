
import os
import duckdb
import psycopg
from pathlib import Path
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(PROJECT_ROOT / ".env")

DATABASE_URL = os.getenv("DATABASE_URL")
GOLD_FILE = PROJECT_ROOT / "datasets" / "processed" / "gold" / "gold_sales_summary.parquet"

duck = duckdb.connect()
postgres = psycopg.connect(DATABASE_URL)

try:
    cursor = duck.execute(
        f"SELECT * FROM read_parquet('{GOLD_FILE.as_posix()}')"
    )

    total_rows = 0

    with postgres.cursor() as pg_cursor:
        pg_cursor.execute(
            "TRUNCATE TABLE quickcommerce.gold_sales_summary"
        )

        with pg_cursor.copy(
            "COPY quickcommerce.gold_sales_summary FROM STDIN"
        ) as copy:
            while True:
                batch = cursor.fetchmany(5000)

                if not batch:
                    break

                for row in batch:
                    copy.write_row(row)

                total_rows += len(batch)
                print(f"Transferred {total_rows:,} rows")

    postgres.commit()

    print("\nGOLD SALES DATA LOADED SUCCESSFULLY")
    print("Total rows:", total_rows)

except Exception:
    postgres.rollback()
    raise

finally:
    duck.close()
    postgres.close()
