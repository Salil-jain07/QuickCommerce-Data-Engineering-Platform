
import sys
from pathlib import Path
from google.cloud import storage

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CONFIG_DIR = PROJECT_ROOT / "backend" / "config"

sys.path.insert(0, str(CONFIG_DIR))

from config import GCS_BUCKET_NAME, GCS_PROJECT_ID

client = storage.Client(project=GCS_PROJECT_ID)
bucket = client.bucket(GCS_BUCKET_NAME)

datasets = [
    "customers",
    "products",
    "stores",
    "orders",
    "order_items",
    "payments",
    "deliveries"
]

grand_total = 0

for dataset in datasets:
    prefix = f"bronze/generated/{dataset}/"
    blobs = list(client.list_blobs(bucket, prefix=prefix))

    total_size = sum(blob.size for blob in blobs)
    grand_total += total_size

    print(f"\n{dataset.upper()}")
    print("Files:", len(blobs))
    print(f"Size: {total_size / (1024 ** 2):.2f} MB")

print("\nTOTAL FILES:", sum(
    len(list(client.list_blobs(bucket, prefix=f"bronze/generated/{dataset}/")))
    for dataset in datasets
))

print(f"TOTAL SIZE: {grand_total / (1024 ** 3):.3f} GB")
