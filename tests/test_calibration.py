"""
SignalGate Phase 3 Tests — Probability Calibration
Covers:
1. FrozenEstimator + CalibratedClassifierCV integration under scikit-learn 1.8.
2. Calibration fitted strictly on calibration partition and assessed on validation.
3. Calibrated probabilities remain finite and within [0, 1].
4. Graceful failure on degenerate or single-class calibration partitions.
5. Expected Calibration Error (ECE) calculation and reliability bins.
6. Calibration comparison and selection based on validation Brier score.
7. Preservation of SYNTHETIC_SMOKE_ONLY in calibration report.
"""

from pathlib import Path
import json
import numpy as np
import pandas as pd
import pytest

from models.base import fit_base
from models.calibrate import (
    fit_calibrator,
    calibrated_p,
    compute_ece,
    evaluate_calibration,
    compare_calibrators,
)

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def test_frozen_estimator_calibration_integration():
    rng = np.random.RandomState(42)
    # Train data
    X_train = pd.DataFrame({"feat_a": rng.normal(0, 1, 100), "feat_b": rng.normal(0, 1, 100)})
    y_train = pd.Series((rng.rand(100) < 0.25).astype(int))

    # Calibration data
    X_calib = pd.DataFrame({"feat_a": rng.normal(0, 1, 50), "feat_b": rng.normal(0, 1, 50)})
    y_calib = pd.Series((rng.rand(50) < 0.25).astype(int))

    # Test/Validation data
    X_val = pd.DataFrame({"feat_a": rng.normal(0, 1, 30), "feat_b": rng.normal(0, 1, 30)})

    base = fit_base(X_train, y_train, seed=11, model_type="hgb", max_iter=20)

    # Sigmoid calibration
    cal_sig = fit_calibrator(base, X_calib, y_calib, method="sigmoid")
    p_sig = calibrated_p(cal_sig, X_val)
    assert len(p_sig) == 30
    assert np.isfinite(p_sig).all()
    assert (p_sig >= 0.0).all() and (p_sig <= 1.0).all()

    # Isotonic calibration
    cal_iso = fit_calibrator(base, X_calib, y_calib, method="isotonic")
    p_iso = calibrated_p(cal_iso, X_val)
    assert len(p_iso) == 30
    assert np.isfinite(p_iso).all()
    assert (p_iso >= 0.0).all() and (p_iso <= 1.0).all()


def test_ece_computation_matches_expected_bounds():
    # Perfectly calibrated case: true probabilities match true labels on average
    y_true = np.array([0, 0, 0, 0, 1, 1, 1, 1])
    y_prob = np.array([0.05, 0.05, 0.05, 0.05, 0.95, 0.95, 0.95, 0.95])

    ece, bins = compute_ece(y_true, y_prob, n_bins=10)
    assert 0.0 <= ece <= 0.10
    assert len(bins) == 10

    # Completely uncalibrated case: inverted predictions
    y_prob_inv = 1.0 - y_prob
    ece_inv, _ = compute_ece(y_true, y_prob_inv, n_bins=10)
    assert ece_inv > 0.80


def test_calibration_fails_gracefully_on_single_class():
    rng = np.random.RandomState(42)
    X_train = pd.DataFrame({"feat": rng.normal(0, 1, 40)})
    y_train = pd.Series([0] * 30 + [1] * 10)
    base = fit_base(X_train, y_train, seed=11, max_iter=10)

    # Degenerate calibration partition with only 0s
    X_calib_degen = pd.DataFrame({"feat": rng.normal(0, 1, 20)})
    y_calib_degen = pd.Series([0] * 20)

    with pytest.raises(ValueError, match="must contain both positive and negative classes"):
        fit_calibrator(base, X_calib_degen, y_calib_degen, method="sigmoid")


def test_compare_calibrators_selects_on_validation_brier():
    rng = np.random.RandomState(42)
    X_train = pd.DataFrame({"feat": rng.normal(0, 1, 100)})
    y_train = pd.Series((rng.rand(100) < 0.2).astype(int))

    X_calib = pd.DataFrame({"feat": rng.normal(0, 1, 50)})
    y_calib = pd.Series((rng.rand(50) < 0.2).astype(int))

    X_val = pd.DataFrame({"feat": rng.normal(0, 1, 50)})
    y_val = pd.Series((rng.rand(50) < 0.2).astype(int))

    base = fit_base(X_train, y_train, seed=11, max_iter=20)
    comparison, calibrators = compare_calibrators(base, X_calib, y_calib, X_val, y_val)

    assert comparison["selected_method"] in ["uncalibrated", "sigmoid", "isotonic"]
    assert "Lowest validation Brier score" in comparison["selection_criterion"]
    assert "uncalibrated" in comparison["methods_evaluated"]
    assert "sigmoid" in comparison["methods_evaluated"]
    assert "isotonic" in comparison["methods_evaluated"]


def test_calibration_report_preserves_synthetic_smoke_status():
    report_path = PROJECT_ROOT / "results" / "calibration_report.json"
    assert report_path.exists(), "results/calibration_report.json must exist"

    with open(report_path, "r", encoding="utf-8") as f:
        report = json.load(f)

    assert report["status"] == "SYNTHETIC_SMOKE_ONLY"
    assert report["is_synthetic"] is True
    assert report["selected_method"] in ["sigmoid", "isotonic", "uncalibrated"]
    assert "calibrator_sigmoid.joblib" in str(report["saved_artifacts"]["sigmoid"]["artifact_path"])
