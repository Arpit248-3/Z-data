"""SignalGate IBM Architecture Integration — Validated Data Contracts.

Pydantic V2 data contracts defining the interface for deterministic routing,
cryptographic audit records, verified factual claims, and advisory proposals.

Governing Specification: docs/ibm_architecture_integration_master_spec.md § C3, § F
"""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from typing import Any, Dict, List, Literal, Optional, Union
from pydantic import BaseModel, ConfigDict, Field, field_validator

ZERO_HASH: str = "0" * 64
SHA256_PATTERN: str = r"^[0-9a-f]{64}$"

# Action and ReasonCode literals conforming to Blueprint § 7 and reference schemas
Action = Literal["ROUTINE", "FRAUD_ALERT", "MANUAL_REVIEW", "HELD", "DEFERRED"]

ReasonCode = Literal[
    "R0_SIGNAL_UNAVAILABLE",
    "R1_HIGH_RISK",
    "R2_INTERMEDIATE_RISK",
    "R3_MODEL_DISAGREEMENT",
    "R4_UNFAMILIAR_INPUT",
    "R5_LOW_RISK_RELIABLE",
    "R6_QUEUE_CAPACITY",
    "R6_CAPACITY_DEFERRED",
]


class AuditRecord(BaseModel):
    """One deterministic routing decision for the append-only cryptographic audit ledger."""

    model_config = ConfigDict(extra="forbid", validate_assignment=True)

    id: str = Field(min_length=1, description="Unique case/record identifier")
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Timezone-aware UTC timestamp of decision",
    )
    seq: int = Field(default=0, ge=0, description="Monotonically increasing sequence number")
    prev_hash: str = Field(
        default=ZERO_HASH,
        pattern=SHA256_PATTERN,
        description="SHA-256 fingerprint of the previous ledger entry",
    )
    p: Optional[float] = Field(default=None, ge=0.0, le=1.0, description="Calibrated fraud probability")
    u: Optional[float] = Field(default=None, description="Disagreement signal (e.g. u2 rank residual)")
    u2: Optional[float] = Field(default=None, description="Explicit u2 rank residual alias")
    n: Optional[float] = Field(default=None, ge=0.0, description="Novelty signal score")
    u_method: Optional[str] = Field(default="u2_rank_residual", description="Disagreement method name")
    action: Action = Field(description="Deterministic routed action")
    reason: ReasonCode = Field(description="Action justification reason code")
    cfg_hash: str = Field(pattern=SHA256_PATTERN, description="Frozen policy configuration hash")
    split_hash: str = Field(pattern=SHA256_PATTERN, description="Partition split hash")
    record_hash: str = Field(
        default=ZERO_HASH,
        pattern=SHA256_PATTERN,
        description="Cryptographic SHA-256 fingerprint of this record",
    )
    signature: str = Field(default="", description="Optional cryptographic signature / HMAC")

    @field_validator("timestamp")
    @classmethod
    def timestamp_must_be_timezone_aware(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("timestamp must include explicit timezone information (UTC required)")
        return value

    def compute_record_hash(self) -> str:
        """Deterministically compute SHA-256 record hash over canonical serialized fields."""
        payload = {
            "id": self.id,
            "timestamp": self.timestamp.isoformat(),
            "seq": self.seq,
            "prev_hash": self.prev_hash,
            "p": round(self.p, 8) if self.p is not None else None,
            "u": round(self.u, 8) if self.u is not None else None,
            "u2": round(self.u2, 8) if self.u2 is not None else None,
            "n": round(self.n, 8) if self.n is not None else None,
            "u_method": self.u_method,
            "action": self.action,
            "reason": self.reason,
            "cfg_hash": self.cfg_hash,
            "split_hash": self.split_hash,
        }
        canonical_str = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(canonical_str.encode("utf-8")).hexdigest()

    def seal(self) -> "AuditRecord":
        """Compute and set the record_hash, returning self."""
        self.record_hash = self.compute_record_hash()
        return self


class Claim(BaseModel):
    """A structured factual claim that must be independently verified by ClaimVerifier."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    field: str = Field(min_length=1, description="Target field under assertion")
    operator: Literal["eq", "ne", "lt", "lte", "gt", "gte", "in"] = Field(
        description="Comparison operator for verification"
    )
    value: Any = Field(description="Expected comparison value")
    template_id: str = Field(min_length=1, description="Factual claim template identifier")


class AgentRecord(BaseModel):
    """Structured record of an agent execution with provenance metadata."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    agent_id: str = Field(min_length=1, description="Identifier of executing agent")
    record_id: str = Field(min_length=1, description="Case ID investigated")
    status: Literal["ok", "unavailable", "failed", "timed_out"] = Field(
        description="Agent execution status"
    )
    claims: List[Claim] = Field(
        default_factory=list,
        description="List of structured claims asserted by the agent",
    )
    input_hash: str = Field(pattern=SHA256_PATTERN, description="SHA-256 hash of AgentCaseView input")
    cfg_hash: str = Field(pattern=SHA256_PATTERN, description="Active policy configuration hash")
    output_hash: Optional[str] = Field(
        default=None,
        pattern=SHA256_PATTERN,
        description="SHA-256 hash of serialized agent response",
    )
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Timezone-aware UTC timestamp of agent run",
    )

    @field_validator("timestamp")
    @classmethod
    def timestamp_must_be_timezone_aware(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("timestamp must include explicit timezone information (UTC required)")
        return value


class Proposal(BaseModel):
    """Advisory policy-change proposal generated by drift sentinel or supervisor.

    In compliance with Master Spec § C3, this represents an advisory proposal only;
    it never mutates active runtime policy without external human gate authorization.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    proposal_id: str = Field(min_length=1, description="Unique proposal identifier")
    base_cfg_hash: str = Field(pattern=SHA256_PATTERN, description="Configuration hash being adapted")
    changes: Dict[str, Any] = Field(description="Dictionary of proposed parameter adjustments")
    rationale: str = Field(min_length=1, description="Empirical or statistical justification")
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Timezone-aware UTC timestamp of proposal creation",
    )

    @field_validator("created_at")
    @classmethod
    def timestamp_must_be_timezone_aware(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("created_at must include explicit timezone information (UTC required)")
        return value


class ModelArtifactManifest(BaseModel):
    """Model checkpoint provenance manifest capturing exact architecture and split identity."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    model_id: str = Field(min_length=1)
    estimator_name: str = Field(min_length=1)
    n_features: int = Field(gt=0)
    calibrator_type: str = Field(min_length=1)
    dataset_source: str = Field(min_length=1)
    dataset_sha256: str = Field(pattern=SHA256_PATTERN)
    split_hash: str = Field(pattern=SHA256_PATTERN)
    model_sha256: str = Field(pattern=SHA256_PATTERN)
    calibrator_sha256: str = Field(pattern=SHA256_PATTERN)
    created_at: str = Field(min_length=1)
