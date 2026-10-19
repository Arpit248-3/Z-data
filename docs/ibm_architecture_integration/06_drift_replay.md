# SignalGate IBM Architecture Integration — Phase 7: Data-Driven Drift Monitoring and Human-Approved Replay Gate

**Governing Specification:** `docs/ibm_architecture_integration_master_spec.md` § C, § K
**Status:** IMPLEMENTED_VERIFIED
**Architecture Version:** `ieee_cis_v1`
**Requirements Covered:** `DRFT-01`, `DRFT-02`, `DRFT-03`
**Last Updated:** 2026-10-18

---

## 1. Executive Summary & Non-Negotiable Boundaries

Phase 7 implements the multi-metric distribution drift engine, the advisory Drift Sentinel, and the deterministic Replay Gate with human approval governance for the real IEEE-CIS Fraud Detection benchmark integration.

The implementation strictly satisfies the non-negotiable boundaries defined in `docs/ibm_architecture_integration_master_spec.md`:
1. **Multi-Metric Distribution Monitoring (`DRFT-01`, Master Spec § K):** Evaluates feature and score distribution divergence using Population Stability Index (PSI), two-sample Kolmogorov-Smirnov (KS) tests, 1D Wasserstein Earth Mover's Distance, and missingness rate deltas.
2. **Strict Separation of Diagnostic Dimensions (`DRFT-01`):** The system strictly distinguishes (1) feature distribution drift, (2) prediction-score drift, (3) calibration/performance degradation (evaluated strictly offline on validation partitions with labels), and (4) epistemic model disagreement ($u_2$).
3. **Drift $\neq$ Fraud Invariant (`DRFT-01`, Master Spec § K):** Distribution drift indicates covariate or output shift, **never proof of fraud**. Drift indicators must never automatically escalate a transaction to `FRAUD_ALERT`.
4. **Strict Ground-Truth Quarantine (`DRFT-01`, Master Spec § C2):** Target labels (`isFraud`, `target`, `label`, `true_label`) and raw transaction identifiers (`TransactionID`, `TransactionDT`) are strictly prohibited and rejected from drift inputs with `LeakageViolationError`.
5. **Advisory Drift Sentinel & Strict Allowlisting (`DRFT-02`, Master Spec § K):** The `DriftSentinel` constructs inert `Proposal` records when statistical triggers are breached. Proposed parameter changes are strictly restricted to allowlisted policy parameters (`t_alert`, `t_review`, `u_threshold`, `disagreement_weight_lambda`, `primary_workload_multiple`). Modifying model weights, tree estimators, calibrators, or dataset files is prohibited.
6. **Deterministic Replay Gate & Human Authorization Protocol (`DRFT-03`, Master Spec § K):**
   - The `ReplayGate` validates schema, base config hash, allowlisted keys, and parameter bounds.
   - Replays proposed policy deterministically across the **validation** partition (`splits['validation']`) or registered scenarios (S0, S1, S2, S3).
   - **Test Set Quarantine:** The held-out test partition (`splits['test']`) is strictly quarantined and forbidden from replay gating.
   - **No Autonomous Activation:** Successful replay leaves the proposal strictly in **`AWAITING_HUMAN_APPROVAL`**.
   - Activation requires explicit human approval with authenticated `approver_id`, timestamp, and rationale.
   - Approval and rejection decisions are cryptographically sealed into the `AuditChain`.

---

## 2. Multi-Metric Drift Monitoring Architecture (`DRFT-01`)

### 2.1 Distribution Metrics & Mathematical Formulations

#### Population Stability Index (PSI)
Quantile bin edges $B_0, \dots, B_K$ are computed over the reference distribution $P_{\text{ref}}$. Comparison distribution proportions $P_{\text{act}}$ are smoothed with $\epsilon = 10^{-4}$:
$$\text{PSI} = \sum_{k=1}^K \left( P_{\text{act}}(k) - P_{\text{ref}}(k) \right) \cdot \ln\left( \frac{P_{\text{act}}(k)}{P_{\text{ref}}(k)} \right)$$

