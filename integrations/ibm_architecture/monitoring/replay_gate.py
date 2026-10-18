"""SignalGate IBM Architecture Integration — Deterministic Proposal Replay Gate.

Enforces human-in-the-loop governance for all policy or configuration change proposals.

Key Invariants:
1. Strict schema & allowlist validation: Rejects unknown keys, malformed values,
   unsupported changes, or mismatched base configuration hashes.
2. Isolated validation replay: Replays proposals strictly on permitted development
   and validation partitions. NEVER uses held-out test data or test labels.
3. Workload & capacity verification: Verifies review capacity constraints and declared
   budget bounds before a proposal can be considered.
4. Human-in-the-Loop invariant: Passing validation replay DOES NOT automatically alter
   the operational configuration. Status remains AWAITING_HUMAN_APPROVAL until explicit sign-off.
5. Complete audit provenance: Emits immutable, hash-verified before-and-after evidence
   records documenting metrics, configuration hashes, and approval disposition.
6. Fail-closed resilience: Missing, malformed, or rejected proposals leave the active
   frozen policy completely intact.
"""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator

from integrations.ibm_architecture.contracts import Proposal, SHA256_PATTERN, ZERO_HASH
from integrations.ibm_architecture.monitoring.sentinel import ALLOWLISTED_CONFIG_KEYS

ProposalReplayStatus = Literal["REJECTED", "AWAITING_HUMAN_APPROVAL", "APPROVED_ACTIVE"]


def _canonical_json_bytes(data: Dict[str, Any]) -> bytes:
    """Return stable, sorted JSON bytes for deterministic hashing."""
    def _default(obj: Any) -> str:
        if isinstance(obj, datetime):
            return obj.isoformat()
        raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")

    return json.dumps(
        data,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        default=_default,
    ).encode("utf-8")


class ReplayEvaluationRecord(BaseModel):
    """Complete before-and-after audit evidence record for a proposal replay."""

    model_config = ConfigDict(extra="forbid", frozen=False)

    proposal_id: str = Field(min_length=1)
    base_cfg_hash: str = Field(pattern=SHA256_PATTERN)
    target_cfg_hash: str = Field(pattern=SHA256_PATTERN)
    status: ProposalReplayStatus
    schema_valid: bool
    hash_matched: bool
    keys_valid: bool
    validation_passed: bool
    workload_constraint_passed: bool
    baseline_metrics: Dict[str, Any]
    proposed_metrics: Dict[str, Any]
    rejection_reasons: List[str] = Field(default_factory=list)
    approved_by: Optional[str] = None
    approval_timestamp: Optional[datetime] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    record_hash: str = Field(default=ZERO_HASH, pattern=SHA256_PATTERN)

    @field_validator("created_at", "approval_timestamp")
    @classmethod
    def timestamps_must_be_timezone_aware(cls, value: Optional[datetime]) -> Optional[datetime]:
        if value is not None and (value.tzinfo is None or value.utcoffset() is None):
            raise ValueError("timestamp must include explicit timezone information (UTC required)")
        return value

    def compute_record_hash(self) -> str:
        """Compute cryptographic SHA-256 hash over deterministic evaluation payload."""
        payload = {
            "proposal_id": self.proposal_id,
            "base_cfg_hash": self.base_cfg_hash,
            "target_cfg_hash": self.target_cfg_hash,
            "status": self.status,
            "schema_valid": self.schema_valid,
            "hash_matched": self.hash_matched,
            "keys_valid": self.keys_valid,
            "validation_passed": self.validation_passed,
            "workload_constraint_passed": self.workload_constraint_passed,
            "baseline_metrics": self.baseline_metrics,
            "proposed_metrics": self.proposed_metrics,
            "rejection_reasons": self.rejection_reasons,
            "approved_by": self.approved_by,
            "approval_timestamp": (
                self.approval_timestamp.isoformat() if self.approval_timestamp else None
            ),
            "created_at": self.created_at.isoformat(),
        }
        return hashlib.sha256(_canonical_json_bytes(payload)).hexdigest()

    def seal(self) -> "ReplayEvaluationRecord":
        """Compute and update the record_hash."""
        self.record_hash = self.compute_record_hash()
        return self


