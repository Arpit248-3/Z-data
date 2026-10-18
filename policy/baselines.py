"""
SignalGate Mandatory Policy Baselines
Implements the reference comparison policies defined in Blueprint Section 6.1:
1. B1 — Fixed-threshold baseline: single probability threshold tuned on validation.
2. B2 — Top-B risk-ranking baseline (MANDATORY COMPARISON): escalates top B-fraction by risk score p.
3. B3a — Confidence-based deferral: escalates cases with highest model uncertainty 1 - max(p, 1-p).
4. B4 — Random escalation control: random selection matching budget under declared seed.

Integrity Guarantees:
- All policies are evaluated on the exact same rows and identical touched-rate budgets.
- True labels are NEVER passed as inputs to any policy or scoring rule.
- Labels are accessed strictly for offline metric computation.
"""

from typing import Any, Dict, List, Optional, Tuple, Union
import numpy as np
import pandas as pd


def compute_policy_metrics(
    escalated_mask: np.ndarray,
    y_true: np.ndarray,
    budget: float,
    policy_name: str,
) -> Dict[str, Any]:
    """
    Compute touched rate, caught fraud count, recall, and precision for an escalation mask.
    """
    n_samples = len(y_true)
    total_positives = int(np.sum(y_true))

    escalated_count = int(np.sum(escalated_mask))
    touched_rate = float(escalated_count / n_samples) if n_samples > 0 else 0.0

    caught_fraud = int(np.sum(y_true[escalated_mask]))
    missed_fraud = total_positives - caught_fraud

    recall = float(caught_fraud / total_positives) if total_positives > 0 else 0.0
    precision = float(caught_fraud / escalated_count) if escalated_count > 0 else 0.0

    return {
        "policy": policy_name,
        "target_budget": round(float(budget), 6),
        "total_transactions": n_samples,
        "escalated_count": escalated_count,
        "touched_rate": round(touched_rate, 6),
        "budget_matched": abs(touched_rate - budget) <= (1.0 / n_samples + 1e-6),
        "total_fraud": total_positives,
        "caught_fraud": caught_fraud,
        "missed_fraud": missed_fraud,
        "recall_at_touched": round(recall, 6),
        "precision": round(precision, 6),
    }


def baseline_fixed_threshold(
    p: Union[pd.Series, np.ndarray],
    threshold: float,
) -> np.ndarray:
    """
    B1 — Fixed-threshold baseline.
    Escalates all transactions where risk score p >= threshold.
    """
    p_arr = np.asarray(p, dtype=float)
    return p_arr >= threshold


def baseline_top_b(
    p: Union[pd.Series, np.ndarray],
    budget: float,
) -> np.ndarray:
    """
    B2 — Top-B risk-ranking baseline (Mandatory).
    Ranks transactions descending by risk score p and escalates the top fraction B = budget.
    """
    p_arr = np.asarray(p, dtype=float)
    n_samples = len(p_arr)

    k_capacity = int(np.floor(n_samples * budget))
    if k_capacity <= 0:
        return np.zeros(n_samples, dtype=bool)
    if k_capacity >= n_samples:
        return np.ones(n_samples, dtype=bool)

    # Deterministic stable ranking: highest p first
    # np.argsort on -p_arr gives descending order with stable index tie-breaking
    sorted_indices = np.argsort(-p_arr, kind="mergesort")
    top_indices = sorted_indices[:k_capacity]

    mask = np.zeros(n_samples, dtype=bool)
    mask[top_indices] = True
    return mask


def baseline_confidence_deferral(
    p: Union[pd.Series, np.ndarray],
    budget: float,
) -> np.ndarray:
    """
    B3a — Confidence-based deferral baseline.
    Uncertainty score c = 1 - max(p, 1-p) = min(p, 1-p).
    Escalates top fraction B of cases closest to the boundary (highest epistemic/aleatoric doubt).
    """
    p_arr = np.asarray(p, dtype=float)
    n_samples = len(p_arr)

    # Higher value indicates lower confidence / higher uncertainty
    uncertainty = np.minimum(p_arr, 1.0 - p_arr)

    k_capacity = int(np.floor(n_samples * budget))
    if k_capacity <= 0:
        return np.zeros(n_samples, dtype=bool)
    if k_capacity >= n_samples:
        return np.ones(n_samples, dtype=bool)

    sorted_indices = np.argsort(-uncertainty, kind="mergesort")
    top_indices = sorted_indices[:k_capacity]

    mask = np.zeros(n_samples, dtype=bool)
    mask[top_indices] = True
    return mask


