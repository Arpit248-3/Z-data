"""SignalGate IBM Architecture Integration — Era-Bagged Heterogeneous Ensemble.

Implements chronological era bagging across 5 heterogeneous members in compliance
with Master Spec § C, § D, and § H:
- Divides training observations into 5 chronological eras.
- Trains 5 members, each omitting one chronological era of training data.
- Heterogeneous architectures: HistGradientBoosting, ExtraTrees, and LogisticRegression.
- Computes per-member raw probability matrix and consensus arithmetic mean.
- Provides resource-constrained local development mode (`n_jobs=1`, bounded depth, sequential `gc.collect()`).
"""

from __future__ import annotations

import gc
from dataclasses import dataclass
from typing import Any, List, Optional, Sequence, Tuple
import numpy as np
from sklearn.ensemble import ExtraTreesClassifier, HistGradientBoostingClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler


def compute_training_eras(n_samples: int, n_eras: int = 5) -> List[Tuple[int, int]]:
    """Divide training observations chronologically into approximately equal eras.

    Parameters
    ----------
    n_samples : int
        Total number of training rows.
    n_eras : int, default 5
        Number of chronological eras.

    Returns
    -------
    List[Tuple[int, int]]
        List of (start_idx, end_idx) half-open intervals spanning [0, n_samples).
    """
    if n_samples <= 0:
        raise ValueError("n_samples must be positive.")
    if n_eras <= 0 or n_eras > n_samples:
        raise ValueError(f"Invalid n_eras {n_eras} for n_samples {n_samples}.")

    step = n_samples / n_eras
    eras: List[Tuple[int, int]] = []
    for i in range(n_eras):
        start = int(round(i * step))
        end = int(round((i + 1) * step)) if i < n_eras - 1 else n_samples
        eras.append((start, end))
    return eras


def get_era_omitted_indices(n_samples: int, omit_era_idx: int, n_eras: int = 5) -> np.ndarray:
    """Return indices of training data omitting one chronological era."""
    eras = compute_training_eras(n_samples, n_eras=n_eras)
    if not (0 <= omit_era_idx < n_eras):
        raise IndexError(f"omit_era_idx {omit_era_idx} out of range for {n_eras} eras.")
    start, end = eras[omit_era_idx]
    mask = np.ones(n_samples, dtype=bool)
    mask[start:end] = False
    return np.flatnonzero(mask)


@dataclass
class MemberPredictions:
    """Container holding raw member probabilities without premature averaging."""

    proba_matrix: np.ndarray  # Shape: (N, M)
    member_ids: List[str]


