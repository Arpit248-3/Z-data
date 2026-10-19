"""SignalGate IBM Architecture Integration — Frozen Policy Configuration.

Encapsulates frozen policy parameters, thresholds, and workload multiples for the
real IEEE-CIS fraud detection pipeline, isolated from root synthetic policies.

Governing Specification: docs/ibm_architecture_integration_master_spec.md § C, § I
"""

from __future__ import annotations

import hashlib
import json
from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, ConfigDict, Field, model_validator


class IEEEPolicyConfig(BaseModel):
    """Pydantic model representing frozen policy configuration for IEEE-CIS integration."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    status: str = Field(default="FROZEN_IEEE_CIS_V1")
    t_alert: float = Field(default=0.084705, ge=0.0, le=1.0, description="Fraud alert probability threshold")
    t_review: float = Field(default=0.071002, ge=0.0, le=1.0, description="Manual review probability threshold")
    u_threshold: float = Field(default=0.526773, ge=0.0, description="Epistemic disagreement threshold")
    disagreement_enabled: bool = Field(default=True, description="Whether disagreement routing is enabled")
    disagreement_variant: Literal["u2_rank_residual", "std_dev"] = Field(
        default="u2_rank_residual", description="Disagreement estimation variant"
    )
    novelty_enabled: bool = Field(default=False, description="Whether novelty routing is enabled")
    n_threshold: Optional[float] = Field(default=None, description="Novelty threshold if enabled")
    target_budget: float = Field(default=0.06525, gt=0.0, le=1.0, description="Target review budget fraction")
    workload_multiples: List[float] = Field(
        default_factory=lambda: [1.0, 1.5, 2.0, 3.0],
        description="Registered workload multiples M * prevalence",
    )
    primary_workload_multiple: float = Field(default=1.5, description="Primary benchmark workload multiple")
    reference_prevalence: float = Field(default=0.03383, gt=0.0, le=1.0, description="Holdout test fraud prevalence")
    disagreement_weight_lambda: float = Field(
        default=0.0, description="P5 candidate ranking lambda (Score = p + lambda * u). Frozen reference is 0.0"
    )

    @model_validator(mode="after")
    def validate_threshold_ordering(self) -> "IEEEPolicyConfig":
        if self.t_review >= self.t_alert:
            raise ValueError(
                f"Invalid threshold ordering: t_review ({self.t_review}) must be strictly less than t_alert ({self.t_alert})"
            )
        if self.novelty_enabled and self.n_threshold is None:
            raise ValueError("Novelty is enabled but n_threshold is not specified")
        return self

    def compute_cfg_hash(self) -> str:
        """Deterministically compute SHA-256 fingerprint over canonical config fields."""
        payload = {
            "status": self.status,
            "t_alert": round(self.t_alert, 8),
            "t_review": round(self.t_review, 8),
            "u_threshold": round(self.u_threshold, 8),
            "disagreement_enabled": self.disagreement_enabled,
            "disagreement_variant": self.disagreement_variant,
            "novelty_enabled": self.novelty_enabled,
            "n_threshold": round(self.n_threshold, 8) if self.n_threshold is not None else None,
            "target_budget": round(self.target_budget, 8),
            "primary_workload_multiple": round(self.primary_workload_multiple, 4),
            "reference_prevalence": round(self.reference_prevalence, 8),
            "disagreement_weight_lambda": round(self.disagreement_weight_lambda, 8),
        }
        canonical_str = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(canonical_str.encode("utf-8")).hexdigest()

    def get_effective_workload_budget(self, multiple: Optional[float] = None) -> float:
        """Calculate effective review budget fraction B_frac = M * prevalence."""
        m = multiple if multiple is not None else self.primary_workload_multiple
        return float(m * self.reference_prevalence)


def get_frozen_ieee_policy_config() -> IEEEPolicyConfig:
    """Return immutable instance of the approved frozen IEEE-CIS policy configuration."""
    return IEEEPolicyConfig()
