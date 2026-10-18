"""SignalGate IBM Architecture Integration — Sanitized Agent Views.

Defines allowlisted, sanitized case views for governed multi-agent triage.
Strictly enforces Ground-Truth Quarantine (Master Spec § C2) by forbidding
and rejecting raw feature matrices, labels (isFraud, target, label), and raw
transaction identifiers (TransactionID, TransactionDT).
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Set, Tuple
from pydantic import BaseModel, ConfigDict, Field, model_validator

from integrations.ibm_architecture.contracts import Action, AuditRecord, ReasonCode, SHA256_PATTERN
from integrations.ibm_architecture.exceptions import LeakageViolationError

# Quarantined keys that must NEVER enter agent views, prompts, or model features
QUARANTINED_FIELDS: Set[str] = {
    "isfraud",
    "is_fraud",
    "true_label",
    "target",
    "label",
    "ground_truth",
    "transactionid",
    "transaction_id",
    "transactiondt",
    "transaction_dt",
}


def check_for_quarantine_violations(data: Any, context: str = "AgentCaseView") -> None:
    """Inspect input dictionary or attributes for forbidden quarantined fields."""
    if isinstance(data, dict):
        keys_lower = {str(k).lower(): k for k in data.keys()}
        violations = [keys_lower[q] for q in QUARANTINED_FIELDS if q in keys_lower]
        if violations:
            raise LeakageViolationError(
                f"Ground-truth quarantine violation in {context}. "
                f"Fields {violations} are evaluation-only and strictly prohibited.",
                violated_fields=violations,
                context=context,
            )


class AgentCaseView(BaseModel):
    """The strictly allowlisted information permitted to reach governed agents.

    Never pass source DataFrames, raw transaction features, or true labels.
    Construct views exclusively from verified, sealed AuditRecords.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    record_id: str = Field(min_length=1, description="Sanitized record identifier")
    p: Optional[float] = Field(default=None, ge=0.0, le=1.0, description="Calibrated posterior probability")
    u: Optional[float] = Field(default=None, description="Disagreement residual signal")
    u2: Optional[float] = Field(default=None, description="Explicit u2 residual signal")
    n: Optional[float] = Field(default=None, ge=0.0, description="Novelty score")
    action: Action = Field(description="Deterministic routed action")
    reason: ReasonCode = Field(description="Deterministic reason code")
    record_hash: str = Field(pattern=SHA256_PATTERN, description="Cryptographic fingerprint of audit record")
    cfg_hash: str = Field(pattern=SHA256_PATTERN, description="Frozen policy hash")
    split_hash: str = Field(pattern=SHA256_PATTERN, description="Partition split hash")

    def __init__(self, **data: Any) -> None:
        check_for_quarantine_violations(data, context="AgentCaseView")
        super().__init__(**data)

    @model_validator(mode="before")
    @classmethod
    def enforce_ground_truth_quarantine(cls, data: Any) -> Any:
        """Reject any attempt to instantiate an AgentCaseView with quarantined columns."""
        check_for_quarantine_violations(data, context="AgentCaseView")
        return data

    @classmethod
    def from_audit_record(cls, record: AuditRecord) -> "AgentCaseView":
        """Build an allowlisted, sanitized view strictly from an AuditRecord."""
        if not isinstance(record, AuditRecord):
            raise TypeError(f"from_audit_record requires an AuditRecord, got {type(record).__name__}")
        
        # Ensure the record was sealed
        rec_hash = record.record_hash
        if not rec_hash or rec_hash == "0" * 64:
            rec_hash = record.compute_record_hash()

        return cls(
            record_id=record.id,
            p=record.p,
            u=record.u,
            u2=record.u2,
            n=record.n,
            action=record.action,
            reason=record.reason,
            record_hash=rec_hash,
            cfg_hash=record.cfg_hash,
            split_hash=record.split_hash,
        )


class AgentView(BaseModel):
    """Immutable collection container for multiple sanitized agent case views."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    cases: Tuple[AgentCaseView, ...] = Field(
        default_factory=tuple,
        description="Immutable tuple of allowlisted agent case views",
    )

    def __init__(self, **data: Any) -> None:
        check_for_quarantine_violations(data, context="AgentView")
        super().__init__(**data)

    @model_validator(mode="before")
    @classmethod
    def _support_records_kwarg(cls, data: Any) -> Any:
        if isinstance(data, dict):
            check_for_quarantine_violations(data, context="AgentView")
            if "records" in data and "cases" not in data:
                data = dict(data)
                data["cases"] = data.pop("records")
        return data

    @property
    def records(self) -> Tuple[AgentCaseView, ...]:
        """Backward-compatible alias for cases property."""
        return self.cases

    @classmethod
    def from_audit_records(cls, records: List[AuditRecord]) -> "AgentView":
        """Construct container from a list of verified AuditRecords."""
        return cls(cases=tuple(AgentCaseView.from_audit_record(r) for r in records))
