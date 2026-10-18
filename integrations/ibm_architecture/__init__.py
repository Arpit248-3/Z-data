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
]
