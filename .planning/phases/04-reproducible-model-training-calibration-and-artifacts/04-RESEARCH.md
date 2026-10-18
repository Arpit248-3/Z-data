# Phase 4: Reproducible Model Training, Calibration and Artifacts — Research & Technical Specifications

**Phase:** `04-reproducible-model-training-calibration-and-artifacts`  
**Date:** 2026-10-18  
**Governing Specification:** `docs/ibm_architecture_integration_master_spec.md` § C, § H  
**Requirements Covered:** `MODL-01`, `MODL-02`, `MODL-03`  

---

## 1. Architectural Objectives & Invariants

The objective of Phase 4 is to design, implement, and verify the model training pipeline, era-bagged heterogeneous ensemble, Platt sigmoid calibrator, disagreement signal extractors ($u, u_2$), and model artifact serialization for the IEEE-CIS Fraud Detection architecture within the isolated integration namespace.

In strict compliance with the governing specification:
1. **Isolated Namespace (`MODL-01`):** All model definitions, ensemble estimators, calibrators, signal extractors, and training orchestration code must reside in `integrations/ibm_architecture/models/`. All persisted model bundles, metadata, and serialization artifacts must live in `models/artifacts/ieee_cis_v1/`. The root canonical synthetic models (`models/calibrated_model.joblib`, `models/hist_gradient_boosting.joblib`, etc.) and active registries remain completely untouched.
2. **Ground-Truth Quarantine Barrier (`MODL-01`, Master Spec § C2):**
   - The evaluation target `isFraud` must never enter the feature preprocessing pipeline, model feature matrices, or inference vectors.
   - Raw transaction identifiers (`TransactionID`) and timestamps (`TransactionDT`) are strictly excluded from feature extraction and model inputs.
   - `FeaturePipeline` and `ModelBundle` pre-validators must raise `LeakageViolationError` if any quarantined column is detected.
3. **Partition Governance & Separation of Concerns (`MODL-02`, Master Spec § H):**
   - **Training Partition ($[0.0, 0.60]$):** Used strictly for fitting `FeaturePipeline`, base estimator B2, and the 5 era-omitted ensemble members.
   - **Calibration Partition ($[0.60, 0.70]$):** Used strictly for fitting `PlattCalibrator` (sigmoid logistic regression) and `IsotonicCalibrator`.
   - **Validation Partition ($[0.70, 0.80]$):** Used strictly for diagnostic evaluation (e.g., ECE calculation, reliability curves, drift calibration). Fitting estimators or calibrators on validation data is strictly prohibited and raises `ValueError`.
   - **Test Partition ($[0.80, 1.00]$):** Immutable holdout partition; strictly quarantined from any model fitting, hyperparameter selection, or threshold tuning.
4. **Disagreement Signal Extraction (`MODL-03`, Master Spec § D, § H):**
   - Disagreement signals are computed directly from the ensemble's per-member prediction matrix:
     * $u$: Population standard deviation across member probabilities ($\text{std}(p_1, \dots, p_M, \text{ddof}=0)$).
     * $u_2$: Mean absolute deviation from the median probability ($\frac{1}{M}\sum_{m=1}^M |p_m - \text{median}(p)|$).
   - Returns structured `DisagreementSignals(p, u, u2, n)` without requiring or accessing ground-truth labels.
5. **Honest Fail-Closed Handling for Missing Raw Data (Master Spec § C1, § H):**
   - Real IEEE-CIS CSVs (`train_transaction.csv`, `train_identity.csv`) are currently absent from `data/raw/` (as audited in Phase 3).
   - Under no circumstances will synthetic records be substituted, nor will false claims of full 590k-sample training or benchmark success be made.
   - Orchestration scripts for full dataset training fail closed with `ArtifactNotFoundError` when raw CSVs are missing.
   - Small, explicitly labeled mock fixtures are used exclusively for unit testing pipeline transformations, model convergence, calibration curves, and signal calculations.
6. **Memory Governance (Windows 11 AMD64, 8 GB RAM):**
   - Preprocessing transforms features to `float32` arrays.
   - Ensemble members use bounded tree depths/iterations (`max_iter=60` for `HistGradientBoostingClassifier`, `n_estimators=100` for `ExtraTreesClassifier`).
   - Intermediate arrays and memory are aggressively cleaned via `gc.collect()`.

---

## 2. Estimator & Ensemble Architecture

