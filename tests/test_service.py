import mlflow
import pytest
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
