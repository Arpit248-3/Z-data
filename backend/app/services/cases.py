"""SignalGate Cases Service

Serves paginated transaction cases and case details from actual persisted artifacts.
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional
from backend.app.schemas import CaseDetailResponse, CaseListItem, CasesResponse
from backend.app.services.artifacts import ArtifactService


class CaseService:
    def __init__(self, artifact_service: ArtifactService):
        self.artifacts = artifact_service

    def _load_all_cases(self, mode: Optional[str] = None) -> List[Dict[str, Any]]:
        mode_upper = (mode or "SYNTHETIC_SMOKE_ONLY").strip().upper()
        if mode_upper in ("IEEE_CIS_OFFLINE_BENCHMARK", "IEEE_CIS", "REAL"):
            cases_path = self.artifacts.project_root / "results" / "ieee_cis_v1" / "cases_benchmark.jsonl"
        elif mode_upper == "LIVE_SOURCE_NOT_CONNECTED":
            return []
        else:
            cases_path = self.artifacts.project_root / "results" / "cases.jsonl"

        if not cases_path.exists():
            return []
        cases = []
        try:
            with open(cases_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        cases.append(json.loads(line))
        except Exception:
            return []
        return cases

    def list_cases(
        self,
        limit: int = 50,
        offset: int = 0,
        action: Optional[str] = None,
        reason_code: Optional[str] = None,
        scenario: Optional[str] = "S0",
        risk_min: Optional[float] = None,
        risk_max: Optional[float] = None,
        search: Optional[str] = None,
        mode: Optional[str] = None,
    ) -> CasesResponse:
        all_cases = self._load_all_cases(mode=mode)
        filtered = []

        for c in all_cases:
            if scenario and c.get("scenario_id") != scenario:
                continue

            dec = c.get("decision", {})
            act = dec.get("action")
            rsn = dec.get("reason_code")
            p_val = c.get("signals", {}).get("p", 0.0)

            if action and act != action:
                continue
            if reason_code:
                target_reason = "R3_MODEL_DISAGREEMENT" if reason_code == "R3_DISAGREEMENT" else reason_code
                if rsn != target_reason:
                    continue
            if risk_min is not None and p_val < risk_min:
                continue
            if risk_max is not None and p_val > risk_max:
                continue
            if search:
                cid = str(c.get("case_id", ""))
                if search not in cid:
                    continue

            filtered.append(c)

        total_count = len(filtered)
        clamped_limit = min(200, max(1, limit))
        paged = filtered[offset : offset + clamped_limit]

        items: List[CaseListItem] = []
        for c in paged:
            dec = c.get("decision", {})
            sigs = c.get("signals", {})
            feats = c.get("features", {})
            offline = c.get("offline_evaluation", {})

            items.append(
                CaseListItem(
                    case_id=c.get("case_id", ""),
                    timestamp=c.get("timestamp", 0),
                    amount=c.get("amount", 0.0),
                    product_cd=feats.get("ProductCD"),
                    card4=feats.get("card4"),
                    scenario_id=c.get("scenario_id", "S0"),
                    p=sigs.get("p", 0.0),
                    u=sigs.get("u"),
                    action=dec.get("action", ""),
                    reason_code=dec.get("reason_code", ""),
                    governor_status=dec.get("governor_status", ""),
                    lane_rank=dec.get("lane_rank"),
                    offline_is_fraud=offline.get("is_fraud"),
                )
            )

        return CasesResponse(
            total_cases=total_count,
            limit=clamped_limit,
            offset=offset,
            scenario_id=scenario or "all",
            cases=items,
        )

    def get_case_detail(self, case_id: str, mode: Optional[str] = None) -> Optional[CaseDetailResponse]:
        # Try requested mode first, then fallback to other if not found
        all_cases = self._load_all_cases(mode=mode)
        if not all_cases and mode:
            all_cases = self._load_all_cases(mode="IEEE_CIS_OFFLINE_BENCHMARK") + self._load_all_cases(mode="SYNTHETIC_SMOKE_ONLY")
        for c in all_cases:
            if str(c.get("case_id")) == str(case_id):
                return CaseDetailResponse(
                    case_id=str(c.get("case_id")),
                    timestamp=c.get("timestamp", 0),
                    amount=c.get("amount", 0.0),
                    scenario_id=c.get("scenario_id", "S0"),
                    status=c.get("status", "SYNTHETIC_SMOKE_ONLY"),
                    signals=c.get("signals", {}),
                    decision=c.get("decision", {}),
                    features=c.get("features", {}),
                    offline_evaluation=c.get("offline_evaluation"),
                    explanations=c.get("explanations", {"status": "disabled", "attributions": None}),
                )
        return None
