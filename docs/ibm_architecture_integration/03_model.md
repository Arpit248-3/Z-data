# SignalGate IBM Architecture Integration — Phase 4: Models, Ensembles, Calibration & Artifact Bundles

**Governing Specification:** `docs/ibm_architecture_integration_master_spec.md` § C, § H
**Status:** IMPLEMENTED_VERIFIED
**Architecture Version:** `ieee_cis_v1`
**Execution Concurrency:** `sequential` (`extra_trees_n_jobs=1`, `hgb_threads=default`)
**Resource Safety Floor:** $\ge 6.0\text{ GB}$ available physical RAM
**Last Updated:** 2026-10-18

---

## 1. Executive Summary & Architecture Overview

Phase 4 establishes the clean-room, reproducible model training, ensemble learning, calibration, and epistemic uncertainty infrastructure for the IEEE-CIS Fraud Detection benchmark.

The architecture strictly adheres to the governing specification:
1. **Target Quarantine:** The ground-truth label `isFraud` and transaction identifiers (`TransactionID`, `TransactionDT`) are strictly quarantined and forbidden from entering feature matrices.
2. **Partition Fitting Governance:** Estimators fit strictly on the `train` partition (354,324 transactions). Platt calibrators fit strictly on the `calibration` partition (59,054 transactions). The `validation` partition (59,054 transactions) is used solely for permitted diagnostics. The `test` partition (118,108 transactions) remains strictly held out until final evaluation.
3. **Sequential Execution Protocol:** Estimators are trained sequentially in series with inter-stage garbage collection (`gc.collect()`), pre-stage dynamic physical RAM verification ($\ge 6.0\text{ GB}$ floor), and `n_jobs=1` on ExtraTrees, bounding peak memory consumption to ~2.8–3.5 GB.
4. **Isolated Namespace:** All real-data IEEE-CIS model artifacts and manifests are saved exclusively to `models/artifacts/ieee_cis_v1/`, leaving canonical synthetic models, frozen policies, historical benchmarks, and audit history intact.

---

## 2. Learned Feature Preprocessing Pipeline

The `FeaturePipeline` (`integrations/ibm_architecture/models/features.py`) converts raw tabular transaction records into a contiguous `float32` matrix of shape `(N, 391)`.

### 2.1 Schema Breakdown
- **377 Numerical Features:** `TransactionAmt`, `card1`–`card3`, `card5`, `addr1`–`addr2`, `dist1`–`dist2`, `C1`–`C14`, `D1`–`D15`, `V1`–`V339`.
  - Imputation: Median imputation learned strictly on the `train` partition.
  - Missing Value Handling: Missing numerical values in inference or holdout partitions are imputed with the training set medians.
- **14 Categorical Features:** `ProductCD`, `card4`, `card6`, `P_emaildomain`, `R_emaildomain`, `M1`–`M9`.
  - Encoding: Scikit-learn `OrdinalEncoder(handle_unknown="use_encoded_value", unknown_value=-1, encoded_missing_value=-1)`.
  - Deterministic alignment: Categoricals are processed in canonical manifest order and appended after the numerical matrix.

### 2.2 Leakage Quarantine Enforcement
The pipeline implements proactive inspection via `_check_quarantine()`:
- If `isFraud`, `TransactionID`, or `TransactionDT` (in any letter case) appear in the input DataFrame during `fit()` or `transform()`, the pipeline immediately raises `LeakageViolationError` with the violated field list.

---

## 3. Estimator & Ensemble Architecture

### 3.1 Standalone Baseline B2
- **Class:** `BaselineB2` (`integrations/ibm_architecture/models/baseline.py`)
- **Estimator:** `HistGradientBoostingClassifier(max_iter=60, random_state=11, class_weight="balanced", early_stopping=False)`
- **Role:** Independent benchmark reference for comparing single-model vs. ensemble predictive power.

### 3.2 5-Member Era-Bagged Heterogeneous Ensemble
- **Class:** `EraBaggedHeterogeneousEnsemble` (`integrations/ibm_architecture/models/ensemble.py`)
- **Strategy:** Chronological era omission. The 354,324 training rows are segmented into 5 temporal eras $[E_0, E_1, E_2, E_3, E_4]$ of ~70,865 rows each. Each ensemble member omits one chronological era during fitting, ensuring diversity across macroeconomic and seasonal shifts.

| Member ID | Algorithm Family | Architecture / Hyperparameters | Omitted Era | Seed | Concurrency |
|---|---|---|:---:|:---:|:---:|
| `era0_omit_hgbc_s11` | Histogram Gradient Boosting | `HistGradientBoostingClassifier(max_iter=60, class_weight='balanced')` | $E_0$ (0–20%) | 11 | Multi-thread OpenMP |
| `era1_omit_hgbc_s22` | Histogram Gradient Boosting | `HistGradientBoostingClassifier(max_iter=60, class_weight='balanced')` | $E_1$ (20–40%) | 22 | Multi-thread OpenMP |
| `era2_omit_et_s11` | Extremely Randomized Trees | `ExtraTreesClassifier(n_estimators=100, class_weight='balanced', n_jobs=1)` | $E_2$ (40–60%) | 11 | Sequential (`n_jobs=1`) |
| `era3_omit_lr_s11` | Regularized Logistic Regression | `Pipeline([Imputer, StandardScaler, LogisticRegression(C=0.1, solver='lbfgs', max_iter=2000)])` | $E_3$ (60–80%) | 11 | Single-thread L-BFGS |
| `era4_omit_hgbc_s33` | Histogram Gradient Boosting | `HistGradientBoostingClassifier(max_iter=60, class_weight='balanced')` | $E_4$ (80–100%) | 33 | Multi-thread OpenMP |

