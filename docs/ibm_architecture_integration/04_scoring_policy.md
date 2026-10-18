# SignalGate IBM Architecture Integration — Phase 5: Dynamic Scoring, Baselines, Frozen Policy & Capacity Governance

**Governing Specification:** `docs/ibm_architecture_integration_master_spec.md` § D, § I  
**Active Execution Mode:** `SYNTHETIC_SMOKE_ONLY`  
**Real-Data Training Status:** `DEFERRED`  
**Benchmark Comparable:** `false`  
**Review Capacity Quota:** $B = 130$ cases (target budget fraction $6.525\%$)  
**Last Updated:** 2026-10-18  

---

## 1. Executive Summary & Policy Architecture

Phase 5 implements the multi-policy decision-support layer, deterministic triage router, comparison baselines, Candidate P5 policy adapter, operational review capacity governor ($B=130$), and production deterministic scoring service within the isolated namespace `integrations/ibm_architecture/policy/`.

All policy rules, reason codes, threshold evaluations, and capacity accounting execute deterministically in Python backend code without LLM interference or non-deterministic floating-point drift.

---

## 2. Multi-Policy Triage Adapters

### 2.1 Decision Router (`RouterPolicyAdapter`)
Evaluates transactions through a deterministic precedence hierarchy against frozen thresholds from `policy/frozen_policy.json`:
- $t_{\text{alert}} = 0.084705$ (High-risk escalation threshold)
- $t_{\text{review}} = 0.071002$ (Intermediate-risk review threshold)
- $u_{\text{threshold}} = 0.526773$ (Epistemic disagreement escalation threshold)

| Reason Code | Name | Trigger Condition | Action Lane | Safeguard Invariant |
|---|---|---|:---:|---|
| **R0** | `R0_SIGNAL_UNAVAILABLE` | Missing, NaN, or non-finite inputs | `MANUAL_REVIEW` | Fails closed; never defaults to `ROUTINE`. |
| **R1** | `R1_HIGH_RISK` | $p_{\text{cal}} \ge t_{\text{alert}}$ | `FRAUD_ALERT` | Can NEVER produce `ROUTINE`. |
| **R2** | `R2_INTERMEDIATE_RISK` | $t_{\text{review}} \le p_{\text{cal}} < t_{\text{alert}}$ | `MANUAL_REVIEW` | High probability ambiguity requires human eyes. |
| **R3** | `R3_MODEL_DISAGREEMENT` | $u_2 \ge u_{\text{threshold}}$ and $p < t_{\text{review}}$ | `MANUAL_REVIEW` | Disagreement is uncertainty, NOT proof of fraud; never produces `FRAUD_ALERT`. |
| **R4** | `R4_UNFAMILIAR_INPUT` | Novelty signal triggered (if enabled) | `MANUAL_REVIEW` | Out-of-distribution input routed to review. |
| **R5** | `R5_LOW_RISK_RELIABLE` | $p < t_{\text{review}}$ and $u_2 < u_{\text{threshold}}$ | `ROUTINE` | Confidently low-risk; automated clearance. |
| **R6** | `R6_CAPACITY_DEFERRED` | Candidate escalation exceeds capacity $B$ | `DEFERRED` | Excess volume shunted to hold; NEVER converts to `ROUTINE`. |

### 2.2 Baseline B2 Policy Adapter (`BaselineB2PolicyAdapter`)
- Mandatory comparator representing conventional risk-score ranking without epistemic disagreement.
- Ranks transactions descending by risk score $p$ and escalates the top fraction $B = \text{budget}$ (derived via stable `mergesort` on $-p$).
- Provides exact touched-rate matching and holdout fraud recall evaluation.

### 2.3 Candidate P5 Policy Adapter (`CandidateP5PolicyAdapter`)
- Evaluates candidate triage priority formula:
  $$\text{score}(x) = p_{\text{calibrated}}(x) + \lambda \cdot u_2(x)$$
- **Default Parameter:** $\lambda = 0.0$ in compliance with Master Spec § D (pure calibrated risk ranking without fabricated disagreement weighting).
- Preserves $\lambda > 0$ evaluation capability for controlled research sweeps.
- Assigns reviews via cohort-level budget ranking with deterministic tie-breaking.

---

## 3. Operational Review Capacity Governance

Implemented in `GovernedCapacityManager`:
- **Primary Operational Quota:** $B = 130$ cases (realized $6.50\%$ touched rate on 2,000-case test partition, derived from $6.525\%$ target budget parameter).
- **Candidate Triage:**
  1. Accepts candidate escalations (`FRAUD_ALERT`, `MANUAL_REVIEW`) from router.
  2. Ranks candidates descending by calibrated risk score $p_{\text{cal}}$ with stable index tie-breaking.
  3. Admits top $K$ candidates against capacity quota (`governor_status: "admitted"`, `lane_rank: 1..K`).
  4. Shunts remaining candidate escalations to `Action.DEFERRED` / `ReasonCode.R6_CAPACITY_DEFERRED` (`governor_status: "deferred"`, `lane_rank: null`).
  5. **Non-Negotiable Invariant:** Deferred cases can NEVER silently convert to `ROUTINE` or disappear from audit logs.
  6. Exact touched-rate accounting:
     $$\text{touched\_rate} = \frac{\text{admitted\_alerts} + \text{admitted\_reviews}}{\text{total\_transactions}}$$

---

## 4. Production Deterministic Scoring Service

Implemented in `DeterministicScoringService`:
- Single-case scoring (`score_single`):
  - Converts input payload, verifies ground-truth quarantine, runs model inference, evaluates router logic, and assigns sandbox governor status.
  - Sub-50ms latency (measured typical: 4.8ms).
- Batch scoring (`score_batch`):
  - Evaluates complete transaction cohorts with full capacity governance and exact touched-rate metrics.
- Explicit Mode Metadata:
  `execution_mode: "SYNTHETIC_SMOKE_ONLY"`, `benchmark_comparable: false`, `real_data_training_status: "DEFERRED"`.

---

## 5. Requirements Compliance Matrix

| Requirement | Description | Status | Evidence |
|---|---|:---:|---|
| **SCOR-01** | Deterministic policy adapters for router, B2 baseline, and P5 candidate | **PASS** | `RouterPolicyAdapter`, `BaselineB2PolicyAdapter`, `CandidateP5PolicyAdapter` in `integrations/ibm_architecture/policy/adapters.py`. |
| **SCOR-02** | Capacity governor enforcing review quota ($B=130$) with deferred queue shunting | **PASS** | `GovernedCapacityManager` in `integrations/ibm_architecture/policy/governor.py`. Tested strictly bounding escalations and assigning R6. |
| **SCOR-03** | Deterministic scoring service with fail-closed safety and explicit metadata | **PASS** | `DeterministicScoringService` in `integrations/ibm_architecture/policy/service.py`. Sub-50ms inference, quarantine rejection, mode stamping. |

---

## 6. Test Verification Results

- `tests/test_ibm_scoring.py`: **9 / 9 PASS (100%)** in 3.26s
- Total passing integration tests: **59 / 59 PASS**
- Full backend pytest suite: **168 / 168 PASS**
