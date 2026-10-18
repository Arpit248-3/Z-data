"""
SignalGate Decision Router
Implements the core decision-support triage routing layer:
- Evaluates calibrated risk probability p, model disagreement u, and novelty signal n.
- Strictly fails closed to MANUAL_REVIEW / R0_SIGNAL_UNAVAILABLE on missing, invalid, or out-of-range signals.
- High risk score (p >= t_alert) produces FRAUD_ALERT / R1_HIGH_RISK and can NEVER produce ROUTINE.
- Excessive disagreement or novelty triggers MANUAL_REVIEW, never FRAUD_ALERT (not proof of fraud).
- Distinguishes intentionally skipped second-stage inference from signal failure.
- Emits auditable reason codes: R0 through R6.
"""

from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, Union
import numpy as np
import pandas as pd


class Action(str, Enum):
    FRAUD_ALERT = "FRAUD_ALERT"
    MANUAL_REVIEW = "MANUAL_REVIEW"
    ROUTINE = "ROUTINE"
    HELD = "HELD"
    DEFERRED = "DEFERRED"


class ReasonCode(str, Enum):
    R0_SIGNAL_UNAVAILABLE = "R0_SIGNAL_UNAVAILABLE"
    R1_HIGH_RISK = "R1_HIGH_RISK"
    R2_INTERMEDIATE_RISK = "R2_INTERMEDIATE_RISK"
    R3_MODEL_DISAGREEMENT = "R3_MODEL_DISAGREEMENT"
    R4_UNFAMILIAR_INPUT = "R4_UNFAMILIAR_INPUT"
    R5_LOW_RISK_RELIABLE = "R5_LOW_RISK_RELIABLE"
    R6_CAPACITY_DEFERRED = "R6_CAPACITY_DEFERRED"


def validate_router_config(cfg: Optional[Dict[str, Any]]) -> Tuple[bool, List[str]]:
    """
    Validate that routing policy thresholds and configuration parameters are mathematically sound.
    Returns (is_valid, error_messages).
    """
    if cfg is None or not isinstance(cfg, dict):
        return False, ["Router configuration must be a non-null dictionary."]

    errors = []

    # t_alert and t_review are required
    if "t_alert" not in cfg or cfg["t_alert"] is None:
        errors.append("Missing required threshold 't_alert'.")
    elif not isinstance(cfg["t_alert"], (int, float)) or not np.isfinite(cfg["t_alert"]):
        errors.append(f"Invalid non-finite 't_alert': {cfg.get('t_alert')}")
    elif not (0.0 <= cfg["t_alert"] <= 1.0):
        errors.append(f"'t_alert' out of bounds [0, 1]: {cfg['t_alert']}")

    if "t_review" not in cfg or cfg["t_review"] is None:
        errors.append("Missing required threshold 't_review'.")
    elif not isinstance(cfg["t_review"], (int, float)) or not np.isfinite(cfg["t_review"]):
        errors.append(f"Invalid non-finite 't_review': {cfg.get('t_review')}")
    elif not (0.0 <= cfg["t_review"] <= 1.0):
        errors.append(f"'t_review' out of bounds [0, 1]: {cfg['t_review']}")

    # Check ordering t_review < t_alert
    if "t_alert" in cfg and "t_review" in cfg and len(errors) == 0:
        if cfg["t_review"] >= cfg["t_alert"]:
            errors.append(f"Invalid threshold ordering: t_review ({cfg['t_review']}) must be strictly less than t_alert ({cfg['t_alert']}).")

    # Disagreement threshold validation
    if cfg.get("disagreement_enabled", False):
        if "u_threshold" not in cfg or cfg["u_threshold"] is None:
            errors.append("Disagreement is enabled but 'u_threshold' is missing.")
        elif not isinstance(cfg["u_threshold"], (int, float)) or not np.isfinite(cfg["u_threshold"]):
            errors.append(f"Invalid non-finite 'u_threshold': {cfg.get('u_threshold')}")
        elif cfg["u_threshold"] < 0.0:
            errors.append(f"'u_threshold' cannot be negative: {cfg['u_threshold']}")

    # Novelty threshold validation
    if cfg.get("novelty_enabled", False):
        if "n_threshold" not in cfg or cfg["n_threshold"] is None:
            errors.append("Novelty is enabled but 'n_threshold' is missing.")
        elif not isinstance(cfg["n_threshold"], (int, float)) or not np.isfinite(cfg["n_threshold"]):
            errors.append(f"Invalid non-finite 'n_threshold': {cfg.get('n_threshold')}")
        elif cfg["n_threshold"] < 0.0:
            errors.append(f"'n_threshold' cannot be negative: {cfg['n_threshold']}")

    return len(errors) == 0, errors


