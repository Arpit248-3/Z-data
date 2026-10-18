# Technology Stack

**Analysis Date:** 2026-10-18

## Languages

**Primary:**
- Python 3.13 (`>=3.13.0`) - Machine learning pipelines, probability calibration, epistemic disagreement residualization, policy routing, evaluation engines, FastAPI REST backend, and regression test suites.
- TypeScript 5.6.3 - Frontend dashboard application logic, type definitions, API clients, and React Three Fiber 3D canvas integrations (`frontend/src/`).

**Secondary:**
- JavaScript (ES Modules, Node.js v20.20.0) - Vite dev/build tooling, tooling shims (`gsd-tools.cjs`), and configuration scripts.
- CSS3 (Vanilla CSS with design tokens) - Complete design system styling (`frontend/src/styles/tokens.css`, `layout.css`, `components.css`, `animations.css`, `global.css`).
- Windows Batch Scripting (`.bat`) - Demo orchestration scripts (`scripts/start_demo.bat`, `scripts/stop_demo.bat`).
- YAML / JSON / JSONL - Project configuration (`config.yaml`), metadata manifests, frozen policy states (`policy/frozen_policy.json`), evaluation benchmarks (`results/results.json`), and streaming offline replay ledgers (`results/replay_rows.jsonl`, `results/cases.jsonl`).

## Runtime

**Environment:**
- Python Runtime: CPython 3.13.7 (Win32 64-bit)
- JavaScript Runtime: Node.js v20.20.0 / npm 10.8.2
- OS Platform: Microsoft Windows 11 / Windows Server (PowerShell / cmd.exe)

**Package Manager:**
- Python: `pip` via `backend/requirements.txt`
  - Lockfile: Implicit via exact package pins in documentation and environment requirements
- Node.js: `npm` with `frontend/package-lock.json`
  - Lockfile: `frontend/package-lock.json` present and committed

## Frameworks

**Core:**
- FastAPI 0.115.0+ (`backend/app/main.py`) - High-performance asynchronous REST API server exposing health, readiness status, overview metrics, policy comparisons, streaming replay rows, audit trails, and the sandbox scoring endpoint.
- Uvicorn 0.32.0+ - ASGI web server implementation.
- Pydantic 2.10.0+ (`backend/app/schemas.py`) - Strong request/response schema validation, recursive target leakage rejection, and deserialization.
- React 18.3.1 (`frontend/src/App.tsx`, `frontend/src/main.tsx`) - Declarative UI library running in strict single-page application mode.
- Vite 5.4.11 (`frontend/vite.config.ts`) - Next-generation frontend build tool and local development server with Hot Module Replacement (HMR).
- React Router DOM 6.28.0 (`frontend/src/app/router.tsx`) - Client-side declarative routing supporting 7 operational routes (`/overview`, `/policy-comparison`, `/shift-storm`, `/case-explorer`, `/sandbox`, `/drift-shift`, `/audit-trail`, `/model-card`).

**Data Science & Machine Learning:**
- scikit-learn 1.6.0+ - Core estimator implementations (`HistGradientBoostingClassifier`, `LogisticRegression`), preprocessing (`StandardScaler`), calibration (`CalibratedClassifierCV`), and metrics.
- NumPy 2.0.0+ & Pandas 2.2.0+ - Tabular data manipulation, array mathematics, and feature vector construction.
- SciPy 1.15.0+ - Scientific computing, statistical distribution calculations, and optimization.
- Joblib 1.4.0+ - High-throughput serialized pipeline persistence and atomic disk loading (`models/artifacts/*.joblib`).

**3D Graphics & Visualization:**
- Three.js 0.160.0 (`frontend/src/components/SignalCoreScene.tsx`, `SandboxDecisionOrb3D.tsx`) - WebGL scene graph, custom shaders, and 3D geometric mesh rendering.
- @react-three/fiber 8.17.10 - Declarative Three.js abstraction for React components.
- Recharts 2.13.3 (`frontend/src/features/policy-comparison/PolicyComparisonPage.tsx`) - Responsive SVG data visualization charts (bar charts, line charts, calibration curves).
- Lucide React 0.460.0 - Comprehensive technical icon library.
- Fontsource Typography (`@fontsource/ibm-plex-sans`, `@fontsource/courier-prime`) - Authoritative cockpit typography with tabular numerals.

**Testing:**
- Pytest 9.1.1 (`tests/`) - Python unit and regression test runner with 109 passing automated test cases across backend, policy, scoring, security, and calibration suites.
- Vitest 2.1.8 (`frontend/src/components/__tests__/`) - Fast Vite-native unit test runner for React components, GLB asset loaders, and UI regression assertions (21 tests).

## Key Dependencies

**Critical:**
- `scikit-learn` (`>=1.6.0`): Powers the primary risk estimator `HistGradientBoostingClassifier`, calibration regressors, and rank residualization.
- `fastapi` (`>=0.115.0`) & `pydantic` (`>=2.10.0`): Guarantees strictly validated API boundaries with zero model degradation or input payload leakage.
- `three` (`^0.160.0`) & `@react-three/fiber` (`^8.17.10`): Powers the real-time Signal Core Planar Radar and 3D Sandbox Decision Orb.
- `joblib` (`>=1.4.0`): Manages zero-copy model checkpointing and deterministic artifact loading.

**Infrastructure:**
- `httpx` (`>=0.28.0`): High-performance HTTP client used for FastAPI `TestClient` integration suites.
- `pyyaml` (`>=6.0.2`): Parses system-wide configuration contract `config.yaml`.

## Configuration

**Environment:**
- No mandatory external `.env` secrets required. Operates in 100% self-contained offline mode (`SYNTHETIC_SMOKE_ONLY`).
- Optional environment overrides supported:
  - `PORT`: Override API server port (default: 8000).
  - `HOST`: Override API server host binding (default: 127.0.0.1).
  - `CORS_ORIGINS`: Comma-separated CORS allowed origins.

**Build:**
- Root ML & Pipeline Config: `config.yaml`
- Frozen Decision Policy: `policy/frozen_policy.json`
- Frontend Build Config: `frontend/vite.config.ts`
- TypeScript Configurations: `frontend/tsconfig.json`, `frontend/tsconfig.app.json`, `frontend/tsconfig.node.json`

## Platform Requirements

**Development:**
- Windows 10/11, macOS, or Linux x86_64/ARM64.
- Python 3.13+ installed and accessible via PATH.
- Node.js 20+ and npm 10+ installed.
- Memory: Minimum 4 GB RAM recommended.
- Storage: ~1.5 GB for repository, dependencies (`node_modules`), datasets, and serialized model artifacts.

**Production / Demonstration Target:**
- Local offline verification workstation (`SYNTHETIC_SMOKE_ONLY`).
- Zero outbound network connectivity required for full operational walkthrough.

---

*Stack analysis: 2026-10-18*