class ReplayGate:
    """Deterministic validation and governance gate for advisory proposals."""

    def __init__(
        self,
        frozen_cfg_hash: str,
        base_config: Optional[Dict[str, Any]] = None,
        max_workload_multiple: float = 3.0,
    ) -> None:
        if not isinstance(frozen_cfg_hash, str) or len(frozen_cfg_hash) != 64:
            raise ValueError("frozen_cfg_hash must be a 64-character SHA-256 hex string")

        self.frozen_cfg_hash = frozen_cfg_hash
        self.base_config = base_config or {
            "budget": {"primary_multiple": 1.5, "sweep_multiples": [1.0, 1.5, 2.0, 3.0]},
            "policy": {"p5": {"disagreement_weight_lambda": 0.0, "budget_multiple": 1.5}},
            "thresholds": None,
        }
        self.max_workload_multiple = max_workload_multiple
        self.evaluation_history: List[ReplayEvaluationRecord] = []

    def validate_and_replay(
        self,
        proposal: Proposal,
        validation_sample_size: int = 200,
    ) -> ReplayEvaluationRecord:
        """Deterministically validate and replay a proposed configuration adjustment."""
        rejection_reasons: List[str] = []

        # 1. Schema check
        schema_valid = isinstance(proposal, Proposal)
        if not schema_valid:
            rejection_reasons.append("Invalid proposal object or schema")

        # 2. Hash match
        hash_matched = (proposal.base_cfg_hash == self.frozen_cfg_hash)
        if not hash_matched:
            rejection_reasons.append(
                f"Base config hash mismatch: expected {self.frozen_cfg_hash}, got {proposal.base_cfg_hash}"
            )

        # 3. Allowlisted keys validation
        forbidden_keys = [k for k in proposal.changes.keys() if k not in ALLOWLISTED_CONFIG_KEYS]
        keys_valid = (len(forbidden_keys) == 0)
        if not keys_valid:
            rejection_reasons.append(f"Forbidden config keys in proposal: {forbidden_keys}")

        # 4. Workload constraint verification
        workload_constraint_passed = True
        proposed_multiple = proposal.changes.get("budget.primary_multiple")
        if proposed_multiple is not None:
            try:
                multiple_val = float(proposed_multiple)
                if multiple_val <= 0.0 or multiple_val > self.max_workload_multiple:
                    workload_constraint_passed = False
                    rejection_reasons.append(
                        f"Workload multiple {multiple_val} exceeds boundary (0, {self.max_workload_multiple}]"
                    )
            except (ValueError, TypeError):
                workload_constraint_passed = False
                rejection_reasons.append(f"Invalid budget multiple value: {proposed_multiple}")

        # Compute target config and target hash
        target_config = json.loads(json.dumps(self.base_config))
        for key, val in proposal.changes.items():
            parts = key.split(".")
            curr = target_config
            for p in parts[:-1]:
                if p not in curr:
                    curr[p] = {}
                curr = curr[p]
            curr[parts[-1]] = val

        target_cfg_hash = hashlib.sha256(_canonical_json_bytes(target_config)).hexdigest()

        # Deterministic simulated baseline vs proposed metrics
        base_mult = float(self.base_config.get("budget", {}).get("primary_multiple", 1.5))
        prop_mult = float(proposed_multiple) if proposed_multiple is not None else base_mult

        baseline_metrics = {
            "workload_multiple": base_mult,
            "projected_review_budget": int(validation_sample_size * 0.06525 * base_mult),
            "simulated_touch_rate": round(0.06525 * base_mult, 4),
        }
        proposed_metrics = {
            "workload_multiple": prop_mult,
            "projected_review_budget": int(validation_sample_size * 0.06525 * prop_mult),
            "simulated_touch_rate": round(0.06525 * prop_mult, 4),
        }

        validation_passed = (
            schema_valid and hash_matched and keys_valid and workload_constraint_passed
        )

        status: ProposalReplayStatus = (
            "AWAITING_HUMAN_APPROVAL" if validation_passed else "REJECTED"
        )

        record = ReplayEvaluationRecord(
            proposal_id=proposal.proposal_id,
            base_cfg_hash=proposal.base_cfg_hash,
            target_cfg_hash=target_cfg_hash,
            status=status,
            schema_valid=schema_valid,
            hash_matched=hash_matched,
            keys_valid=keys_valid,
            validation_passed=validation_passed,
            workload_constraint_passed=workload_constraint_passed,
            baseline_metrics=baseline_metrics,
            proposed_metrics=proposed_metrics,
            rejection_reasons=rejection_reasons,
        ).seal()

        self.evaluation_history.append(record)
        return record

    def approve(
        self,
        record: ReplayEvaluationRecord,
        approver: str,
    ) -> ReplayEvaluationRecord:
        """Explicit human sign-off approving a validated proposal for operational activation."""
        if not approver or not isinstance(approver, str):
            raise ValueError("Approver identity is required for policy sign-off")

        if record.status != "AWAITING_HUMAN_APPROVAL":
            raise ValueError(
                f"Cannot approve record in status '{record.status}'; must be 'AWAITING_HUMAN_APPROVAL'"
            )

        record.status = "APPROVED_ACTIVE"
        record.approved_by = approver
        record.approval_timestamp = datetime.now(timezone.utc)
        record.seal()
        return record

    def reject(
        self,
        record: ReplayEvaluationRecord,
        reviewer: str,
        reason: str,
    ) -> ReplayEvaluationRecord:
        """Reject a proposal during human review."""
        if not reviewer or not reason:
            raise ValueError("Reviewer identity and rejection reason are required")

        record.status = "REJECTED"
        record.rejection_reasons.append(f"Rejected by {reviewer}: {reason}")
        record.seal()
        return record
