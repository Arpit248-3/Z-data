"""SignalGate IBM Architecture Integration — Governed Case Copilot.

Provides decision-support briefs for fraud triage cases strictly within the AgentView boundary:
- Rejects raw features, datasets, or label containers (must receive AgentCaseView).
- Every proposed claim is verified deterministically against AgentCaseView facts.
- Operates in offline-template mode by default or with an optional configured provider.
- Invariant: Agent failure, delay, or disabled state NEVER modifies deterministic routing actions.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any, Callable, List, Optional

from integrations.ibm_architecture.agent_view import AgentCaseView
from integrations.ibm_architecture.contracts import Action, AgentRecord, Claim, ReasonCode
from integrations.ibm_architecture.governance.claim_verifier import ClaimVerifier


def canonical_json_bytes(obj: Any) -> bytes:
    """Serialize object to canonical JSON bytes for deterministic hashing."""
    if hasattr(obj, "model_dump"):
        data = obj.model_dump(mode="json")
    elif isinstance(obj, dict):
        data = obj
    else:
        data = {"value": str(obj)}
    text = json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return text.encode("utf-8")


class CaseCopilot:
    """Decision-support copilot operating strictly within allowlisted AgentCaseView boundaries."""

    def __init__(
        self,
        verifier: Optional[ClaimVerifier] = None,
        llm_provider: Optional[Callable[[AgentCaseView], List[Claim]]] = None,
        timeout_seconds: float = 5.0,
    ) -> None:
        self.verifier = verifier or ClaimVerifier()
        self.llm_provider = llm_provider
        self.timeout_seconds = timeout_seconds

    def generate_brief(self, case_view: AgentCaseView) -> AgentRecord:
        """Generate a verified decision-support record for one case view."""
        # 1. Fail closed if input is not an AgentCaseView
        if not isinstance(case_view, AgentCaseView):
            raise TypeError(
                f"Prohibited input: CaseCopilot requires AgentCaseView, got {type(case_view).__name__}"
            )

        input_hash = hashlib.sha256(canonical_json_bytes(case_view)).hexdigest()

        # 2. Check provider availability
        if self.llm_provider is None:
            raw_claims = self._generate_offline_claims(case_view)
            status = "ok"
        else:
            try:
                raw_claims = self.llm_provider(case_view)
                status = "ok"
            except TimeoutError:
                return AgentRecord(
                    agent_id="case_copilot",
                    record_id=case_view.record_id,
                    status="timed_out",
                    claims=[],
                    input_hash=input_hash,
                    cfg_hash=case_view.cfg_hash,
                    output_hash=None,
                    timestamp=datetime.now(timezone.utc),
                )
            except Exception:
                return AgentRecord(
                    agent_id="case_copilot",
                    record_id=case_view.record_id,
                    status="failed",
                    claims=[],
                    input_hash=input_hash,
                    cfg_hash=case_view.cfg_hash,
                    output_hash=None,
                    timestamp=datetime.now(timezone.utc),
                )

        # 3. Deterministically verify each proposed claim
        verified_claims: List[Claim] = []
        for claim in raw_claims:
            res = self.verifier.verify(claim, case_view)
            if res.is_verified:
                verified_claims.append(claim)

        output_hash = (
            hashlib.sha256(canonical_json_bytes({"claims": [c.model_dump() for c in verified_claims]})).hexdigest()
            if verified_claims
            else None
        )

        return AgentRecord(
            agent_id="case_copilot",
            record_id=case_view.record_id,
            status=status,
            claims=verified_claims,
            input_hash=input_hash,
            cfg_hash=case_view.cfg_hash,
            output_hash=output_hash,
            timestamp=datetime.now(timezone.utc),
        )

    def _generate_offline_claims(self, case_view: AgentCaseView) -> List[Claim]:
        """Generate deterministic factual claims directly from the allowlisted case view."""
        claims: List[Claim] = []

        # T1: Calibrated fraud risk claim
        if case_view.p is not None:
            claims.append(
                Claim(
                    field="p",
                    operator="eq",
                    value=round(case_view.p, 4),
                    template_id="T1_CALIBRATED_RISK",
                )
            )

        # T3: Action and ReasonCode claim
        claims.append(
            Claim(
                field="action",
                operator="eq",
                value=case_view.action.value if hasattr(case_view.action, "value") else str(case_view.action),
                template_id="T3_ROUTING_ACTION",
            )
        )

        # T2: Disagreement claim
        if case_view.u is not None:
            claims.append(
                Claim(
                    field="u",
                    operator="eq",
                    value=round(case_view.u, 4),
                    template_id="T2_MODEL_DISAGREEMENT",
                )
            )

        # T7: Robust u2 claim
        if case_view.u2 is not None:
            claims.append(
                Claim(
                    field="u2",
                    operator="eq",
                    value=round(case_view.u2, 4),
                    template_id="T7_ROBUST_MAD_SIGNAL",
                )
            )

        return claims
