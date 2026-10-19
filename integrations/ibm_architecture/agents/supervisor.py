"""SignalGate IBM Architecture Integration — Agent Supervisor.

Implements the Agent Supervisor orchestrating governed multi-agent operations:
- Enforces strict input validation on all dispatched records (AgentCaseView).
- Catches provider exceptions and guarantees Action Invariance: agent failure never
  mutates or blocks deterministic routing decisions.
- Enforces Proposal Isolation: any policy change proposal emitted by agents remains
  strictly an inert Proposal object requiring human authorization and deterministic replay.
- Records structured AgentRecord provenance entries.

Governing Specification: docs/ibm_architecture_integration_master_spec.md § C, § J, § K
"""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from typing import Any, Dict, List, Optional, Tuple, Union

from integrations.ibm_architecture.agent_view import AgentCaseView, check_for_quarantine_violations
from integrations.ibm_architecture.agents.copilot import CaseCopilot, CopilotBrief
from integrations.ibm_architecture.agents.providers import OfflineTemplateProvider
from integrations.ibm_architecture.contracts import AgentRecord, Proposal


class AgentSupervisor:
    """Governed Agent Supervisor managing copilot dispatch, error isolation, and proposal gating."""

    def __init__(self, copilot: Optional[CaseCopilot] = None) -> None:
        self.copilot: CaseCopilot = copilot or CaseCopilot()
        self.fallback_provider = OfflineTemplateProvider()
        self.agent_records: List[AgentRecord] = []
        self.pending_proposals: List[Proposal] = []

    def dispatch_copilot(self, case_view: Union[AgentCaseView, Dict[str, Any]]) -> Tuple[CopilotBrief, AgentRecord]:
        """Safely dispatch case view to CaseCopilot with exception wrapping and provenance logging.

        Guarantees:
        - If copilot execution fails or times out, returns safe fallback brief and logs failed AgentRecord.
        - Under all conditions, the case's deterministic routing action is preserved untouched.
        """
        # 1. Enforce sanitized view boundary
        if isinstance(case_view, dict):
            check_for_quarantine_violations(case_view, context="AgentSupervisor.dispatch_copilot")
            view = AgentCaseView(**case_view)
        elif isinstance(case_view, AgentCaseView):
            view = case_view
        else:
            raise TypeError(f"Expected AgentCaseView or dict, got {type(case_view).__name__}")

        input_canonical = json.dumps(view.model_dump(), sort_keys=True, separators=(",", ":"))
        input_hash = hashlib.sha256(input_canonical.encode("utf-8")).hexdigest()

        try:
            brief = self.copilot.explain_case(view)
            status = "ok"
            output_canonical = json.dumps(brief.model_dump(), sort_keys=True, separators=(",", ":"))
            output_hash = hashlib.sha256(output_canonical.encode("utf-8")).hexdigest()
        except Exception as exc:
            # Fallback to offline template on copilot failure
            fallback_res = self.fallback_provider.generate("Emergency fallback prompt", view.model_dump())
            brief = CopilotBrief(
                case_id=view.record_id,
                risk_assessment=fallback_res["risk_assessment"],
                uncertainty_interpretation=fallback_res["uncertainty_interpretation"],
                suggested_investigation_focus=fallback_res["suggested_investigation_focus"],
                mode="offline_template",
                provider="supervisor_fallback",
                is_live_llm=False,
                fallback_reason=f"Copilot dispatch failed ({type(exc).__name__}: {str(exc)})",
            )
            status = "failed"
            output_canonical = json.dumps(brief.model_dump(), sort_keys=True, separators=(",", ":"))
            output_hash = hashlib.sha256(output_canonical.encode("utf-8")).hexdigest()

        record = AgentRecord(
            agent_id="case_copilot",
            record_id=view.record_id,
            status=status,
            claims=[],
            input_hash=input_hash,
            cfg_hash=view.cfg_hash,
            output_hash=output_hash,
            timestamp=datetime.now(timezone.utc),
        )
        self.agent_records.append(record)
        return brief, record

    def submit_proposal(self, proposal: Proposal) -> Dict[str, Any]:
        """Register an advisory policy proposal.

        Authority Barrier:
        Proposals have zero execution authority. They cannot mutate active policies.
        They must remain in AWAITING_HUMAN_APPROVAL status until deterministic replay passes.
        """
        if not isinstance(proposal, Proposal):
            raise TypeError(f"Expected Proposal, got {type(proposal).__name__}")

        self.pending_proposals.append(proposal)
        return {
            "proposal_id": proposal.proposal_id,
            "status": "AWAITING_HUMAN_APPROVAL",
            "message": (
                "Advisory proposal registered. Active policy remains unchanged. "
                "Requires deterministic validation replay and explicit human authorization."
            ),
        }
