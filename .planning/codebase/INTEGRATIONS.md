# External Integrations

**Analysis Date:** 2026-10-18

## APIs & External Services

**Internal Dashboard-to-Backend REST Interface:**
- Service: FastAPI REST Service (`backend/app/main.py`)
  - Client / SDK: Custom TypeScript Fetch API Client (`frontend/src/lib/api/client.ts`) and React query hooks (`frontend/src/lib/api/hooks.ts`)
  - Base URL: `http://127.0.0.1:8000/api` (configurable via `VITE_API_URL` or default fallback)
  - Endpoints consumed:
    - `GET /api/health` - Fast process liveness verification
    - `GET /api/status` - Exhaustive subsystem readiness and hash integrity
    - `GET /api/overview` - Summary evaluation metrics ($N=2,000$, fraud prevalence, baseline delta, CI bounds)
    - `GET /api/policies/compare` - Budget sweep and matched-capacity comparisons ($1.0\times$, $1.5\times$, $2.0\times$, $3.0\times$)
    - `GET /api/replay/rows` - Paginated offline telemetry stream (2,000 rows)
    - `GET /api/cases` & `GET /api/cases/{case_id}` - Case search, filtering, and dossier inspection
    - `POST /api/score-sandbox` - Live feature vector evaluation through ML pipeline and frozen policy router
    - `GET /api/audit` - Append-only governance log inspection

**External Third-Party APIs:**
- None detected or utilized. SignalGate operates strictly in self-contained, offline evaluation mode (`SYNTHETIC_SMOKE_ONLY`). No external cloud APIs (e.g. OpenAI, Stripe, AWS, Datadog) are imported or executed.

## Data Storage

**Databases:**
- None (zero database daemon dependencies). No PostgreSQL, SQLite, MySQL, or MongoDB. All operational state is file-backed for deterministic reproducibility.

**File Storage (Local Filesystem):**
- Primary Synthetic Fixture: `data/synthetic_smoke_fixture.csv` (10,000 synthetic transaction records with 394 features)
- Model Artifacts Directory: `models/artifacts/` containing 6 serialized scikit-learn/Joblib objects:
  - `hgb_base.joblib`: Histogram-based Gradient Boosting classifier
  - `logistic_base.joblib`: Logistic Regression baseline classifier
  - `calibrator_sigmoid.joblib`: Platt scaling calibrator
  - `calibrator_isotonic.joblib`: Isotonic regression calibrator
  - `ensemble_members.joblib`: Diversity ensemble member pipelines
  - `residualizer_u2.joblib`: OLS rank residualizer for disagreement $u_2$
  - Companion JSON manifests (`*.meta.json`) recording commit, timestamp, feature names, and hashes
- Streaming & Case Records:
  - `results/replay_rows.jsonl`: 2,000 serialized chronological test evaluations
  - `results/cases.jsonl`: Case ledger indexed by `case_id`
- Evaluation Benchmarks & Reports:
  - `results/results.json`: Canonical evaluation benchmark report ($N=2,000$)
  - `results/split_report.json`: Train/calib/val/test deterministic partition index
  - `results/model_report.json`: Individual estimator performance metrics
  - `results/calibration_report.json`: Reliability diagrams and ECE metrics
  - `results/ensemble_report.json`: Inter-model correlation and disagreement distributions
  - `results/policy_report.json`: Router and governor threshold validation

**Caching:**
- In-memory service caching: `backend/app/services/artifacts.py` maintains an mtime-aware in-memory dictionary cache (`_cache`) for all parsed JSON artifacts to minimize disk I/O while ensuring instant hot-reloading when files change.

## Authentication & Identity

**Auth Provider:**
- Custom / Disabled for offline demonstration mode.
- Rationale: Designed as a local research prototype and audit control room; all API routes are unauthenticated by design for offline peer verification.
- CORS Security: Strict origin restrictions configured in `backend/app/config.py` bound to `http://localhost:5173` and `http://127.0.0.1:5173`.

## Monitoring & Observability

**Error Tracking:**
- Local structured logging and standardized JSON error responses (`backend/app/schemas.py:ErrorResponse`).
- Global exception handlers in `backend/app/main.py` converting `HTTPException`, `RequestValidationError`, and unexpected exceptions into uniform error payloads with error codes (`VALIDATION_ERROR`, `INTERNAL_SERVER_ERROR`, `MODEL_ARTIFACTS_UNAVAILABLE`).

**Governance & Audit Logs:**
- Real-time decision audit log: `logs/audit.jsonl` (appends timestamp, decision ID, input feature vector, latency, signals, and routing decisions for every `POST /api/score-sandbox` request).
- Test set access governance: `logs/test_looks.log` (tamper-evident audit ledger tracking the pre-registered G3 and G5 test-look executions).

## CI/CD & Deployment

**Hosting:**
- Local execution environment. Hosted locally via Uvicorn (FastAPI) and Vite (React).

**Demonstration Orchestration:**
- Windows Launcher: `scripts/start_demo.bat` (runs artifact integrity validation, checks port conflicts, and spawns parallel dev servers).
- Safe Teardown: `scripts/stop_demo.bat` (targets port 8000 and 5173 listener PID mappings for clean termination without affecting other developer tasks).

## Environment Configuration

**Required Environment Variables:**
- None required. All defaults are hardcoded to safe offline constants.

**Optional Environment Variables:**
- `PORT`: Override API port (default: `8000`).
- `HOST`: Override API interface binding (default: `127.0.0.1`).
- `VITE_API_URL`: Override frontend API base path.

**Secrets Location:**
- No secrets or API credentials exist in this repository.

## Webhooks & Callbacks

**Incoming:**
- None.

**Outgoing:**
- None.

---

*Integration audit: 2026-10-18*