def route(
    p: Optional[float],
    u: Optional[float] = None,
    n: Optional[float] = None,
    cfg: Optional[Dict[str, Any]] = None,
    stage2_status: str = "computed",
) -> Tuple[Action, ReasonCode]:
    """
    Route a single transaction to an action lane with auditable reason code.

    Deterministic Precedence:
    1. Configuration validation: if cfg is invalid, fail closed to MANUAL_REVIEW / R0_SIGNAL_UNAVAILABLE.
    2. Input signal validation: if p is None/NaN/Inf/out-of-bounds, fail closed to MANUAL_REVIEW / R0_SIGNAL_UNAVAILABLE.
    3. Stage-2 execution validation:
       - If stage2_status in ('failed', 'unavailable') and second stage was required: fail closed to R0.
       - If stage2_status == 'skipped' but p >= t_review (where stage 2 was needed): fail closed to R0.
    4. Required secondary signal check:
       - If disagreement enabled, stage 2 not skipped, and u is invalid/NaN/None: fail closed to R0.
       - If novelty enabled and n is invalid/NaN/None: fail closed to R0.
    5. High-Risk Rule: p >= t_alert -> FRAUD_ALERT, R1_HIGH_RISK.
    6. Intermediate-Risk Rule: p >= t_review -> MANUAL_REVIEW, R2_INTERMEDIATE_RISK.
    7. Disagreement Rule: u >= u_threshold -> MANUAL_REVIEW, R3_MODEL_DISAGREEMENT.
    8. Novelty Rule: n >= n_threshold -> MANUAL_REVIEW, R4_UNFAMILIAR_INPUT.
    9. Default Reliable Low Risk -> ROUTINE, R5_LOW_RISK_RELIABLE.

    Returns:
    - (Action, ReasonCode) tuple.
    """
    # 1. Config validation
    is_cfg_valid, _ = validate_router_config(cfg)
    if not is_cfg_valid:
        return Action.MANUAL_REVIEW, ReasonCode.R0_SIGNAL_UNAVAILABLE

    t_alert = float(cfg["t_alert"])
    t_review = float(cfg["t_review"])
    disagreement_enabled = bool(cfg.get("disagreement_enabled", False))
    novelty_enabled = bool(cfg.get("novelty_enabled", False))

    # 2. Risk probability p validation
    if p is None or not isinstance(p, (int, float)) or not np.isfinite(p):
        return Action.MANUAL_REVIEW, ReasonCode.R0_SIGNAL_UNAVAILABLE

    p_val = float(p)
    if not (0.0 <= p_val <= 1.0):
        return Action.MANUAL_REVIEW, ReasonCode.R0_SIGNAL_UNAVAILABLE

    # 3. Stage 2 status validation
    if stage2_status in ["failed", "unavailable"]:
        if disagreement_enabled:
            return Action.MANUAL_REVIEW, ReasonCode.R0_SIGNAL_UNAVAILABLE

    if stage2_status == "skipped":
        # Stage 2 skip is allowed only for low-risk routine transactions
        if p_val >= t_review:
            return Action.MANUAL_REVIEW, ReasonCode.R0_SIGNAL_UNAVAILABLE

    # 4. Secondary signal validation
    if disagreement_enabled and stage2_status != "skipped":
        is_u2 = cfg.get("disagreement_variant") == "u2_rank_residual"
        if u is None or not isinstance(u, (int, float)) or not np.isfinite(u):
            return Action.MANUAL_REVIEW, ReasonCode.R0_SIGNAL_UNAVAILABLE
        if not is_u2 and u < 0.0:
            return Action.MANUAL_REVIEW, ReasonCode.R0_SIGNAL_UNAVAILABLE

    if novelty_enabled:
        if n is None or not isinstance(n, (int, float)) or not np.isfinite(n) or n < 0.0:
            return Action.MANUAL_REVIEW, ReasonCode.R0_SIGNAL_UNAVAILABLE

    # 5. High-Risk Rule (R1)
    if p_val >= t_alert:
        return Action.FRAUD_ALERT, ReasonCode.R1_HIGH_RISK

    # 6. Intermediate-Risk Rule (R2)
    if p_val >= t_review:
        return Action.MANUAL_REVIEW, ReasonCode.R2_INTERMEDIATE_RISK

    # 7. Disagreement Rule (R3)
    if disagreement_enabled and stage2_status != "skipped":
        u_threshold = float(cfg["u_threshold"])
        if float(u) >= u_threshold:
            return Action.MANUAL_REVIEW, ReasonCode.R3_MODEL_DISAGREEMENT

    # 8. Novelty Rule (R4)
    if novelty_enabled:
        n_threshold = float(cfg["n_threshold"])
        if float(n) >= n_threshold:
            return Action.MANUAL_REVIEW, ReasonCode.R4_UNFAMILIAR_INPUT

    # 9. Low-Risk Reliable Routine (R5)
    return Action.ROUTINE, ReasonCode.R5_LOW_RISK_RELIABLE


