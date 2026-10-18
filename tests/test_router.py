"""
SignalGate Phase 4 Tests — Decision Router & Capacity Governor
Covers:
1. Exact t_review and t_alert boundary handling.
2. Invalid p, u, n signals and invalid threshold configs.
3. Missing required signals and fail-closed R0 behavior.
4. High risk score never produces ROUTINE.
5. Excessive disagreement produces R3_MODEL_DISAGREEMENT review reason (not fraud alert).
6. Inactive novelty rules when novelty is disabled.
7. Explicitly skipped second-stage inference distinct from second-stage failure.
8. Governor overflow creates visible R6_CAPACITY_DEFERRED cases (never reclassified as ROUTINE).
9. Deterministic ranking and tie-breaking in governor.
10. Rejection of true labels (isFraud, true_label) in scoring and routing interfaces.
"""

import numpy as np
import pandas as pd
import pytest

from policy.router import (
    Action,
    ReasonCode,
    route,
    route_batch,
    validate_router_config,
)
from policy.governor import CapacityGovernor, govern_decisions


def test_router_exact_threshold_boundaries():
    cfg = {
        "t_alert": 0.80,
        "t_review": 0.30,
        "disagreement_enabled": False,
        "novelty_enabled": False,
    }

    # At exact alert boundary: p = 0.80 -> FRAUD_ALERT / R1_HIGH_RISK
    act, rsn = route(p=0.80, cfg=cfg)
    assert act == Action.FRAUD_ALERT
    assert rsn == ReasonCode.R1_HIGH_RISK

    # Slightly below alert boundary: p = 0.7999 -> MANUAL_REVIEW / R2_INTERMEDIATE_RISK
    act, rsn = route(p=0.7999, cfg=cfg)
    assert act == Action.MANUAL_REVIEW
    assert rsn == ReasonCode.R2_INTERMEDIATE_RISK

    # At exact review boundary: p = 0.30 -> MANUAL_REVIEW / R2_INTERMEDIATE_RISK
    act, rsn = route(p=0.30, cfg=cfg)
    assert act == Action.MANUAL_REVIEW
    assert rsn == ReasonCode.R2_INTERMEDIATE_RISK

    # Slightly below review boundary: p = 0.2999 -> ROUTINE / R5_LOW_RISK_RELIABLE
    act, rsn = route(p=0.2999, cfg=cfg)
    assert act == Action.ROUTINE
    assert rsn == ReasonCode.R5_LOW_RISK_RELIABLE


def test_router_invalid_inputs_and_fail_closed_r0():
    cfg = {"t_alert": 0.80, "t_review": 0.30}

    # None probability
    act, rsn = route(p=None, cfg=cfg)
    assert act == Action.MANUAL_REVIEW
    assert rsn == ReasonCode.R0_SIGNAL_UNAVAILABLE

    # NaN probability
    act, rsn = route(p=np.nan, cfg=cfg)
    assert act == Action.MANUAL_REVIEW
    assert rsn == ReasonCode.R0_SIGNAL_UNAVAILABLE

    # Infinite probability
    act, rsn = route(p=np.inf, cfg=cfg)
    assert act == Action.MANUAL_REVIEW
    assert rsn == ReasonCode.R0_SIGNAL_UNAVAILABLE

    # Out of bounds probability (> 1.0 or < 0.0)
    act, rsn = route(p=1.05, cfg=cfg)
    assert act == Action.MANUAL_REVIEW
    assert rsn == ReasonCode.R0_SIGNAL_UNAVAILABLE

    act, rsn = route(p=-0.01, cfg=cfg)
    assert act == Action.MANUAL_REVIEW
    assert rsn == ReasonCode.R0_SIGNAL_UNAVAILABLE


def test_router_invalid_threshold_configurations():
    # t_review >= t_alert
    bad_cfg_1 = {"t_alert": 0.50, "t_review": 0.60}
    is_valid, errors = validate_router_config(bad_cfg_1)
    assert not is_valid
    act, rsn = route(p=0.20, cfg=bad_cfg_1)
    assert act == Action.MANUAL_REVIEW
    assert rsn == ReasonCode.R0_SIGNAL_UNAVAILABLE

    # Missing t_alert
    bad_cfg_2 = {"t_review": 0.20}
    is_valid, _ = validate_router_config(bad_cfg_2)
    assert not is_valid
    act, rsn = route(p=0.10, cfg=bad_cfg_2)
    assert act == Action.MANUAL_REVIEW
    assert rsn == ReasonCode.R0_SIGNAL_UNAVAILABLE


def test_high_risk_score_never_produces_routine():
    # Even if disagreement is high or novelty is high, high risk must produce FRAUD_ALERT
    cfg = {
        "t_alert": 0.70,
        "t_review": 0.30,
        "disagreement_enabled": True,
        "u_threshold": 0.05,
        "novelty_enabled": True,
        "n_threshold": 0.50,
    }

    act, rsn = route(p=0.95, u=0.20, n=0.80, cfg=cfg)
    assert act == Action.FRAUD_ALERT
    assert rsn == ReasonCode.R1_HIGH_RISK
    assert act != Action.ROUTINE


