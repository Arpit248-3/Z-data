# SignalGate Phase 10 — Evaluation, Reproducibility and Acceptance Gates Release Deliverable

**Document Reference:** `docs/ibm_architecture_integration/09_evaluation_release.md`
**Governing Specification:** `docs/ibm_architecture_integration_master_spec.md` § C, § D, § G, § M, § N, § O, § P, § Q
**Requirements Validated:** `EVAL-01`, `EVAL-02`, `EVAL-03`, `EVAL-04`
**Phase:** 10 (`10-benchmark-validation-end-to-end-verification-and-acceptance-gates`)
**Status:** Completed, Cryptographically Bound & Empirically Verified

---

## 1. Executive Summary & Evaluation Framework

SignalGate is a shift-aware financial fraud decision support platform engineered with a deterministic Python core, a 3-member heterogeneous machine learning ensemble, capacity-governed routing, a cryptographic HMAC-SHA256 audit ledger, and an interactive 3-state source mode React cockpit.

Phase 10 represents the final evaluation gate of the **SignalGate — IBM Architecture Integration** milestone. In strict conformance with Master Specification Section N:
1. **Pre-Evaluation Freeze Protocol (`EVAL-01`):** All pre-evaluation artifacts (dataset splits, feature manifests, model bundle checkpoints, calibrators, and policy parameters) were cryptographically fingerprinted before test set evaluation. An immutable record was generated at `results/ieee_cis_v1/pre_evaluation_freeze.json` (SHA-256 freeze hash: `8b88c1f712235a15b80d6f7bfa0f742c4f1624279cbaa2f24547df78e32cb2d1`). Prior test looks are transparently acknowledged; no virgin look is falsely claimed.
2. **Matched-Capacity Benchmark Evaluation (`EVAL-02`):** Baseline B2 and Candidate P5 were evaluated under identical test records (118,108 transactions, 4,064 true frauds) across registered review budgets ($1.0\times, 1.5\times, 2.0\times, 3.0\times$ multiples of reference prevalence) with 1,000 paired bootstrap resamples, S0–S3 shift scenarios, host CPU latency benchmarks, and factual acceptance gate scoring.
3. **End-to-End Regression Matrix (`EVAL-03`):** Verified 100% passing across 224 backend Pytest tests, 29 frontend Vitest tests, zero TypeScript compiler errors (`npx tsc --noEmit`), and clean production Vite bundling.
4. **Authoritative Deliverables (`EVAL-04`):** Authored this comprehensive release deliverable and the companion master integration report `FINAL_INTEGRATION_REPORT.md` with honest capability classification.

```mermaid
flowchart TD
    subgraph PreEvalFreeze ["Pre-Evaluation Freeze (EVAL-01)"]
        F1["Split Manifest (60/10/10/20)"]
        F2["Model Bundle (HistGradBoost + ExtraTrees + LogReg)"]
        F3["Platt Calibrator (Fitted on Calibration Split)"]
        F4["Feature Manifest (391 Features)"]
        F5["Frozen Policy (t_alert, t_review, u_th, lambda=0.0)"]
        F1 & F2 & F3 & F4 & F5 --> FreezeHash["Freeze Hash: 8b88c1f71223...<br/>results/ieee_cis_v1/pre_evaluation_freeze.json"]
    end

    subgraph BenchmarkExec ["Matched-Capacity Benchmark (EVAL-02)"]
        TestSet["Test Partition (118,108 Rows, 4,064 Frauds)"]
        B2["B2 Top-B Baseline"]
        P5["P5 Candidate (lambda=0.0)"]
        Sweeps["Sweeps: 1.0x, 1.5x, 2.0x, 3.0x"]
        Bootstrap["1,000 Paired Bootstrap Resamples"]
        Scenarios["Shift Scenarios (S0, S1, S2, S3-Synthetic)"]
        Latency["Host AMD64 Latency Micro-Benchmark"]

        FreezeHash --> TestSet --> B2 & P5 --> Sweeps --> Bootstrap --> Scenarios --> Latency
    end

    subgraph ReleaseArtifacts ["Verified Deliverables (EVAL-03, EVAL-04)"]
        R_JSON["results/ieee_cis_v1/benchmark_results.json"]
        D_REL["docs/ibm_architecture_integration/09_evaluation_release.md"]
        D_FIN["docs/ibm_architecture_integration/FINAL_INTEGRATION_REPORT.md"]
        Latency --> R_JSON & D_REL & D_FIN
    end
```

