"""SignalGate Overview, Consolidated Results, and Scenarios Routers"""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from backend.app.schemas import (
    ErrorResponse,
    OverviewResponse,
    ScenarioItem,
    ScenariosResponse,
)
from backend.app.services.artifacts import ArtifactService
from backend.app.services.overview import OverviewService
from backend.app.dependencies import get_artifact_service, get_overview_service

router = APIRouter(tags=["Overview & Evaluation"])


@router.get("/overview", response_model=OverviewResponse)
def get_overview(
    mode: Optional[str] = None,
    overview_service: OverviewService = Depends(get_overview_service),
) -> OverviewResponse:
    """Retrieve executive evaluation summary strictly from validated project artifacts."""
    return overview_service.get_overview(mode=mode)


@router.get(
    "/results",
    responses={
        200: {"description": "Full canonical evaluation results artifact."},
        503: {"model": ErrorResponse, "description": "Evaluation artifact is unavailable."},
    },
)
def get_results(
    artifacts: ArtifactService = Depends(get_artifact_service),
) -> Dict[str, Any]:
    """Return the complete canonical results/results.json evaluation document."""
    results = artifacts.get_results_json()
    if results is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "code": "ARTIFACT_UNAVAILABLE",
                "message": "Consolidated evaluation artifact (results/results.json) is missing or unreadable.",
                "details": {"path": "results/results.json"},
            },
        )
    return results


@router.get(
    "/scenarios",
    response_model=ScenariosResponse,
    responses={
        503: {"model": ErrorResponse, "description": "Scenario metadata is unavailable."},
    },
)
def get_scenarios(
    artifacts: ArtifactService = Depends(get_artifact_service),
) -> ScenariosResponse:
    """Return only shift scenarios actually evaluated and stored in results/results.json."""
    results = artifacts.get_results_json()
    if results is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "code": "ARTIFACT_UNAVAILABLE",
                "message": "Scenario data is unavailable because results/results.json is missing.",
                "details": {},
            },
        )

    shift_scenarios = results.get("shift_scenarios", {})
    scenario_items: List[ScenarioItem] = []

    for s_id, s_data in shift_scenarios.items():
        scenario_items.append(
            ScenarioItem(
                scenario_id=s_id,
                name=s_data.get("name", s_id),
                description=s_data.get("metadata", {}).get("notice", f"Scenario {s_id}"),
                status=s_data.get("status", "SYNTHETIC_SMOKE_ONLY"),
                is_synthetic=True,
                sample_count=s_data.get("sample_count", 0),
                fraud_count=s_data.get("fraud_count", 0),
                fraud_prevalence=s_data.get("fraud_prevalence", 0.0),
                b2_recall=s_data.get("b2_recall"),
                signalgate_recall=s_data.get("signalgate_recall"),
                delta_recall_vs_b2_pp=s_data.get("delta_recall_vs_b2_pp"),
                scenario_hash=s_data.get("scenario_hash", ""),
                replay_available=True,
            )
        )

    return ScenariosResponse(
        status=results.get("status", "SYNTHETIC_SMOKE_ONLY"),
        scenarios=scenario_items,
    )
