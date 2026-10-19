"""SignalGate IBM Architecture Integration — P5 Candidate Policy Adapter.

Implements the reference P5 candidate ranking policy:
    Score = p_calibrated + lambda * u_signal

Governing Specification: docs/ibm_architecture_integration_master_spec.md § C, § I
- Under frozen reference configuration, lambda = 0.0.
- When lambda = 0.0, ranking is purely by calibrated risk probability alone.
  The adapter explicitly preserves and documents this identity.
- P5 is strictly a cohort-relative budget-ranking policy. Evaluating P5 on an isolated
  single transaction without cohort context or declared cutoff is mathematically invalid
  and raises ValueError.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Sequence, Tuple, Union
import numpy as np
import pandas as pd

from integrations.ibm_architecture.contracts import Action, ReasonCode
from integrations.ibm_architecture.policy.baselines import compute_policy_evaluation_metrics


class P5CandidatePolicyAdapter:
    """P5 Candidate Budget-Ranking Policy Adapter.

    Ranking formula:
        Score_i = p_calibrated_i + lambda * u_signal_i

    Note: In the frozen reference configuration, lambda = 0.0.
    Under this setting, ranking is strictly by calibrated probability of fraud.
    """

    def __init__(
        self,
        default_lambda: float = 0.0,
        default_budget_fraction: float = 0.05075,
    ) -> None:
        self.default_lambda = default_lambda
        self.default_budget_fraction = default_budget_fraction

    def compute_scores(
        self,
        p: Union[Sequence[float], np.ndarray],
        u: Optional[Union[Sequence[float], np.ndarray]] = None,
        lambda_weight: Optional[float] = None,
    ) -> np.ndarray:
        """Calculate P5 priority scores for a cohort.

        Raises:
            ValueError: If called with a single scalar value without cohort context.
        """
        p_arr = np.asarray(p, dtype=float)
        if p_arr.ndim == 0 or len(p_arr) <= 1:
            raise ValueError(
                "P5CandidatePolicyAdapter is a cohort-relative budget-ranking policy and "
                "cannot be evaluated on an individual transaction without cohort context."
            )

        lam = lambda_weight if lambda_weight is not None else self.default_lambda

        if lam == 0.0 or u is None:
            return p_arr

        u_arr = np.asarray(u, dtype=float)
        if len(u_arr) != len(p_arr):
            raise ValueError(f"Length mismatch: p has {len(p_arr)} elements, u has {len(u_arr)}")

        # Replace non-finite u with 0.0 for ranking safety
        clean_u = np.where(np.isfinite(u_arr), u_arr, 0.0)
        return p_arr + lam * clean_u

    def get_escalation_mask(
        self,
        p: Union[Sequence[float], np.ndarray],
        u: Optional[Union[Sequence[float], np.ndarray]] = None,
        budget_fraction: Optional[float] = None,
        lambda_weight: Optional[float] = None,
    ) -> np.ndarray:
        """Deterministically select top B fraction by P5 priority score."""
        b = budget_fraction if budget_fraction is not None else self.default_budget_fraction
        scores = self.compute_scores(p, u, lambda_weight=lambda_weight)
        n_samples = len(scores)

        k_capacity = int(np.floor(n_samples * b))
        if k_capacity <= 0:
            return np.zeros(n_samples, dtype=bool)
        if k_capacity >= n_samples:
            return np.ones(n_samples, dtype=bool)

        sorted_indices = np.argsort(-scores, kind="mergesort")
        top_indices = sorted_indices[:k_capacity]

        mask = np.zeros(n_samples, dtype=bool)
        mask[top_indices] = True
        return mask

    def route_cohort(
        self,
        p: Union[Sequence[float], np.ndarray],
        u: Optional[Union[Sequence[float], np.ndarray]] = None,
        budget_fraction: Optional[float] = None,
        lambda_weight: Optional[float] = None,
    ) -> Tuple[List[Action], List[ReasonCode]]:
        """Assign Action and ReasonCode across cohort based on P5 ranking."""
        mask = self.get_escalation_mask(p, u, budget_fraction, lambda_weight=lambda_weight)
        actions: List[Action] = []
        reasons: List[ReasonCode] = []

        for is_escalated in mask:
            if is_escalated:
                actions.append("MANUAL_REVIEW")
                reasons.append("R2_INTERMEDIATE_RISK")
            else:
                actions.append("ROUTINE")
                reasons.append("R5_LOW_RISK_RELIABLE")

        return actions, reasons

    def evaluate_cohort(
        self,
        p: Union[Sequence[float], np.ndarray],
        y_true: Union[Sequence[int], np.ndarray],
        u: Optional[Union[Sequence[float], np.ndarray]] = None,
        budget_fraction: Optional[float] = None,
        lambda_weight: Optional[float] = None,
    ) -> Dict[str, Any]:
        """Offline evaluation of P5 candidate against held-out true labels."""
        b = budget_fraction if budget_fraction is not None else self.default_budget_fraction
        mask = self.get_escalation_mask(p, u, b, lambda_weight=lambda_weight)
        y_arr = np.asarray(y_true, dtype=np.int8)
        lam = lambda_weight if lambda_weight is not None else self.default_lambda
        res = compute_policy_evaluation_metrics(mask, y_arr, b, policy_name=f"P5_candidate_lambda_{lam}")
        res["lambda"] = lam
        return res
