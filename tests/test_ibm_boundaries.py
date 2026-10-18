"""Tests for SignalGate IBM Architecture Integration Boundaries (Phase 2).

Validates:
1. Namespace isolation and clean imports.
2. Strict EvidenceMode resolution and fail-closed readiness gates.
3. Ground-truth quarantine enforcement on AgentCaseView (rejection of isFraud, TransactionID, TransactionDT).
4. Cryptographic integrity of AuditRecord sealing and timezone requirements.
5. Immutability and serialization of Claim, AgentRecord, and Proposal contracts.
"""

from datetime import datetime, timezone
import pytest
from pydantic import ValidationError

from integrations.ibm_architecture import (
    Action,
    ReasonCode,
    AuditRecord,
    Claim,
    AgentRecord,
    Proposal,
    ModelArtifactManifest,
    AgentCaseView,
    AgentView,
    EvidenceMode,
    ModeReadiness,
    ModeState,
    ModeRegistry,
    mode_registry,
    LeakageViolationError,
    GroundTruthQuarantineError,
    ModeUnavailableError,
    ZERO_HASH,
)


# =============================================================================
# 1. Namespace & Import Tests
# =============================================================================
def test_isolated_namespace_imports_without_side_effects():
    """Verify integrations.ibm_architecture is cleanly importable without polluting root modules."""
    import integrations.ibm_architecture as ibm
    assert hasattr(ibm, "__version__")
    assert ibm.__version__ == "1.0.0"
    assert "EvidenceMode" in ibm.__all__
    assert "AgentCaseView" in ibm.__all__
    assert "mode_registry" in ibm.__all__


# =============================================================================
# 2. Evidence Mode Resolution & Fail-Closed Registry Tests
# =============================================================================
def test_evidence_mode_resolution_synthetic_smoke():
    """SYNTHETIC_SMOKE_ONLY must resolve to READY and available."""
    state = mode_registry.resolve_mode(EvidenceMode.SYNTHETIC_SMOKE_ONLY)
    assert state.mode == EvidenceMode.SYNTHETIC_SMOKE_ONLY
    assert state.available is True
    assert state.readiness == ModeReadiness.READY
    assert state.prerequisites_met is True
    assert len(state.missing_prerequisites) == 0

    # assert_mode_ready should succeed without exception
    assert_state = mode_registry.assert_mode_ready(EvidenceMode.SYNTHETIC_SMOKE_ONLY)
    assert assert_state.available is True


def test_evidence_mode_resolution_ieee_cis_fails_closed_when_data_missing(tmp_path):
    """IEEE_CIS_OFFLINE_BENCHMARK must fail closed when raw CSVs are missing."""
    empty_registry = ModeRegistry(project_root=tmp_path)
    state = empty_registry.resolve_mode(EvidenceMode.IEEE_CIS_OFFLINE_BENCHMARK)
    assert state.mode == EvidenceMode.IEEE_CIS_OFFLINE_BENCHMARK
    assert state.available is False
    assert state.readiness == ModeReadiness.UNAVAILABLE_MISSING_RAW_DATA
    assert state.prerequisites_met is False
    assert len(state.missing_prerequisites) > 0
    assert any("train_transaction.csv" in p for p in state.missing_prerequisites)

    # Calling assert_mode_ready MUST raise ModeUnavailableError (fail-closed, no synthetic fallback)
    with pytest.raises(ModeUnavailableError) as exc_info:
        empty_registry.assert_mode_ready(EvidenceMode.IEEE_CIS_OFFLINE_BENCHMARK)

    err = exc_info.value
    assert err.mode == EvidenceMode.IEEE_CIS_OFFLINE_BENCHMARK.value
    assert "Missing prerequisites" in str(err)
    assert len(err.missing_prerequisites) > 0


