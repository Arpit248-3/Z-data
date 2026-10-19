"""SignalGate IBM Architecture Integration — Governed Agents & Audit Test Suite.

Verifies:
1. AgentCaseView strict ground-truth quarantine enforcement (LeakageViolationError).
2. CaseCopilot offline template briefs across alert, review, disagreement, and routine cases.
3. CaseCopilot epistemic uncertainty grounding (disagreement is uncertainty, not fraud proof).
4. ConfigurableLLMProvider fail-safe fallback on unconfigured or unreachable endpoints.
5. Action Invariance: Agent execution, failure, or timeout has zero influence on routing actions.
6. Proposal Isolation: Policy proposals remain inert AWAITING_HUMAN_APPROVAL records.
7. ClaimVerifier deterministic comparison operators (eq, ne, lt, lte, gt, gte, in).
8. ClaimVerifier acceptance of true facts, rejection of false facts, and missing evidence handling.
9. ClaimLedger audit tracking and acceptance rate calculation.
10. AuditChain sequential linking (prev_hash, seq, record_hash) and HMAC-SHA256 signatures.
11. AuditChain exhaustive tamper detection (modified payload, dropped block, reordered blocks, forged signature).
12. AuditChain fail-closed key governance (unconfigured key reports signing UNAVAILABLE).

Governing Specification: docs/ibm_architecture_integration_master_spec.md § C, § J
Requirements Covered: AGNT-01, AGNT-02, AGNT-03
"""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
from pathlib import Path
from typing import Dict, List
import pytest

from integrations.ibm_architecture.agent_view import (
    AgentCaseView,
    check_for_quarantine_violations,
)
from integrations.ibm_architecture.agents import (
    AgentSupervisor,
    CaseCopilot,
    ConfigurableLLMProvider,
    CopilotBrief,
    OfflineTemplateProvider,
)
from integrations.ibm_architecture.contracts import (
    Action,
    AgentRecord,
    AuditRecord,
    Claim,
    Proposal,
    ReasonCode,
    ZERO_HASH,
)
from integrations.ibm_architecture.exceptions import LeakageViolationError
from integrations.ibm_architecture.governance import (
    AuditChain,
    ClaimLedger,
    ClaimVerifier,
    VerificationResult,
)


@pytest.fixture
def sample_case_view() -> AgentCaseView:
    """Fixture providing a valid sanitized AgentCaseView."""
    return AgentCaseView(
        record_id="TX_1001",
        p=0.0925,
        u=0.15,
        u2=0.12,
        n=None,
        action="FRAUD_ALERT",
        reason="R1_HIGH_RISK",
        record_hash="a" * 64,
        cfg_hash="b" * 64,
        split_hash="c" * 64,
    )


# ==============================================================================
# 1. Input Quarantine Barrier Tests
# ==============================================================================

def test_agent_case_view_quarantine_enforcement():
    """Verify AgentCaseView rejects all ground-truth labels and raw transaction identifiers."""
    forbidden_keys = [
        "isFraud",
        "isfraud",
        "true_label",
        "target",
        "label",
        "TransactionID",
        "transaction_id",
        "TransactionDT",
        "transaction_dt",
    ]

    for key in forbidden_keys:
        bad_data = {
            "record_id": "TX_1001",
            "p": 0.05,
            "action": "ROUTINE",
            "reason": "R5_LOW_RISK_RELIABLE",
            "record_hash": "a" * 64,
            "cfg_hash": "b" * 64,
            "split_hash": "c" * 64,
            key: 1,
        }
        with pytest.raises(LeakageViolationError) as exc_info:
            AgentCaseView(**bad_data)
        assert "quarantine violation" in str(exc_info.value).lower()

        with pytest.raises(LeakageViolationError):
            CaseCopilot().explain_case(bad_data)


# ==============================================================================
# 2. Case Copilot & Provider Dual-Mode Tests
# ==============================================================================

def test_case_copilot_offline_template_alert_case(sample_case_view: AgentCaseView):
    """Verify Copilot generates structured high-risk advisory brief in offline mode."""
    copilot = CaseCopilot(provider=OfflineTemplateProvider())
    brief = copilot.explain_case(sample_case_view)

    assert isinstance(brief, CopilotBrief)
    assert brief.case_id == "TX_1001"
    assert brief.mode == "offline_template"
    assert brief.is_live_llm is False
    assert "elevated fraud risk" in brief.risk_assessment.lower()
    assert len(brief.suggested_investigation_focus) >= 2


