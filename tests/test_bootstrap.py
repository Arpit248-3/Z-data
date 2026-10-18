"""Tests for SignalGate Paired Bootstrap Module."""

import numpy as np
import pytest
from eval.bootstrap import paired_bootstrap, paired_bootstrap_tuple


def test_paired_bootstrap_hand_calculated_toy():
    # 10 rows, 4 frauds at indices 0, 1, 2, 3
    y_true = [1, 1, 1, 1, 0, 0, 0, 0, 0, 0]
    # Policy A catches 3 frauds (indices 0, 1, 2) -> recall = 3/4 = 0.75
    mask_a = [True, True, True, False, False, False, False, False, False, False]
    # Policy B catches 2 frauds (indices 0, 1) -> recall = 2/4 = 0.50
    mask_b = [True, True, False, False, False, False, False, False, False, False]

    res = paired_bootstrap(
        y_true=y_true,
        mask_a=mask_a,
        mask_b=mask_b,
        n_resamples=500,
        seed=42,
    )

    # Point estimate must be exactly +0.25 (0.75 - 0.50)
    assert res["point_estimate_diff"] == pytest.approx(0.25, abs=1e-5)
    assert res["policy_a_observed"] == pytest.approx(0.75, abs=1e-5)
    assert res["policy_b_observed"] == pytest.approx(0.50, abs=1e-5)
    assert res["n_resamples_requested"] == 500
    assert res["n_resamples_valid"] > 400
    assert "ci_lower" in res
    assert "ci_upper" in res
    assert res["ci_lower"] <= res["ci_upper"]


def test_paired_bootstrap_inconclusive_when_identical():
    # When both policies are identical, point estimate must be 0 and CI must span 0
    y_true = [1, 1, 1, 0, 0, 0, 0, 0]
    mask = [True, False, True, False, False, False, False, False]

    res = paired_bootstrap(
        y_true=y_true,
        mask_a=mask,
        mask_b=mask,
        n_resamples=200,
        seed=11,
    )

    assert res["point_estimate_diff"] == 0.0
    assert res["ci_lower"] <= 0.0 <= res["ci_upper"]
    assert res["is_conclusive"] is False
    assert "Inconclusive" in res["conclusion"]


def test_paired_bootstrap_conclusive_when_strictly_superior():
    # Construct distinct case: A catches all 20 frauds, B catches 0
    rng = np.random.default_rng(42)
    y_true = np.array([1] * 20 + [0] * 80)
    mask_a = np.array([True] * 20 + [False] * 80)
    mask_b = np.array([False] * 100)

    res = paired_bootstrap(
        y_true=y_true,
        mask_a=mask_a,
        mask_b=mask_b,
        n_resamples=300,
        seed=42,
    )

    assert res["point_estimate_diff"] == 1.0
    assert res["ci_lower"] > 0.0
    assert res["is_conclusive"] is True
    assert "Statistically distinguishable" in res["conclusion"]


def test_paired_bootstrap_tuple_signature():
    y_true = [1, 1, 0, 0]
    mA = [True, False, False, False]
    mB = [False, False, False, False]

    diff, lo, hi = paired_bootstrap_tuple(y_true, mA, mB, n_resamples=100, seed=42)
    assert isinstance(diff, float)
    assert isinstance(lo, float)
    assert isinstance(hi, float)
    assert lo <= hi
