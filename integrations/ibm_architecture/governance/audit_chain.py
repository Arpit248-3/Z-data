"""SignalGate IBM Architecture Integration — Cryptographic HMAC-SHA256 Audit Chain.

Implements an append-only, tamper-evident audit log with cryptographic hash-chaining
and HMAC-SHA256 authentication:
- Sequenced records: seq, prev_hash, record_hash, signature.
- Strict HMAC-SHA256 signature verification over every record hash.
- Key management: accepts explicit signing key or loads from SIGNALGATE_AUDIT_HMAC_KEY.
- verify_chain detects any payload tampering, sequence gaps, or falsified signatures.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import os
import threading
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

from integrations.ibm_architecture.contracts import Action, AuditRecord, ReasonCode, SHA256_PATTERN, ZERO_HASH


def canonical_json_bytes(payload: dict) -> bytes:
    """Return stable, deterministic UTF-8 JSON bytes for cryptographic hashing."""
    text = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )
    return text.encode("utf-8")


def compute_audit_record_hash(record_dict: dict) -> str:
    """Hash the record payload excluding 'record_hash' and 'signature'."""
    clean_payload = {
        k: v for k, v in record_dict.items() if k not in ("record_hash", "signature")
    }
    return hashlib.sha256(canonical_json_bytes(clean_payload)).hexdigest()


def compute_hmac_signature(record_hash: str, key: bytes) -> str:
    """Compute HMAC-SHA256 hex digest over record hash."""
    return hmac.new(key, record_hash.encode("ascii"), hashlib.sha256).hexdigest()


def get_default_audit_key() -> bytes:
    """Load audit key from environment or fallback to a deterministic local development key."""
    env_key = os.environ.get("SIGNALGATE_AUDIT_HMAC_KEY")
    if env_key:
        key_bytes = env_key.encode("utf-8")
        if len(key_bytes) < 32:
            raise ValueError("SIGNALGATE_AUDIT_HMAC_KEY must contain at least 32 bytes")
        return key_bytes
    # Safe deterministic local secret for local development/testing
    return b"signalgate_synthetic_audit_key_32bytes_min_secret!!"


@dataclass(frozen=True)
class VerificationResult:
    """Detailed verification outcome for an audit chain."""

    ok: bool
    record_count: int
    errors: Tuple[str, ...]
    final_hash: str

    def __bool__(self) -> bool:
        return self.ok


class AuditChain:
    """Thread-safe append-only HMAC-SHA256 cryptographic audit logger."""

    def __init__(
        self,
        log_path: Union[str, Path],
        signing_key: Optional[bytes] = None,
    ) -> None:
        self.log_path = Path(log_path)
        self.signing_key = signing_key or get_default_audit_key()
        self._lock = threading.Lock()

        # Ensure parent directory exists
        self.log_path.parent.mkdir(parents=True, exist_ok=True)

        # Initialize sequence and previous hash from existing file if present
        self._seq, self._prev_hash = self._inspect_last_record()

    def _inspect_last_record(self) -> Tuple[int, str]:
        """Read the last record in the log file to resume the chain."""
        if not self.log_path.exists() or self.log_path.stat().st_size == 0:
            return 0, ZERO_HASH

        last_line = ""
        with open(self.log_path, "r", encoding="utf-8") as f:
            for line in f:
                stripped = line.strip()
                if stripped:
                    last_line = stripped

        if not last_line:
            return 0, ZERO_HASH

        try:
            record_data = json.loads(last_line)
            seq = int(record_data.get("seq", 0)) + 1
            prev_hash = str(record_data.get("record_hash", ZERO_HASH))
            return seq, prev_hash
        except Exception:
            return 0, ZERO_HASH

    def append(
        self,
        decision_id: str,
        p: Optional[float],
        u: Optional[float],
        action: Union[Action, str],
        reason: Union[ReasonCode, str],
        cfg_hash: str,
        split_hash: str,
        u2: Optional[float] = None,
        n: Optional[float] = None,
        u_method: str = "u2_rank_residual",
    ) -> AuditRecord:
        """Construct, hash, sign, and append an AuditRecord to the log."""
        with self._lock:
            act_str = action.value if hasattr(action, "value") else str(action)
            rsn_str = reason.value if hasattr(reason, "value") else str(reason)

            # Create unsealed record
            rec = AuditRecord(
                id=decision_id,
                timestamp=datetime.now(timezone.utc),
                seq=self._seq,
                prev_hash=self._prev_hash,
                p=p,
                u=u,
                u2=u2,
                n=n,
                u_method=u_method,
                action=act_str,  # type: ignore[arg-type]
                reason=rsn_str,  # type: ignore[arg-type]
                cfg_hash=cfg_hash,
                split_hash=split_hash,
                record_hash=ZERO_HASH,
                signature="",
            )

            # 1. Compute deterministic record hash
            rec_dict = rec.model_dump(mode="json")
            r_hash = compute_audit_record_hash(rec_dict)

            # 2. Compute HMAC-SHA256 signature
            sig = compute_hmac_signature(r_hash, self.signing_key)

            # 3. Finalize record
            rec.record_hash = r_hash
            rec.signature = sig

            # 4. Append to JSONL file
            line = json.dumps(rec.model_dump(mode="json"), sort_keys=True) + "\n"
            with open(self.log_path, "a", encoding="utf-8") as f:
                f.write(line)

            # 5. Advance internal state
            self._prev_hash = r_hash
            self._seq += 1

            return rec


def verify_chain(
    path: Union[str, Path],
    key: Optional[bytes] = None,
) -> VerificationResult:
    """Verify JSON syntax, sequence numbers, hash continuity, and HMAC signatures of an audit log."""
    log_file = Path(path)
    signing_key = key or get_default_audit_key()

    if not log_file.exists():
        return VerificationResult(
            ok=False,
            record_count=0,
            errors=(f"Log file not found: {log_file}",),
            final_hash=ZERO_HASH,
        )

    errors: List[str] = []
    record_count = 0
    expected_seq = 0
    expected_prev_hash = ZERO_HASH
    last_record_hash = ZERO_HASH

    with open(log_file, "r", encoding="utf-8") as f:
        for line_num, line in enumerate(f, start=1):
            stripped = line.strip()
            if not stripped:
                continue

            # 1. JSON parsing
            try:
                rec_dict = json.loads(stripped)
            except Exception as e:
                errors.append(f"Line {line_num}: Malformed JSON syntax ({e})")
                continue

            record_count += 1

            # 2. Sequence verification
            actual_seq = rec_dict.get("seq")
            if actual_seq != expected_seq:
                errors.append(
                    f"Line {line_num}: Sequence mismatch. Expected {expected_seq}, got {actual_seq}"
                )

            # 3. Hash chain continuity (prev_hash)
            actual_prev_hash = rec_dict.get("prev_hash")
            if actual_prev_hash != expected_prev_hash:
                errors.append(
                    f"Line {line_num}: Hash chain broken. Expected prev_hash {expected_prev_hash}, got {actual_prev_hash}"
                )

            # 4. Payload integrity (record_hash verification)
            declared_hash = rec_dict.get("record_hash")
            computed_hash = compute_audit_record_hash(rec_dict)
            if declared_hash != computed_hash:
                errors.append(
                    f"Line {line_num}: Record hash mismatch (tampered payload). "
                    f"Declared {declared_hash}, computed {computed_hash}"
                )

            # 5. HMAC signature authentication
            declared_sig = rec_dict.get("signature")
            computed_sig = compute_hmac_signature(declared_hash or "", signing_key)
            if declared_sig != computed_sig:
                errors.append(
                    f"Line {line_num}: HMAC signature invalid. Declared {declared_sig}, computed {computed_sig}"
                )

            # Advance expected sequence and hash
            expected_seq += 1
            expected_prev_hash = declared_hash or ZERO_HASH
            last_record_hash = declared_hash or ZERO_HASH

    return VerificationResult(
        ok=len(errors) == 0,
        record_count=record_count,
        errors=tuple(errors),
        final_hash=last_record_hash,
    )
