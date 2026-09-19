import joblib
import pandas as pd
import pytest

from hotelprice.config import FEATURES
from hotelprice.data_pipeline import run_data_pipeline


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


@pytest.fixture
def pipeline_env(sample_csv, tmp_path, monkeypatch):
    """Point the pipeline at the small sample and a temp preprocessor file."""
    monkeypatch.setenv("HOTELPRICE_DATA_PATH", str(sample_csv))
    monkeypatch.setenv("HOTELPRICE_PREPROCESSOR_PATH", str(tmp_path / "preprocessor.joblib"))
    monkeypatch.setenv("HOTELPRICE_TEST_SIZE", "0.25")
    monkeypatch.setenv("HOTELPRICE_RANDOM_SEED", "1")
    return tmp_path / "preprocessor.joblib"


def test_split_sizes_and_features(pipeline_env):
    X_train, X_test, y_train, y_test, _ = run_data_pipeline()
    assert len(X_train) == 15 and len(X_test) == 5
    assert len(y_train) == 15 and len(y_test) == 5
    assert list(X_train.columns) == FEATURES
    assert set(X_train.index).isdisjoint(X_test.index)


def test_features_are_numeric_without_nans(pipeline_env):
    X_train, X_test, _, _, _ = run_data_pipeline()
    for X in (X_train, X_test):
        assert not X.isna().any().any()
        assert all(pd.api.types.is_numeric_dtype(t) for t in X.dtypes)


def test_split_is_reproducible_and_seed_dependent(pipeline_env, monkeypatch):
    first = run_data_pipeline()[1].index
    assert first.equals(run_data_pipeline()[1].index)
    monkeypatch.setenv("HOTELPRICE_RANDOM_SEED", "2")
    assert not first.equals(run_data_pipeline()[1].index)


def test_saved_preprocessor_matches_and_handles_unseen_category(pipeline_env):
    X_train, _, _, _, preprocessor = run_data_pipeline()
    loaded = joblib.load(pipeline_env)
    raw = pd.read_csv(pipeline_env.parent / "sample.csv")[FEATURES].loc[X_train.index]
    pd.testing.assert_frame_equal(loaded.transform(raw), X_train)

    raw = raw.head(2).assign(city="Atlantis")
    out = loaded.transform(raw)
    assert out["city"].isna().all()
    assert not out.drop(columns="city").isna().any().any()


def test_real_dataset(tmp_path, monkeypatch):
    monkeypatch.setenv("HOTELPRICE_PREPROCESSOR_PATH", str(tmp_path / "preprocessor.joblib"))
    X_train, X_test, y_train, y_test, _ = run_data_pipeline()
    assert X_train.shape == (1600, 11) and X_test.shape == (400, 11)
    assert len(y_train) == 1600 and len(y_test) == 400
    assert not X_train.isna().any().any() and not X_test.isna().any().any()
