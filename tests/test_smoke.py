from pathlib import Path

import hotelprice

DATASET = Path(__file__).resolve().parents[1] / "data" / "dataset.csv"

EXPECTED_COLUMNS = [
    "hotel",
    "city",
    "room_type",
    "season",
    "day_of_week",
    "is_holiday",
    "is_weekend",
    "occupancy",
    "demand",
    "booking_lead_time_days",
    "competitor_price",
    "room_price",
]


def test_package_imports():
    assert hotelprice.__version__


def test_dataset_schema():
    header = DATASET.read_text().splitlines()[0]
    assert header.split(",") == EXPECTED_COLUMNS
