
import pandas as pd
import numpy as np
from pathlib import Path
from config import RANDOM_SEED

PROJECT_ROOT = Path(__file__).resolve().parents[2]

ORDERS_DIR = PROJECT_ROOT / "datasets/processed/generated/orders"
ITEMS_DIR = PROJECT_ROOT / "datasets/processed/generated/order_items"
OUTPUT_DIR = PROJECT_ROOT / "datasets/processed/generated/payments"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

rng = np.random.default_rng(RANDOM_SEED)

order_files = sorted(ORDERS_DIR.glob("orders_batch_*.parquet"))

total_payments = 0

for batch_number, order_file in enumerate(order_files, start=1):

    item_file = (
        ITEMS_DIR
        / f"order_items_batch_{batch_number:03d}.parquet"
    )

    orders = pd.read_parquet(
        order_file,
        columns=[
            "order_id",
            "order_datetime",
            "payment_method",
            "order_status"
        ]
    )

    items = pd.read_parquet(
        item_file,
        columns=["order_id", "sales_amount"]
    )

    order_totals = (
        items.groupby("order_id")["sales_amount"]
        .sum()
        .round(2)
        .reset_index()
    )

    payments = orders.merge(
        order_totals,
        on="order_id",
        how="left",
        validate="one_to_one"
    )

    if payments["sales_amount"].isna().any():
        raise ValueError(
            f"Missing payment amount in batch {batch_number}"
        )

    payment_status = payments["order_status"].map({
        "Delivered": "Successful",
        "Cancelled": "Refunded",
        "Processing": "Pending"
    })

    payment_datetime = (
        pd.to_datetime(payments["order_datetime"])
        + pd.to_timedelta(
            rng.integers(0, 6, size=len(payments)),
            unit="m"
        )
    )

    payment_df = pd.DataFrame({
        "payment_id": [
            f"PAY{i:012d}"
            for i in range(
                total_payments + 1,
                total_payments + len(payments) + 1
            )
        ],
        "order_id": payments["order_id"],
        "payment_method": payments["payment_method"],
        "payment_amount": payments["sales_amount"],
        "payment_status": payment_status,
        "payment_datetime": payment_datetime,
        "data_origin": "Synthetic"
    })

    output_file = (
        OUTPUT_DIR
        / f"payments_batch_{batch_number:03d}.parquet"
    )

    payment_df.to_parquet(output_file, index=False)

    total_payments += len(payment_df)

    print(
        f"Batch {batch_number}/{len(order_files)} completed: "
        f"{len(payment_df):,} payments"
    )

    del orders, items, order_totals, payments, payment_df

print("\nPayment generation completed!")
print("Total payment records:", f"{total_payments:,}")
print("Output batches:", len(order_files))
print("Output directory:", OUTPUT_DIR)
