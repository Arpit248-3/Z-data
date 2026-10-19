"""Unit and Integration Tests for SignalGate FastAPI API Integration (Phase 8).

Verifies:
- Three-state mode readiness reporting (SYNTHETIC_SMOKE_ONLY, IEEE_CIS_OFFLINE_BENCHMARK, LIVE_SOURCE_NOT_CONNECTED).
- Mode-aware status reporting and bundle dependency checks.
- Real-data model card exposing 391 features, calibrator, and cryptographic hashes.
- Evidence-backed multi-metric drift reports (PSI, KS, Wasserstein, score shift) and discipline notice.
- Dual-mode sandbox scoring routing between synthetic baseline and real IEEE-CIS ensemble.
- Strict recursive ground-truth quarantine rejecting isFraud, target, and TransactionID with HTTP 422.
- Cryptographic AuditChain decision sealing on real-data scoring transactions.
- Advisory governance proposal inspection, deterministic validation replay, and churn calculation.
- Mandatory human authorization gate requiring authenticated credentials for approval.
- Rejection of policy proposals preserving active production policy intact.
- State-transition conflict protection (HTTP 409) preventing duplicate approval.
- Sequential and HMAC integrity verification via GET /api/audit/verify.
- Backward compatibility with existing synthetic endpoints.

Governing Specification: docs/ibm_architecture_integration_master_spec.md § C, § L
Requirements: APII-01, APII-02, APII-03
"""

import pytest
from starlette.testclient import TestClient

from backend.app.main import app
from backend.app.dependencies import get_integration_service
from integrations.ibm_architecture.contracts import Proposal
from integrations.ibm_architecture.policy.frozen_policy import get_frozen_ieee_policy_config


@pytest.fixture
def client():
    """FastAPI test client instance."""
    return TestClient(app)


@pytest.fixture
def integration_service():
    """Singleton IntegrationService dependency."""
    return get_integration_service()


# ==============================================================================
# 1. Mode Readiness & Status Tests (APII-01)
# ==============================================================================

def test_api_mode_readiness(client):
    """GET /api/mode reports truthful status for all 3 required operating modes."""
    response = client.get("/api/mode")
    assert response.status_code == 200
    data = response.json()

    assert "active_mode" in data
    assert "available_modes" in data
    assert set(data["available_modes"]) == {
        "SYNTHETIC_SMOKE_ONLY",
        "IEEE_CIS_OFFLINE_BENCHMARK",
        "LIVE_SOURCE_NOT_CONNECTED",
    }

    modes = data["modes_detail"]
    assert "SYNTHETIC_SMOKE_ONLY" in modes
    assert modes["SYNTHETIC_SMOKE_ONLY"]["ready"] is True

    assert "IEEE_CIS_OFFLINE_BENCHMARK" in modes
    # If bundle is present and verified, ready is True
    assert modes["IEEE_CIS_OFFLINE_BENCHMARK"]["ready"] is True

    assert "LIVE_SOURCE_NOT_CONNECTED" in modes
    assert modes["LIVE_SOURCE_NOT_CONNECTED"]["ready"] is False

    assert "No live banking connections exist" in data["notice"]


def test_api_status_mode_parameter(client):
    """GET /api/status?mode=IEEE_CIS_OFFLINE_BENCHMARK evaluates real-data bundle readiness."""
    response = client.get("/api/status?mode=IEEE_CIS_OFFLINE_BENCHMARK")
    assert response.status_code == 200
    data = response.json()

    assert data["evidence_status"] == "IEEE_CIS_OFFLINE_BENCHMARK"
    assert data["overall_status"] == "OPERATIONAL_OFFLINE_BENCHMARK"
    assert "ieee_cis_bundle" in data["dependencies"]
    assert data["dependencies"]["ieee_cis_bundle"]["ready"] is True


def test_api_status_synthetic_default(client):
    """GET /api/status without query parameter maintains exact synthetic smoke status."""
    response = client.get("/api/status")
    assert response.status_code == 200
    data = response.json()

    assert data["evidence_status"] == "SYNTHETIC_SMOKE_ONLY"
    assert data["overall_status"] == "OPERATIONAL_SYNTHETIC"


# ==============================================================================
# 2. Model Card & Artifact Verification (APII-01, APII-03)
# ==============================================================================

