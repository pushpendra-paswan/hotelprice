import json
import math

import joblib
import mlflow
import pandas as pd
import pytest
from xgboost import XGBRegressor

from hotelprice.config import FEATURES, XGB_PARAMS
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
    # MLflow writes to a temp database and artifact directory, never to the real mlflow.db.
    monkeypatch.setenv("HOTELPRICE_MLFLOW_TRACKING_URI", f"sqlite:///{tmp_path / 'mlflow.db'}")
    monkeypatch.setenv("HOTELPRICE_MLFLOW_ARTIFACT_DIR", str(tmp_path / "mlartifacts"))
    monkeypatch.setenv("HOTELPRICE_MLFLOW_EXPERIMENT", "test-experiment")
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


def test_training_logs_run_to_mlflow(train_env, sample_csv, tmp_path):
    metrics = run_training()

    # The run is in the configured experiment, in the temp store.
    client = mlflow.MlflowClient(f"sqlite:///{tmp_path / 'mlflow.db'}")
    experiment = client.get_experiment_by_name("test-experiment")
    runs = client.search_runs([experiment.experiment_id])
    assert len(runs) == 1
    run = runs[0]

    # Parameters, metrics and tags.
    assert run.data.params["n_estimators"] == str(XGB_PARAMS["n_estimators"])
    assert run.data.params["random_seed"] == "42"
    assert run.data.params["test_size"] == "0.25"
    assert run.data.params["target"] == "room_price"
    assert run.data.params["features"] == ",".join(FEATURES)
    assert run.data.params["n_rows"] == "20"
    assert run.data.metrics == pytest.approx(metrics)
    assert {"dataset_path", "dataset_dvc_md5", "git_commit"} <= set(run.data.tags)

    # MLflow 3 stores the model as a logged model linked to the run; the preprocessor is a run
    # artifact. The model loads back through the runs:/ URI and predicts.
    assert len(run.outputs.model_outputs) == 1
    assert [a.path for a in client.list_artifacts(run.info.run_id)] == ["preprocessor"]
    mlflow.set_tracking_uri(f"sqlite:///{tmp_path / 'mlflow.db'}")
    model = mlflow.xgboost.load_model(f"runs:/{run.info.run_id}/model")
    preprocessor = joblib.load(
        mlflow.artifacts.download_artifacts(
            f"runs:/{run.info.run_id}/preprocessor/preprocessor.joblib", dst_path=str(tmp_path)
        )
    )
    raw = pd.read_csv(sample_csv)[FEATURES].head(3)
    assert model.predict(preprocessor.transform(raw)).shape == (3,)


def test_two_runs_share_one_experiment(train_env, tmp_path):
    run_training()
    run_training()
    client = mlflow.MlflowClient(f"sqlite:///{tmp_path / 'mlflow.db'}")
    experiment = client.get_experiment_by_name("test-experiment")
    assert len(client.search_runs([experiment.experiment_id])) == 2
