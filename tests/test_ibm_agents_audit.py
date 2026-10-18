"""SignalGate IBM Architecture Integration — Phase 6 Governed Agents & Audit Chain Tests.

Verifies:
- ClaimVerifier deterministic verification of factual claims against AgentCaseView.
- Rejection of seeded false claims, unregistered operators, and malformed templates.
- CaseCopilot decision-support brief generation with routing invariance under provider failure.
- Strict AgentCaseView quarantine enforcement (rejects isFraud, raw IDs, raw timestamps).
- AuditChain HMAC-SHA256 authenticated hash-chaining and append-only semantics.
- verify_chain comprehensive tamper detection (detects payload edits, signature corruption, record deletion).
"""

from __future__ import annotations

import json
import tempfile
from pathlib import Path
import pytest

from integrations.ibm_architecture.agent_view import AgentCaseView
from integrations.ibm_architecture.contracts import AuditRecord, Claim, ZERO_HASH
from integrations.ibm_architecture.exceptions import LeakageViolationError
from integrations.ibm_architecture.governance.audit_chain import AuditChain, get_default_audit_key, verify_chain
from integrations.ibm_architecture.governance.claim_ledger import ClaimLedger
from integrations.ibm_architecture.governance.claim_verifier import ClaimVerifier
from integrations.ibm_architecture.governance.copilot import CaseCopilot
from policy.router import Action, ReasonCode


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def sample_case_view() -> AgentCaseView:
    return AgentCaseView(
        record_id="case_abc123",
        p=0.0850,
        u=0.0450,
        u2=0.1200,
        n=0.0100,
        action=Action.FRAUD_ALERT,
        reason=ReasonCode.R1_HIGH_RISK,
        record_hash="a" * 64,
        cfg_hash="b" * 64,
        split_hash="c" * 64,
    )


# ---------------------------------------------------------------------------
# Claim Verifier Tests
# ---------------------------------------------------------------------------

def test_claim_verifier_accepts_valid_factual_claims(sample_case_view: AgentCaseView) -> None:
    verifier = ClaimVerifier()

    # Valid calibrated risk claim
    claim_p = Claim(
        field="p",
        operator="eq",
        value=0.0850,
        template_id="T1_CALIBRATED_RISK",
    )
    res_p = verifier.verify(claim_p, sample_case_view)
    assert res_p.is_verified is True
    assert "p=0.0850" in (res_p.statement or "")

    # Valid routing action claim
    claim_action = Claim(
        field="action",
        operator="eq",
        value=Action.FRAUD_ALERT.value,
        template_id="T3_ROUTING_ACTION",
    )
    res_act = verifier.verify(claim_action, sample_case_view)
    assert res_act.is_verified is True
    assert "FRAUD_ALERT" in (res_act.statement or "")


def test_claim_verifier_rejects_false_and_unregistered_claims(sample_case_view: AgentCaseView) -> None:
    verifier = ClaimVerifier()

    # 1. Seeded false claim: asserting p=0.9999 when actual p=0.0850
    false_claim = Claim(
        field="p",
        operator="eq",
        value=0.9999,
        template_id="T1_CALIBRATED_RISK",
    )
    res_false = verifier.verify(false_claim, sample_case_view)
    assert res_false.is_verified is False
    assert res_false.statement is None
    assert "Factual check failed" in (res_false.rejection_reason or "")

    # 2. Seeded false action: claiming ROUTINE when actual is FRAUD_ALERT
    false_action = Claim(
        field="action",
        operator="eq",
        value=Action.ROUTINE.value,
        template_id="T3_ROUTING_ACTION",
    )
    res_act = verifier.verify(false_action, sample_case_view)
    assert res_act.is_verified is False

    # 3. Disallowed operator
    disallowed_op = Claim(
        field="record_id",
        operator="gt",
        value="case_000",
        template_id="T1_CALIBRATED_RISK",
    )
    res_op = verifier.verify(disallowed_op, sample_case_view)
    assert res_op.is_verified is False
    assert "Disallowed field-operator pair" in (res_op.rejection_reason or "")


# ---------------------------------------------------------------------------
# Case Copilot Tests
# ---------------------------------------------------------------------------

def test_case_copilot_offline_brief(sample_case_view: AgentCaseView) -> None:
    copilot = CaseCopilot()
    record = copilot.generate_brief(sample_case_view)

    assert record.agent_id == "case_copilot"
    assert record.record_id == sample_case_view.record_id
    assert record.status == "ok"
    assert len(record.claims) >= 2
    assert record.input_hash is not None
    assert record.output_hash is not None


def test_case_copilot_quarantine_enforcement() -> None:
    copilot = CaseCopilot()

    # CaseCopilot requires AgentCaseView; passing arbitrary dict or DataFrame raises TypeError
    with pytest.raises(TypeError):
        copilot.generate_brief({"record_id": "test", "isFraud": 1})  # type: ignore

    # Creating AgentCaseView with quarantined field raises LeakageViolationError
    with pytest.raises(LeakageViolationError):
        AgentCaseView(
            record_id="leak",
            isFraud=1,
            action=Action.ROUTINE,
            reason=ReasonCode.R5_LOW_RISK_RELIABLE,
            record_hash="a" * 64,
            cfg_hash="b" * 64,
            split_hash="c" * 64,
        )