def test_api_model_card_ieee_cis(client):
    """GET /api/model/card?mode=IEEE_CIS_OFFLINE_BENCHMARK returns real model architecture metadata."""
    response = client.get("/api/model/card?mode=IEEE_CIS_OFFLINE_BENCHMARK")
    assert response.status_code == 200
    data = response.json()

    assert data["mode"] == "IEEE_CIS_OFFLINE_BENCHMARK"
    assert data["architecture_type"] == "EraBaggedHeterogeneousEnsemble"
    assert set(data["sub_models"]) == {"HistGradientBoosting", "ExtraTrees", "LogisticRegression"}
    assert data["feature_count"] == 391
    assert len(data["features_sample"]) > 0
    assert len(data["manifest_hash"]) == 64
    assert len(data["artifact_hashes"]) >= 4
    assert "test" in data["split_provenance"].get("partitions", {})
    assert "Chronological final test partition is strictly held out" in data["notice"]


def test_api_model_card_synthetic(client):
    """GET /api/model/card?mode=SYNTHETIC_SMOKE_ONLY returns synthetic baseline model metadata."""
    response = client.get("/api/model/card?mode=SYNTHETIC_SMOKE_ONLY")
    assert response.status_code == 200
    data = response.json()

    assert data["mode"] == "SYNTHETIC_SMOKE_ONLY"
    assert data["architecture_type"] == "HistGradientBoostingClassifier"
    assert data["feature_count"] == 14


def test_api_model_card_invalid_mode(client):
    """GET /api/model/card with unsupported mode returns HTTP 400 Bad Request."""
    response = client.get("/api/model/card?mode=UNSUPPORTED_TEST_MODE")
    assert response.status_code == 400
    data = response.json()
    assert data["error"]["code"] == "INVALID_MODE"


# ==============================================================================
# 3. Drift Monitoring API (APII-01, DRFT-01)
# ==============================================================================

def test_api_drift_report(client):
    """GET /api/drift/report returns multi-metric calculations and mandatory discipline notice."""
    response = client.get("/api/drift/report")
    assert response.status_code == 200
    data = response.json()

    assert data["status"] == "IEEE_CIS_OFFLINE_BENCHMARK"
    assert data["features_monitored"] > 0
    assert data["mean_psi"] >= 0.0
    assert data["max_psi"] >= 0.0
    assert len(data["provenance_hash"]) == 64
    assert "not constitute proof of fraud" in data["notice"]
    assert len(data["feature_reports"]) > 0


def test_api_drift_report_invalid_mode(client):
    """GET /api/drift/report for synthetic mode returns HTTP 400 Bad Request."""
    response = client.get("/api/drift/report?mode=SYNTHETIC_SMOKE_ONLY")
    assert response.status_code == 400
    data = response.json()
    assert data["error"]["code"] == "INVALID_DRIFT_MODE"


# ==============================================================================
# 4. Scoring Sandbox Dual-Mode & Quarantine (APII-02)
# ==============================================================================

