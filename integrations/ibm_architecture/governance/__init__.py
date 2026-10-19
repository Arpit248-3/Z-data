"""SignalGate IBM Architecture Integration — Governance Subpackage.

Exports Claim Verifier, Claim Ledger, Cryptographic Audit Chain, Drift Monitor,
Drift Sentinel, and Replay Gate.
"""

from integrations.ibm_architecture.governance.claim_verifier import (
    ClaimVerifier,
    VerificationResult,
)
from integrations.ibm_architecture.governance.claim_ledger import (
    ClaimLedger,
    ClaimLedgerEntry,
)
from integrations.ibm_architecture.governance.audit_chain import (
    AuditChain,
)
from integrations.ibm_architecture.governance.drift_monitor import (
    DriftMonitor,
    DriftReport,
    FeatureDriftResult,
)
from integrations.ibm_architecture.governance.drift_sentinel import (
    DriftSentinel,
    SentinelConfig,
    ALLOWLISTED_POLICY_KEYS,
    PARAMETER_BOUNDS,
)
from integrations.ibm_architecture.governance.replay_gate import (
    ReplayGate,
    ReplayValidationResult,
    ProposalStatus,
)

__all__ = [
    # Claim Verification
    "ClaimVerifier",
    "VerificationResult",
    "ClaimLedger",
    "ClaimLedgerEntry",
    # Audit Chain
    "AuditChain",
    # Drift Monitoring
    "DriftMonitor",
    "DriftReport",
    "FeatureDriftResult",
    # Drift Sentinel
    "DriftSentinel",
    "SentinelConfig",
    "ALLOWLISTED_POLICY_KEYS",
    "PARAMETER_BOUNDS",
    # Replay Gate
    "ReplayGate",
    "ReplayValidationResult",
    "ProposalStatus",
]
