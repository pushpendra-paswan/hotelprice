# PROJECT_CONTEXT

Source of truth for the current project state. Update after every milestone.

## Current Status

- **Completed:** Milestones 0.1 (project definition and structure), 1.1 (dataset and data pipeline), 1.2 (XGBoost training and evaluation), 2.1 (Git and project quality), 2.2 (DVC dataset versioning), 3.1 (MLflow experiment tracking)
- **In progress:** none
- **Next:** Milestone 3.2 (MLflow Model Registry)

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

### 2.2 DVC Dataset Versioning
- **DVC 3.67.1** added to `[project.dependencies]` (`dvc>=3.0`); `dvc init` config committed (`.dvc/config`, `.dvcignore`). Analytics disabled via `core.analytics false` in `.dvc/config`.
- **Dataset tracked by DVC:** `data/dataset.csv` was removed from the Git index (`git rm --cached`) and added with `dvc add`. Git now holds only `data/dataset.csv.dvc` and `data/.gitignore` (`/dataset.csv`). The file is untouched (SHA-256 still `afeb014d…82cf2`; DVC md5 `b96052c3…`).
- **Local remote outside the repo:** `localstorage` at `/home/pushpendra/dvc-remotes/hotelprice`, added with `dvc remote add -d --local`, so both the remote and the default-remote setting live in `.dvc/config.local` (git-ignored, never committed). Each developer creates their own remote; steps are in the README.
- **`dvc.yaml`:** one `train` stage. `cmd: python -m hotelprice.train`; deps: `data/dataset.csv`, `config.py`, `data_pipeline.py`, `train.py`; outs: `models/model.json`, `models/preprocessor.joblib`; metrics: `models/metrics.json` with `cache: false`. `dvc.lock` is committed. No `params.yaml`, no code changes.
- **`.gitignore`:** `models/` became `models/*` plus `!models/metrics.json`, so the metrics file is committed (needed for `dvc metrics diff` across Git revisions) while the model and preprocessor stay ignored and DVC-cached. The stale "dataset is not ignored yet" comment was fixed.
- **README:** new "Data versioning and pipeline (DVC)" section covering remote setup, `dvc pull`, `dvc push`, `dvc repro`, `dvc checkout`, `dvc metrics show/diff`, and how to change the dataset.
- **Commits:** `Add DVC dependency and initialize DVC`, `Track dataset with DVC instead of Git`, `Add DVC train stage and track metrics in Git`, `Document DVC setup and commands in README`, plus this context update. Nothing was pushed to GitHub.

### 3.1 MLflow Experiment Tracking
- **MLflow 3.16.1** added to `[project.dependencies]` (`mlflow>=3.0`).
- **Logging lives directly in `run_training()`** (`train.py`), as plain numbered steps after the existing save step. No tracking module or wrapper. Training command is unchanged; `models/model.json`, `preprocessor.joblib` and `metrics.json` are still written first, so the DVC stage works as before. `dvc.yaml` needed no change (`dvc.lock` only got new dependency hashes for `config.py`/`train.py`).
- **Tracking configuration** (`config.py`, listed in `.env.example`): `HOTELPRICE_MLFLOW_TRACKING_URI` (default `sqlite:///<repo>/mlflow.db`), `HOTELPRICE_MLFLOW_ARTIFACT_DIR` (default `<repo>/mlartifacts`), `HOTELPRICE_MLFLOW_EXPERIMENT` (default `hotel-price-prediction`). SQLite backend (not the file store) so the Model Registry works in 3.2. `mlflow.db`, `mlartifacts/` and `mlruns/` were already in `.gitignore`.
- **Experiment creation:** if the experiment does not exist, it is created with `artifact_location` = the artifact dir; otherwise it is reused (an existing experiment keeps its original artifact location).
- **What each run logs:**
  - Params: all `XGB_PARAMS` (`n_estimators`, `learning_rate`, `max_depth`, `subsample`, `colsample_bytree`, `n_jobs`), `random_seed`, `test_size`, `target`, `features` (comma-joined), `n_rows`, `n_train_rows`, `n_test_rows`.
  - Metrics: `mae`, `rmse`, `r2` (test set).
  - Tags: `dataset_path`, `dataset_dvc_md5` (read from `data/dataset.csv.dvc`, `unknown` if there is no `.dvc` file), `git_commit` (`git rev-parse HEAD`, `unknown` if git fails). The commit is the last commit, so it can be stale if the working tree has uncommitted changes; no dirty flag is logged.
  - Model: `mlflow.xgboost.log_model(model, name="model")`.
  - Preprocessor: run artifact `preprocessor/preprocessor.joblib`.