### 2.1 Baseline Model B2
The reference baseline B2 is a standalone single-model gradient boosted classifier:
- Algorithm: `HistGradientBoostingClassifier`
- Hyperparameters: `max_iter=60`, `random_state=11`, `class_weight='balanced'`, `early_stopping=False`
- Purpose: Establishes the competitive single-model benchmark against which the ensemble and candidate policies are evaluated.

### 2.2 Era-Bagged Heterogeneous Ensemble (`EraBaggedHeterogeneousEnsemble`)
To enhance shift robustness without data leakage, the ensemble divides the training partition into 5 chronological eras and trains 5 heterogeneous members, each omitting one era:

| Member ID | Algorithm | Omitted Era | Random Seed | Configuration |
|---|---|:---:|:---:|---|
| `era0_omit_hgbc_s11` | `HistGradientBoostingClassifier` | Era 0 ($[0\%, 20\%]$) | 11 | `max_iter=60, class_weight='balanced', early_stopping=False` |
| `era1_omit_hgbc_s22` | `HistGradientBoostingClassifier` | Era 1 ($[20\%, 40\%]$) | 22 | `max_iter=60, class_weight='balanced', early_stopping=False` |
| `era2_omit_et_s11` | `ExtraTreesClassifier` | Era 2 ($[40\%, 60\%]$) | 11 | `n_estimators=100, class_weight='balanced', n_jobs=-1` |
| `era3_omit_lr_s11` | `Pipeline[SimpleImputer, StandardScaler, LogisticRegression]` | Era 3 ($[60\%, 80\%]$) | 11 | `solver='lbfgs', max_iter=2000, C=0.1, class_weight='balanced'` |
| `era4_omit_hgbc_s33` | `HistGradientBoostingClassifier` | Era 4 ($[80\%, 100\%]$) | 33 | `max_iter=60, class_weight='balanced', early_stopping=False` |

**Prediction Mechanism:**
1. Member probabilities: Each estimator produces predicted probability for the positive class ($p_{m} = P(Y=1|X)$), forming matrix $P \in \mathbb{R}^{N \times 5}$.
2. Ensemble consensus probability: Arithmetic mean across active members:
   $$\bar{p} = \frac{1}{M}\sum_{m=1}^M p_m$$
3. Structured output: Wrapped in `MemberPredictions(proba_matrix=P, member_ids=[...])`.

---

## 3. Learned Feature Preprocessing (`FeaturePipeline`)

### 3.1 Schema & Imputation
- Categorical columns (14): `ProductCD`, `card4`, `card6`, `P_emaildomain`, `R_emaildomain`, `M1`–`M9`.
  - Processed using `OrdinalEncoder(handle_unknown="use_encoded_value", unknown_value=-1, encoded_missing_value=-1)`.
- Numerical columns (377): `TransactionAmt`, `card1`–`card3`, `card5`, `addr1`–`addr2`, `dist1`–`dist2`, `C1`–`C14`, `D1`–`D15`, `V1`–`V339`.
  - Processed using `SimpleImputer(strategy="median")`.
- Total input features: Exactly 391 features matching `CANONICAL_FEATURE_MANIFEST`.

### 3.2 Quarantine & Fitting Rules
- Fitted strictly on the training partition ($N_{\text{train}}$ rows).
- Input verification: Rejects `isFraud`, `TransactionID`, `TransactionDT` with `LeakageViolationError`.
- Output: Contiguous `float32` matrix $X \in \mathbb{R}^{N \times 391}$.

---

## 4. Calibration Architecture (`PlattCalibrator`)

### 4.1 Platt / Sigmoid Scaling
- Receives uncalibrated ensemble probabilities $\bar{p}_{\text{cal}}$ computed on the **calibration partition**.
- Fits univariate logistic regression:
  $$\ln\left(\frac{P(Y=1|\bar{p})}{1 - P(Y=1|\bar{p})}\right) = A \cdot \bar{p} + B$$
  using `LogisticRegression(solver="lbfgs", max_iter=1000, C=1.0)`.
- Output: Calibrated risk probability $p_{\text{calibrated}} \in [0, 1]$.

### 4.2 Isotonic Regression Alternative
- Non-parametric isotonic regression (`IsotonicRegression(out_of_bounds="clip")`) as a secondary calibrator.

### 4.3 Diagnostic ECE Calculation
- `calibration_ece(scores, labels, n_bins=10)` computes Expected Calibration Error:
  $$\text{ECE} = \sum_{b=1}^B \frac{|B_b|}{N} |\text{acc}(B_b) - \text{conf}(B_b)|$$
