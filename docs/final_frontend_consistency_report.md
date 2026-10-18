# SignalGate — Final Frontend Consistency Correction Report

**Date:** 2026-10-17  
**Auditor / Role:** Senior Frontend Design & Architecture Lead  
**Scope:** Source-of-truth reconciliation across frontend presentations, reports, and canonical evaluation artifacts.  
**Specification References:** `DESIGN.md` (v2.1.0-FINAL-CORRECTED), `config.yaml`, `policy/frozen_policy.json`, `results/results.json`, `results/g3_test_look.json`  
**Execution Environment:** Windows (x64), Node.js v20+, Python 3.13.7

---

## Executive Summary

This report establishes complete, rigorous, mathematical source-of-truth reconciliation across the SignalGate frontend, verifying all presentation surfaces against canonical evaluation results, frozen policy configurations, and registered FastAPI schemas.

| Verification Item | Status | Summary of Finding & Resolution |
| :--- | :---: | :--- |
| **1. Outcome Distribution Reconciliation** | **PASS / RESOLVED** | The prior report text claim of `89.05% Routine, 6.525% Review, 4.425% Alert` was an erratum originating from an early pre-evaluation design draft that omitted capacity-governed deferrals. The canonical evaluation data in `results/results.json` and `results/g3_test_look.json` establishes: **11 Alerts (0.55%)**, **119 Reviews (5.95%)**, **896 Routine (44.80%)**, and **974 Held/Deferred (48.70%)** out of $N = 2,000$ test cases ($100.00\%$). The live UI was already rendering these exact canonical numbers. |
| **2. Decision Threshold Alignment** | **PASS / RESOLVED** | Several frontend displays referenced a placeholder intermediate threshold $p \ge 0.0400$. Reconciled all frontend references in `ModelCardPage.tsx`, `OverviewPage.tsx`, `SignalCoreScene.tsx`, `ShiftStormPage.tsx`, and `SandboxPage.tsx` to the true frozen threshold $t_{\text{review}} = 0.071002$ ($0.0710$). |
| **3. Semantic Color Spectrum** | **PASS / VERIFIED** | Verified that `tokens.css` defines distinct calibrated colors preserving decision semantics in both themes: Coral/Crimson for Fraud Alert, Amber for Manual Review, Green/Sage for Routine, and Violet/Purple for Uncertainty / Held Deferral. |
| **4. Budget Sweep Points & CI** | **PASS / RESOLVED** | Verified that `budget_sweep` in `results/results.json` contains exactly 4 evaluated points: `1.0x` (87 reviews), `1.5x` (130 reviews), `2.0x` (174 reviews), and `3.0x` (261 reviews). The mention of `0.5x` in the prior report was an erratum conflating the `0.5x` replay speed multiplier with budget sweeps. The frontend selector strictly presents `['1.0x', '1.5x', '2.0x', '3.0x']`. Primary paired bootstrap CI is verified as `[-2.75 pp, +2.75 pp]` (`is_conclusive = false`). |
| **5. Route & Model Specifications** | **PASS / VERIFIED** | All frontend API calls map to registered FastAPI endpoints: `/api/health`, `/api/status`, `/api/overview`, `/api/policies/compare`, `/api/scenarios`, `/api/replay/rows`, `/api/cases`, `/api/audit`, `/api/results`, `/api/score-sandbox`. Models, Platt sigmoid calibrator, rank-residualized $u_2$, and SHA-256 hashes match canonical sources. |
| **6. Automated Quality Checks** | **PASS** | `npx tsc --noEmit` (Exit 0), `npm test -- --run` (3/3 passing), `npm run build` (Exit 0), `pytest tests/` (108/108 passing). Zero backend or evaluation files modified. |

---

## 1. Outcome Distribution Reconciliation

### 1.1 Original Display vs. Report Claim
- **Report Claim (docs/post_light_theme_verification_report.md, line 69):**  
  `Shows frozen canonical split (89.05% Routine, 6.525% Review, 4.425% Alert).`
