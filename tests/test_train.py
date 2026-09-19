import json
import math

import joblib
import pandas as pd
import pytest
from xgboost import XGBRegressor

from hotelprice.config import FEATURES
from hotelprice.train import run_training


@pytest.fixture
def train_env(sample_csv, tmp_path, monkeypatch):
    """Point training at the small sample and temp output locations."""
    monkeypatch.setenv("HOTELPRICE_DATA_PATH", str(sample_csv))
    monkeypatch.setenv(
        "HOTELPRICE_PREPROCESSOR_PATH", str(tmp_path / "data_pipeline_preprocessor.joblib")
    )
    monkeypatch.setenv("HOTELPRICE_MODEL_DIR", str(tmp_path / "models"))
    monkeypatch.setenv("HOTELPRICE_TEST_SIZE", "0.25")
    return tmp_path / "models"


def test_training_creates_artifacts(train_env):
    run_training()
    assert (train_env / "model.json").is_file()
    assert (train_env / "preprocessor.joblib").is_file()
    assert (train_env / "metrics.json").is_file()


def test_metrics_are_finite_numbers(train_env):
    metrics = run_training()
    assert set(metrics) == {"mae", "rmse", "r2"}
    assert all(math.isfinite(v) for v in metrics.values())
    assert metrics["mae"] >= 0 and metrics["rmse"] >= metrics["mae"]
    assert json.loads((train_env / "metrics.json").read_text()) == metrics


def test_saved_model_predicts_from_raw_rows(train_env, sample_csv):
    run_training()
    model = XGBRegressor()
    model.load_model(train_env / "model.json")
    preprocessor = joblib.load(train_env / "preprocessor.joblib")

    raw = pd.read_csv(sample_csv)[FEATURES].head(3)
    predictions = model.predict(preprocessor.transform(raw))
    assert predictions.shape == (3,)
    assert all(math.isfinite(p) for p in predictions)


def test_training_is_reproducible(train_env):
    assert run_training() == run_training()
