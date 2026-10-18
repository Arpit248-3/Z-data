"""SignalGate Mode Registry & Telemetry Routers.

Exposes explicit evidence mode readiness, active operating status, and fail-closed switching.
Governing Specification: docs/ibm_architecture_integration_master_spec.md § C1, § F, § L
"""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from integrations.ibm_architecture.modes import EvidenceMode, ModeReadiness, ModeState
from integrations.ibm_architecture.registry import mode_registry

router = APIRouter(prefix="/modes", tags=["Operating Modes"])


class ModeDetail(BaseModel):
    mode: str
    available: bool
    status: str
    active: bool
    description: str
    missing_prerequisites: List[str] = Field(default_factory=list)
    diagnostics: Dict[str, Any] = Field(default_factory=dict)


class ModesOverviewResponse(BaseModel):
    active_mode: str
    supported_modes: List[ModeDetail]
    notice: str


class ModeSelectRequest(BaseModel):
    mode: str


class ModeSelectResponse(BaseModel):
    active_mode: str
    message: str
    status: str
    diagnostics: Dict[str, Any] = Field(default_factory=dict)


@router.get("", response_model=ModesOverviewResponse)
def get_all_modes() -> ModesOverviewResponse:
    """Return all supported evidence modes with explicit readiness, active state, and hardware disclosures."""
    states = mode_registry.get_all_modes()
    mode_details = []

    for mode_enum, state in states.items():
        is_active = (mode_enum == EvidenceMode.SYNTHETIC_SMOKE_ONLY)
        mode_details.append(
            ModeDetail(
                mode=state.mode.value,
                available=state.available,
                status=state.readiness.value,
                active=is_active,
                description=state.description,
                missing_prerequisites=state.missing_prerequisites,
                diagnostics=state.diagnostics,
            )
        )

    return ModesOverviewResponse(
        active_mode=EvidenceMode.SYNTHETIC_SMOKE_ONLY.value,
        supported_modes=mode_details,
        notice=(
            "SignalGate strictly distinguishes runtime operational modes. "
            "SYNTHETIC_SMOKE_ONLY is the active demonstration mode. "
            "Full IEEE-CIS benchmark training is deferred due to host 8 GB RAM limitations."
        ),
    )


@router.get("/{mode_id}", response_model=ModeDetail)
def get_mode_detail(mode_id: str) -> ModeDetail:
    """Retrieve fine-grained readiness diagnostics for a specific operational evidence mode."""
    try:
        mode_enum = EvidenceMode(mode_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "UNKNOWN_MODE",
                "message": f"Operational mode '{mode_id}' is not recognized.",
                "details": {"supported_modes": [m.value for m in EvidenceMode]},
            },
        )

    state = mode_registry.resolve_mode(mode_enum)
    is_active = (mode_enum == EvidenceMode.SYNTHETIC_SMOKE_ONLY)

    return ModeDetail(
        mode=state.mode.value,
        available=state.available,
        status=state.readiness.value,
        active=is_active,
        description=state.description,
        missing_prerequisites=state.missing_prerequisites,
        diagnostics=state.diagnostics,
    )


@router.post("/select", response_model=ModeSelectResponse)
def select_mode(request: ModeSelectRequest) -> ModeSelectResponse:
    """Attempt to switch the active operational evidence mode.

    Fails closed when requested mode is unavailable or deferred; never falls back silently.
    """
    try:
        mode_enum = EvidenceMode(request.mode)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "INVALID_MODE",
                "message": f"Mode '{request.mode}' is invalid.",
                "details": {"supported_modes": [m.value for m in EvidenceMode]},
            },
        )

    state = mode_registry.resolve_mode(mode_enum)

    if not state.available:
        # Fail closed with explicit HTTP 409 Conflict / 503 Unavailable
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "code": "MODE_UNAVAILABLE",
                "message": (
                    f"Operational mode '{request.mode}' cannot be activated: {state.description}"
                ),
                "details": {
                    "mode": state.mode.value,
                    "status": state.readiness.value,
                    "missing_prerequisites": state.missing_prerequisites,
                    "diagnostics": state.diagnostics,
                },
            },
        )

    return ModeSelectResponse(
        active_mode=state.mode.value,
        message=f"Mode '{state.mode.value}' activated successfully.",
        status=state.readiness.value,
        diagnostics=state.diagnostics,
    )