Categorical thresholds:
- $\text{PSI} < 0.10$: **Stable** (negligible drift)
- $0.10 \le \text{PSI} \le 0.20$: **Moderate Drift**
- $\text{PSI} > 0.20$: **Significant Drift**

#### Kolmogorov-Smirnov (KS) Two-Sample Test
Evaluates supremum distance between empirical cumulative distribution functions $F_{\text{ref}}$ and $F_{\text{act}}$:
$$D = \sup_x |F_{\text{ref}}(x) - F_{\text{act}}(x)|$$
Computes asymptotic p-value via `scipy.stats.ks_2samp`.

#### 1D Wasserstein Earth Mover's Distance
Computes optimal transport distance between 1D continuous distributions via `scipy.stats.wasserstein_distance`:
$$l_1(u, v) = \int_{-\infty}^{+\infty} |U(x) - V(x)| dx$$
Where $U$ and $V$ are cumulative distributions of $u$ and $v$.

#### Missingness Delta
$$\Delta_{\text{missing}} = \text{rate}_{\text{actual}} - \text{rate}_{\text{ref}}$$

### 2.2 Separation of Diagnostic Dimensions

```
+-----------------------------------------------------------------------------+
|                          SignalGate Diagnostic Scope                        |
+-----------------------------------------------------------------------------+
| 1. Feature Drift (Covariate Shift)   : P(X_actual) vs P(X_ref)              |
|    - Evaluated across tabular features (TransactionAmt, V-columns, etc.)     |
|    - Metrics: PSI, KS D-stat, Wasserstein distance, missingness delta       |
+-----------------------------------------------------------------------------+
| 2. Prediction-Score Drift             : P(p_actual) vs P(p_ref)             |
|    - Evaluated across calibrated posterior probabilities p                  |
|    - Quantifies output score distribution shifts                            |
+-----------------------------------------------------------------------------+
| 3. Calibration / Performance Degradation: ECE, Brier, Recall, Precision    |
|    - STRICTLY RESTRICTED to offline validation partitions with ground truth  |
|    - Prohibited on unlabelled production streams or held-out test data      |
+-----------------------------------------------------------------------------+
| 4. Model Disagreement (Epistemic)    : Dispersion across tree estimators    |
|    - Robust rank residual dispersion u_2 = median(|p_m - median(p)|)        |
|    - Quantifies estimator disagreement, NOT distribution shift or fraud     |
+-----------------------------------------------------------------------------+
```

---

## 3. Advisory Drift Sentinel (`DRFT-02`)

### 3.1 Trigger Conditions & Allowlisted Policy Parameters

The `DriftSentinel` evaluates calculated `DriftReport` instances against statistical alert thresholds:
- `significant_drift_features >= max_significant_features` (default 1)
- `mean_psi >= mean_psi_alert_threshold` (default 0.10)
- `score_drift.psi >= score_drift_threshold` (default 0.15)

When triggered, it emits an advisory `Proposal` binding `base_cfg_hash = current_policy.compute_cfg_hash()`.

### 3.2 Parameter Allowlist & Boundary Matrix

| Parameter | Allowed Range | Ordering / Constraint | Permitted Adaptation |
|---|:---:|:---:|---|
| `t_alert` | $[0.01, 1.0]$ | $t_{\text{alert}} > t_{\text{review}}$ | High-risk alert threshold adjustment |
| `t_review` | $[0.01, 1.0]$ | $t_{\text{review}} < t_{\text{alert}}$ | Manual review threshold adjustment |
| `u_threshold` | $[0.0, 1.0]$ | Non-negative float | Epistemic disagreement threshold |
| `disagreement_weight_lambda` | $[0.0, 1.0]$ | $[0.0, 1.0]$ | P5 candidate ranking lambda weight |
| `primary_workload_multiple` | $[0.5, 5.0]$ | Positive float | Operational review capacity multiplier |

**Prohibited Keys:** Any proposal containing unapproved keys (e.g. `model_weights`, `raw_features`, `isFraud`, hyperparameters) fails validation immediately.

---

## 4. Deterministic Replay Gate & Human Approval Protocol (`DRFT-03`)

### 4.1 Replay Lifecycle State Machine

