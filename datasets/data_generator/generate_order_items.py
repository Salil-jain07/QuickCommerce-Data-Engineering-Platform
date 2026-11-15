
import pandas as pd
import numpy as np
from pathlib import Path
from config import BATCH_SIZE, RANDOM_SEED

PROJECT_ROOT = Path(__file__).resolve().parents[2]

ORDERS_DIR = (
    PROJECT_ROOT / "datasets/processed/generated/orders"
)

PRODUCT_FILE = (
    PROJECT_ROOT / "datasets/processed/generated/products/products_batch_001.parquet"
)

OUTPUT_DIR = (
    PROJECT_ROOT / "datasets/processed/generated/order_items"
)

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

rng = np.random.default_rng(RANDOM_SEED)

products = pd.read_parquet(PRODUCT_FILE)

product_ids = products["product_id"].to_numpy()
product_prices = products["selling_price"].to_numpy()

order_files = sorted(
    ORDERS_DIR.glob("orders_batch_*.parquet")
)

item_number = 1
total_items = 0

for batch_number, order_file in enumerate(order_files, start=1):

    orders = pd.read_parquet(
        order_file,
        columns=["order_id"]
    )

    order_count = len(orders)

    item_counts = rng.integers(
        1,
        6,
        size=order_count
    )

    product_matrix = rng.integers(
        0,
        len(product_ids),
        size=(order_count, 5)
    )

    for column in range(1, 5):
        duplicates = np.zeros(order_count, dtype=bool)

        for previous_column in range(column):
            duplicates |= (
                product_matrix[:, column]
                == product_matrix[:, previous_column]
            )

        while duplicates.any():
            product_matrix[duplicates, column] = rng.integers(
                0,
                len(product_ids),
                size=duplicates.sum()
            )

            duplicates = np.zeros(order_count, dtype=bool)

            for previous_column in range(column):
                duplicates |= (
                    product_matrix[:, column]
                    == product_matrix[:, previous_column]
                )

    item_mask = (
        np.arange(5)[None, :] < item_counts[:, None]
    )

    selected_product_indices = product_matrix[item_mask]

    selected_products = product_ids[selected_product_indices]

    quantities = rng.integers(
        1,
        6,
        size=len(selected_products)
    )

    unit_prices = product_prices[selected_product_indices]

    order_ids = np.repeat(
        orders["order_id"].to_numpy(),
        item_counts
    )

    item_total = len(selected_products)

    df = pd.DataFrame({
        "order_item_id": [
            f"ITEM{i:012d}"
            for i in range(
                item_number,
                item_number + item_total
            )
        ],
        "order_id": order_ids,
        "product_id": selected_products,
        "quantity": quantities,
        "unit_price": unit_prices,
        "sales_amount": (
            quantities * unit_prices
        ).round(2),
        "data_origin": "Synthetic"
    })

    output_file = (
        OUTPUT_DIR
        / f"order_items_batch_{batch_number:03d}.parquet"
    )

    df.to_parquet(output_file, index=False)

    item_number += item_total
    total_items += item_total

    print(
        f"Batch {batch_number}/{len(order_files)} completed: "
        f"{item_total:,} order items"
    )

    del orders, df, product_matrix

print("\nOrder item generation completed!")
print("Total order items:", f"{total_items:,}")
print("Output batches:", len(order_files))
print("Output directory:", OUTPUT_DIR)
