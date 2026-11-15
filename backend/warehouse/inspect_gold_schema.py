
import duckdb
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
GOLD_DIR = PROJECT_ROOT / "datasets" / "processed" / "gold"

datasets = [
    "gold_order_summary",
    "gold_sales_summary",
    "gold_payment_summary",
    "gold_delivery_summary"
]

con = duckdb.connect()

for dataset in datasets:
    file_path = GOLD_DIR / f"{dataset}.parquet"

    print(f"\n{'=' * 50}")
    print(dataset.upper())
    print("=" * 50)

    schema = con.execute(
        f"DESCRIBE SELECT * FROM read_parquet('{file_path.as_posix()}')"
    ).fetchall()

    for column in schema:
        print(f"{column[0]} : {column[1]}")

con.close()
