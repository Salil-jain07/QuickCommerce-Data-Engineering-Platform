
from fsspec import filesystem
from backend.config.config import GCS_BUCKET_NAME

gcs = filesystem("gcs", token="google_default")

datasets = [
    "customers",
    "products",
    "stores",
    "orders",
    "order_items",
    "payments",
    "deliveries"
]

print("\nSILVER LAYER VERIFICATION")

total_size = 0
successful = 0

for dataset in datasets:
    file_path = f"{GCS_BUCKET_NAME}/silver/{dataset}/{dataset}.parquet"

    if gcs.exists(file_path):
        info = gcs.info(file_path)
        size_mb = info["size"] / (1024 * 1024)
        total_size += size_mb
        successful += 1
        print(f"{dataset}: Uploaded | {size_mb:.2f} MB")
    else:
        print(f"{dataset}: NOT FOUND")

print("\nSUMMARY")
print("Datasets found:", successful, "/", len(datasets))
print("Total Silver storage:", round(total_size, 2), "MB")

if successful != len(datasets):
    raise RuntimeError("Silver layer verification failed: Some datasets are missing.")

print("Silver layer verification passed.")