def test_excessive_disagreement_produces_r3_review_not_fraud_alert():
    cfg = {
        "t_alert": 0.70,
        "t_review": 0.30,
        "disagreement_enabled": True,
        "u_threshold": 0.04,
    }

    # Low risk p = 0.15 (ordinarily routine), but excessive disagreement u = 0.06 >= 0.04
    act, rsn = route(p=0.15, u=0.06, cfg=cfg)
    assert act == Action.MANUAL_REVIEW
    assert rsn == ReasonCode.R3_MODEL_DISAGREEMENT
    assert act != Action.FRAUD_ALERT, "Disagreement alone is NOT proof of fraud!"


def test_novelty_rules_remain_inactive_when_novelty_disabled():
    cfg = {
        "t_alert": 0.70,
        "t_review": 0.30,
        "disagreement_enabled": False,
        "novelty_enabled": False, # Disabled
    }

    # Low risk p = 0.10 with high novelty n = 0.99
    act, rsn = route(p=0.10, n=0.99, cfg=cfg)
    assert act == Action.ROUTINE
    assert rsn == ReasonCode.R5_LOW_RISK_RELIABLE


def test_skipped_stage2_distinct_from_stage2_failure():
    cfg = {
        "t_alert": 0.70,
        "t_review": 0.30,
        "disagreement_enabled": True,
        "u_threshold": 0.05,
    }

    # Low risk p = 0.05, stage 2 intentionally skipped -> ROUTINE
    act_skip, rsn_skip = route(p=0.05, u=None, cfg=cfg, stage2_status="skipped")
    assert act_skip == Action.ROUTINE
    assert rsn_skip == ReasonCode.R5_LOW_RISK_RELIABLE

    # Low risk p = 0.05, stage 2 failed / unavailable -> MANUAL_REVIEW / R0
    act_fail, rsn_fail = route(p=0.05, u=None, cfg=cfg, stage2_status="failed")
    assert act_fail == Action.MANUAL_REVIEW
    assert rsn_fail == ReasonCode.R0_SIGNAL_UNAVAILABLE

    act_unavail, rsn_unavail = route(p=0.05, u=None, cfg=cfg, stage2_status="unavailable")
    assert act_unavail == Action.MANUAL_REVIEW
    assert rsn_unavail == ReasonCode.R0_SIGNAL_UNAVAILABLE


def test_governor_overflow_creates_r6_deferred_cases():
    # 5 transactions, capacity = 2
    df = pd.DataFrame({
        "action": ["FRAUD_ALERT", "FRAUD_ALERT", "MANUAL_REVIEW", "MANUAL_REVIEW", "ROUTINE"],
        "reason": ["R1_HIGH_RISK", "R1_HIGH_RISK", "R2_INTERMEDIATE_RISK", "R3_MODEL_DISAGREEMENT", "R5_LOW_RISK_RELIABLE"],
        "p": [0.90, 0.85, 0.40, 0.20, 0.05],
        "id": ["T1", "T2", "T3", "T4", "T5"],
    })

    governor = CapacityGovernor(capacity=2, priority_col="p")
    gov_df, metrics = governor.govern(df, id_col="id")

    assert metrics["requested_escalations"] == 4
    assert metrics["admitted_alerts"] == 2
    assert metrics["admitted_reviews"] == 0
    assert metrics["deferred_count"] == 2
    assert metrics["routine_count"] == 1
    assert metrics["touched_count"] == 2
    assert metrics["touched_rate"] == 2 / 5

    # Check top 2 were admitted
    assert gov_df.loc[0, "governor_status"] == "admitted"
    assert gov_df.loc[1, "governor_status"] == "admitted"

    # Check ranks 3 and 4 were marked DEFERRED with R6_CAPACITY_DEFERRED
    assert gov_df.loc[2, "action"] == Action.DEFERRED.value
    assert gov_df.loc[2, "reason"] == ReasonCode.R6_CAPACITY_DEFERRED.value
    assert gov_df.loc[2, "governor_status"] == "deferred"

    assert gov_df.loc[3, "action"] == Action.DEFERRED.value
    assert gov_df.loc[3, "reason"] == ReasonCode.R6_CAPACITY_DEFERRED.value
    assert gov_df.loc[3, "governor_status"] == "deferred"

    # Crucial rule: Deferred cases must NEVER become ROUTINE
    assert (gov_df.loc[[2, 3], "action"] != Action.ROUTINE.value).all()


def test_governor_deterministic_ranking_and_tie_breaking():
    # 3 candidates with identical p = 0.50, capacity = 1
    df = pd.DataFrame({
        "action": ["MANUAL_REVIEW", "MANUAL_REVIEW", "MANUAL_REVIEW"],
        "reason": ["R2_INTERMEDIATE_RISK"] * 3,
        "p": [0.50, 0.50, 0.50],
        "id": ["T_300", "T_100", "T_200"],
    })

    # Secondary tie-breaking on id ascending should admit T_100
    gov_df, metrics = govern_decisions(df, capacity=1, priority_col="p", id_col="id")
    admitted = gov_df[gov_df["governor_status"] == "admitted"]
    assert len(admitted) == 1
    assert admitted.iloc[0]["id"] == "T_100"


def test_route_batch_rejects_ground_truth_labels():
    P = [0.1, 0.5, 0.9]
    cfg = {"t_alert": 0.8, "t_review": 0.4}

    with pytest.raises(ValueError, match="LEAKAGE VIOLATION"):
        route_batch(P=P, cfg=cfg, true_label=[0, 1, 1])

    with pytest.raises(ValueError, match="LEAKAGE VIOLATION"):
        route_batch(P=P, cfg=cfg, isFraud=[0, 1, 1])