def test_evidence_mode_resolution_ieee_cis_ready_when_data_present():
    """IEEE_CIS_OFFLINE_BENCHMARK resolves to READY when raw CSVs are verified on disk."""
    state = mode_registry.resolve_mode(EvidenceMode.IEEE_CIS_OFFLINE_BENCHMARK)
    assert state.mode == EvidenceMode.IEEE_CIS_OFFLINE_BENCHMARK
    assert state.available is True
    assert state.readiness == ModeReadiness.READY
    assert state.prerequisites_met is True
    assert len(state.missing_prerequisites) == 0
    # Must not raise ModeUnavailableError
    mode_registry.assert_mode_ready(EvidenceMode.IEEE_CIS_OFFLINE_BENCHMARK)


def test_evidence_mode_resolution_live_source_disconnected():
    """LIVE_SOURCE_NOT_CONNECTED must explicitly report disconnected status."""
    state = mode_registry.resolve_mode(EvidenceMode.LIVE_SOURCE_NOT_CONNECTED)
    assert state.mode == EvidenceMode.LIVE_SOURCE_NOT_CONNECTED
    assert state.available is False
    assert state.readiness == ModeReadiness.NOT_CONNECTED

    with pytest.raises(ModeUnavailableError):
        mode_registry.assert_mode_ready(EvidenceMode.LIVE_SOURCE_NOT_CONNECTED)


def test_mode_registry_get_all_modes():
    """Verify registry returns all three specified evidence modes."""
    all_modes = mode_registry.get_all_modes()
    assert len(all_modes) == 3
    assert EvidenceMode.SYNTHETIC_SMOKE_ONLY in all_modes
    assert EvidenceMode.IEEE_CIS_OFFLINE_BENCHMARK in all_modes
    assert EvidenceMode.LIVE_SOURCE_NOT_CONNECTED in all_modes


# =============================================================================
# 3. AuditRecord & Cryptographic Sealing Tests
# =============================================================================
def test_audit_record_creation_and_sealing():
    """AuditRecord must validate SHA256 fields and seal with deterministic hash."""
    rec = AuditRecord(
        id="case_boundary_001",
        seq=1,
        p=0.88,
        u=-0.04,
        u2=-0.04,
        n=0.01,
        action="FRAUD_ALERT",
        reason="R1_HIGH_RISK",
        cfg_hash="8d3f02ca492ca94bab45f3ceac8d39432c2f29f40d54e7990b4aa78cbbff6240",
        split_hash="07b55a4ed74f238c9ef5b779a749770cf274d4709a4389d9eab860dd9068fbdd",
    )
    assert rec.record_hash == ZERO_HASH
    rec.seal()
    assert rec.record_hash != ZERO_HASH
    assert len(rec.record_hash) == 64
    assert rec.compute_record_hash() == rec.record_hash


def test_audit_record_requires_timezone_aware_timestamp():
    """AuditRecord must reject naive datetimes without timezone."""
    naive_dt = datetime(2026, 10, 18, 12, 0, 0)
    with pytest.raises(ValidationError):
        AuditRecord(
            id="case_naive",
            timestamp=naive_dt,
            action="ROUTINE",
            reason="R5_LOW_RISK_RELIABLE",
            cfg_hash="8d3f02ca492ca94bab45f3ceac8d39432c2f29f40d54e7990b4aa78cbbff6240",
            split_hash="07b55a4ed74f238c9ef5b779a749770cf274d4709a4389d9eab860dd9068fbdd",
        )


# =============================================================================
# 4. Ground-Truth Quarantine & AgentCaseView Tests
# =============================================================================
def test_agent_case_view_from_audit_record_success():
    """AgentCaseView must construct successfully from a sealed AuditRecord."""
    rec = AuditRecord(
        id="audit_case_005",
        p=0.33,
        u=0.15,
        u2=0.15,
        action="MANUAL_REVIEW",
        reason="R3_MODEL_DISAGREEMENT",
        cfg_hash="8d3f02ca492ca94bab45f3ceac8d39432c2f29f40d54e7990b4aa78cbbff6240",
        split_hash="07b55a4ed74f238c9ef5b779a749770cf274d4709a4389d9eab860dd9068fbdd",
    ).seal()

    view = AgentCaseView.from_audit_record(rec)
    assert view.record_id == "audit_case_005"
    assert view.p == 0.33
    assert view.u == 0.15
    assert view.action == "MANUAL_REVIEW"
    assert view.reason == "R3_MODEL_DISAGREEMENT"
    assert view.record_hash == rec.record_hash


