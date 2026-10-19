"""SignalGate Integration Routers

Exposes IEEE-CIS model card, multi-metric drift reports, and Replay Gate governance endpoints:
- GET /api/model/card
- GET /api/drift/report
- GET /api/governance/proposals
- GET /api/governance/proposals/{proposal_id}
- POST /api/governance/proposals/{proposal_id}/replay
- POST /api/governance/proposals/{proposal_id}/approve
- POST /api/governance/proposals/{proposal_id}/reject

Governing Specification: docs/ibm_architecture_integration_master_spec.md § C, § L
Requirements: APII-01, APII-03
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status

from backend.app.dependencies import get_integration_service
from backend.app.schemas import (
    DriftReportAPIResponse,
    ErrorResponse,
    GovernanceDecisionResponse,
    GovernanceProposalResponse,
    ModelCardResponse,
    ProposalApprovalRequest,
    ProposalRejectionRequest,
)
from backend.app.services.integration import IntegrationService
from integrations.ibm_architecture.exceptions import (
    ArtifactNotFoundError,
    GroundTruthQuarantineError,
    IncompatibleArtifactError,
    SignalGateIntegrationError,
)

router = APIRouter(tags=["Model Card & Governance"])


# ------------------------------------------------------------------------------
# Model Card & Metadata
# ------------------------------------------------------------------------------
@router.get(
    "/model/card",
    response_model=ModelCardResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid mode requested."},
        503: {"model": ErrorResponse, "description": "Model bundle artifacts missing or corrupted."},
    },
)
def get_model_card(
    mode: str = Query("IEEE_CIS_OFFLINE_BENCHMARK", description="Operating mode ('IEEE_CIS_OFFLINE_BENCHMARK' or 'SYNTHETIC_SMOKE_ONLY')."),
    integration_service: IntegrationService = Depends(get_integration_service),
) -> ModelCardResponse:
    """Return model architecture metadata, 391 feature manifest, calibrator type, and artifact hashes."""
    try:
        return integration_service.get_model_card(mode=mode)
    except (ArtifactNotFoundError, IncompatibleArtifactError) as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "code": "ARTIFACT_UNAVAILABLE",
                "message": str(e),
                "details": {},
            },
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "INVALID_MODE",
                "message": str(e),
                "details": {"mode": mode},
            },
        )


# ------------------------------------------------------------------------------
# Drift Monitoring Report
# ------------------------------------------------------------------------------
@router.get(
    "/drift/report",
    response_model=DriftReportAPIResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid mode requested for drift monitoring."},
    },
)
def get_drift_report(
    mode: str = Query("IEEE_CIS_OFFLINE_BENCHMARK", description="Operating mode filter."),
    integration_service: IntegrationService = Depends(get_integration_service),
) -> DriftReportAPIResponse:
    """Return deterministic multi-metric drift analysis report with PSI, KS, and Wasserstein metrics."""
    try:
        return integration_service.get_drift_report(mode=mode)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "INVALID_DRIFT_MODE",
                "message": str(e),
                "details": {"mode": mode},
            },
        )


# ------------------------------------------------------------------------------
# Governance & Replay Gate Lifecycle
# ------------------------------------------------------------------------------
@router.get(
    "/governance/proposals",
    response_model=List[GovernanceProposalResponse],
)
def list_proposals(
    integration_service: IntegrationService = Depends(get_integration_service),
) -> List[GovernanceProposalResponse]:
    """List all registered advisory policy proposals in the Replay Gate."""
    return integration_service.list_proposals()


@router.get(
    "/governance/proposals/{proposal_id}",
    response_model=GovernanceProposalResponse,
    responses={
        404: {"model": ErrorResponse, "description": "Proposal not found."},
    },
)
def get_proposal(
    proposal_id: str,
    integration_service: IntegrationService = Depends(get_integration_service),
) -> GovernanceProposalResponse:
    """Retrieve details, parameters, and status for a specific advisory proposal."""
    try:
        return integration_service.get_proposal(proposal_id=proposal_id)
    except KeyError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "PROPOSAL_NOT_FOUND",
                "message": f"Proposal '{proposal_id}' was not found in Replay Gate.",
                "details": {"proposal_id": proposal_id},
            },
        )


@router.post(
    "/governance/proposals/{proposal_id}/replay",
    response_model=GovernanceProposalResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Replay validation failed or quarantine violated."},
        404: {"model": ErrorResponse, "description": "Proposal not found."},
    },
)
def replay_proposal(
    proposal_id: str,
    scenario: str = Query("validation", description="Partition or scenario for replay evaluation."),
    integration_service: IntegrationService = Depends(get_integration_service),
) -> GovernanceProposalResponse:
    """Deterministically replay a proposed policy against the validation partition.

    Upon successful evaluation, transitions status to AWAITING_HUMAN_APPROVAL.
    Never automatically activates the proposal.
    """
    try:
        return integration_service.replay_proposal(proposal_id=proposal_id, scenario_id=scenario)
    except KeyError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "PROPOSAL_NOT_FOUND",
                "message": f"Proposal '{proposal_id}' was not found in Replay Gate.",
                "details": {"proposal_id": proposal_id},
            },
        )
    except GroundTruthQuarantineError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "QUARANTINE_VIOLATION",
                "message": str(e),
                "details": {"scenario": scenario},
            },
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "REPLAY_ERROR",
                "message": str(e),
                "details": {},
            },
        )


@router.post(
    "/governance/proposals/{proposal_id}/approve",
    response_model=GovernanceDecisionResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Missing approver credentials or invalid state."},
        404: {"model": ErrorResponse, "description": "Proposal not found."},
        409: {"model": ErrorResponse, "description": "Proposal cannot be approved in current state."},
    },
)
def approve_proposal(
    proposal_id: str,
    request: ProposalApprovalRequest,
    integration_service: IntegrationService = Depends(get_integration_service),
) -> GovernanceDecisionResponse:
    """Approve a validated policy proposal with explicit human authorization and cryptographic audit sealing."""
    if not request.approver or not request.approver.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "INVALID_APPROVER",
                "message": "Human approver identifier cannot be empty.",
                "details": {},
            },
        )

    try:
        return integration_service.approve_proposal(
            proposal_id=proposal_id,
            approver=request.approver,
            rationale=request.rationale,
        )
    except KeyError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "PROPOSAL_NOT_FOUND",
                "message": f"Proposal '{proposal_id}' was not found in Replay Gate.",
                "details": {"proposal_id": proposal_id},
            },
        )
    except SignalGateIntegrationError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "code": "INVALID_STATE_TRANSITION",
                "message": str(e),
                "details": {"proposal_id": proposal_id},
            },
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "VALIDATION_ERROR",
                "message": str(e),
                "details": {},
            },
        )


@router.post(
    "/governance/proposals/{proposal_id}/reject",
    response_model=GovernanceDecisionResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Missing reviewer credentials or invalid request."},
        404: {"model": ErrorResponse, "description": "Proposal not found."},
    },
)
def reject_proposal(
    proposal_id: str,
    request: ProposalRejectionRequest,
    integration_service: IntegrationService = Depends(get_integration_service),
) -> GovernanceDecisionResponse:
    """Reject an advisory proposal, preserving existing policy completely and sealing rejection event to AuditChain."""
    if not request.reviewer or not request.reviewer.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "INVALID_REVIEWER",
                "message": "Human reviewer identifier cannot be empty.",
                "details": {},
            },
        )

    try:
        return integration_service.reject_proposal(
            proposal_id=proposal_id,
            reviewer=request.reviewer,
            reason=request.reason,
        )
    except KeyError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "PROPOSAL_NOT_FOUND",
                "message": f"Proposal '{proposal_id}' was not found in Replay Gate.",
                "details": {"proposal_id": proposal_id},
            },
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "VALIDATION_ERROR",
                "message": str(e),
                "details": {},
            },
        )
