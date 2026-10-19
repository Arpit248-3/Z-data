"""SignalGate Shift Storm Replay & Local Historical Replay Routers"""

from typing import Optional
from fastapi import APIRouter, Depends, Query, HTTPException, status
from backend.app.schemas import (
    ReplayControlRequest,
    ReplayControlResponse,
    ReplayRowsResponse,
    ReplayStatusResponse,
    ReplayStepResponse,
)
from backend.app.services.replay import ReplayService
from backend.app.services.replay_worker import HistoricalReplayWorker
from backend.app.dependencies import get_replay_service, get_replay_worker

router = APIRouter(prefix="/replay", tags=["Shift Storm & Historical Replay"])


@router.get("/rows", response_model=ReplayRowsResponse)
def get_replay_rows(
    scenario: str = Query("S0", description="Scenario identifier (e.g. S0, S1, S3)."),
    offset: int = Query(0, ge=0, description="Offset for chronological row retrieval."),
    limit: int = Query(100, ge=1, le=500, description="Number of rows to stream (max 500)."),
    mode: str = Query(None, description="Operating mode filter."),
    replay_service: ReplayService = Depends(get_replay_service),
) -> ReplayRowsResponse:
    """Retrieve ordered transaction rows from saved replay artifacts for frontend stream visualization."""
    return replay_service.get_replay_rows(
        scenario=scenario,
        offset=offset,
        limit=limit,
        mode=mode,
    )


# ------------------------------------------------------------------------------
# Stage A: Genuine Local Historical Replay Worker Endpoints
# ------------------------------------------------------------------------------
@router.get("/status", response_model=ReplayStatusResponse)
def get_replay_status(
    worker: HistoricalReplayWorker = Depends(get_replay_worker),
) -> ReplayStatusResponse:
    """Report real-time telemetry, counts, recent caserate, and readiness from the local replay worker."""
    st = worker.get_status()
    return ReplayStatusResponse(**st)


@router.post("/start", response_model=ReplayControlResponse)
def start_replay(
    request: Optional[ReplayControlRequest] = None,
    worker: HistoricalReplayWorker = Depends(get_replay_worker),
) -> ReplayControlResponse:
    """Start local historical replay worker in a background thread."""
    limit = request.limit if request and request.limit is not None else 500
    delay_ms = request.delay_ms if request and request.delay_ms is not None else 50
    res = worker.start(limit=limit, delay_ms=delay_ms)
    if res.get("status") == "ERROR":
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "code": "REPLAY_START_FAILED",
                "message": res.get("message", "Failed to start replay."),
                "details": res,
            },
        )
    return ReplayControlResponse(
        status=res.get("status", "STARTED"),
        message=res.get("message", "Replay worker started."),
        replay_state=res.get("replay_state", "RUNNING"),
        data_provenance=res.get("data_provenance", "HISTORICAL_REPLAY"),
        scored_count=worker.scored_count,
    )


@router.post("/stop", response_model=ReplayControlResponse)
def stop_replay(
    worker: HistoricalReplayWorker = Depends(get_replay_worker),
) -> ReplayControlResponse:
    """Safely stop the running local historical replay worker."""
    res = worker.stop()
    return ReplayControlResponse(
        status=res.get("status", "STOPPED"),
        message=res.get("message", "Replay worker stopped."),
        replay_state=res.get("replay_state", "STOPPED"),
        data_provenance="HISTORICAL_REPLAY",
        scored_count=worker.scored_count,
    )


@router.post("/step", response_model=ReplayStepResponse)
def step_replay(
    worker: HistoricalReplayWorker = Depends(get_replay_worker),
) -> ReplayStepResponse:
    """Synchronously stream and score exactly one genuine historical record."""
    try:
        res = worker.step()
        return ReplayStepResponse(
            status=res.get("status", "SUCCESS"),
            scored=res.get("scored", False),
            event=res.get("event"),
            message=res.get("message"),
            cursor_row=res.get("cursor_row"),
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "code": "REPLAY_STEP_ERROR",
                "message": str(exc),
                "details": {},
            },
        )


@router.post("/reset", response_model=ReplayControlResponse)
def reset_replay(
    worker: HistoricalReplayWorker = Depends(get_replay_worker),
) -> ReplayControlResponse:
    """Reset replay cursor, counters, and idempotency state to initial zero."""
    res = worker.reset()
    return ReplayControlResponse(
        status=res.get("status", "RESET"),
        message=res.get("message", "Replay worker reset."),
        replay_state=res.get("replay_state", "STOPPED"),
        data_provenance="HISTORICAL_REPLAY",
        scored_count=0,
    )