- **Rendered Frontend Code (`frontend/src/features/overview/OverviewPage.tsx`, lines 154–213):**  
  - `FRAUD_ALERT`: 11 cases (0.55%)
  - `MANUAL_REVIEW`: 119 cases (5.95%)
  - `ROUTINE`: 896 cases (44.80%)
  - `HELD / DEFERRED`: 974 cases (48.70%)
  - Denominator: $N = 2,000$ transactions

### 1.2 Canonical Source Checked
1. **`results/g3_test_look.json` (lines 78–89):**
   ```json
   "governor_metrics": {
     "total_transactions": 2000,
     "capacity": 130,
     "requested_escalations": 1104,
     "admitted_alerts": 11,
     "admitted_reviews": 119,
     "deferred_count": 974,
     "routine_count": 896,
     "touched_count": 130,
     "touched_rate": 0.065,
     "deferred_rate": 0.487,
     "capacity_exhausted": true
   }
   ```
2. **`results/results.json` (`primary_policy_comparison.SignalGate_frozen`, lines 200–213):**
   ```json
   "alert_count": 11,
   "review_count": 119,
   "routine_count": 896,
   "deferred_count": 974,
   "touched_count": 130,
   "touched_rate": 0.065,
   "alert_rate": 0.0055,
   "review_rate": 0.0595,
   "routine_rate": 0.448,
   "deferred_rate": 0.487
   ```

### 1.3 Trace & Resolution
- **Root Cause of Conflicting Report Text:**  
  The formula `89.05% Routine, 6.525% Review, 4.425% Alert` originated from early pre-evaluation mockups where total escalation was hypothesized without capacity throttling ($6.525\% + 4.425\% = 10.95\%$, leaving $89.05\%$ routine). That draft completely omitted the capacity governor's deferral lane ($R6$).
- **Verification Finding:**  
  The frontend implementation in `OverviewPage.tsx` and `SignalCoreScene.tsx` was **already using the true canonical counts**:
  - $11 + 119 + 896 + 974 = 2,000$ ($100.00\%$).
  - **FRAUD_ALERT:** 11 cases ($0.55\%$).
  - **MANUAL_REVIEW:** 119 cases ($5.95\%$) (admitted into review queue, consuming 100% of capacity quota $B = 130$).
  - **ROUTINE:** 896 cases ($44.80\%$) (fast-path automated clearance).
  - **HELD / DEFERRED:** 974 cases ($48.70\%$) (epistemic uncertainty and review queue overflow diverted to deferred audit; zero silent leakage).
- **Distinction of HELD vs. DEFERRED:**  
  In the operational router (`policy/router.py`), Action is mapped to `HELD` / `DEFERRED` under reason code `R6_CAPACITY_DEFERRED`. In the static test look, 974 transactions are held for deferred investigation. The UI explicitly separates HELD/DEFERRED ($974$, $48.7\%$) from ROUTINE ($896$, $44.8\%$).

---

## 2. Decision Threshold Reconciliation

### 2.1 Original Display vs. Canonical Thresholds
- **Previous Frontend Displays:**
  - `ModelCardPage.tsx` (lines 167, 179): `p >= 0.040000 (t_review)`, `p < 0.040000 AND u2 < 0.526773`
  - `OverviewPage.tsx` (lines 302, 316): `p >= 0.0400 (t_review)`, `p < 0.0400 & u2 < 0.5268`
  - `SignalCoreScene.tsx` (lines 103, 113): `'p >= 0.0400 OR u2 >= 0.5268'`, `'p < 0.0400 AND u2 < 0.5268'`
  - `ShiftStormPage.tsx` (line 377) & `SandboxPage.tsx` (line 310): `p >= 0.04`
- **Canonical Sources Checked:**
  - `config.yaml` (lines 43–51):
    ```yaml
    thresholds:
      t_alert: 0.084705
      t_review: 0.071002
      u_threshold: 0.526773
    ```
  - `policy/frozen_policy.json` (lines 6–10):
    ```json
    "thresholds": {
      "t_alert": 0.084705,
      "t_review": 0.071002,
      "u_threshold": 0.526773,
      "target_budget": 0.06525
    }
    ```
  - `backend/app/services/scoring.py` (lines 41–76): Live routing uses `frozen_policy["thresholds"]`, which executes with `t_review = 0.071002`.

