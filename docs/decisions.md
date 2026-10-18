# SignalGate Architectural & Implementation Decisions

## Phase 1 Decisions Log

---

### Decision 1: Dataset Fallback & Deterministic Synthetic Development Fixture
- **Context:** The IEEE-CIS Fraud Detection dataset (`train_transaction.csv`, ~590K rows) was searched across the filesystem (`Desktop` and `Downloads`) and confirmed absent. Automated Kaggle download was not configured.
- **Decision:** Rather than blocking development on Kaggle credentials or network downloads, implement `data/generate_fixture.py` to create a deterministic 10,000-row synthetic fixture (`data/synthetic_smoke_fixture.csv`) matching the IEEE-CIS schema.
- **Enforcement:**
  - Status is stamped `SYNTHETIC_SMOKE_ONLY`.
  - Synthetic metrics are strictly prohibited from being presented as benchmark claims.
  - The fixture is generated with declared seed `42` producing reproducible SHA-256 hash `da00179ebf37970ec8907d11cfb366d170ddd5b2b41370e881bf92359b7d17de`.
  - The data loader and schema definitions are built to seamlessly accept the genuine IEEE-CIS `train_transaction.csv` whenever it is provided.

---

### Decision 2: Git Safety and Repository Scope Containment
- **Context:** The parent folder `C:\Users\arpit\Desktop` had an active Git repository tracking hundreds of unrelated files, executables, and desktop shortcuts.
- **Decision:** Initialized a scoped, independent Git repository inside `c:\Users\arpit\Desktop\project\.git`.
- **Enforcement:**
  - Verified `git rev-parse --show-toplevel` resolves to `C:/Users/arpit/Desktop/project`.
  - Added a project `.gitignore` covering Python bytecode, caches, virtual environments, and node modules.
  - Under no circumstances will git commands stage, modify, or commit files outside the `project/` directory.

---

### Decision 3: Pre-Registered Configuration & Reproducibility
- **Context:** Blueprint Section 8.3 requires explicit pre-registration of operational budgets and random seeds before model training or evaluation to avoid p-hacking and post-hoc threshold selection.
- **Decision:** Authored `config.yaml` specifying:
  - Primary touched-rate budget multiple: `1.5` × training-set fraud prevalence.
  - Budget sweep: `[1.0, 1.5, 2.0, 3.0]`.
  - Declared seeds: `[11, 22, 33, 44, 55]`.
  - Split allocations: Train 60%, Calibration 10%, Validation 10%, Test 20%.
  - Optional features disabled by default (`velocity: false`, `v_pruning: false`, `explanations: false`).
- **Enforcement:** No evaluation or tuning against final-test labels occurs in Phase 1.

---

### Decision 4: Missing-Artifact Representation Semantics
- **Context:** Blueprint and Playbook rules forbid substituting missing measurements with invented numbers (e.g. `0.0` or fake ready states).
- **Decision:** All unavailable measurements, models, or hardware features are represented explicitly as `null` accompanied by an explicit status string.
- **Enforcement:**
  - `logs/environment.txt` records:
    - Real IEEE-CIS Dataset: `null [STATUS: PENDING_USER_SUPPLY]`
    - IBM Snap ML Engine: `null [STATUS: NOT_APPLICABLE_ON_X86]`
    - Trained Policy Router: `null [STATUS: PHASE_4_SCHEDULED]`
    - Results JSON Artifact: `null [STATUS: PHASE_5_SCHEDULED]`

---

### Decision 5: Scikit-learn 1.8 Calibration Path
- **Context:** In scikit-learn 1.8.0, passing `cv="prefit"` to `CalibratedClassifierCV` is no longer supported and raises an `InvalidParameterError`.
- **Decision:** Probed and verified the recommended scikit-learn 1.8 architecture:
  ```python
  from sklearn.frozen import FrozenEstimator
  from sklearn.calibration import CalibratedClassifierCV

  frozen_base = FrozenEstimator(fitted_base_estimator)
  calibrator = CalibratedClassifierCV(estimator=frozen_base, method="sigmoid")
  calibrator.fit(X_calib, y_calib)
  ```
- **Result:** Successfully calibrated with verified probabilities in `[0, 1]` and improved Brier score on held-out synthetic test rows.

---

