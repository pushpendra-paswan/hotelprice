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

Only the ML libraries and pytest are installed at this stage. The other tools are added in their own milestones.

## Repository Structure

```text
.
├── data/                # Dataset (dataset.csv)
├── src/hotelprice/      # Python package: config, data pipeline, training
├── pipelines/           # ML pipeline entry points (training, evaluation)
├── config/              # Configuration files
├── tests/               # pytest tests
├── pyproject.toml       # Project metadata and dependencies
├── PROJECT_CONTEXT.md   # Source of truth for current project state
└── CLAUDE.md            # Project rules and milestone roadmap
```

## Setup

Requires Python 3.10+.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

Run the tests:

```bash
pytest
```

Train and evaluate the model on the real dataset:

```bash
python -m hotelprice.train
```

This prints MAE, RMSE and R² on the test split and saves `model.json`, `preprocessor.joblib` and `metrics.json` to `models/` (git-ignored; override with `HOTELPRICE_MODEL_DIR`).

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
