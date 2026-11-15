
import pandas as pd
import numpy as np
from pathlib import Path
from config import TOTAL_CUSTOMERS, BATCH_SIZE, RANDOM_SEED, CITIES, START_DATE, END_DATE

PROJECT_ROOT = Path(__file__).resolve().parents[2]

OUTPUT_DIR = PROJECT_ROOT / "datasets" / "processed" / "generated" / "customers"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

rng = np.random.default_rng(RANDOM_SEED)

first_names = [
    "Aarav", "Vivaan", "Aditya", "Arjun", "Rahul",
    "Rohan", "Ananya", "Diya", "Priya", "Isha",
    "Neha", "Kavya", "Meera", "Sanya", "Aisha"
]

last_names = [
    "Sharma", "Verma", "Patel", "Singh", "Gupta",
    "Jain", "Kumar", "Mehta", "Shah", "Reddy",
    "Malhotra", "Agarwal", "Joshi", "Nair", "Das"
]

loyalty_tiers = ["Bronze", "Silver", "Gold", "Platinum"]
loyalty_probabilities = [0.40, 0.30, 0.20, 0.10]

start_date = np.datetime64(START_DATE, "D")
end_date = np.datetime64(END_DATE, "D")
date_range = (end_date - start_date).astype(int)

total_batches = (TOTAL_CUSTOMERS + BATCH_SIZE - 1) // BATCH_SIZE

customer_number = 1

for batch_number in range(1, total_batches + 1):

    current_batch_size = min(
        BATCH_SIZE,
        TOTAL_CUSTOMERS - (customer_number - 1)
    )

    customer_ids = np.arange(
        customer_number,
        customer_number + current_batch_size
    )

    first = rng.choice(first_names, current_batch_size)
    last = rng.choice(last_names, current_batch_size)

    df = pd.DataFrame({
        "customer_id": [
            f"CUST{i:07d}" for i in customer_ids
        ],
        "customer_name": [
            f"{f} {l}" for f, l in zip(first, last)
        ],
        "age": rng.integers(18, 76, current_batch_size),
        "gender": rng.choice(
            ["Male", "Female", "Other"],
            current_batch_size,
            p=[0.49, 0.49, 0.02]
        ),
        "city": rng.choice(CITIES, current_batch_size),
        "signup_date": (
            start_date +
            rng.integers(0, date_range + 1, current_batch_size)
        ),
        "loyalty_tier": rng.choice(
            loyalty_tiers,
            current_batch_size,
            p=loyalty_probabilities
        )
    })

    output_file = OUTPUT_DIR / f"customers_batch_{batch_number:03d}.parquet"

    df.to_parquet(output_file, index=False)

    print(
        f"Batch {batch_number}/{total_batches} completed: "
        f"{len(df)} customers"
    )

    customer_number += current_batch_size

print("\nCustomer generation completed!")
print("Total customers:", TOTAL_CUSTOMERS)
print("Output directory:", OUTPUT_DIR)