### Decision 6: Hardware and Acceleration Target Grounding
- **Context:** The workspace is running on an x86_64 Windows 11 host (Intel Core i3-1115G4, 2 cores / 4 threads, 8.0 GB RAM), not an IBM LinuxONE s390x mainframe.
- **Decision:** IBM Snap ML and mainframe accelerator benchmarks are marked not applicable for this local environment. All Phase 1 baselines execute purely against supported scikit-learn modules.

---

## Phase 2 Decisions Log

---

### Decision 7: Strict Chronological Partitioning & Tie-Breaking Policy
- **Context:** Blueprint Section 5.3 requires 60/10/10/20 train/calibration/validation/test chronological splits ordered by `TransactionDT`. In transaction streams, duplicate timestamps can occur at partition boundaries.
- **Decision:** Implemented `data/splits.py` with the following policy:
  - Primary ordering: `TransactionDT` ascending.
  - Secondary tie-breaking: `TransactionID` ascending (or original stable row index if ID is absent).
  - Boundary cut-points: Exact row fractions (60% train, 10% calib, 10% val, 20% test).
  - Enforcement: Partitions are strictly disjoint (`train_ids.isdisjoint(calib_ids)`, etc.), timestamps never decrease across partition boundaries, and every split produces a deterministic `split_hash`.
  - Report: Generates `results/split_report.json` labelled `SYNTHETIC_SMOKE_ONLY` when evaluated on synthetic data.

---

### Decision 8: Feature Matrix Isolation and Segment Column Segregation
- **Context:** Blueprint Section 5.2 and Playbook Prompt 2 mandate that `TransactionID`, raw `TransactionDT`, `isFraud`, and segment fields must never accidentally leak into the model feature matrix $X$.
- **Decision:** Implemented `data/features.py`:
  - `FORBIDDEN_MODEL_COLUMNS` (`TransactionID`, `TransactionDT`, `isFraud`, `true_label`, `split`, `partition`) are permanently blocked from $X$.
  - Segment columns (`ProductCD`, `card4`) are isolated into a separate evaluation structure `eval_df` for post-hoc reporting and never enter $X$ by default.
  - Target vector $y$ is extracted and returned separately from $X$.
  - A frozen feature column manifest is generated from the training split and enforced identically across calibration, validation, and test splits.

---

### Decision 9: Numeric Sanitization and Infinite Values Policy
- **Context:** Transaction features may contain infinite values or high-precision 64-bit floats that increase memory pressure on limited-RAM hardware.
- **Decision:**
  - Infinite values ($+\infty, -\infty$) are mapped to `np.nan`, matching HistGradientBoosting's native missingness handling without requiring ad-hoc imputation.
  - `float64` features are safely downcasted to `float32` after verifying values lie within `np.finfo(np.float32)` bounds.

---

### Decision 10: Strict Dataset Integrity & No Silent Fallback
- **Context:** If a corrupted, malformed, or incomplete genuine IEEE-CIS `data/train_transaction.csv` is present, the pipeline must not silently mask the error by falling back to synthetic data.
- **Decision:** `data/load.py` validates all datasets against the schema. If an invalid genuine dataset is detected, it raises an explicit `ValueError` detailing the schema violations. Synthetic data is loaded only when no genuine dataset exists, and is always explicitly flagged as `SYNTHETIC_SMOKE_ONLY`.

---

## Phase 3 Decisions Log

---

### Decision 11: Base Model Architecture & Baseline Pairing
- **Context:** Blueprint Section 3.1 and Playbook Prompt 3 require a primary gradient boosting candidate and a linear sanity baseline fitted strictly on the training partition.
- **Decision:** Implemented in `models/base.py`:
  - Primary: `HistGradientBoostingClassifier(random_state=11, max_iter=50, early_stopping=False)` (handles NaNs natively; `early_stopping=False` prevents random validation splitting that would violate temporal ordering).
  - Baseline: `Pipeline([SimpleImputer(strategy='median'), StandardScaler(), LogisticRegression(random_state=11, max_iter=100)])` (imputer and scaler fitted strictly on train).
  - Both consume the frozen training feature manifest ($81$ features).
  - Artifacts saved: `models/artifacts/hgb_base.joblib` and `models/artifacts/logistic_base.joblib` with SHA-256 manifests.

