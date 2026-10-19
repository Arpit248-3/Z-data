# SignalGate IBM Architecture Integration — Phase 5: Dynamic Scoring, Baselines, Frozen Policy & Capacity Governance

**Governing Specification:** `docs/ibm_architecture_integration_master_spec.md` § C, § I
**Status:** IMPLEMENTED_VERIFIED
**Architecture Version:** `ieee_cis_v1`
**Requirements Covered:** `SCOR-01`, `SCOR-02`, `SCOR-03`
**Last Updated:** 2026-10-18

---

## 1. Executive Summary & Architectural Overview

Phase 5 implements the clean-room, deterministic scoring engine, policy adapters, and capacity governance for the real IEEE-CIS Fraud Detection benchmark.

The implementation strictly satisfies the governing specification and all project invariants:
1. **Namespace & Artifact Isolation (`SCOR-01`):** All policy definitions, adapters, capacity governor logic, and scoring service code reside in `integrations/ibm_architecture/policy/` and `integrations/ibm_architecture/scoring/`. The root synthetic policy (`policy/frozen_policy.json`, `policy/router.py`, `policy/governor.py`, `policy/baselines.py`) and historical canonical results (`results/results.json`, `results/pre_eval_freeze_record.json`) remain strictly untouched and read-only.
2. **Deterministic Python Decision Boundaries (`SCOR-01`, Master Spec § I):** All triage actions (`FRAUD_ALERT`, `MANUAL_REVIEW`, `ROUTINE`, `DEFERRED`), reason codes (`R0`–`R6`), baseline top-$B$ selections, and candidate P5 rankings are evaluated deterministically in Python. LLMs are advisory only (deferred to Phase 6) and are strictly prohibited from calculating authoritative risk probabilities or overriding routing decisions.
3. **Dual-Mode Capacity Governance (`SCOR-02`, Master Spec § I):** The `CapacityGovernor` explicitly distinguishes the original synthetic budget ($K = 130$ cases, derived from 2,000 cases at 6.525%) from the real-data IEEE-CIS benchmark workload ($B_{\text{frac}} = M \cdot p_{\text{prev}} \approx 0.05075 \implies \approx 5,994$ cases on the 118,108-case holdout). Saturation shunts excess escalations to `Action.DEFERRED` with `ReasonCode.R6_CAPACITY_DEFERRED`. Under no circumstances does capacity saturation silently reclassify a high-risk or ambiguous transaction as `ROUTINE`.
4. **Strict Ground-Truth Quarantine (`SCOR-03`, Master Spec § C2):** Feature extraction and scoring requests proactively reject target labels (`isFraud`, `target`, `label`, `true_label`) and raw transaction identifiers (`TransactionID`, `TransactionDT`) with `LeakageViolationError`. The final test partition (`split_hashes['test']`) is strictly quarantined from threshold tuning and policy selection.
5. **Fail-Closed Artifact Integrity (`SCOR-03`, Master Spec § H, § I):** `ScoringService` and `load_bundle()` cryptographically verify SHA-256 checksums of the Phase 4 model bundle components on startup, failing closed with `ArtifactNotFoundError` or `IncompatibleArtifactError` if any artifact is missing or altered.

---

## 2. Frozen IEEE-CIS Policy Configuration

The frozen reference policy (`integrations/ibm_architecture/policy/frozen_policy.py`) encapsulates the calibrated decision parameters:

| Parameter | Frozen Reference Value | Description |
|---|:---:|---|
| `status` | `"FROZEN_IEEE_CIS_V1"` | Explicit version tag distinguishing real-data from synthetic policy |
| `t_alert` | `0.084705` | High-risk alert threshold ($p \ge t_{\text{alert}} \implies \text{FRAUD\_ALERT}$) |
| `t_review` | `0.071002` | Intermediate-risk review threshold ($p \ge t_{\text{review}} \implies \text{MANUAL\_REVIEW}$) |
| `u_threshold` | `0.526773` | Epistemic model disagreement threshold ($u \ge u_{\text{threshold}} \implies \text{MANUAL\_REVIEW}$) |
| `disagreement_enabled` | `True` | Active second-stage disagreement triage |
| `disagreement_variant` | `"u2_rank_residual"` | Robust dispersion metric (median absolute deviation from median) |
| `novelty_enabled` | `False` | Third-stage novelty detection disabled in reference benchmark |
| `workload_multiples` | `[1.0, 1.5, 2.0, 3.0]` | Registered operational review workload sweeps |
| `primary_workload_multiple` | `1.5` | Primary benchmark workload multiple |
| `reference_prevalence` | `0.03383` | Measured fraud prevalence on test holdout partition |
| `target_budget` | `0.05075` | Effective 1.5x workload fraction ($1.5 \times 0.03383$) |
| `disagreement_weight_lambda` | `0.0` | P5 candidate ranking parameter ($\text{Score} = p + \lambda \cdot u$) |

