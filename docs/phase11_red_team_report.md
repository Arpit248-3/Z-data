# SignalGate — Phase 11 Independent Red-Team Audit, Scientific Integrity & Release Readiness Report

**Date:** 2026-10-18  
**Phase:** Phase 11 — Independent Red-Team Audit, Scientific Integrity & Release Assurance  
**Auditor Roles:** Independent Red-Team Auditor, ML Evaluation Reviewer, Application-Security Engineer, Release Assurance Lead  
**Specification References:** `DESIGN.md` (v2.1.0-FINAL-CORRECTED), `config.yaml`, `policy/frozen_policy.json`, `results/results.json`, `results/policy_report.json`, `results/split_report.json`, `docs/runbook.md`, `README.md`  
**Execution Environment:** Windows 10/11 x64, Python 3.13.7, Node.js v20+, Vite 5.4.21  
**Audit Recommendation:** **`READY_WITH_DOCUMENTED_LIMITATIONS`**

---

## 1. Executive Summary

An independent, end-to-end red-team security, scientific integrity, and release-assurance audit was conducted on the SignalGate platform. Rather than accepting previous phase self-reports at face value, every artifact, model checkpoint, routing policy rule, backend endpoint, and frontend component was verified directly against the running code, canonical evaluation data, and frozen policy specifications.

### Summary of Audit Outcomes:
1. **Zero Critical or High Vulnerabilities:** No data leakage, unhandled fall-through routing, arbitrary code execution, unauthorized process termination, or unauthenticated writes were identified.
2. **Scientific Integrity Confirmed:** The canonical test partition (2,000 cases, 111 fraud cases) strictly adheres to the frozen 60/10/10/20 chronological split. Zero future target labels enter live model feature matrices.
3. **Cross-Report Ambiguities Resolved:**
   - **Model Architecture:** The actual fitted pipeline is 100% `scikit-learn` `HistGradientBoostingClassifier` (Primary Estimator) + Platt Sigmoid Calibrator (`LogisticRegression`) + 3-member `HistGradientBoostingClassifier` variance ensemble. An isolated mention of "LightGBM" in `docs/post_light_theme_verification_report.md` was identified as a documentation defect.
   - **Replay Dataset Denominator:** `results/replay_rows.jsonl` contains 5,200 chronological records representing 3 distinct stress scenarios ($S_0$: 2,000 reference, $S_1$: 1,200 prevalence surge, $S_3$: 2,000 covariate shift). The canonical benchmark evaluation look remains strictly evaluated on the 2,000 held-out test rows of $S_0$.
4. **Targeted Red-Team Fixes Applied & Verified:**
   - Corrected an enum mismatch in `CaseExplorerPage.tsx`, `ShiftStormPage.tsx`, and `ModelCardPage.tsx` where `R3_DISAGREEMENT` failed to match canonical backend `ReasonCode.R3_MODEL_DISAGREEMENT`.
   - Added backwards-compatible alias normalization in `backend/app/services/cases.py` and `backend/app/services/audit.py`.
   - Added an automated regression test in `tests/test_api.py` validating that both canonical and alias reason filters return the exact 15 disagreement cases.

---

## 2. Scope & Actual Files Inspected

The audit inspected all canonical evidence artifacts, source modules, and configurations:

### 2.1 Governance & Evaluation Artifacts
- `config.yaml` (SHA-256 verified)
- `data/synthetic_smoke_fixture.csv` (SHA-256 `da00179ebf37970ec8907d11cfb366d170ddd5b2b41370e881bf92359b7d17de`)
- `policy/frozen_policy.json` (Frozen thresholds: $t_{\text{alert}} = 0.084705, t_{\text{review}} = 0.071002, u_{\text{th}} = 0.526773, B = 130$)
- `results/results.json` (Canonical G5 final evaluation look: 2,000 test cases, 111 frauds)
- `results/split_report.json` (Chronological 60/10/10/20 split hash: `07b55a4ed74f238c9ef5b779a749770cf274d4709a4389d9eab860dd9068fbdd`)
- `results/policy_report.json` & `results/model_report.json`
- `results/cases.jsonl` (2,000 records) & `results/replay_rows.jsonl` (5,200 records)
- `logs/audit.jsonl` (Cryptographic append-only operational ledger, 185 records)