---

### Decision 12: Probability Calibration Selection Policy
- **Context:** Raw boosting scores can be overconfident or poorly calibrated. Blueprint Section 5.3 requires calibration to be fitted on the calibration split ($10\%$) and evaluated strictly on the validation split ($10\%$).
- **Decision:** Implemented in `models/calibrate.py`:
  - Evaluated `uncalibrated`, `sigmoid` (Platt scaling), and `isotonic` calibration using `sklearn.frozen.FrozenEstimator` with `CalibratedClassifierCV`.
  - Diagnostics: Validation Brier score and Expected Calibration Error (ECE) across 10 equal-width bins.
  - Outcome on validation:
    - Uncalibrated: Brier = `0.046496`, ECE = `0.027248`, ROC-AUC = `0.583574`
    - Sigmoid: Brier = `0.045650`, ECE = `0.007729`, ROC-AUC = `0.583574`
    - Isotonic: Brier = `0.045734`, ECE = `0.007422`, ROC-AUC = `0.583924`
  - Selection: Selected `sigmoid` calibration based on minimizing validation Brier score.
  - Monotonicity note: Observed that monotonic calibration preserved ROC-AUC exactly ($0.583574$) while reducing calibration error (ECE) by $71.6\%$.

---

### Decision 13: 3-Member Disagreement Ensemble & Rank-Residual $u2$
- **Context:** Blueprint Sections 3.2 and 10.3 specify an ensemble of three models with varied seeds and configurations to emit epistemic disagreement $u = \text{std}(p_1, p_2, p_3)$. If $\text{corr}(p, u)$ is high, a rank-residual variant $u2$ must be investigated to isolate orthogonal disagreement.
- **Decision:** Implemented in `models/ensemble.py`:
  - 3 members fitted on train with seeds `[11, 22, 33]` and varying tree regularization (`max_leaf_nodes` $31, 20, 40$; L2 regularization $0.0, 1.0, 0.1$).
  - Observed raw validation Spearman correlation $\rho(p, raw\_u) = 0.4510$.
  - Implemented `RankResidualizer` fitted strictly on calibration: mapping fractional rank $r_p \to r_u$ via degree-3 polynomial ridge regression. Evaluates against frozen calibration empirical CDF references (preventing test distribution leakage).
  - Outcome on validation: $\rho(p, u2) = 0.0609$ (decorrelation of $0.3901$, an $86.5\%$ reduction in redundancy).
  - Frozen `residualizer_u2.joblib` saved to `models/artifacts/` prior to any test look.

---

### Decision 14: Test Partition Isolation
- **Context:** Final test partition ($20\%$, $2,000$ rows) must not be inspected or used to tune models, calibrators, or ensembles.
- **Decision:** All Phase 3 fittings, calibration comparisons, and ensemble diagnostics operated strictly on Train ($60\%$), Calibration ($10\%$), and Validation ($10\%$). Test partition labels and rows were 100% untouched.

---

## Phase 4 Decisions Log

---

### Decision 15: Decision Router Precedence and Fail-Closed Security Policy
- **Context:** Blueprint Section 7.1 and 7.2 specify the multi-action triage taxonomy and explicit safety guarantees: high risk must never be classified as routine, missing/invalid signals must fail closed, and reason codes must follow deterministic precedence.
- **Decision:** Implemented in `policy/router.py`:
  - **Precedence Hierarchy:**
    1. **Input & Policy Validation:** Validate $p, u, n$ ranges, finite bounds, and valid threshold relationships ($t_{\text{review}} < t_{\text{alert}}$).
    2. **Fail-Closed Availability ($R_0$):** Missing or non-finite required signals route to `MANUAL_REVIEW` with `R0_SIGNAL_UNAVAILABLE`. An intentionally skipped stage-two inference (`stage2_status="skipped"`) is distinguished from an unavailable or failed inference.
    3. **High-Risk Threshold ($R_1$):** If $p \ge t_{\text{alert}}$, produce `FRAUD_ALERT` with `R1_HIGH_RISK`. A high-risk score is strictly prohibited from routing to `ROUTINE`.
    4. **Intermediate-Risk Threshold ($R_2$):** If $p \ge t_{\text{review}}$, produce `MANUAL_REVIEW` with `R2_INTERMEDIATE_RISK`.
    5. **Epistemic Disagreement ($R_3$):** If disagreement is enabled and $u \ge u_{\text{threshold}}$, produce `MANUAL_REVIEW` with `R3_MODEL_DISAGREEMENT`. Excessive disagreement triggers human inspection but is never an automatic assertion of fraud.
    6. **Novelty / Unfamiliarity ($R_4$):** When novelty detection is enabled and $n \ge n_{\text{threshold}}$, produce `MANUAL_REVIEW` with `R4_UNFAMILIAR_INPUT`. When disabled, novelty rules remain completely inactive.
    7. **Low-Risk Routine ($R_5$):** All remaining transactions meeting reliability criteria route to `ROUTINE` with `R5_LOW_RISK_RELIABLE`.
  - **Leakage Prevention:** `route_batch()` actively rejects DataFrames containing `true_label` or `isFraud` columns, ensuring ground-truth labels can never influence triage decisions.

