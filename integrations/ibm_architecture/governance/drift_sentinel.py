"""SignalGate IBM Architecture Integration — Advisory Drift Sentinel.

Implements the advisory Drift Sentinel:
- Evaluates incoming DriftReport structures against configurable statistical triggers.
- Generates structured, immutable Proposal objects when covariate or score shift is detected.
- Enforces strict allowlisting: only approved policy parameters may be modified
  (t_alert, t_review, u_threshold, disagreement_weight_lambda, primary_workload_multiple).
- Enforces strict parameter boundary constraints and ordering (t_review < t_alert).
- Binds base_cfg_hash of active policy configuration to ensure proposal provenance.
- Non-negotiable authority barrier: Sentinel produces strictly inert Proposal records
  with zero execution authority; Sentinel cannot directly mutate active runtime policy.

Governing Specification: docs/ibm_architecture_integration_master_spec.md § C, § K
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Set, Tuple
import uuid

from pydantic import BaseModel, ConfigDict, Field

from integrations.ibm_architecture.contracts import Proposal
from integrations.ibm_architecture.governance.drift_monitor import DriftReport
from integrations.ibm_architecture.policy.frozen_policy import IEEEPolicyConfig

# Strict allowlist of policy configuration parameters that may be proposed
ALLOWLISTED_POLICY_KEYS: Set[str] = {
    "t_alert",
    "t_review",
    "u_threshold",
    "disagreement_weight_lambda",
    "primary_workload_multiple",
}

# Approved valid parameter boundaries
PARAMETER_BOUNDS: Dict[str, Tuple[float, float]] = {
    "t_alert": (0.01, 1.0),
    "t_review": (0.01, 1.0),
    "u_threshold": (0.0, 1.0),
    "disagreement_weight_lambda": (0.0, 1.0),
    "primary_workload_multiple": (0.5, 5.0),
}


class SentinelConfig(BaseModel):
    """Configuration criteria determining when the Drift Sentinel produces an advisory proposal."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    psi_moderate_threshold: float = Field(default=0.10, ge=0.0, description="PSI threshold for moderate drift")
    psi_significant_threshold: float = Field(default=0.20, ge=0.0, description="PSI threshold for significant drift")
    score_drift_threshold: float = Field(default=0.15, ge=0.0, description="Score drift PSI trigger threshold")
    mean_psi_alert_threshold: float = Field(default=0.10, ge=0.0, description="Dataset mean PSI trigger threshold")
    max_significant_features: int = Field(default=1, ge=1, description="Number of significant features to trigger")


class DriftSentinel:
    """Advisory Drift Sentinel generating gated policy proposals from drift reports."""

    def __init__(self, config: Optional[SentinelConfig] = None) -> None:
        self.config = config or SentinelConfig()

    def validate_proposal_changes(
        self,
        changes: Dict[str, Any],
        current_policy: Optional[IEEEPolicyConfig] = None,
    ) -> Tuple[bool, Optional[str]]:
        """Validate proposed parameter changes against allowlist, bounds, and ordering rules."""
        if not changes:
            return False, "Proposed changes dictionary cannot be empty."

        # Check for unapproved keys
        unapproved = set(changes.keys()) - ALLOWLISTED_POLICY_KEYS
        if unapproved:
            return False, f"Proposal contains unapproved/prohibited keys: {sorted(unapproved)}"

        # Validate parameter boundaries
        for key, value in changes.items():
            if not isinstance(value, (int, float)):
                return False, f"Value for '{key}' must be numeric, got {type(value).__name__}"
            low, high = PARAMETER_BOUNDS[key]
            if not (low <= float(value) <= high):
                return False, f"Value for '{key}' ({value}) is outside allowed bounds [{low}, {high}]"

        # Validate ordering constraint t_review < t_alert
        t_alert = changes.get("t_alert")
        t_review = changes.get("t_review")
        if current_policy is not None:
            if t_alert is None:
                t_alert = current_policy.t_alert
            if t_review is None:
                t_review = current_policy.t_review

        if t_alert is not None and t_review is not None:
            if float(t_review) >= float(t_alert):
                return False, f"Invalid threshold ordering: t_review ({t_review}) must be < t_alert ({t_alert})"

        return True, None

    def evaluate_drift(
        self,
        drift_report: DriftReport,
        current_policy: IEEEPolicyConfig,
    ) -> Optional[Proposal]:
        """Inspect drift report and emit an advisory Proposal if statistical triggers are breached.

        Authority Barrier:
        The emitted Proposal is strictly advisory. It cannot mutate or activate runtime policy.
        It requires deterministic replay and human authorization before consideration.
        """
        triggers: List[str] = []

        if drift_report.significant_drift_features >= self.config.max_significant_features:
            triggers.append(
                f"{drift_report.significant_drift_features} feature(s) exhibited significant drift (PSI > 0.20)"
            )

        if drift_report.mean_psi >= self.config.mean_psi_alert_threshold:
            triggers.append(
                f"Overall feature mean PSI ({drift_report.mean_psi:.4f}) breached alert threshold ({self.config.mean_psi_alert_threshold})"
            )

        if (
            drift_report.score_drift is not None
            and drift_report.score_drift.psi is not None
            and drift_report.score_drift.psi >= self.config.score_drift_threshold
        ):
            triggers.append(
                f"Calibrated prediction score PSI ({drift_report.score_drift.psi:.4f}) breached threshold ({self.config.score_drift_threshold})"
            )

        # If no statistical drift trigger breached, Sentinel remains silent
        if not triggers:
            return None

        # Formulate conservative proposed parameter adjustment
        proposed_changes: Dict[str, Any] = {}
        rationale_parts: List[str] = [
            f"Advisory adaptation proposed in response to detected distribution shift: {'; '.join(triggers)}."
        ]

        if drift_report.score_drift and drift_report.score_drift.psi and drift_report.score_drift.psi >= self.config.score_drift_threshold:
            # Conservative review threshold adjustment: lower review threshold slightly to inspect borderline ambiguity
            conservative_t_review = max(0.01, round(current_policy.t_review * 0.95, 6))
            proposed_changes["t_review"] = conservative_t_review
            rationale_parts.append(
                f"Suggest lowering review threshold from {current_policy.t_review:.6f} to {conservative_t_review:.6f} to capture borderline transactions."
            )
        else:
            # Adjust epistemic disagreement threshold slightly to prioritize high-uncertainty cases
            conservative_u = round(min(0.95, current_policy.u_threshold * 0.95), 6)
            proposed_changes["u_threshold"] = conservative_u
            rationale_parts.append(
                f"Suggest tightening disagreement threshold from {current_policy.u_threshold:.6f} to {conservative_u:.6f} for enhanced review coverage."
            )

        # Validate proposal changes
        is_valid, err = self.validate_proposal_changes(proposed_changes, current_policy=current_policy)
        if not is_valid:
            return None

        proposal_id = f"prop_{uuid.uuid4().hex[:12]}"
        base_cfg_hash = current_policy.compute_cfg_hash()

        return Proposal(
            proposal_id=proposal_id,
            base_cfg_hash=base_cfg_hash,
            changes=proposed_changes,
            rationale=" ".join(rationale_parts),
            created_at=datetime.now(timezone.utc),
        )
