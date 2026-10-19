"""Unit and Integration Tests for SignalGate Drift Monitoring and Replay Gate.

Verifies:
- Population Stability Index (PSI), Kolmogorov-Smirnov (KS), and Wasserstein distance.
- Separation of feature drift, prediction score drift, and epistemic uncertainty.
- Handling of missing, NaN, Inf, and non-finite inputs.
- Ground-truth quarantine enforcement across drift inputs (rejection of isFraud, TransactionID).
- Advisory Drift Sentinel allowlisting, parameter bounds, ordering, and proposal generation.
- Replay Gate deterministic validation replay, churn calculation, and test set quarantine.
- Prevention of automatic policy activation (proposals remain in AWAITING_HUMAN_APPROVAL).
- Explicit human approval and rejection protocols with cryptographic AuditChain provenance.
- End-to-end lifecycle from drift detection to approved policy adaptation.

Governing Specification: docs/ibm_architecture_integration_master_spec.md § C, § K
"""

import numpy as np
import pandas as pd
import pytest

from integrations.ibm_architecture.contracts import Action, Proposal
from integrations.ibm_architecture.exceptions import GroundTruthQuarantineError, LeakageViolationError, SignalGateIntegrationError
from integrations.ibm_architecture.governance.audit_chain import AuditChain
from integrations.ibm_architecture.governance.drift_monitor import DriftMonitor, DriftReport, FeatureDriftResult
from integrations.ibm_architecture.governance.drift_sentinel import (
    ALLOWLISTED_POLICY_KEYS,
    DriftSentinel,
    SentinelConfig,
)
from integrations.ibm_architecture.governance.replay_gate import (
    ProposalStatus,
    ReplayGate,
    ReplayValidationResult,
)
from integrations.ibm_architecture.policy.frozen_policy import IEEEPolicyConfig, get_frozen_ieee_policy_config


# ==============================================================================
# Fixtures
# ==============================================================================

@pytest.fixture
def rng():
    return np.random.default_rng(42)


@pytest.fixture
def monitor():
    return DriftMonitor(epsilon=1e-4, bins=10)


@pytest.fixture
def sentinel():
    return DriftSentinel()


@pytest.fixture
def replay_gate():
    return ReplayGate()


@pytest.fixture
def base_policy():
    return get_frozen_ieee_policy_config()


# ==============================================================================
# 1. Multi-Metric Drift Monitoring Tests (DRFT-01)
# ==============================================================================

def test_psi_stable_distribution(monitor, rng):
    """Identical or near-identical distributions yield PSI < 0.10 and category 'stable'."""
    ref = rng.normal(0.0, 1.0, size=1000)
    act = rng.normal(0.0, 1.0, size=1000)

    res = monitor.calculate_psi(ref, act)
    assert res["psi"] is not None
    assert res["psi"] < 0.10
    assert res["category"] == "stable"


def test_psi_significant_drift(monitor, rng):
    """Severely shifted distributions yield PSI > 0.20 and category 'significant_drift'."""
    ref = rng.normal(0.0, 1.0, size=1000)
    act = rng.normal(2.5, 1.0, size=1000)  # substantial covariate shift

    res = monitor.calculate_psi(ref, act)
    assert res["psi"] is not None
    assert res["psi"] > 0.20
    assert res["category"] == "significant_drift"


def test_ks_statistic_computation(monitor, rng):
    """Two-sample KS test computes statistic and p-value correctly via scipy.stats.ks_2samp."""
    ref = rng.normal(0.0, 1.0, size=500)
    act = rng.normal(0.0, 1.0, size=500)

    ks_stat, ks_pval = monitor.calculate_ks(ref, act)
    assert ks_stat is not None
    assert ks_pval is not None
    assert ks_stat >= 0.0
    assert 0.0 <= ks_pval <= 1.0
    # For identical distributions, p-value should typically be high (> 0.05)
    assert ks_pval > 0.05


def test_wasserstein_distance_computation(monitor, rng):
    """1D Earth Mover's Distance computed accurately between distributions."""
    ref = rng.normal(0.0, 1.0, size=500)
    act_identical = rng.normal(0.0, 1.0, size=500)
    act_shifted = rng.normal(3.0, 1.0, size=500)

    w_identical = monitor.calculate_wasserstein(ref, act_identical)
    w_shifted = monitor.calculate_wasserstein(ref, act_shifted)

    assert w_identical is not None
    assert w_shifted is not None
    assert w_shifted > w_identical
    assert abs(w_shifted - 3.0) < 0.5  # Mean shift of 3.0 units