```
              [Proposal Emitted]
                      |
                      v
                 ( PENDING )
                      |
                      | ReplayGate.validate_and_replay()
                      v
      +-------------------------------+
      | Checks:                       |
      | - base_cfg_hash match         |
      | - allowlist parameters        |
      | - parameter bounds/ordering   |
      | - validation data (NOT test!) |
      +-------------------------------+
         /                         \
    (Failed)                     (Pass)
       /                             \
      v                               v
[ FAILED_VALIDATION ]    [ AWAITING_HUMAN_APPROVAL ]
                                  /       \
                     approve_proposal()  reject_proposal()
                                /           \
                               v             v
                         [ APPROVED ]   [ REJECTED ]
```

### 4.2 Replay Metrics & Capacity Adherence
The Replay Gate evaluates candidate policies across validation cases, computing:
- **Touches:** Count of cases receiving `FRAUD_ALERT` or `MANUAL_REVIEW`.
- **Review Rate:** Touched cases divided by validation sample count.
- **Churn Count:** Count of cases where triage action changed between baseline and candidate policy ($A_{\text{base}} \neq A_{\text{cand}}$).
- **Capacity Adherence:** Validates that candidate review volume does not breach the operational capacity limit $B_{\text{frac}} = M \cdot p_{\text{prev}}$.

### 4.3 Explicit Human Authorization & Cryptographic Provenance
- Successful replay leaves the proposal strictly in `AWAITING_HUMAN_APPROVAL`.
- `approve_proposal()` records: `approver_id`, `timestamp`, `rationale`, and cryptographically seals the decision into the `AuditChain`.
- `reject_proposal()` marks the proposal `REJECTED`, leaving the active production policy completely intact.

---

## 5. Verification & Test Evidence

The Phase 7 implementation was comprehensively verified with 18 dedicated unit and integration tests in `tests/test_ibm_drift_replay.py`:

```
============================= test session starts =============================
platform win32 -- Python 3.11.9, pytest-9.1.1, pluggy-1.7.0
rootdir: C:\Users\himan\Downloads\zprject
collected 18 items

tests/test_ibm_drift_replay.py::test_psi_stable_distribution PASSED        [  5%]
tests/test_ibm_drift_replay.py::test_psi_significant_drift PASSED         [ 11%]
tests/test_ibm_drift_replay.py::test_ks_statistic_computation PASSED      [ 16%]
tests/test_ibm_drift_replay.py::test_wasserstein_distance_computation PASSED [ 22%]
tests/test_ibm_drift_replay.py::test_prediction_score_drift_computation PASSED [ 27%]
tests/test_ibm_drift_replay.py::test_missing_and_nonfinite_inputs PASSED   [ 33%]
tests/test_ibm_drift_replay.py::test_drift_monitor_ground_truth_quarantine PASSED [ 38%]
tests/test_ibm_drift_replay.py::test_drift_report_provenance_and_notice PASSED [ 44%]
tests/test_ibm_drift_replay.py::test_sentinel_no_drift_no_proposal PASSED  [ 50%]
tests/test_ibm_drift_replay.py::test_sentinel_generates_advisory_proposal_on_drift PASSED [ 55%]
tests/test_ibm_drift_replay.py::test_sentinel_rejects_forbidden_keys PASSED [ 61%]
tests/test_ibm_drift_replay.py::test_sentinel_parameter_bounds_enforcement PASSED [ 66%]
tests/test_ibm_drift_replay.py::test_replay_gate_validation_replay_success PASSED [ 72%]
tests/test_ibm_drift_replay.py::test_replay_gate_test_partition_quarantine PASSED [ 77%]
tests/test_ibm_drift_replay.py::test_replay_gate_hash_mismatch_rejection PASSED [ 83%]
tests/test_ibm_drift_replay.py::test_replay_gate_explicit_human_approval PASSED [ 88%]
tests/test_ibm_drift_replay.py::test_replay_gate_rejection_leaves_policy_intact PASSED [ 94%]
tests/test_ibm_drift_replay.py::test_end_to_end_drift_to_replay_lifecycle PASSED [100%]

============================= 18 passed in 3.22s ==============================
```

Full repository regression verification: **195 passed** (0 regressions, 100% pass rate).
