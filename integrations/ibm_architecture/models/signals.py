"""SignalGate IBM Architecture Integration — Disagreement Signal Extractors.

Extracts inter-model disagreement signals from MemberPredictions in compliance with
Master Spec § C, § D, and § H:
- $u$: Population standard deviation across member probabilities:
  u = sqrt( (1/M) * sum_{m=1}^M (p_m - bar{p})^2 )
- $u_2$: Mean absolute deviation from the median member probability:
  u_2 = (1/M) * sum_{m=1}^M |p_m - median(p)|
- Signals are computed strictly from unlabelled member probabilities;
  zero ground-truth labels are accessed or required.
"""

from __future__ import annotations

from dataclasses import dataclass
import numpy as np

from integrations.ibm_architecture.models.ensemble import MemberPredictions


@dataclass(frozen=True)
class DisagreementSignals:
    """Structured uncertainty representation for a single transaction case."""

    p: float   # Consensus mean probability
    u: float   # Standard deviation across ensemble members
    u2: float  # Median absolute deviation (MAD) across ensemble members
    n: float   # Number of active ensemble members


class DisagreementSignalExtractor:
    """Computes population standard deviation u across member probabilities."""

    @staticmethod
    def extract(proba_matrix: np.ndarray) -> np.ndarray:
        """Compute standard deviation across columns (members), shape (N,)."""
        P = np.asarray(proba_matrix, dtype=np.float64)
        return np.std(P, axis=1, ddof=0)


class RobustDisagreementSignalExtractor:
    """Computes median absolute deviation u_2 across member probabilities."""

    @staticmethod
    def extract(proba_matrix: np.ndarray) -> np.ndarray:
        """Compute mean absolute deviation from the median across columns, shape (N,)."""
        P = np.asarray(proba_matrix, dtype=np.float64)
        medians = np.median(P, axis=1, keepdims=True)
        return np.mean(np.abs(P - medians), axis=1)


def compute_signals(mp: MemberPredictions) -> np.ndarray:
    """Vectorized calculation of disagreement signals from MemberPredictions.

    Returns a structured numpy array with fields:
      - 'p': float64 (consensus mean probability)
      - 'u': float64 (standard deviation)
      - 'u2': float64 (median absolute deviation)
      - 'n': float64 (active member count)
    """
    P = np.asarray(mp.proba_matrix, dtype=np.float64)
    if P.ndim == 1:
        P = P.reshape(1, -1)

    n_samples, n_members = P.shape
    p_mean = np.mean(P, axis=1)
    u_std = DisagreementSignalExtractor.extract(P)
    u2_mad = RobustDisagreementSignalExtractor.extract(P)
    n_arr = np.full(n_samples, float(n_members), dtype=np.float64)

    dtype = [("p", "f8"), ("u", "f8"), ("u2", "f8"), ("n", "f8")]
    structured = np.empty(n_samples, dtype=dtype)
    structured["p"] = p_mean
    structured["u"] = u_std
    structured["u2"] = u2_mad
    structured["n"] = n_arr

    return structured
