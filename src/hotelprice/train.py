"""Training pipeline: train an XGBoost regressor, evaluate it, save the artifacts, log to MLflow."""

import json
import subprocess

import joblib
import mlflow
import mlflow.xgboost
import numpy as np
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from xgboost import XGBRegressor

from hotelprice.config import (
    FEATURES,
    PROJECT_ROOT,
    TARGET,
    XGB_PARAMS,
    get_data_path,
    get_mlflow_artifact_dir,
    get_mlflow_experiment_name,
    get_mlflow_tracking_uri,
    get_model_dir,
    get_random_seed,
    get_test_size,
)
from hotelprice.data_pipeline import run_data_pipeline


def run_training():
    """Train and evaluate the model, save artifacts to the model dir, log the run to MLflow.

    Returns the metrics.
    """
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

    # 5. Find the dataset version (md5 from the DVC pointer file, if there is one).
    data_path = get_data_path()
    dvc_file = data_path.with_name(data_path.name + ".dvc")
    dataset_md5 = "unknown"
    if dvc_file.is_file():
        for line in dvc_file.read_text().splitlines():
            if "md5:" in line:
                dataset_md5 = line.split("md5:")[1].strip()
                break

    # 6. Find the Git commit of the code (unknown if git is not available).
    try:
        git_commit = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        git_commit = "unknown"

    # 7. Point MLflow at the local store; create the experiment with our artifact directory
    #    the first time (an existing experiment keeps its original artifact location).
    mlflow.set_tracking_uri(get_mlflow_tracking_uri())
    experiment_name = get_mlflow_experiment_name()
    experiment = mlflow.get_experiment_by_name(experiment_name)
    if experiment is None:
        experiment_id = mlflow.create_experiment(
            experiment_name, artifact_location=get_mlflow_artifact_dir().resolve().as_uri()
        )
    else:
        experiment_id = experiment.experiment_id

    # 8. Log the run: parameters, metrics, tags, the XGBoost model and the fitted preprocessor.
    with mlflow.start_run(experiment_id=experiment_id):
        mlflow.log_params(XGB_PARAMS)
        mlflow.log_param("random_seed", get_random_seed())
        mlflow.log_param("test_size", get_test_size())
        mlflow.log_param("target", TARGET)
        mlflow.log_param("features", ",".join(FEATURES))
        mlflow.log_param("n_rows", len(X_train) + len(X_test))
        mlflow.log_param("n_train_rows", len(X_train))
        mlflow.log_param("n_test_rows", len(X_test))
        mlflow.log_metrics(metrics)
        mlflow.set_tags(
            {
                "dataset_path": str(data_path),
                "dataset_dvc_md5": dataset_md5,
                "git_commit": git_commit,
            }
        )
        mlflow.xgboost.log_model(model, name="model")
        mlflow.log_artifact(str(model_dir / "preprocessor.joblib"), artifact_path="preprocessor")

    return metrics


if __name__ == "__main__":
    results = run_training()
    print("Test set metrics")
    print(f"  MAE : {results['mae']:.2f}")
    print(f"  RMSE: {results['rmse']:.2f}")
    print(f"  R²  : {results['r2']:.4f}")
    print(f"Artifacts saved to {get_model_dir()}")
    print(f"MLflow run logged to {get_mlflow_tracking_uri()}")
    print(f"MLflow experiment: {get_mlflow_experiment_name()}")
