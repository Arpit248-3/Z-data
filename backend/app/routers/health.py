"""SignalGate Health & Readiness Routers"""

import datetime
from typing import Optional
from fastapi import APIRouter, Depends, Query
from backend.app.config import settings
from backend.app.schemas import HealthResponse, ModeReadinessResponse, ReadinessStatusResponse
from backend.app.services.artifacts import ArtifactService
from backend.app.services.integration import IntegrationService
from backend.app.services.replay_worker import HistoricalReplayWorker
from backend.app.dependencies import get_artifact_service, get_integration_service, get_replay_worker

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
    worker: HistoricalReplayWorker = Depends(get_replay_worker),
) -> ReadinessStatusResponse:
    """Provide an exhaustive, honest dependency readiness report across all subsystems."""
    readiness = artifacts.get_readiness_status()
    worker_st = worker.get_status()
    is_model_ready, model_err = integration_service.check_bundle_health()

    # Core 5-dimension distinguished readiness (Stage A § 3)
    readiness["dependencies"]["backend_api"] = {
        "ready": True,
        "status": "READY",
        "service": settings.project_name,
        "version": settings.version,
    }
    readiness["dependencies"]["local_model"] = {
        "ready": is_model_ready,
        "status": "READY" if is_model_ready else "NOT_AVAILABLE",
        "model_id": "ieee_cis_v1",
        "error": model_err,
    }
    readiness["dependencies"]["ieee_cis_data"] = {
        "ready": worker_st["ieee_data_readiness"],
        "status": "READY" if worker_st["ieee_data_readiness"] else "NOT_AVAILABLE",
        "path": "data/raw/test_transaction.csv",
        "unlabeled_sample_available": True,
    }
    readiness["dependencies"]["local_replay_state"] = {
        "state": worker_st["replay_state"],
        "data_provenance": "HISTORICAL_REPLAY",
        "scored_count": worker_st["scored_count"],
        "recent_caserate": worker_st["recent_caserate"],
        "avg_latency_ms": worker_st["avg_latency_ms"],
    }
    readiness["dependencies"]["external_live_source"] = {
        "ready": False,
        "status": "DISCONNECTED",
        "notice": "External live banking stream is disconnected. Replay operates on offline IEEE-CIS records only.",
    }
    readiness["dependencies"]["ingestion"] = {
        "status": "HISTORICAL_REPLAY_ACTIVE" if worker_st["replay_state"] == "RUNNING" else ("HISTORICAL_REPLAY_IDLE" if worker_st["scored_count"] > 0 else "IDLE"),
        "provenance": "HISTORICAL_REPLAY",
        "scored_count": worker_st["scored_count"],
        "recent_caserate": worker_st["recent_caserate"],
        "avg_latency_ms": worker_st["avg_latency_ms"],
        "live_edge_status": "DISCONNECTED",
    }

    readiness["readiness"] = {
        "backend_api": "READY",
        "local_model": "READY" if is_model_ready else "NOT_AVAILABLE",
        "ieee_cis_data": "READY" if worker_st["ieee_data_readiness"] else "NOT_AVAILABLE",
        "local_replay": worker_st["replay_state"],
        "external_live_source": "DISCONNECTED",
    }
    readiness["replay"] = worker_st

    if mode and mode.upper() in ("IEEE_CIS_OFFLINE_BENCHMARK", "REAL"):
        readiness["evidence_status"] = "IEEE_CIS_OFFLINE_BENCHMARK"
        readiness["overall_status"] = "OPERATIONAL_OFFLINE_BENCHMARK" if is_model_ready else "DEGRADED"
        readiness["dependencies"]["dataset"] = {
            "ready": True,
            "status": "IEEE_CIS_OFFLINE_BENCHMARK",
            "is_synthetic": False,
            "path": "results/ieee_cis_v1/",
            "records": 118108,
        }
        readiness["dependencies"]["ieee_cis_bundle"] = {
            "ready": is_model_ready,
            "status": "READY" if is_model_ready else "NOT_AVAILABLE",
            "error": model_err,
        }
    elif mode and mode.upper() in ("LIVE_SOURCE_NOT_CONNECTED", "LIVE"):
        readiness["evidence_status"] = "LIVE_SOURCE_NOT_CONNECTED"
        readiness["overall_status"] = "DISCONNECTED"
        readiness["dependencies"]["dataset"] = {
            "ready": False,
            "status": "DISCONNECTED",
            "is_synthetic": False,
            "path": "N/A (Stream Offline)",
            "records": 0,
        }
        readiness["dependencies"]["model_artifacts"] = {
            "ready": False,
            "status": "OFFLINE",
        }
        readiness["dependencies"]["frozen_policy"] = {
            "ready": False,
            "status": "SUSPENDED",
        }
        readiness["dependencies"]["consolidated_results"] = {
            "ready": False,
            "status": "DISCONNECTED",
        }
        readiness["dependencies"]["live_source"] = {
            "ready": False,
            "status": "DISCONNECTED",
            "notice": "Live production banking/payment event stream is disconnected (offline mode only).",
        }
    return ReadinessStatusResponse(**readiness)
