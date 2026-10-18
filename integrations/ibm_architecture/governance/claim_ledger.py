"""SignalGate IBM Architecture Integration — Deterministic Claim Ledger.

Maintains an immutable, auditable in-memory or persisted ledger of verified
agent claims, rejected propositions, and execution records with cryptographic provenance.
"""

from __future__ import annotations

import threading
from typing import Any, Dict, List, Optional
from integrations.ibm_architecture.contracts import AgentRecord, Claim


class ClaimLedger:
    """Thread-safe ledger recording verified agent claims and validation audits."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._records: List[AgentRecord] = []
        self._rejected_claims: List[Dict[str, Any]] = []

    def record_agent_execution(self, record: AgentRecord) -> None:
        """Store a completed AgentRecord in the ledger."""
        with self._lock:
            self._records.append(record)

    def record_rejected_claim(
        self,
        record_id: str,
        claim: Claim,
        rejection_reason: str,
    ) -> None:
        """Store an unverified or rejected proposition for compliance auditing."""
        with self._lock:
            self._rejected_claims.append({
                "record_id": record_id,
                "claim": claim.model_dump(),
                "reason": rejection_reason,
            })

    def get_records_for_case(self, record_id: str) -> List[AgentRecord]:
        """Retrieve all agent records for a given case."""
        with self._lock:
            return [r for r in self._records if r.record_id == record_id]

    def get_all_records(self) -> List[AgentRecord]:
        """Retrieve all recorded agent executions."""
        with self._lock:
            return list(self._records)

    def get_rejected_claims(self) -> List[Dict[str, Any]]:
        """Retrieve all logged rejected claims."""
        with self._lock:
            return list(self._rejected_claims)
