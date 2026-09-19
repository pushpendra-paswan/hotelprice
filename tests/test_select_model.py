import runpy
import sys

import joblib
import mlflow
import pandas as pd
import pytest

from hotelprice.config import FEATURES
from hotelprice.train import run_training


@pytest.fixture
def two_versions(sample_csv, tmp_path, monkeypatch):
    """Train twice into a temp MLflow store so the registry has versions 1 and 2."""
    monkeypatch.setenv("HOTELPRICE_DATA_PATH", str(sample_csv))
    monkeypatch.setenv("HOTELPRICE_PREPROCESSOR_PATH", str(tmp_path / "pipeline.joblib"))
    monkeypatch.setenv("HOTELPRICE_MODEL_DIR", str(tmp_path / "models"))
    monkeypatch.setenv("HOTELPRICE_TEST_SIZE", "0.25")
    monkeypatch.setenv("HOTELPRICE_MLFLOW_TRACKING_URI", f"sqlite:///{tmp_path / 'mlflow.db'}")
    monkeypatch.setenv("HOTELPRICE_MLFLOW_ARTIFACT_DIR", str(tmp_path / "mlartifacts"))
    monkeypatch.setenv("HOTELPRICE_MLFLOW_EXPERIMENT", "test-experiment")
    monkeypatch.setenv("HOTELPRICE_MLFLOW_MODEL_NAME", "test-model")
    run_training()
    run_training()
    return mlflow.MlflowClient(f"sqlite:///{tmp_path / 'mlflow.db'}")


def select(monkeypatch, *args):
    monkeypatch.setattr(sys, "argv", ["select_model", *args])
    runpy.run_module("hotelprice.select_model", run_name="__main__")


def test_alias_controls_loaded_model(two_versions, sample_csv, tmp_path, monkeypatch):
    client = two_versions
    raw = pd.read_csv(sample_csv)[FEATURES].head(3)

    for version in ["1", "2"]:
        select(monkeypatch, version)

        # The alias resolves to the chosen version, and the model loads through the alias URI.
        model_version = client.get_model_version_by_alias("test-model", "champion")
        assert str(model_version.version) == version
        model = mlflow.xgboost.load_model("models:/test-model@champion")

        # The preprocessor is found through the run ID linked to that version.
        preprocessor = joblib.load(
            mlflow.artifacts.download_artifacts(
                f"runs:/{model_version.run_id}/preprocessor/preprocessor.joblib",
                dst_path=str(tmp_path / f"pre{version}"),
            )
        )
        assert model.predict(preprocessor.transform(raw)).shape == (3,)


def test_no_argument_selects_latest_version(two_versions, monkeypatch, capsys):
    select(monkeypatch)
    assert two_versions.get_model_version_by_alias("test-model", "champion").version == 2
    assert "run_id=" in capsys.readouterr().out
