# SignalGate — Final Local Acceptance & Regression Report

**Execution Timestamp**: 2026-10-18T14:42:00Z  
**Host Environment**: Windows 11 Home (Build 26100), 8 GB Physical RAM (AMD Ryzen 5 5500U, Python 3.13.7, Node.js v20.18.0)  
**Governing Specification**: `docs/ibm_architecture_integration_master_spec.md`  
**Execution Mode**: `SYNTHETIC_SMOKE_ONLY` (Full IEEE-CIS real-data training deferred due to host 8 GB RAM limitation)  

---

## Executive Summary & Gate Verdicts

| Gate | Description | Status | Evidence / Notes |
|---|---|---|---|
| **Gate 1** | Manual Browser Acceptance | **PASS** | Manual verification completed by developer in local browser at 1366 × 768. Confirmed mode switcher layout/badges, synthetic scoring workflow, latency/SLA consistency, unavailable mode disclosures (HTTP 409), dashboard pages, and core runtime behavior. |
| **Gate 2** | Full Regression Suite | **PASS** | 16/16 artifact checks passed, 195/195 backend tests passed (0 failures), 29/29 frontend tests passed (0 failures), Vite production build passed (exit 0). |
| **Gate 3** | Runtime & Safety Confirmation | **PASS** | Live FastAPI scoring functional (~22–38 ms), synthetic provenance explicit, real-data benchmark deferred, modes fail closed (HTTP 409), target leakage rejected (HTTP 422), HMAC audit chain verified. |
| **Gate 4** | Working-Tree & Local Freeze | **PASS** | Working tree inspected (`git diff --stat`, `git status`), no git mutations performed (`git add/commit/push` strictly avoided), clean code freeze maintained. |

**Overall Project Status**: **FROZEN AND READY FOR LOCAL SUBMISSION REVIEW**  
All code modifications, test suites, build pipelines, runtime security/telemetry checks, and manual browser verification across all dashboard pages (`/overview`, `/sandbox`, `/drift-shift`, `/policy-comparison`, `/audit-trail`) have passed.

---

## Gate 1: Browser Acceptance & Verification Report

- **Status**: **PASS** (Manual Developer Browser Acceptance Verified)
- **Automated Browser Automation Note**: Headless browser automation encountered a local Playwright CDP protocol issue (`Browser.setDownloadBehavior: Browser context management is not supported`), superseded by complete developer verification in the desktop browser at `http://127.0.0.1:5173`.
- **Manual Verification Scope & Verified Items**:
  1. `/overview`: Signal Core 3D visualizer, status indicators, outcome distributions, and summary metrics verified.
  2. `/sandbox`:
     - **Mode Switcher Dropdown**: Verified at 1366 × 768 desktop view. The panel renders with the responsive 380px layout (`.mode-switcher-panel`), all three mode titles (`SYNTHETIC_SMOKE_ONLY`, `IEEE_CIS_OFFLINE_BENCHMARK`, `LIVE_SOURCE_NOT_CONNECTED`) and readiness badges (`[ACTIVE]`, `[CHECKPOINTS MISSING]`, `[DISCONNECTED]`) are visible without horizontal clipping, and explanatory text wraps cleanly.
     - **Unavailable Modes**: Verified that clicking `IEEE_CIS_OFFLINE_BENCHMARK` or `LIVE_SOURCE_NOT_CONNECTED` does not activate them and displays their missing prerequisite disclosures (failing closed with HTTP 409).
     - **Scoring & Latency Badge**: Submitted sandbox evaluation; verified live model + routing execution. Measured latency displayed correctly with dynamic SLA status badge (`PASS • <250ms SLA`).
  3. `/drift-shift`: PSI/KS drift indicators and sentinel proposals verified.
  4. `/policy-comparison`: Baseline B2 vs Candidate P5 frontier curve and 3D policy comparisons verified.
  5. `/audit-trail`: Cryptographic HMAC-SHA256 audit ledger, claim ledger records, and verification status verified.
- **Verdict**: Gate 1 is marked as **PASS**.

---

## Gate 2: Full Regression Suite

All regression commands were executed sequentially from project root and `frontend/` on the 8 GB RAM host:

### 1. Artifact Validation (`python scripts/validate_artifacts.py`)
- **Status**: **PASS** (16/16 checks passed, Exit Code 0)
- Verified dataset fixture SHA-256 (`da00179ebf37970e...`)
- Verified split hash (`07b55a4ed74f238c...`)
- Verified frozen policy thresholds ($t_{\text{alert}} = 0.084705, t_{\text{review}} = 0.071002, u_{\text{th}} = 0.526773$)
- Verified result status: `SYNTHETIC_SMOKE_ONLY`
- Verified test row provenance (2,000 rows, 111 fraud cases)
- Verified paired bootstrap confidence interval: $[-2.75\text{ pp}, +2.75\text{ pp}]$, conclusive=False
- Verified outcome distribution: Alert=11, Review=119, Routine=896, Deferred=974 (Total=2,000)
- Verified budget sweep multipliers: `['1.0x', '1.5x', '2.0x', '3.0x']`
- Verified model artifacts: `hgb_base.joblib`, `calibrator_sigmoid.joblib`, `ensemble_members.joblib`, `residualizer_u2.joblib` and their metadata JSONs
- Verified feature manifest (67 features) and HMAC-SHA256 audit records