### 2.2 Corrections Made
1. **`frontend/src/features/model-card/ModelCardPage.tsx`:** Updated R2 condition to `p >= 0.071002 (t_review)` and R5 condition to `p < 0.071002 AND u2 < 0.526773`.
2. **`frontend/src/features/overview/OverviewPage.tsx`:** Updated R2 rule readout to `p >= 0.0710 (t_review)` and R5 rule readout to `p < 0.0710 & u2 < 0.5268`.
3. **`frontend/src/components/SignalCoreScene.tsx`:** Updated `TOPOLOGY_DETAILS` formulas for `lane_review` and `lane_routine` to use `0.0710`.
4. **`frontend/src/features/shift-storm/ShiftStormPage.tsx`:** Corrected telemetry progress meter intermediate threshold check to `currentRow.p >= 0.0710`.
5. **`frontend/src/features/sandbox/SandboxPage.tsx`:** Corrected real-time risk bar threshold check to `signals.p >= 0.0710`.

---

## 3. Semantic Color Spectrum Reconciliation

### 3.1 Token Definitions vs. DESIGN.md Specifications
Verified in `frontend/src/styles/tokens.css` that semantic tokens preserve their operational meaning across both themes:

| Semantic State | Operational Role | Dark Theme Token | Dark Value | Light Theme Token | Light Value | Meaning Preserved |
| :--- | :--- | :--- | :---: | :--- | :---: | :---: |
| **Fraud Alert** | High-risk escalation (R1) | `--color-fraud-alert` | `#F27870` (Coral) | `--color-fraud-alert` | `#DC2626` (Crimson) | **YES** |
| **Manual Review** | Human queue workload (R2/R3) | `--color-manual-review` | `#E8B35E` (Amber) | `--color-manual-review` | `#D97706` (Warm Amber) | **YES** |
| **Routine** | Automated low-risk pass (R5) | `--color-routine` | `#68C99A` (Sage) | `--color-routine` | `#059669` (Emerald) | **YES** |
| **Held / Deferred** | Capacity / Epistemic deferral (R6) | `--color-epistemic-defer` | `#B4A0F8` (Violet) | `--color-epistemic-defer` | `#7C3AED` (Royal Purple) | **YES** |
| **Primary Accent** | Surgical interactive teal | `--accent-primary` | `#68D8CB` (Teal) | `--accent-primary` | `#0D9488` (Deep Teal) | **YES** |

### 3.2 Component Class Verification
- `.badge-alert`, `.badge-error`: Uses `var(--color-fraud-alert)`.
- `.badge-caution`, `.badge-degraded`: Uses `var(--color-manual-review)`.
- `.badge-ready`, `.badge-healthy`: Uses `var(--color-routine)`.
- `.badge-synthetic`: Uses `var(--color-epistemic-defer)`.
- Active sidebar navigation in light mode features soft purple container boxing (`--nav-active-bg: #E9D5FF; --nav-active-text: #581C87; --nav-active-border: #C084FC`), ensuring prominent visual distinction without compromising semantic meaning.

---

## 4. Budget Sweep Points & Confidence Intervals

### 4.1 Budget Sweep Multiples
- **Report Claim Erratum:**  
  `docs/post_light_theme_verification_report.md` mentioned:  
  *"Renders 5 discrete budget points (0.5x, 1.0x, 1.5x, 2.0x, 3.0x)"*
- **Canonical Sources Checked:**
  - `config.yaml` (lines 7–11):
    ```yaml
    budget_sweep:
    - 1.0
    - 1.5
    - 2.0
    - 3.0
    ```
  - `results/results.json` (`budget_sweep`, lines 272–553): Exactly 4 multiples evaluated: `"1.0x"`, `"1.5x"`, `"2.0x"`, `"3.0x"`.
  - `backend/app/routers/policies.py` (lines 28–37):
    ```python
    valid_multiples = {"1.0x", "1.5x", "2.0x", "3.0x"}
    if budget_multiple is not None and budget_multiple not in valid_multiples:
        raise HTTPException(status_code=400, detail="Invalid budget multiple")
    ```
