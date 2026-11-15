
import pandas as pd
import numpy as np
from pathlib import Path
from config import TOTAL_STORES, RANDOM_SEED, CITIES, PLATFORMS

PROJECT_ROOT = Path(__file__).resolve().parents[2]

OUTPUT_DIR = (
    PROJECT_ROOT
    / "datasets"
    / "processed"
    / "generated"
    / "stores"
)

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

rng = np.random.default_rng(RANDOM_SEED)

store_types = [
    "Dark Store",
    "Mini Warehouse",
    "Fulfillment Center"
]

store_type_probabilities = [0.75, 0.15, 0.10]

store_number = np.arange(1, TOTAL_STORES + 1)


selected_cities = rng.choice(CITIES, TOTAL_STORES)
selected_platforms = rng.choice(PLATFORMS, TOTAL_STORES)

df = pd.DataFrame({
    "store_id": [
        f"STORE{i:04d}" for i in store_number
    ],
    "store_name": [
        f"{city} {platform} Store {i:04d}"
        for i, (city, platform) in enumerate(
            zip(selected_cities, selected_platforms),
            start=1
        )
    ],
    "platform": selected_platforms,
    "city": selected_cities,
    "store_type": rng.choice(
        store_types,
        TOTAL_STORES,
        p=store_type_probabilities
    ),
    "capacity_sqft": rng.integers(
        800, 5001, TOTAL_STORES
    ),
    "is_active": rng.choice(
        [True, False],
        TOTAL_STORES,
        p=[0.95, 0.05]
    ),
    "data_origin": "Synthetic"
})


output_file = OUTPUT_DIR / "stores.parquet"

df.to_parquet(output_file, index=False)

print("Store generation completed!")
print("Total stores:", len(df))
print("\nPlatform distribution:")
print(df["platform"].value_counts())

print("\nCity distribution:")
print(df["city"].value_counts())

print("\nStore type distribution:")
print(df["store_type"].value_counts())

print("\nSaved file:", output_file)
