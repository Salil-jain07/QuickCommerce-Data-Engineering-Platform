
import pandas as pd
import numpy as np
from pathlib import Path
from config import TOTAL_PRODUCTS, BATCH_SIZE, RANDOM_SEED

PROJECT_ROOT = Path(__file__).resolve().parents[2]

REFERENCE_FILE = (
    PROJECT_ROOT
    / "datasets"
    / "processed"
    / "reference"
    / "grocery_products_cleaned.parquet"
)

OUTPUT_DIR = (
    PROJECT_ROOT
    / "datasets"
    / "processed"
    / "generated"
    / "products"
)

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

rng = np.random.default_rng(RANDOM_SEED)

grocery = pd.read_parquet(REFERENCE_FILE)

categories = grocery["item_type"].dropna().unique()

category_probabilities = (
    grocery["item_type"].value_counts(normalize=True)
    .reindex(categories)
    .to_numpy()
)

weights = grocery["item_weight"].dropna().to_numpy()
mrp_values = grocery["item_mrp"].dropna().to_numpy()

brands = [
    "FreshChoice", "DailyBasket", "QuickMart",
    "NatureFresh", "UrbanHarvest", "ValuePlus",
    "SmartPantry", "PureFoods", "GreenLeaf",
    "DailyEssentials"
]

total_batches = (
    TOTAL_PRODUCTS + BATCH_SIZE - 1
) // BATCH_SIZE

product_number = 1

for batch_number in range(1, total_batches + 1):

    current_batch_size = min(
        BATCH_SIZE,
        TOTAL_PRODUCTS - product_number + 1
    )

    product_ids = np.arange(
        product_number,
        product_number + current_batch_size
    )

    selected_categories = rng.choice(
        categories,
        current_batch_size,
        p=category_probabilities
    )

    selected_weights = rng.choice(
        weights,
        current_batch_size
    ).round(2)

    mrp = rng.choice(
        mrp_values,
        current_batch_size
    ).round(2)

    discount = rng.uniform(
        0.05,
        0.25,
        current_batch_size
    )

    selling_price = (
        mrp * (1 - discount)
    ).round(2)

    selected_brands = rng.choice(
        brands,
        current_batch_size
    )

    df = pd.DataFrame({
        "product_id": [
            f"PROD{i:06d}" for i in product_ids
        ],
        "product_name": [
            f"{category} Product {i:06d}"
            for category, i in zip(
                selected_categories,
                product_ids
            )
        ],
        "category": selected_categories,
        "brand": selected_brands,
        "unit_weight": selected_weights,
        "mrp": mrp,
        "selling_price": selling_price,
        "discount_percentage": (
            discount * 100
        ).round(2),
        "data_origin": "Synthetic"
    })

    output_file = (
        OUTPUT_DIR
        / f"products_batch_{batch_number:03d}.parquet"
    )

    df.to_parquet(output_file, index=False)

    print(
        f"Batch {batch_number}/{total_batches} completed: "
        f"{len(df)} products"
    )

    product_number += current_batch_size

print("\nProduct generation completed!")
print("Total products:", TOTAL_PRODUCTS)
print("Output directory:", OUTPUT_DIR)
