"""Tests for SignalGate Real-Time Scoring Sandbox API."""

import pytest
from starlette.testclient import TestClient

from backend.app.main import app

client = TestClient(app)


def test_score_sandbox_valid_features():
    payload = {
        "features": {
            "TransactionAmt": 125.50,
            "C1": 1.0,
            "C2": 1.0,
            "D1": 14.0,
            "D2": 14.0,
            "V1": 1.0,
            "V2": 1.0,
            "V3": 1.0,
        }
    }
    res = client.post("/api/score-sandbox", json=payload)
    assert res.status_code == 200
    data = res.json()

    # Core response fields
    assert "decision_id" in data
    assert "timestamp" in data
    assert data["audit_logged"] is True
    assert data["latency_ms"] >= 0.0

    # Signals
    sigs = data["signals"]
    assert 0.0 <= sigs["p"] <= 1.0
    assert sigs["u_method"] == "u2_rank_residual"
    assert sigs["novelty_status"] == "disabled"

    # Decision
    dec = data["decision"]
    assert dec["action"] in ["FRAUD_ALERT", "MANUAL_REVIEW", "ROUTINE"]
    assert dec["reason_code"] in [
        "R1_HIGH_RISK",
        "R2_INTERMEDIATE_RISK",
        "R3_MODEL_DISAGREEMENT",
        "R4_UNFAMILIAR_INPUT",
        "R5_LOW_RISK_RELIABLE",
        "R6_CAPACITY_DEFERRED",
    ]
    assert dec["config_hash"] == "8d3f02ca492ca94bab45f3ceac8d39432c2f29f40d54e7990b4aa78cbbff6240"

    # Governance
    gov = data["governor"]
    assert "governor_status" in gov
    assert "semantics" in gov


def test_score_sandbox_missing_features_handled():
    # Only supply a single feature: missing features must be filled with NaN without crashing
    payload = {
        "features": {
            "TransactionAmt": 5000.0,
        }
    }
    res = client.post("/api/score-sandbox", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert 0.0 <= data["signals"]["p"] <= 1.0


def test_score_sandbox_high_risk_never_routine():
    # Construct payload with extreme transaction amount
    payload = {
        "features": {
            "TransactionAmt": 45000.0,
            "C1": 100.0,
            "C2": 100.0,
        }
    }
    res = client.post("/api/score-sandbox", json=payload)
    assert res.status_code == 200
    data = res.json()

    # If score is >= t_review, it must NOT be ROUTINE
    p_val = data["signals"]["p"]
    t_review = data["decision"]["thresholds_applied"]["t_review"]
    if p_val >= t_review:
        assert data["decision"]["action"] in ["FRAUD_ALERT", "MANUAL_REVIEW"]