def test_agent_case_view_rejects_isfraud_leakage():
    """AgentCaseView must raise LeakageViolationError if isFraud is passed."""
    valid_hashes = {
        "record_id": "test_case",
        "p": 0.5,
        "action": "ROUTINE",
        "reason": "R5_LOW_RISK_RELIABLE",
        "record_hash": "a" * 64,
        "cfg_hash": "b" * 64,
        "split_hash": "c" * 64,
    }

    # Direct keyword instantiation
    with pytest.raises(LeakageViolationError) as exc_info:
        AgentCaseView(**valid_hashes, isFraud=1)
    assert "isFraud" in exc_info.value.violated_fields

    # Lowercase variant
    with pytest.raises(LeakageViolationError) as exc_info:
        AgentCaseView(**valid_hashes, isfraud=0)
    assert "isfraud" in exc_info.value.violated_fields


def test_agent_case_view_rejects_transaction_identifiers_leakage():
    """AgentCaseView must raise LeakageViolationError if TransactionID or TransactionDT is passed."""
    valid_hashes = {
        "record_id": "test_case",
        "p": 0.5,
        "action": "ROUTINE",
        "reason": "R5_LOW_RISK_RELIABLE",
        "record_hash": "a" * 64,
        "cfg_hash": "b" * 64,
        "split_hash": "c" * 64,
    }

    with pytest.raises(LeakageViolationError) as exc_info:
        AgentCaseView(**valid_hashes, TransactionID=2990001)
    assert "TransactionID" in exc_info.value.violated_fields

    with pytest.raises(LeakageViolationError) as exc_info:
        AgentCaseView(**valid_hashes, TransactionDT=86400)
    assert "TransactionDT" in exc_info.value.violated_fields


def test_agent_case_view_forbids_extra_arbitrary_fields():
    """AgentCaseView must forbid arbitrary extra fields to prevent covert channel leakage."""
    valid_hashes = {
        "record_id": "test_case",
        "p": 0.5,
        "action": "ROUTINE",
        "reason": "R5_LOW_RISK_RELIABLE",
        "record_hash": "a" * 64,
        "cfg_hash": "b" * 64,
        "split_hash": "c" * 64,
    }

    with pytest.raises(ValidationError):
        AgentCaseView(**valid_hashes, arbitrary_extra_feature=42.0)


def test_agent_view_container_immutable():
    """AgentView container must hold immutable tuples of AgentCaseViews."""
    rec = AuditRecord(
        id="case_tup_01",
        p=0.1,
        action="ROUTINE",
        reason="R5_LOW_RISK_RELIABLE",
        cfg_hash="8d3f02ca492ca94bab45f3ceac8d39432c2f29f40d54e7990b4aa78cbbff6240",
        split_hash="07b55a4ed74f238c9ef5b779a749770cf274d4709a4389d9eab860dd9068fbdd",
    ).seal()

    view = AgentView.from_audit_records([rec])
    assert len(view.cases) == 1
    assert len(view.records) == 1
    assert isinstance(view.cases, tuple)


# =============================================================================
# 5. Claim and Proposal Tests
# =============================================================================
def test_claim_verification_contract():
    """Claim contract must validate comparison operators and immutability."""
    c = Claim(
        field="p",
        operator="gt",
        value=0.5,
        template_id="high_risk_claim_v1",
    )
    assert c.field == "p"
    assert c.operator == "gt"

    with pytest.raises(ValidationError):
        # Invalid operator
        Claim(field="p", operator="invalid_op", value=0.5, template_id="bad")


def test_proposal_advisory_contract():
    """Proposal contract must require timezone-aware timestamp and valid base hash."""
    prop = Proposal(
        proposal_id="prop_001",
        base_cfg_hash="8d3f02ca492ca94bab45f3ceac8d39432c2f29f40d54e7990b4aa78cbbff6240",
        changes={"t_review": 0.075},
        rationale="Shift storm observed in cluster C2 warrants tighter review cutoff.",
    )
    assert prop.proposal_id == "prop_001"
    assert prop.created_at.tzinfo is not None
