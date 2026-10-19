"""SignalGate IBM Architecture Integration — Platt and Isotonic Calibration.

Implements probability calibration with strict partition boundaries:
- Prohibits fitting on 'validation' or 'test' partitions (raises ValueError).
- PlattCalibrator (univariate LogisticRegression, C=1.0) maps raw risk scores to calibrated probabilities.
- IsotonicCalibrator (non-parametric IsotonicRegression).
- Expected Calibration Error (ECE) metric for diagnostic evaluation.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple, Union
import numpy as np
import pandas as pd
from sklearn.isotonic import IsotonicRegression
from sklearn.linear_model import LogisticRegression


def validate_calibration_partition(partition: str) -> None:
    """Enforce partition governance: prohibit fitting on validation or test splits."""
    p_norm = str(partition).strip().lower()
    if p_norm in ["validation", "val", "test", "holdout"]:
        raise ValueError(
            f"Prohibited partition for calibration fitting: '{partition}'. "
            "Master Spec § H mandates calibrators fit strictly on 'calibration' partition."
        )


def calibration_ece(scores: Union[np.ndarray, Sequence[float]], labels: Union[np.ndarray, Sequence[int]], n_bins: int = 10) -> float:
    """Calculate diagnostic Expected Calibration Error (ECE)."""
    s_arr = np.asarray(scores, dtype=np.float64)
    y_arr = np.asarray(labels, dtype=np.int8)

    if len(s_arr) != len(y_arr):
        raise ValueError("scores and labels must have the same length")
    if len(s_arr) == 0:
        return 0.0

    bins = np.linspace(0.0, 1.0, n_bins + 1)
    bin_indices = np.digitize(s_arr, bins) - 1
    bin_indices = np.clip(bin_indices, 0, n_bins - 1)

    ece = 0.0
    n_samples = len(s_arr)
    for b in range(n_bins):
        mask = bin_indices == b
        bin_count = np.sum(mask)
        if bin_count > 0:
            bin_acc = np.mean(y_arr[mask])
            bin_conf = np.mean(s_arr[mask])
            ece += (bin_count / n_samples) * abs(bin_acc - bin_conf)

    return float(ece)


class PlattCalibrator:
    """Platt Scaling (Sigmoid Logistic Regression) fitted strictly on calibration partition."""

    def __init__(self, C: float = 1.0, max_iter: int = 1000) -> None:
        self.C = C
        self.max_iter = max_iter
        self.model = LogisticRegression(solver="lbfgs", max_iter=self.max_iter, C=self.C)
        self.is_fitted: bool = False

    def fit(
        self,
        scores: Union[np.ndarray, pd.Series, Sequence[float]],
        y: Union[np.ndarray, pd.Series, Sequence[int]],
        partition: str = "calibration",
    ) -> PlattCalibrator:
        """Fit Platt calibrator on raw model scores and binary labels."""
        validate_calibration_partition(partition)
        s_arr = np.asarray(scores, dtype=np.float64).reshape(-1, 1)
        y_arr = np.asarray(y, dtype=np.int8)

        self.model.fit(s_arr, y_arr)
        self.is_fitted = True
        return self

    def predict_proba(self, scores: Union[np.ndarray, pd.Series, Sequence[float]]) -> np.ndarray:
        """Predict calibrated probabilities of shape (N, 2)."""
        if not self.is_fitted:
            raise RuntimeError("PlattCalibrator is not fitted.")
        s_arr = np.asarray(scores, dtype=np.float64).reshape(-1, 1)
        return self.model.predict_proba(s_arr)

    def predict(self, scores: Union[np.ndarray, pd.Series, Sequence[float]]) -> np.ndarray:
        """Predict positive calibrated risk probabilities of shape (N,)."""
        proba = self.predict_proba(scores)
        return proba[:, 1]


class IsotonicCalibrator:
    """Non-parametric isotonic regression calibrator fitted on calibration partition."""

    def __init__(self, out_of_bounds: str = "clip") -> None:
        self.out_of_bounds = out_of_bounds
        self.model = IsotonicRegression(out_of_bounds=self.out_of_bounds, y_min=0.0, y_max=1.0)
        self.is_fitted: bool = False

    def fit(
        self,
        scores: Union[np.ndarray, pd.Series, Sequence[float]],
        y: Union[np.ndarray, pd.Series, Sequence[int]],
        partition: str = "calibration",
    ) -> IsotonicCalibrator:
        validate_calibration_partition(partition)
        s_arr = np.asarray(scores, dtype=np.float64)
        y_arr = np.asarray(y, dtype=np.float64)

        self.model.fit(s_arr, y_arr)
        self.is_fitted = True
        return self

    def predict(self, scores: Union[np.ndarray, pd.Series, Sequence[float]]) -> np.ndarray:
        if not self.is_fitted:
            raise RuntimeError("IsotonicCalibrator is not fitted.")
        s_arr = np.asarray(scores, dtype=np.float64)
        return np.clip(self.model.predict(s_arr), 0.0, 1.0)
