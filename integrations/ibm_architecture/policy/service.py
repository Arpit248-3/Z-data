"""SignalGate IBM Architecture Integration — Deterministic Scoring Service.

Provides complete deterministic single-case and batch scoring services:
- Integrates ModelBundle (from Phase 4) with RouterPolicyAdapter and GovernedCapacityManager.
- Enforces strict ground-truth quarantine: rejects isFraud, TransactionID, TransactionDT.
- Fails closed on invalid or missing features.
- Stamped with explicit mode metadata: execution_mode=SYNTHETIC_SMOKE_ONLY, benchmark_comparable=false.
- Enforces operational review capacity quota ($B=130$).
"""

from __future__ import annotations

import time
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union
import numpy as np
import pandas as pd

from integrations.ibm_architecture.exceptions import LeakageViolationError
from integrations.ibm_architecture.models.bundle import ModelBundle, load_synthetic_bundle
from integrations.ibm_architecture.policy.adapters import RouterPolicyAdapter
from integrations.ibm_architecture.policy.governor import GovernedCapacityManager
from policy.router import Action, ReasonCode


class DeterministicScoringService:
    """Production scoring service integrating model bundles, policy router, and capacity governance."""

    def __init__(
        self,
        model_bundle: ModelBundle,
        router_adapter: Optional[RouterPolicyAdapter] = None,
        capacity_manager: Optional[GovernedCapacityManager] = None,
    ) -> None:
        self.bundle = model_bundle
        self.router = router_adapter or RouterPolicyAdapter()
        self.capacity_manager = capacity_manager or GovernedCapacityManager(capacity=130)

    @property
    def execution_mode(self) -> str:
        return self.bundle.execution_mode

    @property
    def is_synthetic(self) -> bool:
        return self.bundle.is_synthetic

    @property
    def real_data_training_status(self) -> str:
        return self.bundle.real_data_training_status

    def score_single(
        self,
        case_features: Union[Dict[str, Any], pd.Series],
    ) -> Dict[str, Any]:
        """Score a single transaction case with deterministic routing and fail-closed safety."""
        t0 = time.perf_counter()

        # Convert to single-row DataFrame
        if isinstance(case_features, pd.Series):
            df_in = pd.DataFrame([case_features.to_dict()])
        else:
            df_in = pd.DataFrame([dict(case_features)])

        # Inference through model bundle (includes quarantine checks)
        scores = self.bundle.score_features(df_in)

        p_cal = float(scores["p_cal"][0])
        p_raw = float(scores["p_raw"][0])
        u_val = float(scores["u"][0])
        u2_val = float(scores["u2"][0])
        p_b2 = float(scores["p_b2"][0])

        # Evaluate deterministic policy router
        action_enum, reason_enum = self.router.route_single(p=p_cal, u=u2_val)
        action_str = action_enum.value
        reason_str = reason_enum.value

        # Single-row capacity simulation (sandbox context)
        governor_status = (
            "admitted" if action_str in [Action.FRAUD_ALERT.value, Action.MANUAL_REVIEW.value] else "not_applicable"
        )
        lane_rank = 1 if governor_status == "admitted" else None
        elapsed_ms = round((time.perf_counter() - t0) * 1000.0, 3)

        return {
            "decision_id": f"dec_{uuid.uuid4().hex[:12]}",
            "p_raw": p_raw,
            "p_cal": p_cal,
            "u": u_val,
            "u2": u2_val,
            "p_b2": p_b2,
            "action": action_str,
            "reason": reason_str,
            "governor_status": governor_status,
            "lane_rank": lane_rank,
            "latency_ms": elapsed_ms,
            "execution_mode": self.bundle.execution_mode,
            "benchmark_comparable": self.bundle.manifest.benchmark_comparable,
            "real_data_training_status": self.bundle.real_data_training_status,
        }

    def score_batch(
        self,
        df: pd.DataFrame,
        enforce_capacity: bool = True,
    ) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """Score a batch of transaction cases with model inference, routing, and optional capacity governance."""
        scores = self.bundle.score_features(df)

        n_samples = len(df)
        p_cal = scores["p_cal"]
        p_raw = scores["p_raw"]
        u_val = scores["u"]
        u2_val = scores["u2"]
        p_b2 = scores["p_b2"]

        routed_actions = []
        routed_reasons = []
        for i in range(n_samples):
            act, rsn = self.router.route_single(float(p_cal[i]), float(u2_val[i]))
            routed_actions.append(act.value)
            routed_reasons.append(rsn.value)

        out_df = pd.DataFrame({
            "p_raw": p_raw,
            "p_cal": p_cal,
            "u": u_val,
            "u2": u2_val,
            "p_b2": p_b2,
            "action": routed_actions,
            "reason": routed_reasons,
        })

        metrics: Dict[str, Any] = {}
        if enforce_capacity:
            out_df, metrics = self.capacity_manager.govern_batch(out_df)
        else:
            out_df["governor_status"] = "not_governed"
            out_df["lane_rank"] = None

        return out_df, metrics

    @classmethod
    def create_default(
        cls,
        project_root: Optional[Path | str] = None,
        capacity: int = 130,
    ) -> DeterministicScoringService:
        """Create a default scoring service instance initialized with canonical synthetic assets."""
        bundle = load_synthetic_bundle(project_root=project_root)
        router = RouterPolicyAdapter()
        capacity_mgr = GovernedCapacityManager(capacity=capacity)
        return cls(
            model_bundle=bundle,
            router_adapter=router,
            capacity_manager=capacity_mgr,
        )
