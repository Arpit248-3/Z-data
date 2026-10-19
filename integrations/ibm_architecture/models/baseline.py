"""SignalGate IBM Architecture Integration — Baseline Estimator B2.

Implements the verified baseline model B2:
- HistGradientBoostingClassifier(max_iter=60, random_state=11, class_weight="balanced", early_stopping=False)
- Standard fit and probability prediction interfaces.
"""

from __future__ import annotations

from typing import Any, Dict, Optional, Tuple, Union
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier


class BaselineB2:
    """Standalone gradient boosting baseline estimator B2."""

    def __init__(
        self,
        max_iter: int = 60,
        random_state: int = 11,
        class_weight: str = "balanced",
        early_stopping: bool = False,
    ) -> None:
        self.max_iter = max_iter
        self.random_state = random_state
        self.class_weight = class_weight
        self.early_stopping = early_stopping
        self.model = HistGradientBoostingClassifier(
            max_iter=self.max_iter,
            random_state=self.random_state,
            class_weight=self.class_weight,
            early_stopping=self.early_stopping,
        )
        self.is_fitted: bool = False

    def fit(self, X: Union[np.ndarray, pd.DataFrame], y: Union[np.ndarray, pd.Series]) -> BaselineB2:
        """Fit the baseline classifier on training data."""
        X_arr = np.asarray(X, dtype=np.float32)
        y_arr = np.asarray(y, dtype=np.int8)
        self.model.fit(X_arr, y_arr)
        self.is_fitted = True
        return self

    def predict_proba(self, X: Union[np.ndarray, pd.DataFrame]) -> np.ndarray:
        """Predict class probabilities of shape (N, 2)."""
        if not self.is_fitted:
            raise RuntimeError("BaselineB2 estimator is not fitted.")
        X_arr = np.asarray(X, dtype=np.float32)
        return self.model.predict_proba(X_arr)

    def predict_positive_proba(self, X: Union[np.ndarray, pd.DataFrame]) -> np.ndarray:
        """Predict positive fraud class probability of shape (N,)."""
        proba = self.predict_proba(X)
        return proba[:, 1]
