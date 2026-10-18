"""
SignalGate Policy Package
Provides fraud triage decision routing, capacity governance, threshold selection,
baseline policies, and JSONL audit trail logging.
"""

from .router import (
    Action,
    ReasonCode,
    route,
    route_batch,
    validate_router_config,
)
from .governor import (
    CapacityGovernor,
    govern_decisions,
)
from .thresholds import (
    ThresholdConfig,
    select_thresholds,
    sweep_thresholds_across_budgets,
)
from .baselines import (
    baseline_fixed_threshold,
    baseline_top_b,
    baseline_confidence_deferral,
    baseline_random,
    evaluate_policies_matched_budget,
)
from .audit import (
    AuditRecord,
    AuditLogger,
    validate_audit_record,
)

__all__ = [
    "Action",
    "ReasonCode",
    "route",
    "route_batch",
    "validate_router_config",
    "CapacityGovernor",
    "govern_decisions",
    "ThresholdConfig",
    "select_thresholds",
    "sweep_thresholds_across_budgets",
    "baseline_fixed_threshold",
    "baseline_top_b",
    "baseline_confidence_deferral",
    "baseline_random",
    "evaluate_policies_matched_budget",
    "AuditRecord",
    "AuditLogger",
    "validate_audit_record",
]
