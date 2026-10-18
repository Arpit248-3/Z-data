"""Integration tests for Phase 8: FastAPI Integration and Explicit Operating Mode Telemetry.

Verifies:
1. /api/modes provides verified access to mode readiness (SYNTHETIC_SMOKE_ONLY active,
   IEEE_CIS_OFFLINE_BENCHMARK deferred, LIVE_SOURCE_NOT_CONNECTED disconnected).
2. Mode selection fails closed without silent fallback.
3. Scoring sandbox enforces recursive quarantine, records audit log, and reports explicit provenance.
4. Governance endpoints expose drift reports, advisory proposals, Replay Gate validation,
   human sign-off lifecycle, and cryptographic audit chain verification.
"""

from fastapi.testclient import TestClient
import pytest

from backend.app.main import app

client = TestClient(app)


def test_api_modes_overview() -> None:
    """Verify /api/modes returns explicit readiness across all 3 evidence modes."""
    response = client.get("/api/modes")
    assert response.status_code == 200
    data = response.json()

    assert data["active_mode"] == "SYNTHETIC_SMOKE_ONLY"
    assert len(data["supported_modes"]) == 3

    modes_map = {m["mode"]: m for m in data["supported_modes"]}

    # 1. Synthetic smoke mode is active and available
    assert modes_map["SYNTHETIC_SMOKE_ONLY"]["available"] is True
    assert modes_map["SYNTHETIC_SMOKE_ONLY"]["active"] is True
    assert modes_map["SYNTHETIC_SMOKE_ONLY"]["status"] == "READY"

    # 2. IEEE-CIS mode is deferred and unavailable on 8GB host
    assert modes_map["IEEE_CIS_OFFLINE_BENCHMARK"]["available"] is False
    assert modes_map["IEEE_CIS_OFFLINE_BENCHMARK"]["active"] is False
    assert modes_map["IEEE_CIS_OFFLINE_BENCHMARK"]["status"] == "UNAVAILABLE_MISSING_CHECKPOINTS"
    assert modes_map["IEEE_CIS_OFFLINE_BENCHMARK"]["diagnostics"]["real_data_training_status"] == "DEFERRED"
    assert "8 GB RAM" in str(modes_map["IEEE_CIS_OFFLINE_BENCHMARK"]["diagnostics"])

    # 3. Live source mode is disconnected
    assert modes_map["LIVE_SOURCE_NOT_CONNECTED"]["available"] is False
    assert modes_map["LIVE_SOURCE_NOT_CONNECTED"]["status"] == "NOT_CONNECTED"


def test_api_mode_detail_and_unknown() -> None:
    """Verify single mode detail retrieval and 404 for unknown modes."""
    res_ok = client.get("/api/modes/SYNTHETIC_SMOKE_ONLY")
    assert res_ok.status_code == 200
    assert res_ok.json()["mode"] == "SYNTHETIC_SMOKE_ONLY"

    res_ieee = client.get("/api/modes/IEEE_CIS_OFFLINE_BENCHMARK")
    assert res_ieee.status_code == 200
    assert res_ieee.json()["status"] == "UNAVAILABLE_MISSING_CHECKPOINTS"
    assert res_ieee.json()["diagnostics"]["real_data_training_status"] == "DEFERRED"

    res_unknown = client.get("/api/modes/NON_EXISTENT_MODE")
    assert res_unknown.status_code == 404
    assert res_unknown.json()["error"]["code"] == "UNKNOWN_MODE"


def test_api_mode_select_fail_closed() -> None:
    """Verify mode switching fails closed for unavailable modes without silent fallback."""
    # Active mode selection succeeds
    res_synth = client.post("/api/modes/select", json={"mode": "SYNTHETIC_SMOKE_ONLY"})
    assert res_synth.status_code == 200
    assert res_synth.json()["active_mode"] == "SYNTHETIC_SMOKE_ONLY"

    # Deferred real-data mode selection fails closed (HTTP 409 Conflict)
    res_ieee = client.post("/api/modes/select", json={"mode": "IEEE_CIS_OFFLINE_BENCHMARK"})
    assert res_ieee.status_code == 409
    err = res_ieee.json()["error"]
    assert err["code"] == "MODE_UNAVAILABLE"
    assert err["details"]["status"] == "UNAVAILABLE_MISSING_CHECKPOINTS"
    assert err["details"]["diagnostics"]["real_data_training_status"] == "DEFERRED"

    # Disconnected live source mode selection fails closed
    res_live = client.post("/api/modes/select", json={"mode": "LIVE_SOURCE_NOT_CONNECTED"})
    assert res_live.status_code == 409
    assert res_live.json()["error"]["code"] == "MODE_UNAVAILABLE"


