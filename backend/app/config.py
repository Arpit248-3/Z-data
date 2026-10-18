"""SignalGate Backend Configuration Module."""

import os
from pathlib import Path
from typing import List
from pydantic import BaseModel, Field


class Settings(BaseModel):
    """Application settings and filesystem path configurations."""

    # Project metadata
    project_name: str = "SignalGate Fraud Triage API"
    version: str = "2.1.0"
    api_prefix: str = "/api"

    # Filesystem root resolution
    project_root: Path = Field(default_factory=lambda: Path(__file__).resolve().parent.parent.parent)

    # Server binding
    host: str = "127.0.0.1"
    port: int = 8000

    # Strict CORS configuration for local React development
    cors_origins: List[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]

    # Pre-registered cryptographic hashes
    expected_split_hash: str = "07b55a4ed74f238c9ef5b779a749770cf274d4709a4389d9eab860dd9068fbdd"
    expected_config_hash: str = "8d3f02ca492ca94bab45f3ceac8d39432c2f29f40d54e7990b4aa78cbbff6240"
    expected_dataset_sha256: str = "da00179ebf37970ec8907d11cfb366d170ddd5b2b41370e881bf92359b7d17de"

    @property
    def results_json_path(self) -> Path:
        return self.project_root / "results" / "results.json"

    @property
    def split_report_path(self) -> Path:
        return self.project_root / "results" / "split_report.json"

    @property
    def model_report_path(self) -> Path:
        return self.project_root / "results" / "model_report.json"

    @property
    def calibration_report_path(self) -> Path:
        return self.project_root / "results" / "calibration_report.json"

    @property
    def ensemble_report_path(self) -> Path:
        return self.project_root / "results" / "ensemble_report.json"

    @property
    def policy_report_path(self) -> Path:
        return self.project_root / "results" / "policy_report.json"

    @property
    def frozen_policy_path(self) -> Path:
        return self.project_root / "policy" / "frozen_policy.json"

    @property
    def artifacts_dir(self) -> Path:
        return self.project_root / "models" / "artifacts"

    @property
    def audit_log_path(self) -> Path:
        return self.project_root / "logs" / "audit.jsonl"

    @property
    def test_looks_log_path(self) -> Path:
        return self.project_root / "logs" / "test_looks.log"

    @property
    def replay_rows_path(self) -> Path:
        return self.project_root / "results" / "replay_rows.jsonl"

    @property
    def cases_path(self) -> Path:
        return self.project_root / "results" / "cases.jsonl"

    @property
    def tables_dir(self) -> Path:
        return self.project_root / "results" / "tables"

    @property
    def figs_dir(self) -> Path:
        return self.project_root / "results" / "figs"


settings = Settings()