- **MLflow 3 stores the model as a "logged model"**, linked to the run and saved under `mlartifacts/models/m-<id>/artifacts/` (with `MLmodel`, `model.ubj`, env files), not under the run's own artifact folder. `runs:/<run_id>/model` still resolves to it. The preprocessor stays in the run's artifacts (`mlartifacts/<run_id>/artifacts/preprocessor/`).
- **Tests:** `train_env` in `tests/test_train.py` now points MLflow at a temp SQLite DB, artifact dir and experiment name. Two new tests: one run has the expected params, metrics, tags, linked model and preprocessor artifact, and both load back and predict; two runs land in one experiment.
- **README:** new "Experiment tracking (MLflow)" section (what is logged, train, start the UI, load a model, env vars).
- No tuning, autologging, extra models, Model Registry, BentoML, Docker or CI/CD.

## Architecture

Target pipeline (built up across milestones):

```text
Dataset → DVC → Data/Feature Pipeline → Training → MLflow Tracking
        → MLflow Model Registry → BentoML → Docker → Local Serving

Git → GitHub → GitHub Actions
```

Implemented so far: Dataset → DVC → Data/Feature Pipeline (`run_data_pipeline`) → Training (`run_training`) → MLflow Tracking (inside `run_training`), wired together by the DVC `train` stage. Data flow:

```text
data/dataset.csv → read_csv → train_test_split (seeded) → preprocessor.fit(train) → transform(train, test)
                                                        └→ artifacts/preprocessor.joblib
                                                        → XGBRegressor.fit → predict(test) → MAE/RMSE/R²
                                                        ├→ models/{model.json, preprocessor.joblib, metrics.json}
                                                        └→ MLflow run (mlflow.db + mlartifacts/): params, metrics, tags, model, preprocessor
```

## Repository Structure

```text
.
├── data/dataset.csv         # existing dataset, 2,000 rows, read-only; DVC-tracked (git-ignored)
├── data/dataset.csv.dvc     # DVC pointer to the dataset (in Git)
├── dvc.yaml, dvc.lock       # DVC pipeline: single `train` stage and its pinned hashes
├── .dvc/config              # DVC config (in Git); .dvc/config.local holds the machine-specific remote
├── src/hotelprice/          # Python package
│   ├── config.py            # column lists + env-driven settings
│   ├── data_pipeline.py     # run_data_pipeline(): load, split, preprocess, save
│   └── train.py             # run_training(): train, evaluate, save model + metrics, log to MLflow
├── mlflow.db, mlartifacts/  # local MLflow store (git-ignored, created on first run)
├── models/                  # training output; model/preprocessor DVC-cached, metrics.json in Git
├── pipelines/               # empty (.gitkeep); ML pipeline entry points
├── config/                  # empty (.gitkeep); configuration files
├── tests/test_smoke.py      # package import + dataset schema tests
├── tests/test_data_pipeline.py  # data pipeline tests
├── tests/test_train.py      # training tests (small sample)
├── tests/conftest.py        # shared small-sample CSV fixture
├── .env.example             # optional HOTELPRICE_* overrides (incl. MLflow) with defaults
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
- **MLflow tracking uses explicit calls** (`log_params`, `log_metrics`, `set_tags`, `log_model`, `log_artifact`), not autologging, so what is logged is visible in `train.py`.
- **Plain sequential code, one pipeline file** (per CLAUDE.md): no helper functions or dataclass; the pipeline reads its settings from config/env rather than function arguments, and tests override them with env vars.
- **Configuration via environment variables** with defaults: `HOTELPRICE_DATA_PATH` (default `data/dataset.csv`), `HOTELPRICE_TEST_SIZE` (0.2), `HOTELPRICE_RANDOM_SEED` (42). Function arguments override the env values.
- **No validation or cleaning step**: the data has no missing or duplicate values. A missing column fails with a pandas `KeyError` on selection.

- **Single `pyproject.toml`** (no requirements files), with a `src/` layout and an installable `hotelprice` package. Runtime dependencies are in `[project.dependencies]` and pytest is in the `dev` extra.
- **Dependency bounds are lower bounds only** (`>=`). Exact reproducibility comes later, for example via a lock or the Docker image.
- **The dataset is DVC-tracked** (since 2.2): `data/.gitignore` (written by DVC) ignores it, and the root `.gitignore` also ignores models except `models/metrics.json`, `mlruns/`, `mlflow.db`, `bentoml/`, `.venv/`, `.env`, and the DVC cache/local config.
- **Configuration** lives in `config/` and secrets come from environment variables. Nothing is configured yet.

## Current Configuration

- Python 3.12.3 (project requires >=3.10).
- Resolved versions in the verified environment: pandas 3.0.6, numpy 2.5.3, scikit-learn 1.9.1, xgboost 3.4.1, pytest 9.1.1.
- pytest: `testpaths = ["tests"]` in `pyproject.toml`.
- DVC 3.67.1: one default remote `localstorage` (directory outside the repo, set in git-ignored `.dvc/config.local`); `core.analytics = false`.
- MLflow 3.16.1: tracking URI `sqlite:///<repo>/mlflow.db`, artifacts in `<repo>/mlartifacts`, experiment `hotel-price-prediction` (all overridable, see `.env.example`). Resolved versions otherwise unchanged; `pip check` clean.
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