def route_batch(
    P: Optional[Union[pd.Series, np.ndarray, List[float]]] = None,
    U: Optional[Union[pd.Series, np.ndarray, List[float]]] = None,
    N: Optional[Union[pd.Series, np.ndarray, List[float]]] = None,
    cfg: Optional[Dict[str, Any]] = None,
    stage2_status: Union[str, List[str], np.ndarray] = "computed",
    p: Optional[Union[pd.Series, np.ndarray, List[float]]] = None,
    u: Optional[Union[pd.Series, np.ndarray, List[float]]] = None,
    n: Optional[Union[pd.Series, np.ndarray, List[float]]] = None,
    **kwargs,
) -> pd.DataFrame:
    """
    Route a batch of samples and emit auditable decision rows.

    Integrity Guard:
    Explicitly rejects if true labels (true_label, isFraud) are passed as kwargs or inputs.
    """
    forbidden_inputs = ["true_label", "isFraud", "label", "y_true"]
    for forb in forbidden_inputs:
        if forb in kwargs:
            raise ValueError(f"LEAKAGE VIOLATION: '{forb}' cannot be supplied to route_batch!")

    if P is None:
        if p is not None:
            P = p
        else:
            raise ValueError("route_batch requires risk probabilities (P or p)")

    if U is None and u is not None:
        U = u
    if N is None and n is not None:
        N = n

    P_arr = np.asarray(P, dtype=object)
    n_samples = len(P_arr)

    U_arr = np.asarray(U, dtype=object) if U is not None else [None] * n_samples
    N_arr = np.asarray(N, dtype=object) if N is not None else [None] * n_samples

    if isinstance(stage2_status, str):
        stage2_arr = [stage2_status] * n_samples
    else:
        stage2_arr = list(stage2_status)

    actions = []
    reasons = []

    for i in range(n_samples):
        act, rsn = route(
            p=P_arr[i],
            u=U_arr[i],
            n=N_arr[i],
            cfg=cfg,
            stage2_status=stage2_arr[i],
        )
        actions.append(act.value)
        reasons.append(rsn.value)

    out_df = pd.DataFrame({
        "action": actions,
        "reason": reasons,
        "p": [float(p) if p is not None and np.isfinite(p) else np.nan for p in P_arr],
        "u": [float(u) if u is not None and np.isfinite(u) else np.nan for u in U_arr],
        "n": [float(n) if n is not None and np.isfinite(n) else np.nan for n in N_arr],
        "stage2_status": stage2_arr,
    })

    return out_df
