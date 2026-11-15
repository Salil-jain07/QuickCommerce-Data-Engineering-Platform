
import sys
from pathlib import Path
from google.cloud import storage

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CONFIG_DIR = PROJECT_ROOT / "backend" / "config"

sys.path.insert(0, str(CONFIG_DIR))

from config import GCS_BUCKET_NAME, GCS_PROJECT_ID

LOCAL_BASE_DIR = PROJECT_ROOT / "datasets" / "processed" / "generated"

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

for dataset in datasets:
    folder = LOCAL_BASE_DIR / dataset
    files = sorted(folder.glob("*.parquet"))

    print(f"\nUploading {dataset}: {len(files)} files")

    for file in files:
        destination = f"bronze/generated/{dataset}/{file.name}"
        blob = bucket.blob(destination)
        blob.upload_from_filename(str(file))

        print(f"Uploaded: {destination}")

print("\nAll generated datasets uploaded successfully!")