---

### Decision 16: Validation-Only Threshold Selection & Pre-Registered Sweep
- **Context:** Blueprint Section 8.3 requires thresholds ($t_{\text{review}}, t_{\text{alert}}, u_{\text{threshold}}$) to be selected strictly on validation data to prevent post-hoc overfitting and p-hacking.
- **Decision:** Implemented in `policy/thresholds.py`:
  - Primary touched-rate budget: $1.5 \times$ training prevalence ($0.0435 \times 1.5 = 0.06525$).
  - Pre-registered budget sweep: $1.0\times, 1.5\times, 2.0\times, 3.0\times$.
  - Objective: Maximize validation recall subject to $\text{touched\_rate} \le \text{budget}$ and $0 \le t_{\text{review}} < t_{\text{alert}} \le 1$.
  - Deterministic tie-breaking: Highest budget utilization, then lowest $t_{\text{review}}$, then highest $t_{\text{alert}}$.
  - Selected primary configuration: $t_{\text{alert}} = 0.084705, t_{\text{review}} = 0.071002, u_{\text{threshold}} = 0.526773$.
  - The configuration was frozen into `policy/frozen_policy.json` (SHA-256: `8d3f02ca492ca94bab45f3ceac8d39432c2f29f40d54e7990b4aa78cbbff6240`) before any test access.

---

### Decision 17: Mandatory Baselines (B1, B2, B3a, B4) Under Matched Budgets
- **Context:** Fair policy comparison requires identical rows, identical evaluation partitions, and budget matching against declared capacity constraints.
- **Decision:** Implemented in `policy/baselines.py`:
  - **B1 (Fixed Threshold):** Threshold selected on validation split to achieve touched rate $\approx 0.065$.
  - **B2 (Top-B Risk Ranking):** Mandatory comparison baseline. Ranks transactions by calibrated risk score $p$ and escalates the top fraction matching declared capacity $\lfloor N \times B \rfloor$. Uses deterministic tie-breaking on row index.
  - **B3a (Confidence Deferral):** Evaluates uncertainty as $1 - \max(p, 1-p)$, escalating transactions where the model is most ambiguous around $0.5$.
  - **B4 (Random Control):** Reproducible pseudorandom escalation matching the exact budget using declared seed `42`.
  - All policies evaluate on the identical set of transactions with identical capacity cutoffs.

---

### Decision 18: Capacity Governor & Deferred Escalation Policy
- **Context:** Operational fraud triage teams face fixed analyst queue limits. When incoming candidate escalations exceed capacity, excess cases cannot simply vanish or silently revert to `ROUTINE`.
- **Decision:** Implemented `CapacityGovernor` in `policy/governor.py`:
  - Candidate escalations are ranked by validated priority score $p$ (with stable row-index secondary tie-breaking).
  - Top candidates within capacity are admitted as `FRAUD_ALERT` or `MANUAL_REVIEW`.
  - Overflow candidates beyond capacity are classified as `DEFERRED` / `HELD` with reason code `R6_CAPACITY_DEFERRED`.
  - Exact touched-rate metric definition: $\text{touched\_rate} = (\text{ALERT} + \text{REVIEW}) / N$. Deferred cases are tracked and reported separately, preventing artificial deflation of queue load.

---

