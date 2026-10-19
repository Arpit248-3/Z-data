"""SignalGate API Pydantic Schemas

Defines request and response contracts strictly adhering to Blueprint Section 7 & 8:
- Reusable, strongly typed models for all public endpoints.
- Structured ErrorResponse with error code, message, and details.
- Nullable representations with explicit status strings for unavailable data.
- Strict leakage rejection on Sandbox scoring inputs.
"""

from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field, field_validator


# ---------------------------------------------------------------------------
# Error Model
# ---------------------------------------------------------------------------
class ErrorDetail(BaseModel):
    code: str
    message: str
    details: Dict[str, Any] = Field(default_factory=dict)


class ErrorResponse(BaseModel):
    error: ErrorDetail


# ---------------------------------------------------------------------------
# Health & Status
# ---------------------------------------------------------------------------
class HealthResponse(BaseModel):
    service_name: str
    version: str
    status: str
    timestamp: str


class ReadinessStatusResponse(BaseModel):
    service_name: str
    version: str
    overall_status: str
    evidence_status: str
    dependencies: Dict[str, Any]
    hashes: Dict[str, Any]
    readiness: Optional[Dict[str, Any]] = None
    replay: Optional[Dict[str, Any]] = None


# ---------------------------------------------------------------------------
# Overview & Results
# ---------------------------------------------------------------------------
class OverviewResponse(BaseModel):
    dataset_status: str
    is_synthetic: bool
    evaluation_status: str
    total_tested_transactions: Optional[int] = None
    available_fraud_count: Optional[int] = None
    fraud_prevalence: Optional[float] = None
    primary_budget: Optional[float] = None
    b2_recall: Optional[float] = None
    signalgate_recall: Optional[float] = None
    delta_recall_pp: Optional[float] = None
    ci_95: Optional[List[float]] = None
    ci_conclusive: Optional[bool] = None
    touched_rate: Optional[float] = None
    alert_rate: Optional[float] = None
    review_rate: Optional[float] = None
    deferred_rate: Optional[float] = None
    confident_miss_count: Optional[int] = None
    routine_fraud_rate: Optional[float] = None
    latency_p95_ms: Optional[float] = None
    frozen_config_hash: Optional[str] = None
    split_hash: Optional[str] = None
    status_fields: Dict[str, str] = Field(default_factory=dict)


# ---------------------------------------------------------------------------
# Policies & Comparison
# ---------------------------------------------------------------------------
class PolicyComparisonItem(BaseModel):
    policy: str
    target_budget: float
    total_transactions: int
    escalated_count: int
    touched_rate: float
    total_fraud: int
    caught_fraud: int
    missed_fraud: int
    recall_at_touched: float
    precision: float
    fpr: Optional[float] = None
    deferred_count: Optional[int] = None
    deferred_rate: Optional[float] = None
    confident_miss_count: Optional[int] = None
    routine_fraud_rate: Optional[float] = None
    threshold: Optional[float] = None


class PolicyCompareResponse(BaseModel):
    status: str
    is_synthetic: bool
    budget_multiple: str
    target_budget: float
    policies: List[PolicyComparisonItem]
    disclaimer: str


# ---------------------------------------------------------------------------
# Scenarios
# ---------------------------------------------------------------------------
class ScenarioItem(BaseModel):
    scenario_id: str
    name: str
    description: str
    status: str
    is_synthetic: bool
    sample_count: int
    fraud_count: int
    fraud_prevalence: float
    b2_recall: Optional[float] = None
    signalgate_recall: Optional[float] = None
    delta_recall_vs_b2_pp: Optional[float] = None
    scenario_hash: str
    replay_available: bool


class ScenariosResponse(BaseModel):
    status: str
    scenarios: List[ScenarioItem]


# ---------------------------------------------------------------------------
# Cases Explorer
# ---------------------------------------------------------------------------
class CaseListItem(BaseModel):
    case_id: str
    timestamp: int
    amount: float
    product_cd: Optional[str] = None
    card4: Optional[str] = None
    scenario_id: str
    p: float
    u: Optional[float] = None
    action: str
    reason_code: str
    governor_status: str
    lane_rank: Optional[int] = None
    offline_is_fraud: Optional[int] = None


