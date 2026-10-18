"""Tests for SignalGate API Security, Validation, and Policy Guardrails.

Verifies:
- Rejection of ground-truth leakage fields (isFraud, true_label, etc.) even when nested.
- Rejection of non-finite (NaN, inf) feature inputs.
- Pagination bounds enforcement.
- Safe handling of malformed JSONL audit lines.
- Safe audit export and path traversal prevention.
- Conservative local-development CORS enforcement.
- Read-only GET endpoint immutability.
- Structured error envelopes without raw tracebacks.
"""

import json
from pathlib import Path
import pytest
from starlette.testclient import TestClient

from backend.app.main import app
from backend.app.dependencies import get_audit_service
from backend.app.services.audit import AuditService

client = TestClient(app)


# ---------------------------------------------------------------------------
# 1. Ground-Truth Leakage Rejection
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    "forbidden_key",
    [
        "isFraud",
        "isfraud",
        "IS_FRAUD",
        "true_label",
        "True_Label",
        "TransactionID",
        "transaction_id",
        "TransactionDT",
        "raw_TransactionDT",
        "target",
        "label",
        "y_true",
        "ground_truth",
    ],
)
def test_sandbox_rejects_forbidden_fields_directly(forbidden_key: str):
    payload = {
        "features": {
            "TransactionAmt": 100.0,
            forbidden_key: 1,
        }
    }
    res = client.post("/api/score-sandbox", json=payload)
    assert res.status_code == 422
    err = res.json()["error"]
    assert err["code"] == "VALIDATION_ERROR"
    assert "LEAKAGE VIOLATION" in json.dumps(err["details"])


def test_sandbox_rejects_forbidden_fields_nested():
    payload = {
        "features": {
            "TransactionAmt": 100.0,
            "nested_metadata": {
                "user_audit": {
                    "isFraud": 1,
                }
            },
        }
    }
    res = client.post("/api/score-sandbox", json=payload)
    assert res.status_code == 422
    err = res.json()["error"]
    assert err["code"] == "VALIDATION_ERROR"
    assert "LEAKAGE VIOLATION" in json.dumps(err["details"])


def test_sandbox_rejects_empty_features():
    payload = {"features": {}}
    res = client.post("/api/score-sandbox", json=payload)
    assert res.status_code == 422
    assert "Feature payload cannot be empty" in json.dumps(res.json())


# ---------------------------------------------------------------------------
# 2. Non-Finite & Invalid Value Constraints
# ---------------------------------------------------------------------------
def test_sandbox_rejects_infinity_values():
    payload = {
        "features": {
            "TransactionAmt": "inf",
        }
    }
    res = client.post("/api/score-sandbox", json=payload)
    assert res.status_code == 422
    assert "non-finite" in json.dumps(res.json())


def test_sandbox_rejects_nan_string_values():
    payload = {
        "features": {
            "TransactionAmt": "nan",
        }
    }
    res = client.post("/api/score-sandbox", json=payload)
    assert res.status_code == 422
    assert "non-finite" in json.dumps(res.json())


# ---------------------------------------------------------------------------
# 3. Pagination Bounds & Query Validation
# ---------------------------------------------------------------------------
def test_cases_pagination_bounds():
    # limit > 200 must fail
    res_high = client.get("/api/cases?limit=250")
    assert res_high.status_code == 422

    # limit < 1 must fail
    res_low = client.get("/api/cases?limit=0")
    assert res_low.status_code == 422

    # offset < 0 must fail
    res_neg = client.get("/api/cases?offset=-1")
    assert res_neg.status_code == 422


def test_audit_pagination_bounds():
    res_high = client.get("/api/audit?limit=250")
    assert res_high.status_code == 422

    res_low = client.get("/api/audit?limit=0")
    assert res_low.status_code == 422


# ---------------------------------------------------------------------------
# 4. Path Traversal & Format Safety in Audit Export
# ---------------------------------------------------------------------------
def test_audit_export_format_pattern_enforcement():
    # Attempt format traversal / invalid extensions
    res_bad_format = client.get("/api/audit/export?format=exe")
    assert res_bad_format.status_code == 422

    res_traversal = client.get("/api/audit/export?format=../../etc/passwd")
    assert res_traversal.status_code == 422


# ---------------------------------------------------------------------------
# 5. Malformed Audit Record Safety
# ---------------------------------------------------------------------------
def test_malformed_audit_records_handled_safely(tmp_path: Path):
    # Create temporary audit log with valid and malformed JSON lines
    log_dir = tmp_path / "logs"
    log_dir.mkdir(parents=True)
    audit_file = log_dir / "audit.jsonl"
    with open(audit_file, "w", encoding="utf-8") as f:
        f.write('{"id": "valid_1", "action": "FRAUD_ALERT", "reason": "R1_HIGH_RISK"}\n')
        f.write('{BROKEN_JSON_LINE_CORRUPT\n')
        f.write('{"id": "valid_2", "action": "ROUTINE", "reason": "R5_LOW_RISK_RELIABLE"}\n')

    class TempAuditArtifacts:
        project_root = tmp_path

    temp_service = AuditService(artifact_service=TempAuditArtifacts())
    app.dependency_overrides[get_audit_service] = lambda: temp_service

    try:
        res = client.get("/api/audit")
        assert res.status_code == 200
        data = res.json()
        assert data["total_records"] == 2
        assert data["skipped_records"] == 1
        assert len(data["records"]) == 2
        assert data["records"][0]["id"] == "valid_1"
        assert data["records"][1]["id"] == "valid_2"
    finally:
        app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# 6. CORS Configuration Safety
# ---------------------------------------------------------------------------
def test_cors_allowed_origins():
    # Permitted local frontend origins
    headers_5173 = {"Origin": "http://localhost:5173"}
    res_5173 = client.get("/api/health", headers=headers_5173)
    assert res_5173.headers.get("access-control-allow-origin") == "http://localhost:5173"

    headers_127 = {"Origin": "http://127.0.0.1:5173"}
    res_127 = client.get("/api/health", headers=headers_127)
    assert res_127.headers.get("access-control-allow-origin") == "http://127.0.0.1:5173"


def test_cors_disallows_untrusted_origins():
    headers_untrusted = {"Origin": "http://evil-attacker-site.com"}
    res_untrusted = client.get("/api/health", headers=headers_untrusted)
    assert res_untrusted.headers.get("access-control-allow-origin") is None


# ---------------------------------------------------------------------------
# 7. Read-Only GET Immutability
# ---------------------------------------------------------------------------
def test_get_endpoints_do_not_mutate_artifacts():
    results_path = Path("results/results.json")
    policy_path = Path("policy/frozen_policy.json")

    mtime_results_before = results_path.stat().st_mtime
    mtime_policy_before = policy_path.stat().st_mtime

    # Exercise multiple GET endpoints repeatedly
    for _ in range(3):
        client.get("/api/overview")
        client.get("/api/results")
        client.get("/api/policies/compare")
        client.get("/api/scenarios")
        client.get("/api/cases?limit=5")
        client.get("/api/replay/rows?limit=10")

    assert results_path.stat().st_mtime == mtime_results_before
    assert policy_path.stat().st_mtime == mtime_policy_before


# ---------------------------------------------------------------------------
# 8. Structured Error Envelopes Without Raw Tracebacks
# ---------------------------------------------------------------------------
def test_structured_error_envelope_404():
    res = client.get("/api/cases/totally_unknown_id_xyz")
    assert res.status_code == 404
    data = res.json()
    assert "error" in data
    assert data["error"]["code"] == "CASE_NOT_FOUND"
    assert "traceback" not in data
    assert "Traceback" not in res.text