def test_prediction_score_drift_computation(monitor, rng):
    """Calibrated posterior probability p distribution drift is computed and categorized."""
    ref_p = rng.beta(0.5, 10.0, size=1000)  # typical low fraud risk distribution
    act_p = rng.beta(2.0, 5.0, size=1000)   # elevated risk distribution shift

    res = monitor.compute_score_drift(ref_p, act_p)
    assert res.feature == "calibrated_posterior_p"
    assert res.psi is not None
    assert res.psi > 0.10
    assert res.wasserstein_distance is not None
    assert res.wasserstein_distance > 0.0


def test_missing_and_nonfinite_inputs(monitor, rng):
    """Handles missing, NaN, Inf, and zero-variance inputs safely without crashing."""
    ref = np.array([np.nan, np.inf, -np.inf, 1.0, 2.0, 3.0, np.nan])
    act = np.array([1.0, 2.0, 3.0, 4.0, np.nan, np.nan])

    res = monitor.compute_feature_drift(ref, act, feature_name="test_nonfinite")
    assert res.feature == "test_nonfinite"
    assert res.ref_sample_count == 3
    assert res.act_sample_count == 4
    assert res.ref_missing_rate > 0.0
    assert res.act_missing_rate > 0.0

    # Constant distribution fallback
    const_ref = np.ones(100)
    const_act = np.ones(100)
    res_const = monitor.compute_feature_drift(const_ref, const_act, feature_name="constant_feat")
    assert res_const.psi is not None
    assert res_const.drift_category == "stable"


def test_drift_monitor_ground_truth_quarantine(monitor, rng):
    """Attempting to include isFraud, target, or TransactionID in monitored features raises LeakageViolationError."""
    df_ref = pd.DataFrame({
        "TransactionAmt": rng.uniform(10, 100, size=100),
        "isFraud": [0] * 100,
        "TransactionID": list(range(100)),
    })
    df_act = df_ref.copy()

    with pytest.raises(LeakageViolationError) as exc_info:
        monitor.compute_drift_report(
            df_ref, df_act, features=["TransactionAmt", "isFraud"]
        )
    assert "isFraud" in str(exc_info.value)

    with pytest.raises(LeakageViolationError) as exc_info2:
        monitor.compute_feature_drift(df_ref["isFraud"], df_act["isFraud"], feature_name="isFraud")
    assert "isFraud" in str(exc_info2.value)


def test_drift_report_provenance_and_notice(monitor, rng):
    """Drift report contains valid SHA-256 provenance hash and non-negotiable discipline notice."""
    df_ref = pd.DataFrame({"V1": rng.normal(0, 1, size=100), "V2": rng.normal(0, 1, size=100)})
    df_act = pd.DataFrame({"V1": rng.normal(0, 1, size=100), "V2": rng.normal(0, 1, size=100)})

    report = monitor.compute_drift_report(
        df_ref, df_act, features=["V1", "V2"],
        reference_window_id="train_baseline",
        comparison_window_id="val_window",
    )

    assert len(report.provenance_hash) == 64
    assert report.features_monitored == 2
    assert "not constitute proof of fraud" in report.notice


# ==============================================================================
# 2. Advisory Drift Sentinel Tests (DRFT-02)
# ==============================================================================

def test_sentinel_no_drift_no_proposal(sentinel, monitor, base_policy, rng):
    """Stable distributions trigger no adaptation proposal from Sentinel."""
    df_ref = pd.DataFrame({"V1": rng.normal(0, 1, size=200)})
    df_act = pd.DataFrame({"V1": rng.normal(0, 1, size=200)})

    report = monitor.compute_drift_report(df_ref, df_act, features=["V1"])
    proposal = sentinel.evaluate_drift(report, current_policy=base_policy)
    assert proposal is None


def test_sentinel_generates_advisory_proposal_on_drift(sentinel, monitor, base_policy, rng):
    """Significant drift triggers valid advisory proposal with base_cfg_hash matching active policy."""
    df_ref = pd.DataFrame({"V1": rng.normal(0, 1, size=500)})
    df_act = pd.DataFrame({"V1": rng.normal(3.0, 1.0, size=500)})  # severe drift

    report = monitor.compute_drift_report(df_ref, df_act, features=["V1"])
    proposal = sentinel.evaluate_drift(report, current_policy=base_policy)

    assert proposal is not None
    assert isinstance(proposal, Proposal)
    assert proposal.base_cfg_hash == base_policy.compute_cfg_hash()
    assert len(proposal.changes) > 0
    # All proposed keys must belong to allowlisted set
    for k in proposal.changes:
        assert k in ALLOWLISTED_POLICY_KEYS
    assert "Advisory adaptation proposed" in proposal.rationale


