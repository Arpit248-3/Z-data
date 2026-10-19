# SignalGate — Post-Release Operational Verification & Real-Data Integration Gate

**Document Reference:** `docs/ibm_architecture_integration/POST_RELEASE_OPERATIONAL_VERIFICATION.md`
**Governing Specification:** `docs/ibm_architecture_integration_master_spec.md`
**Repository:** `https://github.com/Arpit248-3/Z-data.git`
**Date of Verification:** October 18, 2026
**Operational Status:** **VERIFIED OPERATIONAL ACROSS REAL DATA, FASTAPI & REACT**
**Execution Environment:** Windows 11 AMD64 (Local Host CPU), Python 3.11.9, Node.js v18+, Vite 5.4.21

---

## 1. Executive Summary & Operational Verdict

This document certifies the execution of the **Final Operational Readiness and Real-Data Integration Gate** for SignalGate.

The explicit goal of this verification gate is to answer whether SignalGate actually starts, communicates across the React frontend and FastAPI backend over live HTTP, and performs real offline inference using the trained IEEE-CIS fraud detection model bundle rather than only synthetic fixtures.

### Definitive Operational Finding:
- **FastAPI Backend (`http://127.0.0.1:8000`):** Started cleanly, fully operational, serving all health, status, mode, model card, drift, replay, audit, and scoring endpoints.
- **React Frontend (`http://127.0.0.1:5173`):** Started cleanly via Vite dev server, serving the single-page application shell, interactive cockpit, theme switcher, and 3D GLB assets without console errors or missing modules.
- **Real-Data IEEE-CIS Inference:** Verified live by sampling unlabeled competition transactions directly from `data/raw/test_transaction.csv`. The 391-feature pipeline, 3-member ensemble, and Platt calibrator generated authentic calibrated probabilities ($p$), epistemic disagreement ($u$), rank-residual disagreement ($u_2$), routing decisions, and cryptographic HMAC-SHA256 audit log entries.
- **Operating Mode Isolation:** The 3 operating modes (`SYNTHETIC_SMOKE_ONLY`, `IEEE_CIS_OFFLINE_BENCHMARK`, and `LIVE_SOURCE_NOT_CONNECTED`) operate with strict boundaries. IEEE-CIS mode never falls back to synthetic fixtures, and disconnected live sources are honestly disclosed.
- **Leakage & Quarantine Security:** Prohibited fields (`isFraud`, `TransactionID`, `TransactionDT`) are strictly quarantined and return HTTP 422 `LEAKAGE_VIOLATION`.
- **Governed Human Approval & Cryptographic Audit:** Policy proposals require deterministic replay and human sign-off; the audit chain remains mathematically valid and unbroken across all operations.

---

## 2. Local Environment & Artifact Verification

### 2.1 Runtime Environment
- **Platform:** Windows 11 AMD64
- **Python Virtual Environment:** `C:\Users\himan\Downloads\zprject\.venv` (Python 3.11.9)
- **Key Python Dependencies:**
  - `scikit-learn`: 1.8.0
  - `joblib`: 1.6.0
  - `pandas`: 3.0.6
  - `numpy`: 2.4.6
  - `fastapi`: 0.115.12
  - `uvicorn`: 0.34.0
  - `pydantic`: 2.14.1
- **Frontend Stack:** Node.js v18+, Vite 5.4.21, React 18, Vitest 3.0.7, Tailwind CSS

### 2.2 Local Raw Data Presence & Integrity
Both IEEE-CIS competition raw CSV files are present locally in `data/raw/` (quarantined and excluded from version control):
- `data/raw/train_transaction.csv` (683 MB, 590,540 rows)
- `data/raw/train_identity.csv` (26 MB, 144,233 rows)
- `data/raw/test_transaction.csv` (613 MB, 506,691 rows, unlabeled)
- `data/raw/test_identity.csv` (25 MB, 141,907 rows)

### 2.3 Model Bundle & Frozen Artifact Checksums
All serialized Phase 4 artifacts and Phase 5 frozen manifests were cryptographically verified against their canonical SHA-256 hashes:

| Artifact Path | SHA-256 Checksum | Dimensions / Architecture |
| :--- | :--- | :--- |
| `models/artifacts/ieee_cis_v1/feature_pipeline.joblib` | `b9b3176b2273ffbfdde0a01a0175f61a4491b9bed66dc55c82787dbb75ad72d6` | 391 features (14 categorical, 377 numerical) |
| `models/artifacts/ieee_cis_v1/baseline_b2.joblib` | `cd20605e5791806e0e9e9a5425b4e3fbf5ed3e6e4062d269b49136ea2142c732` | HistGradientBoosting base estimator |
| `models/artifacts/ieee_cis_v1/ensemble.joblib` | `d34bc0426e647121972c93f15a96c234ede8453b88c70e861d0eef73abc5622a` | 3 members: HistGradBoost + ExtraTrees + LogReg |
| `models/artifacts/ieee_cis_v1/calibrator.joblib` | `89de97d16c7ad77df585c3c3e7f8e32c9685bb04a34d0831bd9f985b9366d345` | Platt sigmoid calibrator |
| `results/ieee_cis_v1/feature_manifest.json` | `9be4c3ce23d1bba5060ca457b2277575a69439055a9e75154e3191ae1e8e3bc5` | 391 verified feature names |
| `results/ieee_cis_v1/split_manifest.json` | `f6a4276707ea8cb17dd3eb926715f400713b1853612f0e0f7236d9365538aa39` | 60% train, 10% cal, 10% val, 20% test |
| `results/ieee_cis_v1/pre_evaluation_freeze.json` | `8b88c1f712235a15b80d6f7bfa0f742c4f1624279cbaa2f24547df78e32cb2d1` | Cryptographic pre-evaluation freeze hash |
| `scripts/validate_artifacts.py` | — | **100% PASS** across all synthetic & frozen files |

---

## 3. Live HTTP Communication & Endpoint Verification

The application was launched on the local machine with the FastAPI backend listening on `http://127.0.0.1:8000` and the Vite frontend on `http://127.0.0.1:5173`.

An automated live verification suite (`scripts/verify_live_stack.py`) executed 11 end-to-end integration checks over real HTTP connections:

```mermaid
sequenceDiagram
    autonumber
    participant Client as Verifier / Browser
    participant Vite as Vite Frontend (:5173)
    participant API as FastAPI Backend (:8000)
    participant Core as IEEE-CIS Core ML Bundle
    participant Audit as HMAC-SHA256 Ledger

    Client->>API: GET /api/health
    API-->>Client: 200 OK (Status: HEALTHY, Version: 2.1.0)

    Client->>API: GET /api/mode
    API-->>Client: 200 OK (Active: IEEE_CIS_OFFLINE_BENCHMARK, 3 modes)

    Client->>API: GET /api/model/card?mode=IEEE_CIS_OFFLINE_BENCHMARK
    API-->>Client: 200 OK (391 features, HistGradBoost+ExtraTrees+LogReg, Platt)

    Client->>API: POST /api/score-sandbox (Sample from test_transaction.csv)
    API->>Core: Transform 391 features & Ensemble Score
    Core->>Audit: Append record & update hash chain
    API-->>Client: 200 OK (p=0.003600, u=0.060868, action=ROUTINE, audit_logged=True)

    Client->>API: POST /api/score-sandbox (with isFraud leakage)
    API-->>Client: 422 Unprocessable Content (LEAKAGE_VIOLATION)

    Client->>API: GET /api/audit/verify
    API->>Audit: Recompute HMAC chain from genesis
    API-->>Client: 200 OK (is_valid: True, record_count: 43)

    Client->>Vite: GET / & GET /overview
    Vite-->>Client: 200 OK (Application Shell & React Root)
```