def test_api_scoring_sandbox_provenance_and_audit() -> None:
    """Verify scoring sandbox returns explicit synthetic provenance and deferred real benchmark status."""
    payload = {
        "features": {
            "TransactionAmt": 150.0,
            "card1": 5000.0,
            "dist1": 15.0,
            "C1": 3.0,
        }
    }
    response = client.post("/api/score-sandbox", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["audit_logged"] is True
    assert data["provenance"]["dataset_status"] == "SYNTHETIC_SMOKE_ONLY"
    assert data["provenance"]["source_mode"] == "SYNTHETIC_SMOKE_ONLY"
    assert data["provenance"]["real_data_benchmark_status"] == "DEFERRED"
    assert data["decision"]["action"] in ("ROUTINE", "FRAUD_ALERT", "MANUAL_REVIEW", "HELD", "DEFERRED")


def test_api_governance_drift_and_sentinel_proposal() -> None:
    """Verify drift analysis endpoint and Drift Sentinel advisory proposal generation."""
    # 1. Query drift on S1 Covariate Shift scenario
    res_drift = client.get("/api/governance/drift?scenario=S1")
    assert res_drift.status_code == 200
    drift_data = res_drift.json()
    assert drift_data["scenario_id"] == "S1"
    assert drift_data["status"] == "SYNTHETIC_SMOKE_ONLY"
    assert drift_data["real_data_benchmark_status"] == "DEFERRED"
    assert drift_data["overall_drift_detected"] is True

    # 2. Feed drift summary to Drift Sentinel
    res_prop = client.post("/api/governance/drift/propose", json=drift_data)
    assert res_prop.status_code == 200
    prop_data = res_prop.json()
    assert prop_data is not None
    assert "budget.primary_multiple" in prop_data["changes"]


def test_api_governance_replay_gate_workflow() -> None:
    """Verify Replay Gate proposal validation and human sign-off lifecycle."""
    validate_payload = {
        "proposal_id": "api_test_prop_01",
        "base_cfg_hash": "8d3f02ca492ca94bab45f3ceac8d39432c2f29f40d54e7990b4aa78cbbff6240",
        "changes": {"budget.primary_multiple": 2.0},
        "rationale": "Compensate for S1 covariate shift with 2.0x capacity",
    }

    # 1. Validate and replay proposal -> leaves in AWAITING_HUMAN_APPROVAL
    res_val = client.post("/api/governance/proposals/validate", json=validate_payload)
    assert res_val.status_code == 200
    val_data = res_val.json()
    assert val_data["status"] == "AWAITING_HUMAN_APPROVAL"
    assert val_data["validation_passed"] is True

    # 2. Check proposal history
    res_list = client.get("/api/governance/proposals")
    assert res_list.status_code == 200
    history = res_list.json()
    assert any(p["proposal_id"] == "api_test_prop_01" for p in history)

    # 3. Explicit human approval -> transitions to APPROVED_ACTIVE
    approve_payload = {
        "proposal_id": "api_test_prop_01",
        "approver": "ChiefRiskOfficer_Test",
    }
    res_app = client.post("/api/governance/proposals/approve", json=approve_payload)
    assert res_app.status_code == 200
    app_data = res_app.json()
    assert app_data["status"] == "APPROVED_ACTIVE"
    assert app_data["approved_by"] == "ChiefRiskOfficer_Test"


def test_api_governance_copilot_brief_and_quarantine() -> None:
    """Verify Case Copilot brief generation and quarantine enforcement."""
    valid_payload = {
        "record_id": "case_test_999",
        "p": 0.045,
        "u": 0.02,
        "u2": 0.05,
        "n": 5.0,
        "action": "ROUTINE",
        "reason": "R5_LOW_RISK_RELIABLE",
    }
    res_brief = client.post("/api/governance/copilot/brief", json=valid_payload)
    assert res_brief.status_code == 200
    brief_data = res_brief.json()
    assert brief_data["record_id"] == "case_test_999"
    assert len(brief_data["verified_statements"]) > 0
    assert brief_data["verified_claims"] > 0

    # Leakage check: passing forbidden field returns HTTP 400
    leaky_payload = dict(valid_payload)
    leaky_payload["isFraud"] = 1
    res_leak = client.post("/api/governance/copilot/brief", json=leaky_payload)
    assert res_leak.status_code == 400
    assert res_leak.json()["error"]["code"] == "QUARANTINE_VIOLATION"


def test_api_governance_audit_chain_verify() -> None:
    """Verify cryptographic audit chain verification endpoint."""
    res_chain = client.get("/api/governance/audit-chain/verify")
    assert res_chain.status_code == 200
    chain_data = res_chain.json()
    assert chain_data["verified"] is True
    assert chain_data["tamper_detected"] is False
    assert "HMAC-SHA256" in chain_data["details"]
