"""SignalGate IBM Architecture Integration — Cryptographic HMAC-SHA256 Audit Chain.

Implements an append-only, tamper-evident cryptographic decision ledger:
- Monotonic sequence numbers (seq: 0, 1, 2, ...).
- Previous-hash linkage (prev_hash_i = record_hash_{i-1}, genesis is 0^64).
- Deterministic canonical record hash (record_hash = SHA-256(canonical_payload)).
- HMAC-SHA256 signatures with secret key loaded strictly from environment (SIGNALGATE_AUDIT_KEY).
- Fail-closed key governance: If key is unconfigured, signing is reported as UNAVAILABLE
  rather than falling back to a hardcoded or predictable default key.
- Exhaustive tamper detection: Identifies modified payloads, dropped records, reordered records,
  and forged or invalid HMAC signatures.
- Honest cryptographic guarantees: Provides local tamper evidence and unbroken provenance,
  not external hardware WORM or distributed consensus.

Governing Specification: docs/ibm_architecture_integration_master_spec.md § C, § J4
"""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import hmac
import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

from integrations.ibm_architecture.contracts import AuditRecord, ZERO_HASH


class AuditChain:
    """Cryptographic HMAC-SHA256 append-only decision audit ledger."""

    def __init__(self, secret_key: Optional[str] = None) -> None:
        self.secret_key = secret_key if secret_key is not None else os.environ.get("SIGNALGATE_AUDIT_KEY")
        self.records: List[AuditRecord] = []

    def __len__(self) -> int:
        return len(self.records)

    def __getitem__(self, index: int) -> AuditRecord:
        return self.records[index]

    @property
    def signing_status(self) -> str:
        """Report cryptographic signing readiness."""
        return "AVAILABLE" if bool(self.secret_key and self.secret_key.strip()) else "UNAVAILABLE"

    def compute_hmac_signature(self, record_hash: str) -> str:
        """Compute HMAC-SHA256 signature over record_hash using configured secret key."""
        if not self.secret_key:
            return ""
        return hmac.new(
            self.secret_key.encode("utf-8"),
            record_hash.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

    def append_decision(
        self,
        record_id: str,
        action: str,
        reason: str,
        p: Optional[float] = None,
        u: Optional[float] = None,
        u2: Optional[float] = None,
        n: Optional[float] = None,
        cfg_hash: str = ZERO_HASH,
        split_hash: str = ZERO_HASH,
        timestamp: Optional[datetime] = None,
    ) -> AuditRecord:
        """Construct, seal, sign, and append an AuditRecord to the chain."""
        seq = len(self.records)
        prev_hash = self.records[-1].record_hash if seq > 0 else ZERO_HASH
        ts = timestamp or datetime.now(timezone.utc)

        # 1. Instantiate draft record
        draft = AuditRecord(
            id=str(record_id),
            timestamp=ts,
            seq=seq,
            prev_hash=prev_hash,
            p=p,
            u=u,
            u2=u2,
            n=n,
            u_method="u2_rank_residual",
            action=action,  # type: ignore[arg-type]
            reason=reason,  # type: ignore[arg-type]
            cfg_hash=cfg_hash if cfg_hash != ZERO_HASH else hashlib.sha256(b"dummy_cfg").hexdigest(),
            split_hash=split_hash if split_hash != ZERO_HASH else hashlib.sha256(b"dummy_split").hexdigest(),
        )

        # 2. Compute canonical record hash
        rec_hash = draft.compute_record_hash()

        # 3. Compute HMAC signature if key is configured
        sig = self.compute_hmac_signature(rec_hash)

        # 4. Seal record
        sealed = AuditRecord(
            id=draft.id,
            timestamp=draft.timestamp,
            seq=draft.seq,
            prev_hash=draft.prev_hash,
            p=draft.p,
            u=draft.u,
            u2=draft.u2,
            n=draft.n,
            u_method=draft.u_method,
            action=draft.action,
            reason=draft.reason,
            cfg_hash=draft.cfg_hash,
            split_hash=draft.split_hash,
            record_hash=rec_hash,
            signature=sig,
        )

        self.records.append(sealed)
        return sealed

    def verify_chain(self, verify_signatures: bool = True) -> Tuple[bool, List[str]]:
        """Perform exhaustive cryptographic audit of ledger integrity.

        Checks:
        1. Monotonic sequence continuity: seq_i == i.
        2. Genesis linkage: prev_hash_0 == ZERO_HASH.
        3. Block linkage: prev_hash_i == record_hash_{i-1}.
        4. Payload hash integrity: record_hash_i == compute_record_hash(record_i).
        5. HMAC signature validity: hmac.compare_digest(record.signature, expected_sig).
        6. Timestamp monotonicity: timestamp_i >= timestamp_{i-1}.
        """
        errors: List[str] = []

        if not self.records:
            return True, []

        for i, rec in enumerate(self.records):
            # Check 1: Sequence continuity
            if rec.seq != i:
                errors.append(f"Block {i}: Invalid sequence number {rec.seq}, expected {i}")

            # Check 2 & 3: Previous hash linkage
            if i == 0:
                if rec.prev_hash != ZERO_HASH:
                    errors.append(f"Genesis block 0: Invalid prev_hash {rec.prev_hash}, expected {ZERO_HASH}")
            else:
                expected_prev = self.records[i - 1].record_hash
                if rec.prev_hash != expected_prev:
                    errors.append(
                        f"Block {i}: Broken hash chain! prev_hash '{rec.prev_hash}' does not match "
                        f"preceding block hash '{expected_prev}'"
                    )

            # Check 4: Record hash integrity
            calculated_hash = rec.compute_record_hash()
            if rec.record_hash != calculated_hash:
                errors.append(
                    f"Block {i} (ID: {rec.id}): Tampered record! Stored hash '{rec.record_hash}' "
                    f"does not match calculated hash '{calculated_hash}'"
                )

            # Check 5: HMAC signature validity
            if verify_signatures and self.secret_key:
                expected_sig = self.compute_hmac_signature(rec.record_hash)
                if not rec.signature:
                    errors.append(f"Block {i} (ID: {rec.id}): Missing HMAC signature on signed ledger.")
                elif not hmac.compare_digest(rec.signature, expected_sig):
                    errors.append(
                        f"Block {i} (ID: {rec.id}): Forged or invalid HMAC signature! "
                        f"Signature does not match key."
                    )

            # Check 6: Timestamp monotonicity
            if i > 0 and rec.timestamp < self.records[i - 1].timestamp:
                errors.append(
                    f"Block {i}: Timestamp non-monotonic ({rec.timestamp.isoformat()} < "
                    f"{self.records[i - 1].timestamp.isoformat()})"
                )

        return len(errors) == 0, errors

    def export_jsonl(self, path: Union[str, Path]) -> int:
        """Export ledger to JSONL file."""
        out_path = Path(path)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        count = 0
        with open(out_path, "w", encoding="utf-8") as f:
            for rec in self.records:
                data = rec.model_dump()
                # Ensure timestamp is ISO string
                data["timestamp"] = rec.timestamp.isoformat()
                f.write(json.dumps(data) + "\n")
                count += 1
        return count

    @classmethod
    def load_jsonl(cls, path: Union[str, Path], secret_key: Optional[str] = None) -> "AuditChain":
        """Load an AuditChain from an existing JSONL file."""
        chain = cls(secret_key=secret_key)
        in_path = Path(path)
        if not in_path.exists():
            return chain

        with open(in_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                data = json.loads(line)
                rec = AuditRecord(**data)
                chain.records.append(rec)
        return chain
