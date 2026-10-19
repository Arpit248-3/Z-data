"""SignalGate IBM Architecture Integration — Deterministic Replay Gate.

Implements the Replay Gate and human approval lifecycle for policy adaptations:
- Validates proposal schema, base configuration hash match, allowlisted keys, and parameter bounds.
- Deterministically replays proposed policy against the validation partition or scenarios (S0, S1, S2, S3).
- Strictly quarantines the held-out test partition from replay gating and policy selection.
- Calculates comparative metrics: touches, review rate, churn count (decision flips), and capacity adherence.
- Non-negotiable Human Authorization Gate: successful replay transitions proposal status
  to AWAITING_HUMAN_APPROVAL (never automatic activation).
- Explicit human approval (approve_proposal) and rejection (reject_proposal) methods with
  recorded approver identity, timestamp, rationale, and cryptographic AuditChain provenance.
- Failed validation, timeout, or malformed proposals fail closed, leaving active production policy intact.

Governing Specification: docs/ibm_architecture_integration_master_spec.md § C, § K
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
import hashlib
import json
from typing import Any, Dict, List, Optional, Sequence, Tuple, Union

import numpy as np
import pandas as pd
from pydantic import BaseModel, ConfigDict, Field

from integrations.ibm_architecture.contracts import Action, AuditRecord, Proposal
from integrations.ibm_architecture.exceptions import GroundTruthQuarantineError, SignalGateIntegrationError
from integrations.ibm_architecture.governance.audit_chain import AuditChain
from integrations.ibm_architecture.governance.drift_sentinel import DriftSentinel
from integrations.ibm_architecture.policy.frozen_policy import IEEEPolicyConfig
from integrations.ibm_architecture.policy.router import RouterPolicyAdapter


class ProposalStatus(str, Enum):
    """Lifecycle states of an advisory policy change proposal."""

    PENDING = "PENDING"
    REPLAY_VALIDATED = "REPLAY_VALIDATED"
    AWAITING_HUMAN_APPROVAL = "AWAITING_HUMAN_APPROVAL"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    FAILED_VALIDATION = "FAILED_VALIDATION"


class ReplayValidationResult(BaseModel):
    """Immutable result of deterministic validation replay evaluation."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    proposal_id: str = Field(min_length=1, description="Proposal identifier under evaluation")
    scenario_id: str = Field(default="validation", description="Evaluation dataset or scenario partition ID")
    is_valid: bool = Field(description="Whether proposal passed validation checks and replay")
    base_cfg_hash_matches: bool = Field(description="Whether proposal.base_cfg_hash matched active policy")
    allowlist_passed: bool = Field(description="Whether all proposed keys are strictly allowlisted")
    bounds_passed: bool = Field(description="Whether all proposed values satisfy boundary and ordering constraints")
    replay_executed: bool = Field(description="Whether replay simulation successfully ran on validation cases")
    validation_samples: int = Field(ge=0, description="Number of evaluated validation cases")
    baseline_touches: int = Field(ge=0, description="Number of cases touched by baseline policy")
    proposed_touches: int = Field(ge=0, description="Number of cases touched by proposed policy")
    churn_count: int = Field(ge=0, description="Count of cases where triage action changed")
    capacity_exceeded: bool = Field(description="Whether proposed touches breached target capacity budget")
    details: Dict[str, Any] = Field(default_factory=dict, description="Detailed diagnostic metrics")
    rejection_reason: Optional[str] = Field(default=None, description="Explicit failure reason if invalid")


