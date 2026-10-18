"""Tests for SignalGate API Artifact Lifecycle and Missing Dependency Handling."""

from pathlib import Path
import pytest
from starlette.testclient import TestClient

from backend.app.main import app
from backend.app.dependencies import get_artifact_service
from backend.app.services.artifacts import ArtifactService

client = TestClient(app)


class MockMissingArtifactService(ArtifactService):
    """Artifact service simulating missing evaluation and model artifacts."""

    def __init__(self):
        super().__init__(project_root=Path("/non_existent_mock_directory"))

    def get_results_json(self):
        return None

    def get_frozen_policy(self):
        return None

    def get_model_pipeline(self):
        raise FileNotFoundError("Mock model artifacts are missing.")


def test_missing_results_artifact_handling():
    # Override artifact service to simulate missing results
    mock_service = MockMissingArtifactService()
    app.dependency_overrides[get_artifact_service] = lambda: mock_service

    try:
        # 1. /api/results should return structured 503 error
        res_results = client.get("/api/results")
        assert res_results.status_code == 503
        err = res_results.json()["error"]
        assert err["code"] == "ARTIFACT_UNAVAILABLE"

        # 2. /api/overview should return fallback response with explicit NOT_AVAILABLE status
        res_overview = client.get("/api/overview")
        assert res_overview.status_code == 200
        data_ov = res_overview.json()
        assert data_ov["evaluation_status"] == "NOT_AVAILABLE"
        assert data_ov["total_tested_transactions"] is None
        assert data_ov["status_fields"]["results_json"] == "NOT_AVAILABLE"

        # 3. /api/scenarios should return structured 503 error
        res_scenarios = client.get("/api/scenarios")
        assert res_scenarios.status_code == 503
        assert res_scenarios.json()["error"]["code"] == "ARTIFACT_UNAVAILABLE"

        # 4. /api/score-sandbox should return structured 503 error
        res_score = client.post("/api/score-sandbox", json={"features": {"TransactionAmt": 100.0}})
        assert res_score.status_code == 503
        assert res_score.json()["error"]["code"] == "MODEL_ARTIFACTS_UNAVAILABLE"

    finally:
        # Reset dependency overrides
        app.dependency_overrides.clear()


def test_health_operates_when_artifacts_missing():
    # Health endpoint must remain 200 even when artifacts are missing
    mock_service = MockMissingArtifactService()
    app.dependency_overrides[get_artifact_service] = lambda: mock_service

    try:
        res_health = client.get("/api/health")
        assert res_health.status_code == 200
        assert res_health.json()["status"] == "HEALTHY"

        res_status = client.get("/api/status")
        assert res_status.status_code == 200
        data = res_status.json()
        assert data["overall_status"] == "DEGRADED"
        assert data["dependencies"]["consolidated_results"]["status"] == "NOT_AVAILABLE"

    finally:
        app.dependency_overrides.clear()
