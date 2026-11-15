
import pandas as pd
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]

CUSTOMER_DIR = PROJECT_ROOT / "datasets/processed/generated/customers"
PRODUCT_FILE = PROJECT_ROOT / "datasets/processed/generated/products/products_batch_001.parquet"
STORE_FILE = PROJECT_ROOT / "datasets/processed/generated/stores/stores.parquet"

customer_files = sorted(CUSTOMER_DIR.glob("*.parquet"))

customers = pd.concat(
    [pd.read_parquet(file) for file in customer_files],
    ignore_index=True
)

products = pd.read_parquet(PRODUCT_FILE)
stores = pd.read_parquet(STORE_FILE)

def validate_dataset(name, df, id_column):
    print(f"\n========== {name} ==========")
    print("Total records:", len(df))
    print("Total columns:", len(df.columns))
    print("Duplicate IDs:", df[id_column].duplicated().sum())
    print("Missing values:", df.isnull().sum().sum())
    print("Unique IDs:", df[id_column].nunique())

validate_dataset("CUSTOMERS", customers, "customer_id")
validate_dataset("PRODUCTS", products, "product_id")
validate_dataset("STORES", stores, "store_id")

print("\n========== ADDITIONAL CHECKS ==========")

print(
    "Invalid product prices:",
    (products["selling_price"] <= 0).sum()
)

print(
    "Selling price greater than MRP:",
    (products["selling_price"] > products["mrp"]).sum()
)

print(
    "Invalid customer ages:",
    ((customers["age"] < 18) | (customers["age"] > 75)).sum()
)

print(
    "Invalid store platforms:",
    stores["platform"].isnull().sum()
)

print(
    "Store name mismatches:",
    (
        ~stores.apply(
            lambda row: (
                row["city"] in row["store_name"]
                and row["platform"] in row["store_name"]
            ),
            axis=1
        )
    ).sum()
)

print("\nMaster data validation completed!")
