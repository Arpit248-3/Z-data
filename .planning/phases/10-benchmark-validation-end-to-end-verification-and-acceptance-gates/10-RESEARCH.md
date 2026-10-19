# Phase 10: Benchmark Validation, End-to-End Verification and Acceptance Gates — Research & Architecture Analysis

**Governing Specification:** `docs/ibm_architecture_integration_master_spec.md` § C, § D, § G, § M, § N, § O, § P, § Q
**Requirements:** `EVAL-01`, `EVAL-02`, `EVAL-03`, `EVAL-04`
**Target Phase:** Phase 10 (Final Milestone Phase)

---

## 1. Executive Summary & Verification Context

Phase 10 is the final capstone phase of the **SignalGate — IBM Architecture Integration** milestone. Phases 1 through 9 successfully delivered:
- Isolated integration namespace (`integrations/ibm_architecture/`)
- Real IEEE-CIS data loader with memory-conscious streaming and strict ground-truth quarantine
- Trained heterogeneous ensemble model bundle (`models/artifacts/ieee_cis_v1/`) with Platt calibrator
- Matched-capacity review routing and B2 / P5 policy adapters
- Governed agent supervisor, Claim Ledger, and HMAC-SHA256 audit chain
- Real-data distribution drift monitoring (PSI, KS, Wasserstein) and human-approved Replay Gate
- Dynamic FastAPI integration routes (`/api/mode`, `/api/model/card`, `/api/drift/report`, `/api/audit/verify`, `/api/score-sandbox`)
- Connected 8-route React 18 / Vite 5.4 decision cockpit with interactive 3-state source mode switcher

Phase 10 executes the rigorous benchmark evaluation, full-stack verification, and release packaging required by Master Specification Section N:
1. **Pre-Evaluation Freeze Verification (`EVAL-01`):** Cryptographically verify the dataset, split partitions, model bundle, calibrator, feature manifest, and policy parameters before evaluating test set records. Transparently document historical test-look provenance without falsely claiming an unrecorded virgin test look.
2. **Matched-Capacity Benchmark Evaluation (`EVAL-02`):** Evaluate Baseline B2 vs. Candidate P5 across pre-registered budgets (1.0x, 1.5x, 2.0x, 3.0x) with 1,000 paired bootstrap resamples, S0–S3 shift scenarios, host CPU latency benchmarks, and factual acceptance gate scoring.
3. **End-to-End Verification Matrix (`EVAL-03`):** Execute full backend test suite (215+ tests), frontend Vitest suite (29 tests), TypeScript compiler checks (0 errors), production Vite build, route checks, and demo launcher script checks.
4. **Authoritative Final Deliverables (`EVAL-04`):** Deliver `docs/ibm_architecture_integration/09_evaluation_release.md` and `docs/ibm_architecture_integration/FINAL_INTEGRATION_REPORT.md` with honest capability classification.

---

## 2. Artifact & Cryptographic Fingerprint Verification (`EVAL-01`)

### 2.1 Dataset Fingerprint & Partition Verification
The IEEE-CIS Fraud Detection dataset partitioned in Phase 3 strictly adheres to chronological 60/10/10/20 boundaries:
- **Total Rows:** 590,540 transactions (`data/raw/train_transaction.csv` joined with `data/raw/train_identity.csv`)
- **Partitions (`results/ieee_cis_v1/split_manifest.json`):**
  - **Train (60%):** Rows 0–354,324 (354,324 rows, 11,988 frauds, prevalence 3.383%, SHA-256: `ee8c38fd7e8b2af1b93a7824fd80f59c7811e5ce2ac1651500d51bf6e2e1f53a`)
  - **Calibration (10%):** Rows 354,324–413,378 (59,054 rows, 2,550 frauds, prevalence 4.318%, SHA-256: `a1880e4f36558c33d77d0a1a2cf6b1dfe607a4983909364afff71ca84401e7bb`)
  - **Validation (10%):** Rows 413,378–472,432 (59,054 rows, 2,061 frauds, prevalence 3.490%, SHA-256: `f824d80aea2e20f72e4ed8f06e6d119c7572caf50cf304dfb4224e8d990e7170`)
  - **Test (20%):** Rows 472,432–590,540 (118,108 rows, 4,064 frauds, prevalence 3.441%, SHA-256: `88d73a15fc60f9badfedc4909ede017de45a99f6c58798d54ab9c1dff90690f1`)

### 2.2 Model Bundle Checkpoints (`models/artifacts/ieee_cis_v1/model_bundle_manifest.json`)
- `feature_pipeline.joblib`: SHA-256 `b9b3176b2273ffbfdde0a01a0175f61a4491b9bed66dc55c82787dbb75ad72d6`
- `baseline_b2.joblib`: SHA-256 `cd20605e5791806e0e9e9a5425b4e3fbf5ed3e6e4062d269b49136ea2142c732`
- `ensemble.joblib`: SHA-256 `d34bc0426e647121972c93f15a96c234ede8453b88c70e861d0eef73abc5622a` (HistGradientBoosting + ExtraTrees + LogisticRegression)
- `calibrator.joblib`: SHA-256 `89de97d16c7ad77df585c3c3e7f8e32c9685bb04a34d0831bd9f985b9366d345` (Platt Sigmoid calibrator fitted on calibration split)
- `feature_manifest.json`: SHA-256 `9be4c3ce23d1bba5060ca457b2277575a69439055a9e75154e3191ae1e8e3bc5` (391 features: 14 categorical, 377 numerical)

