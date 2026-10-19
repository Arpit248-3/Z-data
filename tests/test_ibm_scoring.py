"""SignalGate IBM Architecture Integration — Policy & Scoring Test Suite.

Verifies:
1. Model bundle cryptographic integrity & fail-closed loader behavior.
2. RouterPolicyAdapter exact threshold boundaries and fail-closed state transitions.
3. High-risk invariant (p >= t_alert never ROUTINE) and disagreement invariant (u >= u_th never FRAUD_ALERT).
4. B2TopBudgetBaselineAdapter exact top-B budget matching and deterministic ranking.
5. P5CandidatePolicyAdapter formula (Score = p + lambda * u), lambda=0.0 default, and cohort requirement.
6. CapacityGovernor dual capacity modes (fixed count K vs. budget fraction B_frac).
7. Capacity saturation and deferred queue segregation (DEFERRED / R6_CAPACITY_DEFERRED).
8. Strict no-silent-clearance invariant under capacity saturation.
9. Deterministic tie-breaking on pseudonymous IDs and index mergesort.
10. ScoringService single-case scoring and structured ScoringResult schema validation.
11. ScoringService batch scoring and CapacityGovernor integration.
12. Strict ground-truth quarantine: isFraud, TransactionID, and TransactionDT rejected with LeakageViolationError.

Governing Specification: docs/ibm_architecture_integration_master_spec.md § C, § I
Requirements Covered: SCOR-01, SCOR-02, SCOR-03
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List
import numpy as np
import pandas as pd
import pytest

from integrations.ibm_architecture.exceptions import (
    ArtifactNotFoundError,
    IncompatibleArtifactError,
    LeakageViolationError,
)
from integrations.ibm_architecture.models import (
    FeaturePipeline,
    ModelBundle,
    ModelBundleManifest,
    load_bundle,
    train_mock_pipeline_for_testing,
)
from integrations.ibm_architecture.policy import (
    B2TopBudgetBaselineAdapter,
    CapacityGovernor,
    IEEEPolicyConfig,
    P5CandidatePolicyAdapter,
    RouterPolicyAdapter,
    get_frozen_ieee_policy_config,
    validate_router_config,
)
from integrations.ibm_architecture.scoring import (
    BatchScoringResult,
    ScoringRequest,
    ScoringResult,
    ScoringService,
    check_feature_quarantine,
)


@pytest.fixture
def mock_scoring_bundle(tmp_path: Path) -> ModelBundle:
    """Create a minimal mock fitted model bundle for testing scoring service."""
    rng = np.random.RandomState(42)
    n_samples = 60
    data = {}
    for i in range(1, 378):
        data[f"num_{i}"] = rng.randn(n_samples)
    for c in ["ProductCD", "card4", "card6", "P_emaildomain", "R_emaildomain", "M1", "M2", "M3", "M4", "M5", "M6", "M7", "M8", "M9"]:
        data[c] = rng.choice(["W", "H", "C", "missing"], size=n_samples)

    data["isFraud"] = rng.choice([0, 1], size=n_samples, p=[0.9, 0.1]).astype(np.int8)
    df = pd.DataFrame(data)
    return train_mock_pipeline_for_testing(df, output_dir=tmp_path / "mock_bundle")


# ==============================================================================
# 1. Artifact Integrity & Fail-Closed Loader Tests
# ==============================================================================

def test_load_bundle_missing_manifest_fails_closed(tmp_path: Path):
    """Verify load_bundle raises ArtifactNotFoundError when manifest is missing."""
    empty_dir = tmp_path / "empty_bundle"
    empty_dir.mkdir(parents=True, exist_ok=True)
    with pytest.raises(ArtifactNotFoundError) as exc_info:
        load_bundle(empty_dir)
    assert "Model bundle provenance manifest" in str(exc_info.value)


def test_load_bundle_missing_component_fails_closed(tmp_path: Path):
    """Verify load_bundle raises ArtifactNotFoundError when a model component is missing."""
    bundle_dir = tmp_path / "incomplete_bundle"
    bundle_dir.mkdir(parents=True, exist_ok=True)
    manifest = ModelBundleManifest(
        artifact_hashes={"feature_pipeline.joblib": "dummy_hash"}
    )
    (bundle_dir / "model_bundle_manifest.json").write_text(json.dumps(manifest.model_dump()))

    with pytest.raises(ArtifactNotFoundError) as exc_info:
        load_bundle(bundle_dir)
    assert "feature_pipeline.joblib" in str(exc_info.value)


def test_load_bundle_tampered_hash_fails_closed(tmp_path: Path, mock_scoring_bundle: ModelBundle):
    """Verify load_bundle raises IncompatibleArtifactError when component hash mismatches."""
    bundle_dir = tmp_path / "mock_bundle"
    # Tamper with calibrator.joblib
    calib_file = bundle_dir / "calibrator.joblib"
    calib_file.write_bytes(b"corrupted_tampered_bytes")

    with pytest.raises(IncompatibleArtifactError) as exc_info:
        load_bundle(bundle_dir)
    assert "Artifact fingerprint mismatch" in str(exc_info.value)


# ==============================================================================
# 2. Router Policy Adapter & Fail-Closed State Transition Tests
# ==============================================================================

def test_router_exact_threshold_boundaries():
    """Verify RouterPolicyAdapter exact decision boundaries."""
    cfg = get_frozen_ieee_policy_config()
    router = RouterPolicyAdapter(config=cfg)

    # 1. High risk: p >= t_alert (0.084705)
    action, reason = router.route(p=0.084705, u=0.1)
    assert action == "FRAUD_ALERT"
    assert reason == "R1_HIGH_RISK"

    action, reason = router.route(p=0.09, u=0.1)
    assert action == "FRAUD_ALERT"
    assert reason == "R1_HIGH_RISK"

    # 2. Intermediate risk: t_review <= p < t_alert
    action, reason = router.route(p=0.071002, u=0.1)
    assert action == "MANUAL_REVIEW"
    assert reason == "R2_INTERMEDIATE_RISK"

    action, reason = router.route(p=0.084704, u=0.1)
    assert action == "MANUAL_REVIEW"
    assert reason == "R2_INTERMEDIATE_RISK"

    # 3. Disagreement: p < t_review, u >= u_threshold (0.526773)
    action, reason = router.route(p=0.02, u=0.526773)
    assert action == "MANUAL_REVIEW"
    assert reason == "R3_MODEL_DISAGREEMENT"

    action, reason = router.route(p=0.02, u=0.60)
    assert action == "MANUAL_REVIEW"
    assert reason == "R3_MODEL_DISAGREEMENT"

    # 4. Low risk reliable: p < t_review, u < u_threshold
    action, reason = router.route(p=0.02, u=0.1)
    assert action == "ROUTINE"
    assert reason == "R5_LOW_RISK_RELIABLE"


def test_router_invalid_signals_fail_closed():
    """Verify RouterPolicyAdapter fails closed on missing, NaN, Inf, or out-of-range signals."""
    router = RouterPolicyAdapter()

    # None, NaN, Inf p
    assert router.route(p=None, u=0.1) == ("MANUAL_REVIEW", "R0_SIGNAL_UNAVAILABLE")
    assert router.route(p=float("nan"), u=0.1) == ("MANUAL_REVIEW", "R0_SIGNAL_UNAVAILABLE")
    assert router.route(p=float("inf"), u=0.1) == ("MANUAL_REVIEW", "R0_SIGNAL_UNAVAILABLE")
    assert router.route(p=-0.05, u=0.1) == ("MANUAL_REVIEW", "R0_SIGNAL_UNAVAILABLE")
    assert router.route(p=1.05, u=0.1) == ("MANUAL_REVIEW", "R0_SIGNAL_UNAVAILABLE")

    # Missing / non-finite u when disagreement is enabled
    assert router.route(p=0.02, u=None) == ("MANUAL_REVIEW", "R0_SIGNAL_UNAVAILABLE")
    assert router.route(p=0.02, u=float("nan")) == ("MANUAL_REVIEW", "R0_SIGNAL_UNAVAILABLE")
    assert router.route(p=0.02, u=-0.1) == ("MANUAL_REVIEW", "R0_SIGNAL_UNAVAILABLE")


def test_router_safety_invariants():
    """Verify high-risk never ROUTINE and disagreement never FRAUD_ALERT."""
    router = RouterPolicyAdapter()

    # Invariant A: p >= t_alert can NEVER produce ROUTINE
    for p_val in [0.084705, 0.1, 0.5, 0.99]:
        for u_val in [0.0, 0.1, 0.9, 2.0]:
            action, _ = router.route(p=p_val, u=u_val)
            assert action != "ROUTINE"
            assert action == "FRAUD_ALERT"

    # Invariant B: Disagreement alone (p < t_review, u >= u_threshold) triggers MANUAL_REVIEW, never FRAUD_ALERT
    action, reason = router.route(p=0.01, u=0.99)
    assert action == "MANUAL_REVIEW"
    assert reason == "R3_MODEL_DISAGREEMENT"


# ==============================================================================
# 3. Baseline B2 Top-Budget Policy Tests
# ==============================================================================

def test_b2_top_b_exact_budget_matching():
    """Verify B2TopBudgetBaselineAdapter escalates exactly floor(N * B) cases."""
    b2 = B2TopBudgetBaselineAdapter(default_budget_fraction=0.05)
    p_scores = np.linspace(0.01, 0.99, 100)

    # 100 samples at B = 0.05 -> exactly 5 cases
    mask = b2.get_escalation_mask(p_scores, budget_fraction=0.05)
    assert np.sum(mask) == 5

    # Highest 5 p-scores should be True
    expected_top_5 = p_scores >= p_scores[95]
    np.testing.assert_array_equal(mask, expected_top_5)

    # Cohort routing
    actions, reasons = b2.route_cohort(p_scores, budget_fraction=0.05)
    assert sum(1 for a in actions if a == "MANUAL_REVIEW") == 5
    assert sum(1 for a in actions if a == "ROUTINE") == 95

    # Offline metric calculation
    y_true = np.zeros(100, dtype=np.int8)
    y_true[98:] = 1  # 2 true fraud cases in top 5
    metrics = b2.evaluate_cohort(p_scores, y_true, budget_fraction=0.05)
    assert metrics["escalated_count"] == 5
    assert metrics["caught_fraud"] == 2
    assert metrics["total_fraud"] == 2
    assert metrics["recall_at_touched"] == 1.0
    assert metrics["budget_matched"] is True


# ==============================================================================
# 4. Candidate P5 Policy Tests
# ==============================================================================

def test_p5_candidate_formula_and_cohort_requirement():
    """Verify P5 ranking Score = p + lambda * u, lambda=0.0 default, and single-case error."""
    p5 = P5CandidatePolicyAdapter(default_lambda=0.0, default_budget_fraction=0.1)

    # 1. Single transaction without cohort context raises ValueError
    with pytest.raises(ValueError) as exc_info:
        p5.compute_scores(p=[0.05])
    assert "cohort-relative budget-ranking policy" in str(exc_info.value)

    # 2. Frozen reference lambda=0.0 ranks purely by calibrated risk p
    p_cohort = np.array([0.1, 0.5, 0.3, 0.9, 0.2])
    u_cohort = np.array([0.8, 0.1, 0.9, 0.0, 0.4])

    scores_ref = p5.compute_scores(p_cohort, u_cohort, lambda_weight=0.0)
    np.testing.assert_array_equal(scores_ref, p_cohort)

    # 3. Non-zero lambda combines p + lambda * u
    scores_lam = p5.compute_scores(p_cohort, u_cohort, lambda_weight=0.5)
    expected_lam = p_cohort + 0.5 * u_cohort
    np.testing.assert_allclose(scores_lam, expected_lam)

    # 4. Cohort routing with B=0.4 (top 2 of 5)
    mask = p5.get_escalation_mask(p_cohort, u_cohort, budget_fraction=0.4, lambda_weight=0.0)
    assert np.sum(mask) == 2
    # Top 2 p values are indices 1 (0.5) and 3 (0.9)
    assert mask[1] and mask[3]


# ==============================================================================
# 5. Capacity Governor Tests (Dual Mode & Saturation Invariant)
# ==============================================================================

def test_capacity_governor_dual_modes():
    """Verify CapacityGovernor supports both fixed integer count and float budget fraction."""
    # Mode A: fixed count
    g_fixed = CapacityGovernor(capacity=130)
    assert g_fixed.resolve_effective_capacity(2000) == 130
    assert g_fixed.resolve_effective_capacity(118108) == 130

    # Mode B: budget fraction
    g_frac = CapacityGovernor(budget_fraction=0.05075)
    assert g_frac.resolve_effective_capacity(2000) == 101
    assert g_frac.resolve_effective_capacity(118108) == int(np.floor(118108 * 0.05075))  # ~5,993

    # Error handling
    with pytest.raises(ValueError):
        CapacityGovernor()  # Neither specified
    with pytest.raises(ValueError):
        CapacityGovernor(capacity=-5)
    with pytest.raises(ValueError):
        CapacityGovernor(budget_fraction=1.5)


def test_capacity_governor_under_capacity():
    """Verify CapacityGovernor admits all candidates when requested <= quota."""
    governor = CapacityGovernor(capacity=10)
    df = pd.DataFrame({
        "p": [0.9, 0.8, 0.7, 0.01, 0.02],
        "action": ["FRAUD_ALERT", "MANUAL_REVIEW", "MANUAL_REVIEW", "ROUTINE", "ROUTINE"],
        "reason": ["R1_HIGH_RISK", "R2_INTERMEDIATE_RISK", "R2_INTERMEDIATE_RISK", "R5_LOW_RISK_RELIABLE", "R5_LOW_RISK_RELIABLE"],
    })
    gov_df, metrics = governor.govern(df)

    assert metrics["requested_escalations"] == 3
    assert metrics["admitted_alerts"] == 1
    assert metrics["admitted_reviews"] == 2
    assert metrics["deferred_count"] == 0
    assert metrics["capacity_exhausted"] is False
    assert metrics["touched_rate"] == 0.6  # 3/5


def test_capacity_governor_saturation_and_no_silent_clearance():
    """Verify capacity saturation shunts excess to DEFERRED / R6 and NEVER reclassifies to ROUTINE."""
    # Quota is strictly 2 cases, but router requested 4 escalations
    governor = CapacityGovernor(capacity=2)
    df = pd.DataFrame({
        "p": [0.95, 0.85, 0.75, 0.65, 0.01],
        "action": ["FRAUD_ALERT", "MANUAL_REVIEW", "MANUAL_REVIEW", "MANUAL_REVIEW", "ROUTINE"],
        "reason": ["R1_HIGH_RISK", "R2_INTERMEDIATE_RISK", "R2_INTERMEDIATE_RISK", "R2_INTERMEDIATE_RISK", "R5_LOW_RISK_RELIABLE"],
    })
    gov_df, metrics = governor.govern(df)

    assert metrics["requested_escalations"] == 4
    assert metrics["admitted_alerts"] == 1
    assert metrics["admitted_reviews"] == 1
    assert metrics["deferred_count"] == 2
    assert metrics["routine_count"] == 1  # Original routine remains routine; deferred NEVER becomes routine
    assert metrics["capacity_exhausted"] is True

    # Invariant Check: The 2 deferred cases must be Action.DEFERRED with R6_CAPACITY_DEFERRED
    deferred_rows = gov_df[gov_df["governor_status"] == "deferred"]
    assert len(deferred_rows) == 2
    assert set(deferred_rows["action"]) == {"DEFERRED"}
    assert set(deferred_rows["reason"]) == {"R6_CAPACITY_DEFERRED"}


def test_capacity_governor_deterministic_tie_breaking():
    """Verify stable deterministic tie-breaking on priority and secondary ID."""
    governor = CapacityGovernor(capacity=2)
    df = pd.DataFrame({
        "id": ["CASE_C", "CASE_A", "CASE_B"],
        "p": [0.8, 0.8, 0.8],  # Identical priority
        "action": ["MANUAL_REVIEW", "MANUAL_REVIEW", "MANUAL_REVIEW"],
        "reason": ["R2_INTERMEDIATE_RISK", "R2_INTERMEDIATE_RISK", "R2_INTERMEDIATE_RISK"],
    })
    # Secondary tie-breaking by id ascending: CASE_A (rank 1), CASE_B (rank 2) admitted; CASE_C deferred
    gov_df, _ = governor.govern(df, id_col="id")

    row_a = gov_df[gov_df["id"] == "CASE_A"].iloc[0]
    row_b = gov_df[gov_df["id"] == "CASE_B"].iloc[0]
    row_c = gov_df[gov_df["id"] == "CASE_C"].iloc[0]

    assert row_a["governor_status"] == "admitted" and row_a["lane_rank"] == 1
    assert row_b["governor_status"] == "admitted" and row_b["lane_rank"] == 2
    assert row_c["governor_status"] == "deferred" and row_c["lane_rank"] == 3


# ==============================================================================
# 6. Scoring Service Single & Batch Tests
# ==============================================================================

def test_scoring_service_single_case(mock_scoring_bundle: ModelBundle):
    """Verify ScoringService single-case scoring and structured result."""
    service = ScoringService(bundle=mock_scoring_bundle)

    # Valid feature dictionary matching mock pipeline schema
    rng = np.random.RandomState(123)
    features = {f"num_{i}": rng.randn() for i in range(1, 378)}
    for c in ["ProductCD", "card4", "card6", "P_emaildomain", "R_emaildomain", "M1", "M2", "M3", "M4", "M5", "M6", "M7", "M8", "M9"]:
        features[c] = "W"

    result = service.score_single(features=features, transaction_id="TEST_TX_001")
    assert isinstance(result, ScoringResult)
    assert result.transaction_id == "TEST_TX_001"
    assert 0.0 <= result.p <= 1.0
    assert result.u is not None and result.u >= 0.0
    assert result.u2 is not None and result.u2 >= 0.0
    assert result.action in ["ROUTINE", "MANUAL_REVIEW", "FRAUD_ALERT"]
    assert result.model_version == mock_scoring_bundle.manifest.architecture_version
    assert len(result.cfg_hash) == 64


def test_scoring_service_single_case_p5_raises_value_error(mock_scoring_bundle: ModelBundle):
    """Verify scoring single case with policy_name='p5' raises ValueError."""
    service = ScoringService(bundle=mock_scoring_bundle)
    features = {"num_1": 1.0}
    with pytest.raises(ValueError) as exc_info:
        service.score_single(features=features, policy_name="p5")
    assert "cohort-relative budget-ranking policy" in str(exc_info.value)


def test_scoring_service_batch_with_capacity(mock_scoring_bundle: ModelBundle):
    """Verify ScoringService batch scoring with capacity governance."""
    service = ScoringService(bundle=mock_scoring_bundle)

    rng = np.random.RandomState(456)
    n_samples = 25
    data = {"pseudonymous_id": [f"TX_{i:04d}" for i in range(n_samples)]}
    for i in range(1, 378):
        data[f"num_{i}"] = rng.randn(n_samples)
    for c in ["ProductCD", "card4", "card6", "P_emaildomain", "R_emaildomain", "M1", "M2", "M3", "M4", "M5", "M6", "M7", "M8", "M9"]:
        data[c] = ["W"] * n_samples

    df = pd.DataFrame(data)

    # Score with tight capacity limit of 3 cases
    batch_res = service.score_batch(
        df=df,
        id_col="pseudonymous_id",
        policy_name="router",
        capacity=3,
    )
    assert isinstance(batch_res, BatchScoringResult)
    assert batch_res.total_transactions == 25
    assert len(batch_res.results) == 25
    assert batch_res.governance_metrics["effective_capacity"] == 3

    # Check that pseudonymous IDs were preserved in output records
    assert batch_res.results[0].transaction_id == "TX_0000"


# ==============================================================================
# 7. Ground-Truth Quarantine Enforcement Tests
# ==============================================================================

def test_scoring_service_leakage_quarantine_rejection(mock_scoring_bundle: ModelBundle):
    """Verify ScoringService proactively raises LeakageViolationError on forbidden fields."""
    service = ScoringService(bundle=mock_scoring_bundle)

    forbidden_fields = ["isFraud", "target", "label", "TransactionID", "TransactionDT"]
    for forbidden in forbidden_fields:
        # In single-case features
        features = {"num_1": 0.5, forbidden: 1}
        with pytest.raises(LeakageViolationError) as exc_info:
            service.score_single(features=features)
        assert forbidden in exc_info.value.violated_fields

        # In batch DataFrame
        df = pd.DataFrame({"num_1": [0.5], forbidden: [1]})
        with pytest.raises(LeakageViolationError) as exc_info_batch:
            service.score_batch(df=df)
        assert forbidden in exc_info_batch.value.violated_fields
