"""Training pipeline: train an XGBoost regressor, evaluate it, and save the artifacts."""

import json

import joblib
import numpy as np
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from xgboost import XGBRegressor

from hotelprice.config import XGB_PARAMS, get_model_dir, get_random_seed
from hotelprice.data_pipeline import run_data_pipeline


def run_training():
    """Train and evaluate the model, save artifacts to the model dir, and return the metrics."""
    # 1. Get the prepared train/test data and the fitted preprocessor from the data pipeline.
    X_train, X_test, y_train, y_test, preprocessor = run_data_pipeline()

    # 2. Train the XGBoost regressor with the configured hyperparameters and seed.
    model = XGBRegressor(**XGB_PARAMS, random_state=get_random_seed())
    model.fit(X_train, y_train)

    # 3. Evaluate on the test set.
    predictions = model.predict(X_test)
    metrics = {
        "mae": float(mean_absolute_error(y_test, predictions)),
        "rmse": float(np.sqrt(mean_squared_error(y_test, predictions))),
        "r2": float(r2_score(y_test, predictions)),
    }

    # 4. Save the model, the fitted preprocessor and the metrics together.
    model_dir = get_model_dir()
    model_dir.mkdir(parents=True, exist_ok=True)
    model.save_model(model_dir / "model.json")
    joblib.dump(preprocessor, model_dir / "preprocessor.joblib")
    (model_dir / "metrics.json").write_text(json.dumps(metrics, indent=2))

    return metrics


if __name__ == "__main__":
    results = run_training()
    print("Test set metrics")
    print(f"  MAE : {results['mae']:.2f}")
    print(f"  RMSE: {results['rmse']:.2f}")
    print(f"  R²  : {results['r2']:.4f}")
    print(f"Artifacts saved to {get_model_dir()}")