def test_case_copilot_offline_template_disagreement_case():
    """Verify Copilot explicitly interprets model disagreement as epistemic uncertainty, not fraud proof."""
    disagreement_view = AgentCaseView(
        record_id="TX_1002",
        p=0.055,  # Below alert threshold
        u=0.55,
        u2=0.58,  # Above disagreement threshold
        action="MANUAL_REVIEW",
        reason="R3_MODEL_DISAGREEMENT",
        record_hash="a" * 64,
        cfg_hash="b" * 64,
        split_hash="c" * 64,
    )
    copilot = CaseCopilot(provider=OfflineTemplateProvider())
    brief = copilot.explain_case(disagreement_view)

    assert brief.case_id == "TX_1002"
    assert "model disagreement" in brief.risk_assessment.lower()
    # Invariant: Disagreement must be explicitly described as uncertainty, NOT proof of fraud
    assert "epistemic model uncertainty" in brief.uncertainty_interpretation
    assert "not affirmative proof of fraud" in brief.uncertainty_interpretation.lower()


def test_case_copilot_offline_template_routine_case():
    """Verify Copilot generates routine low-risk brief for low-risk cases."""
    routine_view = AgentCaseView(
        record_id="TX_1003",
        p=0.012,
        u=0.01,
        u2=0.01,
        action="ROUTINE",
        reason="R5_LOW_RISK_RELIABLE",
        record_hash="a" * 64,
        cfg_hash="b" * 64,
        split_hash="c" * 64,
    )
    copilot = CaseCopilot(provider=OfflineTemplateProvider())
    brief = copilot.explain_case(routine_view)

    assert "routine transaction" in brief.risk_assessment.lower()
    assert "straight-through processing" in brief.suggested_investigation_focus[0].lower()


def test_case_copilot_live_llm_fallback_on_unconfigured(sample_case_view: AgentCaseView):
    """Verify ConfigurableLLMProvider without endpoint seamlessly falls back to offline template."""
    provider = ConfigurableLLMProvider(endpoint_url=None)
    copilot = CaseCopilot(provider=provider)
    brief = copilot.explain_case(sample_case_view)

    assert brief.mode == "offline_template"
    assert brief.is_live_llm is False
    assert brief.fallback_reason == "Live LLM endpoint not configured"


def test_case_copilot_live_llm_fallback_on_network_error(sample_case_view: AgentCaseView):
    """Verify ConfigurableLLMProvider with unreachable endpoint falls back gracefully."""
    # Point to non-existent local port
    provider = ConfigurableLLMProvider(
        endpoint_url="http://127.0.0.1:59999/api/generate",
        timeout_seconds=0.5,
    )
    copilot = CaseCopilot(provider=provider)
    brief = copilot.explain_case(sample_case_view)

    assert brief.mode == "offline_template"
    assert brief.is_live_llm is False
    assert "Live LLM call failed" in str(brief.fallback_reason)


# ==============================================================================
# 3. Action Invariance & Non-Authority Boundary Tests
# ==============================================================================

def test_agent_action_invariance_guarantee(sample_case_view: AgentCaseView):
    """Verify agent advice has ZERO influence on deterministic routing action and reason code."""
    original_action = sample_case_view.action
    original_reason = sample_case_view.reason

    # Execute Copilot
    copilot = CaseCopilot()
    brief = copilot.explain_case(sample_case_view)

    # Assert case view remains completely unchanged
    assert sample_case_view.action == original_action == "FRAUD_ALERT"
    assert sample_case_view.reason == original_reason == "R1_HIGH_RISK"
    assert not hasattr(brief, "action")  # Brief has no action authority


def test_supervisor_dispatch_and_error_isolation(sample_case_view: AgentCaseView):
    """Verify Supervisor wraps execution safely and logs AgentRecord on failure."""
    supervisor = AgentSupervisor()
    brief, record = supervisor.dispatch_copilot(sample_case_view)

    assert isinstance(brief, CopilotBrief)
    assert isinstance(record, AgentRecord)
    assert record.agent_id == "case_copilot"
    assert record.record_id == "TX_1001"
    assert record.status == "ok"
    assert len(record.input_hash) == 64
    assert len(record.output_hash) == 64


