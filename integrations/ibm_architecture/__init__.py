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
    FeaturePipeline,
    BaselineB2,
    EraBaggedHeterogeneousEnsemble,
    MemberPredictions,
    PlattCalibrator,
    IsotonicCalibrator,
    calibration_ece,
    DisagreementSignals,
    DisagreementSignalExtractor,
    RobustDisagreementSignalExtractor,
    compute_signals,
    ModelBundle,
    ModelBundleManifest,
    save_bundle,
    load_bundle,
    check_memory_preflight,
    load_bounded_dev_cohort,
    split_dev_cohort,
    train_local_dev_pipeline,
    load_synthetic_bundle,
    get_model_bundle,
    SyntheticModelAdapter,
)
from integrations.ibm_architecture.policy import (
    RouterPolicyAdapter,
    BaselineB2PolicyAdapter,
    CandidateP5PolicyAdapter,
    GovernedCapacityManager,
    DeterministicScoringService,
)
from integrations.ibm_architecture.governance import (
    ClaimVerifier,
    CaseCopilot,
    ClaimLedger,
    AuditChain,
    verify_chain,
)
from integrations.ibm_architecture.monitoring import (
    DistributionDriftCalculator,
    calculate_feature_drift,
    calculate_psi,
    ALLOWLISTED_CONFIG_KEYS,
    DriftSentinel,
    ProposalReplayStatus,
    ReplayEvaluationRecord,
    ReplayGate,
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
    # Models & Uncertainty
    "FeaturePipeline",
    "BaselineB2",
    "SyntheticModelAdapter",
    "EraBaggedHeterogeneousEnsemble",
    "MemberPredictions",
    "PlattCalibrator",
    "IsotonicCalibrator",
    "calibration_ece",
    "DisagreementSignals",
    "DisagreementSignalExtractor",
    "RobustDisagreementSignalExtractor",
    "compute_signals",
    "ModelBundle",
    "ModelBundleManifest",
    "save_bundle",
    "load_bundle",
    "load_synthetic_bundle",
    "get_model_bundle",
    "check_memory_preflight",
    "load_bounded_dev_cohort",
    "split_dev_cohort",
    "train_local_dev_pipeline",
    # Policy & Governance
    "RouterPolicyAdapter",
    "BaselineB2PolicyAdapter",
    "CandidateP5PolicyAdapter",
    "GovernedCapacityManager",
    "DeterministicScoringService",
    # Governed Agents & Cryptographic Audit
    "ClaimVerifier",
    "CaseCopilot",
    "ClaimLedger",
    "AuditChain",
    "verify_chain",
    # Drift Monitoring & Replay Gate
    "DistributionDriftCalculator",
    "calculate_feature_drift",
    "calculate_psi",
    "ALLOWLISTED_CONFIG_KEYS",
    "DriftSentinel",
    "ProposalReplayStatus",
    "ReplayEvaluationRecord",
    "ReplayGate",
]
