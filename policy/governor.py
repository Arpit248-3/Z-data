"""
SignalGate Capacity Governor
Implements capacity-constrained escalation management:
- Accepts candidate escalations from the router (FRAUD_ALERT, MANUAL_REVIEW).
- Enforces an analyst capacity limit (K cases or budget fraction).
- Deterministically prioritizes candidates by risk score p with stable tie-breaking.
- Marks cases exceeding capacity as DEFERRED / R6_CAPACITY_DEFERRED.
- Strictly prevents deferred cases from being reclassified as ROUTINE or disappearing.
- Implements exact touched-rate accounting:
    touched_rate = (FRAUD_ALERT + MANUAL_REVIEW) / total_transactions
- Tracks and reports deferred cases separately.
"""

from typing import Any, Dict, List, Optional, Tuple, Union
import numpy as np
import pandas as pd

from policy.router import Action, ReasonCode


class CapacityGovernor:
    """
    Capacity Governor that throttles escalation volume to match analyst capacity.
    """

    def __init__(
        self,
        capacity: int,
        priority_col: str = "p",
        action_col: str = "action",
        reason_col: str = "reason",
        priority_signal: Optional[str] = None,
    ):
        if capacity < 0:
            raise ValueError(f"Capacity cannot be negative: {capacity}")
        self.capacity = capacity
        self.priority_col = priority_signal if priority_signal is not None else priority_col
        self.action_col = action_col
        self.reason_col = reason_col

    def govern(
        self,
        df: pd.DataFrame,
        id_col: Optional[str] = None,
    ) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """
        Apply capacity governance to routed decision rows.

        Returns:
        - governed_df: DataFrame with updated action, reason, governor_status, and lane_rank.
        - metrics: Governance metrics (requested, admitted, deferred, touched_rate).
        """
        if len(df) == 0:
            return df.copy(), {
                "total_transactions": 0,
                "capacity": self.capacity,
                "requested_escalations": 0,
                "admitted_alerts": 0,
                "admitted_reviews": 0,
                "deferred_count": 0,
                "routine_count": 0,
                "touched_count": 0,
                "touched_rate": 0.0,
                "deferred_rate": 0.0,
            }

        out_df = df.copy()

        # Initialize governor tracking columns
        out_df["governor_status"] = "not_applicable"
        out_df["lane_rank"] = None

        # Identify candidate escalations
        escalation_mask = out_df[self.action_col].isin([
            Action.FRAUD_ALERT.value,
            Action.MANUAL_REVIEW.value,
            "FRAUD_ALERT",
            "MANUAL_REVIEW",
        ])

        total_transactions = len(out_df)
        requested_count = int(escalation_mask.sum())

        if requested_count == 0:
            return out_df, {
                "total_transactions": total_transactions,
                "capacity": self.capacity,
                "requested_escalations": 0,
                "admitted_alerts": 0,
                "admitted_reviews": 0,
                "deferred_count": 0,
                "routine_count": total_transactions,
                "touched_count": 0,
                "touched_rate": 0.0,
                "deferred_rate": 0.0,
            }

        # Extract candidate indices
        candidate_indices = out_df[escalation_mask].index.tolist()

        # Deterministic sorting of candidates by priority descending, then secondary tie-breaker
        candidate_df = out_df.loc[candidate_indices].copy()

        # Ensure priority column exists
        if self.priority_col not in candidate_df.columns:
            candidate_df[self.priority_col] = 0.0

        # Replace NaN in priority with -1.0 so valid scores rank higher
        candidate_df["_sort_priority"] = candidate_df[self.priority_col].fillna(-1.0)

        if id_col is not None and id_col in candidate_df.columns:
            # Deterministic secondary tie-breaker by ID
            candidate_df = candidate_df.sort_values(
                by=["_sort_priority", id_col],
                ascending=[False, True],
                kind="mergesort",
            )
        else:
            # Stable sort preserving original index order for ties
            candidate_df = candidate_df.sort_values(
                by="_sort_priority",
                ascending=False,
                kind="mergesort",
            )

        ranked_indices = candidate_df.index.tolist()

        admitted_indices = ranked_indices[: self.capacity]
        deferred_indices = ranked_indices[self.capacity :]

        # Update admitted candidates
        for rank, idx in enumerate(admitted_indices, start=1):
            out_df.loc[idx, "governor_status"] = "admitted"
            out_df.loc[idx, "lane_rank"] = rank

        # Update deferred candidates
        for rank, idx in enumerate(deferred_indices, start=len(admitted_indices) + 1):
            out_df.loc[idx, self.action_col] = Action.DEFERRED.value
            out_df.loc[idx, self.reason_col] = ReasonCode.R6_CAPACITY_DEFERRED.value
            out_df.loc[idx, "governor_status"] = "deferred"
            out_df.loc[idx, "lane_rank"] = rank

        # Calculate exact metrics
        admitted_alerts = int((out_df[self.action_col] == Action.FRAUD_ALERT.value).sum())
        admitted_reviews = int(
            ((out_df[self.action_col] == Action.MANUAL_REVIEW.value) & (out_df["governor_status"] == "admitted")).sum()
        )
        deferred_count = len(deferred_indices)
        routine_count = int((out_df[self.action_col] == Action.ROUTINE.value).sum())

        touched_count = admitted_alerts + admitted_reviews
        touched_rate = round(float(touched_count / total_transactions), 6)
        deferred_rate = round(float(deferred_count / total_transactions), 6)

        metrics = {
            "total_transactions": total_transactions,
            "capacity": self.capacity,
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


def govern_decisions(
    df: pd.DataFrame,
    capacity: int,
    priority_col: str = "p",
    id_col: Optional[str] = None,
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """Convenience helper to apply capacity governor."""
    governor = CapacityGovernor(capacity=capacity, priority_col=priority_col)
    return governor.govern(df, id_col=id_col)
