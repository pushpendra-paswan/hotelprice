# PROJECT_CONTEXT

Source of truth for the current project state. Update after every milestone.

## Current Status

- **Completed:** Milestones 0.1 (project definition and structure), 1.1 (dataset and data pipeline)
- **In progress:** none
- **Next:** Milestone 1.2 (XGBoost training and evaluation pipeline)

## Completed Milestones

### 0.1 Project Definition & Architecture
- Repository structure, Python project config, README, `.gitignore`, and a Git repo (`main` branch).
- `data/dataset.csv` in place, unmodified.
- Dependencies installed and pytest running, with two smoke tests.
- No data pipeline, training, MLflow, BentoML, Docker, DVC, or CI/CD code exists yet.

### 1.1 Dataset & Data Pipeline
- `src/hotelprice/config.py`: column definitions (`TARGET`, `CATEGORICAL_FEATURES`, `NUMERICAL_FEATURES`, `FEATURES`) and env-driven settings (data path, preprocessor path, test size, seed).
- `src/hotelprice/data_pipeline.py`: a single function, `run_data_pipeline()`, written as plain sequential steps (load CSV → select features/target → seeded split → define `ColumnTransformer` inline → fit on train / transform test → save preprocessor with joblib). It returns `X_train, X_test, y_train, y_test, preprocessor`. Runnable with `python -m hotelprice.data_pipeline`.
- `tests/test_data_pipeline.py`: 5 tests (small in-memory sample via env overrides, plus one on the real dataset).
- **Refactor (same milestone):** the earlier `data.py`/`features.py` split (`load_data`, `split_data`, `prepare_data`, `select_features`, `build_preprocessor`, `PreparedData`) was collapsed into `data_pipeline.py`. Behavior is unchanged (same split indices and encoding).
- Nothing was added to the dependencies (`joblib` ships with scikit-learn). No model training, MLflow, BentoML, Docker, DVC, or CI/CD code.

## Architecture

Target pipeline (built up across milestones):

```text
Dataset → DVC → Data/Feature Pipeline → Training → MLflow Tracking
        → MLflow Model Registry → BentoML → Docker → Local Serving

Git → GitHub → GitHub Actions
```

Implemented so far: Dataset → Data/Feature Pipeline (`run_data_pipeline`). Data flow:

```text
data/dataset.csv → read_csv → train_test_split (seeded) → preprocessor.fit(train) → transform(train, test)
                                                        └→ artifacts/preprocessor.joblib
```

## Repository Structure

```text
.
├── data/dataset.csv         # existing dataset, 2,000 rows, read-only
├── src/hotelprice/          # Python package
│   ├── config.py            # column lists + env-driven settings
│   └── data_pipeline.py     # run_data_pipeline(): load, split, preprocess, save
├── pipelines/               # empty (.gitkeep); ML pipeline entry points
├── config/                  # empty (.gitkeep); configuration files
├── tests/test_smoke.py      # package import + dataset schema tests
├── tests/test_data_pipeline.py  # data pipeline tests
├── pyproject.toml
├── README.md
├── PROJECT_CONTEXT.md
├── CLAUDE.md
└── .gitignore
```

## Dataset

- Path: `data/dataset.csv`, 2,000 rows plus a header.
- Columns: `hotel, city, room_type, season, day_of_week, is_holiday, is_weekend, occupancy, demand, booking_lead_time_days, competitor_price, room_price`
- Target: `room_price`. The lead-time column is named `booking_lead_time_days`.
- The dataset was not in the repository when this milestone started. A file with the matching schema was at `~/Desktop/dataset.csv` (outside the repo) and was **copied** into `data/`. The SHA-256 of both copies matches (`afeb014d…82cf2`). The Desktop original was left in place.

### Findings (Milestone 1.1)

- Shape: 2,000 rows × 12 columns. No missing values and no duplicate rows.
- Dtypes: 5 string columns, `is_holiday`/`is_weekend`/`booking_lead_time_days` int64, `occupancy`/`demand`/`competitor_price`/`room_price` float64.
- **Target:** `room_price` (float, mean ≈ 8,139, max ≈ 19,599).
- **Categorical features (5):** `hotel` (6 levels), `city` (6), `room_type` (4), `season` (4), `day_of_week` (7).
- **Numerical features (6):** `is_holiday` (binary), `is_weekend` (binary), `occupancy`, `demand`, `booking_lead_time_days`, `competitor_price`.
- `is_weekend` is fully determined by `day_of_week` (Saturday/Sunday). Both are kept because the spec lists both; trees tolerate the redundancy.
- `hotel` and `city` are independent columns (each hotel appears in several cities), so both are kept.

## Important Decisions

