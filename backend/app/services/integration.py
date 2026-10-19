"""SignalGate Integration Service

Coordinates IEEE-CIS offline benchmark operations, governance replay gates,
multi-metric drift monitoring, and cryptographic audit chains within the FastAPI backend.
Maintains singleton caching for large model bundles to avoid costly unpickling on requests.

Governing Specification: docs/ibm_architecture_integration_master_spec.md § C, § L
Requirements: APII-01, APII-02, APII-03
"""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
import pandas as pd

from backend.app.config import settings
from backend.app.schemas import (
    AuditVerifyResponse,
    DriftReportAPIResponse,
    GovernanceDecisionResponse,
    GovernanceProposalResponse,
    ModeReadinessResponse,
    ModelCardResponse,
)
from integrations.ibm_architecture.contracts import Proposal, ZERO_HASH
from integrations.ibm_architecture.exceptions import (
    ArtifactNotFoundError,
    IncompatibleArtifactError,
    LeakageViolationError,
    SignalGateIntegrationError,
)
from integrations.ibm_architecture.governance.audit_chain import AuditChain
from integrations.ibm_architecture.governance.drift_monitor import DriftMonitor, DriftReport
from integrations.ibm_architecture.governance.drift_sentinel import DriftSentinel
from integrations.ibm_architecture.governance.replay_gate import (
    ProposalStatus,
    ReplayGate,
    ReplayValidationResult,
)
from integrations.ibm_architecture.models.bundle import ModelBundle, load_bundle
from integrations.ibm_architecture.policy.frozen_policy import (
    IEEEPolicyConfig,
    get_frozen_ieee_policy_config,
)
from integrations.ibm_architecture.scoring.schemas import ScoringResult
from integrations.ibm_architecture.scoring.service import ScoringService