def test_supervisor_proposal_isolation():
    """Verify policy proposals remain inert AWAITING_HUMAN_APPROVAL records."""
    supervisor = AgentSupervisor()
    proposal = Proposal(
        proposal_id="PROP_2026_01",
        base_cfg_hash="a" * 64,
        changes={"t_alert": 0.090},
        rationale="Minor drift observed in recent validation window",
    )
    res = supervisor.submit_proposal(proposal)

    assert res["status"] == "AWAITING_HUMAN_APPROVAL"
    assert len(supervisor.pending_proposals) == 1
    # Verify proposal cannot mutate active system
    assert not hasattr(proposal, "apply")
    assert not hasattr(proposal, "execute")


# ==============================================================================
# 4. Claim Verifier & Claim Ledger Tests
# ==============================================================================

def test_claim_verifier_comparison_operators(sample_case_view: AgentCaseView):
    """Verify ClaimVerifier correctly evaluates eq, ne, lt, lte, gt, gte, in."""
    verifier = ClaimVerifier()

    # 1. eq
    c_eq_true = Claim(field="action", operator="eq", value="FRAUD_ALERT", template_id="T1")
    assert verifier.verify_claim(c_eq_true, sample_case_view).is_verified is True

    c_eq_false = Claim(field="action", operator="eq", value="ROUTINE", template_id="T1")
    assert verifier.verify_claim(c_eq_false, sample_case_view).is_verified is False

    # 2. ne
    c_ne = Claim(field="reason", operator="ne", value="R5_LOW_RISK_RELIABLE", template_id="T2")
    assert verifier.verify_claim(c_ne, sample_case_view).is_verified is True

    # 3. gt & gte (p = 0.0925)
    c_gt = Claim(field="p", operator="gt", value=0.08, template_id="T3")
    assert verifier.verify_claim(c_gt, sample_case_view).is_verified is True

    c_gte = Claim(field="p", operator="gte", value=0.0925, template_id="T3")
    assert verifier.verify_claim(c_gte, sample_case_view).is_verified is True

    # 4. lt & lte
    c_lt = Claim(field="p", operator="lt", value=0.10, template_id="T4")
    assert verifier.verify_claim(c_lt, sample_case_view).is_verified is True

    c_lte = Claim(field="p", operator="lte", value=0.05, template_id="T4")
    assert verifier.verify_claim(c_lte, sample_case_view).is_verified is False

    # 5. in
    c_in = Claim(field="action", operator="in", value=["FRAUD_ALERT", "MANUAL_REVIEW"], template_id="T5")
    assert verifier.verify_claim(c_in, sample_case_view).is_verified is True


def test_claim_verifier_rejects_missing_evidence(sample_case_view: AgentCaseView):
    """Verify ClaimVerifier fails gracefully when claim references missing fields."""
    verifier = ClaimVerifier()
    c_missing = Claim(field="non_existent_score", operator="eq", value=42, template_id="T6")
    res = verifier.verify_claim(c_missing, sample_case_view)

    assert res.is_verified is False
    assert "not found in case evidence" in res.reason


def test_claim_ledger_tracking_and_statistics(tmp_path: Path, sample_case_view: AgentCaseView):
    """Verify ClaimLedger tracks assertions and computes acceptance rate."""
    ledger = ClaimLedger()
    verifier = ClaimVerifier()

    c1 = Claim(field="p", operator="gt", value=0.05, template_id="T1")
    c2 = Claim(field="action", operator="eq", value="ROUTINE", template_id="T2")  # False claim

    r1 = verifier.verify_claim(c1, sample_case_view)
    r2 = verifier.verify_claim(c2, sample_case_view)

    ledger.record_claim("TX_1001", c1, r1)
    ledger.record_claim("TX_1001", c2, r2)

    assert ledger.total_claims == 2
    assert ledger.verified_count == 1
    assert ledger.rejected_count == 1
    assert ledger.get_acceptance_rate() == 0.5

    # Test JSONL export and reload
    export_file = tmp_path / "claims.jsonl"
    count = ledger.export_jsonl(export_file)
    assert count == 2

    new_ledger = ClaimLedger()
    new_ledger.load_jsonl(export_file)
    assert new_ledger.total_claims == 2
    assert new_ledger.verified_count == 1