---

## 3. Policy Adapters & Decision Logic

### 3.1 Triage Action Router (`RouterPolicyAdapter`)
Evaluates calibrated fraud probability $p$, robust disagreement $u_2$, and optional novelty $n$ against frozen policy thresholds.

**Deterministic Precedence Order:**
1. **Config / Signal Validation:** If $p$ is None, NaN, non-finite, or outside $[0, 1]$, fail closed to `(MANUAL_REVIEW, R0_SIGNAL_UNAVAILABLE)`.
2. **Disagreement Validation:** If disagreement is enabled and $u$ is None, NaN, or non-finite, fail closed to `(MANUAL_REVIEW, R0_SIGNAL_UNAVAILABLE)`.
3. **High-Risk Rule:** $p \ge t_{\text{alert}} \longrightarrow (\text{FRAUD\_ALERT}, \text{R1\_HIGH\_RISK})$.
   *Invariant:* A high-risk transaction can **never** produce `ROUTINE`.
4. **Intermediate-Risk Rule:** $p \ge t_{\text{review}} \longrightarrow (\text{MANUAL\_REVIEW}, \text{R2\_INTERMEDIATE\_RISK})$.
5. **Disagreement Rule:** $u \ge u_{\text{threshold}} \longrightarrow (\text{MANUAL\_REVIEW}, \text{R3\_MODEL\_DISAGREEMENT})$.
   *Invariant:* Disagreement represents epistemic uncertainty, not proof of fraud; it triggers `MANUAL_REVIEW`, **never** `FRAUD_ALERT`.
6. **Novelty Rule:** $n \ge n_{\text{threshold}} \longrightarrow (\text{MANUAL\_REVIEW}, \text{R4\_UNFAMILIAR\_INPUT})$.
7. **Reliable Low-Risk Default:** $(\text{ROUTINE}, \text{R5\_LOW\_RISK\_RELIABLE})$.

### 3.2 Mandatory Baseline B2 (`B2TopBudgetBaselineAdapter`)
Ranks a cohort of transactions descending by calibrated risk score $p$ and escalates the top fraction $B$ matching the review capacity budget:
$$K = \lfloor N \cdot B \rfloor$$
- Ranks cases using stable mergesort, breaking ties deterministically by transaction index or pseudonymous ID.
- Top $K$ transactions receive `(MANUAL_REVIEW, R2_INTERMEDIATE_RISK)`.
- Remaining $N - K$ transactions receive `(ROUTINE, R5_LOW_RISK_RELIABLE)`.
- Computes exact touched rate, caught fraud, recall at touched, and precision against held-out true labels for offline benchmarking.

### 3.3 Candidate P5 Policy (`P5CandidatePolicyAdapter`)
Evaluates the candidate ranking formulation:
$$\text{Score}_i = p_{\text{calibrated}, i} + \lambda \cdot u_{\text{signal}, i}$$

**Key Properties & Verification:**
- **Truth-in-Advertising ($\lambda = 0.0$):** In the frozen reference configuration, $\lambda = 0.0$. Under this setting, P5 ranks strictly by calibrated fraud risk $p$, identical to risk ranking. The adapter records $\lambda = 0.0$ and never represents a $\lambda=0$ run as disagreement-weighted prioritization.
- **Cohort-Relative Context Invariant:** P5 is strictly a cohort-level budget-ranking policy. Calling P5 on an individual transaction without cohort context raises `ValueError`, enforcing mathematical soundness.

---

## 4. Capacity Governance & Deferred Queue Segregation

The `CapacityGovernor` (`integrations/ibm_architecture/policy/governor.py`) regulates operational review volume to match finite analyst capacity while preventing high-risk clearance.

### 4.1 Synthetic vs. Real-Data Benchmark Workload