def test_sentinel_rejects_forbidden_keys(sentinel, base_policy):
    """Attempting to propose forbidden keys (e.g. model_weights, raw_features) fails validation."""
    forbidden_changes = {
        "model_weights": [0.1, 0.2, 0.3],
        "t_review": 0.05,
    }
    is_valid, err = sentinel.validate_proposal_changes(forbidden_changes, current_policy=base_policy)
    assert not is_valid
    assert "unapproved/prohibited keys" in err


def test_sentinel_parameter_bounds_enforcement(sentinel, base_policy):
    """Proposing out-of-bounds parameters or invalid ordering (t_review >= t_alert) fails validation."""
    # Out of bounds
    out_of_bounds = {"t_review": 1.5}
    is_valid, err = sentinel.validate_proposal_changes(out_of_bounds, current_policy=base_policy)
    assert not is_valid
    assert "outside allowed bounds" in err

    # Invalid ordering: t_review >= t_alert (base t_alert is ~0.0847)
    invalid_ordering = {"t_review": 0.090}
    is_valid2, err2 = sentinel.validate_proposal_changes(invalid_ordering, current_policy=base_policy)
    assert not is_valid2
    assert "t_review" in err2 and "must be < t_alert" in err2


# ==============================================================================
# 3. Deterministic Replay Gate Tests (DRFT-03)
# ==============================================================================

def test_replay_gate_validation_replay_success(replay_gate, base_policy, rng):
    """Valid proposal replays deterministically on validation partition and enters AWAITING_HUMAN_APPROVAL."""
    # Construct small synthetic validation cases
    val_cases = [
        {"p": 0.02, "u": 0.10},
        {"p": 0.075, "u": 0.15},  # borderline between old t_review (0.071) and alert (0.084)
        {"p": 0.09, "u": 0.20},   # alert
        {"p": 0.01, "u": 0.60},   # high disagreement
    ]

    proposal = Proposal(
        proposal_id="prop_test_001",
        base_cfg_hash=base_policy.compute_cfg_hash(),
        changes={"t_review": 0.065},  # lower review threshold
        rationale="Lower review threshold to evaluate borderline cases",
    )

    result, status = replay_gate.validate_and_replay(
        proposal=proposal,
        current_policy=base_policy,
        validation_data=val_cases,
        scenario_id="val_slice",
    )

    assert result.is_valid
    assert result.replay_executed
    assert result.validation_samples == 4
    # State transition must be AWAITING_HUMAN_APPROVAL (never automatic activation!)
    assert status == ProposalStatus.AWAITING_HUMAN_APPROVAL
    assert replay_gate.proposal_states[proposal.proposal_id] == ProposalStatus.AWAITING_HUMAN_APPROVAL


def test_replay_gate_test_partition_quarantine(replay_gate, base_policy):
    """Attempting to pass test partition to replay gate raises GroundTruthQuarantineError."""
    proposal = Proposal(
        proposal_id="prop_test_quarantine",
        base_cfg_hash=base_policy.compute_cfg_hash(),
        changes={"t_review": 0.065},
        rationale="Attempted replay on held-out test data",
    )

    with pytest.raises(GroundTruthQuarantineError) as exc_info:
        replay_gate.validate_and_replay(
            proposal=proposal,
            current_policy=base_policy,
            validation_data=[{"p": 0.05, "u": 0.1}],
            scenario_id="test",  # Forbidden!
        )
    assert "quarantined" in str(exc_info.value).lower() or "strictly prohibits" in str(exc_info.value).lower()


def test_replay_gate_hash_mismatch_rejection(replay_gate, base_policy):
    """Proposal with mismatched base_cfg_hash fails validation immediately."""
    proposal = Proposal(
        proposal_id="prop_mismatch",
        base_cfg_hash="a" * 64,  # invalid/stale configuration hash
        changes={"t_review": 0.065},
        rationale="Stale proposal based on previous config",
    )

    result, status = replay_gate.validate_and_replay(
        proposal=proposal,
        current_policy=base_policy,
        validation_data=[{"p": 0.05, "u": 0.1}],
        scenario_id="validation",
    )

    assert not result.is_valid
    assert not result.base_cfg_hash_matches
    assert status == ProposalStatus.FAILED_VALIDATION
    assert "mismatch" in result.rejection_reason.lower()


