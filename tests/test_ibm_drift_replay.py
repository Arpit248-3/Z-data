"""Unit and integration tests for Phase 7: Drift Monitoring and Controlled Scenario Replay.

Verifies:
1. DistributionDriftCalculator calculates PSI and KS without ground-truth labels.
2. Ground-truth and key quarantine enforcement prevents leakage of isFraud, TransactionID, TransactionDT.
3. DriftSentinel generates typed proposals for allowlisted keys and fails closed on provider error.
4. ReplayGate deterministically validates proposals, enforces AWAITING_HUMAN_APPROVAL,
   and requires explicit human sign-off before operational activation.
"""

from datetime import datetime, timezone
import hashlib
import numpy as np
import pandas as pd
import pytest

from integrations.ibm_architecture.contracts import Proposal
from integrations.ibm_architecture.exceptions import GroundTruthQuarantineError
from integrations.ibm_architecture.monitoring import (
    ALLOWLISTED_CONFIG_KEYS,
    DistributionDriftCalculator,
    DriftSentinel,
    ReplayEvaluationRecord,
    ReplayGate,
    calculate_feature_drift,
    calculate_psi,
)

FROZEN_BASE_CFG_HASH = hashlib.sha256(b'{"budget":{"primary_multiple":1.5}}').hexdigest()


@pytest.fixture
def baseline_sample() -> pd.DataFrame:
    """Deterministic baseline feature sample (1,000 cases)."""
    np.random.seed(42)
    return pd.DataFrame({
        "TransactionAmt": np.random.exponential(scale=100.0, size=1000),
        "card1": np.random.uniform(1000, 20000, size=1000),
        "dist1": np.random.gamma(shape=2.0, scale=10.0, size=1000),
        "C1": np.random.poisson(lam=2.0, size=1000),
    })


@pytest.fixture
def shifted_sample() -> pd.DataFrame:
    """Deterministic shifted feature sample with covariate drift on TransactionAmt and C1."""
    np.random.seed(99)
    return pd.DataFrame({
        "TransactionAmt": np.random.exponential(scale=350.0, size=1000),  # Heavy shift
        "card1": np.random.uniform(1000, 20000, size=1000),               # Stable
        "dist1": np.random.gamma(shape=2.0, scale=10.0, size=1000),       # Stable
        "C1": np.random.poisson(lam=8.0, size=1000),                       # Moderate shift
    })


def test_psi_calculation_stable_and_drift() -> None:
    """Verify PSI calculation for stable vs shifted distributions."""
    np.random.seed(123)
    ref = np.random.normal(loc=0.0, scale=1.0, size=2000)
    identical = np.random.normal(loc=0.0, scale=1.0, size=2000)
    shifted = np.random.normal(loc=1.5, scale=1.5, size=2000)

    # Identical distribution should be stable (PSI < 0.10)
    res_stable = calculate_psi(ref, identical)
    assert res_stable["psi"] is not None
    assert res_stable["psi"] < 0.10
    assert res_stable["category"] == "stable"

    # Shifted distribution should be significant drift (PSI > 0.20)
    res_shifted = calculate_psi(ref, shifted)
    assert res_shifted["psi"] is not None
    assert res_shifted["psi"] > 0.20
    assert res_shifted["category"] == "significant_drift"


def test_feature_drift_ks_and_psi(baseline_sample: pd.DataFrame, shifted_sample: pd.DataFrame) -> None:
    """Verify combined PSI and two-sample KS test on a shifted feature."""
    res = calculate_feature_drift(
        reference=baseline_sample["TransactionAmt"],
        actual=shifted_sample["TransactionAmt"],
        feature_name="TransactionAmt",
    )
    assert res["feature"] == "TransactionAmt"
    assert res["psi"] is not None
    assert res["ks_statistic"] is not None
    assert res["ks_pvalue"] is not None
    assert res["ks_pvalue"] < 1e-4  # Highly significant KS shift
    assert res["drift_category"] in ("moderate_drift", "significant_drift")


