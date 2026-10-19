"""SignalGate Scoring Sandbox Routers"""

from fastapi import APIRouter, Depends, HTTPException, status
from backend.app.schemas import ErrorResponse, SandboxScoreRequest, SandboxScoreResponse
from backend.app.services.scoring import ScoringService
from backend.app.dependencies import get_scoring_service

from integrations.ibm_architecture.exceptions import (
    ArtifactNotFoundError,
    IncompatibleArtifactError,
    LeakageViolationError,
)

router = APIRouter(tags=["Scoring Sandbox"])


@router.post(
    "/score-sandbox",
    response_model=SandboxScoreResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid feature payload or parameter."},
        422: {"model": ErrorResponse, "description": "Leakage violation or validation error."},
        503: {"model": ErrorResponse, "description": "Model or policy artifacts are unavailable."},
    },
)
def score_sandbox(
    request: SandboxScoreRequest,
    scoring_service: ScoringService = Depends(get_scoring_service),
) -> SandboxScoreResponse:
    """Evaluate an arbitrary transaction feature vector through the live fitted ML pipeline and frozen policy router.

    Integrity Guard:
    Strictly rejects all target labels (isFraud, true_label) and raw identifiers.
    """
    try:
        return scoring_service.score_sandbox_transaction(request)
    except LeakageViolationError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "code": "LEAKAGE_VIOLATION",
                "message": str(e),
                "details": {"violated_fields": list(e.violated_fields)},
            },
        )
    except (FileNotFoundError, ArtifactNotFoundError, IncompatibleArtifactError) as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "code": "MODEL_ARTIFACTS_UNAVAILABLE",
                "message": str(e),
                "details": {},
            },
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "INVALID_FEATURE_PAYLOAD",
                "message": str(e),
                "details": {},
            },
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "code": "SCORING_ERROR",
                "message": "An unexpected error occurred during model scoring.",
                "details": {},
            },
        )
