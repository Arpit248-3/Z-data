"""
SignalGate Ensemble Disagreement Module
Implements:
1. 3-member deterministic ensemble trained on the training partition.
2. Raw probability disagreement: u = standard_deviation(member_probabilities, axis=members).
3. Diagnostics: distribution metrics and Spearman correlation rho(p, u).
4. Rank-residual disagreement variant u2 (Blueprint Section 10.3 / Line 753):
   - Fits mapping from rank(p) to rank(u) strictly on calibration split.
   - Evaluates empirical CDF using frozen calibration references (zero test leakage).
   - Freezes residualizer prior to any test-time evaluation.
"""

from typing import Any, Dict, List, Optional, Tuple, Union
import numpy as np
import pandas as pd
from scipy.stats import spearmanr
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.linear_model import Ridge
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import PolynomialFeatures

from models.base import raw_score


def fit_ensemble(
    X_train: Union[pd.DataFrame, np.ndarray],
    y_train: Union[pd.Series, np.ndarray],
    seeds: Optional[List[int]] = None,
    configs: Optional[List[Dict[str, Any]]] = None,
) -> List[HistGradientBoostingClassifier]:
    """
    Fit a 3-member ensemble of HistGradientBoostingClassifiers strictly on the training partition.
    """
    if seeds is None:
        seeds = [11, 22, 33]

    if configs is None:
        configs = [
            {"max_leaf_nodes": 31, "l2_regularization": 0.0},
            {"max_leaf_nodes": 20, "l2_regularization": 1.0},
            {"max_leaf_nodes": 40, "l2_regularization": 0.1},
        ]

    if len(seeds) != len(configs):
        raise ValueError(f"Length of seeds ({len(seeds)}) must match configs ({len(configs)}).")

    ensemble_members = []
    y_arr = np.asarray(y_train, dtype=int)

    for i, (seed, cfg) in enumerate(zip(seeds, configs)):
        model = HistGradientBoostingClassifier(
            random_state=seed,
            max_iter=50,
            early_stopping=False,
            **cfg,
        )
        model.fit(X_train, y_arr)
        ensemble_members.append(model)

    return ensemble_members


def predict_ensemble_proba(
    ensemble: List[Any],
    X: Union[pd.DataFrame, np.ndarray],
) -> np.ndarray:
    """
    Compute predicted fraud probabilities P(Y=1) for each ensemble member.

    Returns:
    - 2D numpy array of shape (n_members, n_samples).
    """
    if len(ensemble) == 0:
        raise ValueError("Ensemble cannot be empty.")

    member_probs = []
    for member in ensemble:
        p_member = raw_score(member, X)
        member_probs.append(p_member)

    return np.array(member_probs)


def disagreement(
    ensemble: List[Any],
    X: Union[pd.DataFrame, np.ndarray],
    ddof: int = 0,
) -> np.ndarray:
    """
    Calculate raw probability disagreement u across ensemble members:
    u = standard_deviation(member_probabilities, axis=members).

    Returns:
    - 1D numpy array of standard deviations in [0, 1].
    """
    if len(X) == 0:
        return np.array([], dtype=float)

    member_probs = predict_ensemble_proba(ensemble, X)
    u = np.std(member_probs, axis=0, ddof=ddof)

    if not np.isfinite(u).all():
        raise ValueError("Ensemble emitted non-finite disagreement values.")

    if (u < 0.0).any():
        raise ValueError("Disagreement cannot be negative.")

    return u