class ReplayGate:
    """Deterministic Replay Gate orchestrating validation replays and human approval gates."""

    def __init__(self, sentinel: Optional[DriftSentinel] = None) -> None:
        self.sentinel = sentinel or DriftSentinel()
        self.proposals: Dict[str, Proposal] = {}
        self.proposal_states: Dict[str, ProposalStatus] = {}
        self.replay_results: Dict[str, ReplayValidationResult] = {}
        self.approval_records: Dict[str, Dict[str, Any]] = {}

    def register_proposal(self, proposal: Proposal) -> None:
        """Register an advisory proposal in the Replay Gate."""
        if not isinstance(proposal, Proposal):
            raise TypeError(f"Expected Proposal, got {type(proposal).__name__}")
        self.proposals[proposal.proposal_id] = proposal
        self.proposal_states[proposal.proposal_id] = ProposalStatus.PENDING

    def validate_and_replay(
        self,
        proposal: Proposal,
        current_policy: IEEEPolicyConfig,
        validation_data: Union[pd.DataFrame, Sequence[Dict[str, Any]]],
        scenario_id: str = "validation",
    ) -> Tuple[ReplayValidationResult, ProposalStatus]:
        """Validate proposal and deterministically replay against permitted validation partition.

        Invariants:
        1. Base config hash must match current_policy.compute_cfg_hash().
        2. Proposed changes must be strictly allowlisted and within valid bounds.
        3. Test partition is strictly quarantined: scenario_id cannot be 'test'.
        4. Replay calculates churn count, touched rate delta, and capacity compliance.
        5. On success, transitions status to AWAITING_HUMAN_APPROVAL. Never auto-activates!
        6. On failure, transitions status to FAILED_VALIDATION, leaving active policy intact.
        """
        self.register_proposal(proposal)

        # 1. Test set quarantine check
        if scenario_id.lower() in {"test", "test_partition", "held_out_test"} or "test" in scenario_id.lower().split("_"):
            self.proposal_states[proposal.proposal_id] = ProposalStatus.FAILED_VALIDATION
            raise GroundTruthQuarantineError(
                f"Quarantine violation: Replay Gate strictly prohibits using test partition '{scenario_id}' for replay or threshold adaptation.",
                violated_fields=[scenario_id],
                context="ReplayGate.validate_and_replay",
            )

        # 2. Check base_cfg_hash match
        active_hash = current_policy.compute_cfg_hash()
        base_hash_matches = proposal.base_cfg_hash == active_hash
        if not base_hash_matches:
            result = ReplayValidationResult(
                proposal_id=proposal.proposal_id,
                scenario_id=scenario_id,
                is_valid=False,
                base_cfg_hash_matches=False,
                allowlist_passed=False,
                bounds_passed=False,
                replay_executed=False,
                validation_samples=0,
                baseline_touches=0,
                proposed_touches=0,
                churn_count=0,
                capacity_exceeded=False,
                rejection_reason=(
                    f"Base configuration hash mismatch: Proposal based on {proposal.base_cfg_hash[:12]}..., "
                    f"but active policy hash is {active_hash[:12]}..."
                ),
            )
            self.replay_results[proposal.proposal_id] = result
            self.proposal_states[proposal.proposal_id] = ProposalStatus.FAILED_VALIDATION
            return result, ProposalStatus.FAILED_VALIDATION

        # 3. Check allowlisted keys and bounds
        allowlist_ok, err_msg = self.sentinel.validate_proposal_changes(
            proposal.changes, current_policy=current_policy
        )
        if not allowlist_ok:
            result = ReplayValidationResult(
                proposal_id=proposal.proposal_id,
                scenario_id=scenario_id,
                is_valid=False,
                base_cfg_hash_matches=True,
                allowlist_passed=False,
                bounds_passed=False,
                replay_executed=False,
                validation_samples=0,
                baseline_touches=0,
                proposed_touches=0,
                churn_count=0,
                capacity_exceeded=False,
                rejection_reason=err_msg or "Allowlist/bounds validation failed",
            )
            self.replay_results[proposal.proposal_id] = result
            self.proposal_states[proposal.proposal_id] = ProposalStatus.FAILED_VALIDATION
            return result, ProposalStatus.FAILED_VALIDATION

        # 4. Construct candidate policy
        try:
            cand_dict = current_policy.model_dump()
            cand_dict.update(proposal.changes)
            candidate_policy = IEEEPolicyConfig(**cand_dict)
        except Exception as exc:
            result = ReplayValidationResult(
                proposal_id=proposal.proposal_id,
                scenario_id=scenario_id,
                is_valid=False,
                base_cfg_hash_matches=True,
                allowlist_passed=True,
                bounds_passed=False,
                replay_executed=False,
                validation_samples=0,
                baseline_touches=0,
                proposed_touches=0,
                churn_count=0,
                capacity_exceeded=False,
                rejection_reason=f"Candidate policy formulation failed: {str(exc)}",
            )
            self.replay_results[proposal.proposal_id] = result
            self.proposal_states[proposal.proposal_id] = ProposalStatus.FAILED_VALIDATION
            return result, ProposalStatus.FAILED_VALIDATION

        # 5. Deterministic replay over validation cases
        baseline_router = RouterPolicyAdapter(config=current_policy)
        candidate_router = RouterPolicyAdapter(config=candidate_policy)

        # Standardize validation cases into records with p, u, n
        cases: List[Dict[str, Any]] = []
        if isinstance(validation_data, pd.DataFrame):
            for _, row in validation_data.iterrows():
                p = float(row.get("p", row.get("posterior_prob", 0.0)))
                u = float(row.get("u", row.get("disagreement_u", 0.0)))
                raw_n = row.get("n") if row.get("n") is not None else row.get("novelty_score")
                n = float(raw_n) if raw_n is not None else None
                cases.append({"p": p, "u": u, "n": n})
        elif isinstance(validation_data, Sequence):
            for item in validation_data:
                p = float(item.get("p", item.get("posterior_prob", 0.0)))
                u = float(item.get("u", item.get("disagreement_u", 0.0)))
                raw_n = item.get("n") if item.get("n") is not None else item.get("novelty_score")
                n = float(raw_n) if raw_n is not None else None
                cases.append({"p": p, "u": u, "n": n})
        else:
            raise TypeError(f"Unsupported validation_data type: {type(validation_data).__name__}")

        n_samples = len(cases)
        if n_samples == 0:
            result = ReplayValidationResult(
                proposal_id=proposal.proposal_id,
                scenario_id=scenario_id,
                is_valid=False,
                base_cfg_hash_matches=True,
                allowlist_passed=True,
                bounds_passed=True,
                replay_executed=False,
                validation_samples=0,
                baseline_touches=0,
                proposed_touches=0,
                churn_count=0,
                capacity_exceeded=False,
                rejection_reason="Validation dataset is empty",
            )
            self.replay_results[proposal.proposal_id] = result
            self.proposal_states[proposal.proposal_id] = ProposalStatus.FAILED_VALIDATION
            return result, ProposalStatus.FAILED_VALIDATION

        base_touches = 0
        cand_touches = 0
        churn_count = 0

        for c in cases:
            base_act, _ = baseline_router.route(p=c["p"], u=c["u"], n=c["n"])
            cand_act, _ = candidate_router.route(p=c["p"], u=c["u"], n=c["n"])

            base_is_touched = base_act in {"FRAUD_ALERT", "MANUAL_REVIEW"}
            cand_is_touched = cand_act in {"FRAUD_ALERT", "MANUAL_REVIEW"}

            if base_is_touched:
                base_touches += 1
            if cand_is_touched:
                cand_touches += 1

            if base_act != cand_act:
                churn_count += 1

        # Check capacity budget limit
        budget_frac = candidate_policy.get_effective_workload_budget()
        allowed_capacity = max(10, int(np.ceil(n_samples * budget_frac * 1.5)))
        capacity_exceeded = cand_touches > allowed_capacity

        details = {
            "validation_sample_count": n_samples,
            "baseline_touches": base_touches,
            "proposed_touches": cand_touches,
            "baseline_touch_rate": round(base_touches / n_samples, 4),
            "proposed_touch_rate": round(cand_touches / n_samples, 4),
            "touch_rate_delta": round((cand_touches - base_touches) / n_samples, 4),
            "churn_count": churn_count,
            "churn_rate": round(churn_count / n_samples, 4),
            "capacity_limit": allowed_capacity,
            "capacity_exceeded": capacity_exceeded,
            "candidate_cfg_hash": candidate_policy.compute_cfg_hash(),
        }

        result = ReplayValidationResult(
            proposal_id=proposal.proposal_id,
            scenario_id=scenario_id,
            is_valid=not capacity_exceeded,
            base_cfg_hash_matches=True,
            allowlist_passed=True,
            bounds_passed=True,
            replay_executed=True,
            validation_samples=n_samples,
            baseline_touches=base_touches,
            proposed_touches=cand_touches,
            churn_count=churn_count,
            capacity_exceeded=capacity_exceeded,
            details=details,
            rejection_reason="Proposed policy exceeded review capacity budget" if capacity_exceeded else None,
        )
        self.replay_results[proposal.proposal_id] = result

        # State transition: Successful replay transitions strictly to AWAITING_HUMAN_APPROVAL
        if result.is_valid:
            status = ProposalStatus.AWAITING_HUMAN_APPROVAL
        else:
            status = ProposalStatus.FAILED_VALIDATION

        self.proposal_states[proposal.proposal_id] = status
        return result, status

    def approve_proposal(
        self,
        proposal_id: str,
        approver: str,
        rationale: str,
        audit_chain: Optional[AuditChain] = None,
    ) -> Dict[str, Any]:
        """Approve a validated policy proposal with explicit human authorization and cryptographic provenance.

        Requirements:
        1. Proposal must exist and be in AWAITING_HUMAN_APPROVAL state.
        2. Approver identity must be non-empty string.
        3. Seals approval event into AuditChain.
        """
        if proposal_id not in self.proposals:
            raise KeyError(f"Proposal '{proposal_id}' not found in ReplayGate.")

        current_state = self.proposal_states.get(proposal_id)
        if current_state != ProposalStatus.AWAITING_HUMAN_APPROVAL:
            raise SignalGateIntegrationError(
                f"Cannot approve proposal '{proposal_id}' in state '{current_state}'. "
                f"Proposal must be in state 'AWAITING_HUMAN_APPROVAL'."
            )

        if not approver or not approver.strip():
            raise ValueError("Human approver identifier cannot be empty.")

        proposal = self.proposals[proposal_id]
        replay_res = self.replay_results.get(proposal_id)
        timestamp = datetime.now(timezone.utc)

        approval_record = {
            "proposal_id": proposal_id,
            "approver": approver.strip(),
            "rationale": rationale.strip(),
            "approved_at": timestamp.isoformat(),
            "base_cfg_hash": proposal.base_cfg_hash,
            "candidate_cfg_hash": replay_res.details.get("candidate_cfg_hash") if replay_res else None,
            "status": ProposalStatus.APPROVED.value,
        }
        self.approval_records[proposal_id] = approval_record
        self.proposal_states[proposal_id] = ProposalStatus.APPROVED

        # Cryptographically seal into AuditChain if provided
        audit_seq: Optional[int] = None
        record_hash: Optional[str] = None
        if audit_chain is not None:
            audit_entry = audit_chain.append_decision(
                record_id=f"gate_approval_{proposal_id}",
                action="MANUAL_REVIEW",
                reason="R2_INTERMEDIATE_RISK",
                cfg_hash=proposal.base_cfg_hash,
            )
            audit_seq = audit_entry.seq
            record_hash = audit_entry.record_hash

        return {
            "proposal_id": proposal_id,
            "status": ProposalStatus.APPROVED.value,
            "approver": approver.strip(),
            "approved_at": timestamp.isoformat(),
            "audit_seq": audit_seq,
            "audit_record_hash": record_hash,
            "message": "Policy proposal successfully approved by human authorization.",
        }

    def reject_proposal(
        self,
        proposal_id: str,
        reviewer: str,
        reason: str,
        audit_chain: Optional[AuditChain] = None,
    ) -> Dict[str, Any]:
        """Reject a policy proposal, keeping active production policy completely intact."""
        if proposal_id not in self.proposals:
            raise KeyError(f"Proposal '{proposal_id}' not found in ReplayGate.")

        if not reviewer or not reviewer.strip():
            raise ValueError("Reviewer identifier cannot be empty.")

        timestamp = datetime.now(timezone.utc)
        proposal = self.proposals[proposal_id]

        rejection_record = {
            "proposal_id": proposal_id,
            "reviewer": reviewer.strip(),
            "reason": reason.strip(),
            "rejected_at": timestamp.isoformat(),
            "status": ProposalStatus.REJECTED.value,
        }
        self.approval_records[proposal_id] = rejection_record
        self.proposal_states[proposal_id] = ProposalStatus.REJECTED

        # Cryptographically log rejection to AuditChain if provided
        audit_seq: Optional[int] = None
        if audit_chain is not None:
            audit_entry = audit_chain.append_decision(
                record_id=f"gate_rejection_{proposal_id}",
                action="ROUTINE",
                reason="R5_LOW_RISK_RELIABLE",
                cfg_hash=proposal.base_cfg_hash,
            )
            audit_seq = audit_entry.seq

        return {
            "proposal_id": proposal_id,
            "status": ProposalStatus.REJECTED.value,
            "reviewer": reviewer.strip(),
            "rejected_at": timestamp.isoformat(),
            "audit_seq": audit_seq,
            "message": "Policy proposal rejected. Active production policy remains untouched.",
        }
