"""SignalGate Overview, Consolidated Results, and Scenarios Routers"""

import json
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
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
    mode: Optional[str] = Query(None, description="Operating mode filter."),
    artifacts: ArtifactService = Depends(get_artifact_service),
) -> Dict[str, Any]:
    """Return the complete canonical evaluation document based on mode."""
    mode_upper = (mode or "SYNTHETIC_SMOKE_ONLY").strip().upper()
    if mode_upper in ("IEEE_CIS_OFFLINE_BENCHMARK", "IEEE_CIS", "REAL"):
        benchmark_path = artifacts.project_root / "results" / "ieee_cis_v1" / "benchmark_results.json"
        if benchmark_path.exists():
            try:
                with open(benchmark_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                scenarios = data.get("shift_scenarios", {})
                for s_id, s_data in scenarios.items():
                    s_data.setdefault("sample_count", s_data.get("total_rows", 0))
                    s_data.setdefault("fraud_count", s_data.get("total_fraud", 0))
                    s_data.setdefault("fraud_prevalence", s_data.get("prevalence", 0.0))
                    s_data.setdefault("signalgate_recall", s_data.get("p5_recall", 0.0))
                    s_data.setdefault("name", s_data.get("description", s_id))
                    s_data.setdefault("status", "IEEE_CIS_OFFLINE_BENCHMARK")
                    s_data.setdefault("is_synthetic", False)
                data["status"] = "IEEE_CIS_OFFLINE_BENCHMARK"
                data["is_synthetic"] = False
                return data
            except Exception:
                pass

    if mode_upper in ("LIVE_SOURCE_NOT_CONNECTED", "LIVE"):
        return {
            "status": "LIVE_SOURCE_NOT_CONNECTED",
            "is_synthetic": False,
            "disclaimer": "Live production banking stream is disconnected. No real-time results available.",
            "shift_scenarios": {},
            "budget_sweep": {},
        }

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
    mode: Optional[str] = Query(None, description="Operating mode filter."),
    artifacts: ArtifactService = Depends(get_artifact_service),
) -> ScenariosResponse:
    """Return shift scenarios evaluated under the requested mode."""
    mode_upper = (mode or "SYNTHETIC_SMOKE_ONLY").strip().upper()
    if mode_upper in ("IEEE_CIS_OFFLINE_BENCHMARK", "IEEE_CIS", "REAL"):
        benchmark_path = artifacts.project_root / "results" / "ieee_cis_v1" / "benchmark_results.json"
        if benchmark_path.exists():
            try:
                with open(benchmark_path, "r", encoding="utf-8") as f:
                    bm = json.load(f)
                shift_scenarios = bm.get("shift_scenarios", {})
                scenario_items: List[ScenarioItem] = []
                for s_key, s_data in shift_scenarios.items():
                    # Clean scenario ID (e.g. S0_nominal -> S0)
                    s_id = s_key.split("_")[0]
                    scenario_items.append(
                        ScenarioItem(
                            scenario_id=s_id,
                            name=f"{s_id}: {s_data.get('description', s_key)}",
                            description=s_data.get("description", f"Scenario {s_id}"),
                            status="IEEE_CIS_OFFLINE_BENCHMARK",
                            is_synthetic=(s_id == "S3"),
                            sample_count=s_data.get("total_rows", 0),
                            fraud_count=s_data.get("total_fraud", 0),
                            fraud_prevalence=s_data.get("prevalence", 0.0),
                            b2_recall=s_data.get("b2_recall"),
                            signalgate_recall=s_data.get("p5_recall"),
                            delta_recall_vs_b2_pp=0.0,
                            scenario_hash=bm.get("provenance", {}).get("split_hash_test", "88d73a15fc60f9ba"),
                            replay_available=True,
                        )
                    )
                return ScenariosResponse(
                    status="IEEE_CIS_OFFLINE_BENCHMARK",
                    scenarios=scenario_items,
                )
            except Exception:
                pass

    if mode_upper in ("LIVE_SOURCE_NOT_CONNECTED", "LIVE"):
        return ScenariosResponse(
            status="LIVE_SOURCE_NOT_CONNECTED",
            scenarios=[],
        )

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
