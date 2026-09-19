# PROJECT_CONTEXT

Source of truth for the current project state. Update after every milestone.

## Current Status

- **Completed:** Milestones 0.1 (project definition and structure), 1.1 (dataset and data pipeline), 1.2 (XGBoost training and evaluation), 2.1 (Git and project quality), 2.2 (DVC dataset versioning), 3.1 (MLflow experiment tracking), 3.2 (MLflow Model Registry), 4.1 (BentoML service), 4.2 (Docker), 5.1 (GitHub Actions CI, written and verified locally; not yet run on GitHub), 5.2 (GitHub Actions CD, written and verified locally; not yet run on GitHub)
- **All Version 1 milestones are complete.** Nothing has been pushed to GitHub, so neither workflow has run there yet.
- **In progress:** none
- **Next:** none (see "Version 1 Completion Checklist")

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

### 3.2 MLflow Model Registry
- **Registration is one argument in `run_training()`** (`train.py`): `mlflow.xgboost.log_model(model, name="model", registered_model_name=...)`. Every training run (including `dvc repro`) creates a new version of the registered model, linked to its run (`version.run_id`). `dvc.yaml` is unchanged (`dvc.lock` only has new hashes for `config.py`/`train.py`).
- **Registered model name:** `hotel-price-model`, from env `HOTELPRICE_MLFLOW_MODEL_NAME` (`get_registered_model_name()` in `config.py`, listed in `.env.example`).
- **Alias approach:** the alias `champion` marks the selected version; no Staging/Production stages. Newest version is registered automatically, the alias is moved explicitly. No promotion rules, comparison logic or gates.
- **`src/hotelprice/select_model.py`** (the only new source file): a plain top-to-bottom script. `python -m hotelprice.select_model [VERSION]` lists all versions (run ID, mae/rmse/r2, aliases) and sets `champion` on VERSION, or on the latest version if none is given. It runs at import (no functions), so tests call it with `runpy`.
- **Model + preprocessor per version:** the model is loaded with `models:/hotel-price-model@champion`; the preprocessor is a run artifact, so resolve the version with `client.get_model_version_by_alias(name, "champion")`, then download `runs:/<version.run_id>/preprocessor/preprocessor.joblib`. Snippet is in the README (Model Registry section). BentoML (4.1) needs both.
- **MLflow 3 details:** the version's `source` is `models:/m-<id>` (the logged model), and `search_model_versions` returns `version` as an int and does not fill in aliases, so the script reads aliases from `get_registered_model(name).aliases`.
- **Tests:** `train_env` sets `HOTELPRICE_MLFLOW_MODEL_NAME=test-model`; new `test_training_registers_a_model_version` (two runs → versions 1 and 2, each linked to a finished run) and new `tests/test_select_model.py` (alias set to 1 then 2 loads through `models:/test-model@champion`, with its preprocessor predicting; no argument selects the latest). All use a temp SQLite store under `tmp_path`.
- **README:** new "Model Registry (MLflow)" section (register, select, load champion + preprocessor, env var).
- No BentoML, Docker or CI/CD.

