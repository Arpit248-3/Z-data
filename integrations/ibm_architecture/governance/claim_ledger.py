"""SignalGate IBM Architecture Integration — Claim Ledger.

Implements an append-only ledger for tracking verified and rejected agent claims:
- Stores audit history of all claims asserted by agents.
- Records verification verdicts, observed values, and timestamps.
- Provides filtering, acceptance rate statistics, and JSONL persistence.

Governing Specification: docs/ibm_architecture_integration_master_spec.md § C, § J3
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union
from pydantic import BaseModel, ConfigDict, Field

from integrations.ibm_architecture.contracts import Claim
from integrations.ibm_architecture.governance.claim_verifier import VerificationResult


class ClaimLedgerEntry(BaseModel):
    """Single entry in the claim ledger."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    record_id: str
    claim: Claim
    result: VerificationResult
    timestamp: str


class ClaimLedger:
    """Append-only ledger of claim verifications."""

    def __init__(self) -> None:
        self.entries: List[ClaimLedgerEntry] = []

    def record_claim(
        self,
        record_id: str,
        claim: Claim,
        result: VerificationResult,
    ) -> ClaimLedgerEntry:
        """Append a verified or rejected claim result to the ledger."""
        entry = ClaimLedgerEntry(
            record_id=str(record_id),
            claim=claim,
            result=result,
            timestamp=result.verified_at,
        )
        self.entries.append(entry)
        return entry

    def get_claims_by_record(self, record_id: str) -> List[ClaimLedgerEntry]:
        """Query all claim entries associated with a specific record ID."""
        target = str(record_id)
        return [e for e in self.entries if e.record_id == target]

    @property
    def total_claims(self) -> int:
        return len(self.entries)

    @property
    def verified_count(self) -> int:
        return sum(1 for e in self.entries if e.result.is_verified)

    @property
    def rejected_count(self) -> int:
        return sum(1 for e in self.entries if not e.result.is_verified)

    def get_acceptance_rate(self) -> float:
        """Calculate proportion of claims verified as true."""
        if not self.entries:
            return 1.0
        return round(float(self.verified_count / len(self.entries)), 6)

    def export_jsonl(self, path: Union[str, Path]) -> int:
        """Export ledger entries to JSONL file."""
        out_path = Path(path)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        count = 0
        with open(out_path, "w", encoding="utf-8") as f:
            for e in self.entries:
                f.write(json.dumps(e.model_dump()) + "\n")
                count += 1
        return count

    def load_jsonl(self, path: Union[str, Path]) -> int:
        """Load ledger entries from an existing JSONL file."""
        in_path = Path(path)
        if not in_path.exists():
            return 0
        count = 0
        with open(in_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                data = json.loads(line)
                entry = ClaimLedgerEntry(**data)
                self.entries.append(entry)
                count += 1
        return count