class CasesResponse(BaseModel):
    total_cases: int
    limit: int
    offset: int
    scenario_id: str
    cases: List[CaseListItem]


class CaseDetailResponse(BaseModel):
    case_id: str
    timestamp: int
    amount: float
    scenario_id: str
    status: str
    signals: Dict[str, Any]
    decision: Dict[str, Any]
    features: Dict[str, Any]
    offline_evaluation: Optional[Dict[str, Any]] = None
    explanations: Dict[str, Any]


# ---------------------------------------------------------------------------
# Shift Storm Replay
# ---------------------------------------------------------------------------
class ReplayRowItem(BaseModel):
    row_id: int
    case_id: str
    timestamp: int
    transaction_id: str
    amount: float
    product_cd: str
    card4: str
    p: float
    u: float
    u_method: str
    action: str
    reason_code: str
    governor_status: str
    lane_rank: Optional[int] = None
    scenario_id: str
    status: str
    offline_ground_truth: Optional[Dict[str, Any]] = None


class ReplayRowsResponse(BaseModel):
    total_rows: int
    offset: int
    limit: int
    scenario_id: str
    status: str
    rows: List[ReplayRowItem]


class ReplayStatusResponse(BaseModel):
    state: Optional[str] = None
    replay_state: str
    is_running: bool = False
    data_provenance: str
    source_file: str
    replay_source: Optional[str] = None
    total_available_rows: Optional[int] = None
    cursor_row: int
    cursor_position: Optional[int] = None
    received_count: int
    accepted_count: int
    rejected_count: int
    duplicate_count: int = 0
    scored_count: int
    last_received_event: Optional[Dict[str, Any]] = None
    last_scored_event: Optional[Dict[str, Any]] = None
    recent_caserate: float
    avg_latency_ms: Optional[float] = None
    last_latency_ms: Optional[float] = 0.0
    errors: List[str] = Field(default_factory=list)
    backend_readiness: bool = True
    model_readiness: bool = True
    ieee_data_readiness: bool = True
    live_source_readiness: bool = False
    live_source_status: str = "DISCONNECTED"
    external_live_source_status: str = "DISCONNECTED"
    notice: str


class ReplayControlRequest(BaseModel):
    limit: Optional[int] = Field(500, ge=1, le=50000, description="Max transactions to replay in this run.")
    delay_ms: Optional[int] = Field(50, ge=0, le=5000, description="Inter-transaction delay in milliseconds.")


class ReplayControlResponse(BaseModel):
    status: str
    message: str
    replay_state: str
    data_provenance: Optional[str] = "HISTORICAL_REPLAY"
    scored_count: Optional[int] = None


class ReplayStepResponse(BaseModel):
    status: str
    scored: bool
    event: Optional[Dict[str, Any]] = None
    message: Optional[str] = None
    cursor_row: Optional[int] = None


# ---------------------------------------------------------------------------
# Audit Trail
# ---------------------------------------------------------------------------
class AuditListResponse(BaseModel):
    total_records: int
    offset: int
    limit: int
    skipped_records: int = 0
    records: List[Dict[str, Any]]


import math


# ---------------------------------------------------------------------------
# Scoring Sandbox
# ---------------------------------------------------------------------------
FORBIDDEN_SCORING_FIELDS = {
    "true_label",
    "isfraud",
    "target",
    "label",
    "y_true",
    "ground_truth",
    "transactionid",
    "transactiondt",
    "raw_transactiondt",
    "rawtransactiondt",
    "id",
}


def _check_forbidden_recursively(obj: Any) -> None:
    if isinstance(obj, dict):
        for k, v in obj.items():
            k_norm = str(k).lower().replace("_", "").replace("-", "")
            if k_norm in {f.replace("_", "").replace("-", "") for f in FORBIDDEN_SCORING_FIELDS}:
                raise ValueError(
                    f"LEAKAGE VIOLATION: Forbidden field '{k}' is strictly rejected from scoring inputs."
                )
            _check_forbidden_recursively(v)
    elif isinstance(obj, (list, tuple, set)):
        for item in obj:
            _check_forbidden_recursively(item)


