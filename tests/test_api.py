"""Tests for SignalGate FastAPI Endpoints."""

import pytest
from starlette.testclient import TestClient
from backend.app.main import app

client = TestClient(app)


def test_api_health():
    res = client.get("/api/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "HEALTHY"
    assert data["service_name"] == "SignalGate Fraud Triage API"
    assert "timestamp" in data


def test_api_status_readiness():
    res = client.get("/api/status")
    assert res.status_code == 200
    data = res.json()
    assert data["evidence_status"] == "SYNTHETIC_SMOKE_ONLY"
    assert "dependencies" in data
    deps = data["dependencies"]
    assert deps["dataset"]["status"] == "SYNTHETIC_SMOKE_ONLY"
    assert deps["model_artifacts"]["status"] == "READY"
    assert deps["frozen_policy"]["status"] == "READY"
    assert deps["consolidated_results"]["status"] == "READY"
    assert deps["explanations"]["status"] == "DISABLED"


def test_api_overview():
    res = client.get("/api/overview")
    assert res.status_code == 200
    data = res.json()
    assert data["dataset_status"] == "SYNTHETIC_SMOKE_ONLY"
    assert data["total_tested_transactions"] == 2000
    assert data["available_fraud_count"] == 111
    assert data["primary_budget"] == 0.06525
    assert data["b2_recall"] == pytest.approx(0.09009, abs=1e-4)
    assert data["signalgate_recall"] == pytest.approx(0.09009, abs=1e-4)
    assert data["delta_recall_pp"] == pytest.approx(0.0, abs=1e-4)
    assert data["ci_conclusive"] is False
    assert data["frozen_config_hash"] == "8d3f02ca492ca94bab45f3ceac8d39432c2f29f40d54e7990b4aa78cbbff6240"
    assert data["split_hash"] == "07b55a4ed74f238c9ef5b779a749770cf274d4709a4389d9eab860dd9068fbdd"


def test_api_results():
    res = client.get("/api/results")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "SYNTHETIC_SMOKE_ONLY"
    assert "primary_policy_comparison" in data
    assert "paired_bootstrap_ci" in data
    assert "budget_sweep" in data
    assert "shift_scenarios" in data
    assert "drift_monitoring" in data
    assert "segment_analysis" in data
    assert "value_model" in data
    assert "latency_benchmarks" in data


def test_api_policies_compare_primary_and_sweep():
    # Primary budget comparison
    res = client.get("/api/policies/compare")
    assert res.status_code == 200
    data = res.json()
    assert data["budget_multiple"] == "1.5x"
    assert len(data["policies"]) >= 4
    policy_names = [p["policy"] for p in data["policies"]]
    assert "B2_top_b_risk" in policy_names
    assert "SignalGate_frozen" in policy_names

    # Specific budget sweep multiple
    res_2x = client.get("/api/policies/compare?budget_multiple=2.0x")
    assert res_2x.status_code == 200
    data_2x = res_2x.json()
    assert data_2x["budget_multiple"] == "2.0x"
    assert data_2x["target_budget"] == pytest.approx(0.087, abs=1e-4)

    # Invalid budget multiple
    res_bad = client.get("/api/policies/compare?budget_multiple=99.0x")
    assert res_bad.status_code == 400
    assert res_bad.json()["error"]["code"] == "INVALID_BUDGET_MULTIPLE"


def test_api_scenarios():
    res = client.get("/api/scenarios")
    assert res.status_code == 200
    data = res.json()
    scenarios = {s["scenario_id"]: s for s in data["scenarios"]}
    assert "S0" in scenarios
    assert "S1" in scenarios
    assert "S3" in scenarios
    assert scenarios["S0"]["status"] == "SYNTHETIC_SMOKE_ONLY"
    assert scenarios["S3"]["status"] == "SYNTHETIC_SHIFT"


def test_api_cases_list_and_filters():
    res = client.get("/api/cases?limit=10&offset=0")
    assert res.status_code == 200
    data = res.json()
    assert data["total_cases"] == 2000
    assert len(data["cases"]) == 10

    # Filter by action
    res_alert = client.get("/api/cases?action=FRAUD_ALERT")
    assert res_alert.status_code == 200
    data_alert = res_alert.json()
    for c in data_alert["cases"]:
        assert c["action"] == "FRAUD_ALERT"


def test_api_case_detail_success_and_not_found():
    # Valid case detail lookup
    res_list = client.get("/api/cases?limit=1")
    assert res_list.status_code == 200
    case_id = res_list.json()["cases"][0]["case_id"]

    res_case = client.get(f"/api/cases/{case_id}")
    assert res_case.status_code == 200
    case_data = res_case.json()
    assert case_data["case_id"] == case_id
    assert "signals" in case_data
    assert "decision" in case_data
    assert "features" in case_data
    assert "offline_evaluation" in case_data

    # Non-existent case detail lookup
    res_404 = client.get("/api/cases/non_existent_case_99999")
    assert res_404.status_code == 404
    assert res_404.json()["error"]["code"] == "CASE_NOT_FOUND"


def test_api_replay_rows():
    res = client.get("/api/replay/rows?scenario=S0&offset=0&limit=50")
    assert res.status_code == 200
    data = res.json()
    assert data["scenario_id"] == "S0"
    assert data["total_rows"] == 2000
    assert len(data["rows"]) == 50
    # Sequential ordering verification
    assert data["rows"][0]["row_id"] == 1
    assert data["rows"][1]["row_id"] == 2


def test_api_audit_list_and_export():
    res = client.get("/api/audit?limit=20")
    assert res.status_code == 200
    data = res.json()
    assert data["total_records"] > 0
    assert len(data["records"]) <= 20

    # Export JSONL
    res_export = client.get("/api/audit/export?format=jsonl")
    assert res_export.status_code == 200
    assert "application/x-ndjson" in res_export.headers["content-type"]
    assert len(res_export.text) > 0

    # Export CSV
    res_csv = client.get("/api/audit/export?format=csv")
    assert res_csv.status_code == 200
    assert "text/csv" in res_csv.headers["content-type"]
    assert "id,ts,p,u,action,reason" in res_csv.text


def test_api_cases_filter_reason_code_canonical_and_alias():
    # Canonical enum filter
    res_canonical = client.get("/api/cases?reason_code=R3_MODEL_DISAGREEMENT")
    assert res_canonical.status_code == 200
    data_c = res_canonical.json()
    assert data_c["total_cases"] == 15
    for c in data_c["cases"]:
        assert c["reason_code"] == "R3_MODEL_DISAGREEMENT"

    # Alias filter
    res_alias = client.get("/api/cases?reason_code=R3_DISAGREEMENT")
    assert res_alias.status_code == 200
    data_a = res_alias.json()
    assert data_a["total_cases"] == 15
    for c in data_a["cases"]:
        assert c["reason_code"] == "R3_MODEL_DISAGREEMENT"

