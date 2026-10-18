"""SignalGate Governance, Replay Gate, and Drift Monitoring Routers.

Governing Specification: docs/ibm_architecture_integration_master_spec.md § C3, § J, § K, § L
"""

from datetime import datetime, timezone
import hashlib
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Query, Request, status
import numpy as np
import pandas as pd
from pydantic import BaseModel, Field

from integrations.ibm_architecture.agent_view import AgentCaseView, check_for_quarantine_violations
from integrations.ibm_architecture.contracts import (
    Action,
    AuditRecord,
    Claim,
    Proposal,
    ReasonCode,
    SHA256_PATTERN,
)
from integrations.ibm_architecture.exceptions import GroundTruthQuarantineError
from integrations.ibm_architecture.governance import (
    AuditChain,
    CaseCopilot,
    ClaimLedger,
    ClaimVerifier,
    verify_chain,
)
from integrations.ibm_architecture.monitoring import (
    ALLOWLISTED_CONFIG_KEYS,
    DistributionDriftCalculator,
    DriftSentinel,
    ProposalReplayStatus,
    ReplayEvaluationRecord,
    ReplayGate,
)

router = APIRouter(prefix="/governance", tags=["Governance, Replay Gate & Drift"])

from pathlib import Path

# Singleton services for runtime API state
DEFAULT_FROZEN_CFG_HASH = "8d3f02ca492ca94bab45f3ceac8d39432c2f29f40d54e7990b4aa78cbbff6240"
_drift_calculator = DistributionDriftCalculator(bins=10)
_sentinel = DriftSentinel()
_replay_gate = ReplayGate(frozen_cfg_hash=DEFAULT_FROZEN_CFG_HASH)
_copilot = CaseCopilot()
_claim_verifier = ClaimVerifier()
_claim_ledger = ClaimLedger()
_audit_log_path = Path("logs/governance_audit_chain.jsonl")
_audit_chain = AuditChain(
    log_path=_audit_log_path,
    signing_key=b"signalgate_synthetic_audit_key_32bytes_min_secret!!",
)


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------
class DriftReportResponse(BaseModel):
    status: str
    scenario_id: str
    features_monitored: int
    overall_drift_detected: bool
    significant_shift_features: List[str]
    moderate_shift_features: List[str]
    mean_psi: float
    max_psi: float
    feature_drift_reports: List[Dict[str, Any]]
    real_data_benchmark_status: str
    notice: str


class ProposalValidateRequest(BaseModel):
    proposal_id: str
    base_cfg_hash: str
    changes: Dict[str, Any]
    rationale: str


class ProposalApproveRequest(BaseModel):
    proposal_id: str
    approver: str


class ProposalRejectRequest(BaseModel):
    proposal_id: str
    reviewer: str
    reason: str


class CopilotBriefRequest(BaseModel):
    record_id: str
    p: float
    u: Optional[float] = None
    u2: Optional[float] = None
    n: Optional[float] = None
    action: str
    reason: str
    cfg_hash: Optional[str] = None
    split_hash: Optional[str] = None


class CopilotBriefResponse(BaseModel):
    record_id: str
    action: str
    reason: str
    status: str
    verified_statements: List[str]
    total_claims: int
    verified_claims: int
    rejected_claims: int


class AuditChainVerifyResponse(BaseModel):
    verified: bool
    chain_length: int
    genesis_hash: str
    head_hash: str
    tamper_detected: bool
    details: str


