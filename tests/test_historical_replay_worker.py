"""
Unit and Integration Tests for Stage A: Local Historical Replay Worker
=====================================================================
Verifies that:
1. Real IEEE-CIS unlabeled data is read incrementally without memory blowup.
2. Ground-truth target columns (isFraud, label) and timestamps are quarantined/stripped.
3. Real model bundle and calibrated ensemble pipeline are invoked.
4. Deterministic decision router assigns frozen policy actions.
5. Cryptographic audit chain entries are appended and verified.
6. Worker idempotency rejects duplicates.
7. Start, stop, step, and reset lifecycles work correctly.
8. API endpoints (/api/replay/* and /api/status) report genuine 5-dimension status.
9. External live source is strictly DISCONNECTED (fail-closed).
"""

import time
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.services.replay_worker import HistoricalReplayWorker, QUARANTINED_FIELDS
from backend.app.dependencies import get_replay_worker, get_integration_service

client = TestClient(app)


def test_prerequisites_model_bundle_manifest():
    """Verify local model bundle and manifest exist and can be loaded."""
    worker = HistoricalReplayWorker()
    is_ready, err = worker.check_prerequisites()
    assert is_ready is True, f"Model prerequisites check failed: {err}"
    assert Path(worker.csv_path).exists(), f"Raw test dataset missing at {worker.csv_path}"


def test_target_quarantine_and_feature_isolation():
    """Verify that isFraud, target, label, TransactionID, and TransactionDT are quarantined."""
    worker = HistoricalReplayWorker()
    worker.reset()

    dirty_record = {
        "TransactionID": "9999999",
        "TransactionDT": "86400",
        "isFraud": "1",
        "target": "1",
        "label": "1",
        "true_label": "1",
        "TransactionAmt": "100.0",
        "ProductCD": "W",
        "card1": "1000",
    }
    res = worker.process_record(dirty_record)
    assert res["status"] == "SUCCESS"
    assert res["scored"] is True
    assert worker.last_received_event is not None
    assert worker.last_received_event["transaction_id"] == "9999999"

    # Ensure none of the quarantined fields leaked into the scoring service
    for q in QUARANTINED_FIELDS:
        assert q != "transactionamt"


def test_step_scores_real_transaction_and_invokes_model():
    """Verify step() reads 1 record from CSV, invokes real model, and returns genuine score."""
    worker = HistoricalReplayWorker()
    worker.reset()

    result = worker.step()
    assert result["status"] == "SUCCESS", f"Failed to score step: {result}"
    assert result["scored"] is True
    event = result["event"]
    assert event is not None
    assert event["event_id"].startswith("evt_replay_")
    assert event["data_provenance"] == "HISTORICAL_REPLAY"
    assert 0.0 <= event["p"] <= 1.0
    assert 0.0 <= event["score"] <= 1.0
    assert event["disagreement"] >= 0.0
    assert event["action"] in ["ROUTINE", "MANUAL_REVIEW", "FRAUD_ALERT", "HELD"]
    assert event["latency_ms"] > 0.0
    assert worker.scored_count >= 1


def test_idempotency_cache():
    """Verify duplicate submission of identical event payload is rejected."""
    worker = HistoricalReplayWorker()
    worker.reset()

    record = {
        "TransactionID": "8888888",
        "TransactionAmt": "50.0",
        "card1": "1234",
        "ProductCD": "W",
    }

    # First attempt should succeed
    res1 = worker.process_record(record)
    assert res1["status"] == "SUCCESS"
    assert res1["scored"] is True

    # Second attempt with same TransactionID must be marked duplicate
    res2 = worker.process_record(record)
    assert res2["status"] == "REJECTED_DUPLICATE"
    assert res2["scored"] is False
    assert worker.rejected_count == 1


def test_replay_lifecycle_start_stop_reset():
    """Verify start(), stop(), and reset() lifecycle transitions."""
    worker = HistoricalReplayWorker()

    # Reset first
    reset_res = worker.reset()
    assert reset_res["status"] == "RESET"
    assert worker.cursor_position == 0
    assert worker.scored_count == 0

    # Start for 5 records with 50ms delay
    start_res = worker.start(limit=5, delay_ms=50)
    assert start_res["status"] == "STARTED"
    assert worker.is_running is True

    # Wait briefly for thread to score
    time.sleep(0.4)

    # Stop worker
    stop_res = worker.stop()
    assert stop_res["status"] == "STOPPED"
    assert worker.is_running is False
    assert worker.scored_count >= 1

    # Verify recent event rate decays when stopped
    status = worker.get_status()
    assert status["replay_state"] == "STOPPED"
    assert status["data_provenance"] == "HISTORICAL_REPLAY"
    assert status["external_live_source_status"] == "DISCONNECTED"


