
import pandas as pd
import numpy as np
from pathlib import Path
from config import RANDOM_SEED

PROJECT_ROOT = Path(__file__).resolve().parents[2]

ORDERS_DIR = PROJECT_ROOT / "datasets/processed/generated/orders"
REFERENCE_FILE = PROJECT_ROOT / "datasets/processed/delivery/zomato_delivery_cleaned.parquet"
OUTPUT_DIR = PROJECT_ROOT / "datasets/processed/generated/deliveries"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

rng = np.random.default_rng(RANDOM_SEED)

reference = pd.read_parquet(REFERENCE_FILE)

delivery_times = reference["time_taken_(min)"].dropna().to_numpy()
traffic_values = reference["road_traffic_density"].dropna().to_numpy()
weather_values = reference["weather_condition"].dropna().to_numpy()
vehicle_values = reference["type_of_vehicle"].dropna().to_numpy()

order_files = sorted(ORDERS_DIR.glob("orders_batch_*.parquet"))

total_deliveries = 0

for batch_number, order_file in enumerate(order_files, start=1):

    orders = pd.read_parquet(
        order_file,
        columns=["order_id", "order_datetime", "order_status"]
    )

    count = len(orders)

    distances = np.round(
        rng.uniform(0.5, 5.0, count),
        2
    )

    traffic = rng.choice(
        traffic_values,
        size=count
    )

    weather = rng.choice(
        weather_values,
        size=count
    )

    vehicles = rng.choice(
        vehicle_values,
        size=count
    )

    base_times = rng.choice(
        delivery_times,
        size=count
    )

    traffic_multiplier = pd.Series(traffic).map({
        "Low": 0.85,
        "Medium": 1.0,
        "High": 1.25,
        "Jam": 1.45
    }).to_numpy()

    delivery_duration = np.clip(
        base_times * 0.45 * traffic_multiplier * (distances / 3),
        8,
        60
    )

    delivery_duration = np.round(
        delivery_duration,
        2
    )

    is_delivered = (
        orders["order_status"].to_numpy() == "Delivered"
    )

    is_processing = (
        orders["order_status"].to_numpy() == "Processing"
    )

    delivery_status = np.select(
        [is_delivered, is_processing],
        ["Delivered", "In Transit"],
        default="Cancelled"
    )

    actual_delivery_time = pd.Series(
        pd.to_timedelta(delivery_duration, unit="m")
    )

    actual_delivery_time.loc[~is_delivered] = pd.NaT

    estimated_delivery_time = (
        pd.to_datetime(orders["order_datetime"])
        + pd.to_timedelta(30, unit="m")
    )

    actual_delivery_datetime = (
        pd.to_datetime(orders["order_datetime"])
        + actual_delivery_time
    )

    delivery_df = pd.DataFrame({
        "delivery_id": [
            f"DEL{i:012d}"
            for i in range(
                total_deliveries + 1,
                total_deliveries + count + 1
            )
        ],
        "order_id": orders["order_id"],
        "delivery_partner_id": [
            f"DP{rng.integers(1, 10001):05d}"
            for _ in range(count)
        ],
        "distance_km": distances,
        "traffic_condition": traffic,
        "weather_condition": weather,
        "vehicle_type": vehicles,
        "estimated_delivery_datetime": estimated_delivery_time,
        "actual_delivery_datetime": actual_delivery_datetime,
        "delivery_duration_minutes": np.where(
            is_delivered,
            delivery_duration,
            np.nan
        ),
        "delivery_status": delivery_status,
        "data_origin": "Synthetic"
    })

    output_file = (
        OUTPUT_DIR
        / f"deliveries_batch_{batch_number:03d}.parquet"
    )

    delivery_df.to_parquet(output_file, index=False)

    total_deliveries += count

    print(
        f"Batch {batch_number}/{len(order_files)} completed: "
        f"{count:,} deliveries"
    )

    del orders, delivery_df

print("\nDelivery generation completed!")
print("Total delivery records:", f"{total_deliveries:,}")
print("Output batches:", len(order_files))
print("Output directory:", OUTPUT_DIR)
