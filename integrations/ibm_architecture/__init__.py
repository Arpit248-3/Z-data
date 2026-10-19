"""SignalGate IBM Architecture Integration Package.

Provides isolated, clean-room contracts, evidence mode resolution, ground-truth
quarantine barriers, multi-agent governance, and dataset ingestion interfaces.

Governing Specification: docs/ibm_architecture_integration_master_spec.md
"""

from integrations.ibm_architecture.exceptions import (
    ArtifactNotFoundError,
    GroundTruthQuarantineError,
    IncompatibleArtifactError,
    LeakageViolationError,
    ModeUnavailableError,
    SignalGateIntegrationError,
)
from integrations.ibm_architecture.contracts import (
    Action,
    ReasonCode,
    AuditRecord,
    Claim,
    AgentRecord,
    Proposal,
    ModelArtifactManifest,
    ZERO_HASH,
    SHA256_PATTERN,
)
from integrations.ibm_architecture.agent_view import (
    AgentCaseView,
    AgentView,
    check_for_quarantine_violations,
)
from integrations.ibm_architecture.modes import (
    EvidenceMode,
    ModeReadiness,
    ModeState,
)
from integrations.ibm_architecture.registry import (
    ModeRegistry,
    mode_registry,
)
from integrations.ibm_architecture.data import (
    FeatureManifest,
    CANONICAL_FEATURE_MANIFEST,
    ChronologicalSplitter,
    load_ieee_cis,
    process_mock_ieee_cis_fixture,
    validate_dataset_directory,
)
from integrations.ibm_architecture.models import (
    BaselineB2,
    EraBaggedHeterogeneousEnsemble,
    FeaturePipeline,
    PlattCalibrator,
    IsotonicCalibrator,
    calibration_ece,
    DisagreementSignals,
    ModelBundle,
    ModelBundleManifest,
    save_bundle,
    load_bundle,
    train_pipeline,
    train_mock_pipeline_for_testing,
    check_available_ram,
)
from integrations.ibm_architecture.policy import (
    IEEEPolicyConfig,
    get_frozen_ieee_policy_config,
    RouterPolicyAdapter,
    validate_router_config,
    B2TopBudgetBaselineAdapter,
    compute_policy_evaluation_metrics,
    P5CandidatePolicyAdapter,
    CapacityGovernor,
)
from integrations.ibm_architecture.scoring import (
    ScoringRequest,
    ScoringResult,
    BatchScoringResult,
    ScoringService,
    check_feature_quarantine,
)
from integrations.ibm_architecture.agents import (
    CaseCopilot,
    CopilotBrief,
    AgentSupervisor,
    OfflineTemplateProvider,
    ConfigurableLLMProvider,
    LLMProvider,
)
from integrations.ibm_architecture.governance import (
    ClaimVerifier,
    VerificationResult,
    ClaimLedger,
    ClaimLedgerEntry,
    AuditChain,
    DriftMonitor,
    DriftReport,
    FeatureDriftResult,
    DriftSentinel,
    SentinelConfig,
    ALLOWLISTED_POLICY_KEYS,
    PARAMETER_BOUNDS,
    ReplayGate,
    ReplayValidationResult,
    ProposalStatus,
)

__version__ = "1.0.0"

__all__ = [
    # Exceptions
    "SignalGateIntegrationError",
    "LeakageViolationError",
    "GroundTruthQuarantineError",
    "ModeUnavailableError",
    "ArtifactNotFoundError",
    "IncompatibleArtifactError",
    # Contracts
    "Action",
    "ReasonCode",
    "AuditRecord",
    "Claim",
    "AgentRecord",
    "Proposal",
    "ModelArtifactManifest",
    "ZERO_HASH",
    "SHA256_PATTERN",
    # Agent Views
    "AgentCaseView",
    "AgentView",
    "check_for_quarantine_violations",
    # Modes & Registry
    "EvidenceMode",
    "ModeReadiness",
    "ModeState",
    "ModeRegistry",
    "mode_registry",
    # Data Ingestion
    "FeatureManifest",
    "CANONICAL_FEATURE_MANIFEST",
    "ChronologicalSplitter",
    "load_ieee_cis",
    "process_mock_ieee_cis_fixture",
    "validate_dataset_directory",
    # Models & Calibration
    "BaselineB2",
    "EraBaggedHeterogeneousEnsemble",
    "FeaturePipeline",
    "PlattCalibrator",
    "IsotonicCalibrator",
    "calibration_ece",
    "DisagreementSignals",
    "ModelBundle",
    "ModelBundleManifest",
    "save_bundle",
    "load_bundle",
    "train_pipeline",
    "train_mock_pipeline_for_testing",
    "check_available_ram",
    # Policy & Governance
    "IEEEPolicyConfig",
    "get_frozen_ieee_policy_config",
    "RouterPolicyAdapter",
    "validate_router_config",
    "B2TopBudgetBaselineAdapter",
    "compute_policy_evaluation_metrics",
    "P5CandidatePolicyAdapter",
    "CapacityGovernor",
    # Scoring Service & Contracts
    "ScoringRequest",
    "ScoringResult",
    "BatchScoringResult",
    "ScoringService",
    "check_feature_quarantine",
    # Governed Agents
    "CaseCopilot",
    "CopilotBrief",
    "AgentSupervisor",
    "OfflineTemplateProvider",
    "ConfigurableLLMProvider",
    "LLMProvider",
    # Claim Verification & Cryptographic Audit
    "ClaimVerifier",
    "VerificationResult",
    "ClaimLedger",
    "ClaimLedgerEntry",
    "AuditChain",
    # Drift Monitoring & Replay Gate
    "DriftMonitor",
    "DriftReport",
    "FeatureDriftResult",
    "DriftSentinel",
    "SentinelConfig",
    "ALLOWLISTED_POLICY_KEYS",
    "PARAMETER_BOUNDS",
    "ReplayGate",
    "ReplayValidationResult",
    "ProposalStatus",
]
