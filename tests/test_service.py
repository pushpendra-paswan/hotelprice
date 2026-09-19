import json
import runpy
import sys

import joblib
import mlflow
import pandas as pd
import pytest
import xgboost
from starlette.testclient import TestClient

from hotelprice.config import FEATURES
from hotelprice.service import HotelPriceRequest, HotelPriceService
from hotelprice.train import run_training

ROW = {
    "hotel": "A",
    "city": "Goa",
    "room_type": "Suite",
    "season": "Peak",
    "day_of_week": "Saturday",
    "is_holiday": 1,
    "is_weekend": 1,
    "occupancy": 70.0,
    "demand": 80.0,
    "booking_lead_time_days": 5,
    "competitor_price": 6000.0,
}


@pytest.fixture
def mlflow_env(sample_csv, tmp_path, monkeypatch):
    """Point everything at a temp MLflow store; no training or registry yet."""
    monkeypatch.setenv("HOTELPRICE_DATA_PATH", str(sample_csv))
    monkeypatch.setenv("HOTELPRICE_PREPROCESSOR_PATH", str(tmp_path / "pipeline.joblib"))
    monkeypatch.setenv("HOTELPRICE_MODEL_DIR", str(tmp_path / "models"))
    monkeypatch.setenv("HOTELPRICE_TEST_SIZE", "0.25")
    monkeypatch.setenv("HOTELPRICE_MLFLOW_TRACKING_URI", f"sqlite:///{tmp_path / 'mlflow.db'}")
    monkeypatch.setenv("HOTELPRICE_MLFLOW_ARTIFACT_DIR", str(tmp_path / "mlartifacts"))
    monkeypatch.setenv("HOTELPRICE_MLFLOW_EXPERIMENT", "test-experiment")
    monkeypatch.setenv("HOTELPRICE_MLFLOW_MODEL_NAME", "test-model")
    return mlflow.MlflowClient(f"sqlite:///{tmp_path / 'mlflow.db'}")


@pytest.fixture
def champion_env(mlflow_env):
    """Train once into the temp store and set the champion alias on the new version."""
    run_training()
    mlflow_env.set_registered_model_alias("test-model", "champion", "1")


def test_request_fields_match_feature_config():
    assert list(HotelPriceRequest.model_fields) == FEATURES


def test_service_loads_champion_model(champion_env):
    service = HotelPriceService.inner()
    assert service.model_version == "1"
    assert service.model is not None
    assert service.preprocessor is not None


def test_valid_request_returns_float_prediction(champion_env):
    service = HotelPriceService.inner()
    response = service.predict(**ROW)
    assert isinstance(response.predicted_room_price, float)
    assert response.model_version == "1"

    # An unseen category is encoded as NaN by the preprocessor and must not crash.
    unseen = service.predict(**{**ROW, "hotel": "Unknown Hotel", "city": "Atlantis"})
    assert isinstance(unseen.predicted_room_price, float)


def test_invalid_request_is_rejected_over_http(champion_env):
    with TestClient(HotelPriceService.to_asgi()) as client:
        ok = client.post("/predict", json=ROW)
        assert ok.status_code == 200
        assert isinstance(ok.json()["predicted_room_price"], float)

        missing = client.post("/predict", json={"hotel": "A"})
        assert missing.status_code == 400

        wrong_type = client.post("/predict", json={**ROW, "occupancy": "high"})
        assert wrong_type.status_code == 400

        # The service is still healthy after invalid requests.
        assert client.get("/livez").status_code == 200


def test_service_fails_clearly_without_champion(mlflow_env):
    run_training()  # a version exists, but no alias has been set
    with pytest.raises(RuntimeError, match="select_model"):
        HotelPriceService.inner()


def export(monkeypatch, out_dir):
    monkeypatch.setattr(sys, "argv", ["export_artifacts", str(out_dir)])
    runpy.run_module("hotelprice.export_artifacts", run_name="__main__")


def test_export_writes_champion_artifacts(champion_env, tmp_path, monkeypatch):
    export(monkeypatch, tmp_path / "out")

    metadata = json.loads((tmp_path / "out" / "metadata.json").read_text())
    assert metadata["model_name"] == "test-model"
    assert metadata["model_version"] == "1"

    # The exported files load on their own and predict from a raw row.
    model = xgboost.XGBRegressor()
    model.load_model(tmp_path / "out" / "model.json")
    preprocessor = joblib.load(tmp_path / "out" / "preprocessor.joblib")
    assert model.predict(preprocessor.transform(pd.DataFrame([ROW])[FEATURES])).shape == (1,)


def test_export_fails_clearly_without_champion(mlflow_env, tmp_path, monkeypatch):
    run_training()  # a version exists, but no alias has been set
    with pytest.raises(SystemExit, match="select_model"):
        export(monkeypatch, tmp_path / "out")
    assert not (tmp_path / "out" / "model.json").exists()


def test_service_loads_from_artifact_dir_without_mlflow(champion_env, tmp_path, monkeypatch):
    mlflow_prediction = HotelPriceService.inner().predict(**ROW).predicted_room_price
    export(monkeypatch, tmp_path / "out")

    # Docker mode: the MLflow store is pointed at nothing, so only the exported files can be used.
    monkeypatch.setenv("MODEL_ARTIFACT_DIR", str(tmp_path / "out"))
    monkeypatch.setenv("HOTELPRICE_MLFLOW_TRACKING_URI", f"sqlite:///{tmp_path / 'missing.db'}")
    service = HotelPriceService.inner()
    response = service.predict(**ROW)
    assert response.model_version == "1"
    assert response.predicted_room_price == mlflow_prediction
    assert not (tmp_path / "missing.db").exists()


def test_service_fails_clearly_with_empty_artifact_dir(tmp_path, monkeypatch):
    monkeypatch.setenv("MODEL_ARTIFACT_DIR", str(tmp_path))
    with pytest.raises(RuntimeError, match="export_artifacts"):
        HotelPriceService.inner()
