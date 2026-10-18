"""SignalGate Replay Service

Serves chronological transaction replay rows from saved replay artifacts.
"""

import json
from typing import Any, Dict, List, Optional
from backend.app.schemas import ReplayRowItem, ReplayRowsResponse
from backend.app.services.artifacts import ArtifactService


class ReplayService:
    def __init__(self, artifact_service: ArtifactService):
        self.artifacts = artifact_service

    def _load_replay_rows(self) -> List[Dict[str, Any]]:
        path = self.artifacts.project_root / "results" / "replay_rows.jsonl"
        if not path.exists():
            return []
        rows = []
        try:
            with open(path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        rows.append(json.loads(line))
        except Exception:
            return []
        return rows

    def get_replay_rows(
        self,
        scenario: str = "S0",
        offset: int = 0,
        limit: int = 100,
    ) -> ReplayRowsResponse:
        all_rows = self._load_replay_rows()
        filtered = [r for r in all_rows if r.get("scenario_id") == scenario]
        if not filtered and all_rows:
            filtered = [r for r in all_rows if r.get("scenario_id") == "S0"] or all_rows
        total_rows = len(filtered)

        clamped_limit = min(500, max(1, limit))
        paged = filtered[offset : offset + clamped_limit]

        items: List[ReplayRowItem] = []
        for r in paged:
            items.append(
                ReplayRowItem(
                    row_id=r.get("row_id", 0),
                    case_id=r.get("case_id", ""),
                    timestamp=r.get("timestamp", 0),
                    transaction_id=r.get("transaction_id", ""),
                    amount=r.get("amount", 0.0),
                    product_cd=r.get("product_cd", "W"),
                    card4=r.get("card4", "visa"),
                    p=r.get("p", 0.0),
                    u=r.get("u", 0.0),
                    u_method=r.get("u_method", "u2_rank_residual"),
                    action=r.get("action", ""),
                    reason_code=r.get("reason_code", ""),
                    governor_status=r.get("governor_status", ""),
                    lane_rank=r.get("lane_rank"),
                    scenario_id=r.get("scenario_id", "S0"),
                    status=r.get("status", "SYNTHETIC_SMOKE_ONLY"),
                    offline_ground_truth=r.get("offline_ground_truth"),
                )
            )

        return ReplayRowsResponse(
            total_rows=total_rows,
            offset=offset,
            limit=clamped_limit,
            scenario_id=scenario,
            status="SYNTHETIC_SMOKE_ONLY",
            rows=items,
        )
