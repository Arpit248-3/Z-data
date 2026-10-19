# Phase 5: Dynamic Scoring, Baselines, Frozen Policy and Capacity Governance — Research & Technical Specifications

**Phase:** `05-dynamic-scoring-baselines-frozen-policy-and-capacity-governance`
**Date:** 2026-10-18
**Governing Specification:** `docs/ibm_architecture_integration_master_spec.md` § C, § I
**Requirements Covered:** `SCOR-01`, `SCOR-02`, `SCOR-03`

---

## 1. Architectural Objectives & Invariants

Phase 5 designs, implements, and verifies the deterministic dynamic scoring service, baseline policies, candidate P5 policy adapter, and capacity governance for the IEEE-CIS integration.

In strict compliance with the governing specification:
1. **Isolated Integration Namespace (`SCOR-01`):** All policy definitions, adapters, capacity governor logic, and scoring service code will reside in `integrations/ibm_architecture/policy/` and `integrations/ibm_architecture/scoring/`. Existing canonical synthetic policy files in `policy/` (`frozen_policy.json`, `router.py`, `governor.py`, `baselines.py`) remain completely untouched.
2. **Ground-Truth Quarantine Barrier (`SCOR-03`, Master Spec § C2):**
   - Scoring requests must never include the target label `isFraud` or raw transaction identifiers (`TransactionID`, `TransactionDT`) in feature inputs.
   - If quarantined fields are detected, `ScoringService` immediately raises `LeakageViolationError`.
   - Operational identifiers (e.g. `transaction_id`) are accepted purely as pseudonymous reference keys in request metadata and are never forwarded to feature pipelines or inference models.
3. **Deterministic Policy Adapters (`SCOR-01`, Master Spec § I):**
   - **`RouterPolicyAdapter`:** Evaluates calibrated risk $p$, model disagreement $u$, and novelty $n$ against frozen policy thresholds (`t_alert`, `t_review`, `u_threshold`), assigning actions (`FRAUD_ALERT`, `MANUAL_REVIEW`, `ROUTINE`, `HELD`, `DEFERRED`) and auditable reason codes (`R0`–`R6`).
   - **`B2TopBudgetBaselineAdapter`:** Ranks transactions descending by calibrated risk score $p$ and escalates the top fraction $B$ matching the registered review capacity budget.
   - **`P5CandidatePolicyAdapter`:** Evaluates candidate ranking formula $\text{Score} = p_{\text{calibrated}} + \lambda \cdot u_{\text{signal}}$. Under the reference configuration, $\lambda = 0.0$ (calibrated risk ranking). P5 is strictly a cohort-relative budget-ranking policy; it requires a cohort context and cannot be applied to an isolated single transaction as if batch context were irrelevant.
4. **Capacity Governance & No-Silent-Clearance Invariant (`SCOR-02`, Master Spec § I):**
   - Analyst review capacity is strictly capped at $B = 130$ cases (or budget fraction $6.525\%$ on evaluation cohorts).
   - Candidate escalations (`FRAUD_ALERT`, `MANUAL_REVIEW`) are prioritized deterministically by risk score with stable tie-breaking.
   - When candidate escalations exceed available quota $B$, excess escalations are shunted to `DEFERRED` with reason code `R6_CAPACITY_DEFERRED`.
   - **Critical Safety Invariant:** Capacity saturation must NEVER silently reclassify a high-risk or ambiguous transaction as `ROUTINE`. Deferred cases remain visibly partitioned in a dedicated deferred queue.
5. **Fail-Closed Scoring Service (`SCOR-03`, Master Spec § I):**
   - `ScoringService` loads the cryptographic model bundle from `models/artifacts/ieee_cis_v1/`, verifying artifact SHA-256 hashes on startup.
   - Accepts validated feature inputs, applies `FeaturePipeline.transform()`, extracts calibrated risk $p$, computes disagreement $u$ and $u_2$, and routes via the specified policy.
   - Fails closed to `MANUAL_REVIEW` / `R0_SIGNAL_UNAVAILABLE` on invalid or out-of-bounds input signals, and raises `ArtifactNotFoundError` / `IncompatibleArtifactError` if required model artifacts are missing or altered.

