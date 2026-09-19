# PROJECT_CONTEXT

Source of truth for the current project state. Update after every milestone.

## Current Status

- **Completed:** Milestones 0.1 (project definition and structure), 1.1 (dataset and data pipeline), 1.2 (XGBoost training and evaluation), 2.1 (Git and project quality)
- **In progress:** none
- **Next:** Milestone 2.2 (DVC dataset versioning)

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

### 1.2 XGBoost Training & Evaluation Pipeline
- `src/hotelprice/train.py`: a single function, `run_training()`, as plain sequential steps (call `run_data_pipeline()` → fit `XGBRegressor(**XGB_PARAMS, random_state=seed)` → predict on test → MAE/RMSE/R² with scikit-learn → save artifacts). Runnable with `python -m hotelprice.train`, which prints the metrics.
- `config.py` gained `XGB_PARAMS` (hyperparameters), `get_model_dir()` (env `HOTELPRICE_MODEL_DIR`, default `models/`). The existing `get_random_seed()` (default 42) seeds both the split and the model.
- Artifacts in `models/` (git-ignored): `model.json` (native XGBoost format), `preprocessor.joblib` (same fitted preprocessor), `metrics.json` (`mae`, `rmse`, `r2`).
- `tests/test_train.py`: 4 tests on a small in-memory sample (artifacts created, metrics finite and match the JSON, saved model + preprocessor predict from raw rows, training is reproducible). The `sample_csv` fixture moved from `test_data_pipeline.py` to `tests/conftest.py` so both test files share it.
- No tuning, cross-validation, extra models, feature engineering, MLflow, BentoML, Docker, DVC, or CI/CD.

### 2.1 Git & Project Quality
- **Repo review:** layout is consistent (`src/hotelprice/`, `tests/`, `data/`, `config/`, `pipelines/`); no reorganization was needed.
- **`.gitignore` review:** already covered caches, `.venv/`, `models/`, `artifacts/`, `*.joblib`, `mlruns/`, `mlflow.db`, `bentoml/`, `.env`/`.env.*` (except `.env.example`), and `.ruff_cache/`. No change was needed. `git ls-files` showed only source, tests, config placeholders, docs and `data/dataset.csv` (still tracked until 2.2), so nothing had to be removed from the index.
- **Ruff** added as a dev dependency only (`ruff>=0.6`; 0.16.8 was installed). Config in `pyproject.toml`: `line-length = 100`, rules `E, F, I, UP, B`. It reported two over-long lines (`config.py`, `tests/test_train.py`); `ruff format` fixed both. No logic changed.
- **README** now has a Development section (install, test, lint/format check, apply fixes, train) and a Configuration section.
- **`.env.example`** lists the five `HOTELPRICE_*` variables read by `config.py`, with their defaults. The code reads `os.environ` only and does not load `.env` files (no python-dotenv, per the dependency rule), so variables must be exported in the shell.
- **Commits:** two focused commits (`Add Ruff for linting and formatting`, `Document development commands and add .env.example`) plus this context update. Nothing was pushed.
- No DVC, MLflow, BentoML, Docker or CI/CD.

## Architecture

Target pipeline (built up across milestones):

```text
Dataset → DVC → Data/Feature Pipeline → Training → MLflow Tracking
        → MLflow Model Registry → BentoML → Docker → Local Serving

Git → GitHub → GitHub Actions
```

Implemented so far: Dataset → Data/Feature Pipeline (`run_data_pipeline`) → Training (`run_training`). Data flow:

```text
data/dataset.csv → read_csv → train_test_split (seeded) → preprocessor.fit(train) → transform(train, test)
                                                        └→ artifacts/preprocessor.joblib
                                                        → XGBRegressor.fit → predict(test) → MAE/RMSE/R²
                                                        └→ models/{model.json, preprocessor.joblib, metrics.json}
```

## Repository Structure