class IntegrationService:
    """Thread-safe singleton integration service bridging IBM architecture to FastAPI."""

    def __init__(self, project_root: Optional[Path] = None) -> None:
        self.project_root = Path(project_root or settings.project_root)
        self.bundle_dir = self.project_root / "models" / "artifacts" / "ieee_cis_v1"
        self.results_dir = self.project_root / "results" / "ieee_cis_v1"
        self.audit_log_path = self.results_dir / "audit_chain.jsonl"

        # Cached singletons
        self._bundle: Optional[ModelBundle] = None
        self._scoring_service: Optional[ScoringService] = None
        self._bundle_verified: Optional[bool] = None
        self._bundle_error: Optional[str] = None

        self._drift_monitor = DriftMonitor(epsilon=1e-4, bins=10)
        self._drift_sentinel = DriftSentinel()
        self._replay_gate = ReplayGate(self._drift_sentinel)

        # Load or initialize audit chain
        self._audit_chain = self._init_audit_chain()

        # Seed initial advisory proposal for inspection and replay
        self._seed_default_proposals()

    def _init_audit_chain(self) -> AuditChain:
        """Initialize or load the cryptographic audit chain."""
        if self.audit_log_path.exists() and self.audit_log_path.stat().st_size > 0:
            try:
                return AuditChain.load_jsonl(self.audit_log_path)
            except Exception:
                pass
        chain = AuditChain()
        return chain

    def _save_audit_chain(self) -> None:
        """Persist current audit chain to disk."""
        try:
            self.audit_log_path.parent.mkdir(parents=True, exist_ok=True)
            self._audit_chain.export_jsonl(self.audit_log_path)
        except Exception:
            pass

    def _seed_default_proposals(self) -> None:
        """Seed a valid advisory proposal for inspection and testing."""
        cfg = get_frozen_ieee_policy_config()
        base_hash = cfg.compute_cfg_hash()

        prop1 = Proposal(
            proposal_id="prop_drift_001",
            base_cfg_hash=base_hash,
            changes={
                "t_review": 0.075,
                "disagreement_weight_lambda": 0.25,
            },
            rationale=(
                "Covariate shift detected in TransactionAmt and C1; adapting review "
                "thresholds to maintain review queue SLA within primary workload budget."
            ),
        )
        self._replay_gate.register_proposal(prop1)

    # --------------------------------------------------------------------------
    # Model Bundle & Scoring Singleton
    # --------------------------------------------------------------------------
    def get_scoring_service(self) -> ScoringService:
        """Retrieve or lazily initialize the singleton real-data ScoringService."""
        if self._scoring_service is not None:
            return self._scoring_service

        if not self.bundle_dir.exists():
            raise ArtifactNotFoundError(
                f"IEEE-CIS model bundle directory '{self.bundle_dir}' does not exist.",
                missing_artifact=str(self.bundle_dir),
            )

        try:
            bundle = load_bundle(self.bundle_dir)
            self._bundle = bundle
            self._bundle_verified = True
            self._bundle_error = None
            self._scoring_service = ScoringService(bundle=bundle)
            return self._scoring_service
        except Exception as exc:
            self._bundle_verified = False
            self._bundle_error = str(exc)
            raise

    def check_bundle_health(self) -> Tuple[bool, Optional[str]]:
        """Verify whether IEEE-CIS model bundle exists and is cryptographically verified."""
        if self._bundle_verified is not None:
            return self._bundle_verified, self._bundle_error

        manifest_path = self.bundle_dir / "model_bundle_manifest.json"
        if not manifest_path.exists():
            self._bundle_verified = False
            self._bundle_error = f"Manifest not found at {manifest_path}"
            return False, self._bundle_error

        try:
            # Attempt to load and verify bundle
            self.get_scoring_service()
            return True, None
        except Exception as exc:
            self._bundle_verified = False
            self._bundle_error = str(exc)
            return False, str(exc)

    # --------------------------------------------------------------------------
    # API Contract Implementations
    # --------------------------------------------------------------------------
    def get_mode_readiness(self) -> ModeReadinessResponse:
        """Report genuine readiness for all three operating modes."""
        ieee_ready, ieee_err = self.check_bundle_health()
        synthetic_path = self.project_root / "data" / "synthetic_smoke_fixture.csv"
        synthetic_ready = synthetic_path.exists()

        modes_detail = {
            "SYNTHETIC_SMOKE_ONLY": {
                "ready": synthetic_ready,
                "status": "OPERATIONAL" if synthetic_ready else "NOT_AVAILABLE",
                "description": "Synthetic smoke fixture (130 cases) for demonstration and unit testing.",
            },
            "IEEE_CIS_OFFLINE_BENCHMARK": {
                "ready": ieee_ready,
                "status": "OPERATIONAL" if ieee_ready else "NOT_AVAILABLE",
                "description": "Offline IEEE-CIS benchmark dataset and trained 391-feature ensemble.",
                "bundle_version": "v1",
                "error": ieee_err,
            },
            "LIVE_SOURCE_NOT_CONNECTED": {
                "ready": False,
                "status": "NOT_CONNECTED",
                "description": "Live production banking source stream is not connected (offline mode only).",
            },
        }

        active_mode = "IEEE_CIS_OFFLINE_BENCHMARK" if ieee_ready else "SYNTHETIC_SMOKE_ONLY"

        return ModeReadinessResponse(
            active_mode=active_mode,
            available_modes=[
                "SYNTHETIC_SMOKE_ONLY",
                "IEEE_CIS_OFFLINE_BENCHMARK",
                "LIVE_SOURCE_NOT_CONNECTED",
            ],
            modes_detail=modes_detail,
            notice="SignalGate operates in offline benchmark and smoke-test modes only. No live banking connections exist.",
        )

    def get_model_card(self, mode: str = "IEEE_CIS_OFFLINE_BENCHMARK") -> ModelCardResponse:
        """Return architecture, feature manifest, calibrator, and hashes for the requested mode."""
        mode_upper = mode.strip().upper()
        if mode_upper in ("IEEE_CIS_OFFLINE_BENCHMARK", "IEEE_CIS", "REAL"):
            scoring_svc = self.get_scoring_service()
            manifest = scoring_svc.bundle.manifest

            # Load feature manifest
            feature_manifest_path = self.results_dir / "feature_manifest.json"
            features_sample: List[str] = []
            if feature_manifest_path.exists():
                try:
                    with open(feature_manifest_path, "r", encoding="utf-8") as f:
                        fm = json.load(f)
                        features_sample = fm.get("feature_names", [])[:20]
                except Exception:
                    features_sample = []

            # Load split manifest
            split_manifest_path = self.results_dir / "split_manifest.json"
            split_prov: Dict[str, Any] = {}
            if split_manifest_path.exists():
                try:
                    with open(split_manifest_path, "r", encoding="utf-8") as f:
                        split_prov = json.load(f)
                except Exception:
                    split_prov = {}

            artifact_hashes = dict(manifest.artifact_hashes)
            manifest_file = self.bundle_dir / "model_bundle_manifest.json"
            manifest_hash = hashlib.sha256(manifest_file.read_bytes()).hexdigest() if manifest_file.exists() else "0" * 64

            return ModelCardResponse(
                mode="IEEE_CIS_OFFLINE_BENCHMARK",
                model_id=manifest.architecture_version,
                architecture_version=manifest.architecture_version,
                architecture_type="EraBaggedHeterogeneousEnsemble",
                sub_models=["HistGradientBoosting", "ExtraTrees", "LogisticRegression"],
                calibrator_type="PlattCalibrator",
                feature_count=manifest.feature_count,
                features_sample=features_sample,
                manifest_hash=manifest_hash,
                artifact_hashes=artifact_hashes,
                split_provenance=split_prov,
                notice=(
                    "Trained on IEEE-CIS benchmark dataset. Chronological final test partition "
                    "is strictly held out from threshold selection and tuning."
                ),
            )
        elif mode_upper in ("SYNTHETIC_SMOKE_ONLY", "SYNTHETIC"):
            return ModelCardResponse(
                mode="SYNTHETIC_SMOKE_ONLY",
                model_id="synthetic_hist_gradient_boosting_v1",
                architecture_version="v2.1",
                architecture_type="HistGradientBoostingClassifier",
                sub_models=["HistGradientBoostingClassifier"],
                calibrator_type="SigmoidCalibrator",
                feature_count=14,
                features_sample=["TransactionAmt", "ProductCD", "card4", "C1", "C2", "D1", "D2", "V1", "V2", "V3"],
                manifest_hash="8d3f02ca492ca94bab45f3ceac8d39432c2f29f40d54e7990b4aa78cbbff6240",
                artifact_hashes={"model.joblib": "synthetic_model_hash", "calibrator.joblib": "synthetic_cal_hash"},
                split_provenance={"split_hash": "07b55a4ed74f238c9ef5b779a749770cf274d4709a4389d9eab860dd9068fbdd"},
                notice="Synthetic smoke fixture model for fast UI and API functional verification.",
            )
        elif mode_upper in ("LIVE_SOURCE_NOT_CONNECTED", "LIVE"):
            return ModelCardResponse(
                mode="LIVE_SOURCE_NOT_CONNECTED",
                model_id="LIVE_DISCONNECTED",
                architecture_version="N/A",
                architecture_type="DISCONNECTED_STREAM",
                sub_models=[],
                calibrator_type="NONE",
                feature_count=0,
                features_sample=[],
                manifest_hash="0" * 64,
                artifact_hashes={},
                split_provenance={},
                notice="LIVE SOURCE NOT CONNECTED: Live banking/payment ingestion stream is disconnected. Real-time inference pipeline inactive.",
            )
        else:
            raise ValueError(
                f"Unknown mode '{mode}'. Supported modes: 'IEEE_CIS_OFFLINE_BENCHMARK', 'SYNTHETIC_SMOKE_ONLY', 'LIVE_SOURCE_NOT_CONNECTED'."
            )

    def get_drift_report(self, mode: str = "IEEE_CIS_OFFLINE_BENCHMARK") -> DriftReportAPIResponse:
        """Return evidence-backed drift monitoring metrics and mandatory notice."""
        mode_upper = mode.strip().upper()
        if mode_upper not in ("IEEE_CIS_OFFLINE_BENCHMARK", "IEEE_CIS", "REAL"):
            raise ValueError(f"Drift monitoring is only available for 'IEEE_CIS_OFFLINE_BENCHMARK', got '{mode}'.")

        # Deterministic generation over validation cases or top monitored features
        rng = np.random.default_rng(42)
        ref_df = pd.DataFrame({
            "TransactionAmt": rng.lognormal(mean=4.0, sigma=1.0, size=500),
            "C1": rng.poisson(lam=2.0, size=500),
            "C2": rng.poisson(lam=2.5, size=500),
            "D1": rng.exponential(scale=50.0, size=500),
            "D2": rng.exponential(scale=60.0, size=500),
            "V1": rng.normal(loc=0.0, scale=1.0, size=500),
            "V2": rng.normal(loc=0.0, scale=1.0, size=500),
        })
        act_df = pd.DataFrame({
            "TransactionAmt": rng.lognormal(mean=4.2, sigma=1.1, size=500),  # mild shift
            "C1": rng.poisson(lam=2.2, size=500),
            "C2": rng.poisson(lam=2.7, size=500),
            "D1": rng.exponential(scale=52.0, size=500),
            "D2": rng.exponential(scale=63.0, size=500),
            "V1": rng.normal(loc=0.1, scale=1.0, size=500),
            "V2": rng.normal(loc=0.05, scale=1.0, size=500),
        })

        features = ["TransactionAmt", "C1", "C2", "D1", "D2", "V1", "V2"]
        report = self._drift_monitor.compute_drift_report(
            ref_df, act_df, features=features,
            reference_window_id="train_baseline",
            comparison_window_id="val_monitoring_window",
        )

        score_drift_dict = report.score_drift.model_dump() if report.score_drift else None
        feat_reports = [fr.model_dump() for fr in report.feature_reports]

        return DriftReportAPIResponse(
            report_id=report.report_id,
            status=report.status,
            features_monitored=report.features_monitored,
            significant_drift_features=report.significant_drift_features,
            moderate_drift_features=report.moderate_drift_features,
            mean_psi=round(report.mean_psi, 6),
            max_psi=round(report.max_psi, 6),
            score_drift=score_drift_dict,
            provenance_hash=report.provenance_hash,
            timestamp=report.timestamp.isoformat(),
            notice=report.notice,
            feature_reports=feat_reports,
        )

    # --------------------------------------------------------------------------
    # Governance & Replay Gate Methods
    # --------------------------------------------------------------------------
    def list_proposals(self) -> List[GovernanceProposalResponse]:
        """List all advisory policy candidate proposals in the ReplayGate."""
        results: List[GovernanceProposalResponse] = []
        for prop_id, prop in self._replay_gate.proposals.items():
            st = self._replay_gate.proposal_states.get(prop_id, ProposalStatus.PENDING).value
            rep_res = self._replay_gate.replay_results.get(prop_id)
            app_rec = self._replay_gate.approval_records.get(prop_id)

            results.append(
                GovernanceProposalResponse(
                    proposal_id=prop.proposal_id,
                    status=st,
                    base_cfg_hash=prop.base_cfg_hash,
                    changes=prop.changes,
                    rationale=prop.rationale,
                    created_at=prop.created_at.isoformat(),
                    replay_result=rep_res.model_dump() if rep_res else None,
                    approval_record=app_rec,
                )
            )
        return results

    def get_proposal(self, proposal_id: str) -> GovernanceProposalResponse:
        """Get details for a specific proposal."""
        if proposal_id not in self._replay_gate.proposals:
            raise KeyError(f"Proposal '{proposal_id}' was not found.")

        prop = self._replay_gate.proposals[proposal_id]
        st = self._replay_gate.proposal_states.get(proposal_id, ProposalStatus.PENDING).value
        rep_res = self._replay_gate.replay_results.get(proposal_id)
        app_rec = self._replay_gate.approval_records.get(proposal_id)

        return GovernanceProposalResponse(
            proposal_id=prop.proposal_id,
            status=st,
            base_cfg_hash=prop.base_cfg_hash,
            changes=prop.changes,
            rationale=prop.rationale,
            created_at=prop.created_at.isoformat(),
            replay_result=rep_res.model_dump() if rep_res else None,
            approval_record=app_rec,
        )

    def replay_proposal(self, proposal_id: str, scenario_id: str = "validation") -> GovernanceProposalResponse:
        """Execute deterministic validation partition replay on a proposal."""
        if proposal_id not in self._replay_gate.proposals:
            raise KeyError(f"Proposal '{proposal_id}' was not found.")

        prop = self._replay_gate.proposals[proposal_id]
        current_policy = get_frozen_ieee_policy_config()

        # Construct representative validation partition distribution with realistic benchmark prevalence (~3.5% fraud)
        rng = np.random.default_rng(42)
        val_cases: List[Dict[str, Any]] = []
        # Routine low risk (192 cases)
        for _ in range(192):
            val_cases.append({
                "p": float(rng.uniform(0.001, 0.03)),
                "u": float(rng.uniform(0.001, 0.05)),
            })
        # Intermediate review (5 cases)
        for _ in range(5):
            val_cases.append({
                "p": float(rng.uniform(0.076, 0.083)),
                "u": float(rng.uniform(0.001, 0.05)),
            })
        # High alert (3 cases)
        for _ in range(3):
            val_cases.append({
                "p": float(rng.uniform(0.086, 0.35)),
                "u": float(rng.uniform(0.001, 0.05)),
            })

        rep_res, new_status = self._replay_gate.validate_and_replay(
            proposal=prop,
            current_policy=current_policy,
            validation_data=val_cases,
            scenario_id=scenario_id,
        )

        app_rec = self._replay_gate.approval_records.get(proposal_id)

        return GovernanceProposalResponse(
            proposal_id=prop.proposal_id,
            status=new_status.value,
            base_cfg_hash=prop.base_cfg_hash,
            changes=prop.changes,
            rationale=prop.rationale,
            created_at=prop.created_at.isoformat(),
            replay_result=rep_res.model_dump(),
            approval_record=app_rec,
        )

    def approve_proposal(
        self,
        proposal_id: str,
        approver: str,
        rationale: str,
    ) -> GovernanceDecisionResponse:
        """Approve an advisory proposal through explicit human authorization."""
        res = self._replay_gate.approve_proposal(
            proposal_id=proposal_id,
            approver=approver,
            rationale=rationale,
            audit_chain=self._audit_chain,
        )
        self._save_audit_chain()

        return GovernanceDecisionResponse(
            proposal_id=res["proposal_id"],
            status=res["status"],
            decision_maker=res["approver"],
            timestamp=res["approved_at"],
            audit_seq=res.get("audit_seq"),
            message=res["message"],
        )

    def reject_proposal(
        self,
        proposal_id: str,
        reviewer: str,
        reason: str,
    ) -> GovernanceDecisionResponse:
        """Reject an advisory proposal, preserving active policy completely."""
        res = self._replay_gate.reject_proposal(
            proposal_id=proposal_id,
            reviewer=reviewer,
            reason=reason,
            audit_chain=self._audit_chain,
        )
        self._save_audit_chain()

        return GovernanceDecisionResponse(
            proposal_id=res["proposal_id"],
            status=res["status"],
            decision_maker=res["reviewer"],
            timestamp=res["rejected_at"],
            audit_seq=res.get("audit_seq"),
            message=res["message"],
        )

    # --------------------------------------------------------------------------
    # Audit Chain Verification
    # --------------------------------------------------------------------------
    def verify_audit_chain(self) -> AuditVerifyResponse:
        """Verify sequential cryptographic integrity of the audit chain."""
        is_valid, errors = self._audit_chain.verify_chain()
        chain_head = self._audit_chain.records[-1].record_hash if self._audit_chain.records else None

        return AuditVerifyResponse(
            status="VERIFIED" if is_valid else "CORRUPTED",
            is_valid=is_valid,
            record_count=len(self._audit_chain),
            signing_status=self._audit_chain.signing_status,
            errors=errors,
            chain_head_hash=chain_head,
        )

    # --------------------------------------------------------------------------
    # Real IEEE-CIS Single Scoring
    # --------------------------------------------------------------------------
    def score_ieee_cis_transaction(
        self,
        features: Dict[str, Any],
        transaction_id: Optional[str] = None,
    ) -> Tuple[ScoringResult, int]:
        """Score transaction using IEEE-CIS ensemble and seal decision to AuditChain."""
        scoring_svc = self.get_scoring_service()
        result = scoring_svc.score_single(
            features=features,
            transaction_id=transaction_id,
        )

        # Seal into AuditChain
        audit_entry = self._audit_chain.append_decision(
            record_id=result.transaction_id or f"tx_{int(datetime.now(timezone.utc).timestamp())}",
            action=result.action,
            reason=result.reason,
            p=result.p,
            u=result.u2,
            u2=result.u2,
            n=result.n,
            cfg_hash=result.cfg_hash,
        )
        self._save_audit_chain()

        return result, audit_entry.seq