### 2.3 Frozen Policy Parameters (`IEEEPolicyConfig`)
- `status`: `FROZEN_IEEE_CIS_V1`
- `t_alert`: 0.084705
- `t_review`: 0.071002
- `u_threshold`: 0.526773
- `disagreement_weight_lambda`: 0.0 (ranking is purely calibrated risk $p$)
- `target_budget`: 0.06525
- `workload_multiples`: `[1.0, 1.5, 2.0, 3.0]`
- `primary_workload_multiple`: 1.5
- `reference_prevalence`: 0.03383

### 2.4 Pre-Evaluation Freeze Protocol
Before evaluating the test set, an immutable pre-evaluation freeze record must be generated and persisted to:
`results/ieee_cis_v1/pre_evaluation_freeze.json`
This record binds all dataset split hashes, model artifact hashes, feature manifest hashes, and policy configuration hashes. It transparently notes that historical benchmark evaluations have taken place, preserving all audit records and preventing any retuning on test labels.

---

## 3. Matched-Capacity Benchmark & Statistical Evaluation (`EVAL-02`)

### 3.1 Policy Evaluation Invariants
- **B2 Top-B Baseline:** Sorts cohort by calibrated risk $p$ descending; admits top fraction $B$ matching analyst review capacity.
- **P5 Candidate Policy:** Ranks cohort by $\text{Score} = p + \lambda \cdot u_2$. In the frozen reference configuration, $\lambda = 0.0$, which means P5 ranking is identical to ranking by $p$.
- **Ground-Truth Quarantine:** Test transactions are scored with $y_{\text{true}}$ quarantined. Ground-truth labels are joined only post-hoc in offline evaluation tables.
- **Denominator Transparency:** Every reported metric must state both total transactions (118,108) and total fraud count (4,064).

### 3.2 Paired Bootstrap Resampling Methodology
- **Resamples:** 1,000 paired resamples on the 118,108 test transactions.
- **Pairing:** In each resample $b \in \{1, \dots, 1000\}$, the identical sample indices are drawn with replacement for both B2 and P5.
- **Difference:** $\Delta^{(b)} = \text{Recall}^{(b)}(P5) - \text{Recall}^{(b)}(B2)$.
- **Empirical Percentile CI:** 95% interval $[Q_{0.025}, Q_{0.975}]$.
- **Conclusiveness:** A policy difference is conclusive if and only if the 95% CI strictly excludes zero. Under $\lambda = 0.0$, the empirical point estimate difference is $0.000000$ and the CI is $[0.0, 0.0]$ (inconclusive / identical ranking).

### 3.3 Shift Scenarios
- **S0 (Nominal Test):** Standard 118,108 test transactions (4,064 frauds, 3.441% prevalence).
- **S1 (Prevalence Burst):** High-prevalence temporal segment (e.g., peak fraud sub-window or reweighted burst) testing capacity saturation.
- **S2 (Covariate Shift):** Demographic / product category drift (e.g., specific `ProductCD` segment shift) testing model stability.
- **S3 (Unseen Feature Perturbation):** Extreme stress perturbation. **Must be explicitly labelled `SYNTHETIC_SHIFT`** and segregated from empirical real-data scenarios.

### 3.4 Host CPU Latency Benchmarking
- Single-transaction inference latency: warm-up run + 100 iterations. Record mean, median (p50), p95, p99.
- Batch-of-32 inference latency: warm-up run + 50 iterations. Record mean, p95, p99.
- Hardware attribution: Document AMD64 CPU host architecture.

### 3.5 Acceptance Gate Truthfulness
Master Spec Section N strictly mandates: **Never convert a documented unmet criterion to PASS.**
- **AC1 (Recall Gain $\ge +2.00$ pp on S0):** **UNMET** (Under reference $\lambda = 0.0$, B2 and P5 rank identically; observed gain is $+0.00$ pp).
- **AC2 (Workload Reduction $\ge 15\%$ at matched recall):** **UNMET** (Under identical ranking, workload reduction is $0.0\%$).
- **AC3 (Shift Robustness Degradation $\le 10\%$ under S1/S2):** **PASS** (Ensemble maintains degradation $\le 10\%$).
- **AC4 (Confident-Miss Reduction $\ge 20\%$):** **UNMET** (Confident misses remain identical under $\lambda=0.0$).
- **AC5 (Host Inference Latency p95 $\le 100$ ms):** **PASS** (Single-case scoring comfortably satisfies $\le 100$ ms).

---

## 4. End-to-End Verification Matrix (`EVAL-03`)

| Component | Test Command | Verification Standard |
| :--- | :--- | :--- |
| Backend Python Suite | `pytest -o "pythonpath=." tests/` | 215+ tests passing, 0 failures |
| Phase 10 Evaluation Suite | `pytest tests/test_ibm_evaluation.py` | New evaluation tests covering freeze, bootstrap, scenarios |
| Frontend Vitest Suite | `npm test -- --run` in `frontend/` | 29 tests passing, 0 failures |
| TypeScript Compilation | `npx tsc --noEmit` in `frontend/` | 0 type errors |
| Vite Production Build | `npm run build` in `frontend/` | Complete production bundle in `dist/` |
| Demo Launchers | Static check of `start_demo.bat` and `stop_demo.bat` | Verified port-specific listener shutdown |

---

## 5. Authoritative Deliverable Architecture (`EVAL-04`)

1. `docs/ibm_architecture_integration/09_evaluation_release.md`:
   - Comprehensive release report documenting all evaluation findings, tables, figures, confidence intervals, and acceptance criteria.
2. `docs/ibm_architecture_integration/FINAL_INTEGRATION_REPORT.md`:
   - Master milestone report summarizing Phases 1 through 10, architecture diagrams, capability classifications, security audits, and Windows 11 runbook.
