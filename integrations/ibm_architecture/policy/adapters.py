"""SignalGate IBM Architecture Integration — Deterministic Policy Adapters.

Implements the multi-policy triage adapters in compliance with Master Spec § D & § I:
1. RouterPolicyAdapter: Evaluates frozen multi-threshold decision logic emitting Action and ReasonCode (R0-R6).
2. BaselineB2PolicyAdapter: Mandatory top-B risk ranking baseline.
3. CandidateP5PolicyAdapter: Transparent P5 candidate policy (score = p_cal + lambda * u).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union
import numpy as np
import pandas as pd

from policy.baselines import baseline_top_b, compute_policy_metrics
from policy.router import Action, ReasonCode, route, validate_router_config


class RouterPolicyAdapter:
    """Adapter for the deterministic multi-threshold triage router."""

    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        if config is None:
            # Load default frozen policy
            policy_file = Path(__file__).resolve().parent.parent.parent.parent / "policy" / "frozen_policy.json"
            if policy_file.exists():
                with open(policy_file, "r", encoding="utf-8") as f:
                    policy_data = json.load(f)
                    self.config = policy_data.get("thresholds", {})
            else:
                self.config = {
                    "t_alert": 0.084705,
                    "t_review": 0.071002,
                    "u_threshold": 0.526773,
                    "disagreement_enabled": True,
                    "novelty_enabled": False,
                    "target_budget": 0.06525,
                }
        else:
            self.config = dict(config)

        self.is_valid, self.validation_errors = validate_router_config(self.config)

    def route_single(
        self,
        p: Optional[float],
        u: Optional[float] = None,
        n: Optional[float] = None,
        stage2_status: str = "computed",
    ) -> Tuple[Action, ReasonCode]:
        """Route a single transaction. Fails closed to MANUAL_REVIEW / R0 on invalid inputs."""
        return route(
            p=p,
            u=u,
            n=n,
            cfg=self.config,
            stage2_status=stage2_status,
        )

    def route_batch(
        self,
        p_arr: np.ndarray,
        u_arr: Optional[np.ndarray] = None,
        n_arr: Optional[np.ndarray] = None,
    ) -> List[Tuple[Action, ReasonCode]]:
        """Route a batch of transactions deterministically."""
        n_samples = len(p_arr)
        out = []
        for i in range(n_samples):
            p_val = float(p_arr[i]) if p_arr[i] is not None and np.isfinite(p_arr[i]) else None
            u_val = float(u_arr[i]) if u_arr is not None and np.isfinite(u_arr[i]) else None
            n_val = float(n_arr[i]) if n_arr is not None and np.isfinite(n_arr[i]) else None
            act, rsn = self.route_single(p_val, u_val, n_val)
            out.append((act, rsn))
        return out


class BaselineB2PolicyAdapter:
    """Adapter for the mandatory Baseline B2 top-B risk ranking policy."""

    def __init__(self, default_budget: float = 0.06525) -> None:
        self.default_budget = float(default_budget)

    def escalate_mask(
        self,
        p_scores: Union[pd.Series, np.ndarray],
        budget: Optional[float] = None,
    ) -> np.ndarray:
        """Return boolean mask of transactions escalated under budget B."""
        b = self.default_budget if budget is None else float(budget)
        return baseline_top_b(p_scores, b)

    def evaluate(
        self,
        p_scores: Union[pd.Series, np.ndarray],
        y_true: np.ndarray,
        budget: Optional[float] = None,
    ) -> Dict[str, Any]:
        """Compute complete triage metrics for B2 against holdout labels."""
        b = self.default_budget if budget is None else float(budget)
        mask = self.escalate_mask(p_scores, b)
        return compute_policy_metrics(mask, y_true, b, policy_name="Baseline_B2_Top_Budget")


class CandidateP5PolicyAdapter:
    """Adapter for Candidate P5 policy: score(x) = p_cal + lambda * u."""

    def __init__(
        self,
        disagreement_weight_lambda: float = 0.0,
        budget_multiple: float = 1.5,
        train_prevalence: float = 0.0435,
    ) -> None:
        self.weight_lambda = float(disagreement_weight_lambda)
        self.budget_multiple = float(budget_multiple)
        self.train_prevalence = float(train_prevalence)

    def score(
        self,
        p_calibrated: np.ndarray,
        disagreement: Optional[np.ndarray] = None,
    ) -> np.ndarray:
        """Calculate combined triage priority score."""
        p = np.asarray(p_calibrated, dtype=np.float64)
        if self.weight_lambda == 0.0 or disagreement is None:
            return p
        u = np.asarray(disagreement, dtype=np.float64)
        return p + self.weight_lambda * u

    def route_cohort(
        self,
        p_calibrated: np.ndarray,
        disagreement: Optional[np.ndarray] = None,
        budget_fraction: Optional[float] = None,
    ) -> np.ndarray:
        """Assign review decisions based on top-budget ranking with deterministic tie handling.

        Returns boolean mask of escalated cases.
        """
        scores = self.score(p_calibrated, disagreement)
        n = len(scores)

        target_budget = (
            budget_fraction
            if budget_fraction is not None
            else self.budget_multiple * self.train_prevalence
        )
        k = int(np.floor(target_budget * n))
        k = max(0, min(k, n))

        if k == 0:
            return np.zeros(n, dtype=bool)
        if k >= n:
            return np.ones(n, dtype=bool)

        # Deterministic stable ranking: highest score first
        sorted_indices = np.argsort(-scores, kind="mergesort")
        mask = np.zeros(n, dtype=bool)
        mask[sorted_indices[:k]] = True
        return mask
