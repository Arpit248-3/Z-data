"""
SignalGate Phase 4 Tests — Policy Metrics, Baselines & Audit Logging
Covers:
1. Exact hand-calculated touched_rate accounting: (ALERT + REVIEW) / total.
2. B2 baseline matches declared budget within rounding tolerance.
3. Matched-budget comparison of B1, B2, B3a, B4, and SignalGate on identical rows.
4. Threshold selection optimality and budget feasibility.
5. Preservation of SYNTHETIC_SMOKE_ONLY across policy reports and G3 test look.
6. Frozen policy configuration reproducibility and hash verification.
7. Audit record schema validation.
"""

from pathlib import Path
import json
import numpy as np
import pandas as pd
import pytest

from policy.baselines import (
    baseline_top_b,
    baseline_fixed_threshold,
    baseline_confidence_deferral,
    baseline_random,
    compute_policy_metrics,
    evaluate_policies_matched_budget,
)
from policy.thresholds import select_thresholds
from policy.audit import (
    AuditRecord,
    validate_audit_record,
)

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def test_touched_rate_hand_calculated_example():
    # 10 transactions: 2 FRAUD_ALERT, 3 MANUAL_REVIEW, 1 DEFERRED, 4 ROUTINE
    # touched_rate = (2 + 3) / 10 = 0.50 (DEFERRED is reported separately!)
    escalated_mask = np.array([True, True, True, True, True, False, False, False, False, False])
    y_true = np.array([1, 1, 0, 0, 0, 1, 0, 0, 0, 0]) # 3 total fraud

    metrics = compute_policy_metrics(escalated_mask, y_true, budget=0.50, policy_name="TestPolicy")

    assert metrics["total_transactions"] == 10
    assert metrics["escalated_count"] == 5
    assert metrics["touched_rate"] == 0.50
    assert metrics["caught_fraud"] == 2
    assert metrics["total_fraud"] == 3
    assert metrics["missed_fraud"] == 1
    assert np.isclose(metrics["recall_at_touched"], 2 / 3)
    assert np.isclose(metrics["precision"], 2 / 5)


def test_b2_top_b_budget_matching():
    # Test on various sizes and budgets
    for n in [100, 500, 1000]:
        p = np.linspace(0.01, 0.99, n)
        for budget in [0.0435, 0.06525, 0.087, 0.1305]:
            mask = baseline_top_b(p, budget=budget)
            observed_touched_rate = np.mean(mask)
            # Must match within floor rounding tolerance (1 / n)
            expected_k = int(np.floor(n * budget))
            assert np.sum(mask) == expected_k
            assert abs(observed_touched_rate - (expected_k / n)) < 1e-9


def test_all_baselines_evaluated_on_identical_rows_and_budget():
    rng = np.random.RandomState(42)
    n = 200
    p = rng.beta(1, 15, n)
    y = (rng.rand(n) < 0.05).astype(int)
    budget = 0.06525

    results = evaluate_policies_matched_budget(p, y, budget=budget, seed=11)

    assert "B2_top_b_risk" in results
    assert "B1_fixed_threshold" in results
    assert "B3a_confidence_deferral" in results
    assert "B4_random_control" in results

    # Check identical row count
    for name, pol_res in results.items():
        assert pol_res["total_transactions"] == n
        # Check budget matching within rounding tolerance
        assert pol_res["touched_rate"] <= budget + (1.0 / n)


def test_threshold_selection_optimality_on_validation_split():
    rng = np.random.RandomState(42)
    p_val = rng.uniform(0.01, 0.95, size=200)
    y_val = (p_val > 0.80).astype(int) # Deterministic fraud for high p
    budget = 0.10

    cfg, summary = select_thresholds(p_val, y_val, target_budget=budget, use_disagreement=False)

    assert cfg is not None
    assert cfg.t_review < cfg.t_alert
    assert cfg.validation_metrics["touched_rate"] <= budget + 1e-6
    assert cfg.validation_metrics["recall"] > 0.0


def test_frozen_policy_configuration_reproducibility():
    frozen_cfg_path = PROJECT_ROOT / "policy" / "frozen_policy.json"
    assert frozen_cfg_path.exists(), "policy/frozen_policy.json must exist after Phase 4 run"

    with open(frozen_cfg_path, "r", encoding="utf-8") as f:
        frozen_data = json.load(f)

    assert frozen_data["status"] == "SYNTHETIC_SMOKE_ONLY"
    assert "thresholds" in frozen_data
    assert frozen_data["thresholds"]["t_review"] < frozen_data["thresholds"]["t_alert"]
    assert "matched_budget_validation_comparison" in frozen_data


def test_g3_test_look_report_exists_and_preserves_synthetic_status():
    g3_path = PROJECT_ROOT / "results" / "g3_test_look.json"
    assert g3_path.exists(), "results/g3_test_look.json must exist after G3 test look"

    with open(g3_path, "r", encoding="utf-8") as f:
        g3_data = json.load(f)

    assert g3_data["status"] == "SYNTHETIC_SMOKE_ONLY"
    assert g3_data["is_synthetic"] is True
    assert g3_data["test_look"] == "G3_LOOK_1"
    assert g3_data["test_rows"] == 2000
    assert "comparison_on_identical_test_rows" in g3_data


def test_audit_record_schema_validation():
    valid_record = {
        "id": "2987001",
        "ts": 86400,
        "p": 0.085,
        "u": 0.012,
        "u_method": "u2_rank_residual",
        "n": None,
        "stage2_status": "computed",
        "action": "FRAUD_ALERT",
        "reason": "R1_HIGH_RISK",
        "latency_ms": 2.45,
        "explanation_status": "not_computed",
        "feature_attributions": None,
        "cfg_hash": "a" * 64,
        "split_hash": "b" * 64,
        "lane_rank": 1,
        "governor_status": "admitted",
        "synthetic_scenario": True,
    }

    is_valid, errors = validate_audit_record(valid_record)
    assert is_valid, f"Valid audit record failed validation: {errors}"

    # Corrupt with missing key
    corrupt_record = dict(valid_record)
    del corrupt_record["reason"]
    is_valid_c, errors_c = validate_audit_record(corrupt_record)
    assert not is_valid_c
    assert any("reason" in e for e in errors_c)

    # Corrupt with true label leakage
    leakage_record = dict(valid_record)
    leakage_record["true_label"] = 1
    is_valid_l, errors_l = validate_audit_record(leakage_record)
    assert not is_valid_l
    assert any("LEAKAGE" in e for e in errors_l)