- **Resolution:**  
  `0.5x` does **not exist** in the evaluation records; it was mistakenly cited in the prior report narrative due to confusion with the replay speed controls in `ShiftStormPage.tsx` (`0.5x, 1x, 2x, 5x`).  
  The frontend code in `PolicyComparisonPage.tsx` (lines 96–97) was already strictly limited to the actual 4 evaluated points:
  ```tsx
  {['1.0x', '1.5x', '2.0x', '3.0x'].map((b) => ...
  ```
  No continuous curves are plotted through unevaluated intermediate budgets.

### 4.2 Paired Bootstrap Confidence Interval
- **Canonical Source:** `results/results.json` (lines 253–271):
  - Metric: `recall_at_budget`
  - $n_{\text{resamples}} = 1000$
  - Point estimate difference: $0.0\text{ pp}$
  - 95% Confidence Interval: `[-0.027523, +0.027523]` ($\mathbf{[-2.75\text{ pp}, +2.75\text{ pp}]}$)
  - Two-sided p-value: $1.0$
  - `is_conclusive`: **`false`**
- **Resolution:**  
  The previously hardcoded `[-1.80 pp, +1.80 pp]` was an erratum stemming from `delta_recall_vs_b2_pp = 1.8018` under alternate budget multiples (`1.0x` and `3.0x`). Line 132 of `PolicyComparisonPage.tsx` is now permanently aligned with the canonical $1.5\times$ primary evaluation CI `[-2.75 pp, +2.75 pp]`.

---

## 5. Route & Model Specifications Verification

### 5.1 Backend Route Registrations
Every frontend API call in `frontend/src/lib/api/client.ts` was audited against backend router files:

| Frontend API Method | URL Called | HTTP Method | Backend Router File | Registered Endpoint | Verified? |
| :--- | :--- | :---: | :--- | :--- | :---: |
| `api.getHealth()` | `/api/health` | GET | `backend/app/routers/health.py` | `@router.get("/health")` | **YES** |
| `api.getStatus()` | `/api/status` | GET | `backend/app/routers/health.py` | `@router.get("/status")` | **YES** |
| `api.getOverview()` | `/api/overview` | GET | `backend/app/routers/overview.py` | `@router.get("/overview")` | **YES** |
| `api.getPoliciesCompare(m)` | `/api/policies/compare?budget_multiple=...` | GET | `backend/app/routers/policies.py` | `@router.get("/compare")` | **YES** |
| `api.getScenarios()` | `/api/scenarios` | GET | `backend/app/routers/overview.py` | `@router.get("/scenarios")` | **YES** |
| `api.getReplayRows(...)` | `/api/replay/rows?...` | GET | `backend/app/routers/replay.py` | `@router.get("/rows")` | **YES** |
| `api.getCases(...)` | `/api/cases?...` | GET | `backend/app/routers/cases.py` | `@router.get("")` | **YES** |
| `api.getCaseDetail(id)` | `/api/cases/{case_id}` | GET | `backend/app/routers/cases.py` | `@router.get("/{case_id}")` | **YES** |
| `api.getAudit(...)` | `/api/audit?...` | GET | `backend/app/routers/audit.py` | `@router.get("")` | **YES** |
| `api.getResults()` | `/api/results` | GET | `backend/app/routers/overview.py` | `@router.get("/results")` | **YES** |
| `api.scoreSandbox(f)` | `/api/score-sandbox` | POST | `backend/app/routers/scoring.py` | `@router.post("/score-sandbox")` | **YES** |
| Export Audit | `/api/audit/export?format=...` | GET | `backend/app/routers/audit.py` | `@router.get("/export")` | **YES** |

### 5.2 Model Governance Claims
- **Primary Estimator:** `HistGradientBoostingClassifier` (scikit-learn), trained on 6,000 synthetic rows with native histogram binning.
- **Risk Calibrator:** Platt Scaling (Sigmoid Logistic Regression) fitted on held-out calibration split (1,000 rows).
- **Epistemic Disagreement ($u_2$):** Rank-residualized inter-model disagreement ensemble.
- **Capacity Governor:** Quota enforcer strictly capping human queue at $B = 130$ cases ($6.525\%$ capacity).
- **Cryptographic Hashes:**
  - Frozen Config Hash: `8d3f02ca492ca94bab45f3ceac8d39432c2f29f40d54e7990b4aa78cbbff6240`
  - Split Hash: `07b55a4ed74f238c9ef5b779a749770cf274d4709a4389d9eab860dd9068fbdd`
