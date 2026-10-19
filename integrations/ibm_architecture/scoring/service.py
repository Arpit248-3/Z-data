"""SignalGate IBM Architecture Integration — Deterministic Scoring Service.

Implements the dynamic scoring service for single-transaction and cohort batch evaluation:
- Loads versioned cryptographic model bundle from models/artifacts/ieee_cis_v1/.
- Strictly fails closed on missing artifacts or checksum mismatches (ArtifactNotFoundError, IncompatibleArtifactError).
- Enforces strict ground-truth quarantine: isFraud, TransactionID, and TransactionDT are prohibited from feature payloads.
- Calculates calibrated probability p, ensemble consensus, and epistemic disagreement signals u and u2.
- Deterministically routes cases to actions (ROUTINE, MANUAL_REVIEW, FRAUD_ALERT, DEFERRED) and auditable reason codes (R0-R6).
- Applies dual-mode capacity governance to prevent capacity saturation from silently clearing high-risk cases.

Governing Specification: docs/ibm_architecture_integration_master_spec.md § C, § I
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Union
import numpy as np
import pandas as pd

from integrations.ibm_architecture.exceptions import (
    ArtifactNotFoundError,
    IncompatibleArtifactError,
    LeakageViolationError,
)
from integrations.ibm_architecture.models.bundle import ModelBundle, load_bundle
from integrations.ibm_architecture.models.signals import compute_signals, compute_single_signals
from integrations.ibm_architecture.policy.frozen_policy import (
    IEEEPolicyConfig,
    get_frozen_ieee_policy_config,
)
from integrations.ibm_architecture.policy.router import RouterPolicyAdapter
from integrations.ibm_architecture.policy.baselines import B2TopBudgetBaselineAdapter
from integrations.ibm_architecture.policy.p5_candidate import P5CandidatePolicyAdapter
from integrations.ibm_architecture.policy.governor import CapacityGovernor
from integrations.ibm_architecture.scoring.schemas import (
    BatchScoringResult,
    ScoringRequest,
    ScoringResult,
)

QUARANTINED_FIELDS: Set[str] = {
    "isfraud",
    "target",
    "label",
    "true_label",
    "transactionid",
    "transactiondt",
}


def check_feature_quarantine(field_names: Set[str], context: str = "scoring") -> None:
    """Verify that no quarantined ground-truth or raw identifier fields exist in feature payload."""
    detected = set()
    for field in field_names:
        if field.strip().lower() in QUARANTINED_FIELDS:
            detected.add(field)

    if detected:
        raise LeakageViolationError(
            message=f"Quarantined ground-truth or identifier fields detected in {context} payload.",
            violated_fields=detected,
            context=context,
        )


class ScoringService:
    """Deterministic dynamic scoring service for IEEE-CIS fraud detection."""

    def __init__(
        self,
        bundle_dir: Optional[Union[str, Path]] = None,
        bundle: Optional[ModelBundle] = None,
        policy_config: Optional[IEEEPolicyConfig] = None,
    ) -> None:
        # Load or bind verified model bundle
        if bundle is not None:
            self.bundle = bundle
        else:
            self.bundle = load_bundle(bundle_dir)

        # Policy configuration
        self.policy_config = policy_config or get_frozen_ieee_policy_config()
        self.router = RouterPolicyAdapter(config=self.policy_config)
        self.b2_baseline = B2TopBudgetBaselineAdapter(
            default_budget_fraction=self.policy_config.get_effective_workload_budget()
        )
        self.p5_candidate = P5CandidatePolicyAdapter(
            default_lambda=self.policy_config.disagreement_weight_lambda,
            default_budget_fraction=self.policy_config.get_effective_workload_budget(),
        )

    @property
    def model_version(self) -> str:
        return self.bundle.manifest.architecture_version

    @property
    def policy_version(self) -> str:
        return self.policy_config.status

    @property
    def cfg_hash(self) -> str:
        return self.policy_config.compute_cfg_hash()

    def score_single(
        self,
        features: Dict[str, Any],
        transaction_id: Optional[str] = None,
        policy_name: str = "router",
    ) -> ScoringResult:
        """Score a single transaction request.

        Raises:
            LeakageViolationError: If quarantined fields are present in features.
            ValueError: If P5 policy is requested on an isolated single case.
        """
        # 1. Enforce quarantine
        check_feature_quarantine(set(features.keys()), context="score_single")

        if policy_name.lower() == "p5":
            raise ValueError(
                "P5CandidatePolicyAdapter is a cohort-relative budget-ranking policy and "
                "cannot be evaluated on an individual transaction without cohort context."
            )

        # 2. Convert to single-row DataFrame
        input_df = pd.DataFrame([features])

        try:
            X_trans = self.bundle.feature_pipeline.transform(input_df)
            member_preds = self.bundle.ensemble.predict_member_proba(X_trans)
            raw_p = float(self.bundle.ensemble.predict_positive_proba(X_trans)[0])
            calibrated_p = float(self.bundle.calibrator.predict([raw_p])[0])

            signals = compute_single_signals(member_preds.proba_matrix[0])
            u_val = float(signals.u)
            u2_val = float(signals.u2)

            action, reason = self.router.route(calibrated_p, u=u2_val)
        except Exception:
            # Strictly fail closed on inference or transform exceptions
            calibrated_p = 1.0
            u_val = None
            u2_val = None
            action, reason = "MANUAL_REVIEW", "R0_SIGNAL_UNAVAILABLE"

        return ScoringResult(
            transaction_id=str(transaction_id) if transaction_id is not None else None,
            p=round(calibrated_p, 6),
            u=round(u_val, 6) if u_val is not None else None,
            u2=round(u2_val, 6) if u2_val is not None else None,
            n=float(self.bundle.ensemble.n_members),
            action=action,
            reason=reason,
            governor_status="not_applicable",
            lane_rank=None,
            model_version=self.model_version,
            policy_version=self.policy_version,
            cfg_hash=self.cfg_hash,
        )

    def score_batch(
        self,
        df: pd.DataFrame,
        id_col: Optional[str] = None,
        policy_name: str = "router",
        capacity: Optional[int] = None,
        budget_fraction: Optional[float] = None,
    ) -> BatchScoringResult:
        """Score a cohort batch of transactions with capacity governance."""
        total_samples = len(df)
        if total_samples == 0:
            return BatchScoringResult(
                results=[],
                total_transactions=0,
                policy_name=policy_name,
                governance_metrics={"total_transactions": 0, "effective_capacity": 0},
            )

        # 1. Enforce quarantine (prohibit isFraud, TransactionID, TransactionDT)
        check_feature_quarantine(set(df.columns), context="score_batch")

        # 2. Extract pseudonymous transaction IDs if column specified
        pseudonymous_ids: Optional[List[str]] = None
        feature_df = df
        if id_col is not None and id_col in df.columns:
            pseudonymous_ids = df[id_col].astype(str).tolist()
            feature_df = df.drop(columns=[id_col])

        # 3. Transform features
        X_trans = self.bundle.feature_pipeline.transform(feature_df)

        # 4. Predict raw probabilities and member matrix
        raw_probs = self.bundle.ensemble.predict_positive_proba(X_trans)
        member_preds = self.bundle.ensemble.predict_member_proba(X_trans)

        # 5. Predict calibrated probabilities
        calibrated_probs = self.bundle.calibrator.predict(raw_probs)

        # 6. Compute disagreement signals
        signals_arr = compute_signals(member_preds)
        u_arr = signals_arr["u"]
        u2_arr = signals_arr["u2"]

        # Effective budget fraction
        b_frac = budget_fraction if budget_fraction is not None else self.policy_config.get_effective_workload_budget()

        # 7. Apply policy routing
        p_name = policy_name.lower().strip()
        if p_name == "b2":
            actions, reasons = self.b2_baseline.route_cohort(calibrated_probs, budget_fraction=b_frac)
            gov_metrics = {
                "policy": "b2_top_b",
                "budget_fraction": b_frac,
                "effective_capacity": int(np.floor(total_samples * b_frac)),
                "total_transactions": total_samples,
                "escalated_count": int(sum(1 for a in actions if a != "ROUTINE")),
            }
            governor_status = ["admitted" if a != "ROUTINE" else "not_applicable" for a in actions]
            lane_ranks = [None] * total_samples

        elif p_name == "p5":
            actions, reasons = self.p5_candidate.route_cohort(
                calibrated_probs, u=u2_arr, budget_fraction=b_frac
            )
            gov_metrics = {
                "policy": "p5_candidate",
                "lambda": self.policy_config.disagreement_weight_lambda,
                "budget_fraction": b_frac,
                "effective_capacity": int(np.floor(total_samples * b_frac)),
                "total_transactions": total_samples,
                "escalated_count": int(sum(1 for a in actions if a != "ROUTINE")),
            }
            governor_status = ["admitted" if a != "ROUTINE" else "not_applicable" for a in actions]
            lane_ranks = [None] * total_samples

        else:
            # Default: Triage router + Capacity Governor
            actions, reasons = self.router.route_batch(calibrated_probs, u_seq=u2_arr)

            batch_df = pd.DataFrame({
                "p": calibrated_probs,
                "action": actions,
                "reason": reasons,
            })
            if pseudonymous_ids is not None:
                batch_df["_pseudo_id"] = pseudonymous_ids

            governor = CapacityGovernor(
                capacity=capacity,
                budget_fraction=b_frac if capacity is None else None,
                priority_col="p",
                action_col="action",
                reason_col="reason",
            )
            governed_df, gov_metrics = governor.govern(
                batch_df, id_col="_pseudo_id" if pseudonymous_ids is not None else None
            )

            actions = governed_df["action"].tolist()
            reasons = governed_df["reason"].tolist()
            governor_status = governed_df["governor_status"].tolist()
            lane_ranks = governed_df["lane_rank"].tolist()

        # 8. Assemble results
        results: List[ScoringResult] = []
        for i in range(total_samples):
            p_val = float(calibrated_probs[i])
            u_val = float(u_arr[i])
            u2_val = float(u2_arr[i])
            t_id = pseudonymous_ids[i] if pseudonymous_ids is not None else None

            results.append(
                ScoringResult(
                    transaction_id=t_id,
                    p=round(p_val, 6),
                    u=round(u_val, 6),
                    u2=round(u2_val, 6),
                    n=float(self.bundle.ensemble.n_members),
                    action=actions[i],
                    reason=reasons[i],
                    governor_status=governor_status[i],
                    lane_rank=lane_ranks[i],
                    model_version=self.model_version,
                    policy_version=self.policy_version,
                    cfg_hash=self.cfg_hash,
                )
            )

        return BatchScoringResult(
            results=results,
            total_transactions=total_samples,
            policy_name=policy_name,
            governance_metrics=gov_metrics,
        )