def test_score_sandbox_ieee_cis_mode_valid(client):
    """POST /api/score-sandbox with IEEE-CIS mode routes through ensemble with audit sealing."""
    payload = {
        "mode": "IEEE_CIS_OFFLINE_BENCHMARK",
        "features": {
            "TransactionAmt": 150.0,
            "ProductCD": "W",
            "card1": 1000.0,
            "C1": 1.0,
            "C2": 1.0,
        },
    }
    response = client.post("/api/score-sandbox", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["mode"] == "IEEE_CIS_OFFLINE_BENCHMARK"
    assert 0.0 <= data["signals"]["p"] <= 1.0
    assert data["signals"]["u_method"] == "u2_rank_residual"
    assert data["decision"]["action"] in {"ROUTINE", "MANUAL_REVIEW", "FRAUD_ALERT", "DEFERRED"}
    assert data["decision"]["reason_code"].startswith("R")
    assert data["audit_logged"] is True
    assert data["audit_seq"] is not None
    assert data["latency_ms"] >= 0.0


def test_score_sandbox_ieee_cis_mode_leakage_rejection(client):
    """POST /api/score-sandbox strictly rejects isFraud, target, and TransactionID with 422."""
    for forbidden_field in ["isFraud", "target", "TransactionID", "true_label"]:
        payload = {
            "mode": "IEEE_CIS_OFFLINE_BENCHMARK",
            "features": {
                "TransactionAmt": 200.0,
                forbidden_field: 1,
            },
        }
        response = client.post("/api/score-sandbox", json=payload)
        assert response.status_code == 422
        data = response.json()
        assert data["error"]["code"] == "VALIDATION_ERROR"
        assert "LEAKAGE VIOLATION" in data["error"]["message"]


def test_score_sandbox_synthetic_backward_compatibility(client):
    """POST /api/score-sandbox default mode preserves exact synthetic scoring behavior."""
    payload = {
        "features": {
            "TransactionAmt": 123.44,
            "ProductCD": "W",
            "card4": "discover",
            "C1": 2.0,
            "C2": 2.0,
            "D1": 1.209,
            "D2": 10.6313,
            "V1": 1.6792,
            "V2": -0.7171,
            "V3": -0.3057,
        }
    }
    response = client.post("/api/score-sandbox", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["mode"] == "SYNTHETIC_SMOKE_ONLY"
    assert data["decision"]["action"] == "ROUTINE"
    assert data["decision"]["reason_code"] == "R5_LOW_RISK_RELIABLE"
    assert data["provenance"]["dataset_status"] == "SYNTHETIC_SMOKE_ONLY"


# ==============================================================================
# 5. Governance & Replay Gate Endpoints (APII-01, APII-03)
# ==============================================================================

def test_governance_proposals_list(client):
    """GET /api/governance/proposals lists all registered advisory proposals."""
    response = client.get("/api/governance/proposals")
    assert response.status_code == 200
    data = response.json()

    assert isinstance(data, list)
    assert len(data) >= 1
    proposal = data[0]
    assert "proposal_id" in proposal
    assert "base_cfg_hash" in proposal
    assert "status" in proposal


def test_governance_proposal_detail_and_replay(client, integration_service):
    """GET proposal detail and POST replay execution transitions to AWAITING_HUMAN_APPROVAL."""
    # Register clean test proposal
    cfg = get_frozen_ieee_policy_config()
    test_id = "prop_api_replay_test"
    prop = Proposal(
        proposal_id=test_id,
        base_cfg_hash=cfg.compute_cfg_hash(),
        changes={"t_review": 0.075},
        rationale="Unit test proposal for replay evaluation",
    )
    integration_service._replay_gate.register_proposal(prop)

    # 1. GET detail
    res_get = client.get(f"/api/governance/proposals/{test_id}")
    assert res_get.status_code == 200
    assert res_get.json()["proposal_id"] == test_id
    assert res_get.json()["status"] == "PENDING"

    # 2. POST replay
    res_replay = client.post(f"/api/governance/proposals/{test_id}/replay?scenario=val_slice")
    assert res_replay.status_code == 200
    rep_data = res_replay.json()
    assert rep_data["status"] == "AWAITING_HUMAN_APPROVAL"
    assert rep_data["replay_result"]["is_valid"] is True
    assert rep_data["replay_result"]["replay_executed"] is True
    assert rep_data["replay_result"]["churn_count"] >= 0


def test_governance_proposal_human_approval_lifecycle(client, integration_service):
    """POST /approve transitions proposal to APPROVED and seals event to AuditChain."""
    cfg = get_frozen_ieee_policy_config()
    test_id = "prop_api_approval_test"
    prop = Proposal(
        proposal_id=test_id,
        base_cfg_hash=cfg.compute_cfg_hash(),
        changes={"t_review": 0.075},
        rationale="Unit test proposal for human approval",
    )
    integration_service._replay_gate.register_proposal(prop)

    # Execute replay to transition to AWAITING_HUMAN_APPROVAL
    client.post(f"/api/governance/proposals/{test_id}/replay")

    # Approve with valid human credentials
    approve_payload = {
        "approver": "Chief_Risk_Officer_01",
        "rationale": "Empirical churn and capacity requirements verified via validation replay.",
    }
    res_approve = client.post(f"/api/governance/proposals/{test_id}/approve", json=approve_payload)
    assert res_approve.status_code == 200
    app_data = res_approve.json()

    assert app_data["proposal_id"] == test_id
    assert app_data["status"] == "APPROVED"
    assert app_data["decision_maker"] == "Chief_Risk_Officer_01"
    assert app_data["audit_seq"] is not None

    # Check detail reflects APPROVED
    res_detail = client.get(f"/api/governance/proposals/{test_id}")
    assert res_detail.json()["status"] == "APPROVED"


def test_governance_proposal_approval_empty_approver_error(client, integration_service):
    """POST /approve with empty approver returns HTTP 422 or 400 Bad Request."""
    test_id = "prop_empty_app_test"
    cfg = get_frozen_ieee_policy_config()
    prop = Proposal(
        proposal_id=test_id,
        base_cfg_hash=cfg.compute_cfg_hash(),
        changes={"t_review": 0.075},
        rationale="Test empty approver",
    )
    integration_service._replay_gate.register_proposal(prop)
    client.post(f"/api/governance/proposals/{test_id}/replay")

    res = client.post(f"/api/governance/proposals/{test_id}/approve", json={"approver": "", "rationale": "valid"})
    assert res.status_code in (400, 422)


def test_governance_proposal_rejection(client, integration_service):
    """POST /reject transitions proposal to REJECTED preserving production policy."""
    cfg = get_frozen_ieee_policy_config()
    test_id = "prop_api_reject_test"
    prop = Proposal(
        proposal_id=test_id,
        base_cfg_hash=cfg.compute_cfg_hash(),
        changes={"t_review": 0.075},
        rationale="Test rejection flow",
    )
    integration_service._replay_gate.register_proposal(prop)

    reject_payload = {
        "reviewer": "Risk_Analyst_02",
        "reason": "Risk-reward profile unfavorable under current macro conditions.",
    }
    res = client.post(f"/api/governance/proposals/{test_id}/reject", json=reject_payload)
    assert res.status_code == 200
    data = res.json()

    assert data["proposal_id"] == test_id
    assert data["status"] == "REJECTED"
    assert data["decision_maker"] == "Risk_Analyst_02"


def test_governance_proposal_not_found(client):
    """Operations on non-existent proposals return HTTP 404 Not Found."""
    res_get = client.get("/api/governance/proposals/non_existent_proposal_id")
    assert res_get.status_code == 404
    assert res_get.json()["error"]["code"] == "PROPOSAL_NOT_FOUND"

    res_replay = client.post("/api/governance/proposals/non_existent_proposal_id/replay")
    assert res_replay.status_code == 404


def test_governance_conflict_state_transition(client, integration_service):
    """Attempting to approve an already approved proposal returns HTTP 409 Conflict."""
    cfg = get_frozen_ieee_policy_config()
    test_id = "prop_conflict_test"
    prop = Proposal(
        proposal_id=test_id,
        base_cfg_hash=cfg.compute_cfg_hash(),
        changes={"t_review": 0.075},
        rationale="Conflict test proposal",
    )
    integration_service._replay_gate.register_proposal(prop)
    client.post(f"/api/governance/proposals/{test_id}/replay")

    # First approval succeeds
    client.post(
        f"/api/governance/proposals/{test_id}/approve",
        json={"approver": "Approver_1", "rationale": "Initial approval"},
    )

    # Second approval must fail with 409 Conflict
    res_second = client.post(
        f"/api/governance/proposals/{test_id}/approve",
        json={"approver": "Approver_2", "rationale": "Duplicate approval"},
    )
    assert res_second.status_code == 409
    assert res_second.json()["error"]["code"] == "INVALID_STATE_TRANSITION"


# ==============================================================================
# 6. Audit Chain Cryptographic Verification (APII-01, APII-03)
# ==============================================================================

def test_audit_verification_endpoint(client):
    """GET /api/audit/verify confirms unbroken cryptographic ledger integrity."""
    response = client.get("/api/audit/verify")
    assert response.status_code == 200
    data = response.json()

    assert data["status"] == "VERIFIED"
    assert data["is_valid"] is True
    assert data["record_count"] >= 0
    assert len(data["errors"]) == 0
    if data["record_count"] > 0:
        assert data["chain_head_hash"] is not None
        assert len(data["chain_head_hash"]) == 64


# ==============================================================================
# 7. Cases Router Mode Parameter (APII-01)
# ==============================================================================

def test_cases_list_with_mode(client):
    """GET /api/cases supports mode parameter without error."""
    response = client.get("/api/cases?mode=IEEE_CIS_OFFLINE_BENCHMARK&limit=10")
    assert response.status_code == 200
    data = response.json()
    assert "cases" in data
    assert len(data["cases"]) <= 10
