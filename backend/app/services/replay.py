"""SignalGate Replay Service

Serves chronological transaction replay rows from saved replay artifacts.
"""

import json
from typing import Any, Dict, List, Optional, Tuple
from backend.app.schemas import ReplayRowItem, ReplayRowsResponse
from backend.app.services.artifacts import ArtifactService


class ReplayService:
    def __init__(self, artifact_service: ArtifactService):
        self.artifacts = artifact_service

    def _load_replay_rows(self, mode: Optional[str] = None) -> Tuple[List[Dict[str, Any]], str]:
        mode_upper = (mode or "SYNTHETIC_SMOKE_ONLY").strip().upper()
        if mode_upper in ("IEEE_CIS_OFFLINE_BENCHMARK", "IEEE_CIS", "REAL"):
            path = self.artifacts.project_root / "results" / "ieee_cis_v1" / "replay_rows.jsonl"
            status = "IEEE_CIS_OFFLINE_BENCHMARK"
            if not path.exists():
                # Fallback to cases_benchmark.jsonl
                bench_path = self.artifacts.project_root / "results" / "ieee_cis_v1" / "cases_benchmark.jsonl"
                if bench_path.exists():
                    rows = []
                    try:
                        with open(bench_path, "r", encoding="utf-8") as f:
                            for idx, line in enumerate(f, 1):
                                if line.strip():
                                    c = json.loads(line)
                                    cid = str(c.get("case_id") or c.get("TransactionID") or idx)
                                    feat = c.get("features", {})
                                    sig = c.get("signals", {})
                                    dec = c.get("decision", {})
                                    off = c.get("offline_evaluation", {})
                                    rows.append({
                                        "row_id": idx,
                                        "case_id": cid,
                                        "timestamp": c.get("timestamp", 86400),
                                        "transaction_id": cid,
                                        "amount": float(c.get("amount", feat.get("TransactionAmt", 50.0))),
                                        "product_cd": str(feat.get("ProductCD", "W")),
                                        "card4": str(feat.get("card4", "visa")),
                                        "p": float(sig.get("p", 0.02)),
                                        "u": float(sig.get("u2", 0.15)),
                                        "u_method": "u2_rank_residual",
                                        "action": str(dec.get("action", "ROUTINE")),
                                        "reason_code": str(dec.get("reason_code", "R5_LOW_RISK_RELIABLE")),
                                        "governor_status": str(dec.get("governor_status", "not_applicable")),
                                        "lane_rank": dec.get("lane_rank"),
                                        "scenario_id": str(c.get("scenario_id", "S0")),
                                        "status": status,
                                        "offline_ground_truth": off,
                                    })
                        return rows, status
                    except Exception:
                        pass
        elif mode_upper in ("LIVE_SOURCE_NOT_CONNECTED", "LIVE"):
            return [], "LIVE_SOURCE_NOT_CONNECTED"
        else:
            path = self.artifacts.project_root / "results" / "replay_rows.jsonl"
            status = "SYNTHETIC_SMOKE_ONLY"

        if not path.exists():
            return [], status
        rows = []
        try:
            with open(path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        rows.append(json.loads(line))
        except Exception:
            return [], status
        return rows, status

    def get_replay_rows(
        self,
        scenario: str = "S0",
        offset: int = 0,
        limit: int = 100,
        mode: Optional[str] = None,
    ) -> ReplayRowsResponse:
        all_rows, status_str = self._load_replay_rows(mode=mode)
        if status_str == "LIVE_SOURCE_NOT_CONNECTED":
            return ReplayRowsResponse(
                total_rows=0,
                offset=offset,
                limit=limit,
                scenario_id=scenario,
                status=status_str,
                rows=[],
            )

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
                    scenario_id=r.get("scenario_id", scenario),
                    status=status_str,
                    offline_ground_truth=r.get("offline_ground_truth"),
                )
            )

        return ReplayRowsResponse(
            total_rows=total_rows,
            offset=offset,
            limit=clamped_limit,
            scenario_id=scenario,
            status=status_str,
            rows=items,
        )
