"""SignalGate IBM Architecture Integration — Evidence Modes and Readiness Contracts.

Defines the explicit operational source modes and typed readiness states.
Strictly adheres to Master Spec § C1:
- Zero silent fallbacks between modes.
- Distinguishes runtime source modes from evidence classifications.
- Real-data benchmark mode becomes selectable only after prerequisites are verified.
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class EvidenceMode(str, Enum):
    """Explicit operational source and evidence modes."""

    SYNTHETIC_SMOKE_ONLY = "SYNTHETIC_SMOKE_ONLY"
    IEEE_CIS_OFFLINE_BENCHMARK = "IEEE_CIS_OFFLINE_BENCHMARK"
    LIVE_SOURCE_NOT_CONNECTED = "LIVE_SOURCE_NOT_CONNECTED"


class ModeReadiness(str, Enum):
    """Readiness status classifications for evidence modes."""

    READY = "READY"
    UNAVAILABLE_MISSING_RAW_DATA = "UNAVAILABLE_MISSING_RAW_DATA"
    UNAVAILABLE_MISSING_CHECKPOINTS = "UNAVAILABLE_MISSING_CHECKPOINTS"
    NOT_CONNECTED = "NOT_CONNECTED"
    INCOMPATIBLE = "INCOMPATIBLE"


class ModeState(BaseModel):
    """Detailed readiness state descriptor for an evidence mode."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    mode: EvidenceMode = Field(description="The evidence mode being evaluated")
    available: bool = Field(description="Whether the mode is currently selectable and runnable")
    readiness: ModeReadiness = Field(description="Structured readiness classification")
    description: str = Field(description="Human-readable operational description")
    prerequisites_met: bool = Field(description="True if all required filesystem/runtime assets exist")
    missing_prerequisites: List[str] = Field(
        default_factory=list,
        description="List of missing files, credentials, or hardware prerequisites",
    )
    diagnostics: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional diagnostic details, detected paths, or verification hashes",
    )
