"""SignalGate IBM Architecture Integration — Monitoring and Replay Module.

Exposes drift calculations, advisory drift sentinel, and proposal replay gate.
"""

from integrations.ibm_architecture.monitoring.drift import (
    DistributionDriftCalculator,
    calculate_feature_drift,
    calculate_psi,
)
from integrations.ibm_architecture.monitoring.sentinel import (
    ALLOWLISTED_CONFIG_KEYS,
    DriftSentinel,
)
from integrations.ibm_architecture.monitoring.replay_gate import (
    ProposalReplayStatus,
    ReplayEvaluationRecord,
    ReplayGate,
)

__all__ = [
    "DistributionDriftCalculator",
    "calculate_feature_drift",
    "calculate_psi",
    "ALLOWLISTED_CONFIG_KEYS",
    "DriftSentinel",
    "ProposalReplayStatus",
    "ReplayEvaluationRecord",
    "ReplayGate",
]