### 4.1 BentoML Service
- **BentoML 1.4.39** added to `[project.dependencies]` (`bentoml>=1.4`). **No version conflicts:** the install changed no existing package (pydantic stays 2.13.5, MLflow 3.16.1); `pip check` is clean. FastAPI is present only as a pre-existing transitive dependency of MLflow; the code does not import it and BentoML is the serving layer.
- **`src/hotelprice/service.py`** (the only new source file, single file, no helper functions): the `HotelPriceRequest` and `HotelPriceResponse` pydantic models plus one `@bentoml.service` class, `HotelPriceService`. Run: `bentoml serve hotelprice.service:HotelPriceService` (port 3000).
- **Startup (`__init__`, once):** set the tracking URI (`get_mlflow_tracking_uri()`) → `get_model_version_by_alias(name, "champion")` → `mlflow.xgboost.load_model("models:/<name>@champion")` → download `runs:/<version.run_id>/preprocessor/preprocessor.joblib` into a temp dir and `joblib.load` it. Each step raises `RuntimeError` with a clear message (alias missing → tells the user to run `train` then `select_model`; model or preprocessor unloadable → names the model version/run). Name and URI come from the existing `HOTELPRICE_MLFLOW_MODEL_NAME` / `HOTELPRICE_MLFLOW_TRACKING_URI`; no new variables.
- **Request** (`POST /predict`, JSON body, one field per feature in `config.FEATURES` order; a test asserts the field list equals `FEATURES`): strings `hotel, city, room_type, season, day_of_week`; ints `is_holiday, is_weekend, booking_lead_time_days`; floats `occupancy, demand, competitor_price`. All required.
- **Response:** `{"predicted_room_price": <float>, "model_version": "<registered version>"}`.
- **Endpoint** (`@bentoml.api(input_spec=HotelPriceRequest)`, so fields arrive as kwargs): builds a one-row DataFrame in `FEATURES` order → `preprocessor.transform` → `model.predict` → float. No preprocessing is re-implemented; unseen categories become NaN in the saved preprocessor.
- **Validation errors return HTTP 400** (BentoML's behavior, not 422) with pydantic details.
- **Tests** (`tests/test_service.py`, 5 tests, temp SQLite MLflow store under `tmp_path`, one training run per test): request fields equal `FEATURES`; service loads the champion (version, model, preprocessor); valid request returns a float and an unseen category does not crash; over HTTP (`starlette.testclient.TestClient(HotelPriceService.to_asgi())`) a valid request returns 200 and a missing field / wrong type return 400 while `/livez` stays 200; missing champion alias raises a `RuntimeError` mentioning `select_model`. Tests call the service class through `HotelPriceService.inner()`.
- **README:** new "Serving (BentoML)" section (serve command, env vars, champion prerequisite, curl request/response, error behavior, health endpoints).
- No Bento build, Docker, authentication, batching, caching, monitoring or extra endpoints. Training, MLflow logging and DVC are unchanged.

### 4.2 Docker
- **Problem solved:** the service read the local MLflow store (`mlflow.db`, absolute artifact paths), which cannot exist in a container. The image now holds a snapshot of the champion and never touches MLflow.
- **How artifacts get into the image:** `python -m hotelprice.export_artifacts [OUTPUT_DIR]` (new script `src/hotelprice/export_artifacts.py`, plain top-to-bottom like `select_model.py`) resolves `models:/<name>@champion`, then writes to the git-ignored `serving_artifacts/`: `model.json` (native XGBoost), `preprocessor.joblib` (downloaded from the run linked to that model version) and `metadata.json` (`model_name`, `model_version`, `run_id`). It exits with a clear message (mentions `select_model`) if the alias does not exist. The Dockerfile then `COPY`s `serving_artifacts/`.
- **Two loading modes** (simple `if`/early return at the top of `HotelPriceService.__init__`, same single file): `MODEL_ARTIFACT_DIR` set → load `metadata.json` (model version for responses), `model.json` via `xgboost.XGBRegressor().load_model`, and `preprocessor.joblib`; failure raises `RuntimeError` naming the directory and `export_artifacts`. Not set → the unchanged MLflow-registry path (local development). `import mlflow` moved inside that second branch, so the image does not need MLflow. Preprocessing is not duplicated (the same saved preprocessor is used).
- **`requirements-serving.txt`:** `bentoml==1.4.39`, `xgboost-cpu==3.4.1`, `scikit-learn==1.9.1`, `pandas==3.0.6`, `numpy==2.5.3`, `joblib==1.6.0`, `pydantic==2.13.5` (same versions as the training environment). No MLflow, DVC, Ruff or pytest.
- **`Dockerfile`:** `python:3.12-slim` (project runs Python 3.12.3); `pip install --no-cache-dir -r requirements-serving.txt` before any code is copied; non-root user `app` (uid 1000); copies only `__init__.py`, `config.py`, `service.py` (into `/app/hotelprice/`) and `serving_artifacts/`; `ENV MODEL_ARTIFACT_DIR=/app/serving_artifacts`; `EXPOSE 3000`; `HEALTHCHECK` on `/livez` via `python -c urllib.request.urlopen(...)` (no curl in slim); `CMD bentoml serve hotelprice.service:HotelPriceService --port 3000`. No secrets, `.env` or `mlflow.db`.
- **`.dockerignore`:** excludes `.git`, `.dvc`/`*.dvc`/`dvc.*`, `data/`, `models/`, `artifacts/`, `mlflow.db`, `mlruns/`, `mlartifacts/`, `bentoml/`, virtualenvs, `tests/`, caches, `.env*`, `*.md`, `pyproject.toml`, `config/`, `pipelines/`, editor files. `serving_artifacts/` is included (and in `.gitignore`).
- **Image size decision:** the first build with plain `xgboost==3.4.1` was **1.46 GB** (disk usage): the default Linux wheel pulls ~290 MB of NVIDIA NCCL/CUDA libraries. Switching the pin to `xgboost-cpu==3.4.1` (same release and API, CPU-only, GPU support is out of scope) gave the final **`hotel-price-service:local`: 787 MB disk usage (178 MB compressed)**. Remaining size is mostly scipy/pandas/sklearn/numpy. No other reductions were applied.
- **Tests** (added to `tests/test_service.py`, temp MLflow store under `tmp_path`): export writes the three files and they load and predict on their own; export exits with a `select_model` message without a champion and writes nothing; service in `MODEL_ARTIFACT_DIR` mode with the MLflow URI pointing at a non-existent DB gives the same prediction and version as MLflow mode (and does not create that DB); an empty artifact dir raises a clear `RuntimeError`.
- **README:** new "Docker" section (workflow, curl example, variables, rebuild rule). `.env.example` documents `MODEL_ARTIFACT_DIR`.
- No docker-compose, MLflow server container, registry push, GPU support or CI/CD. Training, MLflow logging and DVC are unchanged.

### 5.1 GitHub Actions CI
- **One new workflow, `.github/workflows/ci.yml`**, plus one fixture CSV. No new Python code, helper scripts, composite actions or dependencies. Triggers: `pull_request` and `push` to `main`. `permissions: contents: read`; concurrency group `ci-<workflow>-<ref>` with `cancel-in-progress: true`; no secrets. Actions pinned to majors (`actions/checkout@v4`, `actions/setup-python@v5`), Python `3.12` (same as the Dockerfile and the local environment) with pip caching keyed on `pyproject.toml`.
- **Job `test`** (20 min timeout): `pip install -e ".[dev]"` → `ruff check .` → `ruff format --check .` (check only) → `pytest`.
- **Job `ml-validation-and-docker`** (`needs: test`, 30 min timeout): install → `python -m hotelprice.train` → inline `python -c` check of `metrics.json` (file must exist; `mae`, `rmse`, `r2` finite) → `python -m hotelprice.select_model` → `python -m hotelprice.export_artifacts` → `docker build -t hotel-price-service:ci .` (never pushed) → container smoke test. Smoke test is one bash step: `docker run -d`, a `trap` on EXIT that prints `docker logs` if the step failed and always removes the container; wait for `/readyz` with a bounded loop (30 × 2 s); one valid `/predict` built from the first fixture row (response must have a finite float `predicted_room_price`); one invalid request (`{"hotel": "Taj"}`) that must return a 4xx.
- **How CI gets data and artifacts without DVC:** the job-level env sets `HOTELPRICE_DATA_PATH=tests/fixtures/hotel_sample.csv`, `HOTELPRICE_MLFLOW_TRACKING_URI=sqlite:///<workspace>/mlflow.db` (fresh on every runner) and `HOTELPRICE_MODEL_DIR=<workspace>/ci-models` (so the tracked `models/metrics.json` is not overwritten). Training registers version 1 in that throwaway store, `select_model` moves `champion` to it, and `export_artifacts` writes `serving_artifacts/` for the `COPY` in the Dockerfile. No `dvc pull`, no remote, no real dataset.
- **Fixture:** `tests/fixtures/hotel_sample.csv`, 300 rows = `df.sample(n=300, random_state=42)` of the real dataset (same 12 columns and dtypes, all categories present). It is plain Git, not in DVC, and `data/dataset.csv` was not touched (SHA-256 unchanged, `dvc status` up to date).
- **Test changes so a fresh clone passes:** the two tests that read the real dataset were changed. `test_real_dataset` became `test_fixture_dataset` (same checks on the fixture: 240/60 split). In `test_smoke.py`, `test_fixture_schema` always runs and `test_dataset_schema` (real dataset header) is now skipped when `data/dataset.csv` is absent, so it still runs locally where the dataset exists. All other tests already used in-memory samples.
- **README:** new "Continuous integration" section (jobs, when it runs, how CI gets data, local commands) and a CI status badge (repo URL `github.com/pushpendra-paswan/hotelprice` is the `origin` remote).
- Not added: CD, image publishing, registry logins, DVC steps, schedules, Python matrix, coverage, scanners, notifications. Training, MLflow, DVC, BentoML and Docker behavior are unchanged.

### 5.2 GitHub Actions CD
- **One new file, `.github/workflows/cd.yml`** (workflow `CD`), one job `deliver` (40 min timeout). No new Python code, helper scripts, composite/reusable workflows or dependencies. `ci.yml` only got a comment saying its ML steps and smoke test must stay in sync with `cd.yml` (the same comment is in `cd.yml`).
- **Trigger conditions:** `workflow_run` on workflow `CI`, `types: [completed]`, `branches: [main]`, plus `workflow_dispatch`. The job `if` requires either a manual run on `refs/heads/main`, or `workflow_run.conclusion == 'success'` **and** `workflow_run.event == 'push'`. The `event == 'push'` check matters: the `branches` filter matches the head branch name, so a fork PR from a branch called `main` would otherwise pass it. So CD never publishes for pull requests, forks or failed CI. `workflow_run` executes the default branch's workflow file; a comment in the file explains why publishing is safe.
- **Commit:** `COMMIT_SHA = workflow_run.head_sha || github.sha`, and `actions/checkout` uses `ref: ${{ env.COMMIT_SHA }}`, so the exact commit CI validated is built, not the current branch head.
- **Permissions / safety:** `contents: read`, `packages: write` only; concurrency group `cd` with `cancel-in-progress: false` (deliveries queue rather than race); only the built-in `GITHUB_TOKEN`, no other secrets.
- **Steps:** same as the CI `ml-validation-and-docker` job: `setup-python` 3.12 (pip cache), `pip install -e ".[dev]"`, train on the fixture, metrics check, `select_model`, `export_artifacts`, same job-level env (fixture CSV, temp SQLite MLflow DB, `ci-models`). The four ML `run:` steps are byte-identical to CI (checked by comparing the parsed YAML). Then:
  1. **Build** (plain `docker build`): image name `ghcr.io/<repo>-service` with the repo lowercased in shell (`tr`), tag = full commit SHA (no `latest`); exported as `IMAGE` via `$GITHUB_ENV`. Labels: `org.opencontainers.image.source` (`$GITHUB_SERVER_URL/$GITHUB_REPOSITORY`), `org.opencontainers.image.revision` (SHA), `org.opencontainers.image.description` (states the model was trained on the CI fixture, not the real dataset).
  2. **Container smoke test:** same script as CI (name `hotel-price-cd`, image `$IMAGE`): bounded `/readyz` loop (30 × 2 s), one valid `/predict` needing a finite float, one invalid request needing a 4xx, logs printed on failure, container always removed.
  3. **Push to GHCR:** `docker login ghcr.io -u $GITHUB_ACTOR --password-stdin` with `GITHUB_TOKEN`, `docker push "$IMAGE"`, prints `Published image: <ref>` and writes the reference, the fixture-model note, `docker pull` and `docker run` to `$GITHUB_STEP_SUMMARY`. It comes after the smoke test, so a failed verification stops the job before any push. No `docker/*` actions are used.
- **Image reference:** `ghcr.io/pushpendra-paswan/hotelprice-service:<full commit SHA>` (the owner/repo part comes from `github.repository`, lowercased). Package visibility is not touched by the workflow: new GHCR packages are private, so pulling needs `docker login ghcr.io` with a token that has `read:packages`, unless someone makes the package public by hand.
- **Pull and run** (deployment stays local and manual):
  ```bash
  echo "$GHCR_TOKEN" | docker login ghcr.io -u <github-username> --password-stdin
  docker pull ghcr.io/pushpendra-paswan/hotelprice-service:<commit-sha>
  docker run --rm -p 3000:3000 ghcr.io/pushpendra-paswan/hotelprice-service:<commit-sha>
  ```
- **Fixture-model limitation:** the real dataset is DVC-managed with a local remote and is not reachable from GitHub runners, so the delivered image holds a model trained on the 300-row fixture (MAE about 479 locally). It proves the delivery pipeline (build, verify, tag, publish) but is **not the production-quality model**. Real delivery would need the real dataset available to CI (for example a cloud DVC remote), out of scope for Version 1. The image label and job summary say so.
- **README:** new "Continuous delivery (GitHub Actions)" section (when it runs, naming/tagging, labels, limitation, pull/run, private-by-default note); the repository-structure line lists `cd.yml`.
- Not added: cloud deployment, Kubernetes, other registries, semver tags, GitHub Releases, signing, scanners, notifications, schedules, environment approval gates. Training, MLflow, DVC, BentoML, Docker and CI behavior are unchanged.

## Architecture

Target pipeline (built up across milestones):

```text
Dataset → DVC → Data/Feature Pipeline → Training → MLflow Tracking
        → MLflow Model Registry → BentoML → Docker → Local Serving

Git → GitHub → GitHub Actions (CI in 5.1: tests + quality, ML validation on a fixture, Docker build + smoke test; CD in 5.2: after CI passes on main, rebuild on the fixture, smoke test, push SHA-tagged image to ghcr.io)
```

Implemented so far (through Docker): Dataset → DVC → Data/Feature Pipeline (`run_data_pipeline`) → Training (`run_training`) → MLflow Tracking + Model Registry (inside `run_training`; `select_model` sets the alias), wired together by the DVC `train` stage, then BentoML (`service.py`) loading the champion from the registry. Data flow:

```text
data/dataset.csv → read_csv → train_test_split (seeded) → preprocessor.fit(train) → transform(train, test)
                                                        └→ artifacts/preprocessor.joblib
                                                        → XGBRegressor.fit → predict(test) → MAE/RMSE/R²
                                                        ├→ models/{model.json, preprocessor.joblib, metrics.json}
                                                        └→ MLflow run (mlflow.db + mlartifacts/): params, metrics, tags, model, preprocessor

models:/<name>@champion + runs:/<champion run_id>/preprocessor → BentoML service (startup) → POST /predict   (local mode)

models:/<name>@champion → export_artifacts → serving_artifacts/{model.json, preprocessor.joblib, metadata.json}
    → docker build (COPY) → image with MODEL_ARTIFACT_DIR → BentoML service (startup) → POST /predict   (Docker mode)
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
│   ├── train.py             # run_training(): train, evaluate, save model + metrics, log + register in MLflow
│   ├── select_model.py      # script: list registered versions, set the "champion" alias
│   ├── export_artifacts.py  # script: export champion model + preprocessor + metadata to serving_artifacts/
│   └── service.py           # BentoML service: loads champion (MLflow, or MODEL_ARTIFACT_DIR), POST /predict
├── serving_artifacts/       # exported champion snapshot for the image (git-ignored, created by export_artifacts)
├── Dockerfile, .dockerignore, requirements-serving.txt   # serving image
├── mlflow.db, mlartifacts/  # local MLflow store (git-ignored, created on first run)
├── models/                  # training output; model/preprocessor DVC-cached, metrics.json in Git
├── pipelines/               # empty (.gitkeep); ML pipeline entry points
├── config/                  # empty (.gitkeep); configuration files
├── tests/test_smoke.py      # package import + dataset schema tests
├── tests/test_data_pipeline.py  # data pipeline tests
├── tests/test_train.py      # training, MLflow and registration tests (small sample)
├── tests/test_select_model.py  # alias selection tests
├── tests/test_service.py    # BentoML service + export tests (temp MLflow store)
├── tests/conftest.py        # shared small-sample CSV fixture
├── tests/fixtures/hotel_sample.csv  # 300-row sample of the real dataset (same schema), used by CI
├── .github/workflows/ci.yml # CI: `test` and `ml-validation-and-docker` jobs
├── .github/workflows/cd.yml # CD: `deliver` job (after CI on main): build, smoke test, push to ghcr.io
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
- BentoML 1.4.39 (pydantic 2.13.5, unchanged); service on port 3000 by default; reads the same `HOTELPRICE_MLFLOW_TRACKING_URI` / `HOTELPRICE_MLFLOW_MODEL_NAME` as training.
- Docker 29.6.1 (local build); base image `python:3.12-slim`; container port 3000; `MODEL_ARTIFACT_DIR=/app/serving_artifacts` inside the image; serving dependency pins in `requirements-serving.txt`.
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

# Model Registry: each training run registers a new version; set the champion alias
python -m hotelprice.select_model 2   # alias on version 2 (no argument = latest version)
# Load: mlflow.xgboost.load_model("models:/hotel-price-model@champion"); preprocessor via the version's run_id

# Serve (needs a champion: train, then select_model). Health: /livez, /readyz
bentoml serve hotelprice.service:HotelPriceService
curl -X POST http://localhost:3000/predict -H 'Content-Type: application/json' \
  -d '{"hotel":"The Meridian","city":"Bengaluru","room_type":"Standard","season":"Shoulder","day_of_week":"Wednesday","is_holiday":0,"is_weekend":0,"occupancy":10.0,"demand":45.96,"booking_lead_time_days":16,"competitor_price":6791.59}'

# Docker: export the champion snapshot, build, run (rebuild after any champion change)
python -m hotelprice.export_artifacts                 # writes serving_artifacts/ (git-ignored)
docker build -t hotel-price-service:local .
docker run --rm -p 3000:3000 hotel-price-service:local   # same /predict, /livez, /readyz on :3000

# CI checks, run locally (no real dataset needed; see README "Continuous integration")
ruff check . && ruff format --check . && pytest
HOTELPRICE_DATA_PATH=tests/fixtures/hotel_sample.csv HOTELPRICE_MODEL_DIR=$PWD/ci-models python -m hotelprice.train   # in a scratch clone: writes mlflow.db

# CD (runs on GitHub after CI passes on main; pull a delivered image, needs `docker login ghcr.io` with read:packages)
docker pull ghcr.io/pushpendra-paswan/hotelprice-service:<commit-sha>
docker run --rm -p 3000:3000 ghcr.io/pushpendra-paswan/hotelprice-service:<commit-sha>

# Optional overrides
HOTELPRICE_DATA_PATH=path/to.csv HOTELPRICE_TEST_SIZE=0.3 HOTELPRICE_RANDOM_SEED=1 HOTELPRICE_PREPROCESSOR_PATH=/tmp/p.joblib python -m hotelprice.data_pipeline
# Training output dir: HOTELPRICE_MODEL_DIR=/tmp/models python -m hotelprice.train
# MLflow: HOTELPRICE_MLFLOW_TRACKING_URI, HOTELPRICE_MLFLOW_ARTIFACT_DIR, HOTELPRICE_MLFLOW_EXPERIMENT, HOTELPRICE_MLFLOW_MODEL_NAME
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

## Verification Results (Milestone 3.2)

- `ruff check .` and `ruff format --check .` pass. `pytest`: 16 passed (13 previous + 3 new).
- **Register:** `dvc repro` (code changed, retrained) created version 1; `python -m hotelprice.train` created version 2 (metrics identical to earlier milestones: MAE 387.36, RMSE 495.51, R² 0.9772). A second `dvc repro` skipped the stage.
- **Alias switching** (real `mlflow.db`): `select_model 1` → `models:/hotel-price-model@champion` resolved to v1 (run `5bdd4cc8…`, source `models:/m-c950ec37…`); `select_model 2` → resolved to v2 (run `4bcaa85d…`, source `models:/m-b50f30d9…`). Each time the linked run's preprocessor was downloaded via `runs:/<run_id>/preprocessor/preprocessor.joblib`, and model + preprocessor predicted 5867, 15160, 7466 for 3 real rows (actual 5744, 15168, 7002). The predictions are the same for both versions because the runs are deterministic and identical; the version, run ID and source show that the alias moved. The listing shows `aliases=champion` on the selected version. `select_model` with no argument set the alias on v2. Final state: `champion` → v2.
- **MLflow UI:** `mlflow ui --backend-store-uri sqlite:///mlflow.db --port 5000` served HTTP 200; the registered-models and model-versions REST endpoints returned `hotel-price-model` with alias `champion` → version 2 and versions 1 and 2, each with its run ID. Checked through the API, not by looking at the pages in a browser. The UI process was stopped.
- `git status`: `mlflow.db` and `mlartifacts/` are ignored; changes are `.env.example`, `dvc.lock`, `config.py`, `train.py`, `select_model.py`, the tests, README and this file.

## Verification Results (Milestone 4.1)

- `ruff check .` and `ruff format .` clean. `pytest`: 21 passed (16 previous + 5 new, about 70 s). `dvc repro`: stage `train` unchanged, skipped. `pip check` clean after installing BentoML.
- **`bentoml serve hotelprice.service:HotelPriceService`** against the real `mlflow.db` (champion = version 2): `/livez` and `/readyz` returned 200; the service log showed "Service HotelPriceService initialized".
- **Served vs direct** (dataset rows 0, 500, 1500, sent with `requests`): served predictions 5867.1142578125, 8568.1923828125, 7092.30712890625 were **exactly equal** to the champion model + its run's preprocessor loaded directly in Python (actual prices 5743.83, 8710.88, 6874.36). Each response reported `model_version` "2".
- **Invalid requests:** `{"hotel":"Taj"}` → HTTP 400 listing the 10 missing fields; `occupancy: "high"` → HTTP 400 (`float_parsing`). `/livez` still 200 afterwards. A request with unseen hotel/city returned 200 with a price.
- The server was stopped after the check.

## Verification Results (Milestone 4.2)

- `ruff check .` and `ruff format .` clean. `pytest`: 25 passed (21 previous + 4 new, about 110 s). `dvc status`: "Data and pipelines are up to date" (no change to training, MLflow or DVC).
- **Export** against the real `mlflow.db` (champion = version 2, run `4bcaa85d…`): wrote `model.json` (937 KB), `preprocessor.joblib` (4 KB), `metadata.json` (`hotel-price-model`, version `2`).
- **Build:** `docker build -t hotel-price-service:local .` succeeded; 787 MB disk usage / 178 MB compressed (1.46 GB before switching to `xgboost-cpu`). The pip layer is cached when only code or artifacts change.
- **Run:** `docker run -d -p 3000:3000` became ready in about 5 s; `/livez` and `/readyz` returned 200; `docker inspect` health status `healthy`; `id` inside shows `uid=1000(app)`; log shows "Service HotelPriceService initialized".
- **Predictions** (dataset rows 0, 500, 1500, 1999, sent to the container on :3000, to the non-container MLflow-mode service on :3001, and computed directly by loading `models:/hotel-price-model@champion` and the run's preprocessor in Python): 5867.1142578125, 8568.1923828125, 7092.30712890625, 12444.6982421875, all **exactly equal** across the three paths (actual prices 5743.83, 8710.88, 6874.36, 12571.79). Every response reported `model_version` "2".
- **Invalid requests to the container:** `{"hotel":"Taj"}` → HTTP 400 (10 missing fields); `occupancy: "high"` → HTTP 400 (`float_parsing`); `/livez` still 200 afterwards.
- **No `mlflow.db` or data in the container:** the build context is filtered by `.dockerignore` and the Dockerfile copies only named paths. Checked inside the running container: `/app` contains only `hotelprice/`, `requirements-serving.txt` and `serving_artifacts/` (three files); `find /` for `mlflow.db`, `dataset.csv*`, `.env`, `mlartifacts` found nothing; `import mlflow` and `import dvc` both fail with `ModuleNotFoundError`; the run used no volume mounts. The MLflow-free loading path is also covered by a test that points the MLflow URI at a non-existent DB.
- Existing MLflow-based local serving still works (the port-3001 service above loaded the champion from the real store).

## Verification Results (Milestone 5.1)

**Verified locally**
- `ruff check .` and `ruff format --check .` clean; `dvc status`: up to date; dataset SHA-256 unchanged. In the main working tree (with the real dataset) the smoke and data-pipeline tests give 8 passed, 0 skipped.
- Workflow YAML parses with PyYAML (triggers, `permissions: contents: read`, concurrency, two jobs, `needs: test`). `actionlint` is not installed, so it was not run.
- **Fresh-clone reproduction** (temp `git clone` + the milestone's changed files copied in, new venv, no `data/dataset.csv`, no `mlflow.db`/`models/`/`serving_artifacts/`, no DVC remote). A small runner script (in the scratchpad, not in the repo) read `ci.yml` and executed every `run:` step literally with `bash -e`, with the job-level `env` applied:
  - `test` job: install, `ruff check` (clean), `ruff format --check` (16 files formatted), `pytest` **25 passed, 1 skipped** (the real-dataset schema test) in about 110 s.
  - `ml-validation-and-docker` job: training on the fixture (MAE 478.92, RMSE 586.10, R² 0.9690, registered version 1 in the fresh SQLite store), metrics check, `select_model` (champion → v1), `export_artifacts`, `docker build -t hotel-price-service:ci .` succeeded, container smoke test: `/readyz` ready, valid request returned `predicted_room_price` 6693.15, invalid request returned 400, container removed.
- **Failure paths** (run against the same step text): metrics check exits 1 for a NaN `r2`, a missing key and a missing `metrics.json`; a smoke test forced to fail exits 1, prints the container logs and removes the container.
- The temp clone and the `hotel-price-service:ci` image were deleted afterwards.

**Not verified: can only be verified on GitHub**
- The workflow has **not run on GitHub Actions** (nothing has been pushed). Unverified there: runner-specific behavior (`ubuntu-latest` toolchain, Docker and curl versions, port 3000 being free), pip caching (`cache-dependency-path: pyproject.toml`), `setup-python` 3.12 availability, the concurrency cancel, the fork behavior, total run time and the CI badge (it shows "no status" until a first run).
- The local Docker build reused cached layers (the pip layer was already built); a cold `docker build` on a runner was not timed and will download the dependencies.

## Verification Results (Milestone 5.2)

**Verified locally**
- `ruff check .` and `ruff format --check .` clean; `pytest`: **26 passed** (115 s); `dvc status`: up to date. No Python, training, MLflow, DVC, BentoML or Docker file changed.
- `cd.yml` and `ci.yml` parse with PyYAML (`actionlint` and `yamllint` are not installed, so they were not run): triggers `workflow_run` (CI, completed, `main`) + `workflow_dispatch`; permissions `contents: read`, `packages: write`; concurrency `cd`; the job `if` and 40 min timeout are as designed. The four ML steps are identical to the CI job's.
- **Fresh-clone reproduction** (temp `git clone` of `main`, the new workflow files copied in, brand-new venv, no `data/dataset.csv`, `mlflow.db`, `models/` or `serving_artifacts/`, no DVC remote). A scratchpad runner script (not in the repo) read `cd.yml` and executed each `run:` step literally with `bash -e`, applying the job env and emulating `$GITHUB_ENV`, with `GITHUB_REPOSITORY=Pushpendra-Paswan/HotelPrice` to test the lowercasing and `COMMIT_SHA` = the clone's HEAD (`86e82312841b…`): install, train on the fixture (MAE 478.92, RMSE 586.10, R² 0.9690), metrics check, `select_model`, `export_artifacts`, build, smoke test (prediction 6693.15, invalid request 400, container removed) all passed. Image built as `ghcr.io/pushpendra-paswan/hotelprice-service:86e82312841bdd9cfed9562574a0f303cd8123b7`; `docker inspect` showed the three labels with the expected values (source `https://github.com/Pushpendra-Paswan/HotelPrice`, revision = the SHA, fixture description).
- **Push/pull mechanics against a temporary local registry** (`registry:2` on `localhost:5000`): the image was re-tagged to `localhost:5000/...:<sha>` and the workflow's actual "Push image" step text was run with only the `docker login` line removed and `IMAGE` pointing at the local registry. The push succeeded, `$GITHUB_STEP_SUMMARY` contained the image reference, the fixture note and the `docker pull` / `docker run` commands. The local image was then removed, pulled back from the registry, and run: `/predict` returned `6693.15478515625`, `model_version` "1", the same value as in the smoke test. The registry container, the pulled containers, the `registry:2` image and the temp clone/venv were removed afterwards.

**Not verified: can only be verified on GitHub**
- The workflow has **not run on GitHub Actions**, and **nothing was pushed to ghcr.io** (nothing has been pushed to GitHub at all). Unverified there: that GitHub accepts the workflow file, the `workflow_run` trigger and its `head_sha` checkout, the job `if` expression (including `workflow_run.event == 'push'`), skipping when CI fails or comes from a PR, the `GITHUB_TOKEN` login and `packages: write` permission to create the package, the `ghcr.io` push itself, that the package gets linked to the repository through the source label, the concurrency queueing, the job summary rendering, `ubuntu-latest` behavior and total run time. The `docker login` line itself was never exercised.
- **First-run caveat:** a `workflow_run` workflow only triggers once its file exists on the default branch, so the first delivery happens after `cd.yml` is on `main` and CI passes there. The package will be private until someone changes its visibility.

## Known Issues / Limitations

- Dependencies are not pinned to exact versions, so future installs may resolve newer versions.
- `pipelines/` and `config/` are placeholders; settings currently live in `src/hotelprice/config.py` and env vars.
- The preprocessor is a run artifact, not part of the registered model; it is found through the version's `run_id` (two lookups). Bundling it with the model is not done.
- Every training run registers a new version, including each `dvc repro`, so versions accumulate. The 3 runs from 3.1 have no registered version. Versions 1 and 2 in the local registry come from identical deterministic runs, so their predictions and metrics are the same.
- `select_model.py` runs on import; it is meant to be run as a script only.
- `ruff format .` (0.16) also reformats Python code blocks in `README.md`.
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

- Local mode (no `MODEL_ARTIFACT_DIR`) reads the **local** MLflow store (`mlflow.db` + `mlartifacts/`), and model artifact paths stored in the DB are absolute paths, so it only works where the store and artifacts exist at the same paths. The Docker image avoids this by using the export.
- The champion is resolved once at startup; moving the alias needs a service restart (local mode) or a re-export and image rebuild (Docker mode).
- **The image is a snapshot of the champion at export time.** Changing the champion means `export_artifacts` then `docker build`; nothing warns if `serving_artifacts/` is stale. `serving_artifacts/` is git-ignored, so a fresh clone (and CI) has none and cannot build the image until it is created.
- `requirements-serving.txt` pins must be kept in step with the training environment by hand (joblib preprocessor and model compatibility). It uses `xgboost-cpu` (CPU-only build of the same release) rather than `xgboost`; the Docker path has no GPU support.
- The image is about 787 MB (scipy, pandas, sklearn, numpy dominate); no image scanning or multi-stage build was done.
- `export_artifacts.py`, like `select_model.py`, runs on import and is meant to be run as a script only.
- `bentoml serve` prints MLflow INFO lines and the agent hint at startup; the test run shows Pydantic/starlette deprecation warnings from BentoML internals.
- **Neither CI nor CD has run on GitHub yet** (see Verification 5.1 and 5.2); nothing has been pushed to ghcr.io.
- **The delivered image is not the real model:** it holds a model trained on the 300-row CI fixture (see 5.2). Only the CI/CD path is proven, not model quality.
- CD repeats the CI ML-validation steps by copy (no shared workflow, by design), so `ci.yml` and `cd.yml` must be edited together. CD does not re-run tests or lint; it relies on the CI conclusion. Images are tagged only with the commit SHA (no `latest`, no semver), old images are never cleaned up, and package visibility is private by default.
- **CI has not run on GitHub yet** (see Verification 5.1). CI runs on a 300-row fixture, so its metrics (MAE about 479) differ from the real-dataset metrics and prove the pipeline works, not model quality; the finite-metrics check has no quality threshold.
- CI installs the full project (`pip install -e ".[dev]"`, including DVC, MLflow and BentoML) twice, once per job, so runs are slow (tests about 2 min locally, plus install time). Docker layers are not cached between runs.
- The fixture must be regenerated by hand if the dataset schema changes; `test_dataset_schema` (skipped in CI) and `test_fixture_schema` are the checks that they stay in step.
- `ci-models/` (job env `HOTELPRICE_MODEL_DIR`) is not git-ignored; it only exists on the runner or in a scratch clone.
- Tests use `HotelPriceService.inner()` to get the plain class; this is BentoML SDK behavior that could change between versions.

## Version 1 Completion Checklist

Compared with "Version 1 Done When" in CLAUDE.md. Locally verified means run on this machine; GitHub items cannot be checked until the repository is pushed.

| Criterion | Status |
|-----------|--------|
| Dataset → DVC | Done, verified locally (local remote, `dvc repro`, `dvc pull` in a clean clone) |
| Data/feature pipeline → Training | Done, verified locally (26 tests pass) |
| MLflow tracking and Model Registry (`champion` alias) | Done, verified locally |
| BentoML serving from the registry | Done, verified locally (served predictions equal direct model predictions) |
| Docker image, local inference | Done, verified locally (build, run, `/predict`, invalid request → 400) |
| GitHub Actions: tests, quality, ML validation, Docker build (CI) | Written; every step reproduced locally in a fresh clone; **not yet run on GitHub** |
| GitHub Actions: versioned image build and publish (CD) | Written; steps, tagging, labels and push/pull reproduced locally (temporary local registry); **not yet run on GitHub, nothing pushed to ghcr.io** |
| Another developer can reproduce everything from the repository instructions | README documents setup, DVC remote, training, registry, serving, Docker, CI and CD; verified by clean-clone reproductions. The real dataset only reaches others through a copy of the DVC remote directory (no cloud remote in V1) |

**Still to do to close Version 1 (outside this milestone):** push to GitHub, confirm CI is green, confirm CD publishes `ghcr.io/pushpendra-paswan/hotelprice-service:<sha>`, pull it with a `read:packages` token and run it, and check the CI badge. Known gap: the delivered image contains a fixture-trained model (see Known Issues).