### 2.2 Model Checkpoints (`models/artifacts/`)
- `hgb_base.joblib` (131,888 bytes) & `hgb_base.meta.json` (3,330 bytes)
- `calibrator_sigmoid.joblib` (132,538 bytes) & `calibrator_sigmoid.meta.json` (3,350 bytes)
- `ensemble_members.joblib` (385,066 bytes) & `ensemble_members.meta.json` (1,699 bytes)
- `residualizer_u2.joblib` (16,347 bytes) & `residualizer_u2.meta.json` (1,069 bytes)

### 2.3 Backend API & Services (`backend/app/`)
- `main.py` (CORS middleware, error handling, route mounting)
- `schemas.py` (Recursive leakage rejection, input sanitization, Pydantic validation)
- `routers/` (`scoring.py`, `cases.py`, `replay.py`, `audit.py`, `policies.py`, `overview.py`, `health.py`)
- `services/` (`scoring.py`, `cases.py`, `replay.py`, `audit.py`, `artifacts.py`)

### 2.4 Policy & Router Core (`policy/`)
- `router.py` (Action & ReasonCode enums, fail-closed logic, deterministic routing)
- `governor.py` (Queue capacity enforcer, saturated deferrals)
- `audit.py` (SHA-256 hash chaining and audit record serialization)

### 2.5 Frontend Applications (`frontend/src/`)
- Routing & Navigation: `app/router.tsx`, `app/AppShell.tsx`
- Routed Views:
  - `features/overview/OverviewPage.tsx`
  - `features/shift-storm/ShiftStormPage.tsx`
  - `features/case-explorer/CaseExplorerPage.tsx`
  - `features/policy-comparison/PolicyComparisonPage.tsx`
  - `features/drift-shift/DriftShiftPage.tsx`
  - `features/audit-trail/AuditTrailPage.tsx`
  - `features/model-card/ModelCardPage.tsx`
  - `features/sandbox/SandboxPage.tsx`
- Styles & Tokens: `styles/tokens.css`, `styles/components.css`, `styles/layout.css`

### 2.6 Automation & Operational Scripts (`scripts/`)
- `scripts/validate_artifacts.py` (Deterministic cryptographic integrity validator)
- `scripts/start_demo.bat` & `scripts/stop_demo.bat` (Verified process-ownership Windows shutdown)
- `scripts/generate_replay_artifacts.py`

---

## 3. Findings Classification Matrix

| Finding ID | Severity | Category | Target Component | Status |
| :--- | :---: | :---: | :--- | :---: |
| **FIND-UI-ROUTER-01** | **MEDIUM** | Functional Bug | `CaseExplorerPage.tsx` / `ShiftStormPage.tsx` | **RESOLVED** |
| **FIND-DOC-ARCH-01** | **INFORMATIONAL** | Documentation | `post_light_theme_verification_report.md` | **DOCUMENTED** |
| **FIND-API-ALIAS-01** | **LOW** | Defensive API | `backend/app/services/cases.py` / `audit.py` | **RESOLVED** |
| **FIND-TEST-COV-01** | **LOW** | Regression Test | `tests/test_api.py` | **RESOLVED** |
| **FIND-TOOL-BROWSER-01**| **INFORMATIONAL**| Testing Limit | Playwright browser subagent target closed | **DOCUMENTED** |

---

## 4. Reproducible Defect Details & Corrections

### Finding FIND-UI-ROUTER-01: Disagreement Reason Code Enum Mismatch
- **Severity:** MEDIUM
- **Affected Files:**
  - `frontend/src/features/case-explorer/CaseExplorerPage.tsx` (Line 226)
  - `frontend/src/features/shift-storm/ShiftStormPage.tsx` (Line 32)
  - `frontend/src/features/model-card/ModelCardPage.tsx` (Lines 82, 152)
- **Inspection & Reproduction Method:**
  Executed query filtering for disagreement cases in `results/cases.jsonl`:
  ```python
  r3_exact = [c for c in cases if c.get('decision', {}).get('reason_code') == 'R3_MODEL_DISAGREEMENT'] # 15
  r3_wrong = [c for c in cases if c.get('decision', {}).get('reason_code') == 'R3_DISAGREEMENT']       # 0
  ```
- **Expected Behavior:**
  Filtering by disagreement reason code in the Case Explorer UI must return all 15 disagreement cases evaluated in $S_0$.