---

## 2. Pre-Evaluation Freeze Audit Table (`EVAL-01`)

The immutable pre-evaluation freeze record was generated and persisted prior to test partition evaluation:
- **Record Path:** `results/ieee_cis_v1/pre_evaluation_freeze.json`
- **Freeze Fingerprint:** `8b88c1f712235a15b80d6f7bfa0f742c4f1624279cbaa2f24547df78e32cb2d1`
- **Historical Look Acknowledgement:** Transparently documents that this evaluation represents a verified reproduction and acceptance gate execution under Master Spec Section N, preserving prior G3/G5 test-look records and not falsely claiming an unrecorded virgin test look.

| Component | Target Artifact / Partition | Canonical SHA-256 Checksum | Dimensions / Parameters |
| :--- | :--- | :--- | :--- |
| **Train Split (60%)** | `split_manifest.json` partition `train` | `ee8c38fd7e8b2af1b93a7824fd80f59c7811e5ce2ac1651500d51bf6e2e1f53a` | 354,324 rows (11,988 frauds, 3.383% prevalence) |
| **Calibration Split (10%)** | `split_manifest.json` partition `calibration` | `a1880e4f36558c33d77d0a1a2cf6b1dfe607a4983909364afff71ca84401e7bb` | 59,054 rows (2,550 frauds, 4.318% prevalence) |
| **Validation Split (10%)** | `split_manifest.json` partition `validation` | `f824d80aea2e20f72e4ed8f06e6d119c7572caf50cf304dfb4224e8d990e7170` | 59,054 rows (2,061 frauds, 3.490% prevalence) |
| **Test Split (20%)** | `split_manifest.json` partition `test` | `88d73a15fc60f9badfedc4909ede017de45a99f6c58798d54ab9c1dff90690f1` | 118,108 rows (4,064 frauds, 3.441% prevalence) |
| **Feature Pipeline** | `models/artifacts/ieee_cis_v1/feature_pipeline.joblib` | `b9b3176b2273ffbfdde0a01a0175f61a4491b9bed66dc55c82787dbb75ad72d6` | 391 features (14 categorical, 377 numerical) |
| **Baseline Model (B2)** | `models/artifacts/ieee_cis_v1/baseline_b2.joblib` | `cd20605e5791806e0e9e9a5425b4e3fbf5ed3e6e4062d269b49136ea2142c732` | HistGradientBoosting base estimator |
| **Ensemble Model** | `models/artifacts/ieee_cis_v1/ensemble.joblib` | `d34bc0426e647121972c93f15a96c234ede8453b88c70e861d0eef73abc5622a` | 3 members: HistGradBoost + ExtraTrees + LogReg |
| **Platt Calibrator** | `models/artifacts/ieee_cis_v1/calibrator.joblib` | `89de97d16c7ad77df585c3c3e7f8e32c9685bb04a34d0831bd9f985b9366d345` | Platt Sigmoid fitted on 59,054 calibration records |
| **Feature Manifest** | `results/ieee_cis_v1/feature_manifest.json` | `9be4c3ce23d1bba5060ca457b2277575a69439055a9e75154e3191ae1e8e3bc5` | 391 features; strict quarantine of `isFraud`, IDs |
| **Frozen Policy** | `integrations/ibm_architecture/policy/frozen_policy.py` | Config Hash: `f5f4a23cfa3b0d343f4c9bd28d3b76a4eb88839e148dc46497800940cbd4fd8e` | $t_{\text{alert}}=0.084705, t_{\text{review}}=0.071002, u_{\text{th}}=0.526773, \lambda=0.0$ |

---

## 3. Model Accuracy & Calibration on Held-Out Test Partition