class EraBaggedHeterogeneousEnsemble:
    """5-member heterogeneous ensemble trained with chronological era omission.

    Members:
      - Member 0: HistGradientBoosting (seed 11) omitting Era 0
      - Member 1: HistGradientBoosting (seed 22) omitting Era 1
      - Member 2: ExtraTreesClassifier (seed 11) omitting Era 2
      - Member 3: LogisticRegression with median imputation & scaling (seed 11) omitting Era 3
      - Member 4: HistGradientBoosting (seed 33) omitting Era 4
    """

    def __init__(
        self,
        n_eras: int = 5,
        mode: str = "local_dev",
    ) -> None:
        self.n_eras = n_eras
        self.mode = mode
        self._members: List[Tuple[str, Any, Tuple[int, int]]] = []
        self.member_ids: List[str] = []
        self.era_definitions: List[Tuple[int, int]] = []
        self.is_fitted: bool = False

    def _build_member_specs(self) -> List[Tuple[str, Any]]:
        """Construct estimator specifications based on execution mode."""
        if self.mode == "local_dev":
            # Resource-capped settings: max_iter=30, max_depth=12, n_estimators=30, n_jobs=1
            specs = [
                (
                    "era0_omit_hgbc_s11",
                    HistGradientBoostingClassifier(
                        max_iter=30,
                        random_state=11,
                        class_weight="balanced",
                        early_stopping=False,
                    ),
                ),
                (
                    "era1_omit_hgbc_s22",
                    HistGradientBoostingClassifier(
                        max_iter=30,
                        random_state=22,
                        class_weight="balanced",
                        early_stopping=False,
                    ),
                ),
                (
                    "era2_omit_et_s11",
                    ExtraTreesClassifier(
                        n_estimators=30,
                        max_depth=12,
                        random_state=11,
                        class_weight="balanced",
                        n_jobs=1,
                    ),
                ),
                (
                    "era3_omit_lr_s11",
                    Pipeline([
                        ("imputer", SimpleImputer(strategy="median")),
                        ("scaler", StandardScaler()),
                        (
                            "lr",
                            LogisticRegression(
                                solver="lbfgs",
                                max_iter=1000,
                                C=0.1,
                                class_weight="balanced",
                                random_state=11,
                            ),
                        ),
                    ]),
                ),
                (
                    "era4_omit_hgbc_s33",
                    HistGradientBoostingClassifier(
                        max_iter=30,
                        random_state=33,
                        class_weight="balanced",
                        early_stopping=False,
                    ),
                ),
            ]
        else:
            # Full benchmark settings
            specs = [
                (
                    "era0_omit_hgbc_s11",
                    HistGradientBoostingClassifier(
                        max_iter=60,
                        random_state=11,
                        class_weight="balanced",
                        early_stopping=False,
                    ),
                ),
                (
                    "era1_omit_hgbc_s22",
                    HistGradientBoostingClassifier(
                        max_iter=60,
                        random_state=22,
                        class_weight="balanced",
                        early_stopping=False,
                    ),
                ),
                (
                    "era2_omit_et_s11",
                    ExtraTreesClassifier(
                        n_estimators=100,
                        random_state=11,
                        class_weight="balanced",
                        n_jobs=-1,
                    ),
                ),
                (
                    "era3_omit_lr_s11",
                    Pipeline([
                        ("imputer", SimpleImputer(strategy="median")),
                        ("scaler", StandardScaler()),
                        (
                            "lr",
                            LogisticRegression(
                                solver="lbfgs",
                                max_iter=2000,
                                C=0.1,
                                class_weight="balanced",
                                random_state=11,
                            ),
                        ),
                    ]),
                ),
                (
                    "era4_omit_hgbc_s33",
                    HistGradientBoostingClassifier(
                        max_iter=60,
                        random_state=33,
                        class_weight="balanced",
                        early_stopping=False,
                    ),
                ),
            ]
        return specs[: self.n_eras]

    def fit(self, X_train: np.ndarray, y_train: np.ndarray) -> "EraBaggedHeterogeneousEnsemble":
        """Fit each ensemble member on its respective era-omitted training partition."""
        X_arr = np.asarray(X_train, dtype=np.float32)
        y_arr = np.asarray(y_train, dtype=np.int8)
        n_samples = len(X_arr)

        self.era_definitions = compute_training_eras(n_samples, n_eras=self.n_eras)
        specs = self._build_member_specs()

        self._members = []
        for era_idx, (name, estimator) in enumerate(specs):
            train_idx = get_era_omitted_indices(n_samples, omit_era_idx=era_idx, n_eras=self.n_eras)
            X_era = X_arr[train_idx]
            y_era = y_arr[train_idx]

            # Fit member on era-omitted subset
            estimator.fit(X_era, y_era)
            self._members.append((name, estimator, self.era_definitions[era_idx]))

            # Clean memory aggressively between member fits
            del X_era, y_era, train_idx
            gc.collect()

        self.member_ids = [m[0] for m in self._members]
        self.is_fitted = True
        return self

    def predict_member_proba(self, X: np.ndarray) -> MemberPredictions:
        """Produce raw probability matrix (N, M) across all active members."""
        if not self.is_fitted:
            raise RuntimeError("EraBaggedHeterogeneousEnsemble must be fitted before predict_member_proba().")

        X_arr = np.asarray(X, dtype=np.float32)
        member_probas: List[np.ndarray] = []

        for name, estimator, _ in self._members:
            p = estimator.predict_proba(X_arr)[:, 1].astype(np.float64)
            member_probas.append(p)

        proba_matrix = np.column_stack(member_probas)
        return MemberPredictions(proba_matrix=proba_matrix, member_ids=list(self.member_ids))

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        """Compute ensemble consensus probability bar{p} = mean(p_m), shape (N,)."""
        mp = self.predict_member_proba(X)
        return mp.proba_matrix.mean(axis=1)

    @property
    def n_members(self) -> int:
        return len(self._members)