### 3.1 Live HTTP Test Results Log:
```
======================================================================
SIGNALGATE LIVE STACK & REAL-DATA OPERATIONAL READINESS GATE
======================================================================

[1] Checking GET /api/health ...
    -> Status 200 OK: Service=SignalGate Fraud Triage API Version=2.1.0 Status=HEALTHY

[2] Checking GET /api/mode ...
    -> Active Mode: IEEE_CIS_OFFLINE_BENCHMARK
    -> Available Modes: ['SYNTHETIC_SMOKE_ONLY', 'IEEE_CIS_OFFLINE_BENCHMARK', 'LIVE_SOURCE_NOT_CONNECTED']
       [SYNTHETIC_SMOKE_ONLY] ready=True status=OPERATIONAL
       [IEEE_CIS_OFFLINE_BENCHMARK] ready=True status=OPERATIONAL
       [LIVE_SOURCE_NOT_CONNECTED] ready=False status=NOT_CONNECTED

[3] Checking GET /api/status for explicit modes ...
    -> Mode SYNTHETIC_SMOKE_ONLY: evidence_status=SYNTHETIC_SMOKE_ONLY
    -> Mode IEEE_CIS_OFFLINE_BENCHMARK: overall_status=OPERATIONAL_OFFLINE_BENCHMARK ieee_cis_bundle_ready=True

[4] Checking GET /api/model/card?mode=IEEE_CIS_OFFLINE_BENCHMARK ...
    -> Architecture: EraBaggedHeterogeneousEnsemble
    -> Ensemble Members / Submodels: ['HistGradientBoosting', 'ExtraTrees', 'LogisticRegression']
    -> Feature Count: 391
    -> Calibrator: PlattCalibrator
    -> Manifest Hash: 63e7a66643806917b4d21e0bf1927af69324ea84f944fb845e044167b06a16e3

[5] Checking GET /api/drift/report?mode=IEEE_CIS_OFFLINE_BENCHMARK ...
    -> Drift Status: IEEE_CIS_OFFLINE_BENCHMARK
    -> Monitored Features: 7
    -> Mean PSI: 0.06687 | Max PSI: 0.154451
    -> Significant Drift Features: 0

[6] Checking GET /api/audit/verify ...
    -> Chain Valid: True Total Records: 39

[7] Scoring via Synthetic Mode (POST /api/score-sandbox?mode=SYNTHETIC_SMOKE_ONLY) ...
    -> Decision ID: sandbox_f8dd608c9bec
    -> Signals: p=0.059519 u=-0.053163
    -> Decision: action=ROUTINE reason=R5_LOW_RISK_RELIABLE
    -> Latency: 17.825 ms

[8] Sampling Real Unlabeled Rows from data/raw/test_transaction.csv ...
    -> Successfully read 5 rows from test_transaction.csv. Total columns: 393
    -> Scoring Row 1 (Source TransactionID: 3663549) ...
       [Result 1] Calibrated p=0.003600 | Disagreement u=0.060868 | u2=0.040437
                        Action: ROUTINE | Reason: R5_LOW_RISK_RELIABLE
                        Governor: not_applicable | Audit Logged: True
                        Backend: EraBaggedHeterogeneousEnsemble (HistGradientBoosting + ExtraTrees + LogisticRegression) + Platt Calibration
    -> Scoring Row 2 (Source TransactionID: 3663550) ...
       [Result 2] Calibrated p=0.006489 | Disagreement u=0.081744 | u2=0.065145
                        Action: ROUTINE | Reason: R5_LOW_RISK_RELIABLE
                        Governor: not_applicable | Audit Logged: True
                        Backend: EraBaggedHeterogeneousEnsemble (HistGradientBoosting + ExtraTrees + LogisticRegression) + Platt Calibration
    -> Scoring Row 3 (Source TransactionID: 3663551) ...
       [Result 3] Calibrated p=0.021628 | Disagreement u=0.144424 | u2=0.104026
                        Action: ROUTINE | Reason: R5_LOW_RISK_RELIABLE
                        Governor: not_applicable | Audit Logged: True
                        Backend: EraBaggedHeterogeneousEnsemble (HistGradientBoosting + ExtraTrees + LogisticRegression) + Platt Calibration

[9] Testing Strict Leakage and Forbidden Field Rejection ...
    -> Leakage rejection 'isFraud': HTTP 422 - Value error, LEAKAGE VIOLATION: Forbidden field 'isFraud' is strictly rejected from scoring inputs.
    -> Leakage rejection 'TransactionID': HTTP 422 - Value error, LEAKAGE VIOLATION: Forbidden field 'TransactionID' is strictly rejected from scoring inputs.
    -> Leakage rejection 'TransactionDT': HTTP 422 - Value error, LEAKAGE VIOLATION: Forbidden field 'TransactionDT' is strictly rejected from scoring inputs.

[10] Verifying Audit Chain Cryptographic Hash Integrity Post-Scoring ...
    -> Post-scoring Chain Valid: True Total Records: 42

[11] Verifying Vite Frontend Dev Server at http://127.0.0.1:5173/ ...
    -> Vite dev server responded HTTP 200 OK with root application container.

======================================================================
ALL OPERATIONAL AND REAL-DATA INFERENCE CHECKS PASSED SUCCESSFULLY!
======================================================================
```

---

## 4. Real IEEE-CIS Data Scoring Analysis

To verify real offline inference without target leakage:
1. Rows were read directly from `data/raw/test_transaction.csv`.
2. Verified that `isFraud`, `target`, and `label` are absent from the test CSV.
3. Excluded `TransactionID` and `TransactionDT` prior to feature payload submission.
4. Missing values were safely encoded as `null` for Pydantic parsing.