Inference was executed on the 118,108 held-out test transactions using the serialized model bundle:
- **Transform Duration:** 2.50s (47,243 rows/sec)
- **Scoring Duration:** 18.36s (6,432 rows/sec across the 3-member ensemble)

| Metric | Heterogeneous Ensemble (Platt Calibrated) | Baseline B2 (Uncalibrated Base) | Relative Advantage / Observation |
| :--- | :--- | :--- | :--- |
| **ROC-AUC** | **0.880471** | **0.881911** | Parity ($-0.0014$ ROC-AUC difference) |
| **PR-AUC** | **0.460812** | **0.446793** | **+1.40 percentage points** PR-AUC advantage for Ensemble |
| **Brier Score Loss** | **0.024619** | **0.098420** | **75.0% lower** mean squared probability error |
| **Expected Calibration Error (ECE)** | **0.008889** | **0.222197** | **96.0% calibration error reduction** (see Calibration Qualification below) |
| **Confident Misses ($p < 0.01$ false neg)** | **441** | **0** | Calibration artifact: uncalibrated B2 rarely outputs scores $< 0.01$ (see note below) |

> [!NOTE]
> **Ensemble Architecture Clarification:** The authoritative IEEE-CIS model bundle serialized at `models/artifacts/ieee_cis_v1/ensemble.joblib` and recorded in `models/artifacts/ieee_cis_v1/model_bundle_manifest.json` comprises three scikit-learn estimators: `HistGradientBoostingClassifier`, `ExtraTreesClassifier`, and `LogisticRegression`. Any prior tentative working notes mentioning external gradient boosting libraries (LightGBM, CatBoost, XGBoost) were superseded during Phase 4 model training in favor of this fully reproducible, dependency-isolated scikit-learn ensemble.
>
> **Calibration Comparison Qualification:**
> 1. **Uncalibrated vs. Calibrated Baseline:** Baseline B2 (`baseline_b2.joblib`) is an **uncalibrated base estimator**, while the 3-member ensemble is post-processed through a **Platt sigmoid calibrator** fitted on the dedicated 59,054-row calibration split. Consequently, the direct ECE comparison ($0.008889$ vs. $0.222197$) must be recognized as an uncalibrated-vs-calibrated comparison rather than a like-for-like calibration evaluation.
> 2. **Confident Misses ($p < 0.01$) Analysis:** B2 records 0 confident misses under $p < 0.01$ solely because its uncalibrated sigmoid-transformed raw outputs are compressed away from the extremes, never assigning scores below $0.01$. Conversely, the Platt-calibrated ensemble outputs authentic posterior probabilities across $[0, 1]$, accurately placing low-risk transactions in the $[0, 0.01)$ bracket where 441 false negatives reside out of 4,064 total frauds ($10.8\%$). This difference is a mathematical artifact of calibration curve morphology, not superior detection sensitivity in B2.

---

## 4. Matched-Capacity Review Budget Sweep (`EVAL-02`)

