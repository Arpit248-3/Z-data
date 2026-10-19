# Phase 7: Data-Driven Drift Monitoring and Human-Approved Replay Gate — Research & Technical Specifications

**Phase:** `07-data-driven-drift-monitoring-and-human-approved-replay-gate`
**Date:** 2026-10-18
**Governing Specification:** `docs/ibm_architecture_integration_master_spec.md` § C, § K
**Requirements Covered:** `DRFT-01`, `DRFT-02`, `DRFT-03`

---

## 1. Architectural Objectives & Non-Negotiable Invariants

Phase 7 implements deterministic, evidence-backed drift monitoring, the advisory Drift Sentinel, and the human-approved Replay Gate for the IEEE-CIS integration.

In strict compliance with the governing specification and review directives:

### 1.1 Multi-Metric Drift Monitoring (`DRFT-01`, Master Spec § K)
The drift monitoring engine computes multi-dimensional distribution divergence:
- **Population Stability Index (PSI):** Quantile binning over reference distributions with epsilon smoothing ($10^{-4}$) to prevent numerical instability.
- **Kolmogorov-Smirnov (KS) Two-Sample Test:** Computes supremum distance $D$ and asymptotic p-value via `scipy.stats.ks_2samp`.
- **Wasserstein Distance (Earth Mover's Distance):** Measures optimal transport distance between 1D distributions via `scipy.stats.wasserstein_distance`.
- **Missingness Delta:** Tracks changes in feature missing rates ($\Delta_{\text{missing}} = \text{rate}_{\text{actual}} - \text{rate}_{\text{ref}}$).

### 1.2 Separation of Four Orthogonal Diagnostic Dimensions
The engine strictly segregates and labels four distinct monitoring phenomena:
1. **Feature Distribution Drift (Covariate Shift):** Divergence in input feature vectors $P(X)$.
2. **Prediction-Score Drift (Concept/Output Shift):** Divergence in calibrated ensemble posterior probability $P(p)$.
3. **Calibration & Performance Degradation:** ECE (Expected Calibration Error), Brier score, and recall/precision degradation. Strictly restricted to offline validation partitions where ground-truth labels are available; **never** evaluated on unlabelled live or holdout streaming data.
4. **Model Disagreement & Epistemic Uncertainty:** Inter-model prediction dispersion ($u_2$) across tree estimators.

### 1.3 Non-Negotiable Drift Discipline
- **Drift $\neq$ Fraud Invariant:** Covariate shift or score drift indicates distribution change, **not proof of fraud**. Drift indicators must never automatically escalate a transaction to `FRAUD_ALERT`.
- **Ground-Truth Quarantine:** Drift monitoring evaluates feature and score distributions only. Target labels (`isFraud`, `target`, `label`, `true_label`) and transaction identifiers (`TransactionID`, `TransactionDT`) are strictly quarantined and prohibited from drift calculation inputs.
- **Evidence Labeling:** Saved baseline reports are marked `HISTORICAL_RECORDED`; dynamic evaluations are marked `LIVE_EVALUATED` or `BENCHMARK_SCENARIO`.

### 1.4 Advisory Drift Sentinel & Strict Allowlisting (`DRFT-02`, Master Spec § K)
- Continuously inspects drift reports. If drift breaches operational alert thresholds (e.g., `significant_drift_features > 0`, `mean_psi >= 0.10`, or `score_psi >= 0.15`), the Sentinel constructs an advisory `Proposal`.
- **Strict Allowlisted Policy Keys:**
  $$\{\texttt{t\_alert}, \texttt{t\_review}, \texttt{u\_threshold}, \texttt{disagreement\_weight\_lambda}, \texttt{primary\_workload\_multiple}\}$$
- **Prohibited Modifications:** Strictly forbids proposals modifying model weights, tree hyperparameters, calibrators, feature transformations, dataset paths, or arbitrary code.
- **Parameter Bounds & Ordering:**
  - $0.01 \le t_{\text{review}} < t_{\text{alert}} \le 1.0$
  - $0.0 \le u_{\text{threshold}} \le 1.0$
  - $0.0 \le \lambda \le 1.0$
  - $0.5 \le \text{workload\_multiplier} \le 5.0$
- **Zero Execution Authority:** The Sentinel produces strictly inert `Proposal` records with status `AWAITING_REPLAY` / `PENDING`. It has zero authority or code paths to mutate active runtime policies.

### 1.5 Deterministic Replay Gate & Human Authorization Protocol (`DRFT-03`, Master Spec § K)
- Validates proposal schema, base configuration hash matching (`base_cfg_hash == active_policy_hash`), allowlisted keys, and parameter bounds.
- **Deterministic Validation Partition Replay:**
  - Replays the candidate policy configuration deterministically across the **validation** partition (`splits['validation']`) or registered scenarios (S0, S1, S2, S3).
  - **Strict Test Partition Quarantine:** The final held-out test partition (`splits['test']`) is strictly quarantined and forbidden from being used for replay gating or policy selection.
  - Replay computes comparative metrics: baseline vs. proposed touches, review rate, churn count (number of cases changing action), and capacity impact against budget $B$.
- **Explicit Human Authorization Lifecycle:**
  - On replay verification passing, the proposal transitions strictly to **`AWAITING_HUMAN_APPROVAL`**.
  - **No automated threshold tuning or autonomous activation is permitted.**
  - Transition to `APPROVED` requires explicit human approval with authenticated `approver_id`, timestamp, and rationale.
  - Transition to `REJECTED` occurs if validation fails, parameter bounds are breached, timeout occurs, or the human reviewer rejects the proposal.
  - If rejected or failed, the active production policy remains 100% untouched.
- **Cryptographic Audit Chain Integration:**
  - Drift evaluation summaries and Replay Gate approval decisions are signed and sequentially appended to the cryptographic `AuditChain`.

---

## 2. Component Specifications

### 2.1 Drift Engine (`integrations/ibm_architecture/governance/drift_monitor.py`)
- **`FeatureDriftResult` Schema:**
  - `feature: str`
  - `psi: Optional[float]`
  - `ks_statistic: Optional[float]`
  - `ks_pvalue: Optional[float]`
  - `wasserstein_distance: Optional[float]`
  - `drift_category: Literal["stable", "moderate_drift", "significant_drift", "unknown"]`
  - `ref_sample_count: int`
  - `act_sample_count: int`
  - `ref_missing_rate: float`
  - `act_missing_rate: float`
  - `missing_rate_delta: float`
- **`DriftReport` Schema:**
  - `report_id: str`
  - `reference_window_id: str`
  - `comparison_window_id: str`
  - `features_monitored: int`
  - `significant_drift_features: int`
  - `moderate_drift_features: int`
  - `mean_psi: float`
  - `max_psi: float`
  - `score_drift: Optional[FeatureDriftResult]` (Drift on calibrated posterior $p$)
  - `feature_reports: List[FeatureDriftResult]`
  - `provenance_hash: str`
  - `timestamp: datetime`
  - `status: str`
  - `notice: str` (Discipline disclaimer)
- **`DriftMonitor` Class:**
  - Implements `calculate_psi`, `calculate_ks`, `calculate_wasserstein`, `compute_feature_drift`, and `compute_drift_report`.
  - Quarantines labels and IDs.
  - Binds deterministic SHA-256 provenance hash.

### 2.2 Advisory Drift Sentinel (`integrations/ibm_architecture/governance/drift_sentinel.py`)
- **`SentinelConfig` Schema:**
  - `psi_moderate_threshold: float = 0.10`
  - `psi_significant_threshold: float = 0.20`
  - `score_drift_threshold: float = 0.15`
  - `max_significant_features: int = 1`
  - `mean_psi_alert_threshold: float = 0.10`
- **`DriftSentinel` Class:**
  - Evaluates `DriftReport` against thresholds.
  - Emits inert `Proposal` targeting allowlisted parameters.
  - Validates parameter ordering and bounds.
  - Enforces matching `base_cfg_hash`.

### 2.3 Deterministic Replay Gate (`integrations/ibm_architecture/governance/replay_gate.py`)
- **`ProposalStatus` Enum:**
  - `PENDING = "PENDING"`
  - `REPLAY_VALIDATED = "REPLAY_VALIDATED"`
  - `AWAITING_HUMAN_APPROVAL = "AWAITING_HUMAN_APPROVAL"`
  - `APPROVED = "APPROVED"`
  - `REJECTED = "REJECTED"`
  - `FAILED_VALIDATION = "FAILED_VALIDATION"`
- **`ReplayValidationResult` Schema:**
  - `proposal_id: str`
  - `is_valid: bool`
  - `base_cfg_hash_matches: bool`
  - `allowlist_passed: bool`
  - `bounds_passed: bool`
  - `replay_executed: bool`
  - `validation_samples: int`
  - `baseline_touches: int`
  - `proposed_touches: int`
  - `churn_count: int`
  - `capacity_exceeded: bool`
  - `details: Dict[str, Any]`
  - `rejection_reason: Optional[str]`
- **`ReplayGate` Class:**
  - `validate_and_replay(proposal, current_policy, validation_data, scenario_id="validation")`:
    - Validates schema, hashes, allowlist, and bounds.
    - Runs policy comparison over validation partition.
    - Transitions proposal to `AWAITING_HUMAN_APPROVAL`.
  - `approve_proposal(proposal_id, approver, rationale, audit_chain=None)`:
    - Transitions from `AWAITING_HUMAN_APPROVAL` to `APPROVED`.
    - Seals decision record into `AuditChain`.
  - `reject_proposal(proposal_id, reviewer, reason, audit_chain=None)`:
    - Transitions to `REJECTED`.
    - Active policy remains completely unchanged.

---

## 3. Preservation & Non-Regression Invariants

1. **Test Set Isolation:** Test partition (`splits['test']`) remains strictly held out and quarantined from replay gating.
2. **Artifact Preservation:** Synthetic models, root policies, Phase 4 trained model bundle (`models/artifacts/ieee_cis_v1/`), historical results (`results/results.json`, `pre_eval_freeze_record.json`), and 3D assets remain untouched.
3. **Zero Autonomous Activation:** No threshold tuning or activation can occur without deterministic replay and explicit human approval.
4. **Full Test Suite:** All 177 existing tests must continue to pass with zero regressions.
