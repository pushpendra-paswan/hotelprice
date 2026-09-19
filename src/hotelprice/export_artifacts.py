"""Export the champion model and its preprocessor from the MLflow registry for the Docker image.

Usage: python -m hotelprice.export_artifacts [OUTPUT_DIR]   (default: serving_artifacts/)
Writes model.json (native XGBoost), preprocessor.joblib and metadata.json to OUTPUT_DIR.
Re-run it (and rebuild the image) whenever the champion changes.
"""

import json
import shutil
import sys
import tempfile
from pathlib import Path

import mlflow

from hotelprice.config import PROJECT_ROOT, get_mlflow_tracking_uri, get_registered_model_name

ALIAS = "champion"

# 1. Resolve the champion alias to a registered model version (and the run that produced it).
mlflow.set_tracking_uri(get_mlflow_tracking_uri())
name = get_registered_model_name()
try:
    version = mlflow.MlflowClient().get_model_version_by_alias(name, ALIAS)
except mlflow.exceptions.MlflowException as e:
    sys.exit(
        f"No '{ALIAS}' alias found for registered model '{name}' in {get_mlflow_tracking_uri()}. "
        f"Run `python -m hotelprice.train` and then `python -m hotelprice.select_model` first. "
        f"({e})"
    )

# 2. Write the model as a native XGBoost file and the preprocessor from the same run.
out_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else PROJECT_ROOT / "serving_artifacts"
out_dir.mkdir(parents=True, exist_ok=True)
mlflow.xgboost.load_model(f"models:/{name}@{ALIAS}").save_model(out_dir / "model.json")
with tempfile.TemporaryDirectory() as tmp_dir:
    preprocessor_path = mlflow.artifacts.download_artifacts(
        f"runs:/{version.run_id}/preprocessor/preprocessor.joblib", dst_path=tmp_dir
    )
    shutil.copy(preprocessor_path, out_dir / "preprocessor.joblib")

# 3. Record which registered version this snapshot is (the service reports it in every response).
metadata = {"model_name": name, "model_version": str(version.version), "run_id": version.run_id}
(out_dir / "metadata.json").write_text(json.dumps(metadata, indent=2) + "\n")
print(f"Exported '{name}' version {version.version} ({ALIAS}) to {out_dir}")
