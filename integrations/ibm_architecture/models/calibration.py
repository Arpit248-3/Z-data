"""SignalGate IBM Architecture Integration — Probability Calibration & Diagnostic ECE.

Fitted strictly on the calibration partition in compliance with Master Spec § C, § H:
- Validation and test partitions are strictly prohibited from calibration fitting.
- PlattCalibrator: univariate logistic regression sigmoid scaling.
- IsotonicCalibrator: non-parametric isotonic regression.
- Diagnostic Expected Calibration Error (ECE) calculation.
"""

from __future__ import annotations

import numpy as np
from sklearn.isotonic import IsotonicRegression
from sklearn.linear_model import LogisticRegression


FORBIDDEN_CALIBRATION_PARTITIONS = {"validation", "test", "holdout", "val"}


def validate_calibration_partition(partition: str) -> None:
    """Validate that calibrator is never fitted on validation or test partitions."""
    clean_p = partition.strip().lower()
    if clean_p in FORBIDDEN_CALIBRATION_PARTITIONS:
        raise ValueError(
            f"Partition protection violation: calibrator must NEVER be fitted on '{partition}' partition. "
            f"Calibration is permitted strictly on 'calibration' partition."
        )


def calibration_ece(scores: np.ndarray, labels: np.ndarray, n_bins: int = 10) -> float:
    """Compute Expected Calibration Error (ECE) across confidence bins.

    ECE = sum_{b=1}^B (|B_b| / N) * |acc(B_b) - conf(B_b)|
    """
    scores_arr = np.asarray(scores, dtype=np.float64)
    labels_arr = np.asarray(labels, dtype=np.int8)

    if len(scores_arr) != len(labels_arr):
        raise ValueError(f"Scores ({len(scores_arr)}) and labels ({len(labels_arr)}) must have matching length.")

    n_samples = len(scores_arr)
    if n_samples == 0:
        return 0.0

    bins = np.linspace(0.0, 1.0, n_bins + 1)
    ece = 0.0

    for i in range(n_bins):
        low, high = bins[i], bins[i + 1]
        if i == n_bins - 1:
            bin_mask = (scores_arr >= low) & (scores_arr <= high)
        else:
            bin_mask = (scores_arr >= low) & (scores_arr < high)

        bin_count = np.sum(bin_mask)
        if bin_count > 0:
            bin_acc = np.mean(labels_arr[bin_mask])
            bin_conf = np.mean(scores_arr[bin_mask])
            ece += (bin_count / n_samples) * abs(bin_acc - bin_conf)

    return float(ece)


class PlattCalibrator:
    """Univariate logistic regression sigmoid probability calibrator.

    Maps uncalibrated ensemble consensus probability bar{p} into calibrated risk p_{calibrated}.
    Must be fitted strictly on the calibration partition.
    """

    def __init__(self, C: float = 1.0, max_iter: int = 1000) -> None:
        self.C = C
        self.max_iter = max_iter
        self.model = LogisticRegression(
            solver="lbfgs",
            max_iter=self.max_iter,
            C=self.C,
            random_state=11,
        )
        self.is_fitted: bool = False

    def fit(
        self,
        uncalibrated_scores: np.ndarray,
        labels: np.ndarray,
        partition: str = "calibration",
    ) -> "PlattCalibrator":
        """Fit sigmoid scaling strictly on calibration partition."""
        validate_calibration_partition(partition)

        scores = np.asarray(uncalibrated_scores, dtype=np.float64).reshape(-1, 1)
        y = np.asarray(labels, dtype=np.int8)

        self.model.fit(scores, y)
        self.is_fitted = True
        return self

    def predict_proba(self, uncalibrated_scores: np.ndarray) -> np.ndarray:
        """Transform raw probabilities into calibrated probabilities in [0, 1]."""
        if not self.is_fitted:
            raise RuntimeError("PlattCalibrator must be fitted before predict_proba().")

        scores = np.asarray(uncalibrated_scores, dtype=np.float64).reshape(-1, 1)
        cal_probas = self.model.predict_proba(scores)[:, 1]
        return np.clip(cal_probas.astype(np.float64), 0.0, 1.0)


class IsotonicCalibrator:
    """Non-parametric isotonic regression probability calibrator."""

    def __init__(self, out_of_bounds: str = "clip") -> None:
        self.out_of_bounds = out_of_bounds
        self.model = IsotonicRegression(
            y_min=0.0,
            y_max=1.0,
            out_of_bounds=self.out_of_bounds,
        )
        self.is_fitted: bool = False

    def fit(
        self,
        uncalibrated_scores: np.ndarray,
        labels: np.ndarray,
        partition: str = "calibration",
    ) -> "IsotonicCalibrator":
        """Fit isotonic regression strictly on calibration partition."""
        validate_calibration_partition(partition)

        scores = np.asarray(uncalibrated_scores, dtype=np.float64)
        y = np.asarray(labels, dtype=np.float64)

        self.model.fit(scores, y)
        self.is_fitted = True
        return self

    def predict_proba(self, uncalibrated_scores: np.ndarray) -> np.ndarray:
        """Transform raw probabilities into monotonically calibrated probabilities."""
        if not self.is_fitted:
            raise RuntimeError("IsotonicCalibrator must be fitted before predict_proba().")

        scores = np.asarray(uncalibrated_scores, dtype=np.float64)
        cal_probas = self.model.predict(scores)
        return np.clip(cal_probas.astype(np.float64), 0.0, 1.0)
