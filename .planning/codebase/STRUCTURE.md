# Codebase Structure

**Analysis Date:** 2026-10-18

## Directory Layout

```
project/
├── .agents/                 # Antigravity agent configuration and project skills
├── .planning/               # GSD planning system, state, and codebase maps
│   └── codebase/            # 7 authoritative codebase architecture documents
├── backend/                 # FastAPI REST backend service
│   ├── app/                 # Application source package
│   │   ├── routers/         # API endpoint controllers (health, scoring, etc.)
│   │   ├── services/        # Business logic, caching, and model execution
│   │   ├── config.py        # Pydantic application settings & path resolution
│   │   ├── dependencies.py  # FastAPI dependency injection providers
│   │   ├── main.py          # Application factory, lifespan, CORS, and middleware
│   │   └── schemas.py       # Pydantic request/response schemas & validation
│   └── requirements.txt     # Python backend dependencies
├── data/                    # Synthetic datasets, split builders, and feature schemas
│   ├── features.py          # Feature transformation and preprocessing logic
│   ├── generate_fixture.py  # Deterministic synthetic dataset generator
│   ├── schema.py            # Feature column taxonomy and leakage guard sets
│   ├── splits.py            # Deterministic time-ordered split partitioning
│   └── synthetic_smoke_fixture.csv # 10,000-row synthetic evaluation dataset
├── design_assets/           # Design system assets, tokens, and visual specs
├── docs/                    # Technical documentation, reports, and UI/UX audits
│   └── stitch_designs/      # Exported design specifications and mockups
├── eval/                    # Evaluation metrics, bootstrap statistical engine, drift
│   ├── bootstrap.py         # Paired bootstrap CI estimation engine
│   ├── drift.py             # Covariate shift and Population Stability Index (PSI)
│   ├── latency.py           # Latency benchmarking utilities
│   ├── metrics.py           # Binary classification metrics at fixed capacity
│   └── segments.py          # Cohort and subgroup slice evaluation
├── frontend/                # Vite + React 18 single-page dashboard application
│   ├── public/              # Static assets (3D GLTF/GLB models, icons)
│   │   └── models/          # 3D assets (model-pipeline.glb, sandbox instrument)
│   ├── src/                 # Frontend TypeScript source code
│   │   ├── app/             # Application shell, layout, and React Router
│   │   ├── components/      # Reusable UI widgets and 3D Canvas visualizers
│   │   ├── context/         # React Context providers (ThemeContext)
│   │   ├── features/        # Feature pages (overview, sandbox, replay, etc.)
│   │   ├── lib/api/         # REST API fetch client, typed hooks, and interfaces
│   │   └── styles/          # Vanilla CSS design tokens, typography, and layouts
│   ├── package.json         # Frontend dependencies and npm scripts
│   ├── tsconfig.json        # TypeScript compiler configuration
│   └── vite.config.ts       # Vite bundler and dev server configuration
├── logs/                    # Audit trails and test look governance logs
│   ├── audit.jsonl          # Immutable append-only sandbox decision log
│   └── test_looks.log       # Governed test partition access ledger
├── models/                  # Machine learning estimators and probability calibrators
│   ├── artifacts/           # Serialized Joblib model binaries and meta JSONs
│   ├── base.py              # Estimator base classes and artifact loaders
│   ├── calibrate.py         # Platt sigmoid scaling and isotonic calibrators
│   └── ensemble.py          # Diversity ensemble and rank-residualizer ($u_2$)
├── policy/                  # Decision routing and human reviewer capacity governor
│   ├── audit.py             # Decision record formatting and audit helpers
│   ├── baselines.py         # Baseline decision policy benchmarks (B1, B2, B3a, B4)
│   ├── frozen_policy.json   # Tuned, pre-registered decision thresholds ($t, u$)
│   ├── governor.py          # Capacity governor implementation ($B=130$)
│   ├── router.py            # Core decision router state machine (R0-R6)
│   └── thresholds.py        # Policy threshold grid search and validation
├── reference/               # Architectural reference materials (legacy IBM project)
├── results/                 # Evaluation output reports, tables, figures, replay rows
│   ├── figs/                # Generated publication-quality PNG figures
│   ├── tables/              # Generated benchmark CSV summary tables
│   ├── cases.jsonl          # Offline case ledger for Case Explorer
│   ├── replay_rows.jsonl    # 2,000-row streaming replay evaluation stream
│   └── results.json         # Canonical benchmark report ($N=2,000$)
├── scripts/                 # Automation, evaluation, and demo launcher scripts
│   ├── preflight.py         # Preflight verification and hash audit
│   ├── run_phase5_evaluation.py # End-to-end evaluation pipeline execution
│   ├── start_demo.bat       # One-click Windows demo launcher
│   ├── stop_demo.bat        # Safe process cleanup script
│   └── validate_artifacts.py# Integrity gate check for models and results
├── tests/                   # Pytest test suite (109 passing automated tests)
├── config.yaml              # Central configuration file for SignalGate
├── DESIGN.md                # Authoritative Design System Specification (v2.1)
└── README.md                # Platform documentation and quickstart guide
```

## Directory Purposes

**`backend/app/`:**
- Purpose: FastAPI server source code providing REST endpoints for the frontend.
- Contains: Route handlers (`routers/`), business logic and artifact caches (`services/`), configuration models (`config.py`), request/response models (`schemas.py`), and DI providers (`dependencies.py`).
- Key files: `backend/app/main.py`, `backend/app/schemas.py`, `backend/app/services/scoring.py`.