| Dimension | Synthetic Smoke Fixture | IEEE-CIS Real-Data Holdout |
|---|:---:|:---:|
| Total Test Cases ($N$) | 2,000 | 118,108 |
| Prevalence ($p_{\text{prev}}$) | 0.0435 | 0.03383 |
| Workload Formulation | Fixed $B = 0.06525$ ($1.5 \times p_{\text{prev}}$) | Multiples $M \in \{1.0, 1.5, 2.0, 3.0\} \times p_{\text{prev}}$ |
| Primary Capacity ($K$) | $\lfloor 2,000 \times 0.06525 \rfloor = \mathbf{130}\text{ cases}$ | $\lfloor 118,108 \times 0.05075 \rfloor \approx \mathbf{5,994}\text{ cases}$ |
| Touch Rate at Capacity | 6.50% | 5.08% |
| Consequence of Misapplying $K=130$ | Baseline configuration | **Disaster:** 0.11% touch rate; 99.89% false deferral |

To eliminate this failure mode, `CapacityGovernor` provides native dual-mode resolution:
- **Mode A (Fixed Count):** `capacity: int` — for small test cohorts and synthetic sanity checks.
- **Mode B (Budget Fraction):** `budget_fraction: float` — for benchmark evaluation on arbitrary cohort sizes, calculating $K = \lfloor N \cdot B_{\text{frac}} \rfloor$.

### 4.2 Deterministic Tie-Breaking & Segregation Protocol
When candidate escalations (`FRAUD_ALERT`, `MANUAL_REVIEW`) exceed quota $K$:
1. Candidates are sorted descending by priority score (calibrated risk $p$, or P5 score).
2. Ties are resolved deterministically using pseudonymous `transaction_id` ascending, or dataset index mergesort.
3. Ranks $1 \dots K$ are admitted against quota (`governor_status="admitted"`, `lane_rank` $1 \dots K$).
4. Ranks $> K$ are shunted to `Action.DEFERRED` with `ReasonCode.R6_CAPACITY_DEFERRED` (`governor_status="deferred"`, `lane_rank` $K+1 \dots$).
5. **No-Silent-Clearance Invariant:** Capacity exhaustion *never* reclassifies an escalation as `ROUTINE`. Deferred cases remain segregated in a dedicated review queue.

---

## 5. Deterministic Dynamic Scoring Service

The `ScoringService` (`integrations/ibm_architecture/scoring/service.py`) provides unified single-case and cohort batch scoring.

```
Incoming Request (Features + ID)
            │
            ▼
┌───────────────────────────────┐
│   check_feature_quarantine()  │ ── Prohibits isFraud, TransactionID, TransactionDT
└───────────────┬───────────────┘
                │
                ▼
┌───────────────────────────────┐
│   FeaturePipeline.transform   │ ── learned median imputation + ordinal encoding (391 features)
└───────────────┬───────────────┘
                │
                ▼
┌───────────────────────────────┐
│ Ensemble & Platt Calibration  │ ── produces raw probability, calibrated p, and member predictions
└───────────────┬───────────────┘
                │
                ▼
┌───────────────────────────────┐
│     Disagreement Signals      │ ── computes u (std dev) and u2 (rank residual)
└───────────────┬───────────────┘
                │
                ▼
┌───────────────────────────────┐
│     Policy Routing & Rules    │ ── RouterPolicyAdapter / B2 / P5
└───────────────┬───────────────┘
                │
                ▼
┌───────────────────────────────┐
│       CapacityGovernor        │ ── admits top-K; shunts excess to DEFERRED / R6
└───────────────┬───────────────┘
                │
                ▼
        ScoringResult / BatchScoringResult
```

### 5.1 Single-Case API Contract
- Method: `score_single(features: Dict[str, Any], transaction_id: Optional[str] = None, policy_name: str = "router") -> ScoringResult`
- Fails closed to `(MANUAL_REVIEW, R0_SIGNAL_UNAVAILABLE)` if input features produce non-finite transforms or model execution fails.
- Rejects P5 requests without cohort context with `ValueError`.
- Returns immutable `ScoringResult` with sanitized probabilities, uncertainty signals, deterministic actions, and cryptographic configuration hashes (`cfg_hash`).