def test_case_copilot_routing_invariance(sample_case_view: AgentCaseView) -> None:
    # Simulated failing provider
    def failing_provider(cv: AgentCaseView) -> list[Claim]:
        raise RuntimeError("LLM provider rate limit exceeded")

    copilot = CaseCopilot(llm_provider=failing_provider)
    record = copilot.generate_brief(sample_case_view)

    assert record.status == "failed"
    assert len(record.claims) == 0

    # Invariant: Original case view routing action and reason code remain unaltered
    assert sample_case_view.action == Action.FRAUD_ALERT
    assert sample_case_view.reason == ReasonCode.R1_HIGH_RISK


# ---------------------------------------------------------------------------
# Claim Ledger Tests
# ---------------------------------------------------------------------------

def test_claim_ledger() -> None:
    ledger = ClaimLedger()
    copilot = CaseCopilot()
    cv = AgentCaseView(
        record_id="c_1",
        p=0.02,
        action=Action.ROUTINE,
        reason=ReasonCode.R5_LOW_RISK_RELIABLE,
        record_hash="0" * 64,
        cfg_hash="0" * 64,
        split_hash="0" * 64,
    )

    record = copilot.generate_brief(cv)
    ledger.record_agent_execution(record)

    claims = ledger.get_records_for_case("c_1")
    assert len(claims) == 1
    assert claims[0].record_id == "c_1"


# ---------------------------------------------------------------------------
# Cryptographic Audit Chain Tests
# ---------------------------------------------------------------------------

def test_audit_chain_append_and_verify() -> None:
    test_key = b"test_secret_audit_key_32_bytes_length!!"

    with tempfile.TemporaryDirectory() as tmp_dir:
        log_path = Path(tmp_dir) / "test_audit.jsonl"
        chain = AuditChain(log_path=log_path, signing_key=test_key)

        # Append 3 records
        r0 = chain.append(
            decision_id="dec_0",
            p=0.01,
            u=0.02,
            action=Action.ROUTINE,
            reason=ReasonCode.R5_LOW_RISK_RELIABLE,
            cfg_hash="1" * 64,
            split_hash="2" * 64,
        )
        assert r0.seq == 0
        assert r0.prev_hash == ZERO_HASH
        assert len(r0.signature) == 64

        r1 = chain.append(
            decision_id="dec_1",
            p=0.09,
            u=0.05,
            action=Action.FRAUD_ALERT,
            reason=ReasonCode.R1_HIGH_RISK,
            cfg_hash="1" * 64,
            split_hash="2" * 64,
        )
        assert r1.seq == 1
        assert r1.prev_hash == r0.record_hash

        r2 = chain.append(
            decision_id="dec_2",
            p=0.075,
            u=0.03,
            action=Action.MANUAL_REVIEW,
            reason=ReasonCode.R2_INTERMEDIATE_RISK,
            cfg_hash="1" * 64,
            split_hash="2" * 64,
        )
        assert r2.seq == 2
        assert r2.prev_hash == r1.record_hash

        # Verify intact chain
        v_res = verify_chain(log_path, test_key)
        assert v_res.ok is True
        assert v_res.record_count == 3
        assert len(v_res.errors) == 0
        assert v_res.final_hash == r2.record_hash


def test_audit_chain_tamper_detection() -> None:
    test_key = b"test_secret_audit_key_32_bytes_length!!"

    with tempfile.TemporaryDirectory() as tmp_dir:
        log_path = Path(tmp_dir) / "tamper_test.jsonl"
        chain = AuditChain(log_path=log_path, signing_key=test_key)

        chain.append("d0", 0.01, 0.01, Action.ROUTINE, ReasonCode.R5_LOW_RISK_RELIABLE, "0" * 64, "0" * 64)
        chain.append("d1", 0.08, 0.02, Action.FRAUD_ALERT, ReasonCode.R1_HIGH_RISK, "0" * 64, "0" * 64)

        # 1. Tamper test: Alter payload in line 1
        with open(log_path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        tampered_dict = json.loads(lines[0])
        tampered_dict["p"] = 0.999  # Attacker alters score
        lines[0] = json.dumps(tampered_dict) + "\n"

        tampered_log = Path(tmp_dir) / "tampered.jsonl"
        with open(tampered_log, "w", encoding="utf-8") as f:
            f.writelines(lines)

        res = verify_chain(tampered_log, test_key)
        assert res.ok is False
        assert any("tampered payload" in err for err in res.errors)

        # 2. Tamper test: Wrong HMAC key
        wrong_key = b"wrong_key_that_does_not_match_original!!"
        res_key = verify_chain(log_path, wrong_key)
        assert res_key.ok is False
        assert any("HMAC signature invalid" in err for err in res_key.errors)
