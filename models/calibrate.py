"""
SignalGate Probability Calibration Module
Implements:
1. Version-safe probability calibration using sklearn.frozen.FrozenEstimator and CalibratedClassifierCV.
2. Method comparison: Uncalibrated vs. Sigmoid (Platt scaling) vs. Isotonic calibration.
3. Calibration diagnostics: Brier score, Expected Calibration Error (ECE), and reliability diagram data.
4. Validation-only selection rule (minimizing validation Brier score).
5. Strict finite-probability bounds assertions in [0, 1].
"""

import math
from typing import Any, Dict, List, Optional, Tuple, Union
import numpy as np
import pandas as pd
from sklearn.calibration import CalibratedClassifierCV
from sklearn.frozen import FrozenEstimator
from sklearn.metrics import brier_score_loss, roc_auc_score

from models.base import raw_score


def compute_ece(
    y_true: Union[pd.Series, np.ndarray],
    y_prob: Union[pd.Series, np.ndarray],
    n_bins: int = 10,
) -> Tuple[float, List[Dict[str, Any]]]:
    """
    Compute Expected Calibration Error (ECE) and reliability diagram bins.

    Bins [0, 1] into n_bins equal-width intervals.
    ECE = sum_{b=1}^{B} (|B_b| / N) * |acc(B_b) - conf(B_b)|

    Returns:
    - ece: float score in [0, 1]
    - reliability_bins: List of dictionaries describing each bin's count, mean prediction, and observed rate.
    """
    y_arr = np.asarray(y_true, dtype=int)
    p_arr = np.asarray(y_prob, dtype=float)

    if len(y_arr) != len(p_arr):
        raise ValueError(f"Length mismatch: y_true ({len(y_arr)}) vs y_prob ({len(p_arr)})")

    n_samples = len(y_arr)
    if n_samples == 0:
        return 0.0, []

    bin_edges = np.linspace(0.0, 1.0, n_bins + 1)
    reliability_bins = []
    total_weighted_gap = 0.0

    for i in range(n_bins):
        lower = bin_edges[i]
        upper = bin_edges[i + 1]

        # Include upper boundary in the last bin
        if i == n_bins - 1:
            mask = (p_arr >= lower) & (p_arr <= upper)
        else:
            mask = (p_arr >= lower) & (p_arr < upper)

        bin_count = int(np.sum(mask))

        if bin_count > 0:
            mean_pred = float(np.mean(p_arr[mask]))
            actual_rate = float(np.mean(y_arr[mask]))
            gap = abs(actual_rate - mean_pred)
            total_weighted_gap += (bin_count / n_samples) * gap
        else:
            mean_pred = None
            actual_rate = None
            gap = None

        reliability_bins.append({
            "bin_idx": i,
            "range": [round(float(lower), 3), round(float(upper), 3)],
            "count": bin_count,
            "mean_pred": round(mean_pred, 5) if mean_pred is not None else None,
            "actual_rate": round(actual_rate, 5) if actual_rate is not None else None,
            "gap": round(gap, 5) if gap is not None else None,
        })

    ece = round(float(total_weighted_gap), 6)
    return ece, reliability_bins


def evaluate_calibration(
    y_true: Union[pd.Series, np.ndarray],
    y_prob: Union[pd.Series, np.ndarray],
    n_bins: int = 10,
) -> Dict[str, Any]:
    """
    Calculate full calibration metrics: Brier score, ECE, ROC-AUC, and reliability diagram bins.
    """
    y_arr = np.asarray(y_true, dtype=int)
    p_arr = np.asarray(y_prob, dtype=float)

    brier = round(float(brier_score_loss(y_arr, p_arr)), 6)
    ece, bins = compute_ece(y_arr, p_arr, n_bins=n_bins)

    try:
        auc = round(float(roc_auc_score(y_arr, p_arr)), 6)
    except Exception:
        auc = None

    return {
        "brier_score": brier,
        "ece": ece,
        "roc_auc": auc,
        "n_samples": len(y_arr),
        "fraud_count": int(np.sum(y_arr)),
        "reliability_bins": bins,
    }


