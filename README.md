# Dynamic Hotel Price Prediction Platform

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

Only the ML libraries, DVC, pytest and Ruff (dev) are installed at this stage. The other tools are added in their own milestones.

## Repository Structure

```text
.
├── data/                # Dataset (dataset.csv is DVC-tracked; dataset.csv.dvc is in Git)
├── src/hotelprice/      # Python package: config, data pipeline, training
├── pipelines/           # ML pipeline entry points (training, evaluation)
├── config/              # Configuration files
├── tests/               # pytest tests
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

Training prints MAE, RMSE and R² on the test split and saves `model.json`, `preprocessor.joblib` and `metrics.json` to `models/` (git-ignored).

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

### Configuration

Settings are read from environment variables and all have defaults, so none are required. See `.env.example` for the list (`HOTELPRICE_DATA_PATH`, `HOTELPRICE_PREPROCESSOR_PATH`, `HOTELPRICE_MODEL_DIR`, `HOTELPRICE_TEST_SIZE`, `HOTELPRICE_RANDOM_SEED`). The code does not load `.env` files itself; export the variables in your shell, e.g. `HOTELPRICE_RANDOM_SEED=1 python -m hotelprice.train`.

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
