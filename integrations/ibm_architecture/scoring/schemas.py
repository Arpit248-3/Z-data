"""SignalGate IBM Architecture Integration — Scoring Schemas.

Pydantic schemas for deterministic single-transaction and batch scoring requests and results.

Governing Specification: docs/ibm_architecture_integration_master_spec.md § C, § I
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field

from integrations.ibm_architecture.contracts import Action, ReasonCode


class ScoringRequest(BaseModel):
    """Input payload for single-transaction scoring."""

    model_config = ConfigDict(extra="forbid")

    features: Dict[str, Any] = Field(description="Dictionary of transaction feature values")
    transaction_id: Optional[str] = Field(default=None, description="Optional pseudonymous reference identifier")
    policy_name: str = Field(default="router", description="Target policy adapter ('router', 'b2', 'p5')")


class ScoringResult(BaseModel):
    """Immutable scoring decision record with full provenance."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    transaction_id: Optional[str] = Field(default=None, description="Pseudonymous record identifier")
    p: float = Field(ge=0.0, le=1.0, description="Calibrated fraud probability")
    u: Optional[float] = Field(default=None, description="Disagreement signal (standard deviation)")
    u2: Optional[float] = Field(default=None, description="Robust disagreement signal (rank residual)")
    n: Optional[float] = Field(default=None, description="Novelty signal score")
    action: Action = Field(description="Deterministic routed action")
    reason: ReasonCode = Field(description="Deterministic justification reason code")
    governor_status: str = Field(default="not_applicable", description="Capacity governor status ('admitted', 'deferred', 'not_applicable')")
    lane_rank: Optional[int] = Field(default=None, description="Governor prioritization queue rank")
    model_version: str = Field(description="Architecture and model bundle version")
    policy_version: str = Field(description="Policy configuration status and identity")
    cfg_hash: str = Field(description="SHA-256 fingerprint of the governing policy configuration")
    timestamp_utc: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="Timezone-aware UTC timestamp of scoring",
    )


class BatchScoringResult(BaseModel):
    """Aggregate result holding scored cases and capacity governance metrics."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    results: List[ScoringResult] = Field(description="List of scored transaction results")
    total_transactions: int = Field(ge=0, description="Total transactions in scored batch")
    policy_name: str = Field(description="Policy adapter applied")
    governance_metrics: Dict[str, Any] = Field(description="Capacity governance and quota accounting")
