"""SignalGate Health & Readiness Routers"""

import datetime
from typing import Optional
from fastapi import APIRouter, Depends, Query
from backend.app.config import settings
from backend.app.schemas import HealthResponse, ModeReadinessResponse, ReadinessStatusResponse
from backend.app.services.artifacts import ArtifactService
from backend.app.services.integration import IntegrationService
from backend.app.dependencies import get_artifact_service, get_integration_service

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


@router.get("/mode", response_model=ModeReadinessResponse)
def get_mode(
    integration_service: IntegrationService = Depends(get_integration_service),
) -> ModeReadinessResponse:
    """Report genuine readiness and status for all three operating modes."""
    return integration_service.get_mode_readiness()


@router.get("/status", response_model=ReadinessStatusResponse)
def get_status(
    mode: Optional[str] = Query(None, description="Operating mode filter (e.g. IEEE_CIS_OFFLINE_BENCHMARK)"),
    artifacts: ArtifactService = Depends(get_artifact_service),
    integration_service: IntegrationService = Depends(get_integration_service),
) -> ReadinessStatusResponse:
    """Provide an exhaustive, honest dependency readiness report across all subsystems."""
    readiness = artifacts.get_readiness_status()
    if mode and mode.upper() in ("IEEE_CIS_OFFLINE_BENCHMARK", "REAL"):
        is_ready, err = integration_service.check_bundle_health()
        readiness["evidence_status"] = "IEEE_CIS_OFFLINE_BENCHMARK"
        readiness["overall_status"] = "OPERATIONAL_OFFLINE_BENCHMARK" if is_ready else "DEGRADED"
        readiness["dependencies"]["ieee_cis_bundle"] = {
            "ready": is_ready,
            "status": "READY" if is_ready else "NOT_AVAILABLE",
            "error": err,
        }
    return ReadinessStatusResponse(**readiness)