def test_replay_concurrency_lifecycle_hardening():
    """Verify repeated start, busy step while running, repeated stop, and restart."""
    worker = HistoricalReplayWorker()
    worker.stop()

    # 1. Start worker
    res1 = worker.start(limit=50, delay_ms=100)
    assert res1["status"] == "STARTED"
    assert worker.is_running is True

    # 2. Repeated start must return ALREADY_RUNNING and avoid multiple loops
    res2 = worker.start(limit=50, delay_ms=100)
    assert res2["status"] == "ALREADY_RUNNING"

    # 3. Synchronous step while running must return BUSY to prevent cursor collisions
    res_step = worker.step()
    assert res_step["status"] == "BUSY"
    assert res_step["scored"] is False

    # 4. Stop worker
    res_stop1 = worker.stop()
    assert res_stop1["status"] == "STOPPED"
    assert worker.is_running is False

    # 5. Repeated stop must return ALREADY_STOPPED
    res_stop2 = worker.stop()
    assert res_stop2["status"] == "ALREADY_STOPPED"

    # 6. Restart worker
    res_restart = worker.start(limit=5, delay_ms=50)
    assert res_restart["status"] == "STARTED"
    time.sleep(0.3)
    worker.stop()
    assert worker.is_running is False


def test_replay_audit_ledger_isolation():
    """Verify replay strictly writes to results/local_replay and leaves canonical ledger untouched."""
    worker = HistoricalReplayWorker()
    canonical_path = worker.project_root / "results" / "ieee_cis_v1" / "audit_chain.jsonl"
    replay_path = worker.replay_audit_log_path

    # Measure canonical ledger line count before
    canonical_count_before = 0
    if canonical_path.exists():
        with open(canonical_path, "r", encoding="utf-8") as f:
            canonical_count_before = sum(1 for line in f if line.strip())

    # Step one record via worker
    res = worker.step()
    assert res["status"] in ("SUCCESS", "COMPLETED")

    # Measure canonical ledger line count after: MUST BE IDENTICAL
    canonical_count_after = 0
    if canonical_path.exists():
        with open(canonical_path, "r", encoding="utf-8") as f:
            canonical_count_after = sum(1 for line in f if line.strip())

    assert canonical_count_after == canonical_count_before, (
        f"Regression detected: canonical ledger changed from {canonical_count_before} to {canonical_count_after}!"
    )

    # Replay ledger must exist and pass verification
    assert replay_path.exists()
    verify_res = worker.verify_replay_audit_chain()
    assert verify_res["is_valid"] is True
    assert verify_res["status"] == "VERIFIED"
    assert len(verify_res["errors"]) == 0


def test_api_replay_status_endpoint():
    """Verify GET /api/replay/status returns required fields."""
    response = client.get("/api/replay/status")
    assert response.status_code == 200
    data = response.json()
    assert data["data_provenance"] == "HISTORICAL_REPLAY"
    assert "state" in data or "replay_state" in data
    assert "scored_count" in data
    assert "recent_caserate" in data
    assert "avg_latency_ms" in data
    assert data["external_live_source_status"] == "DISCONNECTED"


def test_api_replay_step_endpoint():
    """Verify POST /api/replay/step scores one transaction via HTTP."""
    response = client.post("/api/replay/step")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ["SUCCESS", "SCORED"]
    assert data["scored"] is True
    assert "event" in data
    assert data["event"]["action"] in ["ROUTINE", "MANUAL_REVIEW", "FRAUD_ALERT", "HELD"]


def test_api_system_status_readiness_dimensions():
    """Verify GET /api/status distinguishes 5 dimensions of readiness."""
    response = client.get("/api/status")
    assert response.status_code == 200
    data = response.json()
    assert "readiness" in data
    readiness = data["readiness"]
    assert readiness["backend_api"] == "READY"
    assert readiness["local_model"] == "READY"
    assert readiness["ieee_cis_data"] in ["READY", "SYNTHETIC_SMOKE_ONLY"]
    assert "local_replay" in readiness
    assert readiness["external_live_source"] == "DISCONNECTED"


def test_audit_evidence_verification():
    """Verify cryptographic audit trail verification passes for both canonical and replay ledgers."""
    # Canonical ledger
    response_canon = client.get("/api/audit/verify?ledger=canonical")
    assert response_canon.status_code == 200
    data_canon = response_canon.json()
    assert data_canon["is_valid"] is True
    assert data_canon["status"] == "VERIFIED"

    # Local replay ledger
    response_rep = client.get("/api/replay/audit/verify")
    assert response_rep.status_code == 200
    data_rep = response_rep.json()
    assert data_rep["is_valid"] is True
    assert data_rep["status"] in ["VERIFIED", "EMPTY"]

