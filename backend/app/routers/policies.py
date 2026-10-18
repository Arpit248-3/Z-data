"""SignalGate Policy Comparison Routers"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from backend.app.schemas import ErrorResponse, PolicyCompareResponse
from backend.app.services.policies import PolicyService
from backend.app.dependencies import get_policy_service

router = APIRouter(prefix="/policies", tags=["Policy Comparison"])


@router.get(
    "/compare",
    response_model=PolicyCompareResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid budget multiple filter."},
        503: {"model": ErrorResponse, "description": "Policy comparison artifact unavailable."},
    },
)
def compare_policies(
    budget_multiple: Optional[str] = Query(
        None,
        description="Optional budget sweep multiple: '1.0x', '1.5x', '2.0x', or '3.0x'.",
    ),
    policy_service: PolicyService = Depends(get_policy_service),
) -> PolicyCompareResponse:
    """Return offline matched-budget policy comparison data (B1, B2, B3a, B4, SignalGate)."""
    valid_multiples = {"1.0x", "1.5x", "2.0x", "3.0x"}
    if budget_multiple is not None and budget_multiple not in valid_multiples:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "INVALID_BUDGET_MULTIPLE",
                "message": f"Budget multiple '{budget_multiple}' is not in pre-registered sweep.",
                "details": {"valid_multiples": sorted(list(valid_multiples))},
            },
        )

    res = policy_service.compare_policies(budget_multiple=budget_multiple)
    if res is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "code": "ARTIFACT_UNAVAILABLE",
                "message": "Policy comparison data could not be extracted from results.json.",
                "details": {},
            },
        )
    return res
