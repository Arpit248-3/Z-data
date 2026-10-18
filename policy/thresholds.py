"""
SignalGate Threshold Selection Module
Implements validation-only threshold optimization under pre-registered budget constraints:
- Operates strictly on validation split; never inspects or evaluates final test labels.
- Pre-registered budgets: 1.0x, 1.5x (primary), 2.0x, 3.0x training-set fraud prevalence.
- Enforces strict threshold ordering: 0 <= t_review < t_alert <= 1.
- Optimizes validation recall subject to touched_rate <= budget.
- Deterministic tie-breaking policy.
- Flags infeasible parameter combinations explicitly without fabricating thresholds.
"""

from dataclasses import asdict, dataclass
from typing import Any, Dict, List, Optional, Tuple, Union
import numpy as np
import pandas as pd

from policy.router import route_batch, Action


@dataclass
class ThresholdConfig:
    t_alert: float
    t_review: float
    u_threshold: Optional[float] = None
    disagreement_enabled: bool = False
    disagreement_variant: Optional[str] = None
    novelty_enabled: bool = False
    n_threshold: Optional[float] = None
    target_budget: float = 0.06525
    validation_metrics: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def evaluate_threshold_combination(
    p_val: np.ndarray,
    y_val: np.ndarray,
    t_alert: float,
    t_review: float,
    u_val: Optional[np.ndarray] = None,
    u_threshold: Optional[float] = None,
    disagreement_enabled: bool = False,
) -> Dict[str, Any]:
    """
    Simulate routing decisions for a single candidate threshold combination on validation data.
    """
    n_samples = len(p_val)
    total_positives = int(np.sum(y_val))

    # Vectorized fast simulation
    high_risk_mask = p_val >= t_alert
    inter_risk_mask = (p_val >= t_review) & (~high_risk_mask)

    if disagreement_enabled and u_val is not None and u_threshold is not None:
        disagree_mask = (u_val >= u_threshold) & (~high_risk_mask) & (~inter_risk_mask)
    else:
        disagree_mask = np.zeros(n_samples, dtype=bool)

    escalated_mask = high_risk_mask | inter_risk_mask | disagree_mask
    escalated_count = int(np.sum(escalated_mask))
    touched_rate = float(escalated_count / n_samples) if n_samples > 0 else 0.0

    caught_fraud = int(np.sum(y_val[escalated_mask]))
    recall = float(caught_fraud / total_positives) if total_positives > 0 else 0.0

    return {
        "t_alert": round(float(t_alert), 6),
        "t_review": round(float(t_review), 6),
        "u_threshold": round(float(u_threshold), 6) if u_threshold is not None else None,
        "disagreement_enabled": disagreement_enabled,
        "escalated_count": escalated_count,
        "touched_rate": round(touched_rate, 6),
        "caught_fraud": caught_fraud,
        "total_fraud": total_positives,
        "recall": round(recall, 6),
        "alert_count": int(np.sum(high_risk_mask)),
        "review_count": int(np.sum(inter_risk_mask)),
        "disagreement_count": int(np.sum(disagree_mask)),
    }