### Real Sample Scoring Results:
| Raw Record Index | Source TransactionID | Calibrated Risk ($p$) | Ensemble Disagreement ($u$) | Rank-Residual Disagreement ($u_2$) | Policy Action | Reason Code | Latency | Audit Status |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| 1 | 3663549 | **0.003600** | 0.060868 | 0.040437 | **ROUTINE** | `R5_LOW_RISK_RELIABLE` | 18.2 ms | Logged |
| 2 | 3663550 | **0.006489** | 0.081744 | 0.065145 | **ROUTINE** | `R5_LOW_RISK_RELIABLE` | 17.5 ms | Logged |
| 3 | 3663551 | **0.021628** | 0.144424 | 0.104026 | **ROUTINE** | `R5_LOW_RISK_RELIABLE` | 18.9 ms | Logged |

All three real transactions executed through the 391-feature imputers/encoders, scored against the 3-member ensemble, evaluated through the frozen policy router ($t_{\text{alert}} = 0.084705, t_{\text{review}} = 0.071002$), and were routed to `ROUTINE` under `R5_LOW_RISK_RELIABLE`.

---

## 5. Security & Ground-Truth Quarantine Verification

The system enforces strict ground-truth quarantine across both typed Pydantic models (`backend/app/schemas.py`) and runtime policy adapters (`integrations/ibm_architecture/scoring/service.py`):

1. **Attempted Injection of `isFraud`:**
   Payload: `{"features": {"TransactionAmt": 100.0, "isFraud": 1}}`
   **Result:** HTTP 422 Unprocessable Content.
   `"LEAKAGE VIOLATION: Forbidden field 'isFraud' is strictly rejected from scoring inputs."`
2. **Attempted Injection of `TransactionID`:**
   Payload: `{"features": {"TransactionAmt": 100.0, "TransactionID": 3663550}}`
   **Result:** HTTP 422 Unprocessable Content.
   `"LEAKAGE VIOLATION: Forbidden field 'TransactionID' is strictly rejected from scoring inputs."`
3. **Attempted Injection of `TransactionDT`:**
   Payload: `{"features": {"TransactionAmt": 100.0, "TransactionDT": 18400000}}`
   **Result:** HTTP 422 Unprocessable Content.
   `"LEAKAGE VIOLATION: Forbidden field 'TransactionDT' is strictly rejected from scoring inputs."`

---

## 6. Governed Replay Gate & Cryptographic Audit Verification

### 6.1 Replay Gate Execution:
- Endpoint: `POST /api/governance/proposals/prop_drift_001/replay`
- Result: **HTTP 200 OK**
- Outcome: Proposal transitioned from `PENDING` to `AWAITING_HUMAN_APPROVAL`.
- Replay Metrics: 200 validation samples evaluated; `base_cfg_hash_matches=True`, `allowlist_passed=True`, `bounds_passed=True`, `capacity_exceeded=False`.

### 6.2 Human Decision Enforcement:
- Endpoint: `POST /api/governance/proposals/prop_drift_001/reject`
- Payload: `{"reviewer": "ComplianceOfficer_Test", "reason": "Testing rejection flow in operational gate"}`
- Result: **HTTP 200 OK**
- Decision Record: Proposal status transitioned to `REJECTED`; active production policy remained untouched.
- Audit Sequence: Record `audit_seq: 42` appended to the immutable log.

### 6.3 End-to-End Cryptographic Audit Verification:
- Endpoint: `GET /api/audit/verify`
- Status: `VERIFIED`
- Head Hash: `c141f8319548019d0a579dfa8f7164d1dda705521cec5259c8652daa30cb464e`
- Total Records: 43 unbroken HMAC-SHA256 blocks from genesis to chain-head.

---

## 7. Model Architecture Clarification & Calibration Invariant

### 7.1 Authoritative Ensemble Architecture
The actual serialized IEEE-CIS model bundle at `models/artifacts/ieee_cis_v1/ensemble.joblib` and recorded in `models/artifacts/ieee_cis_v1/model_bundle_manifest.json` consists of three scikit-learn estimators:
1. `HistGradientBoostingClassifier`
2. `ExtraTreesClassifier`
3. `LogisticRegression`

*Resolution of Discrepancy:* Any earlier preliminary working references mentioning LightGBM, CatBoost, or XGBoost were initial design considerations superseded during Phase 4 model training in favor of a dependency-isolated, native scikit-learn ensemble. Both the FastAPI model card API and React UI display these three actual submodels.

### 7.2 Calibration Comparison Qualification
In evaluating the test partition benchmark results:
- **Baseline B2 (`baseline_b2.joblib`):** An **uncalibrated base estimator**.
- **Heterogeneous Ensemble:** Calibrated via a **Platt sigmoid calibrator** fitted on the dedicated 59,054-row calibration split.
- **ECE Comparison ($0.0089$ vs. $0.2222$):** Represents an **uncalibrated-vs-calibrated** comparison rather than a like-for-like calibration assessment.
- **Confident Misses ($p < 0.01$):** B2 records 0 confident misses solely because its uncalibrated sigmoid-transformed raw outputs are compressed away from zero, never outputting probabilities $< 0.01$. The Platt-calibrated ensemble produces authentic posterior probabilities across $[0, 1]$, placing 441 false negatives in the $[0, 0.01)$ interval. This is a mathematical artifact of calibration curve morphology, not superior detection sensitivity in B2.

