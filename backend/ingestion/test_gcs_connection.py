from google.cloud import storage
from backend.config.config import GCS_BUCKET_NAME, GCS_PROJECT_ID

client = storage.Client(project=GCS_PROJECT_ID)

bucket = client.bucket(GCS_BUCKET_NAME)

print("Bucket exists:", bucket.exists())