# DVC (one-time remote setup per clone; the path is machine-specific and stays out of Git)
mkdir -p ~/dvc-remotes/hotelprice
dvc remote add -d --local localstorage ~/dvc-remotes/hotelprice
dvc pull            # fetch dataset (+ models) from the remote
dvc repro           # run the train stage (skips if nothing changed)
dvc push            # upload DVC-tracked data to the remote
dvc checkout        # after `git checkout <commit>`, restore that commit's data/models
dvc metrics show    # print models/metrics.json
dvc metrics diff    # compare workspace (or two revisions) metrics

# MLflow: training logs a run each time; open the UI at http://127.0.0.1:5000
python -m hotelprice.train
mlflow ui --backend-store-uri sqlite:///mlflow.db

# Optional overrides
HOTELPRICE_DATA_PATH=path/to.csv HOTELPRICE_TEST_SIZE=0.3 HOTELPRICE_RANDOM_SEED=1 HOTELPRICE_PREPROCESSOR_PATH=/tmp/p.joblib python -m hotelprice.data_pipeline
# Training output dir: HOTELPRICE_MODEL_DIR=/tmp/models python -m hotelprice.train
# MLflow: HOTELPRICE_MLFLOW_TRACKING_URI, HOTELPRICE_MLFLOW_ARTIFACT_DIR, HOTELPRICE_MLFLOW_EXPERIMENT
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

## Verification Results (Milestone 2.2)

- `dvc push` uploaded the dataset; after training, the model and preprocessor. `dvc status -c` reports cache and remote in sync (3 objects: dataset, model, preprocessor).
- **`dvc repro`:** first run trained (MAE 387.36, RMSE 495.51, R² 0.9772, identical to Milestone 1.2) and wrote `dvc.lock`; the second run printed `Stage 'train' didn't change, skipping` / `Data and pipelines are up to date.`
- **Versioning demo** (temporary branch `demo-dataset-versioning`, deleted afterwards with `git branch -D`; its two commits were never on `main`): the dataset was replaced by its first 1,200 rows (`head -n 1201`), then `dvc add`, commit of the `.dvc` change, `dvc repro`, commit of `dvc.lock`/`metrics.json`.

  | Dataset | MAE | RMSE | R² |
  |---------|-----|------|-----|
  | Original (2,000 rows) | 387.36 | 495.51 | 0.9772 |
  | Demo (1,200 rows) | 398.92 | 493.57 | 0.9816 |

  `dvc metrics diff main` showed those differences. `git checkout <original commit>` + `dvc checkout` restored the 2,001-line CSV (SHA-256 matches the original) and the original metrics; switching back to the demo branch + `dvc checkout` restored the 1,201-line CSV and the demo metrics.
- **Cleanup:** back on `main`, `dvc checkout` restored the real dataset (SHA-256 `afeb014d…82cf2`, `cmp` identical to a backup taken before the demo). `dvc gc -w -c` removed the demo objects from the local cache and the remote. `git status` is clean, `git branch` shows only `main`, and the log has no demo commits.
- **`git ls-files`:** `data/dataset.csv.dvc`, `data/.gitignore`, `dvc.yaml`, `dvc.lock`, `.dvc/config`, `.dvcignore` and `models/metrics.json` are tracked. `data/dataset.csv`, `models/model.json`, `models/preprocessor.joblib`, `artifacts/`, `.dvc/config.local` and `.dvc/cache` are not.
- `pytest`: 11 passed; `ruff check .` and `ruff format --check .` pass.
- **Clean clone** (temp dir, fresh venv, `pip install -e ".[dev]"`, `pip check` clean): before configuring a remote, `dvc pull` fails with missing files, as expected. After `dvc remote add -d --local` pointing at a copy of the store, `dvc pull` fetched the dataset (SHA-256 matches) and models, `dvc status` was up to date, `dvc repro -f` retrained with the same metrics, `pytest` gave 11 passed, ruff was clean and `git status` stayed clean. The temp clone and remote copy were deleted.

