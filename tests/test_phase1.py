"""
SignalGate Phase 1 Verification Tests
Tests for schema validation, forbidden column guards, fixture reproducibility, and config parameters.
"""

import hashlib
import os
from pathlib import Path
import pandas as pd
import pytest
import yaml

from data.schema import (
    TARGET_COLUMN,
    ID_COLUMN,
    TIME_COLUMN,
    FORBIDDEN_MODEL_COLUMNS,
    validate_schema,
    get_feature_columns,
)
from data.generate_fixture import compute_file_sha256

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def test_config_parameters_and_budgets():
    config_path = PROJECT_ROOT / "config.yaml"
    assert config_path.exists(), "config.yaml must exist in project root"

    with open(config_path, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)

    # Blueprint section 8.3 required parameters
    assert cfg["budget_primary_multiple"] == 1.5
    assert cfg["budget_sweep"] == [1.0, 1.5, 2.0, 3.0]
    assert cfg["seeds"] == [11, 22, 33, 44, 55]
    assert cfg["split_pct"] == {"train": [0, 60], "calib": [60, 70], "val": [70, 80], "test": [80, 100]}
    assert cfg["features"]["velocity"] is False
    assert cfg["features"]["v_pruning"] is False
    assert cfg["explanations"]["enabled"] is False
    assert cfg["dataset"]["status"] == "SYNTHETIC_SMOKE_ONLY"


def test_synthetic_fixture_schema_and_reproducibility():
    fixture_path = PROJECT_ROOT / "data" / "synthetic_smoke_fixture.csv"
    assert fixture_path.exists(), f"Synthetic fixture missing at {fixture_path}"

    df = pd.read_csv(fixture_path)
    assert len(df) == 10000, f"Expected 10,000 rows, got {len(df)}"

    # Schema validation
    is_valid, errors = validate_schema(df, is_synthetic=True)
    assert is_valid, f"Schema validation failed: {errors}"

    # Target validity
    assert set(df[TARGET_COLUMN].unique()).issubset({0, 1})
    fraud_count = df[TARGET_COLUMN].sum()
    assert 300 <= fraud_count <= 600, f"Unexpected fraud count: {fraud_count}"

    # Monotonic timestamps
    assert df[TIME_COLUMN].is_monotonic_increasing, "TransactionDT must be monotonically non-decreasing"

    # Deterministic SHA-256 reproducibility check
    expected_hash = "da00179ebf37970ec8907d11cfb366d170ddd5b2b41370e881bf92359b7d17de"
    observed_hash = compute_file_sha256(str(fixture_path))
    assert observed_hash == expected_hash, f"Hash mismatch! Expected {expected_hash}, got {observed_hash}"


def test_leakage_guards_exclude_forbidden_columns():
    fixture_path = PROJECT_ROOT / "data" / "synthetic_smoke_fixture.csv"
    df = pd.read_csv(fixture_path, nrows=50)

    features = get_feature_columns(df)
    for forbidden in FORBIDDEN_MODEL_COLUMNS:
        assert forbidden not in features, f"Forbidden column '{forbidden}' found in feature matrix!"


def test_preflight_environment_report_exists():
    env_log = PROJECT_ROOT / "logs" / "environment.txt"
    assert env_log.exists(), "logs/environment.txt must exist after running preflight"
    content = env_log.read_text(encoding="utf-8")
    assert "SYNTHETIC_SMOKE_ONLY" in content
    assert "HistGradientBoostingClassifier" in content
    assert "FrozenEstimator" in content
