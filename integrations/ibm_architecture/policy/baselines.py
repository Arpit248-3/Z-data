"""SignalGate IBM Architecture Integration — Baseline Comparison Policies.

Implements reference baseline adapters including the mandatory B2 top-budget policy:
- B2TopBudgetBaselineAdapter: deterministic top-B risk ranking matching analyst review budget.
- Computes touched rate, caught fraud, recall, and precision for offline metric reporting.
- Strictly separates offline evaluation from inference (ground truth is never passed to scoring).

Governing Specification: docs/ibm_architecture_integration_master_spec.md § C, § I
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple, Union
import numpy as np
import pandas as pd

from integrations.ibm_architecture.contracts import Action, ReasonCode


def compute_policy_evaluation_metrics(
    escalated_mask: np.ndarray,
    y_true: np.ndarray,
    budget_fraction: float,
    policy_name: str,
) -> Dict[str, Any]:
    """Compute touched rate, caught fraud count, recall, and precision for an offline evaluation."""
    n_samples = len(y_true)
    total_positives = int(np.sum(y_true))

    escalated_count = int(np.sum(escalated_mask))
    touched_rate = float(escalated_count / n_samples) if n_samples > 0 else 0.0

    caught_fraud = int(np.sum(y_true[escalated_mask]))
    missed_fraud = total_positives - caught_fraud

    recall = float(caught_fraud / total_positives) if total_positives > 0 else 0.0
    precision = float(caught_fraud / escalated_count) if escalated_count > 0 else 0.0

    return {
        "policy": policy_name,
        "target_budget": round(float(budget_fraction), 6),
        "total_transactions": n_samples,
        "escalated_count": escalated_count,
        "touched_rate": round(touched_rate, 6),
        "budget_matched": abs(touched_rate - budget_fraction) <= (1.0 / n_samples + 1e-6) if n_samples > 0 else True,
        "total_fraud": total_positives,
        "caught_fraud": caught_fraud,
        "missed_fraud": missed_fraud,
        "recall_at_touched": round(recall, 6),
        "precision": round(precision, 6),
    }


class B2TopBudgetBaselineAdapter:
    """Mandatory B2 Top-B Risk Ranking Baseline Policy Adapter.

    Ranks transactions descending by calibrated risk score p and escalates the top
    fraction B matching the review capacity budget.
    """

    def __init__(self, default_budget_fraction: float = 0.05075) -> None:
        if default_budget_fraction <= 0.0 or default_budget_fraction > 1.0:
            raise ValueError(f"Budget fraction must be in (0, 1], got {default_budget_fraction}")
        self.default_budget_fraction = default_budget_fraction

    def get_escalation_mask(
        self,
        p: Union[Sequence[float], np.ndarray],
        budget_fraction: Optional[float] = None,
    ) -> np.ndarray:
        """Deterministically select top B fraction by calibrated risk p."""
        b = budget_fraction if budget_fraction is not None else self.default_budget_fraction
        p_arr = np.asarray(p, dtype=float)
        n_samples = len(p_arr)

        if n_samples == 0:
            return np.zeros(0, dtype=bool)

        k_capacity = int(np.floor(n_samples * b))
        if k_capacity <= 0:
            return np.zeros(n_samples, dtype=bool)
        if k_capacity >= n_samples:
            return np.ones(n_samples, dtype=bool)

        # Deterministic stable ranking: highest p first
        # np.argsort on -p_arr gives descending order with stable index tie-breaking
        sorted_indices = np.argsort(-p_arr, kind="mergesort")
        top_indices = sorted_indices[:k_capacity]

        mask = np.zeros(n_samples, dtype=bool)
        mask[top_indices] = True
        return mask

    def route_cohort(
        self,
        p: Union[Sequence[float], np.ndarray],
        budget_fraction: Optional[float] = None,
    ) -> Tuple[List[Action], List[ReasonCode]]:
        """Assign Action and ReasonCode across cohort based on B2 top-B ranking."""
        mask = self.get_escalation_mask(p, budget_fraction)
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
        budget_fraction: Optional[float] = None,
    ) -> Dict[str, Any]:
        """Offline evaluation of B2 baseline against held-out true labels."""
        b = budget_fraction if budget_fraction is not None else self.default_budget_fraction
        mask = self.get_escalation_mask(p, b)
        y_arr = np.asarray(y_true, dtype=np.int8)
        return compute_policy_evaluation_metrics(mask, y_arr, b, policy_name="B2_top_b_risk")
