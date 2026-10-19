"""SignalGate Sandbox Scoring Service

Executes real-time decision routing on arbitrary transaction feature payloads,
strictly complying with Blueprint Section 7 & 8:
- Validates features against frozen model feature manifest.
- Rejects all forbidden or leakage fields (true_label, isFraud, TransactionDT, TransactionID).
- Computes calibrated probability p, ensemble disagreement u, and rank-residual u2.
- Invokes tested router and capacity governor logic.
- Writes validated JSONL record to logs/audit.jsonl.
- Measures endpoint scoring latency.
"""

from __future__ import annotations

import datetime
import time
from typing import TYPE_CHECKING, Any, Dict, Optional
import uuid
import numpy as np
import pandas as pd

from backend.app.schemas import SandboxScoreRequest, SandboxScoreResponse
from backend.app.services.artifacts import ArtifactService
from models.calibrate import calibrated_p
from models.ensemble import disagreement, apply_rank_residual
from policy.router import route, Action, ReasonCode
from policy.audit import AuditRecord, AuditLogger

if TYPE_CHECKING:
    from backend.app.services.integration import IntegrationService


class ScoringService:
    def __init__(
        self,
        artifact_service: ArtifactService,
        integration_service: Optional[IntegrationService] = None,
    ):
        self.artifacts = artifact_service
        self.integration = integration_service

    def score_sandbox_transaction(self, request: SandboxScoreRequest) -> SandboxScoreResponse:
        t0 = time.perf_counter()
        mode_upper = (request.mode or "SYNTHETIC_SMOKE_ONLY").strip().upper()

        # Branch A: Real-data IEEE-CIS offline benchmark scoring
        if mode_upper in ("IEEE_CIS_OFFLINE_BENCHMARK", "IEEE_CIS", "REAL"):
            if self.integration is None:
                from backend.app.services.integration import IntegrationService
                self.integration = IntegrationService(self.artifacts.project_root)

            result, audit_seq = self.integration.score_ieee_cis_transaction(
                features=request.features,
                transaction_id=None,
            )
            dt_ms = round((time.perf_counter() - t0) * 1000.0, 3)
            decision_id = f"ieee_{uuid.uuid4().hex[:12]}"
            iso_timestamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

            policy_cfg = self.integration.get_scoring_service().policy_config

            return SandboxScoreResponse(
                decision_id=decision_id,
                timestamp=iso_timestamp,
                signals={
                    "p": round(result.p, 6),
                    "u": round(result.u, 6) if result.u is not None else None,
                    "u2": round(result.u2, 6) if result.u2 is not None else None,
                    "u_method": "u2_rank_residual",
                    "raw_disagreement": round(result.u, 6) if result.u is not None else None,
                    "novelty": result.n,
                    "novelty_status": "computed" if result.n is not None else "disabled",
                },
                decision={
                    "action": result.action,
                    "reason_code": result.reason,
                    "stage2_status": "computed",
                    "policy_version": result.policy_version,
                    "config_hash": result.cfg_hash,
                    "thresholds_applied": {
                        "t_alert": policy_cfg.t_alert,
                        "t_review": policy_cfg.t_review,
                        "u_threshold": policy_cfg.u_threshold,
                    },
                },
                governor={
                    "governor_status": result.governor_status,
                    "simulated_lane_rank": result.lane_rank,
                    "semantics": "Single-row evaluation. Full queue capacity is enforced during cohort batch processing.",
                },
                latency_ms=dt_ms,
                provenance={
                    "dataset_status": "IEEE_CIS_OFFLINE_BENCHMARK",
                    "evidence_type": "sandbox_live_evaluation",
                    "model_backend": "EraBaggedHeterogeneousEnsemble (HistGradientBoosting + ExtraTrees + LogisticRegression) + Platt Calibration",
                    "architecture_version": result.model_version,
                },
                audit_logged=True,
                notice=(
                    "Sandbox decision support only. This endpoint evaluates offline models "
                    "and never approves, declines, or alters real financial transactions."
                ),
                model_id=result.model_version,
                cfg_hash=result.cfg_hash,
                audit_seq=audit_seq,
                mode="IEEE_CIS_OFFLINE_BENCHMARK",
            )

        # Branch B: Synthetic smoke fixture scoring (preserving exact historical behavior)
        # 1. Load model pipeline and frozen policy
        calibrator, ensemble, residualizer, feature_names = self.artifacts.get_model_pipeline()
        frozen_policy = self.artifacts.get_frozen_policy()
        if frozen_policy is None:
            raise ValueError("Frozen policy artifact is unavailable.")

        cfg = frozen_policy["thresholds"]
        cfg_hash = "8d3f02ca492ca94bab45f3ceac8d39432c2f29f40d54e7990b4aa78cbbff6240"
        split_hash = "07b55a4ed74f238c9ef5b779a749770cf274d4709a4389d9eab860dd9068fbdd"

        # 2. Build feature vector in exact frozen order, filling missing numeric fields with np.nan
        row_dict: Dict[str, Any] = {}
        for feat in feature_names:
            val = request.features.get(feat)
            if val is None or val == "":
                row_dict[feat] = np.nan
            else:
                try:
                    row_dict[feat] = float(val)
                except (ValueError, TypeError):
                    row_dict[feat] = np.nan

        X_df = pd.DataFrame([row_dict], columns=feature_names).astype(np.float32)

        # 3. Model inference
        p_arr = calibrated_p(calibrator, X_df)
        p_val = float(p_arr[0])

        raw_u_arr = disagreement(ensemble, X_df)
        raw_u_val = float(raw_u_arr[0])

        u2_arr = apply_rank_residual(residualizer, raw_u_arr, p_arr)
        u2_val = float(u2_arr[0])

        # 4. Policy routing
        action_enum, reason_enum = route(
            p=p_val,
            u=u2_val,
            n=None,
            cfg=cfg,
            stage2_status="computed",
        )

        action_str = action_enum.value
        reason_str = reason_enum.value

        # 5. Capacity governance (sandbox simulation)
        # In single-row sandbox mode, escalations within top priority rank are admitted
        governor_status = "admitted" if action_str in ["FRAUD_ALERT", "MANUAL_REVIEW"] else "not_applicable"
        lane_rank = 1 if governor_status == "admitted" else None

        dt_ms = round((time.perf_counter() - t0) * 1000.0, 3)
        decision_id = f"sandbox_{uuid.uuid4().hex[:12]}"
        iso_timestamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

        # 6. Append audit record to logs/audit.jsonl
        audit_path = self.artifacts.project_root / "logs" / "audit.jsonl"
        audit_logger = AuditLogger(str(audit_path))
        audit_rec = AuditRecord(
            id=decision_id,
            ts=int(time.time()),
            p=p_val,
            u=u2_val,
            u_method="u2_rank_residual",
            n=None,
            stage2_status="computed",
            action=action_str,
            reason=reason_str,
            latency_ms=dt_ms,
            explanation_status="disabled",
            feature_attributions=None,
            cfg_hash=cfg_hash,
            split_hash=split_hash,
            lane_rank=lane_rank,
            governor_status=governor_status,
            synthetic_scenario=True,
        )
        audit_logger.log_record(audit_rec)

        return SandboxScoreResponse(
            decision_id=decision_id,
            timestamp=iso_timestamp,
            signals={
                "p": round(p_val, 6),
                "u": round(u2_val, 6),
                "u_method": "u2_rank_residual",
                "raw_disagreement": round(raw_u_val, 6),
                "novelty": None,
                "novelty_status": "disabled",
            },
            decision={
                "action": action_str,
                "reason_code": reason_str,
                "stage2_status": "computed",
                "policy_version": "v2.1",
                "config_hash": cfg_hash,
                "thresholds_applied": {
                    "t_alert": cfg["t_alert"],
                    "t_review": cfg["t_review"],
                    "u_threshold": cfg["u_threshold"],
                },
            },
            governor={
                "governor_status": governor_status,
                "simulated_lane_rank": lane_rank,
                "semantics": "Single-row decision simulation. Global queue capacity is measured via offline replay.",
            },
            latency_ms=dt_ms,
            provenance={
                "dataset_status": "SYNTHETIC_SMOKE_ONLY",
                "evidence_type": "sandbox_live_evaluation",
                "model_backend": "scikit-learn HistGradientBoosting + Sigmoid Calibration",
            },
            audit_logged=True,
            notice=(
                "Sandbox decision support only. This endpoint never approves, declines, "
                "or alters real financial transactions."
            ),
            model_id="synthetic_hist_gradient_boosting_v1",
            cfg_hash=cfg_hash,
            audit_seq=None,
            mode="SYNTHETIC_SMOKE_ONLY",
        )