Workload budget multiples were evaluated across $M \in [1.0, 1.5, 2.0, 3.0]$ relative to reference prevalence ($0.03383$).
- **Total Test Transactions ($N$):** 118,108
- **Total Test Frauds ($P$):** 4,064 (prevalence: 3.441%)
- **Policy Comparison:** Baseline B2 ([`B2TopBudgetBaselineAdapter`](file:///c:/Users/himan/Downloads/zprject/integrations/ibm_architecture/policy/baselines.py)) vs. Candidate P5 ([`P5CandidatePolicyAdapter`](file:///c:/Users/himan/Downloads/zprject/integrations/ibm_architecture/policy/p5_candidate.py)).

| Multiple | Target Budget Fraction | Review Capacity Slots | Caught Fraud (B2) | Caught Fraud (P5) | Touched Rate | Realized Recall (B2) | Realized Recall (P5) | Precision | Recall Gain ($\Delta$) |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **1.0x** | 0.033830 | 3,995 | 1,777 / 4,064 | 1,777 / 4,064 | 3.3825% | **43.725%** | **43.725%** | 44.481% | **+0.000 pp** |
| **1.5x (Primary)** | 0.050745 | 5,993 | 2,067 / 4,064 | 2,067 / 4,064 | 5.0742% | **50.861%** | **50.861%** | 34.490% | **+0.000 pp** |
| **2.0x** | 0.067660 | 7,991 | 2,271 / 4,064 | 2,271 / 4,064 | 6.7658% | **55.881%** | **55.881%** | 28.419% | **+0.000 pp** |
| **3.0x** | 0.101490 | 11,986 | 2,575 / 4,064 | 2,575 / 4,064 | 10.1483% | **63.361%** | **63.361%** | 21.483% | **+0.000 pp** |

> [!NOTE]
> **Identical Ranking Finding:** In the frozen reference configuration, the disagreement weighting parameter is explicitly frozen to $\lambda = 0.0$ (`IEEEPolicyConfig.disagreement_weight_lambda = 0.0`). Under this setting, the P5 ranking formula reduces to:
> $$\text{Score}_i = p_i + 0.0 \cdot u_{2, i} = p_i$$
> Because P5 and B2 both rank strictly by calibrated risk probability $p$, they produce mathematically identical selections. This confirms Master Spec Section D: *"The P5 reference policy with lambda zero is effectively ranking by calibrated risk alone. Do not claim that its ranking score adds disagreement-based prioritization."*

---

## 5. Paired Bootstrap Resampling Analysis (`EVAL-02`)

The primary protocol evaluated 1,000 paired bootstrap replicates on the full 118,108 test transactions:
- **Resamples Requested:** 1,000
- **Resamples Valid:** 1,000 (0 degenerate resamples)
- **Random Seed:** 42 (deterministic reproducibility)
- **Significance Level ($\alpha$):** 0.05 (95% empirical percentile confidence interval)
- **Observed Recall:** B2 = 50.8612%, P5 = 50.8612%
- **Point Estimate Difference ($\Delta$):** $+0.000000$
- **95% Confidence Interval:** $[+0.000000, +0.000000]$
- **Statistical Conclusiveness:** **INCONCLUSIVE (Identical Ranking)**. Because P5 and B2 evaluate identical row selections under $\lambda = 0.0$, the empirical difference across all 1,000 replicates is identically zero.

---

## 6. Shift Scenarios & Distribution Robustness

| Scenario | Evidence Status | Records & Frauds | Prevalence | Realized B2 Recall | Realized P5 Recall | Robustness Finding |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **S0: Nominal** | `EMPIRICAL_TEST_PARTITION` | 118,108 rows (4,064 frauds) | 3.441% | 50.861% | 50.861% | Nominal benchmark performance |
| **S1: Prevalence Burst** | `EMPIRICAL_TEST_BURST` | 23,621 rows (947 frauds) | 4.009% | 48.997% | 48.997% | Relative degradation: $3.66\%$ ($\le 10\%$ tolerance) |
| **S2: Covariate Shift** | `EMPIRICAL_SEGMENT_SHIFT` | 89,848 rows (2,374 frauds) | 2.642% | 52.148% | 52.148% | Segment-level recall stability preserved |
| **S3: Stress Perturbation** | `SYNTHETIC_SHIFT` | 118,108 rows (4,064 frauds) | 3.441% | 47.884% | 47.884% | Stress degradation: $5.85\%$ ($\le 10\%$ tolerance) |

> [!IMPORTANT]
> **Synthetic Segregation Compliance:** In strict adherence to Master Spec Section C1, Scenario S3 is explicitly classified as `SYNTHETIC_SHIFT` with a prominent disclaimer that it represents synthetic Gaussian perturbation testing, not empirical transaction activity.

---

## 7. Host AMD64 CPU Latency Micro-Benchmark

Benchmarks were executed on the local host Windows 11 AMD64 machine using Python 3.11 with initial warm-up iterations:
- **Single-Transaction Scoring ($N = 100$ calls):**
  - **Mean Latency:** 24.50 ms
  - **Median Latency (p50):** 20.15 ms
  - **95th Percentile Latency (p95):** **32.74 ms** (comfortably satisfies $\le 100.0$ ms target)
  - **99th Percentile Latency (p99):** 39.06 ms
- **Batch-of-32 Scoring ($N = 50$ calls):**
  - **Batch Mean Latency:** 27.20 ms
  - **Batch 95th Percentile (p95):** 35.25 ms
  - **Amortized Per-Row Latency:** **0.85 ms / row**
- **Hardware Platform:** Windows 11 AMD64 (Local Host CPU). No specialized GPU or coprocessor required.

---

## 8. Acceptance Criteria Scorecard (`EVAL-02`)

Master Specification Section N strictly mandates: **Never convert a documented unmet criterion to PASS.**
SignalGate adheres strictly to this truthfulness standard:

| Criterion | Target Requirement | Empirically Observed | Verdict | Spec Compliance Rationale |
| :--- | :--- | :--- | :---: | :--- |
| **AC1: S0 Recall Gain** | S0 recall improvement of P5 over B2 $\ge +2.00$ percentage points at primary $1.5\times$ budget | $+0.0000$ percentage points | **UNMET** | Under frozen reference configuration ($\lambda = 0.0$), P5 and B2 rank transactions identically. The $+2.00$ pp gain target is not achieved and is reported factually as UNMET. |
| **AC2: Workload Reduction** | Review workload reduction $\ge 15.0\%$ at matched baseline recall | $0.0\%$ reduction | **UNMET** | Because ranking order is identical, review workload to achieve equal recall is identical. Reported factually as UNMET. |
| **AC3: Shift Robustness** | Relative recall degradation $\le 10.0\%$ under S1 and S2 shift scenarios | Burst degradation: $3.66\%$ | **PASS** | Heterogeneous ensemble calibration maintains stable relative recall under burst and segment shifts. |
| **AC4: Confident-Miss Reduction** | Reduction of confident misses ($p < 0.01$ false negatives) $\ge 20.0\%$ | 441 misses (P5) vs 0 misses (B2) | **UNMET** | P5 produces identical confident misses to calibrated probability ranking. Reported factually as UNMET. |
| **AC5: Host Inference Latency** | Single-case host inference latency $\text{p95} \le 100.0$ ms on host CPU | $\text{p95} = 32.744$ ms | **PASS** | Single-row ensemble scoring averages ~20–33 ms on Windows AMD64 CPU, well within operational bounds. |

---

## 9. Full-Stack Verification & Regression Matrix (`EVAL-03`)

| Verification Gate | Command Executed | Result / Output | Status |
| :--- | :--- | :--- | :---: |
| **Python Backend Tests** | `pytest -o "pythonpath=." tests/` | **224 passed**, 23 warnings in 27.81s | **PASS (100%)** |
| **Phase 10 Evaluation Tests** | `pytest tests/test_ibm_evaluation.py` | **9 passed**, 0 failures in 3.16s | **PASS (100%)** |
| **Frontend Vitest Suite** | `npm test -- --run` in `frontend/` | **29 passed** across 5 test suites in 1.34s | **PASS (100%)** |
| **TypeScript Compilation** | `npx tsc --noEmit` in `frontend/` | 0 type errors, clean exit (code 0) | **PASS** |
| **Vite Production Build** | `npm run build` in `frontend/` | Clean build in 12.49s (`dist/assets/`) | **PASS** |
| **Artifact Checksum Check** | `python scripts/validate_artifacts.py` | 100% hash match across all synthetic & frozen files | **PASS** |
| **Demo Launchers** | Static check of `start_demo.bat` & `stop_demo.bat` | Verified port-specific listener shutdown | **PASS** |

---

## 10. Release Verdict & Deliverable Attestation

Phase 10 has satisfied all governing requirements for **SignalGate Phase 10 — Evaluation, Reproducibility and Acceptance Gates**:
- `EVAL-01` verified: Pre-evaluation freeze record generated and locked at `results/ieee_cis_v1/pre_evaluation_freeze.json`.
- `EVAL-02` verified: 118,108-row test partition evaluated across 4 budget levels with 1,000 paired bootstrap resamples and truthful acceptance criteria scoring.
- `EVAL-03` verified: 224 Pytest tests, 29 Vitest tests, TypeScript compilation, and production build cleanly passing.
- `EVAL-04` verified: Deliverable authored and released with complete provenance.
