"""SignalGate Case Explorer Routers"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from backend.app.schemas import (
    CaseDetailResponse,
    CasesResponse,
    ErrorResponse,
)
from backend.app.services.cases import CaseService
from backend.app.dependencies import get_case_service

router = APIRouter(prefix="/cases", tags=["Case Explorer"])


@router.get("", response_model=CasesResponse)
def list_cases(
    limit: int = Query(50, ge=1, le=200, description="Page size limit (maximum 200)."),
    offset: int = Query(0, ge=0, description="Row offset for pagination."),
    action: Optional[str] = Query(None, description="Filter by triage action (e.g. FRAUD_ALERT)."),
    reason_code: Optional[str] = Query(None, description="Filter by reason code (e.g. R1_HIGH_RISK)."),
    scenario: Optional[str] = Query("S0", description="Filter by scenario ID (default 'S0')."),
    risk_min: Optional[float] = Query(None, ge=0.0, le=1.0, description="Minimum risk probability p."),
    risk_max: Optional[float] = Query(None, ge=0.0, le=1.0, description="Maximum risk probability p."),
    search: Optional[str] = Query(None, description="Substring search on case identifier."),
    case_service: CaseService = Depends(get_case_service),
) -> CasesResponse:
    """Return paginated cases from actual saved prediction records."""
    return case_service.list_cases(
        limit=limit,
        offset=offset,
        action=action,
        reason_code=reason_code,
        scenario=scenario,
        risk_min=risk_min,
        risk_max=risk_max,
        search=search,
    )


@router.get(
    "/{case_id}",
    response_model=CaseDetailResponse,
    responses={
        404: {"model": ErrorResponse, "description": "Case identifier was not found."},
    },
)
def get_case(
    case_id: str,
    case_service: CaseService = Depends(get_case_service),
) -> CaseDetailResponse:
    """Retrieve full signals, decision rationale, and feature metadata for a specific case."""
    case = case_service.get_case_detail(case_id=case_id)
    if case is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "CASE_NOT_FOUND",
                "message": f"Case with identifier '{case_id}' was not found in saved records.",
                "details": {"case_id": case_id},
            },
        )
    return case