- **Actual Verified Behavior Prior to Fix:**
  Selecting `R3_DISAGREEMENT` in the dropdown sent `reason_code=R3_DISAGREEMENT` to `/api/cases`. Because all 15 cases are logged with `R3_MODEL_DISAGREEMENT`, the endpoint returned 0 cases. Additionally, in `ShiftStormPage.tsx`, `getReasonDescription()` failed to match `R3_MODEL_DISAGREEMENT`, falling through to the generic default description.
- **Recommended Correction:**
  1. Update `CaseExplorerPage.tsx` dropdown to `<option value="R3_MODEL_DISAGREEMENT">R3_MODEL_DISAGREEMENT</option>`.
  2. Update `ShiftStormPage.tsx` switch statement to handle canonical `R1_HIGH_RISK`, `R2_INTERMEDIATE_RISK`, and `R3_MODEL_DISAGREEMENT`.
  3. Align `ModelCardPage.tsx` FROZEN_RULES table to `R3_MODEL_DISAGREEMENT`.
  4. Update `CaseService` and `AuditService` to accept `R3_DISAGREEMENT` as a transparent alias for `R3_MODEL_DISAGREEMENT`.
- **Post-Fix Verification Result:**
  Verified via new automated test `test_api_cases_filter_reason_code_canonical_and_alias()` in `tests/test_api.py`. Both queries return the exact 15 cases. (Exit Code 0).

---

## 5. Scientific Integrity & Data Leakage Review

### 5.1 Dataset Provenance & Partition Isolation
- **Dataset Identification:** `data/synthetic_smoke_fixture.csv` (10,000 rows, SHA-256: `da00179ebf37970ec8907d11cfb366d170ddd5b2b41370e881bf92359b7d17de`).
- **Labeling Standard:** Labeled consistently as `SYNTHETIC_SMOKE_ONLY` throughout metadata and UI cards.
- **Partition Ratios:**
  - Training: 6,000 rows (60.0%)
  - Calibration: 1,000 rows (10.0%)
  - Validation: 1,000 rows (10.0%)
  - Test (Held-Out): 2,000 rows (20.0%)
  - Split Hash: `07b55a4ed74f238c9ef5b779a749770cf274d4709a4389d9eab860dd9068fbdd` (Deterministic temporal index partition).
- **Leakage Prevention Verification:**
  - Raw `TransactionID` and `TransactionDT` are explicitly stripped from feature extraction in `data/features.py`.
  - Live scoring rejects any request containing `isFraud`, `target`, `label`, `TransactionID`, or `TransactionDT` (case-insensitive, normalized).
  - Model pipeline training strictly executed on training split; threshold calibration executed on calibration and validation splits; test split remained strictly held out until frozen evaluation.

### 5.2 Cross-Report Investigation Findings
1. **Model Architecture Discrepancy:**
   - **Reported:** `docs/post_light_theme_verification_report.md` line 100 stated: "Architecture breakdown of LightGBM + HistGradientBoosting ensemble + Sigmoid Calibrator."
   - **Audited Reality:** Inspecting `models/base.py`, `models/ensemble.py`, and `models/artifacts/hgb_base.meta.json` reveals that LightGBM is not present. The architecture is pure `scikit-learn` `HistGradientBoostingClassifier` with a 3-member `HistGradientBoostingClassifier` variance ensemble.
   - **Conclusion:** Documentation error in `post_light_theme_verification_report.md`. The actual models and artifacts are correct and internally consistent.
2. **Replay Rows vs. Held-Out Evaluation Cases:**
   - **Reported:** 2,000 evaluation cases vs 5,200 replay records.
   - **Audited Reality:** `results/cases.jsonl` contains exactly 2,000 records for the held-out test look ($S_0$). `results/replay_rows.jsonl` contains 5,200 records: $S_0$ (2,000 rows) + $S_1$ (1,200 rows) + $S_3$ (2,000 rows).
   - **Conclusion:** Completely legitimate and accurate. The replay stage requires multi-scenario stress data, while the benchmark evaluation is strictly $S_0$.

---

## 6. Frozen Policy & Router Safety Checks

The deterministic triage router in `policy/router.py` was evaluated against all safety boundaries:

| Safety Invariant | Test Method | Expected Result | Actual Result | Verification |
| :--- | :--- | :--- | :--- | :---: |
| **Fail-Closed on Null/NaN Risk** | `route(p=None, u=0.1)` | `MANUAL_REVIEW`, `R0_SIGNAL_UNAVAILABLE` | `MANUAL_REVIEW`, `R0_SIGNAL_UNAVAILABLE` | **PASS** |
| **Fail-Closed on Invalid Config** | `route(p=0.05, cfg={})` | `MANUAL_REVIEW`, `R0_SIGNAL_UNAVAILABLE` | `MANUAL_REVIEW`, `R0_SIGNAL_UNAVAILABLE` | **PASS** |
| **High Risk Never Bypasses to Routine** | `route(p=0.084705, u=0.0)` | `FRAUD_ALERT`, `R1_HIGH_RISK` | `FRAUD_ALERT`, `R1_HIGH_RISK` | **PASS** |
| **High Disagreement Diverts to Review** | `route(p=0.05, u=0.55)` | `MANUAL_REVIEW`, `R3_MODEL_DISAGREEMENT` | `MANUAL_REVIEW`, `R3_MODEL_DISAGREEMENT` | **PASS** |
| **Routine Only for Low Risk & Low Disagree**| `route(p=0.05, u=0.1)` | `ROUTINE`, `R5_LOW_RISK_RELIABLE` | `ROUTINE`, `R5_LOW_RISK_RELIABLE` | **PASS** |
| **Capacity Saturated Deferral** | 6 escalations, $B=3$ | 1 Alert, 2 Reviews, 3 Deferred | 1 Alert, 2 Reviews, 3 Deferred | **PASS** |

### Evaluated Benchmark Outcome Integrity
In `results/results.json`, SignalGate frozen policy outcome distribution on $N=2,000$:
- `alert_count`: 11 (0.55%)
- `review_count`: 119 (5.95%)
- `routine_count`: 896 (44.80%)
- `deferred_count`: 974 (48.70%)
- `touched_count`: 130 (6.50% — strictly matches analyst budget cap $B=130$)
- `recall_at_touched`: 9.009% (10 caught / 111 fraud)
- `paired_bootstrap_ci`: `[-2.75 pp, +2.75 pp]`, `is_conclusive: false`
- **Claim Integrity:** The platform explicitly displays: *"Inconclusive: 95% confidence interval spans zero. Do not claim superiority."* Zero false superiority claims were detected.

---

## 7. API & Security Audit

### 7.1 Input Sanitization & Leakage Protection
- **Recursive Leakage Validation:** The Pydantic model `SandboxScoreRequest` enforces `_check_forbidden_recursively()`, which recursively inspects nested dictionaries, lists, and tuples. Forbidden keys (e.g., `isFraud`, `true_label`, `TransactionID`, `TransactionDT`) are rejected with HTTP 400.
- **Non-Finite Value Defense:** Rejects NaN, Inf, and string representations like `"inf"` or `"-inf"` before payload features reach the estimator.

### 7.2 API Security Architecture
- **CORS Configuration:** `backend/app/main.py` restricts origins to `settings.cors_origins` (`http://localhost:5173`, `http://127.0.0.1:5173`).
- **Bounded Pagination:** All query parameters specify strict `le` and `ge` limits:
  - `/api/cases`: `limit` bounded to $\le 200$.
  - `/api/replay/rows`: `limit` bounded to $\le 500$.
  - `/api/audit`: `limit` bounded to $\le 200$.
- **Path Traversal Protection:** Audit export format validated via regex `pattern="^(jsonl|csv)$"`. File paths are never dynamically constructed from user input.
- **Process Shutdown Script Safety:** `scripts/stop_demo.bat` uses WMI command-line inspection via PowerShell. It strictly verifies that listening processes on ports 8000/5173 contain `backend.app.main` or `vite`/`project` before terminating. Unrelated Python or Node processes are left untouched.

---

## 8. Audit Trail & Cryptographic Artifact Integrity

