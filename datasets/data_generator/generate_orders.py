
import pandas as pd
import numpy as np
from pathlib import Path
from config import (
    TOTAL_ORDERS,
    BATCH_SIZE,
    RANDOM_SEED,
    START_DATE,
    END_DATE
)

PROJECT_ROOT = Path(__file__).resolve().parents[2]

CUSTOMER_DIR = (
    PROJECT_ROOT / "datasets/processed/generated/customers"
)

STORE_FILE = (
    PROJECT_ROOT / "datasets/processed/generated/stores/stores.parquet"
)

OUTPUT_DIR = (
    PROJECT_ROOT / "datasets/processed/generated/orders"
)

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

rng = np.random.default_rng(RANDOM_SEED)

customer_files = sorted(CUSTOMER_DIR.glob("*.parquet"))

customers = pd.concat(
    [pd.read_parquet(file, columns=["customer_id"]) for file in customer_files],
    ignore_index=True
)

stores = pd.read_parquet(STORE_FILE)

customer_ids = customers["customer_id"].to_numpy()
store_ids = stores["store_id"].to_numpy()
store_platforms = stores["platform"].to_numpy()
store_cities = stores["city"].to_numpy()

payment_methods = [
    "UPI",
    "Credit Card",
    "Debit Card",
    "Wallet",
    "Cash"
]

payment_probabilities = [
    0.40, 0.20, 0.15, 0.20, 0.05
]

order_statuses = [
    "Delivered",
    "Cancelled",
    "Processing"
]

status_probabilities = [
    0.92, 0.05, 0.03
]

start_timestamp = pd.Timestamp(START_DATE)
end_timestamp = pd.Timestamp(END_DATE) + pd.Timedelta(days=1)

total_seconds = int(
    (end_timestamp - start_timestamp).total_seconds()
)

total_batches = (
    TOTAL_ORDERS + BATCH_SIZE - 1
) // BATCH_SIZE

order_number = 1

for batch_number in range(1, total_batches + 1):

    current_batch_size = min(
        BATCH_SIZE,
        TOTAL_ORDERS - order_number + 1
    )

    selected_customers = rng.choice(
        customer_ids,
        current_batch_size
    )

    selected_store_indices = rng.integers(
        0,
        len(store_ids),
        current_batch_size
    )

    selected_stores = store_ids[selected_store_indices]
    selected_platforms = store_platforms[selected_store_indices]
    selected_cities = store_cities[selected_store_indices]

    random_seconds = rng.integers(
        0,
        total_seconds,
        current_batch_size
    )

    order_datetimes = (
        start_timestamp
        + pd.to_timedelta(random_seconds, unit="s")
    )

    df = pd.DataFrame({
        "order_id": [
            f"ORD{i:010d}"
            for i in range(
                order_number,
                order_number + current_batch_size
            )
        ],
        "customer_id": selected_customers,
        "store_id": selected_stores,
        "platform": selected_platforms,
        "city": selected_cities,
        "order_datetime": order_datetimes,
        "payment_method": rng.choice(
            payment_methods,
            current_batch_size,
            p=payment_probabilities
        ),
        "order_status": rng.choice(
            order_statuses,
            current_batch_size,
            p=status_probabilities
        ),
        "data_origin": "Synthetic"
    })

    output_file = (
        OUTPUT_DIR
        / f"orders_batch_{batch_number:03d}.parquet"
    )

    df.to_parquet(output_file, index=False)

    print(
        f"Batch {batch_number}/{total_batches} completed: "
        f"{len(df)} orders"
    )

    order_number += current_batch_size

print("\nOrder generation completed!")
print("Total orders:", TOTAL_ORDERS)
print("Total batches:", total_batches)
print("Output directory:", OUTPUT_DIR)
