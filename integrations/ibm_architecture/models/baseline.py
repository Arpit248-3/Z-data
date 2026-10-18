"""SignalGate IBM Architecture Integration — Baseline Model B2.

Single-model gradient boosted decision tree classifier establishing the competitive
benchmark for fraud risk triage.
"""

from __future__ import annotations

import numpy as np
from sklearn.ensemble import HistGradientBoostingClassifier


class BaselineB2:
    """Baseline Model B2: HistGradientBoostingClassifier with balanced class weighting."""

    def __init__(
        self,
        max_iter: int = 30,
        random_state: int = 11,
        class_weight: str = "balanced",
        early_stopping: bool = False,
    ) -> None:
        self.max_iter = max_iter
        self.random_state = random_state
        self.class_weight = class_weight
        self.early_stopping = early_stopping
        self.estimator = HistGradientBoostingClassifier(
            max_iter=self.max_iter,
            random_state=self.random_state,
            class_weight=self.class_weight,
            early_stopping=self.early_stopping,
        )
        self.is_fitted: bool = False

    def fit(self, X: np.ndarray, y: np.ndarray) -> "BaselineB2":
        """Fit estimator strictly on training feature matrix and labels."""
        X_arr = np.asarray(X, dtype=np.float32)
        y_arr = np.asarray(y, dtype=np.int8)
        self.estimator.fit(X_arr, y_arr)
        self.is_fitted = True
        return self

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        """Predict positive class probabilities, shape (N,)."""
        if not self.is_fitted:
            raise RuntimeError("BaselineB2 must be fitted before predict_proba().")
        X_arr = np.asarray(X, dtype=np.float32)
        probas = self.estimator.predict_proba(X_arr)
        return probas[:, 1].astype(np.float64)

    @property
    def member_id(self) -> str:
        return f"baseline_b2_hgbc_s{self.random_state}"
