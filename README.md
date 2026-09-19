# Dynamic Hotel Price Prediction Platform

[![CI](https://github.com/pushpendra-paswan/hotelprice/actions/workflows/ci.yml/badge.svg)](https://github.com/pushpendra-paswan/hotelprice/actions/workflows/ci.yml)

An end-to-end ML/MLOps project that predicts hotel room prices and covers the full lifecycle: data versioning, training, experiment tracking, model registry, serving, containerization, and CI/CD. The ML is intentionally simple (XGBoost regression); the focus is the MLOps lifecycle.

**Version 1 is local development and local serving only.**

## ML Problem

- **Target:** `room_price`
- **Features:** `hotel`, `city`, `room_type`, `season`, `day_of_week`, `is_holiday`, `is_weekend`, `occupancy`, `demand`, `booking_lead_time_days`, `competitor_price`
- **Model:** XGBoost regression
- **Metrics:** MAE, RMSE, R²
- **Dataset:** `data/dataset.csv` (2,000 rows). It is treated as read-only input.

## Architecture

```text
Dataset → DVC → Data/Feature Pipeline → Training → MLflow Tracking
        → MLflow Model Registry → BentoML → Docker → Local Serving

Git → GitHub → GitHub Actions (tests, code quality, ML validation,
                               Docker build, versioned image build/publish)
```

## Tech Stack

| Area | Tools |
|------|-------|
| ML | Python, Pandas, NumPy, Scikit-learn, XGBoost |
| Versioning | Git, GitHub, DVC (local) |
| Tracking & registry | MLflow, MLflow Model Registry |
| Serving | BentoML |
| Containers | Docker |
| CI/CD | GitHub Actions |

Only the ML libraries, DVC, MLflow, pytest and Ruff (dev) are installed at this stage. The other tools are added in their own milestones.

## Repository Structure

```text
.
├── data/                # Dataset (dataset.csv is DVC-tracked; dataset.csv.dvc is in Git)
├── src/hotelprice/      # Python package: config, data pipeline, training, model selection, artifact export, BentoML service
├── pipelines/           # ML pipeline entry points (training, evaluation)
├── config/              # Configuration files
├── tests/               # pytest tests; tests/fixtures/hotel_sample.csv is the small dataset used by CI
├── .github/workflows/   # GitHub Actions CI (ci.yml)
├── Dockerfile, .dockerignore, requirements-serving.txt   # serving image (needs serving_artifacts/)
├── dvc.yaml             # DVC pipeline (train stage); dvc.lock pins its inputs/outputs
├── .env.example         # Configurable environment variables (all optional)
├── pyproject.toml       # Project metadata and dependencies
├── PROJECT_CONTEXT.md   # Source of truth for current project state
└── CLAUDE.md            # Project rules and milestone roadmap
```

## Development

Requires Python 3.10+. Run everything from the repository root.

```bash
# Install (runtime + dev dependencies: pytest, ruff)
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

# Run the tests
pytest

# Lint and format checks (ruff)
ruff check .
ruff format --check .

# Apply fixes
ruff check --fix .
ruff format .

# Train and evaluate on the real dataset
python -m hotelprice.train
```

Training prints MAE, RMSE and R² on the test split and saves `model.json`, `preprocessor.joblib` and `metrics.json` to `models/` (git-ignored except `metrics.json`) and logs the run to MLflow.

### Experiment tracking (MLflow)

Every training run (`python -m hotelprice.train`, or the DVC `train` stage) is logged to a local MLflow tracking store: a SQLite database (`mlflow.db`) plus an artifact directory (`mlartifacts/`), both git-ignored. SQLite is used instead of the plain file store so the Model Registry works. Runs go to the experiment `hotel-price-prediction`.

Each run logs:

- **Parameters:** the XGBoost hyperparameters, `random_seed`, `test_size`, `target`, `features`, `n_rows`, `n_train_rows`, `n_test_rows`
- **Metrics:** `mae`, `rmse`, `r2` (test set)
- **Tags:** `dataset_path`, `dataset_dvc_md5` (from `data/dataset.csv.dvc`), `git_commit`
- **Model:** the XGBoost model (`mlflow.xgboost.log_model`, name `model`)
- **Preprocessor:** `preprocessor/preprocessor.joblib` as a run artifact

`models/model.json`, `models/preprocessor.joblib` and `models/metrics.json` are still written, so the DVC stage is unchanged.

```bash
# Train (logs a new run each time)
python -m hotelprice.train

# Open the MLflow UI at http://127.0.0.1:5000 (run from the repository root)
mlflow ui --backend-store-uri sqlite:///mlflow.db
```

Load a logged model back (replace `<run_id>` with a run ID from the UI):

```python
import mlflow, mlflow.xgboost

mlflow.set_tracking_uri("sqlite:///mlflow.db")
model = mlflow.xgboost.load_model("runs:/<run_id>/model")
```

MLflow settings (all optional): `HOTELPRICE_MLFLOW_TRACKING_URI` (default `sqlite:///<repo>/mlflow.db`), `HOTELPRICE_MLFLOW_ARTIFACT_DIR` (default `<repo>/mlartifacts`), `HOTELPRICE_MLFLOW_EXPERIMENT` (default `hotel-price-prediction`). The artifact directory only applies when the experiment is first created; an existing experiment keeps its original location. If you change the tracking URI, start the UI with the same `--backend-store-uri`.

### Model Registry (MLflow)

Every training run also registers its model in the MLflow Model Registry (same SQLite store) under the name `hotel-price-model`. Each run creates a new version linked to its run, so the run ID, metrics, params and the preprocessor artifact are reachable from the version. Versions are selected with **aliases** (not the deprecated Staging/Production stages): the alias `champion` marks the version to use.

```bash
# Register: every training run adds a new version
python -m hotelprice.train

# List versions (run ID, metrics, aliases) and set "champion" on version 2
python -m hotelprice.select_model 2

# No argument = the latest version
python -m hotelprice.select_model
```

The registry and its aliases are also visible in the MLflow UI under the **Models** tab.

Load the champion model and its matching preprocessor (the BentoML service below loads them the same way):

```python
import joblib, mlflow, mlflow.xgboost, pandas as pd
from hotelprice.config import FEATURES

mlflow.set_tracking_uri("sqlite:///mlflow.db")
client = mlflow.MlflowClient()

# Model: the alias URI always resolves to the currently selected version.
model = mlflow.xgboost.load_model("models:/hotel-price-model@champion")

# Preprocessor: resolve the champion version, then use its linked run ID.
version = client.get_model_version_by_alias("hotel-price-model", "champion")
path = mlflow.artifacts.download_artifacts(
    f"runs:/{version.run_id}/preprocessor/preprocessor.joblib"
)
preprocessor = joblib.load(path)

raw_rows = pd.read_csv("data/dataset.csv").head(3)
predictions = model.predict(preprocessor.transform(raw_rows[FEATURES]))
```

The registered name is set with `HOTELPRICE_MLFLOW_MODEL_NAME` (default `hotel-price-model`).

### Serving (BentoML)

`src/hotelprice/service.py` is a single-file BentoML service. At startup it loads the `champion` model from the MLflow Model Registry (`models:/<name>@champion`) and the fitted preprocessor logged with that model version's run, then serves one prediction endpoint. It fails at startup with a clear error if the alias, model or preprocessor is missing.

**A champion model must exist before serving:** train, then select a version.

```bash
python -m hotelprice.train             # registers a new model version
python -m hotelprice.select_model      # sets the "champion" alias (latest version, or pass a number)
bentoml serve hotelprice.service:HotelPriceService    # http://localhost:3000
```

Environment variables (all optional, see `.env.example`): `HOTELPRICE_MLFLOW_TRACKING_URI` (default: the repo's `mlflow.db`) and `HOTELPRICE_MLFLOW_MODEL_NAME` (default `hotel-price-model`). Without `MODEL_ARTIFACT_DIR` the service reads the local MLflow store, so it must run where that store and its artifacts exist. With `MODEL_ARTIFACT_DIR` set it loads exported files instead (see Docker below).

Example request (a row from the dataset; all 11 feature fields are required):

```bash
curl -X POST http://localhost:3000/predict \
  -H 'Content-Type: application/json' \
  -d '{"hotel": "The Meridian", "city": "Bengaluru", "room_type": "Standard",
       "season": "Shoulder", "day_of_week": "Wednesday", "is_holiday": 0, "is_weekend": 0,
       "occupancy": 10.0, "demand": 45.96, "booking_lead_time_days": 16,
       "competitor_price": 6791.59}'
```

```json
{"predicted_room_price": 5867.1142578125, "model_version": "2"}
```

Unknown categories (e.g. a new hotel name) are accepted and encoded as missing by the preprocessor. A missing field or wrong type returns HTTP 400 with the validation details. Health endpoints: `GET /livez` and `GET /readyz`.

### Docker

The image is self-contained: it holds the service code and a **snapshot of the champion model** exported from the MLflow registry. It does not contain MLflow, DVC, `mlflow.db`, the dataset or any secrets, and needs nothing from the host at runtime. Inside the image `MODEL_ARTIFACT_DIR` is set, so the service loads `model.json`, `preprocessor.joblib` and `metadata.json` from that directory (the model version in each response comes from `metadata.json`). Without `MODEL_ARTIFACT_DIR` (local development) the service loads from MLflow as described above.

```bash
python -m hotelprice.train                            # 1. train (registers a new model version)
python -m hotelprice.select_model                     # 2. set the champion alias (or pass a version)
python -m hotelprice.export_artifacts                 # 3. write serving_artifacts/ (git-ignored)
docker build -t hotel-price-service:local .           # 4. build the image
docker run --rm -p 3000:3000 hotel-price-service:local    # 5. serve on http://localhost:3000
```

The request and response are the same as above:

```bash
curl -X POST http://localhost:3000/predict -H 'Content-Type: application/json' \
  -d '{"hotel": "The Meridian", "city": "Bengaluru", "room_type": "Standard", "season": "Shoulder", "day_of_week": "Wednesday", "is_holiday": 0, "is_weekend": 0, "occupancy": 10.0, "demand": 45.96, "booking_lead_time_days": 16, "competitor_price": 6791.59}'
# {"predicted_room_price": 5867.1142578125, "model_version": "2"}
```

`GET /livez` and `GET /readyz` work as before, and the image has a `HEALTHCHECK` on `/livez` (`docker ps` shows `healthy`).

| Variable | Where | Meaning |
|----------|-------|---------|
| `MODEL_ARTIFACT_DIR` | image (`/app/serving_artifacts`) | Set: load the exported snapshot from this directory. Unset: load the champion from MLflow. |
| `HOTELPRICE_MLFLOW_TRACKING_URI`, `HOTELPRICE_MLFLOW_MODEL_NAME` | export script and local serving | Which registry to read. Not used inside the container. |

**Rebuild rule:** the image contains the champion as it was when you ran `export_artifacts`. If you train a new model or move the `champion` alias, re-run `export_artifacts` and `docker build`; a running or already built image never changes. `requirements-serving.txt` pins the library versions used for training (the preprocessor and model must load with compatible versions); update it if the training environment changes. It uses `xgboost-cpu`, the CPU-only build of the same XGBoost release, which keeps the image about 700 MB smaller than the default `xgboost` wheel (GPU libraries).

### Data versioning and pipeline (DVC)

`data/dataset.csv` is tracked by DVC, not Git. Git stores only the small pointer `data/dataset.csv.dvc`; the file itself lives in the local DVC cache and a local remote. The `train` stage in `dvc.yaml` runs `python -m hotelprice.train`. `models/model.json` and `models/preprocessor.joblib` are DVC outputs, and `models/metrics.json` is a DVC metric that is kept in Git.

**Set up your own local remote** (once per clone). The remote path is machine-specific, so it goes in `.dvc/config.local`, which is git-ignored:

```bash
mkdir -p ~/dvc-remotes/hotelprice
dvc remote add -d --local localstorage ~/dvc-remotes/hotelprice
```

Use any directory outside the repository. To get the dataset from a copy of the remote that another developer shares (for example a shared folder), point the remote at that directory instead.

```bash
dvc pull               # download the dataset (and models) from the remote into the workspace
dvc push               # upload new or changed DVC-tracked data to the remote
dvc repro              # run the train stage; does nothing if inputs are unchanged
dvc checkout           # after `git checkout <commit>`, restore the data that commit points to
dvc metrics show       # print models/metrics.json
dvc metrics diff       # compare metrics with the last Git commit (or pass two revisions)
```

To change the dataset: edit it, run `dvc add data/dataset.csv`, then `git add data/dataset.csv.dvc` and commit, and `dvc push` to upload the new version.

### Continuous integration (GitHub Actions)

`.github/workflows/ci.yml` runs on every pull request and on every push to `main`. A new push to the same branch cancels the run in progress. It needs no secrets and no setup, so it also works on forks.

CI only has what is in Git, so it never uses DVC or the real dataset (`data/dataset.csv`, `mlflow.db`, `models/` and `serving_artifacts/` are not in Git). It uses `tests/fixtures/hotel_sample.csv` instead: a fixed-seed sample of 300 rows of the real dataset with the same columns and dtypes. The fixture is plain Git, not DVC-tracked.

| Job | What it does |
|-----|--------------|
| `test` | `pip install -e ".[dev]"`, `ruff check .`, `ruff format --check .`, `pytest` |
| `ml-validation-and-docker` (after `test` passes) | trains on the fixture into a temporary MLflow SQLite store and fails if `metrics.json` is missing or MAE, RMSE or R² is not finite; sets the `champion` alias; exports `serving_artifacts/`; builds `hotel-price-service:ci` (not pushed); starts the container, waits for `/readyz`, checks that one valid `/predict` returns a numeric price and one invalid request gets a 4xx, then stops it (container logs are printed on failure) |

Run the same checks locally (from a clean clone, without the real dataset, in a virtual environment):

```bash
pip install -e ".[dev]"
ruff check . && ruff format --check . && pytest

# ML validation and Docker build, using the fixture and a throwaway MLflow store
export HOTELPRICE_DATA_PATH=tests/fixtures/hotel_sample.csv
export HOTELPRICE_MLFLOW_TRACKING_URI=sqlite:///$PWD/mlflow.db   # use a temp dir to keep your own runs separate
export HOTELPRICE_MODEL_DIR=$PWD/ci-models
python -m hotelprice.train
python -m hotelprice.select_model
python -m hotelprice.export_artifacts
docker build -t hotel-price-service:ci .
```

Note that this writes to `mlflow.db`, `mlartifacts/` and `serving_artifacts/` in the working directory, so run it in a scratch clone if you already have your own MLflow runs. The container smoke test is the last step of the workflow file; run the container as in the Docker section and call `/predict` with a fixture row.

### Configuration

Settings are read from environment variables and all have defaults, so none are required. See `.env.example` for the list (`HOTELPRICE_DATA_PATH`, `HOTELPRICE_PREPROCESSOR_PATH`, `HOTELPRICE_MODEL_DIR`, `HOTELPRICE_TEST_SIZE`, `HOTELPRICE_RANDOM_SEED`, plus the `HOTELPRICE_MLFLOW_*` variables above, including `HOTELPRICE_MLFLOW_MODEL_NAME`). The code does not load `.env` files itself; export the variables in your shell, e.g. `HOTELPRICE_RANDOM_SEED=1 python -m hotelprice.train`.

## Roadmap

| Milestone | Scope |
|-----------|-------|
| 0.1 | Project definition and structure |
| 1.1 | Data loading, preprocessing, train/test split |
| 1.2 | XGBoost training and evaluation pipeline |
| 2.1 | Git workflow and project quality |
| 2.2 | DVC dataset versioning |
| 3.1 | MLflow experiment tracking |
| 3.2 | MLflow Model Registry |
| 4.1 | BentoML service |
| 4.2 | Dockerize the BentoML service |
| 5.1 | GitHub Actions CI |
| 5.2 | GitHub Actions CD |

See `PROJECT_CONTEXT.md` for the current status.