### 5.2 Batch API Contract
- Method: `score_batch(df: pd.DataFrame, id_col: Optional[str] = None, policy_name: str = "router", capacity: Optional[int] = None, budget_fraction: Optional[float] = None) -> BatchScoringResult`
- Proactively segregates pseudonymous identifiers (`id_col`) before feature transformation.
- Evaluates chosen policy (`"router"`, `"b2"`, `"p5"`).
- Automatically applies `CapacityGovernor` when `policy_name="router"`.
- Returns immutable `BatchScoringResult` binding individual results and batch governance KPIs.

---

## 6. Verification Evidence & Requirements Compliance Matrix

### 6.1 Unit & Integration Test Suite (`tests/test_ibm_scoring.py`)
A comprehensive test suite of 16 tests was implemented and executed:

| Test Case | Scope & Verification Invariant | Result |
|---|---|:---:|
| `test_load_bundle_missing_manifest_fails_closed` | Missing manifest raises `ArtifactNotFoundError` | **PASS** |
| `test_load_bundle_missing_component_fails_closed` | Missing component raises `ArtifactNotFoundError` | **PASS** |
| `test_load_bundle_tampered_hash_fails_closed` | Tampered joblib raises `IncompatibleArtifactError` | **PASS** |
| `test_router_exact_threshold_boundaries` | Exact threshold cutoffs for $t_{\text{alert}}$, $t_{\text{review}}$, $u_{\text{threshold}}$ | **PASS** |
| `test_router_invalid_signals_fail_closed` | Missing, NaN, Inf, out-of-bounds inputs produce `MANUAL_REVIEW` / `R0` | **PASS** |
| `test_router_safety_invariants` | High risk never `ROUTINE`; disagreement never `FRAUD_ALERT` | **PASS** |
| `test_b2_top_b_exact_budget_matching` | Exact $\lfloor N \cdot B \rfloor$ top-risk cutoffs and offline metrics | **PASS** |
| `test_p5_candidate_formula_and_cohort_requirement` | P5 $\text{Score} = p + \lambda u$, $\lambda=0.0$ default, single-case error | **PASS** |
| `test_capacity_governor_dual_modes` | Fixed count $K=130$ and budget fraction $B_{\text{frac}}$ resolution | **PASS** |
| `test_capacity_governor_under_capacity` | All escalations admitted when requested $\le K$ | **PASS** |
| `test_capacity_governor_saturation_and_no_silent_clearance` | Excess shunted to `DEFERRED` / `R6`; never reclassified as `ROUTINE` | **PASS** |
| `test_capacity_governor_deterministic_tie_breaking` | Stable sorting on priority descending, pseudonymous ID ascending | **PASS** |
| `test_scoring_service_single_case` | End-to-end single transaction scoring and schema validation | **PASS** |
| `test_scoring_service_single_case_p5_raises_value_error` | P5 single-row rejection with informative error | **PASS** |
| `test_scoring_service_batch_with_capacity` | Batch scoring and capacity governor queue segregation | **PASS** |
| `test_scoring_service_leakage_quarantine_rejection` | Proactive rejection of `isFraud`, `TransactionID`, `TransactionDT` | **PASS** |

### 6.2 Full Regression Test Suite
- Executed full test suite: `.\.venv\Scripts\python.exe -m pytest -o "pythonpath=." tests/`
- Result: **160 passed**, 0 failed (**100% pass rate**).
- Baseline preservation: All 144 pre-existing tests pass with zero regressions.

### 6.3 Requirements Traceability Matrix

| Requirement | Description | Implementation Status | Evidence |
|---|---|:---:|---|
| **SCOR-01** | Deterministic policy adapters for router, B2 baseline, and P5 candidate | **VERIFIED** | [`integrations/ibm_architecture/policy/`](file:///c:/Users/himan/Downloads/zprject/integrations/ibm_architecture/policy/) (`router.py`, `baselines.py`, `p5_candidate.py`, `frozen_policy.py`) |
| **SCOR-02** | Strict capacity governance ($B=130$ vs. real workload $B_{\text{frac}}$) with deferred queue segregation | **VERIFIED** | [`integrations/ibm_architecture/policy/governor.py`](file:///c:/Users/himan/Downloads/zprject/integrations/ibm_architecture/policy/governor.py), `CapacityGovernor` |
| **SCOR-03** | Dynamic scoring service with feature transform, calibrated $p$, $u, u_2$, and ground-truth quarantine | **VERIFIED** | [`integrations/ibm_architecture/scoring/service.py`](file:///c:/Users/himan/Downloads/zprject/integrations/ibm_architecture/scoring/service.py), `ScoringService` |