- Strictly diagnostic; never used to tune or select models.

---

## 5. Disagreement Signal Calculator (`signals.py`)

### 5.1 Signal Definitions
From per-member probability matrix $P \in \mathbb{R}^{N \times M}$:
1. **$u$ (Standard Deviation Spread):**
   $$u = \sqrt{\frac{1}{M} \sum_{m=1}^M (p_m - \bar{p})^2}$$
   Measures epistemic and aleatoric spread across ensemble architectures.
2. **$u_2$ (Median Absolute Deviation):**
   $$\tilde{p} = \text{median}(p_1, \dots, p_M), \quad u_2 = \frac{1}{M}\sum_{m=1}^M |p_m - \tilde{p}|$$
   Robust dispersion metric resilient to single-member outlier predictions.
3. **$n$ (Member Count):**
   Float count of active ensemble members ($M=5$).

### 5.2 Interface & Contracts
- Single-case calculation: `DisagreementSignals(p, u, u2, n)`
- Batch calculation: `compute_signals(mp: MemberPredictions) -> np.ndarray` (structured array with dtype `[('p', float64), ('u', float64), ('u2', float64), ('n', float64)]`).
- Exposed to agents strictly through sanitized `AgentCaseView(p=..., u=..., u2=..., n=...)`.

---

## 6. Serialization & Model Artifact Bundle

All Phase 4 artifacts are saved to `models/artifacts/ieee_cis_v1/`:
1. `feature_pipeline.joblib`: Fitted `FeaturePipeline` instance.
2. `baseline_b2.joblib`: Fitted baseline `HistGradientBoostingClassifier`.
3. `ensemble.joblib`: Fitted `EraBaggedHeterogeneousEnsemble`.
4. `calibrator.joblib`: Fitted `PlattCalibrator`.
5. `model_bundle_manifest.json`: Complete cryptographic manifest containing:
   - Model versions, seeds, and hyperparameters.
   - Input feature manifest SHA-256 fingerprint.
   - Partitions used for training and calibration.
   - Validation ECE score and diagnostic reliability metrics.
   - Operational mode readiness (`TRAINING_PIPELINE_VERIFIED_RAW_DATA_ABSENT`).

---

## 7. Package Layout in `integrations/ibm_architecture/models/`

```text
integrations/ibm_architecture/models/
├── __init__.py           # Exports FeaturePipeline, BaselineB2, EraBaggedHeterogeneousEnsemble, PlattCalibrator, compute_signals
├── features.py           # FeaturePipeline with median imputation, ordinal encoding, and quarantine
├── baseline.py           # B2 HistGradientBoosting baseline estimator
├── ensemble.py           # EraBaggedHeterogeneousEnsemble and MemberPredictions
├── calibration.py        # PlattCalibrator, IsotonicCalibrator, and calibration_ece
├── signals.py            # DisagreementSignalExtractor, RobustDisagreementSignalExtractor, compute_signals
├── bundle.py             # ModelBundle, ModelBundleManifest, save_bundle, load_bundle
└── trainer.py            # Training pipeline orchestrator with fail-closed missing data handling
```

---

## 8. Verification Strategy

1. **Unit Tests (`tests/test_ibm_models.py`):**
   - Feature pipeline fits strictly on training data without leakage.
   - Preprocessing raises `LeakageViolationError` if `isFraud`, `TransactionID`, or `TransactionDT` are passed.
   - Baseline B2 fits, converges, and produces valid deterministic probabilities in $[0, 1]$.
   - Era-bagged ensemble divides training data into 5 eras, omits corresponding eras, and computes per-member and consensus probabilities.
   - Platt calibrator learns monotonic mapping on calibration scores and returns calibrated probabilities in $[0, 1]$.
   - Prohibits fitting calibrator on validation or test partitions (`ValueError`).
   - Disagreement signals $u$ and $u_2$ are non-negative scalars and match expected mathematical definitions.
   - `ModelBundle` serializes and deserializes cleanly with matching predictions and SHA-256 hashes.
   - Training pipeline fails closed with `ArtifactNotFoundError` when raw CSVs are missing from `data/raw/`.
2. **Regression Suites:**
   - 135 backend pytest tests continue to pass with zero regressions.
   - 21 frontend Vitest tests continue to pass.
