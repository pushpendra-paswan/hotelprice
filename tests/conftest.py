import pandas as pd
import pytest


@pytest.fixture
def sample_csv(tmp_path):
    rows = 20
    df = pd.DataFrame(
        {
            "hotel": ["A", "B"] * (rows // 2),
            "city": ["Goa", "Delhi", "Mumbai", "Jaipur"] * (rows // 4),
            "room_type": ["Standard", "Suite"] * (rows // 2),
            "season": ["Low", "Peak", "High", "Shoulder"] * (rows // 4),
            "day_of_week": ["Monday", "Saturday", "Sunday", "Friday", "Tuesday"] * (rows // 5),
            "is_holiday": [0, 1] * (rows // 2),
            "is_weekend": [0, 0, 1, 1, 0] * (rows // 5),
            "occupancy": [float(40 + i) for i in range(rows)],
            "demand": [float(50 + i) for i in range(rows)],
            "booking_lead_time_days": list(range(rows)),
            "competitor_price": [5000.0 + 100 * i for i in range(rows)],
            "room_price": [5500.0 + 110 * i for i in range(rows)],
        }
    )
    path = tmp_path / "sample.csv"
    df.to_csv(path, index=False)
    return path