### Decision 19: Keep/Drop Discipline for Disagreement Signals ($u$ vs $u2$)
- **Context:** Raw ensemble disagreement $u = \text{std}(p_1, p_2, p_3)$ had a $0.4510$ Spearman correlation with risk score $p$. The rank-residualized signal $u2$ reduced this correlation to $0.0609$ ($86.5\%$ decorrelation).
- **Decision:** Compared on the synthetic validation partition under the primary $1.5\times$ budget ($65$ analyst capacity out of $1,000$ transactions):
  - Risk Only: Recall $= 0.0625$ ($3$ of $48$ frauds caught).
  - Risk + $u2$: Recall $= 0.0833$ ($4$ of $48$ frauds caught, $+2.08\text{ pp}$ recall delta).
  - Because $u2$ demonstrated orthogonal informative value and improved recall under the matched budget constraint, it was retained and enabled in the frozen policy configuration.

---

### Decision 20: Pre-Registered G3 Test Look Execution and Synthetic Status Integrity
- **Context:** Blueprint Gate G3 requires a single pre-registered test look on the held-out test split ($2,000$ rows) to verify pipeline execution before frontend development.
- **Decision:**
  - Frozen configuration SHA-256 (`8d3f02ca492ca94bab45f3ceac8d39432c2f29f40d54e7990b4aa78cbbff6240`) was logged to `logs/test_looks.log` prior to evaluation.
  - G3 test look executed once: Test B2 Recall $= 0.0901$ ($10$ of $111$ frauds caught); SignalGate Candidate Recall $= 0.0901$ ($10$ of $111$ frauds caught).
  - Under no circumstances will thresholds, models, or features be retuned in response to this test look.
  - All test artifacts and logs explicitly preserve `SYNTHETIC_SMOKE_ONLY` to prevent synthetic development numbers from being cited as benchmark claims.

---

## Phase 5 Decisions Log

---

### Decision 21: Full Evaluation Matrix & Touched-Rate Accounting Discipline
- **Context:** Blueprint Section 6.3 mandates clear separation between operational multi-action triage and binary contingency evaluations, avoiding artificial inflation of review performance.
- **Decision:** Implemented in `eval/metrics.py`:
  - `touched_rate = (count(FRAUD_ALERT) + count(MANUAL_REVIEW)) / total_transactions`.
  - Queue overflow (`DEFERRED` / `HELD`) is reported strictly as deferred volume (`deferred_rate`) and is never silently counted as reviewed or routine.
  - Confident-miss count and routine fraud rate explicitly track actual fraud leaked into `ROUTINE`.
  - Transaction-amount weighted metrics (`amount_fraud_caught`, `amount_fraud_missed`, `amount_caught_pct`) quantify financial volume without assuming guaranteed recovery.

---

### Decision 22: Paired Bootstrap Resampling Protocol & Inconclusiveness Discipline
- **Context:** Blueprint Section 6.4 requires paired bootstrap comparisons on identical test rows to compute 95% confidence intervals for policy recall differences ($\Delta = \text{Recall}_{\text{SignalGate}} - \text{Recall}_{B2}$) under matched workload budgets.
- **Decision:** Implemented in `eval/bootstrap.py`:
  - 1,000 paired resamples using fixed seed `42` resample the same row indices simultaneously across both policies.
  - Degenerate resamples (0 positive fraud labels) are filtered with tracked valid counts.
  - Inconclusiveness Rule: If the 95% empirical percentile interval spans zero, the policy difference is explicitly labeled **inconclusive**. Point estimate positivity is never cited as proof of superiority.
  - Test look outcome: Point estimate $= +0.0000$, 95% CI: $[-0.0275, +0.0275]$. Labeled inconclusive on synthetic smoke data.

---

### Decision 23: Covariate and Prevalence Shift Scenarios (S0, S1, S3)
- **Context:** Evaluating triage resilience requires testing beyond static reference distributions without data leakage or label-optimized shift injection.
- **Decision:** Implemented in `data/scenario_builders.py`:
  - **S0 (Reference):** Untouched chronological test split ($2,000$ rows, $111$ frauds).
  - **S3 (Covariate Shift):** Deterministic log-normal transaction amount scaling and Gaussian perturbation on top $V$ and $D$ features with fixed seed `42`. Labeled `SYNTHETIC_SHIFT`.
  - **S1 (Prevalence Burst):** Chronological temporal subwindow capturing transaction density shifts.
  - Each scenario produces a deterministic SHA-256 hash and metadata provenance record.

