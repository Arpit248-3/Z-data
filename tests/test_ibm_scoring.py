"""SignalGate IBM Architecture Integration — Phase 5 Policy & Governance Tests.

Verifies:
- RouterPolicyAdapter decision logic and reason codes (R0-R6).
- BaselineB2PolicyAdapter top-B ranking and budget matching.
- CandidateP5PolicyAdapter scoring formula (p_cal + lambda * u) and cohort ranking.
- GovernedCapacityManager capacity quota ($B=130$) and R6 deferred queue shunting.
- DeterministicScoringService single-case and batch scoring with fail-closed safety and leakage rejection.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from integrations.ibm_architecture.exceptions import LeakageViolationError
from integrations.ibm_architecture.policy.adapters import (
    BaselineB2PolicyAdapter,
    CandidateP5PolicyAdapter,
    RouterPolicyAdapter,
)
from integrations.ibm_architecture.policy.governor import GovernedCapacityManager
from integrations.ibm_architecture.policy.service import DeterministicScoringService
from policy.router import Action, ReasonCode


# ---------------------------------------------------------------------------
# Router Policy Adapter Tests
# ---------------------------------------------------------------------------

def test_router_adapter_decision_logic() -> None:
    router = RouterPolicyAdapter()
    cfg = router.config

    t_alert = cfg["t_alert"]
    t_review = cfg["t_review"]
    u_thresh = cfg.get("u_threshold", 0.5)

    # 1. R1: High Risk
    act, rsn = router.route_single(p=t_alert + 0.01, u=0.1)
    assert act == Action.FRAUD_ALERT
    assert rsn == ReasonCode.R1_HIGH_RISK

    # 2. R2: Intermediate Risk
    act, rsn = router.route_single(p=(t_alert + t_review) / 2.0, u=0.1)
    assert act == Action.MANUAL_REVIEW
    assert rsn == ReasonCode.R2_INTERMEDIATE_RISK

    # 3. R3: High Disagreement (Never FRAUD_ALERT)
    act, rsn = router.route_single(p=t_review - 0.01, u=u_thresh + 0.1)
    assert act == Action.MANUAL_REVIEW
    assert rsn == ReasonCode.R3_MODEL_DISAGREEMENT

    # 4. R5: Low Risk, Low Disagreement
    act, rsn = router.route_single(p=t_review - 0.01, u=u_thresh - 0.1)
    assert act == Action.ROUTINE
    assert rsn == ReasonCode.R5_LOW_RISK_RELIABLE

    # 5. R0: Missing/invalid signal (fail closed)
    act_nan, rsn_nan = router.route_single(p=float("nan"), u=0.1)
    assert act_nan == Action.MANUAL_REVIEW
    assert rsn_nan == ReasonCode.R0_SIGNAL_UNAVAILABLE

    act_none, rsn_none = router.route_single(p=None)
    assert act_none == Action.MANUAL_REVIEW
    assert rsn_none == ReasonCode.R0_SIGNAL_UNAVAILABLE


def test_router_adapter_batch() -> None:
    router = RouterPolicyAdapter()
    p_arr = np.array([0.9, 0.075, 0.01, float("nan")])
    u_arr = np.array([0.1, 0.1, 0.8, 0.1])
    results = router.route_batch(p_arr, u_arr)

    assert len(results) == 4
    assert results[0][0] == Action.FRAUD_ALERT
    assert results[1][0] == Action.MANUAL_REVIEW
    assert results[2][0] == Action.MANUAL_REVIEW
    assert results[3][0] == Action.MANUAL_REVIEW
    assert results[3][1] == ReasonCode.R0_SIGNAL_UNAVAILABLE


# ---------------------------------------------------------------------------
# Baseline B2 Policy Adapter Tests
# ---------------------------------------------------------------------------

def test_baseline_b2_top_b() -> None:
    b2 = BaselineB2PolicyAdapter(default_budget=0.10)
    p_scores = np.array([0.05, 0.95, 0.20, 0.80, 0.10, 0.50, 0.30, 0.70, 0.40, 0.60])
    mask = b2.escalate_mask(p_scores, budget=0.20)

    # In a 10-element array with 20% budget, exactly 2 elements must be escalated
    assert int(mask.sum()) == 2
    # The two highest scores are 0.95 and 0.80 (indices 1 and 3)
    assert bool(mask[1]) is True
    assert bool(mask[3]) is True
    assert bool(mask[0]) is False


def test_baseline_b2_evaluate() -> None:
    b2 = BaselineB2PolicyAdapter()
    p_scores = np.array([0.1, 0.2, 0.8, 0.9])
    y_true = np.array([0, 0, 1, 1])
    metrics = b2.evaluate(p_scores, y_true, budget=0.50)

    assert metrics["policy"] == "Baseline_B2_Top_Budget"
    assert metrics["escalated_count"] == 2
    assert metrics["caught_fraud"] == 2
    assert metrics["recall_at_touched"] == 1.0


# ---------------------------------------------------------------------------
# Candidate P5 Policy Adapter Tests
# ---------------------------------------------------------------------------

def test_candidate_p5_scoring_and_routing() -> None:
    # Lambda = 0.0 (default pure risk ranking)
    p5_pure = CandidateP5PolicyAdapter(disagreement_weight_lambda=0.0)
    p_arr = np.array([0.1, 0.5, 0.8])
    u_arr = np.array([0.9, 0.1, 0.2])
    scores_pure = p5_pure.score(p_arr, u_arr)
    assert np.allclose(scores_pure, p_arr)

    # Lambda = 0.5
    p5_weighted = CandidateP5PolicyAdapter(disagreement_weight_lambda=0.5)
    scores_weighted = p5_weighted.score(p_arr, u_arr)
    expected = p_arr + 0.5 * u_arr
    assert np.allclose(scores_weighted, expected)

    # Cohort routing
    mask = p5_pure.route_cohort(p_arr, u_arr, budget_fraction=0.34)
    # 1 out of 3 escalated
    assert int(mask.sum()) == 1
    assert bool(mask[2]) is True  # highest score 0.8


# ---------------------------------------------------------------------------
# Governed Capacity Manager Tests
# ---------------------------------------------------------------------------

def test_governed_capacity_manager_quota_and_deferred_queue() -> None:
    governor = GovernedCapacityManager(capacity=3, priority_signal="p_cal")

    df = pd.DataFrame({
        "p_cal": [0.95, 0.85, 0.75, 0.65, 0.55, 0.05],
        "action": [
            Action.FRAUD_ALERT.value,
            Action.MANUAL_REVIEW.value,
            Action.MANUAL_REVIEW.value,
            Action.MANUAL_REVIEW.value,
            Action.MANUAL_REVIEW.value,
            Action.ROUTINE.value,
        ],
        "reason": [
            ReasonCode.R1_HIGH_RISK.value,
            ReasonCode.R2_INTERMEDIATE_RISK.value,
            ReasonCode.R2_INTERMEDIATE_RISK.value,
            ReasonCode.R2_INTERMEDIATE_RISK.value,
            ReasonCode.R2_INTERMEDIATE_RISK.value,
            ReasonCode.R5_LOW_RISK_RELIABLE.value,
        ],
    })

    governed_df, metrics = governor.govern_batch(df)

    # Total escalations requested = 5, capacity = 3
    # Top 3 admitted, remaining 2 deferred
    assert metrics["requested_escalations"] == 5
    assert metrics["capacity"] == 3
    assert metrics["touched_count"] == 3
    assert metrics["deferred_count"] == 2
    assert metrics["routine_count"] == 1

    # Check that deferred records carry reason R6_CAPACITY_DEFERRED
    deferred_rows = governed_df[governed_df["action"] == Action.DEFERRED.value]
    assert len(deferred_rows) == 2
    assert all(r == ReasonCode.R6_CAPACITY_DEFERRED.value for r in deferred_rows["reason"])

    # Verify that ROUTINE record remained unchanged
    routine_rows = governed_df[governed_df["action"] == Action.ROUTINE.value]
    assert len(routine_rows) == 1
    assert routine_rows.iloc[0]["reason"] == ReasonCode.R5_LOW_RISK_RELIABLE.value


# ---------------------------------------------------------------------------
# Deterministic Scoring Service Tests
# ---------------------------------------------------------------------------

def test_deterministic_scoring_service_single_case() -> None:
    service = DeterministicScoringService.create_default()
    assert service.execution_mode == "SYNTHETIC_SMOKE_ONLY"
    assert service.is_synthetic is True

    # Read row from fixture
    df_fixture = pd.read_csv("data/synthetic_smoke_fixture.csv", nrows=1)
    clean_row = df_fixture.drop(columns=["isFraud", "TransactionID", "TransactionDT"], errors="ignore").iloc[0].to_dict()

    res = service.score_single(clean_row)
    assert "decision_id" in res
    assert "p_raw" in res
    assert "p_cal" in res
    assert "u" in res
    assert "u2" in res
    assert "p_b2" in res
    assert "action" in res
    assert "reason" in res
    assert res["execution_mode"] == "SYNTHETIC_SMOKE_ONLY"
    assert res["benchmark_comparable"] is False
    assert res["real_data_training_status"] == "DEFERRED"


def test_deterministic_scoring_service_quarantine_rejection() -> None:
    service = DeterministicScoringService.create_default()
    leak_case = {"isFraud": 1, "TransactionAmt": 100.0}
    with pytest.raises(LeakageViolationError):
        service.score_single(leak_case)

    id_case = {"TransactionID": 99999, "TransactionAmt": 100.0}
    with pytest.raises(LeakageViolationError):
        service.score_single(id_case)


def test_deterministic_scoring_service_batch() -> None:
    service = DeterministicScoringService.create_default(capacity=5)
    df_fixture = pd.read_csv("data/synthetic_smoke_fixture.csv", nrows=10)
    clean_df = df_fixture.drop(columns=["isFraud", "TransactionID", "TransactionDT"], errors="ignore")

    out_df, metrics = service.score_batch(clean_df, enforce_capacity=True)
    assert len(out_df) == 10
    assert "action" in out_df.columns
    assert "reason" in out_df.columns
    assert "governor_status" in out_df.columns
    assert "capacity" in metrics
    assert metrics["capacity"] == 5