## Verification Results (Milestone 3.1)

- `ruff check .` and `ruff format --check .` pass. `pytest`: 13 passed (11 previous + 2 MLflow tests, about 35 s in total; the real `mlflow.db` was not touched by tests).
- **Runs:** `dvc repro` (deps changed, so it retrained; the second `dvc repro` skipped the stage) plus two `python -m hotelprice.train` runs gave 3 runs, all `FINISHED`, in the same experiment `hotel-price-prediction`. Metrics identical to earlier milestones (MAE 387.36, RMSE 495.51, R² 0.9772). `models/metrics.json` is unchanged in Git.
- **Logged values** (checked via `mlflow.search_runs`): 13 params (`n_rows` 2000, train 1600, test 400, seed 42, test size 0.2, the 6 XGBoost params, target, features), 3 metrics, tags `git_commit` = `2094583…` and `dataset_dvc_md5` = `b96052c3…` (matches `dataset.csv.dvc`).
- **MLflow UI:** `mlflow ui --backend-store-uri sqlite:///mlflow.db --port 5000` served HTTP 200. Its REST API (`/api/2.0/mlflow/runs/search`, logged-models search) returned the 3 runs with params and metrics and the logged models. It was checked through the API, not by looking at the pages in a browser. The UI process was stopped afterwards.
- **Load back:** `mlflow.xgboost.load_model("runs:/<run_id>/model")` and the downloaded `preprocessor/preprocessor.joblib` predicted for 3 raw dataset rows: 5867, 15160, 7466 vs actual 5744, 15168, 7002.
- `git status`: `mlflow.db` and `mlartifacts/` are ignored; changes are `.env.example`, `dvc.lock`, `pyproject.toml`, `config.py`, `train.py`, `tests/test_train.py`, README and this file.

## Known Issues / Limitations

- Dependencies are not pinned to exact versions, so future installs may resolve newer versions.
- `pipelines/` and `config/` are placeholders; settings currently live in `src/hotelprice/config.py` and env vars.
- The preprocessor is logged as a run artifact, separate from the model; registering the model and preprocessor together is left to 3.2.
- `mlflow.db` and `mlartifacts/` are local and git-ignored, and are not DVC-tracked; each clone has its own run history. Runs from every `dvc repro` or manual train are added, so the store grows.
- Because the `git_commit` tag is `HEAD`, a run from an uncommitted working tree carries the previous commit's SHA.
- The MLflow artifact dir only applies at experiment creation. If `mlflow.db` is deleted but `mlartifacts/` is kept, old artifacts are orphaned.
- MLflow prints INFO lines and an agent-hint message on start; `MLFLOW_DISABLE_AGENT_HINT=1` silences the hint.
- The test suite is slower with MLflow (each training test creates a SQLite store).
- Metrics are from a single train/test split with untuned hyperparameters; no cross-validation. The test set is not used for model selection.
- `run_data_pipeline()` writes the preprocessor file on every call, so it has a side effect (tests redirect it to a temp path).
- `test_real_dataset` reads the real dataset (or `HOTELPRICE_DATA_PATH`) and expects 2,000 rows at the default 0.2 split.
- **DVC remote is per-machine.** `.dvc/config.local` is not committed, so a fresh clone cannot `dvc pull` until a remote is added. The remote is a local directory, so the dataset only reaches another developer if they get a copy of that directory (e.g. a shared folder); there is no cloud remote in Version 1.
- `run_data_pipeline()` also writes `artifacts/preprocessor.joblib`, which is not a declared DVC output (it is git-ignored and duplicated in `models/`), so it is not versioned.
- `dvc gc` deletes cached objects not referenced by the current workspace (`-w`) or other revisions; use it carefully once real history exists.
- The dataset had to be sourced from outside the repo (see Dataset). If a different canonical dataset exists, replace it deliberately.

## Next Milestone

**3.2 MLflow Model Registry**: register the trained model (and its preprocessor) in the MLflow Model Registry on the same SQLite store, per the milestone prompt.
