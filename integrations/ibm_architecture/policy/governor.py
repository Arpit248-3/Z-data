r"""SignalGate IBM Architecture Integration — Governed Capacity Manager.

Enforces strict review capacity limits ($B = 130$ cases, target $6.525\%$ budget)
with fail-closed deferred queue management in compliance with Master Spec § D & § I:
- Throttles requested escalations to fit analyst review capacity.
- Deterministically prioritizes candidates by calibrated risk score with stable tie-breaking.
- Assigns excess candidates to Action.DEFERRED / ReasonCode.R6_CAPACITY_DEFERRED.
- Invariant: Deferred cases can NEVER silently convert to ROUTINE or disappear.
- Implements exact touched-rate accounting: (admitted_alerts + admitted_reviews) / total.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple
import numpy as np
import pandas as pd

from policy.governor import CapacityGovernor
from policy.router import Action, ReasonCode


class GovernedCapacityManager:
    """Manages operational triage review quotas and deferred escalation queues."""

    def __init__(
        self,
        capacity: int = 130,
        target_budget_fraction: float = 0.06525,
        priority_signal: str = "p_cal",
    ) -> None:
        if capacity < 0:
            raise ValueError(f"Review capacity cannot be negative: {capacity}")
        self.capacity = int(capacity)
        self.target_budget_fraction = float(target_budget_fraction)
        self.priority_signal = priority_signal
        self._governor = CapacityGovernor(
            capacity=self.capacity,
            priority_signal=self.priority_signal,
            action_col="action",
            reason_col="reason",
        )

    def govern_batch(
        self,
        df: pd.DataFrame,
        id_col: Optional[str] = None,
    ) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """Apply operational review capacity governance to routed decision records.

        Returns:
            governed_df: DataFrame with updated 'action', 'reason', 'governor_status', 'lane_rank'.
            metrics: Capacity accounting metrics.
        """
        # Ensure priority signal column exists; fallback to 'p' if 'p_cal' is not present
        df_in = df.copy()
        if self.priority_signal not in df_in.columns and "p" in df_in.columns:
            df_in[self.priority_signal] = df_in["p"]

        governed_df, metrics = self._governor.govern(df_in, id_col=id_col)

        # Enforce invariant checks
        deferred_mask = governed_df["action"] == Action.DEFERRED.value
        if deferred_mask.any():
            # Verify all deferred records carry reason R6_CAPACITY_DEFERRED
            reasons = governed_df.loc[deferred_mask, "reason"].unique()
            assert all(r == ReasonCode.R6_CAPACITY_DEFERRED.value for r in reasons), (
                f"Invariant violation: Deferred records found with non-R6 reason: {reasons}"
            )

        return governed_df, metrics

    def calculate_capacity_for_cohort(self, total_cases: int) -> int:
        """Derive integer capacity K from target budget fraction and cohort size."""
        return int(np.floor(self.target_budget_fraction * total_cases))