def test_replay_gate_explicit_human_approval(replay_gate, base_policy):
    """Proposal in AWAITING_HUMAN_APPROVAL transitions to APPROVED only on explicit human call with valid approver ID."""
    proposal = Proposal(
        proposal_id="prop_to_approve",
        base_cfg_hash=base_policy.compute_cfg_hash(),
        changes={"t_review": 0.068},
        rationale="Fine-tune review threshold",
    )

    replay_gate.validate_and_replay(
        proposal=proposal,
        current_policy=base_policy,
        validation_data=[{"p": 0.05, "u": 0.1}],
    )

    # Empty approver ID must raise error
    with pytest.raises(ValueError):
        replay_gate.approve_proposal(
            proposal_id=proposal.proposal_id,
            approver="",
            rationale="Approved without approver id",
        )

    # Valid human approval
    audit_chain = AuditChain(secret_key="test_key_for_replay_gate_123456")
    approval_res = replay_gate.approve_proposal(
        proposal_id=proposal.proposal_id,
        approver="lead_risk_officer@signalgate.org",
        rationale="Validated against Q3 validation holdout; touched rate within 1.1x SLA.",
        audit_chain=audit_chain,
    )

    assert approval_res["status"] == "APPROVED"
    assert approval_res["approver"] == "lead_risk_officer@signalgate.org"
    assert approval_res["audit_seq"] is not None
    assert replay_gate.proposal_states[proposal.proposal_id] == ProposalStatus.APPROVED

    # Audit chain must reflect the approval event
    assert len(audit_chain) == 1
    assert audit_chain[-1].id == f"gate_approval_{proposal.proposal_id}"


def test_replay_gate_rejection_leaves_policy_intact(replay_gate, base_policy):
    """Rejection transitions proposal to REJECTED, leaving current policy untouched."""
    proposal = Proposal(
        proposal_id="prop_to_reject",
        base_cfg_hash=base_policy.compute_cfg_hash(),
        changes={"t_review": 0.068},
        rationale="Aggressive threshold change",
    )

    replay_gate.validate_and_replay(
        proposal=proposal,
        current_policy=base_policy,
        validation_data=[{"p": 0.05, "u": 0.1}],
    )

    reject_res = replay_gate.reject_proposal(
        proposal_id=proposal.proposal_id,
        reviewer="risk_committee@signalgate.org",
        reason="Exceeds churn tolerance on borderline cohort.",
    )

    assert reject_res["status"] == "REJECTED"
    assert replay_gate.proposal_states[proposal.proposal_id] == ProposalStatus.REJECTED


def test_end_to_end_drift_to_replay_lifecycle(monitor, sentinel, replay_gate, base_policy, rng):
    """End-to-end flow from feature drift detection -> sentinel proposal -> replay gate validation -> human approval -> audit record."""
    # 1. Simulate severe feature drift in comparison dataset
    ref_df = pd.DataFrame({"V1": rng.normal(0, 1, size=400), "V2": rng.normal(0, 1, size=400)})
    act_df = pd.DataFrame({"V1": rng.normal(2.5, 1, size=400), "V2": rng.normal(2.5, 1, size=400)})

    report = monitor.compute_drift_report(
        ref_df, act_df, features=["V1", "V2"],
        reference_window_id="ref_train", comparison_window_id="act_val"
    )
    assert report.significant_drift_features >= 1

    # 2. Sentinel observes drift and emits advisory Proposal
    proposal = sentinel.evaluate_drift(report, current_policy=base_policy)
    assert proposal is not None

    # 3. Replay Gate deterministically replays on validation cases
    val_data = [{"p": 0.07, "u": 0.1}, {"p": 0.08, "u": 0.2}, {"p": 0.02, "u": 0.05}]
    result, status = replay_gate.validate_and_replay(
        proposal=proposal,
        current_policy=base_policy,
        validation_data=val_data,
        scenario_id="val_e2e",
    )
    assert result.is_valid
    assert status == ProposalStatus.AWAITING_HUMAN_APPROVAL

    # 4. Human risk officer reviews replay metrics and authorizes adaptation
    audit_chain = AuditChain(secret_key="e2e_secret_key_signalgate_123456")
    approval = replay_gate.approve_proposal(
        proposal_id=proposal.proposal_id,
        approver="compliance_lead@signalgate.org",
        rationale="Approved after verifying replay touched rate stability on validation cohort.",
        audit_chain=audit_chain,
    )
    assert approval["status"] == "APPROVED"
    assert replay_gate.proposal_states[proposal.proposal_id] == ProposalStatus.APPROVED
    assert len(audit_chain) == 1
    assert audit_chain[-1].id == f"gate_approval_{proposal.proposal_id}"
