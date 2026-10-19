"""SignalGate IBM Architecture Integration — Deterministic Triage Decision Router.

Implements the deterministic action router adapter evaluating calibrated risk p,
epistemic disagreement u, and optional novelty n against frozen thresholds.

Governing Specification: docs/ibm_architecture_integration_master_spec.md § C, § I
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Sequence, Tuple, Union
import numpy as np
import pandas as pd

from integrations.ibm_architecture.contracts import Action, ReasonCode
from integrations.ibm_architecture.policy.frozen_policy import IEEEPolicyConfig, get_frozen_ieee_policy_config


def validate_router_config(cfg: Union[IEEEPolicyConfig, Dict[str, Any]]) -> Tuple[bool, List[str]]:
    """Validate router policy thresholds and ordering. Returns (is_valid, error_messages)."""
    errors: List[str] = []
    if isinstance(cfg, IEEEPolicyConfig):
        return True, []

    if not isinstance(cfg, dict):
        return False, ["Router configuration must be an IEEEPolicyConfig or dictionary."]

    t_alert = cfg.get("t_alert")
    t_review = cfg.get("t_review")
    u_threshold = cfg.get("u_threshold")

    if t_alert is None or not isinstance(t_alert, (int, float)) or not np.isfinite(t_alert) or not (0.0 <= t_alert <= 1.0):
        errors.append(f"Invalid t_alert threshold: {t_alert}")

    if t_review is None or not isinstance(t_review, (int, float)) or not np.isfinite(t_review) or not (0.0 <= t_review <= 1.0):
        errors.append(f"Invalid t_review threshold: {t_review}")

    if not errors and t_review >= t_alert:
        errors.append(f"Invalid threshold ordering: t_review ({t_review}) must be strictly less than t_alert ({t_alert})")

    if cfg.get("disagreement_enabled", False):
        if u_threshold is None or not isinstance(u_threshold, (int, float)) or not np.isfinite(u_threshold) or u_threshold < 0.0:
            errors.append(f"Invalid u_threshold: {u_threshold}")

    return len(errors) == 0, errors


class RouterPolicyAdapter:
    """Deterministic Action Router evaluating calibrated risk and model disagreement."""

    def __init__(self, config: Optional[Union[IEEEPolicyConfig, Dict[str, Any]]] = None) -> None:
        if config is None:
            self.config = get_frozen_ieee_policy_config()
        elif isinstance(config, IEEEPolicyConfig):
            self.config = config
        elif isinstance(config, dict):
            is_valid, errs = validate_router_config(config)
            if not is_valid:
                raise ValueError(f"Invalid router configuration: {'; '.join(errs)}")
            self.config = IEEEPolicyConfig(**config)
        else:
            raise TypeError(f"Unsupported config type: {type(config)}")

    @property
    def cfg_hash(self) -> str:
        return self.config.compute_cfg_hash()

    def route(
        self,
        p: Optional[float],
        u: Optional[float] = None,
        n: Optional[float] = None,
    ) -> Tuple[Action, ReasonCode]:
        """Route a single case with strict fail-closed precedence.

        Precedence Rules:
        1. Bad / Non-finite Signal -> (MANUAL_REVIEW, R0_SIGNAL_UNAVAILABLE)
        2. High Risk (p >= t_alert) -> (FRAUD_ALERT, R1_HIGH_RISK) [Never ROUTINE]
        3. Intermediate Risk (p >= t_review) -> (MANUAL_REVIEW, R2_INTERMEDIATE_RISK)
        4. Model Disagreement (u >= u_threshold) -> (MANUAL_REVIEW, R3_MODEL_DISAGREEMENT) [Never FRAUD_ALERT]
        5. Novelty (n >= n_threshold) -> (MANUAL_REVIEW, R4_UNFAMILIAR_INPUT)
        6. Reliable Low Risk -> (ROUTINE, R5_LOW_RISK_RELIABLE)
        """
        # Step 1: Validate calibrated risk probability p
        if p is None or not isinstance(p, (int, float)) or not np.isfinite(p) or not (0.0 <= p <= 1.0):
            return "MANUAL_REVIEW", "R0_SIGNAL_UNAVAILABLE"

        # Step 2: Validate disagreement signal u if enabled
        if self.config.disagreement_enabled:
            if u is None or not isinstance(u, (int, float)) or not np.isfinite(u) or u < 0.0:
                return "MANUAL_REVIEW", "R0_SIGNAL_UNAVAILABLE"

        # Step 3: Validate novelty signal n if enabled
        if self.config.novelty_enabled:
            if n is None or not isinstance(n, (int, float)) or not np.isfinite(n) or n < 0.0:
                return "MANUAL_REVIEW", "R0_SIGNAL_UNAVAILABLE"

        # Step 4: High-risk check
        if p >= self.config.t_alert:
            return "FRAUD_ALERT", "R1_HIGH_RISK"

        # Step 5: Intermediate-risk check
        if p >= self.config.t_review:
            return "MANUAL_REVIEW", "R2_INTERMEDIATE_RISK"

        # Step 6: Disagreement check
        if self.config.disagreement_enabled and u is not None and u >= self.config.u_threshold:
            return "MANUAL_REVIEW", "R3_MODEL_DISAGREEMENT"

        # Step 7: Novelty check
        if self.config.novelty_enabled and n is not None and self.config.n_threshold is not None:
            if n >= self.config.n_threshold:
                return "MANUAL_REVIEW", "R4_UNFAMILIAR_INPUT"

        # Step 8: Default low-risk reliable
        return "ROUTINE", "R5_LOW_RISK_RELIABLE"

    def route_batch(
        self,
        p_seq: Sequence[Optional[float]],
        u_seq: Optional[Sequence[Optional[float]]] = None,
        n_seq: Optional[Sequence[Optional[float]]] = None,
    ) -> Tuple[List[Action], List[ReasonCode]]:
        """Vectorized / batch routing across a cohort of transactions."""
        n_samples = len(p_seq)
        u_vals = u_seq if u_seq is not None else [None] * n_samples
        n_vals = n_seq if n_seq is not None else [None] * n_samples

        actions: List[Action] = []
        reasons: List[ReasonCode] = []

        for p_val, u_val, n_val in zip(p_seq, u_vals, n_vals):
            act, rsn = self.route(p_val, u_val, n_val)
            actions.append(act)
            reasons.append(rsn)

        return actions, reasons
