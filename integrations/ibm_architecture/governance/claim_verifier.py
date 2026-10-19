"""SignalGate IBM Architecture Integration — Deterministic Claim Verifier.

Implements deterministic verification of structured agent claims against source facts:
- Evaluates typed Claim objects across comparison operators (eq, ne, lt, lte, gt, gte, in).
- Validates assertions against factual evidence from AgentCaseView or AuditRecord.
- Rejects unsupported, contradictory, or unevidenced claims deterministically.
- Enforces Grounding Boundary: Arbitrary agent prose is never rendered as established fact
  unless independently verified by ClaimVerifier.

Governing Specification: docs/ibm_architecture_integration_master_spec.md § C, § J3
"""

from __future__ import annotations

from datetime import datetime, timezone
import math
from typing import Any, Dict, List, Tuple, Union
from pydantic import BaseModel, ConfigDict, Field

from integrations.ibm_architecture.agent_view import AgentCaseView
from integrations.ibm_architecture.contracts import AuditRecord, Claim


class VerificationResult(BaseModel):
    """Result of deterministic claim verification against factual case evidence."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    claim: Claim = Field(description="Structured claim evaluated")
    is_verified: bool = Field(description="Whether the claim is mathematically verified by facts")
    observed_value: Any = Field(default=None, description="Actual value observed on source record")
    reason: str = Field(description="Justification explanation for verification outcome")
    verified_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="Timezone-aware UTC timestamp of verification",
    )


class ClaimVerifier:
    """Deterministic factual claim verification engine."""

    TOLERANCE: float = 1e-5

    def _extract_fact(self, field: str, evidence: Union[AgentCaseView, AuditRecord, Dict[str, Any]]) -> Tuple[bool, Any]:
        """Extract field value from evidence source."""
        if isinstance(evidence, (AgentCaseView, AuditRecord)):
            if hasattr(evidence, field):
                return True, getattr(evidence, field)
            # Check model_dump if attribute lookup misses
            dump = evidence.model_dump()
            if field in dump:
                return True, dump[field]
            return False, None
        elif isinstance(evidence, dict):
            if field in evidence:
                return True, evidence[field]
            return False, None
        return False, None

    def verify_claim(
        self,
        claim: Claim,
        evidence: Union[AgentCaseView, AuditRecord, Dict[str, Any]],
    ) -> VerificationResult:
        """Verify a single claim against evidence.

        Evaluates operators: eq, ne, lt, lte, gt, gte, in.
        """
        found, observed = self._extract_fact(claim.field, evidence)

        if not found:
            return VerificationResult(
                claim=claim,
                is_verified=False,
                observed_value=None,
                reason=f"Field '{claim.field}' not found in case evidence.",
            )

        if observed is None:
            return VerificationResult(
                claim=claim,
                is_verified=False,
                observed_value=None,
                reason=f"Observed value for field '{claim.field}' is null/None.",
            )

        op = claim.operator
        expected = claim.value
        is_verified = False
        reason = ""

        try:
            if op == "eq":
                if isinstance(observed, (int, float)) and isinstance(expected, (int, float)):
                    is_verified = abs(float(observed) - float(expected)) <= self.TOLERANCE
                else:
                    is_verified = observed == expected
                reason = "Exact match verified" if is_verified else f"Value mismatch: observed {observed} != expected {expected}"

            elif op == "ne":
                if isinstance(observed, (int, float)) and isinstance(expected, (int, float)):
                    is_verified = abs(float(observed) - float(expected)) > self.TOLERANCE
                else:
                    is_verified = observed != expected
                reason = "Inequality verified" if is_verified else f"Values match unexpectedly: {observed}"

            elif op == "lt":
                is_verified = float(observed) < float(expected)
                reason = "Strict less-than verified" if is_verified else f"Observed {observed} not less than {expected}"

            elif op == "lte":
                is_verified = float(observed) <= (float(expected) + self.TOLERANCE)
                reason = "Less-than-or-equal verified" if is_verified else f"Observed {observed} exceeds {expected}"

            elif op == "gt":
                is_verified = float(observed) > float(expected)
                reason = "Strict greater-than verified" if is_verified else f"Observed {observed} not greater than {expected}"

            elif op == "gte":
                is_verified = float(observed) >= (float(expected) - self.TOLERANCE)
                reason = "Greater-than-or-equal verified" if is_verified else f"Observed {observed} strictly less than {expected}"

            elif op == "in":
                if isinstance(expected, (list, tuple, set)):
                    is_verified = observed in expected
                else:
                    is_verified = str(observed) in str(expected)
                reason = "Set membership verified" if is_verified else f"Observed {observed} not found in {expected}"

            else:
                reason = f"Unsupported comparison operator: {op}"

        except Exception as exc:
            is_verified = False
            reason = f"Verification computation error ({type(exc).__name__}: {str(exc)})"

        return VerificationResult(
            claim=claim,
            is_verified=is_verified,
            observed_value=observed,
            reason=reason,
        )

    def verify_claims(
        self,
        claims: List[Claim],
        evidence: Union[AgentCaseView, AuditRecord, Dict[str, Any]],
    ) -> List[VerificationResult]:
        """Verify multiple claims against evidence."""
        return [self.verify_claim(c, evidence) for c in claims]