---

## 2. Policy Specifications & Mathematical Formulations

### 2.1 Frozen Policy Configuration (`frozen_policy.py`)
The frozen reference policy binds the following parameters established during pre-evaluation calibration:
- `t_alert`: **0.084705** (transactions with $p \ge t_{\text{alert}}$ produce `FRAUD_ALERT`, `R1_HIGH_RISK`)
- `t_review`: **0.071002** (transactions with $p \ge t_{\text{review}}$ produce `MANUAL_REVIEW`, `R2_INTERMEDIATE_RISK`)
- `u_threshold`: **0.526773** (transactions with $u \ge u_{\text{threshold}}$ produce `MANUAL_REVIEW`, `R3_MODEL_DISAGREEMENT`)
- `disagreement_enabled`: `True`
- `disagreement_variant`: `"u2_rank_residual"` (or population standard deviation $u$)
- `novelty_enabled`: `False`
- `target_budget`: **0.06525** ($B = 130$ cases on 2,000-case evaluation cohort)

### 2.2 Triage Decision Router (`RouterPolicyAdapter`)
Evaluation follows strict deterministic precedence:
1. **Config Validation:** If router parameters are missing, non-finite, out of $[0, 1]$, or $t_{\text{review}} \ge t_{\text{alert}}$, fail closed to `(MANUAL_REVIEW, R0_SIGNAL_UNAVAILABLE)`.
2. **Signal Validation:** If $p$ is None, NaN, Inf, or outside $[0, 1]$, fail closed to `(MANUAL_REVIEW, R0_SIGNAL_UNAVAILABLE)`.
3. **Secondary Signal Validation:** If disagreement is enabled and $u$ is None, NaN, Inf, or negative, fail closed to `(MANUAL_REVIEW, R0_SIGNAL_UNAVAILABLE)`.
4. **High-Risk Rule:** $p \ge t_{\text{alert}} \longrightarrow (\text{FRAUD\_ALERT}, \text{R1\_HIGH\_RISK})$. A high risk score can NEVER produce `ROUTINE`.
5. **Intermediate-Risk Rule:** $p \ge t_{\text{review}} \longrightarrow (\text{MANUAL\_REVIEW}, \text{R2\_INTERMEDIATE\_RISK})$.
6. **Disagreement Rule:** $u \ge u_{\text{threshold}} \longrightarrow (\text{MANUAL\_REVIEW}, \text{R3\_MODEL\_DISAGREEMENT})$. Disagreement alone triggers review, never fraud alert (uncertainty is not proof of fraud).
7. **Default Reliable Low-Risk:** $(\text{ROUTINE}, \text{R5\_LOW\_RISK\_RELIABLE})$.

### 2.3 Baseline B2 Top-Budget Policy (`B2TopBudgetBaselineAdapter`)
- Sorts cohort transactions descending by calibrated risk $p$. Stable tie-breaking on row index / transaction ID.
- Determines capacity $K = \lfloor N \cdot B \rfloor$.
- Top $K$ transactions are escalated (`MANUAL_REVIEW` or `FRAUD_ALERT`).
- Remaining $N - K$ transactions are assigned `ROUTINE`.

### 2.4 Candidate P5 Policy (`P5CandidatePolicyAdapter`)
- **Ranking Score:**
  $$\text{Score}_i = p_i + \lambda \cdot u_i$$
- **Frozen Reference Parameter:** $\lambda = 0.0$.
  *Documentation requirement:* When $\lambda = 0.0$, the P5 candidate ranks transactions purely by calibrated probability of fraud $p$, equivalent to risk ranking. The adapter must explicitly record $\lambda$ and never falsely claim that a $\lambda=0.0$ ranking incorporates disagreement-weighted prioritization.
- **Cohort Dependency:** P5 requires batch/cohort context to calculate cutoffs. If called on a single row without cohort bounds or declared threshold, it fails closed with an informative error stating cohort context is required.

---

## 3. Capacity Governance Architecture (`CapacityGovernor`)

The Capacity Governor manages operational escalation volume to match analyst capacity $B = 130$:

```
                      +-----------------------------+
                      |   Router Candidate Queue    |
                      |  (FRAUD_ALERT, MANUAL_REV)  |
                      +--------------+--------------+
                                     |
                         Sort by Risk Score p (desc)
                                     |
                     +---------------+---------------+
                     |                               |
              Rank <= B (130)                  Rank > B (130)
                     |                               |
                     v                               v
             +---------------+               +---------------+
             | Admitted Case |               | Deferred Case |
             | (Action kept, |               | Action=DEFERRED|
             | status=ADMIT) |               | Reason=R6)    |
             +---------------+               +---------------+
```

### 3.1 Accounting & Metrics
- $\text{Total Transactions} = N$
- $\text{Requested Escalations} = \text{Alerts} + \text{Reviews}$
- $\text{Admitted Count} = \min(\text{Requested}, B)$
- $\text{Deferred Count} = \max(0, \text{Requested} - B)$
- $\text{Touched Rate} = \frac{\text{Admitted Count}}{N}$
- $\text{Deferred Rate} = \frac{\text{Deferred Count}}{N}$

---

## 4. Deterministic Scoring Service (`ScoringService`)

### 4.1 Interface Specification
```python
class ScoringService:
    def __init__(self, bundle: Optional[ModelBundle] = None, policy_cfg: Optional[Dict[str, Any]] = None):
        ...

    def score_single(
        self,
        features: Dict[str, Any] | pd.Series,
        transaction_id: Optional[str | int] = None,
        policy_name: str = "router",
    ) -> ScoringResult:
        ...

    def score_batch(
        self,
        df: pd.DataFrame,
        id_col: Optional[str] = "TransactionID",
        policy_name: str = "router",
        capacity: Optional[int] = 130,
    ) -> BatchScoringResult:
        ...
```

### 4.2 Result Schemas
- `ScoringResult`: Immutable record with `transaction_id`, `p`, `u`, `u2`, `action`, `reason`, `model_version`, `policy_version`, `timestamp_utc`.
- `BatchScoringResult`: Contains list of `ScoringResult` rows, summary statistics, governor accounting (admitted, deferred, touched rate), and policy metadata.

---

## 5. Threat Model & Security Controls

| Threat | Vulnerability | Mitigation |
|---|---|---|
| **Target Leakage** | Caller passes `isFraud` into scoring dictionary | Proactive inspection raises `LeakageViolationError` before preprocessing |
| **Silent Clearance Leak** | High-volume fraud spike saturates capacity; excess cases cleared | Governor shunts excess cases to `DEFERRED` / `R6`; never reclassifies as `ROUTINE` |
| **Model Desynchronization** | Scorer uses model weights from different training run | Checksum validation in `load_bundle()` guarantees exact manifest match |
| **Ambiguity Masking** | Highly uncertain transaction ($u \ge 0.52$) classified as routine | Router rule 6 routes directly to `MANUAL_REVIEW`, `R3_MODEL_DISAGREEMENT` |
| **Invalid Input Crash** | NaN or Inf features cause uncaught exception | Imputer handles missing values; signal validator fails closed to `R0` |

---

## 6. Implementation & Verification Plan

1. **Task 1: Policy Adapters (`integrations/ibm_architecture/policy/`):**
   - Author `router.py`, `baselines.py`, `p5_candidate.py`, `governor.py`, `frozen_policy.py`, and `__init__.py`.
2. **Task 2: Deterministic Scoring Service (`integrations/ibm_architecture/scoring/`):**
   - Author `service.py`, `schemas.py`, and `__init__.py`.
   - Wire package exports into top-level `integrations/ibm_architecture/__init__.py`.
3. **Task 3: Comprehensive Unit Test Suite (`tests/test_ibm_scoring.py`):**
   - Author test suite verifying router boundaries, fail-closed handling, B2 budget matching, P5 cohort requirement, capacity governor overflow and tie-breaking, leakage quarantine rejection, and scoring service single/batch execution.
   - Run full pytest suite confirming 100% pass rate with zero regressions.
4. **Task 4: Author Deliverable `docs/ibm_architecture_integration/04_scoring_policy.md`:**
   - Author authoritative deliverable documenting policy architectures, threshold mathematics, capacity governor invariants, scoring service APIs, and compliance matrix.