**`frontend/src/`:**
- Purpose: Client-side single-page dashboard application.
- Contains: Feature views (`features/`), shared components (`components/`), API clients (`lib/api/`), styles (`styles/`), and application shell (`app/`).
- Key files: `frontend/src/App.tsx`, `frontend/src/app/router.tsx`, `frontend/src/styles/tokens.css`.

**`policy/`:**
- Purpose: Policy routing, threshold configuration, and operational capacity governance.
- Contains: The decision router state machine (`router.py`), capacity governor (`governor.py`), baseline algorithms (`baselines.py`), and the canonical frozen policy (`frozen_policy.json`).
- Key files: `policy/router.py`, `policy/governor.py`, `policy/frozen_policy.json`.

**`models/`:**
- Purpose: Estimators, calibration transforms, ensemble disagreement, and serialized model weights.
- Contains: scikit-learn models (`base.py`, `calibrate.py`, `ensemble.py`) and serialized Joblib files (`artifacts/`).
- Key files: `models/base.py`, `models/calibrate.py`, `models/ensemble.py`.

**`eval/`:**
- Purpose: Offline statistical verification, hypothesis testing, and drift metrics.
- Contains: Paired bootstrap resampling engine (`bootstrap.py`), fixed-capacity metrics (`metrics.py`), and PSI drift calculators (`drift.py`).
- Key files: `eval/bootstrap.py`, `eval/metrics.py`.

**`tests/`:**
- Purpose: Automated test verification.
- Contains: 16 test modules covering API behavior, artifact freshness, model inference, calibration monotonicity, routing rules, capacity limits, and security constraints.
- Key files: `tests/test_api.py`, `tests/test_api_security.py`, `tests/test_router.py`.

## Key File Locations

**Entry Points:**
- `backend/app/main.py`: ASGI application entry point (`app`).
- `frontend/src/main.tsx`: React DOM mount entry point.
- `scripts/start_demo.bat`: Local demonstration orchestrator.

**Configuration:**
- `config.yaml`: Root project configuration (budgets, splits, dataset, acceptance criteria).
- `policy/frozen_policy.json`: Tuned frozen policy thresholds.
- `backend/app/config.py`: Backend runtime settings and paths.
- `frontend/vite.config.ts`: Vite frontend bundling configuration.

**Core Logic:**
- `policy/router.py`: Decision routing rules (R0 through R6).
- `policy/governor.py`: Capacity governance and deferred queue assignment.
- `backend/app/services/scoring.py`: Live scoring inference pipeline.
- `models/ensemble.py`: Rank-residualized epistemic disagreement ($u_2$).

**Testing:**
- `tests/test_api.py`: FastAPI endpoint tests.
- `tests/test_api_security.py`: Anti-leakage and input validation security tests.
- `tests/test_router.py`: Decision router and governor unit tests.
- `frontend/src/components/__tests__/`: Vitest frontend unit tests.

## Naming Conventions

**Files:**
- Python modules: snake_case (`router.py`, `scoring.py`, `frozen_policy.json`).
- React components: PascalCase (`OverviewPage.tsx`, `SignalCoreScene.tsx`, `AppShell.tsx`).
- CSS files: lowercase kebab-case (`tokens.css`, `layout.css`, `animations.css`).
- Test files: prefixed with `test_` for Python (`test_router.py`) or suffixed with `.test.ts` for frontend (`phase10_quality.test.ts`).

**Directories:**
- Python packages: lowercase snake_case (`backend/app`, `policy`, `eval`, `models`).
- Frontend features: lowercase kebab-case (`features/case-explorer`, `features/policy-comparison`, `features/shift-storm`).

## Where to Add New Code

**New API Endpoint:**
- Router: Add new or extend existing controller in `backend/app/routers/` (e.g. `policies.py` or new file).
- Mount: Register router in `backend/app/main.py:create_app()` using `app.include_router()`.
- Schemas: Define request and response Pydantic schemas in `backend/app/schemas.py`.
- Tests: Add corresponding endpoint assertions in `tests/test_api.py`.

**New Frontend Page / View:**
- Feature Folder: Create new directory under `frontend/src/features/<feature-name>/`.
- Page Component: Implement `<FeatureName>Page.tsx`.
- Route Definition: Register route path in `frontend/src/app/router.tsx`.
- Navigation: Add navigation tab in `frontend/src/components/Sidebar.tsx` or `TopBar.tsx`.
- API Client: Add query method in `frontend/src/lib/api/client.ts` and hook in `frontend/src/lib/api/hooks.ts`.

**New Machine Learning Estimator or Signal:**
- Model Definition: Add implementation in `models/` (e.g. `models/signals/`).
- Pipeline Binding: Update `models/base.py` or `models/ensemble.py`.
- Scoring Integration: Incorporate into `backend/app/services/scoring.py`.
- Unit Tests: Add test coverage in `tests/test_models.py` or `tests/test_ensemble.py`.

**New Policy or Baseline:**
- Algorithm: Implement in `policy/baselines.py`.
- Router Integration: Extend `policy/router.py` if new reason codes are required.
- Benchmark Report: Update `scripts/run_phase5_evaluation.py` to include in comparative matrix.

## Special Directories

- `models/artifacts/`: Stores binary Joblib models (`*.joblib`) and metadata manifests (`*.meta.json`). Generated during training phases and committed for deterministic offline reproduction.
- `results/`: Contains evaluation outputs, figures (`figs/`), tables (`tables/`), and replay streams (`replay_rows.jsonl`). Read-only during runtime operations.
- `logs/`: Holds runtime append-only audit records (`audit.jsonl`). Created and modified during live scoring sandbox operations.
- `reference/architecture/IBM-main/`: Legacy reference architecture used for design comparison; isolated from current production runtime.

---

*Structure analysis: 2026-10-18*