```text
.
├── data/dataset.csv         # existing dataset, 2,000 rows, read-only
├── src/hotelprice/          # Python package
│   ├── config.py            # column lists + env-driven settings
│   ├── data_pipeline.py     # run_data_pipeline(): load, split, preprocess, save
│   └── train.py             # run_training(): train, evaluate, save model + metrics
├── models/                  # training output (git-ignored, created by train)
├── pipelines/               # empty (.gitkeep); ML pipeline entry points
├── config/                  # empty (.gitkeep); configuration files
├── tests/test_smoke.py      # package import + dataset schema tests
├── tests/test_data_pipeline.py  # data pipeline tests
├── tests/test_train.py      # training tests (small sample)
├── tests/conftest.py        # shared small-sample CSV fixture
├── .env.example             # optional HOTELPRICE_* overrides with defaults
├── pyproject.toml           # dependencies, pytest and ruff config
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

- **Training hyperparameters** (`XGB_PARAMS`): `n_estimators=300, learning_rate=0.05, max_depth=5, subsample=0.8, colsample_bytree=0.8, n_jobs=1`, seed 42. Fixed values, not tuned. `n_jobs=1` keeps runs deterministic.
- **Model saved as XGBoost JSON** (`model.save_model`) rather than pickle, so it is portable across versions; the preprocessor is saved with joblib. Both live in `models/` so inference needs only that directory.
- **RMSE is `sqrt(mean_squared_error)`** (works across scikit-learn versions).
- `run_data_pipeline()` still writes `artifacts/preprocessor.joblib` as before; training saves a second copy in `models/`, which is the one to load for inference.

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
- Ruff: `line-length = 100`, lint rules `E, F, I, UP, B`, `src = ["src", "tests"]` in `pyproject.toml`.

## Commands

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
pytest

# Lint and format (ruff)
ruff check .
ruff format --check .
ruff check --fix . && ruff format .   # apply fixes

# Run the data pipeline on the real dataset (also saves artifacts/preprocessor.joblib)
python -m hotelprice.data_pipeline

# Train and evaluate on the real dataset (saves models/model.json, preprocessor.joblib, metrics.json)
python -m hotelprice.train

# Optional overrides
HOTELPRICE_DATA_PATH=path/to.csv HOTELPRICE_TEST_SIZE=0.3 HOTELPRICE_RANDOM_SEED=1 HOTELPRICE_PREPROCESSOR_PATH=/tmp/p.joblib python -m hotelprice.data_pipeline
# Training output dir: HOTELPRICE_MODEL_DIR=/tmp/models python -m hotelprice.train
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

## Verification Results (Milestone 1.2)

- `pytest`: 11 passed (2 smoke + 5 data pipeline + 4 training).
- `python -m hotelprice.train` on the real dataset (1,600 train / 400 test, seed 42):

  | Metric | Test value |
  |--------|-----------|
  | MAE    | 387.36 |
  | RMSE   | 495.51 |
  | R²     | 0.9772 |

- `models/model.json`, `models/preprocessor.joblib`, `models/metrics.json` were created; `git status` shows `models/` is not tracked.
- Reproducibility is covered by a test (two runs give identical metrics).

## Verification Results (Milestone 2.1)

- `ruff check .` passes and `ruff format --check .` reports all 11 files formatted.
- `pytest`: 11 passed in the working tree.
- **Clean clone:** `git clone` into a temp directory, fresh venv, `pip install -e ".[dev]"`, then `pip check` (no broken requirements), `pytest` (11 passed), ruff check/format (clean), and `python -m hotelprice.train` all succeeded with no fixes needed. Metrics were identical to Milestone 1.2 (MAE 387.36, RMSE 495.51, R² 0.9772), `models/` contained `model.json`, `preprocessor.joblib` and `metrics.json`, and `git status` in the clone stayed clean. The temp clone was deleted afterwards.

## Known Issues / Limitations

- Dependencies are not pinned to exact versions, so future installs may resolve newer versions.
- `pipelines/` and `config/` are placeholders; settings currently live in `src/hotelprice/config.py` and env vars.
- The preprocessor is saved locally only; logging/registering it with the model is left to the MLflow milestones.
- Metrics are from a single train/test split with untuned hyperparameters; no cross-validation. The test set is not used for model selection.
- `run_data_pipeline()` writes the preprocessor file on every call, so it has a side effect (tests redirect it to a temp path).
- `test_real_dataset` reads the real dataset (or `HOTELPRICE_DATA_PATH`) and expects 2,000 rows at the default 0.2 split.
- The dataset had to be sourced from outside the repo (see Dataset). If a different canonical dataset exists, replace it deliberately.

## Next Milestone

**2.2 DVC dataset versioning**: track `data/dataset.csv` with local DVC and stop tracking the CSV in Git, per the milestone prompt.