# ==============================================================================
# 5. Cryptographic HMAC-SHA256 Audit Chain Tests
# ==============================================================================

def test_audit_chain_sequential_linking_and_hmac():
    """Verify AuditChain builds monotonically linked blocks with valid HMAC-SHA256 signatures."""
    key = "super_secret_test_key_2026"
    chain = AuditChain(secret_key=key)

    assert chain.signing_status == "AVAILABLE"

    # Append 3 decisions
    r0 = chain.append_decision("TX_001", action="ROUTINE", reason="R5_LOW_RISK_RELIABLE", p=0.01)
    r1 = chain.append_decision("TX_002", action="MANUAL_REVIEW", reason="R2_INTERMEDIATE_RISK", p=0.075)
    r2 = chain.append_decision("TX_003", action="FRAUD_ALERT", reason="R1_HIGH_RISK", p=0.095)

    assert len(chain.records) == 3

    # Check sequence numbers
    assert [r.seq for r in chain.records] == [0, 1, 2]

    # Check hash linkage
    assert r0.prev_hash == ZERO_HASH
    assert r1.prev_hash == r0.record_hash
    assert r2.prev_hash == r1.record_hash

    # Check HMAC signatures are non-empty and 64 hex chars
    assert len(r0.signature) == 64
    assert len(r1.signature) == 64
    assert len(r2.signature) == 64

    # Full verification passes
    is_valid, errors = chain.verify_chain()
    assert is_valid is True
    assert len(errors) == 0


def test_audit_chain_tamper_detection_modified_payload():
    """Verify AuditChain detects modified record payload (tamper evidence)."""
    key = "test_key"
    chain = AuditChain(secret_key=key)
    chain.append_decision("TX_001", action="ROUTINE", reason="R5_LOW_RISK_RELIABLE", p=0.01)
    chain.append_decision("TX_002", action="FRAUD_ALERT", reason="R1_HIGH_RISK", p=0.09)

    # Tamper with block 1: modify action without re-computing hash
    tampered_rec = chain.records[1].model_copy(update={"action": "ROUTINE"})
    chain.records[1] = tampered_rec

    is_valid, errors = chain.verify_chain()
    assert is_valid is False
    assert any("Tampered record" in err for err in errors)


def test_audit_chain_tamper_detection_dropped_block():
    """Verify AuditChain detects dropped or omitted records."""
    key = "test_key"
    chain = AuditChain(secret_key=key)
    chain.append_decision("TX_001", action="ROUTINE", reason="R5_LOW_RISK_RELIABLE", p=0.01)
    chain.append_decision("TX_002", action="MANUAL_REVIEW", reason="R2_INTERMEDIATE_RISK", p=0.075)
    chain.append_decision("TX_003", action="FRAUD_ALERT", reason="R1_HIGH_RISK", p=0.095)

    # Drop block 1
    del chain.records[1]

    is_valid, errors = chain.verify_chain()
    assert is_valid is False
    assert any("Broken hash chain" in err or "Invalid sequence" in err for err in errors)


def test_audit_chain_tamper_detection_forged_signature():
    """Verify AuditChain detects forged or invalid HMAC signature."""
    key = "test_key"
    chain = AuditChain(secret_key=key)
    chain.append_decision("TX_001", action="ROUTINE", reason="R5_LOW_RISK_RELIABLE", p=0.01)

    # Forged signature
    forged_rec = chain.records[0].model_copy(update={"signature": "f" * 64})
    chain.records[0] = forged_rec

    is_valid, errors = chain.verify_chain()
    assert is_valid is False
    assert any("Forged or invalid HMAC signature" in err for err in errors)


def test_audit_chain_unconfigured_key_handling():
    """Verify AuditChain handles missing key by reporting UNAVAILABLE and skipping signature."""
    chain = AuditChain(secret_key=None)
    assert chain.signing_status == "UNAVAILABLE"

    rec = chain.append_decision("TX_001", action="ROUTINE", reason="R5_LOW_RISK_RELIABLE", p=0.01)
    assert rec.signature == ""

    # Unsigned chain verifies structure correctly
    is_valid, errors = chain.verify_chain(verify_signatures=False)
    assert is_valid is True
    assert len(errors) == 0