def test_drift_calculator_quarantine_enforcement(baseline_sample: pd.DataFrame) -> None:
    """Verify drift calculator rejects isFraud, TransactionID, or TransactionDT."""
    calc = DistributionDriftCalculator()

    # Attempting to monitor isFraud must raise GroundTruthQuarantineError
    with pytest.raises(GroundTruthQuarantineError):
        calc.compute_drift(
            reference_df=baseline_sample,
            comparison_df=baseline_sample,
            features=["TransactionAmt", "isFraud"],
        )

    # Attempting to monitor TransactionID must raise GroundTruthQuarantineError
    with pytest.raises(GroundTruthQuarantineError):
        calc.compute_drift(
            reference_df=baseline_sample,
            comparison_df=baseline_sample,
            features=["TransactionID"],
        )

    # Attempting to monitor TransactionDT must raise GroundTruthQuarantineError
    with pytest.raises(GroundTruthQuarantineError):
        calc.compute_drift(
            reference_df=baseline_sample,
            comparison_df=baseline_sample,
            features=["TransactionDT"],
        )


def test_drift_calculator_synthetic_mode_telemetry(
    baseline_sample: pd.DataFrame, shifted_sample: pd.DataFrame
) -> None:
    """Verify drift summary reports explicit SYNTHETIC_SMOKE_ONLY status and deferred benchmark."""
    calc = DistributionDriftCalculator()
    summary = calc.compute_drift(
        reference_df=baseline_sample,
        comparison_df=shifted_sample,
        features=["TransactionAmt", "card1", "dist1", "C1"],
        scenario_id="S1_COVARIATE_SHIFT",
        mode="SYNTHETIC_SMOKE_ONLY",
    )

    assert summary["status"] == "SYNTHETIC_SMOKE_ONLY"
    assert summary["scenario_id"] == "S1_COVARIATE_SHIFT"
    assert summary["real_data_benchmark_status"] == "DEFERRED"
    assert summary["overall_drift_detected"] is True
    assert "TransactionAmt" in summary["significant_shift_features"]
    assert len(summary["feature_drift_reports"]) == 4


def test_drift_sentinel_offline_proposal_generation(
    baseline_sample: pd.DataFrame, shifted_sample: pd.DataFrame
) -> None:
    """Verify DriftSentinel produces an advisory Proposal when drift is detected."""
    calc = DistributionDriftCalculator()
    summary = calc.compute_drift(
        reference_df=baseline_sample,
        comparison_df=shifted_sample,
        features=["TransactionAmt", "card1"],
        scenario_id="S1_COVARIATE_SHIFT",
    )

    sentinel = DriftSentinel()
    proposal = sentinel.evaluate_and_propose(summary, base_cfg_hash=FROZEN_BASE_CFG_HASH)

    assert proposal is not None
    assert isinstance(proposal, Proposal)
    assert proposal.base_cfg_hash == FROZEN_BASE_CFG_HASH
    assert "budget.primary_multiple" in proposal.changes
    assert proposal.changes["budget.primary_multiple"] == 2.0
    for k in proposal.changes.keys():
        assert k in ALLOWLISTED_CONFIG_KEYS


def test_drift_sentinel_returns_none_when_no_drift(baseline_sample: pd.DataFrame) -> None:
    """Verify DriftSentinel emits no proposal when distribution is stable."""
    calc = DistributionDriftCalculator()
    # Baseline vs self has zero drift
    summary = calc.compute_drift(
        reference_df=baseline_sample,
        comparison_df=baseline_sample,
        features=["card1"],
        scenario_id="S0_BASELINE",
    )

    sentinel = DriftSentinel()
    proposal = sentinel.evaluate_and_propose(summary, base_cfg_hash=FROZEN_BASE_CFG_HASH)
    assert proposal is None


def test_drift_sentinel_fail_closed_on_provider_error(
    baseline_sample: pd.DataFrame, shifted_sample: pd.DataFrame
) -> None:
    """Verify DriftSentinel fails closed if external provider throws an exception."""
    calc = DistributionDriftCalculator()
    summary = calc.compute_drift(
        reference_df=baseline_sample,
        comparison_df=shifted_sample,
        features=["TransactionAmt"],
    )

    def failing_provider(s: dict) -> Proposal:
        raise ConnectionError("Simulated LLM API timeout")

    sentinel = DriftSentinel(llm_provider=failing_provider)
    proposal = sentinel.evaluate_and_propose(summary, base_cfg_hash=FROZEN_BASE_CFG_HASH)
    assert proposal is None


