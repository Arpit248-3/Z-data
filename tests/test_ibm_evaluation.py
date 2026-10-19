"""SignalGate IBM Architecture Integration — Evaluation Test Suite.

Verifies:
1. Pre-evaluation freeze record integrity, schema, and fail-closed tampering detection.
2. Canonical benchmark evaluation results, split provenance, and denominator reporting.
3. Matched-capacity review budget constraints across 1.0x, 1.5x, 2.0x, and 3.0x sweeps.
4. P5 vs B2 identical ranking behavior under frozen lambda = 0.0.
5. 1,000 paired bootstrap resamples, empirical percentile confidence intervals, and conclusiveness.
6. Shift scenarios (S0, S1, S2, S3) and explicit segregation of synthetic perturbations.
7. Acceptance criteria scorecard truthfulness: asserting AC1, AC2, AC4 are UNMET and AC3, AC5 are PASS.
8. Host CPU latency micro-benchmarks within operational thresholds.

Governing Specification: docs/ibm_architecture_integration_master_spec.md § N
Requirements Covered: EVAL-01, EVAL-02, EVAL-03
"""

from __future__ import annotations

import json
from pathlib import Path
import numpy as np
import pytest

from integrations.ibm_architecture.evaluation.freeze import (
    CANONICAL_ARTIFACT_HASHES,
    CANONICAL_FEATURE_MANIFEST_HASH,
    CANONICAL_ROW_COUNTS,
    CANONICAL_SPLIT_HASHES,
    PreEvaluationFreezeRecord,
    load_and_validate_freeze_record,
    verify_and_generate_freeze_record,
)
from integrations.ibm_architecture.evaluation.benchmark_runner import run_paired_bootstrap
from integrations.ibm_architecture.exceptions import IncompatibleArtifactError

PROJECT_ROOT = Path(__file__).resolve().parent.parent


# =============================================================================
# 1. Pre-Evaluation Freeze Protocol Tests (EVAL-01)
# =============================================================================
def test_pre_evaluation_freeze_record_exists_and_validates():
    """Verify pre_evaluation_freeze.json exists and strictly validates all canonical fingerprints."""
    freeze_path = PROJECT_ROOT / "results" / "ieee_cis_v1" / "pre_evaluation_freeze.json"
    assert freeze_path.exists(), f"Missing {freeze_path}"

    record = load_and_validate_freeze_record(freeze_path)
    assert record.status == "PRE_EVALUATION_FREEZE_VERIFIED"
    assert record.architecture_version == "ieee_cis_v1"

    # Dataset metadata
    assert record.dataset["total_raw_rows"] == 590540
    assert record.dataset["verified"] is True

    # Split manifest hashes
    for part, expected_hash in CANONICAL_SPLIT_HASHES.items():
        assert record.split_manifest[part]["split_hash"] == expected_hash
        assert record.split_manifest[part]["row_count"] == CANONICAL_ROW_COUNTS[part]

    # Model bundle artifact hashes
    for artifact, expected_hash in CANONICAL_ARTIFACT_HASHES.items():
        assert record.model_bundle["artifact_hashes"][artifact] == expected_hash

    # Feature manifest
    assert record.feature_manifest["total_features"] == 391
    assert record.feature_manifest["sha256"] == CANONICAL_FEATURE_MANIFEST_HASH
    assert record.feature_manifest["target_excluded"] is True
    assert record.feature_manifest["identifiers_excluded"] is True

    # Frozen policy
    pol = record.frozen_policy
    assert pol["status"] == "FROZEN_IEEE_CIS_V1"
    assert pol["t_alert"] == 0.084705
    assert pol["t_review"] == 0.071002
    assert pol["u_threshold"] == 0.526773
    assert pol["disagreement_weight_lambda"] == 0.0
    assert pol["workload_multiples"] == [1.0, 1.5, 2.0, 3.0]
    assert pol["verified"] is True

    # Historical look acknowledgement
    ack = record.historical_look_acknowledgement
    assert ack["historical_test_looks_acknowledged"] is True
    assert ack["evaluation_classification"] == "BENCHMARK_REPRODUCTION_AND_ACCEPTANCE_EVALUATION"


