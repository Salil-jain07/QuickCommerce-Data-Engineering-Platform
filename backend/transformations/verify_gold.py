
from fsspec import filesystem
from backend.config.config import GCS_BUCKET_NAME

gcs = filesystem("gcs", token="google_default")

datasets = [
    "gold_order_summary",
    "gold_sales_summary",
    "gold_payment_summary",
    "gold_delivery_summary"
]

print("\nGOLD LAYER VERIFICATION")

successful = 0
total_size = 0

for dataset in datasets:
    path = f"{GCS_BUCKET_NAME}/gold/{dataset}.parquet"

    if gcs.exists(path):
        info = gcs.info(path)
        size_mb = info["size"] / (1024 * 1024)
        total_size += size_mb
        successful += 1
        print(f"{dataset}: Uploaded | {size_mb:.2f} MB")
    else:
        print(f"{dataset}: NOT FOUND")

print("\nSUMMARY")
print("Gold datasets found:", successful, "/", len(datasets))
print("Total Gold storage:", round(total_size, 2), "MB")

if successful != len(datasets):
    raise RuntimeError("Gold layer verification failed: Some datasets are missing.")

print("Gold layer verification passed.")