def test_replay_gate_validation_and_human_approval_lifecycle() -> None:
    """Verify ReplayGate workflow from validation to AWAITING_HUMAN_APPROVAL to APPROVED_ACTIVE."""
    gate = ReplayGate(frozen_cfg_hash=FROZEN_BASE_CFG_HASH)

    proposal = Proposal(
        proposal_id="prop_001",
        base_cfg_hash=FROZEN_BASE_CFG_HASH,
        changes={"budget.primary_multiple": 2.0},
        rationale="Compensate for covariate drift by raising budget quota",
        created_at=datetime.now(timezone.utc),
    )

    # 1. Validation and replay leaves status in AWAITING_HUMAN_APPROVAL
    record = gate.validate_and_replay(proposal)
    assert record.status == "AWAITING_HUMAN_APPROVAL"
    assert record.schema_valid is True
    assert record.hash_matched is True
    assert record.keys_valid is True
    assert record.validation_passed is True
    assert record.workload_constraint_passed is True
    assert record.approved_by is None
    assert record.approval_timestamp is None
    assert len(record.rejection_reasons) == 0

    # 2. Human approval transitions to APPROVED_ACTIVE
    approved_record = gate.approve(record, approver="RiskOfficer_Arpit")
    assert approved_record.status == "APPROVED_ACTIVE"
    assert approved_record.approved_by == "RiskOfficer_Arpit"
    assert approved_record.approval_timestamp is not None
    assert approved_record.record_hash == approved_record.compute_record_hash()


def test_replay_gate_rejects_mismatched_base_hash() -> None:
    """Verify ReplayGate rejects proposals targeting an outdated configuration hash."""
    gate = ReplayGate(frozen_cfg_hash=FROZEN_BASE_CFG_HASH)
    wrong_hash = "f" * 64

    proposal = Proposal(
        proposal_id="prop_stale",
        base_cfg_hash=wrong_hash,
        changes={"budget.primary_multiple": 2.0},
        rationale="Stale proposal against obsolete hash",
        created_at=datetime.now(timezone.utc),
    )

    record = gate.validate_and_replay(proposal)
    assert record.status == "REJECTED"
    assert record.hash_matched is False
    assert record.validation_passed is False
    assert any("hash mismatch" in r.lower() for r in record.rejection_reasons)


def test_replay_gate_rejects_excessive_workload_multiple() -> None:
    """Verify ReplayGate enforces upper boundary on workload multiple (e.g. max 3.0x)."""
    gate = ReplayGate(frozen_cfg_hash=FROZEN_BASE_CFG_HASH, max_workload_multiple=3.0)

    proposal = Proposal(
        proposal_id="prop_greedy",
        base_cfg_hash=FROZEN_BASE_CFG_HASH,
        changes={"budget.primary_multiple": 5.0},  # Exceeds max 3.0
        rationale="Unbounded budget request",
        created_at=datetime.now(timezone.utc),
    )

    record = gate.validate_and_replay(proposal)
    assert record.status == "REJECTED"
    assert record.workload_constraint_passed is False
    assert any("exceeds boundary" in r.lower() for r in record.rejection_reasons)


def test_replay_gate_human_rejection() -> None:
    """Verify ReplayGate human rejection workflow."""
    gate = ReplayGate(frozen_cfg_hash=FROZEN_BASE_CFG_HASH)

    proposal = Proposal(
        proposal_id="prop_002",
        base_cfg_hash=FROZEN_BASE_CFG_HASH,
        changes={"budget.primary_multiple": 2.5},
        rationale="Elevate review budget",
        created_at=datetime.now(timezone.utc),
    )

    record = gate.validate_and_replay(proposal)
    assert record.status == "AWAITING_HUMAN_APPROVAL"

    rejected_record = gate.reject(record, reviewer="RiskCommittee_Lead", reason="Budget limit frozen for Q4")
    assert rejected_record.status == "REJECTED"
    assert any("Budget limit frozen for Q4" in r for r in rejected_record.rejection_reasons)
