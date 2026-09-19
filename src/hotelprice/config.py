"""Runtime configuration. Values come from environment variables with defaults."""

import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]

TARGET = "room_price"
CATEGORICAL_FEATURES = ["hotel", "city", "room_type", "season", "day_of_week"]
NUMERICAL_FEATURES = [
    "is_holiday",
    "is_weekend",
    "occupancy",
    "demand",
    "booking_lead_time_days",
    "competitor_price",
]
FEATURES = CATEGORICAL_FEATURES + NUMERICAL_FEATURES


def get_data_path() -> Path:
    """Dataset location (env: HOTELPRICE_DATA_PATH, default: data/dataset.csv)."""
    return Path(os.environ.get("HOTELPRICE_DATA_PATH", PROJECT_ROOT / "data" / "dataset.csv"))


def get_preprocessor_path() -> Path:
    """Where the fitted preprocessor is saved (env: HOTELPRICE_PREPROCESSOR_PATH)."""
    return Path(
        os.environ.get("HOTELPRICE_PREPROCESSOR_PATH", PROJECT_ROOT / "artifacts" / "preprocessor.joblib")
    )


def get_test_size() -> float:
    """Fraction of rows held out for testing (env: HOTELPRICE_TEST_SIZE, default: 0.2)."""
    return float(os.environ.get("HOTELPRICE_TEST_SIZE", "0.2"))


def get_random_seed() -> int:
    """Seed for the train/test split (env: HOTELPRICE_RANDOM_SEED, default: 42)."""
    return int(os.environ.get("HOTELPRICE_RANDOM_SEED", "42"))
