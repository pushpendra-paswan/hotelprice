from pathlib import Path

import joblib
import pandas as pd
import pytest

from hotelprice.config import FEATURES
from hotelprice.data_pipeline import run_data_pipeline


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


def test_fixture_dataset(tmp_path, monkeypatch):
    # The CI fixture: 300 rows with the real dataset's schema (the real dataset is DVC-tracked).
    fixture = Path(__file__).parent / "fixtures" / "hotel_sample.csv"
    monkeypatch.setenv("HOTELPRICE_DATA_PATH", str(fixture))
    monkeypatch.setenv("HOTELPRICE_PREPROCESSOR_PATH", str(tmp_path / "preprocessor.joblib"))
    X_train, X_test, y_train, y_test, _ = run_data_pipeline()
    assert X_train.shape == (240, 11) and X_test.shape == (60, 11)
    assert len(y_train) == 240 and len(y_test) == 60
    assert not X_train.isna().any().any() and not X_test.isna().any().any()
