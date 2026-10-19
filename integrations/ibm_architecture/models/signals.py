"""SignalGate IBM Architecture Integration — Disagreement Signal Extractors.

Computes epistemic disagreement and dispersion signals without accessing ground-truth labels:
- u: Population standard deviation across active ensemble member predictions.
- u2: Median absolute deviation (MAD) from median member probability.
- Vectorized and single-case calculations returning structured DisagreementSignals.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Union
import numpy as np

from integrations.ibm_architecture.models.ensemble import MemberPredictions


@dataclass(frozen=True)
class DisagreementSignals:
    """Uncertainty and consensus signals extracted from heterogeneous ensemble."""

    p: float   # Ensemble consensus probability (mean)
    u: float   # Population standard deviation across member probabilities
    u2: float  # Median absolute deviation (MAD) from median probability
    n: float   # Active ensemble member count


class DisagreementSignalExtractor:
    """Computes population standard deviation across ensemble member probabilities."""

    def extract(self, probabilities: Union[np.ndarray, List[float]]) -> float:
        p_arr = np.asarray(probabilities, dtype=np.float64)
        if len(p_arr) == 0:
            return 0.0
        val = float(np.std(p_arr, ddof=0))
        return val if val > 1e-12 else 0.0


class RobustDisagreementSignalExtractor:
    """Computes median absolute deviation from the median member probability."""

    def extract(self, probabilities: Union[np.ndarray, List[float]]) -> float:
        p_arr = np.asarray(probabilities, dtype=np.float64)
        if len(p_arr) == 0:
            return 0.0
        med = np.median(p_arr)
        val = float(np.mean(np.abs(p_arr - med)))
        return val if val > 1e-12 else 0.0


def compute_signals(mp: MemberPredictions) -> np.ndarray:
    """Compute vectorized structured signals array with fields [p, u, u2, n] across batch."""
    P = mp.proba_matrix.astype(np.float64)
    n_samples, n_members = P.shape

    # 1. Consensus mean p
    p_vec = np.mean(P, axis=1)

    # 2. Population standard deviation u
    u_vec = np.std(P, axis=1, ddof=0)
    u_vec = np.where(u_vec > 1e-12, u_vec, 0.0)

    # 3. Median absolute deviation u2
    med_vec = np.median(P, axis=1, keepdims=True)
    u2_vec = np.mean(np.abs(P - med_vec), axis=1)
    u2_vec = np.where(u2_vec > 1e-12, u2_vec, 0.0)

    # 4. Member count n
    n_vec = np.full(n_samples, fill_value=float(n_members), dtype=np.float64)

    dtype = [("p", np.float64), ("u", np.float64), ("u2", np.float64), ("n", np.float64)]
    out = np.empty(n_samples, dtype=dtype)
    out["p"] = p_vec
    out["u"] = u_vec
    out["u2"] = u2_vec
    out["n"] = n_vec

    return out


def compute_single_signals(probabilities: Union[np.ndarray, List[float]]) -> DisagreementSignals:
    """Compute DisagreementSignals for a single transaction vector."""
    p_arr = np.asarray(probabilities, dtype=np.float64)
    n_members = len(p_arr)
    if n_members == 0:
        return DisagreementSignals(p=0.0, u=0.0, u2=0.0, n=0.0)

    p_val = float(np.mean(p_arr))
    u_raw = float(np.std(p_arr, ddof=0))
    u_val = u_raw if u_raw > 1e-12 else 0.0
    u2_raw = float(np.mean(np.abs(p_arr - np.median(p_arr))))
    u2_val = u2_raw if u2_raw > 1e-12 else 0.0

    return DisagreementSignals(p=p_val, u=u_val, u2=u2_val, n=float(n_members))
