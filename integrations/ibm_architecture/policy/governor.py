"""SignalGate IBM Architecture Integration — Capacity Governor.

Implements capacity-constrained escalation management with dual capacity modes:
- Mode A (Fixed Count): capacity: int (e.g. K = 130 for synthetic cohorts or unit tests)
- Mode B (Budget Fraction): budget_fraction: float (e.g. B_frac = 0.05075 for 1.5x IEEE-CIS workload)
- Deterministically prioritizes candidates by risk score p with stable tie-breaking.
- Marks excess escalations as DEFERRED / R6_CAPACITY_DEFERRED.
- Strict Invariant: Capacity saturation must NEVER silently reclassify an alert or review
  candidate as ROUTINE. Deferred cases remain segregated in a dedicated deferred queue.
- Implements exact touched-rate accounting:
    touched_rate = (admitted_alerts + admitted_reviews) / total_transactions

Governing Specification: docs/ibm_architecture_integration_master_spec.md § C, § I
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple, Union
import numpy as np
import pandas as pd

from integrations.ibm_architecture.contracts import Action, ReasonCode


class CapacityGovernor:
    """Capacity Governor that throttles escalation volume to match analyst capacity.

    Supports both fixed case quotas (e.g. K = 130) and cohort-relative budget fractions
    (e.g. B_frac = M * p_prev), preventing synthetic budgets from starving large real-data cohorts.
    """

    def __init__(
        self,
        capacity: Optional[int] = None,
        budget_fraction: Optional[float] = None,
        priority_col: str = "p",
        action_col: str = "action",
        reason_col: str = "reason",
    ) -> None:
        if capacity is None and budget_fraction is None:
            raise ValueError("Either 'capacity' (int) or 'budget_fraction' (float) must be specified.")
        if capacity is not None and capacity < 0:
            raise ValueError(f"Capacity cannot be negative: {capacity}")
        if budget_fraction is not None and (budget_fraction <= 0.0 or budget_fraction > 1.0):
            raise ValueError(f"budget_fraction must be in (0, 1], got {budget_fraction}")

        self.capacity = capacity
        self.budget_fraction = budget_fraction
        self.priority_col = priority_col
        self.action_col = action_col
        self.reason_col = reason_col

    def resolve_effective_capacity(self, n_samples: int) -> int:
        """Resolve the effective integer quota K for a cohort of size n_samples."""
        if self.capacity is not None:
            return self.capacity
        assert self.budget_fraction is not None
        return int(np.floor(n_samples * self.budget_fraction))

    def govern(
        self,
        df: pd.DataFrame,
        id_col: Optional[str] = None,
    ) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """Apply capacity governance to routed decision rows.

        Returns:
            governed_df: DataFrame with updated action, reason, governor_status, and lane_rank.
            metrics: Exact operational metrics (requested, admitted, deferred, touched_rate).
        """
        total_transactions = len(df)
        effective_k = self.resolve_effective_capacity(total_transactions)

        if total_transactions == 0:
            return df.copy(), {
                "total_transactions": 0,
                "effective_capacity": effective_k,
                "requested_escalations": 0,
                "admitted_alerts": 0,
                "admitted_reviews": 0,
                "deferred_count": 0,
                "routine_count": 0,
                "touched_count": 0,
                "touched_rate": 0.0,
                "deferred_rate": 0.0,
                "capacity_exhausted": False,
            }

        out_df = df.copy()

        # Initialize governor tracking columns
        out_df["governor_status"] = "not_applicable"
        out_df["lane_rank"] = None

        # Identify candidate escalations
        escalation_mask = out_df[self.action_col].isin(["FRAUD_ALERT", "MANUAL_REVIEW"])
        requested_count = int(escalation_mask.sum())

        if requested_count == 0:
            return out_df, {
                "total_transactions": total_transactions,
                "effective_capacity": effective_k,
                "requested_escalations": 0,
                "admitted_alerts": 0,
                "admitted_reviews": 0,
                "deferred_count": 0,
                "routine_count": total_transactions,
                "touched_count": 0,
                "touched_rate": 0.0,
                "deferred_rate": 0.0,
                "capacity_exhausted": False,
            }

        # Extract candidate indices
        candidate_indices = out_df[escalation_mask].index.tolist()
        candidate_df = out_df.loc[candidate_indices].copy()

        # Ensure priority column exists
        if self.priority_col not in candidate_df.columns:
            candidate_df[self.priority_col] = 0.0

        # Replace NaN in priority with -1.0 so valid scores rank higher
        candidate_df["_sort_priority"] = candidate_df[self.priority_col].fillna(-1.0)

        # Deterministic sorting: highest priority first, then tie-breaker
        if id_col is not None and id_col in candidate_df.columns:
            candidate_df = candidate_df.sort_values(
                by=["_sort_priority", id_col],
                ascending=[False, True],
                kind="mergesort",
            )
        else:
            candidate_df = candidate_df.sort_values(
                by="_sort_priority",
                ascending=False,
                kind="mergesort",
            )

        ranked_indices = candidate_df.index.tolist()
        admitted_indices = ranked_indices[:effective_k]
        deferred_indices = ranked_indices[effective_k:]

        # Update admitted candidates
        for rank, idx in enumerate(admitted_indices, start=1):
            out_df.loc[idx, "governor_status"] = "admitted"
            out_df.loc[idx, "lane_rank"] = rank

        # Update deferred candidates: shunted to DEFERRED / R6_CAPACITY_DEFERRED
        for rank, idx in enumerate(deferred_indices, start=len(admitted_indices) + 1):
            out_df.loc[idx, self.action_col] = "DEFERRED"
            out_df.loc[idx, self.reason_col] = "R6_CAPACITY_DEFERRED"
            out_df.loc[idx, "governor_status"] = "deferred"
            out_df.loc[idx, "lane_rank"] = rank

        # Calculate exact metrics
        admitted_alerts = int((out_df[self.action_col] == "FRAUD_ALERT").sum())
        admitted_reviews = int(
            ((out_df[self.action_col] == "MANUAL_REVIEW") & (out_df["governor_status"] == "admitted")).sum()
        )
        deferred_count = len(deferred_indices)
        routine_count = int((out_df[self.action_col] == "ROUTINE").sum())

        touched_count = admitted_alerts + admitted_reviews
        touched_rate = round(float(touched_count / total_transactions), 6)
        deferred_rate = round(float(deferred_count / total_transactions), 6)

        metrics = {
            "total_transactions": total_transactions,
            "effective_capacity": effective_k,
            "requested_escalations": requested_count,
            "admitted_alerts": admitted_alerts,
            "admitted_reviews": admitted_reviews,
            "deferred_count": deferred_count,
            "routine_count": routine_count,
            "touched_count": touched_count,
            "touched_rate": touched_rate,
            "deferred_rate": deferred_rate,
            "capacity_exhausted": deferred_count > 0,
        }

        return out_df, metrics
