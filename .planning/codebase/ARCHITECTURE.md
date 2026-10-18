<!-- refreshed: 2026-10-18 -->
# Architecture

**Analysis Date:** 2026-10-18

## System Overview

```text
┌─────────────────────────────────────────────────────────────────────────────────────────────┐
│                           OPERATIONAL COCKPIT (React 18 SPA)                                │
├───────────────────────────────┬───────────────────────────────┬─────────────────────────────┤
│   Overview & Signal Core      │   Policy Comparison           │   Shift Storm Replay        │
│   `frontend/src/features/`    │   `frontend/src/features/`    │   `frontend/src/features/`  │
│   `overview/OverviewPage.tsx` │   `policy-comparison/...`     │   `shift-storm/...`         │
├───────────────────────────────┼───────────────────────────────┼─────────────────────────────┤
│   Case Explorer Dossiers      │   Scoring Sandbox & 3D Orb    │   Audit Trail & Model Card  │
│   `case-explorer/...`         │   `sandbox/SandboxPage.tsx`   │   `audit-trail/`, `model-`  │
└───────────────────────────────┴───────────────┬───────────────┴─────────────────────────────┘
                                                │ HTTP / REST (Vite Proxy / Fetch Client)
                                                ▼
┌─────────────────────────────────────────────────────────────────────────────────────────────┐
│                           FASTAPI DECISION SERVICE (Port 8000)                              │
├───────────────────────────────┬───────────────────────────────┬─────────────────────────────┤
│   API Routers                 │   Request Validation (Pydantic│   Service Layer             │
│   `backend/app/routers/`      │   `backend/app/schemas.py`    │   `backend/app/services/`   │
│   (health, overview, policies,│   - Leakage prevention        │   - `scoring.py`            │
│    cases, replay, scoring)    │   - Finite scalar enforcement │   - `artifacts.py`          │
└───────────────────────────────┴───────────────┬───────────────┴─────────────────────────────┘
                                                │
         ┌──────────────────────────────────────┴──────────────────────────────────────┐
         ▼                                                                            ▼
┌─────────────────────────────────────────────────────────────┐  ┌────────────────────────────────────────────┐
│               ML PIPELINE & INFERENCE STAGE                 │  │        DECISION POLICY & GOVERNOR          │
├─────────────────────────────────────────────────────────────┤  ├────────────────────────────────────────────┤
│ 1. Feature Preprocessing (`data/schema.py`)                 │  │ 1. Decision Router (`policy/router.py`)    │
│    - Strips target & raw IDs                                │  │    - $p \ge t_{\text{alert}} \rightarrow$  │
│ 2. Primary Estimator (`models/base.py`)                     │  │      `FRAUD_ALERT` (R1)                    │
│    - `HistGradientBoostingClassifier`                       │  │    - $p \ge t_{\text{rev}} \lor u_2 \ge u$ │
│ 3. Platt Probability Calibration (`models/calibrate.py`)    │  │      $\rightarrow \text{MANUAL_REVIEW}$    │
│    - Converts margin to calibrated probability $p$          │  │    - Else $\rightarrow \text{ROUTINE}$ (R5)│
│ 4. Epistemic Disagreement Ensembles (`models/ensemble.py`)  │  │ 2. Capacity Governor (`policy/governor.py`)│
│    - Computes variance residualized on risk rank ($u_2$)    │  │    - Bounded review quota ($B=130$)        │
│                                                             │  │    - Overflow $\rightarrow \text{DEFERRED}$│
└─────────────────────────────────────────────────────────────┘  └────────────────────────────────────────────┘
                                                │
                                                ▼
┌─────────────────────────────────────────────────────────────────────────────────────────────┐
│                          PERSISTENT FILE-BACKED DATA & ARTIFACTS                            │
│  `data/synthetic_smoke_fixture.csv`  │  `models/artifacts/*.joblib`  │  `results/results.json`│
│  `results/replay_rows.jsonl`         │  `policy/frozen_policy.json`  │  `logs/audit.jsonl`    │
└─────────────────────────────────────────────────────────────────────────────────────────────┘
```

## Component Responsibilities

| Component | Responsibility | File |
|-----------|----------------|------|
| **FastAPI Gateway** | API routing, lifespan handling, CORS policy, and error normalization | `backend/app/main.py` |
| **Artifact Service** | Caching, disk freshness checking, and SHA-256 verification of evaluation outputs | `backend/app/services/artifacts.py` |
| **Scoring Service** | End-to-end sandbox inference execution, feature preprocessing, and leakage guards | `backend/app/services/scoring.py` |
| **Decision Router** | Deterministic rule-based triage action mapping ($p, u_2, n$) with fail-closed safety | `policy/router.py` |
| **Capacity Governor** | Bounded reviewer queue enforcement ($B=130$) with risk-ordered tie breaking and deferred shunting | `policy/governor.py` |
| **Primary Estimator** | Non-linear tree boosting on tabular transaction features | `models/base.py` |
| **Calibrator** | Platt scaling sigmoid transformation to guarantee posterior calibration ($ECE \le 0.001$) | `models/calibrate.py` |
| **Disagreement Engine** | Model diversity variance extraction and OLS rank residualization ($u_2$) | `models/ensemble.py` |
| **Statistical Evaluator** | Paired bootstrap hypothesis testing and 95% confidence interval estimation | `eval/bootstrap.py` |
| **App Shell & Router** | Cockpit layout, navigation state, theme switching, and client route mounting | `frontend/src/app/AppShell.tsx`, `router.tsx` |
| **Signal Core Radar** | Three.js planar disk mapping transactions across risk rings and uncertainty angles | `frontend/src/components/SignalCoreScene.tsx` |
| **API Client & Hooks** | Type-safe HTTP fetch client and React component data binding | `frontend/src/lib/api/client.ts`, `hooks.ts` |

## Pattern Overview

**Overall:** Decoupled ML Decision-Support Service with Layered Policy Governance and Zero-Leakage Ingestion.

**Key Characteristics:**
- **Separation of Risk Estimation from Governance:** Machine learning models predict only risk $p$ and epistemic disagreement $u_2$. All decisions to alert, review, pass, or defer are strictly owned by deterministic policy layers (`policy/router.py` and `policy/governor.py`).
- **Fail-Closed Safety:** Missing features, non-finite values, or uncalibrated margins automatically fail closed to `MANUAL_REVIEW` / `R0_SIGNAL_UNAVAILABLE`. Under no circumstances can corrupted inputs default to `ROUTINE` clearance.
- **Matched-Capacity Evaluation:** Benchmark evaluation against baselines B1, B2, B3a, and B4 is strictly conducted at identical touched capacity ($B = 130$ cases, $6.525\%$ touched rate) to eliminate capacity confounding.
- **Strict Anti-Leakage Sandbox:** Sandbox scoring inputs are recursively audited to forbid ground truth (`isFraud`, `true_label`) and database row identifiers (`TransactionID`).

## Layers

**1. Presentation Layer (`frontend/src/`):**
- Purpose: Operational control room interface for fraud analysts and risk engineers.
- Location: `frontend/src/`
- Contains: React components, Three.js canvases, CSS design system, and custom hooks.
- Depends on: Backend REST endpoints exposed at `/api/*`.
- Used by: Human operators in the browser.

**2. API & Contract Layer (`backend/app/`):**
- Purpose: HTTP request routing, schema deserialization, parameter validation, and response formatting.
- Location: `backend/app/routers/`, `backend/app/schemas.py`, `backend/app/services/`
- Contains: FastAPI APIRouters, Pydantic DTOs, and lifecycle dependencies.
- Depends on: Policy engine and serialized model artifacts.
- Used by: Frontend application and automated test clients.

**3. Decision Policy Layer (`policy/`):**
- Purpose: Business logic, review queue management, and audit logging.
- Location: `policy/router.py`, `policy/governor.py`, `policy/thresholds.py`, `policy/audit.py`
- Contains: Routing state machine, capacity governor priority queues, and cryptographic audit records.
- Depends on: Model inference outputs ($p, u_2$).
- Used by: API scoring service and offline evaluation batch scripts.

**4. Machine Learning & Inference Layer (`models/`, `data/`):**
- Purpose: Feature extraction, model fitting, prediction, probability calibration, and ensemble disagreement estimation.
- Location: `models/base.py`, `models/calibrate.py`, `models/ensemble.py`, `data/features.py`, `data/schema.py`
- Contains: Estimator pipelines, sigmoid calibrators, and residualizers.
- Depends on: Scikit-learn, NumPy, Pandas, and local Joblib artifacts.
- Used by: Scoring service and evaluation scripts.

**5. Evaluation & Benchmarking Layer (`eval/`, `scripts/`):**
- Purpose: Offline statistical verification, paired bootstrap sampling, drift monitoring, and baseline comparison.
- Location: `eval/bootstrap.py`, `eval/metrics.py`, `eval/drift.py`, `scripts/run_phase5_evaluation.py`
- Contains: 1000-sample bootstrap loops, PSI calculations, and test look ledgers.
- Depends on: Model outputs, policy definitions, and split manifests.
- Used by: Verification scripts to produce `results/results.json`.

## Data Flow

### Primary Request Path (Sandbox Scoring)

1. **User Submission:** Operator enters transaction features or selects a preset in `/sandbox` (`frontend/src/features/sandbox/SandboxPage.tsx`).
2. **Client Validation:** Client-side validator checks for prohibited fields (`isFraud`, `TransactionID`) before network transmission.
3. **HTTP Dispatch:** JSON POST sent via `frontend/src/lib/api/client.ts:scoreSandbox()`.
4. **Endpoint Ingestion:** `backend/app/routers/scoring.py:score_sandbox()` receives `SandboxScoreRequest`.
5. **Leakage Guard:** `backend/app/schemas.py:SandboxScoreRequest:reject_forbidden_features()` performs recursive validation and rejects any target labels or non-finite values (HTTP 422/400).
6. **Feature Matrix Formulation:** `backend/app/services/scoring.py:score_sandbox_transaction()` constructs a single-row Pandas DataFrame and casts numeric/categorical fields per `data/schema.py`.
7. **Model Inference:** `models/base.py` evaluates the `HistGradientBoostingClassifier` and applies Platt sigmoid scaling (`models/calibrate.py`) to yield calibrated posterior probability $p$.
8. **Disagreement Computation:** `models/ensemble.py` queries the 5 ensemble members, extracts raw prediction variance, and projects it through `residualizer_u2.joblib` to produce rank-residualized disagreement $u_2$.
9. **Policy Routing:** `policy/router.py:route()` evaluates frozen thresholds ($t_{\text{alert}} = 0.084705, t_{\text{review}} = 0.071002, u_{\text{threshold}} = 0.526773$) and yields an `Action` and `ReasonCode`.
10. **Capacity Governance:** `policy/governor.py` verifies capacity availability and assigns `governor_status` (`admitted_review`, `admitted_alert`, or `deferred`).
11. **Audit Logging:** An immutable record is appended to `logs/audit.jsonl` with nanosecond timestamp and decision ID.
12. **Response Rendering:** HTTP 200 returned with `SandboxScoreResponse`; frontend visualizes signals and animates the 3D Decision Orb.

## Key Abstractions

**Action & ReasonCode (`policy/router.py`):**
- Purpose: Auditable, finite-state triage outcome enumeration.
- Enums:
  - `Action`: `FRAUD_ALERT`, `MANUAL_REVIEW`, `ROUTINE`, `HELD`, `DEFERRED`.
  - `ReasonCode`: `R0_SIGNAL_UNAVAILABLE`, `R1_HIGH_RISK`, `R2_INTERMEDIATE_RISK`, `R3_MODEL_DISAGREEMENT`, `R4_UNFAMILIAR_INPUT`, `R5_LOW_RISK_RELIABLE`, `R6_CAPACITY_DEFERRED`.

**CapacityGovernor (`policy/governor.py`):**
- Purpose: Deterministic capacity regulator enforcing analyst review budgets without silent leaks.
- Pattern: Strategy / Priority Filter with stable secondary index tie-breaking.

**ArtifactService (`backend/app/services/artifacts.py`):**
- Purpose: Thread-safe, mtime-aware singleton for loading, caching, and cryptographically validating disk artifacts.
- Pattern: Singleton with mtime invalidation cache.

**SignalCoreScene (`frontend/src/components/SignalCoreScene.tsx`):**
- Purpose: WebGL / R3F Canvas representing multi-dimensional risk and epistemic uncertainty as a 2.5D planar radar disk.
- Pattern: Declarative React Three Fiber scene with 2D SVG vector fallback (`SignalCoreFallback.tsx`).

## Entry Points

**API Server:**
- Location: `backend/app/main.py:app`
- Triggers: Launched via `python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000` or `scripts/start_demo.bat`.
- Responsibilities: Serves REST API and Swagger UI.

**Frontend Dashboard:**
- Location: `frontend/src/main.tsx` & `frontend/src/App.tsx`
- Triggers: Launched via `npm run dev` in `frontend/` or `scripts/start_demo.bat`.
- Responsibilities: Boots React application and mounts client router.

**Evaluation Pipeline:**
- Location: `scripts/run_phase5_evaluation.py`
- Triggers: Executed via Python during verification phases.
- Responsibilities: Runs full evaluation on test partition and generates `results/results.json`.

## Architectural Constraints

- **Single Machine / Localhost Binding:** All services communicate exclusively over `127.0.0.1` (`8000` for backend, `5173` for frontend).
- **Synthetic Smoke Constraint:** All data and results are synthetic fixtures (`SYNTHETIC_SMOKE_ONLY`). Production payment gateway connectivity is prohibited.
- **Read-Only Test Ledger:** Test set evaluation is governed by pre-registered looks (`logs/test_looks.log`) to prevent p-hacking and iterative threshold overfitting.
- **Stateless Scoring API:** `POST /api/score-sandbox` maintains no in-memory user sessions or cumulative state; every evaluation is pure and independently audited to disk.

## Anti-Patterns

### Silent Failure to Routine Clearance
**What happens:** Traditional fraud systems that encounter missing features, NaN signals, or queue overcapacity often default to clearing the transaction.
**Why it's wrong:** Silent fraud leakage occurs during operational outages or capacity saturation.
**Do this instead:** SignalGate strictly shunts missing signals to `MANUAL_REVIEW` / `R0_SIGNAL_UNAVAILABLE` and queue overcapacity to `DEFERRED` / `R6_CAPACITY_DEFERRED` (`policy/router.py:route()`, `policy/governor.py:govern()`).

### Raw Epistemic Disagreement Confounding
**What happens:** Using raw ensemble standard deviation as a disagreement metric without correcting for predicted risk.
**Why it's wrong:** High-risk transactions naturally exhibit higher variance near decision boundaries, causing false disagreement alarms on transactions already detected by the primary model.
**Do this instead:** SignalGate uses $u_2$ (inter-model variance residualized against risk rank via OLS regression in `models/ensemble.py`), isolating genuine covariate shift.

## Error Handling

**Strategy:** Uniform JSON error envelopes with structured error codes and HTTP status codes.
- `400 BAD REQUEST`: Invalid feature schema or malformed JSON.
- `422 UNPROCESSABLE ENTITY`: Leakage guard triggered (presence of `isFraud`, `TransactionID`, or non-finite values).
- `503 SERVICE UNAVAILABLE`: Serialized model artifacts or frozen policy missing from disk.
- `500 INTERNAL SERVER ERROR`: Unhandled runtime exceptions with scrubbed stack traces.

## Cross-Cutting Concerns

**Logging:**
- Standard Python logging with structured JSON formatting for operational events.
- Immutable append-only disk logging for sandbox scoring decisions (`logs/audit.jsonl`).

**Validation:**
- Strict Pydantic models for incoming requests and outgoing responses (`backend/app/schemas.py`).
- Deterministic cryptographic hashing (`split_hash`, `config_hash`, `dataset_sha256`) checked at startup.

---

*Architecture analysis: 2026-10-18*
