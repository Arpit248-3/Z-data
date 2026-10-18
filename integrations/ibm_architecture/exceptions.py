"""SignalGate IBM Architecture Integration — Exception Hierarchy.

Strict exception classes enforcing ground-truth quarantine barriers, fail-closed
mode resolution, and artifact integrity guarantees.
"""

from typing import Any, Iterable, Optional, Set


class SignalGateIntegrationError(Exception):
    """Base exception for all SignalGate IBM Architecture integration operations."""

    def __init__(self, message: str, details: Optional[dict[str, Any]] = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details or {}


class LeakageViolationError(SignalGateIntegrationError, ValueError):
    """Raised when ground-truth labels or raw identifiers violate quarantine barriers.

    In compliance with Master Spec § C2, target labels (`isFraud`, `target`, `label`,
    `true_label`) and raw transaction identifiers (`TransactionID`, `TransactionDT`)
    must never enter feature matrices, calibration/inference requests, scoring forms,
    routing decisions, AgentCaseView, LLM prompts, or online operational paths.
    """

    def __init__(
        self,
        message: str,
        violated_fields: Optional[Iterable[str]] = None,
        context: Optional[str] = None,
    ) -> None:
        self.violated_fields: Set[str] = set(violated_fields or [])
        self.context = context or "unspecified"
        details = {
            "violated_fields": sorted(self.violated_fields),
            "context": self.context,
        }
        full_msg = message
        if self.violated_fields:
            full_msg = f"{message} (Quarantined fields detected: {sorted(self.violated_fields)})"
        super().__init__(full_msg, details=details)


class GroundTruthQuarantineError(LeakageViolationError):
    """Explicit alias for ground-truth label leakage violations."""
    pass


class ModeUnavailableError(SignalGateIntegrationError, RuntimeError):
    """Raised when an evidence mode cannot be resolved or executed.

    In compliance with Master Spec § C1, real benchmark modes must fail closed
    with explicit diagnostic error reporting rather than silently degrading
    to synthetic smoke fixtures or inventing transaction records.
    """

    def __init__(
        self,
        mode: str,
        reason: str,
        missing_prerequisites: Optional[Iterable[str]] = None,
        diagnostics: Optional[dict[str, Any]] = None,
    ) -> None:
        self.mode = mode
        self.reason = reason
        self.missing_prerequisites = list(missing_prerequisites or [])
        details = {
            "mode": mode,
            "reason": reason,
            "missing_prerequisites": self.missing_prerequisites,
            "diagnostics": diagnostics or {},
        }
        msg = f"Evidence mode '{mode}' is unavailable: {reason}."
        if self.missing_prerequisites:
            msg += f" Missing prerequisites: {', '.join(self.missing_prerequisites)}"
        super().__init__(msg, details=details)


class ArtifactNotFoundError(SignalGateIntegrationError, FileNotFoundError):
    """Raised when a required artifact (dataset, checkpoint, manifest) is not found."""

    def __init__(self, artifact_path: str, expected_purpose: str) -> None:
        self.artifact_path = artifact_path
        self.expected_purpose = expected_purpose
        details = {
            "artifact_path": artifact_path,
            "expected_purpose": expected_purpose,
        }
        msg = f"Required artifact not found at '{artifact_path}' for purpose: {expected_purpose}"
        super().__init__(msg, details=details)


class IncompatibleArtifactError(SignalGateIntegrationError, ValueError):
    """Raised when an artifact hash, schema, or partition does not match expectations."""

    def __init__(
        self,
        artifact_path: str,
        expected_hash: str,
        actual_hash: str,
        details: Optional[dict[str, Any]] = None,
    ) -> None:
        self.artifact_path = artifact_path
        self.expected_hash = expected_hash
        self.actual_hash = actual_hash
        err_details = details or {}
        err_details.update({
            "artifact_path": artifact_path,
            "expected_hash": expected_hash,
            "actual_hash": actual_hash,
        })
        msg = (
            f"Artifact fingerprint mismatch at '{artifact_path}'. "
            f"Expected SHA-256: {expected_hash}, got: {actual_hash}"
        )
        super().__init__(msg, details=err_details)