### 2. Complete Backend Test Suite (`python -m pytest tests/ -q`)
- **Status**: **PASS** (195 passed in 25.42s, 0 failures, Exit Code 0)
- Comprehensive test coverage across all integration domains:
  - `tests/test_api_scoring.py`: 3 passed
  - `tests/test_ibm_scoring.py`: 9 passed
  - `tests/test_api_integration_modes.py`: 8 passed
  - `tests/test_ibm_agents_audit.py`: passed
  - `tests/test_ibm_boundaries.py`: passed
  - `tests/test_ibm_drift_replay.py`: passed
  - `tests/test_ibm_models.py`: passed
  - `tests/test_calibration.py`, `test_ensemble.py`, `test_features.py`: passed
  - `tests/test_router.py`, `test_shift_drift.py`, `test_splits.py`: passed

### 3. Frontend Unit Tests (`npm test -- --run`)
- **Status**: **PASS** (29 passed across 5 test suites in 4.08s, 0 failures, Exit Code 0)
  - `src/lib/__tests__/latency.test.ts`: 8 tests passed (threshold constant export, undefined/null handling, invalid numbers, fast latency $\le 250$ms, exact 250.0ms boundary, strict 250.01ms exceeded boundary, cold-start 2120.6ms rejection of PASS, and custom thresholds)
  - `src/components/__tests__/phase10_quality.test.ts`: 6 tests passed
  - `src/components/__tests__/pipeline_glb_integration.test.ts`: 6 tests passed
  - `src/components/__tests__/sandbox_instrument_glb_integration.test.ts`: 6 tests passed
  - `src/components/__tests__/status_and_metrics.test.ts`: 3 tests passed

### 4. Production Build (`npm run build`)
- **Status**: **PASS** (Built in 23.73s, Exit Code 0)
- TypeScript compilation (`tsc`) passed with 0 diagnostic errors.
- Vite bundled all 2,441 modules into `frontend/dist/`.

---

## Gate 3: Runtime and Safety Confirmation

Verified against running demo instances at `http://127.0.0.1:8000` (FastAPI) and `http://127.0.0.1:5173` (Vite):

1. **Synthetic Scoring Response**:
   - `POST /api/score-sandbox` returned HTTP 200.
   - Evaluated signals: $p = 0.0556$, $u = -0.1750$, decision action `ROUTINE` with reason `R5_LOW_RISK_RELIABLE`.
   - Measured live model + routing latency: **27.75 ms** (well below the 250 ms threshold).
2. **Synthetic Provenance Disclosure**:
   - `provenance.dataset_status`: `SYNTHETIC_SMOKE_ONLY`
   - `provenance.source_mode`: `SYNTHETIC_SMOKE_ONLY`
   - `provenance.real_data_benchmark_status`: `DEFERRED`
   - `provenance.model_backend`: `scikit-learn HistGradientBoosting + Sigmoid Calibration`
3. **Real-Data Benchmark Status**:
   - `GET /api/modes` explicitly reports `IEEE_CIS_OFFLINE_BENCHMARK` as `available: false`, status `UNAVAILABLE_MISSING_CHECKPOINTS`, `real_data_training_status: DEFERRED` ("Full IEEE-CIS 590,540-row training is deferred due to host 8 GB RAM limitation. Minimum recommended hardware is 16 GB RAM.").
4. **Mode Switch Fail-Closed Safety**:
   - `POST /api/modes/select` with `{"mode": "IEEE_CIS_OFFLINE_BENCHMARK"}` returned **HTTP 409 Conflict** (`MODE_UNAVAILABLE`).
   - `POST /api/modes/select` with `{"mode": "LIVE_SOURCE_NOT_CONNECTED"}` returned **HTTP 409 Conflict** (`MODE_UNAVAILABLE`).
   - Unavailable modes cannot silently become active or bypass hardware safety checks.
5. **Target Leakage Rejection**:
   - `POST /api/score-sandbox` with payload containing `"isFraud": 1` returned **HTTP 422 Unprocessable Entity** (`LEAKAGE VIOLATION: Forbidden field 'isFraud' is strictly rejected from scoring inputs.`).
6. **Cryptographic HMAC Audit Chain**:
   - `GET /api/governance/audit-chain/verify` returned `verified: true`, `tamper_detected: false`.
7. **Frontend Production Serving**:
   - `GET http://127.0.0.1:5173/sandbox` serves valid HTML shell with React root mounting point.

---

## Gate 4: Working-Tree Status and Local Freeze

- **Status**: **PASS**
- **Git Restrictions Respected**:
  - No commits were created (`git commit` was not run).
  - No changes were staged (`git add` was not run).
  - No branches were pushed or published to GitHub (`git push` was not run).
  - No uncommitted files were discarded (`git reset --hard` or `git clean` were not run).
- **Working Tree Inspection**:
  - `git diff --stat`: 17 tracked files modified (+831 insertions, -388 deletions), consisting of Phase 4–10 synthetic integrations, mode switcher responsive layout styling, and latency SLA dynamic badge logic.
  - `git status --short --untracked-files=all`: Reflects uncommitted milestone documentation and integration modules.
- **Code Freeze**: No further code modifications will be made.

---

## Disclosures & Boundary Limitations

1. **Hardware Limitation**: Full IEEE-CIS 590,540-row training is deferred due to host 8 GB RAM physical memory limits. The system operates strictly in `SYNTHETIC_SMOKE_ONLY` mode.
2. **No Hardware Attestation**: No IBM Secure Execution, TEE, or cryptographic hardware enclave is claimed. Audit logs use software-based HMAC-SHA256 chain verification.
3. **No Live Settlement**: Payment gateway connection is explicitly disconnected (`LIVE_SOURCE_NOT_CONNECTED`).
4. **Visual Inspection**: Automated headless CDP capture was superseded by successful manual developer browser verification across all key views, completing Gate 1.