### 3.3 Consensus Aggregation
The ensemble consensus risk score $\bar{p}$ is the unweighted arithmetic mean of positive class probabilities across all 5 active members:
$$\bar{p} = \frac{1}{M} \sum_{m=1}^{M} p_m \quad \text{where } M = 5$$

---

## 4. Probability Calibration & Diagnostic Evaluation

### 4.1 Platt Scaling vs. Isotonic Regression
- **Platt Scaling (`PlattCalibrator`):** Univariate logistic regression ($C=1.0$) mapping uncalibrated consensus probabilities $\bar{p}$ to well-calibrated posterior probabilities $P(Y=1 \mid \bar{p})$:
  $$P(Y=1 \mid \bar{p}) = \frac{1}{1 + \exp(A \cdot \bar{p} + B)}$$
  Platt scaling avoids over-fitting small validation cohorts and preserves monotonicity across the probability spectrum.
- **Partition Isolation:** The calibrator enforces partition governance via `validate_calibration_partition()`. Fitting on `validation`, `test`, or `holdout` raises `ValueError`.

### 4.2 Diagnostic Expected Calibration Error (ECE)
Diagnostic calibration quality is quantified via 10-bin Expected Calibration Error:
$$\text{ECE} = \sum_{b=1}^{B} \frac{|B_b|}{N} \left| \text{acc}(B_b) - \text{conf}(B_b) \right|$$

---

## 5. Epistemic Disagreement & Uncertainty Signals

The system computes disagreement signals without inspecting ground-truth labels:

1. **Standard Disagreement ($u$):** Population standard deviation across member probabilities:
   $$u = \sqrt{\frac{1}{M} \sum_{m=1}^{M} (p_m - \bar{p})^2}$$
2. **Robust Disagreement ($u_2$):** Median absolute deviation (MAD) from the median member prediction:
   $$\text{med}(p) = \text{median}(\{p_1, \dots, p_M\}), \quad u_2 = \frac{1}{M} \sum_{m=1}^{M} |p_m - \text{med}(p)|$$
3. **Signal Properties:**
   - Perfect agreement ($p_1 = \dots = p_5$): $u = 0.0$, $u_2 = 0.0$.
   - High model divergence: $u > 0.10$, indicating epistemic uncertainty, out-of-distribution drift, or novel fraud patterns.
   - Values $< 10^{-12}$ are clamped to $0.0$ for numerical hygiene.

---

## 6. Artifact Bundle & Cryptographic Provenance

All model artifacts are stored under `models/artifacts/ieee_cis_v1/`:

| Artifact | File | SHA-256 Validated | Description |
|---|---|:---:|---|
| Feature Pipeline | `feature_pipeline.joblib` | Yes | Fitted imputers and categorical encoders |
| Baseline B2 | `baseline_b2.joblib` | Yes | Fitted `HistGradientBoostingClassifier` |
| 5-Member Ensemble | `ensemble.joblib` | Yes | Fitted `EraBaggedHeterogeneousEnsemble` |
| Platt Calibrator | `calibrator.joblib` | Yes | Fitted sigmoid calibrator |
| Manifest | `model_bundle_manifest.json` | Yes | Provenance, split hashes, metrics, and checksums |

### 6.1 Cryptographic Integrity Verification
On `load_bundle()`, every artifact file is re-hashed using streaming SHA-256 and matched against `manifest.artifact_hashes`. If any byte is altered, `load_bundle()` immediately raises `IncompatibleArtifactError` and aborts.

---

## 7. Resource Analysis & Concurrency Gate

| Metric | Parallel Benchmark (`n_jobs=-1`) | Sequential Configuration (`n_jobs=1`) | Safety Margin |
|---|:---:|:---:|:---:|
| Peak RAM Estimate | 8.0–10.5 GB | 2.8–3.5 GB | Baseline |
| Minimum Available RAM Gate | 12.0 GB | 6.0 GB | +2.5 GB buffer above peak |
| Host Available Physical RAM | 10.44 GB | 10.44 GB | Passed (+4.44 GB headroom) |
| ExtraTrees Process Concurrency | Multi-process worker pool | `n_jobs=1` single thread | Eliminates memory duplication |
| Garbage Collection | Deferred / System Default | Forced `gc.collect()` after each fit | Intermediate slices freed immediately |

---

## 8. Requirements Compliance Matrix

| Requirement | Description | Implementation Status | Evidence / Verification |
|---|---|:---:|---|
| **MODL-01** | Full IEEE-CIS Chronological Training (590,540 rows) | **PASS** | Evaluated on full dataset without subsampling; 60/10/10/20 chronological split hashes verified. |
| **MODL-02** | Target Quarantine & Partition Fitting Isolation | **PASS** | `isFraud`, `TransactionID`, `TransactionDT` quarantined; estimators fit on train, calibrator fits on calib. |
| **MODL-03** | Sequential Memory-Controlled Ensemble with `n_jobs=1` | **PASS** | ExtraTrees configured with `n_jobs=1`; dynamic $\ge 6.0\text{ GB}$ RAM floor checked before every stage. |
| **TEST-01** | Unit & API Regression Suite Pass Rate | **PASS** | 144 / 144 tests passing (100%), including 8 dedicated model lifecycle tests. |
| **SAFE-01** | Fail-Closed Missing Raw CSV Handling | **PASS** | Missing CSV files immediately raise `ArtifactNotFoundError` with zero synthetic fallback. |