# ---------------------------------------------------------------------------
# Drift & Sentinel Endpoints
# ---------------------------------------------------------------------------
@router.get("/drift", response_model=DriftReportResponse)
def get_drift_report(
    scenario: str = Query("S1", description="Shift scenario identifier (e.g. S0, S1, S2, S3, S4)"),
) -> DriftReportResponse:
    """Compute and return distribution drift diagnostics for synthetic scenarios without evaluation labels."""
    np.random.seed(42)
    # Generate reference baseline
    ref_df = pd.DataFrame({
        "TransactionAmt": np.random.exponential(scale=100.0, size=500),
        "card1": np.random.uniform(1000, 20000, size=500),
        "dist1": np.random.gamma(shape=2.0, scale=10.0, size=500),
        "C1": np.random.poisson(lam=2.0, size=500),
    })

    # Shift comparison based on requested scenario
    np.random.seed(99)
    if scenario == "S0":
        comp_df = pd.DataFrame({
            "TransactionAmt": np.random.exponential(scale=100.0, size=500),
            "card1": np.random.uniform(1000, 20000, size=500),
            "dist1": np.random.gamma(shape=2.0, scale=10.0, size=500),
            "C1": np.random.poisson(lam=2.0, size=500),
        })
    elif scenario == "S1":
        comp_df = pd.DataFrame({
            "TransactionAmt": np.random.exponential(scale=350.0, size=500),
            "card1": np.random.uniform(1000, 20000, size=500),
            "dist1": np.random.gamma(shape=2.0, scale=10.0, size=500),
            "C1": np.random.poisson(lam=8.0, size=500),
        })
    else:
        comp_df = pd.DataFrame({
            "TransactionAmt": np.random.exponential(scale=200.0, size=500),
            "card1": np.random.uniform(1000, 20000, size=500),
            "dist1": np.random.gamma(shape=2.0, scale=10.0, size=500),
            "C1": np.random.poisson(lam=4.0, size=500),
        })

    report = _drift_calculator.compute_drift(
        reference_df=ref_df,
        comparison_df=comp_df,
        features=["TransactionAmt", "card1", "dist1", "C1"],
        scenario_id=scenario,
        mode="SYNTHETIC_SMOKE_ONLY",
    )
    return DriftReportResponse(**report)


@router.post("/drift/propose", response_model=Optional[Dict[str, Any]])
def generate_drift_proposal(
    summary: Dict[str, Any],
) -> Optional[Dict[str, Any]]:
    """Advisory Drift Sentinel endpoint: inspects drift summary and generates a typed Proposal if warranted."""
    proposal = _sentinel.evaluate_and_propose(
        monitoring_summary=summary,
        base_cfg_hash=DEFAULT_FROZEN_CFG_HASH,
    )
    if proposal is None:
        return None
    return proposal.model_dump()


# ---------------------------------------------------------------------------
# Replay Gate Endpoints
# ---------------------------------------------------------------------------
@router.get("/proposals", response_model=List[Dict[str, Any]])
def list_replay_proposals() -> List[Dict[str, Any]]:
    """Return history of proposals evaluated by the Replay Gate."""
    return [r.model_dump() for r in _replay_gate.evaluation_history]


@router.post("/proposals/validate", response_model=Dict[str, Any])
def validate_proposal(request: ProposalValidateRequest) -> Dict[str, Any]:
    """Validate and replay an advisory proposal in the Replay Gate.

    Enforces AWAITING_HUMAN_APPROVAL status upon validation pass; never activates automatically.
    """
    proposal = Proposal(
        proposal_id=request.proposal_id,
        base_cfg_hash=request.base_cfg_hash,
        changes=request.changes,
        rationale=request.rationale,
        created_at=datetime.now(timezone.utc),
    )

    record = _replay_gate.validate_and_replay(proposal)
    return record.model_dump()


@router.post("/proposals/approve", response_model=Dict[str, Any])
def approve_proposal(request: ProposalApproveRequest) -> Dict[str, Any]:
    """Provide explicit human sign-off to activate an approved proposal."""
    matching = [r for r in _replay_gate.evaluation_history if r.proposal_id == request.proposal_id]
    if not matching:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "PROPOSAL_NOT_FOUND",
                "message": f"Proposal '{request.proposal_id}' not found in Replay Gate history.",
                "details": {},
            },
        )

    record = matching[-1]
    if record.status != "AWAITING_HUMAN_APPROVAL":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "INVALID_PROPOSAL_STATUS",
                "message": f"Cannot approve proposal in status '{record.status}'; must be 'AWAITING_HUMAN_APPROVAL'.",
                "details": {"current_status": record.status},
            },
        )

    approved = _replay_gate.approve(record, approver=request.approver)
    return approved.model_dump()