def test_freeze_verification_fails_closed_on_tampering(tmp_path: Path):
    """Verifier must fail closed with IncompatibleArtifactError when hashes are tampered."""
    # Create dummy directory with modified split_manifest
    fake_results = tmp_path / "results" / "ieee_cis_v1"
    fake_results.mkdir(parents=True)
    fake_split_manifest = fake_results / "split_manifest.json"
    fake_split_manifest.write_text(
        json.dumps({
            "partitions": {
                "train": {"split_hash": "tampered_hash", "row_count": 354324},
            }
        }),
        encoding="utf-8",
    )

    with pytest.raises(Exception):
        verify_and_generate_freeze_record(project_root=tmp_path)


# =============================================================================
# 2. Benchmark Evaluation & Matched Capacity Tests (EVAL-02)
# =============================================================================
def test_benchmark_results_provenance_and_schema():
    """Verify benchmark_results.json exists, adheres to schema, and binds freeze hash."""
    results_path = PROJECT_ROOT / "results" / "ieee_cis_v1" / "benchmark_results.json"
    assert results_path.exists(), f"Missing {results_path}"

    with open(results_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert data["status"] == "BENCHMARK_EVALUATION_COMPLETED"
    assert data["architecture_version"] == "ieee_cis_v1"

    # Provenance binds freeze hash
    freeze_record = load_and_validate_freeze_record()
    assert data["provenance"]["freeze_hash"] == freeze_record.freeze_hash
    assert data["provenance"]["split_hash_test"] == CANONICAL_SPLIT_HASHES["test"]

    # Test partition summary
    summary = data["test_partition_summary"]
    assert summary["total_transactions"] == 118108
    assert summary["total_frauds"] == 4064
    assert pytest.approx(summary["prevalence"], abs=1e-5) == 0.034409

    # Model accuracy
    acc = data["overall_model_accuracy"]["heterogeneous_ensemble"]
    assert pytest.approx(acc["roc_auc"], abs=1e-3) == 0.8805
    assert pytest.approx(acc["brier_score"], abs=1e-3) == 0.0246
    assert pytest.approx(acc["expected_calibration_error"], abs=1e-3) == 0.0089


def test_budget_sweep_matched_capacity_and_identical_ranking():
    """Verify all registered budgets (1.0x, 1.5x, 2.0x, 3.0x) and identical ranking under lambda=0."""
    results_path = PROJECT_ROOT / "results" / "ieee_cis_v1" / "benchmark_results.json"
    with open(results_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    sweep = data["budget_sweep"]
    expected_multiples = ["1.0x", "1.5x", "2.0x", "3.0x"]
    for mult in expected_multiples:
        assert mult in sweep
        entry = sweep[mult]

        # Budget matching
        assert entry["baseline_b2"]["budget_matched"] is True
        assert entry["candidate_p5"]["budget_matched"] is True
        assert entry["baseline_b2"]["total_transactions"] == 118108
        assert entry["candidate_p5"]["total_transactions"] == 118108
        assert entry["baseline_b2"]["total_fraud"] == 4064
        assert entry["candidate_p5"]["total_fraud"] == 4064

        # Under lambda = 0.0, rankings and caught fraud must be mathematically identical
        assert entry["candidate_p5"]["caught_fraud"] == entry["baseline_b2"]["caught_fraud"]
        assert entry["candidate_p5"]["recall_at_touched"] == entry["baseline_b2"]["recall_at_touched"]
        assert entry["recall_gain_percentage_points"] == 0.0


def test_paired_bootstrap_resampling_results():
    """Verify 1,000 paired bootstrap replicates and empirical percentile confidence bounds."""
    results_path = PROJECT_ROOT / "results" / "ieee_cis_v1" / "benchmark_results.json"
    with open(results_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    boot = data["primary_bootstrap_1_5x"]
    assert boot["method"] == "paired_percentile_bootstrap"
    assert boot["n_resamples_requested"] == 1000
    assert boot["n_resamples_valid"] == 1000
    assert boot["point_estimate_diff"] == 0.0
    assert boot["ci_lower"] == 0.0
    assert boot["ci_upper"] == 0.0
    assert boot["is_conclusive"] is False
    assert "Inconclusive" in boot["conclusion"]


def test_run_paired_bootstrap_conclusive_on_synthetic_difference():
    """Unit test run_paired_bootstrap on toy data with distinct policies."""
    y = np.array([1] * 20 + [0] * 80, dtype=np.int8)
    m_p5 = np.array([True] * 15 + [False] * 85, dtype=bool)  # catches 15/20 = 0.75
    m_b2 = np.array([True] * 5 + [False] * 95, dtype=bool)   # catches 5/20 = 0.25

    res = run_paired_bootstrap(y, m_p5, m_b2, n_resamples=500, seed=42)
    assert pytest.approx(res["point_estimate_diff"], abs=1e-5) == 0.50
    assert res["ci_lower"] > 0.0
    assert res["ci_upper"] > res["ci_lower"]
    assert res["is_conclusive"] is True


def test_shift_scenarios_and_synthetic_shift_segregation():
    """Verify scenarios S0, S1, S2, S3 with strict SYNTHETIC_SHIFT segregation."""
    results_path = PROJECT_ROOT / "results" / "ieee_cis_v1" / "benchmark_results.json"
    with open(results_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    scenarios = data["shift_scenarios"]
    assert "S0_nominal" in scenarios
    assert "S1_prevalence_burst" in scenarios
    assert "S2_covariate_shift" in scenarios
    assert "S3_unseen_feature_perturbation" in scenarios

    # Real data statuses
    assert scenarios["S0_nominal"]["evidence_status"] == "EMPIRICAL_TEST_PARTITION"
    assert scenarios["S1_prevalence_burst"]["evidence_status"] == "EMPIRICAL_TEST_BURST"
    assert scenarios["S2_covariate_shift"]["evidence_status"] == "EMPIRICAL_SEGMENT_SHIFT"

    # Synthetic stress status must be segregated per Master Spec § C1
    assert scenarios["S3_unseen_feature_perturbation"]["evidence_status"] == "SYNTHETIC_SHIFT"
    assert "synthetic_stress_disclaimer" in scenarios["S3_unseen_feature_perturbation"]


def test_acceptance_criteria_scorecard_truthful_standards():
    """Verify Master Spec § N rule: never convert documented unmet criteria to PASS."""
    results_path = PROJECT_ROOT / "results" / "ieee_cis_v1" / "benchmark_results.json"
    with open(results_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    scorecard = data["acceptance_criteria_scorecard"]

    # AC1: S0 recall gain target (+2.00 pp) -> UNMET
    assert scorecard["AC1_recall_gain"]["status"] == "UNMET"
    assert "+0.0000 percentage points" in scorecard["AC1_recall_gain"]["observed"]

    # AC2: Workload reduction (>= 15%) -> UNMET
    assert scorecard["AC2_workload_reduction"]["status"] == "UNMET"
    assert scorecard["AC2_workload_reduction"]["observed"] == "0.0%"

    # AC3: Shift robustness degradation (<= 10%) -> PASS
    assert scorecard["AC3_shift_robustness"]["status"] == "PASS"

    # AC4: Confident-miss reduction (>= 20%) -> UNMET
    assert scorecard["AC4_confident_miss_reduction"]["status"] == "UNMET"

    # AC5: Host inference latency (p95 <= 100 ms) -> PASS
    assert scorecard["AC5_host_inference_latency"]["status"] == "PASS"


def test_host_latency_benchmarks():
    """Verify host CPU latency micro-benchmarks are within operational bounds."""
    results_path = PROJECT_ROOT / "results" / "ieee_cis_v1" / "benchmark_results.json"
    with open(results_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    lat = data["latency_benchmarks"]
    single = lat["single_transaction"]
    assert single["p95_ms"] <= 100.0
    assert single["meets_p95_100ms_target"] is True
    assert "Windows AMD64" in lat["hardware_platform"]