def select_thresholds(
    p_val: Union[pd.Series, np.ndarray],
    y_val: Union[pd.Series, np.ndarray],
    target_budget: float,
    u_val: Optional[Union[pd.Series, np.ndarray]] = None,
    use_disagreement: bool = False,
    disagreement_variant: Optional[str] = None,
) -> Tuple[Optional[ThresholdConfig], Dict[str, Any]]:
    """
    Select optimal thresholds strictly on validation data to maximize recall subject to touched_rate <= target_budget.

    Deterministic Tie-Breaking Policy:
    1. Highest validation recall.
    2. Closest touched_rate to target_budget (maximum allowed utilization without exceeding).
    3. Higher t_alert (concentrating highest risk into alerts).
    4. Higher t_review.

    Returns:
    - (ThresholdConfig or None if infeasible, detailed search summary)
    """
    p_arr = np.asarray(p_val, dtype=float)
    y_arr = np.asarray(y_val, dtype=int)
    u_arr = np.asarray(u_val, dtype=float) if u_val is not None else None

    n_samples = len(p_arr)
    if n_samples == 0:
        raise ValueError("Cannot select thresholds on empty validation data.")

    # Candidate quantiles for t_alert (top 1% to top 5% of risk)
    alert_quantiles = np.linspace(95.0, 99.5, 10)
    candidate_t_alerts = np.unique(np.percentile(p_arr, alert_quantiles))

    # Candidate quantiles for t_review (surrounding target budget)
    # Target budget quantile corresponds to (1.0 - budget)
    base_q = max(50.0, (1.0 - target_budget * 1.5) * 100)
    top_q = min(99.0, (1.0 - target_budget * 0.5) * 100)
    review_quantiles = np.linspace(base_q, top_q, 25)
    candidate_t_reviews = np.unique(np.percentile(p_arr, review_quantiles))

    # Disagreement candidates (if enabled)
    candidate_u_thresholds = [None]
    if use_disagreement and u_arr is not None:
        u_quantiles = [92.0, 95.0, 97.0, 98.5]
        candidate_u_thresholds = list(np.unique(np.percentile(u_arr, u_quantiles)))

    feasible_candidates = []

    for t_alert in candidate_t_alerts:
        for t_review in candidate_t_reviews:
            if t_review >= t_alert:
                continue

            for u_thresh in candidate_u_thresholds:
                metrics = evaluate_threshold_combination(
                    p_val=p_arr,
                    y_val=y_arr,
                    t_alert=t_alert,
                    t_review=t_review,
                    u_val=u_arr,
                    u_threshold=u_thresh,
                    disagreement_enabled=use_disagreement and (u_thresh is not None),
                )

                # Budget constraint: touched_rate <= target_budget (with numerical tolerance)
                if metrics["touched_rate"] <= target_budget + 1e-6:
                    feasible_candidates.append(metrics)

    if not feasible_candidates:
        search_summary = {
            "feasible": False,
            "target_budget": target_budget,
            "reason": "No candidate threshold combination met the constraint touched_rate <= target_budget.",
            "candidates_tested": len(candidate_t_alerts) * len(candidate_t_reviews) * len(candidate_u_thresholds),
        }
        return None, search_summary

    # Apply deterministic tie-breaking
    best_candidate = max(
        feasible_candidates,
        key=lambda c: (
            c["recall"],
            c["touched_rate"],
            c["t_alert"],
            c["t_review"],
        ),
    )

    config = ThresholdConfig(
        t_alert=best_candidate["t_alert"],
        t_review=best_candidate["t_review"],
        u_threshold=best_candidate["u_threshold"],
        disagreement_enabled=best_candidate["disagreement_enabled"],
        disagreement_variant=disagreement_variant if best_candidate["disagreement_enabled"] else None,
        target_budget=round(float(target_budget), 6),
        validation_metrics=best_candidate,
    )

    search_summary = {
        "feasible": True,
        "target_budget": target_budget,
        "selected_config": config.to_dict(),
        "candidates_tested": len(feasible_candidates),
        "selection_rule": "Maximize validation recall subject to touched_rate <= budget; tie-break on highest budget utilization.",
    }

    return config, search_summary


def sweep_thresholds_across_budgets(
    p_val: Union[pd.Series, np.ndarray],
    y_val: Union[pd.Series, np.ndarray],
    training_prevalence: float,
    budget_multiples: Optional[List[float]] = None,
    u_val: Optional[Union[pd.Series, np.ndarray]] = None,
    use_disagreement: bool = False,
    disagreement_variant: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Perform threshold sweep across pre-registered budget multiples (e.g. 1.0x, 1.5x, 2.0x, 3.0x).
    """
    if budget_multiples is None:
        budget_multiples = [1.0, 1.5, 2.0, 3.0]

    sweep_results = {}
    for mult in budget_multiples:
        budget = round(float(training_prevalence * mult), 6)
        key = f"{mult:.1f}x"
        cfg, summary = select_thresholds(
            p_val=p_val,
            y_val=y_val,
            target_budget=budget,
            u_val=u_val,
            use_disagreement=use_disagreement,
            disagreement_variant=disagreement_variant,
        )
        sweep_results[key] = {
            "multiple": mult,
            "target_budget": budget,
            "feasible": cfg is not None,
            "thresholds": cfg.to_dict() if cfg else None,
            "summary": summary,
        }

    return sweep_results
