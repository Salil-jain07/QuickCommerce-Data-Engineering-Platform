import os

GCS_BUCKET_NAME = os.getenv(
    "GCS_BUCKET_NAME",
    "quickcommerce-data-platform-salil"
)

GCS_PROJECT_ID = os.getenv(
    "GCS_PROJECT_ID",
    "project-655a0943-237b-4426-821"
)

GCS_REGION = os.getenv(
    "GCS_REGION",
    "asia-south1"
)