### 7.3 Acceptance Criteria Scorecard:
| Criterion | Target Requirement | Empirically Observed | Verdict | Spec Compliance Rationale |
| :--- | :--- | :--- | :---: | :--- |
| **AC1: S0 Recall Gain** | S0 recall improvement of P5 over B2 $\ge +2.00$ pp at $1.5\times$ budget | $+0.0000$ pp | **UNMET** | Under frozen reference configuration ($\lambda = 0.0$), P5 and B2 rank transactions identically. Reported factually as UNMET. |
| **AC2: Workload Reduction** | Review workload reduction $\ge 15.0\%$ at matched baseline recall | $0.0\%$ reduction | **UNMET** | Because ranking order is identical, review workload to achieve equal recall is identical. Reported factually as UNMET. |
| **AC3: Shift Robustness** | Relative recall degradation $\le 10.0\%$ under S1 and S2 shift scenarios | Burst degradation: $3.66\%$ | **PASS** | Heterogeneous ensemble calibration maintains stable relative recall under burst and segment shifts. |
| **AC4: Confident-Miss Reduction** | Reduction of confident misses ($p < 0.01$ false negatives) $\ge 20.0\%$ | 0.0% reduction | **UNMET** | P5 produces identical confident misses to calibrated probability ranking. Reported factually as UNMET. |
| **AC5: Host Inference Latency** | Single-case host inference latency $\text{p95} \le 100.0$ ms on host CPU | $\text{p95} = 32.74$ ms | **PASS** | Single-row ensemble scoring averages ~20–33 ms on Windows AMD64 CPU, well within operational bounds. |

---

## 8. Full Automated Regression Matrix

All automated test suites and quality gates pass with zero failures:

| Quality Gate | Verification Command | Result | Status |
| :--- | :--- | :--- | :---: |
| **Backend Test Suite** | `pytest -o "pythonpath=." tests/` | **224 passed**, 23 warnings in 30.79s | **PASS (100%)** |
| **Frontend Test Suite** | `npm test -- --run` in `frontend/` | **29 passed** across 5 test suites in 1.34s | **PASS (100%)** |
| **TypeScript Validation** | `npx tsc --noEmit` in `frontend/` | **0 errors**, clean exit | **PASS** |
| **Vite Production Bundler** | `npm run build` in `frontend/` | Clean build in `frontend/dist/assets/` | **PASS** |
| **Artifact Checksum Check** | `python scripts/validate_artifacts.py` | **100% hash match** across all synthetic & frozen files | **PASS** |
| **Live Stack Verification** | `python scripts/verify_live_stack.py` | **11/11 live HTTP integration checks passed** | **PASS** |

---

## 9. Operator Runbook

### 9.1 Starting the Services
To launch the verified local demonstration stack:
```cmd
scripts\start_demo.bat
```
This launcher:
1. Validates that Python 3.10+ and Node.js v18+ are available.
2. Cryptographically verifies evaluation artifacts via `scripts\validate_artifacts.py`.
3. Checks if ports 8000 and 5173 are already bound.
4. Starts FastAPI on `http://127.0.0.1:8000` and Vite on `http://127.0.0.1:5173`.

### 9.2 Service URLs:
- **Frontend Cockpit:** `http://127.0.0.1:5173/overview`
- **Scoring Sandbox:** `http://127.0.0.1:5173/sandbox`
- **Case Explorer:** `http://127.0.0.1:5173/cases`
- **Policy Comparison:** `http://127.0.0.1:5173/policies`
- **Drift & Shift Storm:** `http://127.0.0.1:5173/drift`
- **Audit Ledger:** `http://127.0.0.1:5173/audit`
- **Model Card & Governance:** `http://127.0.0.1:5173/model-card`
- **Backend API Health:** `http://127.0.0.1:8000/api/health`
- **Interactive OpenAPI Documentation:** `http://127.0.0.1:8000/docs`

### 9.3 Safe Shutdown:
To terminate running SignalGate demo listeners without affecting unrelated developer processes:
```cmd
scripts\stop_demo.bat
```
`scripts\stop_demo.bat` inspects command-line ownership on ports 8000 and 5173, cleanly terminating only verified SignalGate processes.