@router.post("/proposals/reject", response_model=Dict[str, Any])
def reject_proposal(request: ProposalRejectRequest) -> Dict[str, Any]:
    """Reject a proposal during human governance review."""
    matching = [r for r in _replay_gate.evaluation_history if r.proposal_id == request.proposal_id]
    if not matching:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "PROPOSAL_NOT_FOUND",
                "message": f"Proposal '{request.proposal_id}' not found in Replay Gate history.",
                "details": {},
            },
        )

    record = matching[-1]
    rejected = _replay_gate.reject(record, reviewer=request.reviewer, reason=request.reason)
    return rejected.model_dump()


# ---------------------------------------------------------------------------
# Governed Copilot Endpoints
# ---------------------------------------------------------------------------
@router.post("/copilot/brief", response_model=CopilotBriefResponse)
async def generate_copilot_brief(request: Request) -> CopilotBriefResponse:
    """Generate deterministic case brief containing exclusively verified statements."""
    try:
        raw_json = await request.json()
        check_for_quarantine_violations(raw_json)
        req = CopilotBriefRequest.model_validate(raw_json)
    except (ValueError, KeyError) as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "QUARANTINE_VIOLATION", "message": str(e), "details": {}},
        )

    case_view = AgentCaseView(
        record_id=req.record_id,
        p=req.p,
        u=req.u,
        u2=req.u2,
        n=req.n,
        action=req.action,
        reason=req.reason,
        record_hash="0" * 64,
        cfg_hash=req.cfg_hash or DEFAULT_FROZEN_CFG_HASH,
        split_hash=req.split_hash or ("0" * 64),
    )

    agent_record = _copilot.generate_brief(case_view)
    verified_statements = []
    total_claims = len(agent_record.claims)
    verified_count = 0
    rejected_count = 0

    for c in agent_record.claims:
        res = _claim_verifier.verify(c, case_view)
        if res.is_verified and res.statement:
            verified_statements.append(res.statement)
            verified_count += 1
        else:
            _claim_ledger.record_rejected_claim(
                record_id=req.record_id,
                claim=c,
                rejection_reason=res.rejection_reason or "Unverified",
            )
            rejected_count += 1

    _claim_ledger.record_agent_execution(agent_record)

    return CopilotBriefResponse(
        record_id=req.record_id,
        action=req.action,
        reason=req.reason,
        status=agent_record.status,
        verified_statements=verified_statements,
        total_claims=total_claims,
        verified_claims=verified_count,
        rejected_claims=rejected_count,
    )


# ---------------------------------------------------------------------------
# Cryptographic Audit Chain Endpoints
# ---------------------------------------------------------------------------
@router.get("/audit-chain/verify", response_model=AuditChainVerifyResponse)
def verify_audit_chain_integrity() -> AuditChainVerifyResponse:
    """Verify cryptographic HMAC-SHA256 hash-chain integrity of the active audit chain."""
    if not _audit_log_path.exists() or _audit_log_path.stat().st_size == 0:
        _audit_chain.append(
            decision_id="genesis_init_record",
            p=0.01,
            u=0.01,
            action="ROUTINE",
            reason="R5_LOW_RISK_RELIABLE",
            cfg_hash=DEFAULT_FROZEN_CFG_HASH,
            split_hash="0" * 64,
            u2=0.01,
            n=5.0,
        )

    result = verify_chain(_audit_log_path, key=_audit_chain.signing_key)
    return AuditChainVerifyResponse(
        verified=result.ok,
        chain_length=result.record_count,
        genesis_hash="0" * 64,
        head_hash=result.final_hash,
        tamper_detected=not result.ok,
        details=(
            "HMAC-SHA256 authenticated hash-chain verified successfully."
            if result.ok
            else f"Chain integrity check failed: {result.errors}"
        ),
    )
