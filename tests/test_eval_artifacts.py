"""Tests for SignalGate Phase 5 Evaluation Artifacts and Hash Integrity."""

import json
from pathlib import Path
import pandas as pd
import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def test_results_json_schema_and_provenance():
    results_path = PROJECT_ROOT / "results" / "results.json"
    assert results_path.exists(), f"Missing {results_path}"

    with open(results_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Synthetic status preservation
    assert data["status"] == "SYNTHETIC_SMOKE_ONLY"
    assert data["is_synthetic"] is True

    # Provenance and cryptographic hashes
    prov = data["provenance"]
    assert prov["dataset_sha256"] == "da00179ebf37970ec8907d11cfb366d170ddd5b2b41370e881bf92359b7d17de"
    assert prov["split_hash"] == "07b55a4ed74f238c9ef5b779a749770cf274d4709a4389d9eab860dd9068fbdd"
    assert prov["frozen_config_hash"] == "8d3f02ca492ca94bab45f3ceac8d39432c2f29f40d54e7990b4aa78cbbff6240"
    assert prov["test_look"] == "G5_LOOK_2_FINAL"
    assert prov["test_rows"] == 2000
    assert prov["test_fraud_count"] == 111

    # Policies present in primary comparison
    primary = data["primary_policy_comparison"]
    for expected_pol in ["B1_fixed_threshold", "B2_top_b_risk", "B3a_confidence_deferral", "B4_random_control", "SignalGate_frozen"]:
        assert expected_pol in primary
        assert primary[expected_pol]["total_transactions"] == 2000
        assert primary[expected_pol]["total_fraud"] == 111
        assert 0.0 <= primary[expected_pol]["recall_at_touched"] <= 1.0

    # Bootstrap CI
    boot = data["paired_bootstrap_ci"]
    assert boot["method"] == "paired_percentile_bootstrap"
    assert boot["n_resamples_requested"] == 1000
    assert boot["n_resamples_valid"] == 1000
    assert boot["ci_lower"] <= boot["ci_upper"]

    # Budget sweep
    sweep = data["budget_sweep"]
    for mult in ["1.0x", "1.5x", "2.0x", "3.0x"]:
        assert mult in sweep
        assert sweep[mult]["signalgate_metrics"]["total_transactions"] == 2000

    # Shift scenarios
    shift = data["shift_scenarios"]
    assert "S0" in shift
    assert "S1" in shift
    assert "S3" in shift
    assert shift["S3"]["status"] == "SYNTHETIC_SHIFT"

    # Latency
    lat = data["latency_benchmarks"]
    assert lat["acceptance_check_ac5"]["passed"] is True
    assert lat["single_transaction_path"]["p95_ms"] <= 50.0

    # Value model
    val = data["value_model"]["primary_evaluation"]
    assert "financial_outcomes_usd" in val
    assert "scenario_net_benefit_usd" in val["financial_outcomes_usd"]


def test_csv_tables_exist_and_non_empty():
    tables_dir = PROJECT_ROOT / "results" / "tables"
    expected_tables = [
        "policy_comparison.csv",
        "budget_sweep.csv",
        "shift_comparison.csv",
        "segment_analysis.csv",
        "latency.csv",
    ]
    for table_name in expected_tables:
        path = tables_dir / table_name
        assert path.exists(), f"Missing {path}"
        df = pd.read_csv(path)
        assert len(df) > 0, f"Empty CSV table: {table_name}"


def test_visual_figures_exist_and_non_empty():
    figs_dir = PROJECT_ROOT / "results" / "figs"
    expected_figs = [
        "policy_recall_comparison.png",
        "budget_sweep_recall.png",
        "shift_comparison.png",
        "drift_psi_distribution.png",
        "latency_distribution.png",
    ]
    for fig_name in expected_figs:
        path = figs_dir / fig_name
        assert path.exists(), f"Missing {path}"
        assert path.stat().st_size > 1000, f"Figure too small / empty: {fig_name}"


def test_test_looks_log_ledger_integrity():
    log_path = PROJECT_ROOT / "logs" / "test_looks.log"
    assert log_path.exists()
    content = log_path.read_text(encoding="utf-8")
    assert "TEST LOOK G3" in content
    assert "TEST LOOK G5" in content
    assert "8d3f02ca492ca94bab45f3ceac8d39432c2f29f40d54e7990b4aa78cbbff6240" in content
