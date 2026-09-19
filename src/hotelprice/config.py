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


# XGBRegressor hyperparameters (the seed comes from get_random_seed(), passed at training time).
XGB_PARAMS = {
    "n_estimators": 300,
    "learning_rate": 0.05,
    "max_depth": 5,
    "subsample": 0.8,
    "colsample_bytree": 0.8,
    "n_jobs": 1,  # single thread keeps results deterministic
}


def get_data_path() -> Path:
    """Dataset location (env: HOTELPRICE_DATA_PATH, default: data/dataset.csv)."""
    return Path(os.environ.get("HOTELPRICE_DATA_PATH", PROJECT_ROOT / "data" / "dataset.csv"))


def get_preprocessor_path() -> Path:
    """Where the fitted preprocessor is saved (env: HOTELPRICE_PREPROCESSOR_PATH)."""
    return Path(
        os.environ.get(
            "HOTELPRICE_PREPROCESSOR_PATH", PROJECT_ROOT / "artifacts" / "preprocessor.joblib"
        )
    )


def get_model_dir() -> Path:
    """Where the trained model, preprocessor and metrics are saved (env: HOTELPRICE_MODEL_DIR)."""
    return Path(os.environ.get("HOTELPRICE_MODEL_DIR", PROJECT_ROOT / "models"))


def get_test_size() -> float:
    """Fraction of rows held out for testing (env: HOTELPRICE_TEST_SIZE, default: 0.2)."""
    return float(os.environ.get("HOTELPRICE_TEST_SIZE", "0.2"))


def get_random_seed() -> int:
    """Seed for the train/test split and the model (env: HOTELPRICE_RANDOM_SEED, default: 42)."""
    return int(os.environ.get("HOTELPRICE_RANDOM_SEED", "42"))
