"""BentoML service: serves room price predictions from the "champion" model.

Run: bentoml serve hotelprice.service:HotelPriceService
Two loading modes, chosen at startup:
- MODEL_ARTIFACT_DIR set (Docker): load model.json, preprocessor.joblib and metadata.json from that
  directory, written by `python -m hotelprice.export_artifacts`. MLflow is not needed.
- MODEL_ARTIFACT_DIR not set (local): load the champion from the MLflow registry. Requires
  `python -m hotelprice.train`, then `python -m hotelprice.select_model`.
"""

import json
import os
import tempfile
from pathlib import Path

import bentoml
import joblib
import pandas as pd
import xgboost
from pydantic import BaseModel

from hotelprice.config import FEATURES, get_mlflow_tracking_uri, get_registered_model_name

ALIAS = "champion"


# Request: one field per model input feature (names and order match config.FEATURES).
class HotelPriceRequest(BaseModel):
    hotel: str
    city: str
    room_type: str
    season: str
    day_of_week: str
    is_holiday: int
    is_weekend: int
    occupancy: float
    demand: float
    booking_lead_time_days: int
    competitor_price: float


# Response: the predicted price and the registered model version that produced it.
class HotelPriceResponse(BaseModel):
    predicted_room_price: float
    model_version: str


@bentoml.service
class HotelPriceService:
    def __init__(self) -> None:
        artifact_dir = os.environ.get("MODEL_ARTIFACT_DIR")
        if artifact_dir:
            # Docker mode: load the exported snapshot; no MLflow store is needed.
            try:
                self.model_version = str(
                    json.loads((Path(artifact_dir) / "metadata.json").read_text())["model_version"]
                )
                self.model = xgboost.XGBRegressor()
                self.model.load_model(Path(artifact_dir) / "model.json")
                self.preprocessor = joblib.load(Path(artifact_dir) / "preprocessor.joblib")
            except Exception as e:
                raise RuntimeError(
                    f"Could not load model artifacts from MODEL_ARTIFACT_DIR='{artifact_dir}'. "
                    f"Run `python -m hotelprice.export_artifacts` first. ({e})"
                ) from e
            return

        # Local mode: load the champion from the MLflow registry (MLflow is not in the image).
        import mlflow

        # 1. Point MLflow at the tracking store and find the version the champion alias points to.
        mlflow.set_tracking_uri(get_mlflow_tracking_uri())
        name = get_registered_model_name()
        try:
            version = mlflow.MlflowClient().get_model_version_by_alias(name, ALIAS)
        except mlflow.exceptions.MlflowException as e:
            raise RuntimeError(
                f"No '{ALIAS}' alias found for registered model '{name}' in "
                f"{get_mlflow_tracking_uri()}. Run `python -m hotelprice.train` and then "
                f"`python -m hotelprice.select_model` first. ({e})"
            ) from e
        self.model_version = str(version.version)

        # 2. Load the champion model from the registry (once, at startup).
        try:
            self.model = mlflow.xgboost.load_model(f"models:/{name}@{ALIAS}")
        except Exception as e:
            raise RuntimeError(
                f"Could not load model 'models:/{name}@{ALIAS}' (version {self.model_version}): {e}"
            ) from e

        # 3. Download the fitted preprocessor logged in the same run as that model version.
        try:
            with tempfile.TemporaryDirectory() as tmp_dir:
                preprocessor_path = mlflow.artifacts.download_artifacts(
                    f"runs:/{version.run_id}/preprocessor/preprocessor.joblib", dst_path=tmp_dir
                )
                self.preprocessor = joblib.load(preprocessor_path)
        except Exception as e:
            raise RuntimeError(
                f"Could not load the preprocessor for '{name}' version {self.model_version} "
                f"(run {version.run_id}): {e}"
            ) from e

    @bentoml.api(input_spec=HotelPriceRequest)
    def predict(self, **params) -> HotelPriceResponse:
        # 1. Build a one-row DataFrame in the canonical feature order.
        row = pd.DataFrame([params])[FEATURES]

        # 2. Apply the fitted preprocessor (unknown categories become NaN).
        features = self.preprocessor.transform(row)

        # 3. Predict and return the price with the model version that produced it.
        price = float(self.model.predict(features)[0])
        return HotelPriceResponse(predicted_room_price=price, model_version=self.model_version)
