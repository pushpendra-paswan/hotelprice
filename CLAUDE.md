# Dynamic Hotel Price Prediction Platform

End-to-end ML/MLOps project that predicts hotel room prices and covers the full lifecycle: data versioning, training, experiment tracking, model registry, serving, containerization, and CI/CD. The ML is intentionally simple; the focus is the MLOps lifecycle. Version 1 is local development and local serving only.

## ML Problem

- Target: `room_price`
- Features: hotel, city, room type, season, day of week, holiday/weekend, occupancy, demand, booking lead time, competitor price
- Model: XGBoost regression
- Metrics: MAE, RMSE, R²
- The dataset already exists in the repo. Never create, generate, or replace it.

## Tech Stack (use only these)

- **ML:** Python, Pandas, NumPy, Scikit-learn, XGBoost
- **Versioning:** Git, GitHub, DVC (local)
- **Tracking & registry:** MLflow, MLflow Model Registry
- **Serving:** BentoML (do not use FastAPI)
- **Containers:** Docker
- **CI/CD:** GitHub Actions

Do not add other technologies or dependencies unless explicitly requested. Cloud infrastructure, Kubernetes, and production monitoring are out of scope for Version 1.

## Architecture

```text
Dataset → DVC → Data/Feature Pipeline → Training → MLflow Tracking
        → MLflow Model Registry → BentoML → Docker → Local Serving

Git → GitHub → GitHub Actions (tests, code quality, ML validation,
                               Docker build, versioned image build/publish)
```

## Working Rules

**Before every milestone**
1. Read `PROJECT_CONTEXT.md`.
2. Inspect the existing repository and identify what is already implemented.
3. Implement only the requested milestone. Do not build future milestones early.
4. Do not recreate or overwrite working functionality unnecessarily.
5. - Prefer plain, sequential code over many small helper functions. Add a function or a new file only when it is reused or clearly improves readability.

**After every milestone**
1. Verify it works (run the tests and commands).
2. Update `PROJECT_CONTEXT.md` with what was actually implemented, architecture changes, key decisions, verification results, and the next milestone.
3. Do not create separate milestone reports.

## `PROJECT_CONTEXT.md`

Source of truth for current project state. Keep it accurate and include:
- Current status and completed milestones
- Current architecture and repository structure (when useful)
- Important implementation decisions
- Current configuration
- Commands to run and test the project
- Known issues/limitations
- Next milestone

## Coding Principles

- Keep it simple and production-oriented; prefer clear, maintainable Python.
- Prefer plain, sequential code over many small helper functions. Add a function or a new file only when it is reused or clearly improves readability.
- No unnecessary abstractions or dependencies.
- Follow the existing repository structure and reuse existing utilities.
- Keep configuration separate from application logic; use environment variables for configurable values.
- Never hardcode secrets or credentials.
- Keep ML code reproducible (fixed seeds, versioned data, logged parameters).
- Make everything runnable locally with simple commands.
- Add tests where appropriate.
- Keep generated artifacts (models, data, MLflow runs) out of Git unless intended.

## Milestone Roadmap

- **0.1** Project definition and structure (README, `PROJECT_CONTEXT.md`, `.gitignore`)
- **1.1** Data loading, preprocessing, train/test split
- **1.2** XGBoost training and evaluation pipeline
- **2.1** Git workflow and project quality
- **2.2** DVC dataset versioning
- **3.1** MLflow experiment tracking
- **3.2** MLflow Model Registry
- **4.1** BentoML service (loads model from MLflow registry)
- **4.2** Dockerize the BentoML service
- **5.1** GitHub Actions CI (tests, quality checks, ML validation, Docker build)
- **5.2** GitHub Actions CD (versioned Docker image tagged with Git commit SHA)

Detailed tasks for each milestone are provided in the milestone prompt.

## Version 1 Done When

The full pipeline (Dataset → DVC → Training → MLflow → Registry → BentoML → Docker → Local Inference) works end to end, GitHub Actions runs test, validate, build, and deliver, and another developer can reproduce everything from the repository instructions.
