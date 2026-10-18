"""SignalGate Shift Storm Replay Routers"""

from fastapi import APIRouter, Depends, Query
from backend.app.schemas import ReplayRowsResponse
from backend.app.services.replay import ReplayService
from backend.app.dependencies import get_replay_service

router = APIRouter(prefix="/replay", tags=["Shift Storm Replay"])


@router.get("/rows", response_model=ReplayRowsResponse)
def get_replay_rows(
    scenario: str = Query("S0", description="Scenario identifier (e.g. S0, S1, S3)."),
    offset: int = Query(0, ge=0, description="Offset for chronological row retrieval."),
    limit: int = Query(100, ge=1, le=500, description="Number of rows to stream (max 500)."),
    replay_service: ReplayService = Depends(get_replay_service),
) -> ReplayRowsResponse:
    """Retrieve ordered transaction rows from saved replay artifacts for frontend stream visualization."""
    return replay_service.get_replay_rows(
        scenario=scenario,
        offset=offset,
        limit=limit,
    )