---

### Decision 24: Distribution Drift Monitoring (PSI and KS Statistics)
- **Context:** Monitoring distribution changes between training reference data and incoming test/shift streams provides early warning of pipeline degradation.
- **Decision:** Implemented in `eval/drift.py`:
  - Established quantile reference bins on the training partition ($6,000$ rows).
  - Applied epsilon smoothing ($\epsilon = 10^{-4}$) to safely handle zero frequencies.
  - Classified stability into standard bands: Stable ($\text{PSI} < 0.10$), Moderate ($0.10 \le \text{PSI} \le 0.20$), and Significant ($\text{PSI} > 0.20$).
  - Two-sample Kolmogorov-Smirnov test calculates feature-level maximum distance and asymptotic p-value.
  - Discipline: Drift statistics monitor feature stability and are explicitly distinguished from fraud prediction or novelty scoring.

---

### Decision 25: Segment-Level Escalation Analysis & Fairness Scope Discipline
- **Context:** Blueprint Section 6.3 requires screening for triage disparities across transaction and card segments (`ProductCD`, `card4`) while preventing unsupported demographic fairness claims.
- **Decision:** Implemented in `eval/segments.py`:
  - Evaluated group-level sample sizes, fraud counts, alert/review/deferred volumes, touched rates, recall, and precision.
  - Handled rare and zero-count categories safely without division errors.
  - Explicit Disclaimer: Benchmark segment screening evaluates operational categories (merchant products and card networks), not protected demographic classes. Demographic fairness certification is explicitly disclaimed.

---

### Decision 26: Operational Scenario Value Model
- **Context:** Operational ROI analysis must transparently separate observed transaction amounts from speculative labor, friction, and recovery assumptions.
- **Decision:** Implemented in `eval/value_model.py`:
  - Formula: $\text{Net Benefit} = (\text{Caught Fraud Value} \times \text{Recovery Rate}) - (\text{Review Cost} \times \text{Touched}) - (\text{Friction Cost} \times \text{False Alerts})$.
  - Base assumptions: Labor cost per review $= \$20.00$, false alert customer friction $= \$30.00$, recovery rate $= 90\%$.
  - Sensitivity grid explores cost parameters ($\$10-\$30$ review, $\$15-\$50$ friction, $80\%-100\%$ recovery).
  - Explicit disclaimer: Observed transaction amounts do not guarantee cash recovery or chargeback prevention.

---

### Decision 27: Micro-Benchmarking of Latency on Commodity x86 Hardware
- **Context:** Blueprint Acceptance Criterion AC5 requires single-row p95 latency $\le 50.0\text{ ms}$.
- **Decision:** Implemented in `eval/latency.py`:
  - Timed using `time.perf_counter_ns` with untimed warmup (200 single calls, 50 batch calls).
  - Benchmarked 5,000 single-row end-to-end calls and 1,000 batch-of-32 calls covering preprocessing, base scoring, ensemble disagreement, rank residualization, and routing.
  - Result: Single-row p95 $= 16.37\text{ ms}$ (comfortably within AC5 threshold of $50.0\text{ ms}$). Batch-32 throughput $= 0.47\text{ ms}$ per transaction.
  - Hardware Discipline: Benchmark captures host environment metadata (AMD64 Windows 11, Intel Core i3-1115G4). Mainframe acceleration or hardware coprocessors are explicitly not claimed.

---

### Decision 28: Gate G5 Final Test Look Execution & Canonical Results Artifact
- **Context:** Gate G5 represents the second and final pre-registered evaluation look on the held-out test split prior to frontend development.
- **Decision:**
  - Verified identical cryptographic hashes before evaluation: Dataset (`da0017...`), Split (`07b55a...`), and Config (`8d3f02...`).
  - Recorded final G5 look in `logs/test_looks.log`.
  - Emitted canonical `results/results.json`, 5 CSV evidence tables in `results/tables/`, and 5 high-resolution evaluation figures in `results/figs/`.
  - Evaluation results remain frozen; no iterative tuning or policy modifications will be made.




