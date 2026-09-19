from pathlib import Path

import pytest

import hotelprice

DATASET = Path(__file__).resolve().parents[1] / "data" / "dataset.csv"
FIXTURE = Path(__file__).parent / "fixtures" / "hotel_sample.csv"

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


def test_fixture_schema():
    header = FIXTURE.read_text().splitlines()[0]
    assert header.split(",") == EXPECTED_COLUMNS


@pytest.mark.skipif(not DATASET.exists(), reason="real dataset is DVC-tracked (dvc pull)")
def test_dataset_schema():
    header = DATASET.read_text().splitlines()[0]
    assert header.split(",") == EXPECTED_COLUMNS
