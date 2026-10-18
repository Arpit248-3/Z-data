"""SignalGate Health & Readiness Routers"""

import datetime
from fastapi import APIRouter, Depends
from backend.app.config import settings
from backend.app.schemas import HealthResponse, ReadinessStatusResponse
from backend.app.services.artifacts import ArtifactService
from backend.app.dependencies import get_artifact_service

router = APIRouter(tags=["Health & Status"])


@router.get("/health", response_model=HealthResponse)
def get_health() -> HealthResponse:
    """Report whether the FastAPI application process is alive and operational.

    Note: A healthy process does not imply ML models or evaluation artifacts are ready.
    """
    iso_ts = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    return HealthResponse(
        service_name=settings.project_name,
        version=settings.version,
        status="HEALTHY",
        timestamp=iso_ts,
    )


@router.get("/status", response_model=ReadinessStatusResponse)
def get_status(
    artifacts: ArtifactService = Depends(get_artifact_service),
) -> ReadinessStatusResponse:
    """Provide an exhaustive, honest dependency readiness report across all subsystems."""
    readiness = artifacts.get_readiness_status()
    return ReadinessStatusResponse(**readiness)
