"""
SignalGate JSONL Audit Trail Module
Implements structured decision auditing conforming strictly to Blueprint Section 8.4:
- Captures row ID, timestamp, risk score p, disagreement u, novelty n, and stage-2 status.
- Logs decision action and reason code (R0-R6).
- Records latency, configuration hash, split hash, lane rank, governor status, and synthetic flag.
- Validates every record against the strict audit schema before appending.
- Never logs true labels in live inference audit records.
"""

from dataclasses import asdict, dataclass
import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union
import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parent.parent

VALID_ACTIONS = {"FRAUD_ALERT", "MANUAL_REVIEW", "ROUTINE", "HELD", "DEFERRED"}
VALID_REASONS = {
    "R0_SIGNAL_UNAVAILABLE",
    "R1_HIGH_RISK",
    "R2_INTERMEDIATE_RISK",
    "R3_MODEL_DISAGREEMENT",
    "R4_UNFAMILIAR_INPUT",
    "R5_LOW_RISK_RELIABLE",
    "R6_CAPACITY_DEFERRED",
}
VALID_GOVERNOR_STATUSES = {"admitted", "deferred", "not_applicable"}
VALID_STAGE2_STATUSES = {"computed", "skipped", "failed", "unavailable"}


@dataclass
class AuditRecord:
    id: str
    ts: int
    p: Optional[float]
    u: Optional[float]
    u_method: Optional[str]
    n: Optional[float]
    stage2_status: str
    action: str
    reason: str
    latency_ms: float
    explanation_status: str
    feature_attributions: Optional[List[Dict[str, Any]]]
    cfg_hash: str
    split_hash: str
    lane_rank: Optional[int]
    governor_status: str
    synthetic_scenario: bool

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def validate_audit_record(record: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validate that an audit record conforms strictly to the Blueprint Section 8.4 schema.
    """
    errors = []
    required_keys = [
        "id", "ts", "p", "u", "u_method", "n", "stage2_status", "action",
        "reason", "latency_ms", "explanation_status", "feature_attributions",
        "cfg_hash", "split_hash", "lane_rank", "governor_status", "synthetic_scenario"
    ]

    for k in required_keys:
        if k not in record:
            errors.append(f"Missing required audit field: '{k}'")

    if errors:
        return False, errors

    # Check action and reason
    if record["action"] not in VALID_ACTIONS:
        errors.append(f"Invalid action '{record['action']}'. Must be in {VALID_ACTIONS}")

    if record["reason"] not in VALID_REASONS:
        errors.append(f"Invalid reason code '{record['reason']}'. Must be in {VALID_REASONS}")

    if record["governor_status"] not in VALID_GOVERNOR_STATUSES:
        errors.append(f"Invalid governor_status '{record['governor_status']}'")

    if record["stage2_status"] not in VALID_STAGE2_STATUSES:
        errors.append(f"Invalid stage2_status '{record['stage2_status']}'")

    # Check p value if not None
    if record["p"] is not None:
        if not isinstance(record["p"], (int, float)) or not (0.0 <= record["p"] <= 1.0):
            errors.append(f"Audit record p out of bounds [0, 1]: {record['p']}")

    # Check forbidden leakage keys
    for forbidden in ["true_label", "isFraud", "label"]:
        if forbidden in record:
            errors.append(f"CRITICAL LEAKAGE: Ground-truth target '{forbidden}' found in audit record!")

    return len(errors) == 0, errors


class AuditLogger:
    """
    Appends validated audit records to a JSONL log file.
    """

    def __init__(self, log_path: Union[str, Path] = "logs/audit.jsonl"):
        out_path = Path(log_path)
        if not out_path.is_absolute():
            out_path = PROJECT_ROOT / out_path
        self.log_path = out_path
        os.makedirs(self.log_path.parent, exist_ok=True)

    def log_record(self, record: Union[AuditRecord, Dict[str, Any]]):
        rec_dict = record.to_dict() if isinstance(record, AuditRecord) else dict(record)
        is_valid, errors = validate_audit_record(rec_dict)
        if not is_valid:
            raise ValueError(f"Audit record failed schema validation: {errors}")

        with open(self.log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec_dict) + "\n")

    def log_batch(self, records: List[Union[AuditRecord, Dict[str, Any]]]):
        lines = []
        for rec in records:
            rec_dict = rec.to_dict() if isinstance(rec, AuditRecord) else dict(rec)
            is_valid, errors = validate_audit_record(rec_dict)
            if not is_valid:
                raise ValueError(f"Audit record failed schema validation: {errors}")
            lines.append(json.dumps(rec_dict))

        with open(self.log_path, "a", encoding="utf-8") as f:
            f.write("\n".join(lines) + "\n")


def write_audit_record(
    record: Union[AuditRecord, Dict[str, Any]],
    log_path: Union[str, Path] = "logs/audit.jsonl",
):
    """Convenience helper to write a single validated audit record."""
    logger = AuditLogger(log_path)
    logger.log_record(record)