class SandboxScoreRequest(BaseModel):
    features: Dict[str, Any]
    mode: str = "SYNTHETIC_SMOKE_ONLY"

    @field_validator("features")
    def reject_forbidden_features(cls, v: Dict[str, Any]) -> Dict[str, Any]:
        if not v:
            raise ValueError("Feature payload cannot be empty.")

        # 1. Recursive leakage check
        _check_forbidden_recursively(v)

        # 2. Enforce scalar and finite-value constraints
        for k, val in v.items():
            if isinstance(val, (dict, list, tuple)):
                raise ValueError(f"Feature '{k}' must be a scalar value (float, int, str, or null).")
            if isinstance(val, float):
                if math.isnan(val) or math.isinf(val):
                    raise ValueError(f"Feature '{k}' contains non-finite value ({val}). Pass null to represent missing data.")
            elif isinstance(val, str):
                if val.strip().lower() in ("nan", "inf", "-inf", "+inf", "infinity", "-infinity"):
                    raise ValueError(f"Feature '{k}' contains non-finite string representation '{val}'.")

        return v


class SandboxScoreResponse(BaseModel):
    decision_id: str
    timestamp: str
    signals: Dict[str, Any]
    decision: Dict[str, Any]
    governor: Dict[str, Any]
    latency_ms: float
    provenance: Dict[str, Any]
    audit_logged: bool
    notice: str
    model_id: Optional[str] = None
    cfg_hash: Optional[str] = None
    audit_seq: Optional[int] = None
    mode: Optional[str] = None


# ---------------------------------------------------------------------------
# Operating Modes & Model Card
# ---------------------------------------------------------------------------
class ModeReadinessResponse(BaseModel):
    active_mode: str
    available_modes: List[str]
    modes_detail: Dict[str, Any]
    notice: str


class ModelCardResponse(BaseModel):
    mode: str
    model_id: str
    architecture_version: str
    architecture_type: str
    sub_models: List[str]
    calibrator_type: str
    feature_count: int
    features_sample: List[str]
    manifest_hash: str
    artifact_hashes: Dict[str, str]
    split_provenance: Dict[str, Any]
    notice: str
    thresholds: Optional[Dict[str, float]] = None
    capacity_budget: Optional[Dict[str, Any]] = None


# ---------------------------------------------------------------------------
# Drift Monitoring
# ---------------------------------------------------------------------------
class DriftReportAPIResponse(BaseModel):
    report_id: str
    status: str
    features_monitored: int
    significant_drift_features: int
    moderate_drift_features: int
    mean_psi: float
    max_psi: float
    score_drift: Optional[Dict[str, Any]] = None
    provenance_hash: str
    timestamp: str
    notice: str
    feature_reports: Optional[List[Dict[str, Any]]] = None


# ---------------------------------------------------------------------------
# Governance & Replay Gate
# ---------------------------------------------------------------------------
class GovernanceProposalResponse(BaseModel):
    proposal_id: str
    status: str
    base_cfg_hash: str
    changes: Dict[str, Any]
    rationale: str
    created_at: str
    replay_result: Optional[Dict[str, Any]] = None
    approval_record: Optional[Dict[str, Any]] = None


class ProposalApprovalRequest(BaseModel):
    approver: str = Field(..., min_length=1, description="Authenticated human approver identifier")
    rationale: str = Field(..., min_length=1, description="Audit-trailed business and risk justification")


class ProposalRejectionRequest(BaseModel):
    reviewer: str = Field(..., min_length=1, description="Authenticated human reviewer identifier")
    reason: str = Field(..., min_length=1, description="Audit-trailed rejection rationale")


class GovernanceDecisionResponse(BaseModel):
    proposal_id: str
    status: str
    decision_maker: str
    timestamp: str
    audit_seq: Optional[int] = None
    message: str


# ---------------------------------------------------------------------------
# Audit Chain Verification
# ---------------------------------------------------------------------------
class AuditVerifyResponse(BaseModel):
    status: str
    is_valid: bool
    record_count: int
    signing_status: str
    errors: List[str]
    chain_head_hash: Optional[str] = None