def baseline_random(
    n_samples: int,
    budget: float,
    seed: int = 11,
) -> np.ndarray:
    """
    B4 — Random escalation control.
    Randomly escalates fraction B of transactions under declared seed.
    """
    rng = np.random.RandomState(seed)
    k_capacity = int(np.floor(n_samples * budget))

    if k_capacity <= 0:
        return np.zeros(n_samples, dtype=bool)
    if k_capacity >= n_samples:
        return np.ones(n_samples, dtype=bool)

    perm = rng.permutation(n_samples)
    selected_indices = perm[:k_capacity]

    mask = np.zeros(n_samples, dtype=bool)
    mask[selected_indices] = True
    return mask


def evaluate_policies_matched_budget(
    p: Union[pd.Series, np.ndarray],
    y_true: Union[pd.Series, np.ndarray],
    budget: float,
    threshold_cfg: Optional[Dict[str, Any]] = None,
    u: Optional[Union[pd.Series, np.ndarray]] = None,
    seed: int = 11,
) -> Dict[str, Any]:
    """
    Evaluate B1, B2, B3a, B4, and SignalGate router candidate policy on the identical rows
    under the exact matched touched-rate budget.
    """
    p_arr = np.asarray(p, dtype=float)
    y_arr = np.asarray(y_true, dtype=int)
    n_samples = len(p_arr)

    results = {}

    # 1. B2 — Top-B Risk Ranking (Primary benchmark)
    mask_b2 = baseline_top_b(p_arr, budget)
    results["B2_top_b_risk"] = compute_policy_metrics(mask_b2, y_arr, budget, "B2_top_b_risk")

    # 2. B1 — Fixed Threshold (tuned to match budget)
    # Determine threshold matching budget
    k_capacity = int(np.floor(n_samples * budget))
    if k_capacity > 0:
        sorted_p = np.sort(p_arr)
        t_fixed = float(sorted_p[-k_capacity])
    else:
        t_fixed = 1.0
    mask_b1 = baseline_fixed_threshold(p_arr, t_fixed)
    results["B1_fixed_threshold"] = compute_policy_metrics(mask_b1, y_arr, budget, "B1_fixed_threshold")
    results["B1_fixed_threshold"]["threshold"] = round(t_fixed, 6)

    # 3. B3a — Confidence Deferral
    mask_b3a = baseline_confidence_deferral(p_arr, budget)
    results["B3a_confidence_deferral"] = compute_policy_metrics(mask_b3a, y_arr, budget, "B3a_confidence_deferral")

    # 4. B4 — Random Control
    mask_b4 = baseline_random(n_samples, budget, seed=seed)
    results["B4_random_control"] = compute_policy_metrics(mask_b4, y_arr, budget, "B4_random_control")

    # 5. SignalGate Candidate Policy (if threshold config provided)
    if threshold_cfg is not None:
        from policy.router import route_batch
        from policy.governor import govern_decisions

        # Route transactions
        routed_df = route_batch(P=p_arr, U=u, cfg=threshold_cfg)
        # Apply capacity governor matching budget exactly
        governed_df, gov_metrics = govern_decisions(routed_df, capacity=k_capacity, priority_col="p")

        escalated_sg = governed_df["action"].isin(["FRAUD_ALERT", "MANUAL_REVIEW"]).to_numpy()
        results["SignalGate_candidate"] = compute_policy_metrics(escalated_sg, y_arr, budget, "SignalGate_candidate")
        results["SignalGate_candidate"]["governor_metrics"] = gov_metrics

        # Compute delta vs B2 (mandatory check)
        b2_recall = results["B2_top_b_risk"]["recall_at_touched"]
        sg_recall = results["SignalGate_candidate"]["recall_at_touched"]
        results["SignalGate_candidate"]["delta_recall_vs_B2_pp"] = round((sg_recall - b2_recall) * 100, 4)

    return results