class RankResidualizer:
    """
    Learns the relationship between predicted risk probability p and raw disagreement u
    strictly on the calibration partition, and produces the rank-residual disagreement signal u2:
    u2 = r_u - hat{r}_u(r_p)

    Guarantees:
    - Uses empirical CDF references frozen from calibration data.
    - Operates row-by-row or on batches without inspecting test-set distribution statistics.
    """

    def __init__(self, degree: int = 3, alpha: float = 1.0):
        self.degree = degree
        self.alpha = alpha
        self.sorted_p_calib: Optional[np.ndarray] = None
        self.sorted_u_calib: Optional[np.ndarray] = None
        self.n_calib: int = 0
        self.regressor: Optional[Pipeline] = None
        self.is_fitted: bool = False

    def fit(
        self,
        raw_u_calib: Union[pd.Series, np.ndarray],
        p_calib: Union[pd.Series, np.ndarray],
    ) -> "RankResidualizer":
        p_arr = np.asarray(p_calib, dtype=float)
        u_arr = np.asarray(raw_u_calib, dtype=float)

        if len(p_arr) != len(u_arr):
            raise ValueError(f"Length mismatch: p_calib ({len(p_arr)}) vs raw_u_calib ({len(u_arr)})")

        if len(p_arr) < 10:
            raise ValueError(f"Insufficient samples to fit rank residualizer: {len(p_arr)}")

        self.n_calib = len(p_arr)
        self.sorted_p_calib = np.sort(p_arr)
        self.sorted_u_calib = np.sort(u_arr)

        # Empirical calibration ranks in [0, 1]
        r_p = np.searchsorted(self.sorted_p_calib, p_arr, side="right") / self.n_calib
        r_u = np.searchsorted(self.sorted_u_calib, u_arr, side="right") / self.n_calib

        # Polynomial ridge fit
        self.regressor = Pipeline([
            ("poly", PolynomialFeatures(degree=self.degree, include_bias=True)),
            ("ridge", Ridge(alpha=self.alpha)),
        ])
        self.regressor.fit(r_p.reshape(-1, 1), r_u)
        self.is_fitted = True

        return self

    def transform(
        self,
        raw_u: Union[pd.Series, np.ndarray],
        p: Union[pd.Series, np.ndarray],
    ) -> np.ndarray:
        if not self.is_fitted:
            raise RuntimeError("RankResidualizer must be fitted on calibration data before transform.")

        p_arr = np.asarray(p, dtype=float)
        u_arr = np.asarray(raw_u, dtype=float)

        if len(p_arr) == 0:
            return np.array([], dtype=float)

        # Evaluate against frozen calibration empirical CDFs (no test distribution leakage)
        r_p = np.searchsorted(self.sorted_p_calib, p_arr, side="right") / self.n_calib
        r_u = np.searchsorted(self.sorted_u_calib, u_arr, side="right") / self.n_calib

        predicted_r_u = self.regressor.predict(r_p.reshape(-1, 1))
        u2 = r_u - predicted_r_u

        return u2


def fit_rank_residual(
    raw_u_calib: Union[pd.Series, np.ndarray],
    p_calib: Union[pd.Series, np.ndarray],
) -> RankResidualizer:
    """Fit and return a frozen RankResidualizer instance."""
    residualizer = RankResidualizer()
    residualizer.fit(raw_u_calib, p_calib)
    return residualizer


def apply_rank_residual(
    residualizer: RankResidualizer,
    raw_u: Union[pd.Series, np.ndarray],
    p: Union[pd.Series, np.ndarray],
) -> np.ndarray:
    """Apply frozen RankResidualizer to produce u2."""
    return residualizer.transform(raw_u, p)


def compute_disagreement_diagnostics(
    p: Union[pd.Series, np.ndarray],
    raw_u: Union[pd.Series, np.ndarray],
    u2: Optional[Union[pd.Series, np.ndarray]] = None,
) -> Dict[str, Any]:
    """
    Compute summary statistics and Spearman correlations for uncertainty signals.
    """
    p_arr = np.asarray(p, dtype=float)
    u_arr = np.asarray(raw_u, dtype=float)

    corr_raw, pval_raw = spearmanr(p_arr, u_arr)

    diag = {
        "raw_u_distribution": {
            "mean": round(float(np.mean(u_arr)), 6),
            "std": round(float(np.std(u_arr)), 6),
            "min": round(float(np.min(u_arr)), 6),
            "p25": round(float(np.percentile(u_arr, 25)), 6),
            "p50": round(float(np.median(u_arr)), 6),
            "p75": round(float(np.percentile(u_arr, 75)), 6),
            "p95": round(float(np.percentile(u_arr, 95)), 6),
            "max": round(float(np.max(u_arr)), 6),
        },
        "spearman_corr_p_raw_u": round(float(corr_raw), 4),
        "spearman_pval_p_raw_u": round(float(pval_raw), 6),
    }

    if u2 is not None:
        u2_arr = np.asarray(u2, dtype=float)
        corr_u2, pval_u2 = spearmanr(p_arr, u2_arr)
        diag["u2_distribution"] = {
            "mean": round(float(np.mean(u2_arr)), 6),
            "std": round(float(np.std(u2_arr)), 6),
            "min": round(float(np.min(u2_arr)), 6),
            "p25": round(float(np.percentile(u2_arr, 25)), 6),
            "p50": round(float(np.median(u2_arr)), 6),
            "p75": round(float(np.percentile(u2_arr, 75)), 6),
            "p95": round(float(np.percentile(u2_arr, 95)), 6),
            "max": round(float(np.max(u2_arr)), 6),
        }
        diag["spearman_corr_p_u2"] = round(float(corr_u2), 4)
        diag["spearman_pval_p_u2"] = round(float(pval_u2), 6)
        diag["decorrelation_achieved"] = round(float(abs(corr_raw) - abs(corr_u2)), 4)

    return diag