- **Ordinal encoding for categoricals** (`OrdinalEncoder`), numerics passed through unscaled. XGBoost is tree-based, so scaling is unnecessary, and the low cardinality (max 7) makes integer codes cheap and adequate. This avoids one-hot column growth and keeps feature names identical to the raw columns.
- **Unseen categories at inference encode to NaN** (`handle_unknown="use_encoded_value", unknown_value=np.nan`), which XGBoost treats as missing, so serving does not crash on new values.
- **The preprocessor is fit on the training split only**, returned by `run_data_pipeline()`, and saved with joblib to `artifacts/preprocessor.joblib` (git-ignored, path via `HOTELPRICE_PREPROCESSOR_PATH`), so inference can load the exact fitted transformation (no leakage). Registering it with the model is for the MLflow milestones.
- **Plain sequential code, one pipeline file** (per CLAUDE.md): no helper functions or dataclass; the pipeline reads its settings from config/env rather than function arguments, and tests override them with env vars.
- **Configuration via environment variables** with defaults: `HOTELPRICE_DATA_PATH` (default `data/dataset.csv`), `HOTELPRICE_TEST_SIZE` (0.2), `HOTELPRICE_RANDOM_SEED` (42). Function arguments override the env values.
- **No validation or cleaning step**: the data has no missing or duplicate values. A missing column fails with a pandas `KeyError` on selection.

- **Single `pyproject.toml`** (no requirements files), with a `src/` layout and an installable `hotelprice` package. Runtime dependencies are in `[project.dependencies]` and pytest is in the `dev` extra.
- **Dependency bounds are lower bounds only** (`>=`). Exact reproducibility comes later, for example via a lock or the Docker image.
- **`.gitignore` does not ignore `data/dataset.csv`.** Data files will be handled by DVC in milestone 2.2. It ignores models, `mlruns/`, `mlflow.db`, `bentoml/`, `.venv/`, `.env`, and the DVC cache.
- **Configuration** lives in `config/` and secrets come from environment variables. Nothing is configured yet.

## Current Configuration

- Python 3.12.3 (project requires >=3.10).
- Resolved versions in the verified environment: pandas 3.0.6, numpy 2.5.3, scikit-learn 1.9.1, xgboost 3.4.1, pytest 9.1.1.
- pytest: `testpaths = ["tests"]` in `pyproject.toml`.

## Commands

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
pytest

# Run the data pipeline on the real dataset (also saves artifacts/preprocessor.joblib)
python -m hotelprice.data_pipeline

# Optional overrides
HOTELPRICE_DATA_PATH=path/to.csv HOTELPRICE_TEST_SIZE=0.3 HOTELPRICE_RANDOM_SEED=1 HOTELPRICE_PREPROCESSOR_PATH=/tmp/p.joblib python -m hotelprice.data_pipeline
```

## Verification Results (Milestone 0.1)

- `pip install -e ".[dev]"` in a fresh venv succeeded and `pip check` reported no broken requirements.
- `import pandas, numpy, sklearn, xgboost` succeeded.
- `pytest`: 2 passed (`test_package_imports`, `test_dataset_schema`).
- `sha256sum` of `data/dataset.csv` matches the source file.

## Verification Results (Milestone 1.1, after refactor)

- `pytest`: 7 passed (2 smoke + 5 data pipeline).
- `python -m hotelprice.data_pipeline` on the real dataset: X_train (1600, 11), X_test (400, 11); no NaNs; all feature columns numeric; `artifacts/preprocessor.joblib` written.
- Behavior matches the pre-refactor version: same first train indices (968, 240, 819) with seed 42.
- The loaded joblib preprocessor reproduces the training features exactly and encodes an unseen category as NaN (tested).
- `xgboost.DMatrix(X_train, label=y_train)` built from the prepared data before the refactor (input format accepted; no model was trained).

## Known Issues / Limitations

- Dependencies are not pinned to exact versions, so future installs may resolve newer versions.
- `pipelines/` and `config/` are placeholders; settings currently live in `src/hotelprice/config.py` and env vars.
- The preprocessor is saved locally only; logging/registering it with the model is left to the MLflow milestones.
- `run_data_pipeline()` writes the preprocessor file on every call, so it has a side effect (tests redirect it to a temp path).
- `test_real_dataset` reads the real dataset (or `HOTELPRICE_DATA_PATH`) and expects 2,000 rows at the default 0.2 split.
- The dataset had to be sourced from outside the repo (see Dataset). If a different canonical dataset exists, replace it deliberately.

## Next Milestone

**1.2 XGBoost training and evaluation pipeline**: train an `XGBRegressor` on `run_data_pipeline()` output with a fixed seed, evaluate MAE, RMSE, and R² on the test split, and expose a simple training entry point (no MLflow yet).