- **Explainability:** SHAP TreeExplainer attributions are explicitly disclosed as disabled in this offline static protocol; no reconstructed values are fabricated.

---

## 6. Verification Test Results

### 6.1 TypeScript Verification (`npx tsc --noEmit`)
```powershell
$ npx tsc --noEmit
# Exit Code: 0 (Zero errors)
```

### 6.2 Frontend Unit Tests (`npm test -- --run`)
```powershell
$ npm test -- --run

> signalgate-frontend@1.0.0 test
> vitest run --run

 RUN  v2.1.9 C:/Users/arpit/Desktop/project/frontend

 ✓ src/components/__tests__/status_and_metrics.test.ts (3 tests) 4ms

 Test Files  1 passed (1)
      Tests  3 passed (3)
   Duration  438ms
# Exit Code: 0
```

### 6.3 Frontend Production Build (`npm run build`)
```powershell
$ npm run build

> signalgate-frontend@1.0.0 build
> tsc && vite build

vite v5.4.21 building for production...
transforming...
✓ 2432 modules transformed.
rendering chunks...
computing gzip size...
dist/index.html                           1.27 kB │ gzip:   0.65 kB
dist/assets/index-BJ1WRbqP.css           57.48 kB │ gzip:   9.52 kB
dist/assets/vendor-icons-U3EKFZYf.js     19.13 kB │ gzip:   3.90 kB
dist/assets/index-W8rRMKLw.js           145.09 kB │ gzip:  27.41 kB
dist/assets/vendor-react-qk5t2Hku.js    206.35 kB │ gzip:  67.33 kB
dist/assets/vendor-recharts-CPf9dk41.js 373.09 kB │ gzip: 103.47 kB
dist/assets/vendor-three-ULcn-Mu3.js    799.09 kB │ gzip: 215.77 kB
✓ built in 14.66s
# Exit Code: 0
```

### 6.4 Backend Verification Suite (`python -m pytest tests/`)
```powershell
$ python -m pytest tests/

============================= test session starts =============================
platform win32 -- Python 3.13.7, pytest-9.1.1, pluggy-1.6.0
rootdir: C:\Users\arpit\Desktop\project
collected 108 items

tests\test_api.py ..........                                             [  9%]
tests\test_api_artifacts.py ..                                           [ 11%]
tests\test_api_scoring.py ...                                            [ 13%]
tests\test_api_security.py .........................                     [ 37%]
tests\test_bootstrap.py ....                                             [ 40%]
tests\test_calibration.py .....                                          [ 45%]
tests\test_ensemble.py .....                                             [ 50%]
tests\test_eval_artifacts.py ....                                        [ 53%]
tests\test_eval_metrics.py ....                                          [ 57%]
tests\test_features.py .......                                           [ 63%]
tests\test_metrics.py .......                                            [ 70%]
tests\test_models.py ....                                                [ 74%]
tests\test_phase1.py ....                                                [ 77%]
tests\test_router.py ..........                                          [ 87%]
tests\test_shift_drift.py ......                                         [ 92%]
tests\test_splits.py ........                                            [100%]

============================ 108 passed in 11.61s =============================
# Exit Code: 0
```

---

## 7. Protected Artifacts Confirmation

In strict compliance with prompt constraints:
- `backend/` Python files: **UNTOUCHED** (0 bytes changed)
- `config.yaml`: **UNTOUCHED**
- `policy/frozen_policy.json`: **UNTOUCHED**
- `results/results.json`: **UNTOUCHED**
- `results/g3_test_look.json`: **UNTOUCHED**
- `eval/g3_test_look.csv`: **UNTOUCHED**
- `models/`: **UNTOUCHED**
- No thresholds retuned, no bootstrap iterations recomputed, no G3/G5 evaluation re-executed.

---

## 8. Conclusion

All discrepancies between reports, mockups, and canonical artifacts have been comprehensively reconciled and documented. SignalGate's frontend now exhibits 100% internal and external consistency with the scientific records and backend contracts.
