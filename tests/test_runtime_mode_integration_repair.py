"""Integration tests for SignalGate Runtime Mode & Evidence Integration Repairs.

Verifies:
1. Chronological IEEE-CIS replay streaming via GET /api/replay/rows?mode=IEEE_CIS_OFFLINE_BENCHMARK.
2. Audit trail latency measurement and cryptographic verification.
3. Baseline policy comparison suite in offline benchmark mode.
4. Mode-aware consolidated results and scenarios routing.
"""

from datetime import datetime, timezone
import pytest
from starlette.testclient import TestClient

from backend.app.main import app
from integrations.ibm_architecture.contracts import Action, AuditRecord, ReasonCode


@pytest.fixture
def client():
    return TestClient(app)


def test_ieee_cis_replay_rows_streaming(client):
    """GET /api/replay/rows in IEEE-CIS mode returns authentic transaction stream."""
    response = client.get("/api/replay/rows?mode=IEEE_CIS_OFFLINE_BENCHMARK")
    assert response.status_code == 200
    data = response.json()

    assert data["status"] == "IEEE_CIS_OFFLINE_BENCHMARK"
    assert data["total_rows"] >= 120
    rows = data["rows"]
    assert len(rows) == 100  # Default pagination limit

    # Ensure transaction IDs and amounts are authentic IEEE-CIS format
    first_row = rows[0]
    assert len(str(first_row["transaction_id"])) > 0
    assert first_row["amount"] > 0
    assert 0.0 <= first_row["p"] <= 1.0
    assert first_row["action"] in ("ROUTINE", "MANUAL_REVIEW", "FRAUD_ALERT")


def test_audit_trail_has_latency_and_verifies(client):
    """GET /api/audit contains measured latency and passes cryptographic verification."""
    # First verify the cryptographic audit chain integrity
    verify_res = client.get("/api/audit/verify")
    assert verify_res.status_code == 200
    verify_data = verify_res.json()
    assert verify_data["is_valid"] is True
    assert verify_data["record_count"] >= 100

    # Next fetch audit trail rows
    trail_res = client.get("/api/audit?limit=25&mode=IEEE_CIS_OFFLINE_BENCHMARK")
    assert trail_res.status_code == 200
    trail_data = trail_res.json()
    assert trail_data["total_records"] >= 100

    records = trail_data["records"]
    assert len(records) > 0
    # Check that latency_ms is present and realistic
    latencies = [r.get("latency_ms") for r in records if r.get("latency_ms") is not None]
    assert len(latencies) > 0
    for lat in latencies:
        assert isinstance(lat, (int, float))
        assert 1.0 <= lat <= 200.0


def test_ieee_cis_policy_comparison_baseline_suite(client):
    """GET /api/policies/compare returns complete baseline suite under IEEE-CIS mode."""
    response = client.get("/api/policies/compare?mode=IEEE_CIS_OFFLINE_BENCHMARK")
    assert response.status_code == 200
    data = response.json()

    assert "policies" in data
    policies = data["policies"]
    policy_names = [p["policy"] for p in policies]

    # Full baseline suite must be present
    assert "B1_fixed_threshold" in policy_names
    assert "B2_top_b_risk" in policy_names
    assert "B3a_confidence_deferral" in policy_names
    assert "B4_random_control" in policy_names
    assert "SignalGate_candidate" in policy_names


def test_ieee_cis_consolidated_results(client):
    """GET /api/results in IEEE-CIS mode returns authentic benchmark results."""
    response = client.get("/api/results?mode=IEEE_CIS_OFFLINE_BENCHMARK")
    assert response.status_code == 200
    data = response.json()

    assert data["test_partition_summary"]["total_transactions"] == 118108
    assert "shift_scenarios" in data
    s0 = data["shift_scenarios"]["S0_nominal"]
    assert s0["signalgate_recall"] > 0.40  # ~0.5086


def test_ieee_cis_scenarios(client):
    """GET /api/scenarios in IEEE-CIS mode returns S0-S3 authentic scenarios."""
    response = client.get("/api/scenarios?mode=IEEE_CIS_OFFLINE_BENCHMARK")
    assert response.status_code == 200
    data = response.json()

    scenario_ids = [s["scenario_id"] for s in data["scenarios"]]
    assert "S0" in scenario_ids
    assert "S1" in scenario_ids
    assert "S2" in scenario_ids
    assert "S3" in scenario_ids


def test_audit_record_canonical_hashing_with_latency():
    """AuditRecord latency_ms field must not disrupt canonical record hash determinism."""
    now = datetime(2026, 3, 1, 0, 0, 0, tzinfo=timezone.utc)
    dummy_hash = "a" * 64
    rec1 = AuditRecord(
        id="rec_test_001",
        seq=1,
        timestamp=now,
        p=0.075,
        u=0.53,
        u2=0.53,
        action="MANUAL_REVIEW",
        reason="R2_INTERMEDIATE_RISK",
        cfg_hash=dummy_hash,
        split_hash=dummy_hash,
        latency_ms=23.45,
    )
    rec2 = AuditRecord(
        id="rec_test_001",
        seq=1,
        timestamp=now,
        p=0.075,
        u=0.53,
        u2=0.53,
        action="MANUAL_REVIEW",
        reason="R2_INTERMEDIATE_RISK",
        cfg_hash=dummy_hash,
        split_hash=dummy_hash,
        latency_ms=None,
    )
    # Canonical record hash only hashes invariant core governance fields
    assert rec1.compute_record_hash() == rec2.compute_record_hash()
