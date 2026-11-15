
# Synthetic Data Generation Configuration

# Main dataset targets
TOTAL_ORDERS = 10_000_000
TOTAL_CUSTOMERS = 1_000_000
TOTAL_PRODUCTS = 50_000
TOTAL_STORES = 1_000

# Process orders in batches
BATCH_SIZE = 100_000

# 10 million orders / 100,000 per batch = 100 batches
TOTAL_BATCHES = TOTAL_ORDERS // BATCH_SIZE

# Reproducibility
RANDOM_SEED = 42

# Quick-commerce platforms
PLATFORMS = [
    "Blinkit",
    "Swiggy Instamart",
    "Flipkart Minutes"
]

# Indian cities
CITIES = [
    "Bhopal",
    "Indore",
    "Delhi",
    "Mumbai",
    "Bengaluru",
    "Hyderabad",
    "Pune",
    "Chennai",
    "Kolkata",
    "Jaipur",
    "Lucknow",
    "Ahmedabad"
]

# Synthetic order generation period
START_DATE = "2025-01-01"
END_DATE = "2026-10-31"

# Output format
OUTPUT_FORMAT = "parquet"

# Local output directory
OUTPUT_DIR = "datasets/processed/generated"
