"""SignalGate IBM Architecture Integration — Era-Bagged Heterogeneous Ensemble.

Implements the 5-member era-bagged ensemble with sequential, memory-controlled fitting:
- 5 chronological era-omitted members across diverse algorithm families.
- ExtraTreesClassifier configured with n_jobs=1 for strictly bounded memory.
- Inter-stage garbage collection (gc.collect()) and pre-stage RAM verification hooks.
- Consensus averaging across active member probabilities.
"""

from __future__ import annotations

from dataclasses import dataclass
import gc
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple, Union
import numpy as np
import pandas as pd
from sklearn.ensemble import ExtraTreesClassifier, HistGradientBoostingClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler


def compute_training_eras(n_samples: int, n_eras: int = 5) -> List[Tuple[int, int]]:
    """Segment training partition chronologically into n_eras equal disjoint slices [start, end)."""
    if n_eras <= 0:
        raise ValueError(f"n_eras must be positive, got {n_eras}")
    if n_samples < n_eras:
        raise ValueError(f"n_samples ({n_samples}) must be >= n_eras ({n_eras})")

    step = n_samples // n_eras
    eras = []
    for i in range(n_eras):
        start = i * step
        end = (i + 1) * step if i < n_eras - 1 else n_samples
        eras.append((start, end))
    return eras


def get_era_omitted_indices(n_samples: int, omit_era_idx: int, n_eras: int = 5) -> np.ndarray:
    """Return indices of training samples omitting one chronological era."""
    eras = compute_training_eras(n_samples, n_eras=n_eras)
    if not (0 <= omit_era_idx < n_eras):
        raise IndexError(f"omit_era_idx {omit_era_idx} out of range [0, {n_eras})")

    omit_start, omit_end = eras[omit_era_idx]
    all_indices = np.arange(n_samples, dtype=np.int32)
    mask = (all_indices < omit_start) | (all_indices >= omit_end)
    return all_indices[mask]


@dataclass(frozen=True)
class MemberPredictions:
    """Raw member probability predictions from the heterogeneous ensemble."""

    proba_matrix: np.ndarray  # Shape: (N, 5), float32/float64
    member_ids: List[str]

    def __post_init__(self) -> None:
        if self.proba_matrix.ndim != 2:
            raise ValueError(f"proba_matrix must be 2D, got ndim={self.proba_matrix.ndim}")
        if self.proba_matrix.shape[1] != len(self.member_ids):
            raise ValueError(
                f"Column count ({self.proba_matrix.shape[1]}) must match member_ids count ({len(self.member_ids)})"
            )


class EraBaggedHeterogeneousEnsemble:
    """Sequential, memory-controlled 5-member era-bagged ensemble."""

    MEMBER_SPECS = [
        ("era0_omit_hgbc_s11", 0, "hgbc", 11),
        ("era1_omit_hgbc_s22", 1, "hgbc", 22),
        ("era2_omit_et_s11", 2, "et", 11),
        ("era3_omit_lr_s11", 3, "lr", 11),
        ("era4_omit_hgbc_s33", 4, "hgbc", 33),
    ]

    def __init__(self, extra_trees_n_jobs: int = 1) -> None:
        self.extra_trees_n_jobs = extra_trees_n_jobs
        self.member_ids = [spec[0] for spec in self.MEMBER_SPECS]
        self.members: Dict[str, Any] = {}
        self.is_fitted: bool = False

        # Initialize base un-fitted estimator templates
        self._init_member_estimators()

    @property
    def n_members(self) -> int:
        return len(self.member_ids)

    def _init_member_estimators(self) -> None:
        """Instantiate the 5 heterogeneous member estimators."""
        self.members["era0_omit_hgbc_s11"] = HistGradientBoostingClassifier(
            max_iter=60, random_state=11, class_weight="balanced", early_stopping=False
        )
        self.members["era1_omit_hgbc_s22"] = HistGradientBoostingClassifier(
            max_iter=60, random_state=22, class_weight="balanced", early_stopping=False
        )
        self.members["era2_omit_et_s11"] = ExtraTreesClassifier(
            n_estimators=100,
            random_state=11,
            class_weight="balanced",
            n_jobs=self.extra_trees_n_jobs,
        )
        self.members["era3_omit_lr_s11"] = Pipeline(
            [
                ("imputer", SimpleImputer(strategy="median")),
                ("scaler", StandardScaler()),
                (
                    "clf",
                    LogisticRegression(
                        solver="lbfgs",
                        max_iter=2000,
                        C=0.1,
                        class_weight="balanced",
                        random_state=11,
                    ),
                ),
            ]
        )
        self.members["era4_omit_hgbc_s33"] = HistGradientBoostingClassifier(
            max_iter=60, random_state=33, class_weight="balanced", early_stopping=False
        )

    def fit(
        self,
        X: Union[np.ndarray, pd.DataFrame],
        y: Union[np.ndarray, pd.Series],
        pre_stage_ram_check: Optional[Callable[[str], None]] = None,
    ) -> EraBaggedHeterogeneousEnsemble:
        """Fit all 5 members sequentially in series with inter-stage garbage collection."""
        X_arr = np.asarray(X, dtype=np.float32)
        y_arr = np.asarray(y, dtype=np.int8)
        n_samples = len(X_arr)

        for member_id, omit_era_idx, model_type, seed in self.MEMBER_SPECS:
            # 1. Pre-stage RAM check hook
            if pre_stage_ram_check is not None:
                pre_stage_ram_check(f"fit_member_{member_id}")

            # 2. Extract era-omitted training subset
            indices = get_era_omitted_indices(n_samples, omit_era_idx=omit_era_idx, n_eras=5)
            X_subset = X_arr[indices]
            y_subset = y_arr[indices]

            # 3. Fit member estimator
            estimator = self.members[member_id]
            estimator.fit(X_subset, y_subset)

            # 4. Clean up slice and force garbage collection
            del X_subset, y_subset, indices
            gc.collect()

        self.is_fitted = True
        return self

    def predict_member_proba(self, X: Union[np.ndarray, pd.DataFrame]) -> MemberPredictions:
        """Generate prediction matrix of positive class probabilities across all 5 members."""
        if not self.is_fitted:
            raise RuntimeError("EraBaggedHeterogeneousEnsemble is not fitted.")
        X_arr = np.asarray(X, dtype=np.float32)
        n_samples = len(X_arr)

        proba_matrix = np.empty((n_samples, len(self.member_ids)), dtype=np.float32)
        for i, member_id in enumerate(self.member_ids):
            estimator = self.members[member_id]
            col_proba = estimator.predict_proba(X_arr)[:, 1]
            proba_matrix[:, i] = col_proba.astype(np.float32)

        return MemberPredictions(proba_matrix=proba_matrix, member_ids=self.member_ids)

    predict_member_probas = predict_member_proba

    def predict_proba(self, X: Union[np.ndarray, pd.DataFrame]) -> np.ndarray:
        """Return consensus probability matrix of shape (N, 2)."""
        mp = self.predict_member_proba(X)
        p_bar = np.mean(mp.proba_matrix, axis=1)
        p_neg = 1.0 - p_bar
        return np.column_stack([p_neg, p_bar])

    def predict_positive_proba(self, X: Union[np.ndarray, pd.DataFrame]) -> np.ndarray:
        """Return 1D array of ensemble consensus positive probabilities of shape (N,)."""
        mp = self.predict_member_proba(X)
        return np.mean(mp.proba_matrix, axis=1)