def fit_calibrator(
    base_model: Any,
    X_calib: Union[pd.DataFrame, np.ndarray],
    y_calib: Union[pd.Series, np.ndarray],
    method: str = "sigmoid",
) -> Any:
    """
    Fit a probability calibrator on the designated calibration partition using FrozenEstimator.

    Parameters:
    - base_model: Pre-fitted base estimator (fitted on train partition).
    - X_calib: Feature matrix of the calibration partition.
    - y_calib: Ground-truth target labels of the calibration partition.
    - method: 'sigmoid' (Platt scaling) or 'isotonic'.

    Returns:
    - Fitted CalibratedClassifierCV instance.
    """
    if method not in ["sigmoid", "isotonic"]:
        raise ValueError(f"Unsupported calibration method '{method}'. Choose 'sigmoid' or 'isotonic'.")

    if len(X_calib) == 0 or len(y_calib) == 0:
        raise ValueError("Cannot fit calibrator on empty calibration data.")

    y_calib_arr = np.asarray(y_calib, dtype=int)
    if len(np.unique(y_calib_arr)) < 2:
        raise ValueError("Calibration partition must contain both positive and negative classes.")

    frozen_base = FrozenEstimator(base_model)
    calibrator = CalibratedClassifierCV(estimator=frozen_base, method=method)
    calibrator.fit(X_calib, y_calib_arr)

    return calibrator


def calibrated_p(calibrator: Any, X: Union[pd.DataFrame, np.ndarray]) -> np.ndarray:
    """
    Emit calibrated fraud probabilities P(Y=1) for feature matrix X.

    Returns:
    - 1D numpy array of probabilities bounded in [0, 1].
    """
    if len(X) == 0:
        return np.array([], dtype=float)

    if not hasattr(calibrator, "predict_proba"):
        raise AttributeError("Calibrator must provide predict_proba method.")

    probs = calibrator.predict_proba(X)

    if probs.ndim != 2 or probs.shape[1] < 2:
        raise ValueError(f"Unexpected calibrated predict_proba output shape: {probs.shape}")

    p = probs[:, 1]

    if not np.isfinite(p).all():
        raise ValueError("Calibrator emitted non-finite (NaN/Inf) probabilities.")

    if (p < 0.0).any() or (p > 1.0).any():
        raise ValueError(f"Calibrated probabilities out of bounds [0, 1]: min={p.min()}, max={p.max()}")

    return p


def compare_calibrators(
    base_model: Any,
    X_calib: Union[pd.DataFrame, np.ndarray],
    y_calib: Union[pd.Series, np.ndarray],
    X_val: Union[pd.DataFrame, np.ndarray],
    y_val: Union[pd.Series, np.ndarray],
    methods: Optional[List[str]] = None,
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """
    Compare uncalibrated, sigmoid, and isotonic calibration models strictly on validation data.

    Decision Rule:
    The candidate with the lowest validation Brier score is selected.
    If tied, the candidate with lower validation ECE is chosen.

    Returns:
    - report: Detailed comparative diagnostics on validation data.
    - calibrators: Dict mapping method name -> fitted calibrator instance (or None for uncalibrated).
    """
    if methods is None:
        methods = ["uncalibrated", "sigmoid", "isotonic"]

    results = {}
    calibrators = {}

    y_val_arr = np.asarray(y_val, dtype=int)

    # 1. Uncalibrated baseline
    p_uncal = raw_score(base_model, X_val)
    results["uncalibrated"] = {
        "method": "uncalibrated",
        "description": "Raw uncalibrated base model probabilities",
        "validation_metrics": evaluate_calibration(y_val_arr, p_uncal),
        "status": "EVALUATED",
    }
    calibrators["uncalibrated"] = None

    # 2. Fitted calibration methods
    for method in ["sigmoid", "isotonic"]:
        if method not in methods:
            continue
        try:
            cal = fit_calibrator(base_model, X_calib, y_calib, method=method)
            p_cal = calibrated_p(cal, X_val)
            metrics = evaluate_calibration(y_val_arr, p_cal)
            results[method] = {
                "method": method,
                "description": f"{method.capitalize()} calibration fitted on calibration split",
                "validation_metrics": metrics,
                "status": "EVALUATED",
            }
            calibrators[method] = cal
        except Exception as e:
            results[method] = {
                "method": method,
                "description": f"{method.capitalize()} calibration",
                "validation_metrics": None,
                "status": f"FIT_FAILED: {e}",
            }
            calibrators[method] = None

    # Select best calibration method on validation Brier score
    valid_candidates = [
        m for m, res in results.items()
        if res.get("validation_metrics") is not None
    ]

    selected_method = min(
        valid_candidates,
        key=lambda m: (
            results[m]["validation_metrics"]["brier_score"],
            results[m]["validation_metrics"]["ece"],
        ),
    )

    summary = {
        "selected_method": selected_method,
        "selection_criterion": "Lowest validation Brier score (secondary: lowest validation ECE)",
        "methods_evaluated": results,
        "monotonicity_note": (
            "Monotone probability calibration improves the empirical interpretation and reliability of probabilities, "
            "but does not alter ranking metrics (such as ROC-AUC) under strictly monotonic mappings."
        ),
    }

    return summary, calibrators
