"""SignalGate Audit Trail Service

Reads and exports auditable JSONL records strictly conforming to Blueprint Section 8.4.
"""

import csv
import io
import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from backend.app.schemas import AuditListResponse
from backend.app.services.artifacts import ArtifactService


class AuditService:
    def __init__(self, artifact_service: ArtifactService):
        self.artifacts = artifact_service

    def _read_audit_records(self) -> Tuple[List[Dict[str, Any]], int]:
        audit_path = self.artifacts.project_root / "logs" / "audit.jsonl"
        if not audit_path.exists():
            return [], 0

        records: List[Dict[str, Any]] = []
        skipped = 0

        with open(audit_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    rec = json.loads(line)
                    records.append(rec)
                except Exception:
                    skipped += 1

        return records, skipped

    def list_records(
        self,
        limit: int = 50,
        offset: int = 0,
        action: Optional[str] = None,
        reason_code: Optional[str] = None,
        case_id: Optional[str] = None,
    ) -> AuditListResponse:
        records, skipped = self._read_audit_records()
        filtered = []

        for r in records:
            if action and r.get("action") != action:
                continue
            if reason_code:
                target_reason = "R3_MODEL_DISAGREEMENT" if reason_code == "R3_DISAGREEMENT" else reason_code
                if r.get("reason") != target_reason:
                    continue
            if case_id and str(r.get("id")) != str(case_id):
                continue
            filtered.append(r)

        total_records = len(filtered)
        clamped_limit = min(200, max(1, limit))
        paged = filtered[offset : offset + clamped_limit]

        return AuditListResponse(
            total_records=total_records,
            offset=offset,
            limit=clamped_limit,
            skipped_records=skipped,
            records=paged,
        )

    def export_records(
        self,
        format_type: str = "jsonl",
        action: Optional[str] = None,
        reason_code: Optional[str] = None,
        case_id: Optional[str] = None,
    ) -> str:
        records, _ = self._read_audit_records()
        filtered = []

        for r in records:
            if action and r.get("action") != action:
                continue
            if reason_code:
                target_reason = "R3_MODEL_DISAGREEMENT" if reason_code == "R3_DISAGREEMENT" else reason_code
                if r.get("reason") != target_reason:
                    continue
            if case_id and str(r.get("id")) != str(case_id):
                continue
            filtered.append(r)

        if format_type == "csv":
            if not filtered:
                return "id,ts,p,u,action,reason,stage2_status\n"
            output = io.StringIO()
            headers = ["id", "ts", "p", "u", "action", "reason", "stage2_status", "lane_rank", "governor_status"]
            writer = csv.DictWriter(output, fieldnames=headers, extrasaction="ignore")
            writer.writeheader()
            for r in filtered:
                writer.writerow(r)
            return output.getvalue()

        # Default JSONL
        return "\n".join(json.dumps(r) for r in filtered) + "\n"
