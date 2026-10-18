"""Tests for SignalGate Scenario Builders, Drift Monitoring, Segments, and Value Model."""

import numpy as np
import pandas as pd
import pytest

from data.scenario_builders import build_all_scenarios, build_scenario_s3
from eval.drift import calculate_psi, calculate_feature_drift, monitor_dataset_drift
from eval.segments import analyze_segment_escalation, analyze_all_segments
from eval.value_model import ScenarioValueModel
from eval.latency import time_calls


def test_scenario_builders_deterministic_reproducibility():
    # Construct small synthetic test dataframe
    rng = np.random.default_rng(42)
    n = 200
    df = pd.DataFrame({
        "TransactionID": list(range(1000, 1000 + n)),
        "TransactionDT": list(range(86400, 86400 + n * 10, 10)),
        "TransactionAmt": rng.uniform(10.0, 500.0, size=n),
        "isFraud": [1 if i % 20 == 0 else 0 for i in range(n)],
        "ProductCD": ["W" if i % 2 == 0 else "C" for i in range(n)],
        "card4": ["visa" if i % 3 == 0 else "mastercard" for i in range(n)],
        "V1": rng.normal(0, 1, size=n),
        "V2": rng.normal(0, 1, size=n),
        "D1": rng.uniform(0, 100, size=n),
    })

    scenarios = build_all_scenarios(df, seed=42)
    assert "S0" in scenarios
    assert "S3" in scenarios
    assert "S1" in scenarios

    # S0 preserves rows and fraud count
    assert scenarios["S0"]["sample_count"] == n
    assert scenarios["S0"]["fraud_count"] == 10
    assert scenarios["S0"]["status"] == "SYNTHETIC_SMOKE_ONLY"

    # S3 deterministic reproducibility
    s3_a = build_scenario_s3(df, seed=42)
    s3_b = build_scenario_s3(df, seed=42)
    assert s3_a["scenario_hash"] == s3_b["scenario_hash"]
    assert s3_a["status"] == "SYNTHETIC_SHIFT"
    assert "TransactionAmt" in s3_a["metadata"]["shifted_features"]


def test_psi_stable_vs_significant_drift():
    rng = np.random.default_rng(42)
    # Reference distribution
    ref = rng.normal(0.0, 1.0, size=1000)

    # Identical distribution -> stable (PSI < 0.10)
    act_identical = rng.normal(0.0, 1.0, size=1000)
    psi_stable = calculate_psi(ref, act_identical)
    assert psi_stable["category"] == "stable"
    assert psi_stable["psi"] < 0.10

    # Severely shifted distribution -> significant drift (PSI > 0.20)
    act_shifted = rng.normal(2.5, 1.0, size=1000)
    psi_shifted = calculate_psi(ref, act_shifted)
    assert psi_shifted["category"] == "significant_drift"
    assert psi_shifted["psi"] > 0.20


def test_ks_statistic_computation():
    rng = np.random.default_rng(42)
    ref = rng.normal(0.0, 1.0, size=500)
    act = rng.normal(1.5, 1.0, size=500)

    drift = calculate_feature_drift(ref, act, feature_name="test_feature")
    assert drift["feature"] == "test_feature"
    assert drift["ks_statistic"] is not None
    assert drift["ks_pvalue"] is not None
    assert drift["ks_statistic"] > 0.2
    assert drift["ks_pvalue"] < 0.001


def test_segment_escalation_safe_handling():
    # Segments with rare and zero-count categories
    segments = ["W", "W", "W", "W", "C", "C", "RARE_GRP", "MISSING_GRP"]
    actions = [
        "FRAUD_ALERT", "ROUTINE", "ROUTINE", "ROUTINE",
        "MANUAL_REVIEW", "ROUTINE",
        "DEFERRED", "ROUTINE"
    ]
    y_true = [1, 0, 0, 0, 0, 0, 0, 0]

    rep = analyze_segment_escalation(
        segment_series=segments,
        actions=actions,
        y_true=y_true,
        segment_name="ProductCD",
        min_sample_size=2,
    )

    assert rep["total_transactions"] == 8
    assert rep["unique_groups"] == 4
    # Ensure no exception and disparity ratio handles rare groups
    assert "disclaimer" in rep
    assert "Demographic fairness" in rep["disclaimer"]


def test_scenario_value_model_hand_calculated():
    # 2 caught frauds @ $100 and $200 = $300.
    # Total touched = 4. Cost per review = $20 -> $80.
    # False alerts = 1. Friction cost = $30 -> $30.
    # Recovery rate = 0.90 -> gross prevented = 300 * 0.9 = $270.
    # Total costs = $80 + $30 = $110.
    # Net benefit = $270 - $110 = $160.
    y_true = [1, 1, 0, 0, 0]
    actions = [
        "FRAUD_ALERT",   # fraud caught ($100)
        "MANUAL_REVIEW",  # fraud caught ($200)
        "FRAUD_ALERT",   # false alert! ($50)
        "MANUAL_REVIEW",  # false review ($50)
        "ROUTINE",        # non-fraud ($50)
    ]
    amounts = [100.0, 200.0, 50.0, 50.0, 50.0]

    model = ScenarioValueModel(
        cost_per_review=20.0,
        friction_per_false_alert=30.0,
        recovery_rate=0.90,
    )
    res = model.evaluate(y_true, actions, amounts)

    outcomes = res["financial_outcomes_usd"]
    assert outcomes["gross_prevented_fraud_usd"] == 270.0
    assert outcomes["analyst_review_costs_usd"] == 80.0  # 4 touched * $20
    assert outcomes["customer_friction_costs_usd"] == 30.0  # 1 false alert * $30
    assert outcomes["total_triage_costs_usd"] == 110.0
    assert outcomes["scenario_net_benefit_usd"] == 160.0


def test_latency_percentile_calculation():
    # Test time_calls with simple dummy function
    def dummy_fn(x):
        return sum(x)

    res = time_calls(dummy_fn, input_data=[1, 2, 3], n_calls=100, warmup=10)
    assert res["n_calls"] == 100
    assert res["p50_ms"] <= res["p90_ms"] <= res["p95_ms"] <= res["p99_ms"]
    assert res["min_ms"] <= res["max_ms"]