Execution of `python scripts/validate_artifacts.py` verified 19/19 cryptographic checks:
1. Dataset fixture SHA-256: `da00179ebf37970ec8907d11cfb366d170ddd5b2b41370e881bf92359b7d17de` (**MATCH**)
2. Split metadata hash: `07b55a4ed74f238c9ef5b779a749770cf274d4709a4389d9eab860dd9068fbdd` (**MATCH**)
3. Frozen policy thresholds: $t_{\text{alert}}=0.084705, t_{\text{review}}=0.071002, u_{\text{th}}=0.526773$ (**MATCH**)
4. Result provenance: 2,000 test cases, 111 fraud cases (**MATCH**)
5. Paired bootstrap CI: $[-2.75\text{ pp}, +2.75\text{ pp}]$, `conclusive=False` (**MATCH**)
6. Outcome distribution: 11 Alert, 119 Review, 896 Routine, 974 Deferred (**MATCH**)
7. Budget sweep multiples: `['1.0x', '1.5x', '2.0x', '3.0x']` (**MATCH**)
8. Model pipeline weights: `hgb_base.joblib`, `calibrator_sigmoid.joblib`, `ensemble_members.joblib`, `residualizer_u2.joblib` present and non-empty (**MATCH**)
9. Feature manifest: 67 features, SHA-256 `eb9b39dca71480208ea28d8137cd08867877426ad9d8271d039c867c5a391b52` (**MATCH**)
10. Audit trail log: 185 tamper-evident JSONL records with SHA-256 policy and split references (**MATCH**)

---

## 9. Accessibility & Browser Verification Status

### 9.1 Accessibility Verification
- **Skip Link:** Working `.skip-to-content` link bypassing header to `<main id="main-content">`.
- **Keyboard Navigation:** Escape key closes modal drawers in `CaseExplorerPage`, `MetricCard`, and `ModelCardPage`. Focus rings remain visible with `2px solid var(--accent-primary)`.
- **Reduced Motion:** Verified CSS media query `prefers-reduced-motion` suppresses animations. 3D scenes gracefully swap to static rendering or fallback SVG instruments.
- **Contrast Ratios:** Contrast ratios meet WCAG AA/AAA standards across both dark (`13.5:1` primary) and light (`16.0:1` primary) themes.
- **JSON Payload Editor:** Verified dark-on-light high-contrast code styling (`#0F172A` on `#FFFFFF`, 16:1 contrast ratio) in Light Mode, eliminating invisible text issues.

### 9.2 Tooling Disclosure on Browser Testing
- **Status:** **UNVERIFIED AUTOMATED VISUAL SNAPSHOT / VERIFIED VIA UNIT TESTS & RUNTIME BUILD**
- **Exact Limitation:** Headless browser automation in this environment encountered Playwright target closure (`playwright: target closed`) during automated video recording.
- **Mitigation:** Verified all DOM components, CSS selectors, theme variables, and HTTP endpoints via Vite production bundle builds, TypeScript compilation, Vitest component test suites, and FastAPI test clients.

---

## 10. Automated Test Results & Verification Commands

All test suites were executed independently during the audit:

```bash
# 1. Deterministic Artifact Cryptographic Validator
python scripts/validate_artifacts.py
# Result: 19/19 checks passed
# Exit Code: 0

# 2. Full Backend Pytest Suite
python -m pytest tests/
# Result: 109 passed in 15.91s (including new reason-code alias regression test)
# Exit Code: 0

# 3. Frontend TypeScript Compilation
cd frontend && npx tsc --noEmit
# Result: 0 errors
# Exit Code: 0

# 4. Frontend Vitest Component Suite
cd frontend && npm test -- --run
# Result: 2 test files passed, 9 tests passed in 1.02s
# Exit Code: 0

# 5. Frontend Production Bundle Build
cd frontend && npm run build
# Result: Built in 19.93s, zero errors
# Exit Code: 0
```

---

## 11. Remaining Risks & Limitations

1. **Synthetic Development Evidence:** All evaluation data derives from `synthetic_smoke_fixture.csv`. While structurally identical to financial transaction schemas (67 features), it does not represent live production payment flows.
2. **Offline Replay vs. Streaming Network Latency:** Replay telemetry is replayed from static test records; real-world payment network jitter and network transport overhead are not modeled.
3. **Headless Browser Visual Automation:** Automated browser video capture requires a dedicated GUI display context on Windows; manual inspection remains recommended for visual layout reviews.

---

## 12. Final Release-Readiness Recommendation

### **`READY_WITH_DOCUMENTED_LIMITATIONS`**

**Justification:**
- Zero unresolved Critical or High security or integrity defects exist.
- All 19 cryptographic artifact checks and 109 backend unit tests pass.
- All 9 frontend component tests and TypeScript strict type-checks pass.
- Frozen policy thresholds, dataset hashes, and model weights are 100% intact.
- The identified UI reason-code mismatch has been repaired and verified with regression tests.
- Platform evidence status is transparently disclosed as `SYNTHETIC_SMOKE_ONLY` with documented inconclusive superiority confidence intervals.
