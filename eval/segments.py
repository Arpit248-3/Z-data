"""SignalGate Segment-Level Escalation Analysis Module

Analyzes policy escalation rates across business and card segments (ProductCD, card4),
strictly adhering to Blueprint Section 6.3 and 8.2:
- Tracks group counts, fraud prevalence, and action distributions (Alert, Review, Routine, Deferred).
- Computes group-level touched rates, recall, and precision.
- Handles rare and missing categories safely without divide-by-zero errors.
- Enforces strict regulatory discipline: explicitly disclaims demographic fairness certification
  from benchmark merchant/card categories.
"""

from typing import Any, Dict, List, Optional, Sequence, Union
import numpy as np
import pandas as pd


def analyze_segment_escalation(
    segment_series: Union[Sequence[Any], pd.Series, np.ndarray],
    actions: Union[Sequence[str], pd.Series, np.ndarray],
    y_true: Union[Sequence[int], pd.Series, np.ndarray],
    segment_name: str = "ProductCD",
    min_sample_size: int = 10,
    status: str = "SYNTHETIC_SMOKE_ONLY",
) -> Dict[str, Any]:
    """Analyze escalation and triage metrics by segment category.

    Args:
        segment_series: Segment category values (e.g. 'W', 'C', 'visa', 'mastercard').
        actions: Triage action strings ('FRAUD_ALERT', 'MANUAL_REVIEW', 'ROUTINE', 'DEFERRED').
        y_true: Binary ground-truth labels (0 or 1).
        segment_name: Name of the segment column.
        min_sample_size: Minimum sample size to include in group disparity ratio.
        status: Dataset status string.

    Returns:
        Dict[str, Any] containing group breakdown, disparity ratio, and disclaimers.
    """
    seg = pd.Series(segment_series).fillna("MISSING").astype(str)
    act = pd.Series(actions).astype(str)
    y = pd.Series(y_true).astype(int)

    n_total = len(seg)
    if not (len(act) == n_total and len(y) == n_total):
        raise ValueError("Length mismatch between segment_series, actions, and y_true")

    df = pd.DataFrame({
        "segment": seg,
        "action": act,
        "is_fraud": y,
    })

    groups = []
    touched_rates = []

    for group_val, grp in df.groupby("segment"):
        grp_size = len(grp)
        fraud_cnt = int(grp["is_fraud"].sum())
        prevalence = float(fraud_cnt / grp_size) if grp_size > 0 else 0.0

        alert_cnt = int((grp["action"] == "FRAUD_ALERT").sum())
        review_cnt = int((grp["action"] == "MANUAL_REVIEW").sum())
        deferred_cnt = int(((grp["action"] == "DEFERRED") | (grp["action"] == "HELD")).sum())
        routine_cnt = int((grp["action"] == "ROUTINE").sum())
        touched_cnt = alert_cnt + review_cnt

        touched_rate = float(touched_cnt / grp_size) if grp_size > 0 else 0.0
        caught_fraud = int(((grp["is_fraud"] == 1) & (grp["action"].isin(["FRAUD_ALERT", "MANUAL_REVIEW"]))).sum())

        recall = float(caught_fraud / fraud_cnt) if fraud_cnt > 0 else None
        precision = float(caught_fraud / touched_cnt) if touched_cnt > 0 else None

        if grp_size >= min_sample_size:
            touched_rates.append(touched_rate)

        groups.append({
            "segment_value": group_val,
            "sample_size": grp_size,
            "pct_of_total": round(float(grp_size / n_total), 4),
            "fraud_count": fraud_cnt,
            "fraud_prevalence": round(prevalence, 6),
            "alert_count": alert_cnt,
            "review_count": review_cnt,
            "routine_count": routine_cnt,
            "deferred_count": deferred_cnt,
            "touched_count": touched_cnt,
            "touched_rate": round(touched_rate, 6),
            "caught_fraud": caught_fraud,
            "recall": round(recall, 6) if recall is not None else None,
            "precision": round(precision, 6) if precision is not None else None,
        })

    # Sort groups descending by sample size
    groups = sorted(groups, key=lambda x: x["sample_size"], reverse=True)

    # Disparity ratio (min / max touched rate among adequately sized groups)
    if len(touched_rates) >= 2 and max(touched_rates) > 0:
        disparity_ratio = float(min(touched_rates) / max(touched_rates))
    else:
        disparity_ratio = None

    return {
        "status": status,
        "segment_name": segment_name,
        "total_transactions": n_total,
        "unique_groups": len(groups),
        "min_sample_size_threshold": min_sample_size,
        "groups": groups,
        "disparity_ratio_min_over_max": round(disparity_ratio, 4) if disparity_ratio is not None else None,
        "disclaimer": (
            "Benchmark segment screening only: ProductCD and card4 represent merchant transaction "
            "and network classes, not demographic protected attributes. Demographic fairness certification "
            "is explicitly not claimed."
        ),
    }


def analyze_all_segments(
    eval_df: pd.DataFrame,
    actions: Sequence[str],
    y_true: Sequence[int],
    segment_columns: Optional[List[str]] = None,
    status: str = "SYNTHETIC_SMOKE_ONLY",
) -> Dict[str, Any]:
    """Run segment analysis across all provided segment columns."""
    if segment_columns is None:
        segment_columns = ["ProductCD", "card4"]

    reports = {}
    for col in segment_columns:
        if col in eval_df.columns:
            reports[col] = analyze_segment_escalation(
                segment_series=eval_df[col],
                actions=actions,
                y_true=y_true,
                segment_name=col,
                status=status,
            )
        else:
            reports[col] = {
                "status": "UNAVAILABLE",
                "segment_name": col,
                "reason": f"Column '{col}' not found in evaluation dataframe.",
            }

    return {
        "status": status,
        "segment_reports": reports,
    }
