"""SignalGate Evaluation Metrics Module

Provides comprehensive evaluation metrics adhering strictly to Blueprint Section 6.3 and 8.2:
- Operational action rates (Alert, Review, Routine, Deferred)
- Strict touched-rate definition: (ALERT + REVIEW) / total_transactions
- Binary evaluation masks and contingency counts (TP, FP, FN, TN)
- Recall at matched touched rate, precision, FPR, PR-AUC
- Confident-miss and ROUTINE-lane fraud rates
- Transaction-amount weighted fraud metrics
- Expected Calibration Error (ECE)
"""

from typing import Any, Dict, Optional, Sequence, Union
import numpy as np
import pandas as pd
from sklearn.metrics import precision_recall_curve, auc


def recall_at_touched(
    y_true: Union[Sequence[int], np.ndarray, pd.Series],
    touched_mask: Union[Sequence[bool], np.ndarray, pd.Series],
) -> float:
    """Calculate recall strictly among cases in the touched mask.

    Args:
        y_true: Binary ground-truth fraud labels (0 or 1).
        touched_mask: Boolean mask indicating touched/escalated transactions.

    Returns:
        float: Fraction of total fraud caught (0.0 if no fraud).
    """
    y = np.asarray(y_true, dtype=int)
    m = np.asarray(touched_mask, dtype=bool)
    if len(y) != len(m):
        raise ValueError(f"Length mismatch: y_true ({len(y)}) vs touched_mask ({len(m)})")
    total_positives = int(np.sum(y == 1))
    if total_positives == 0:
        return 0.0
    caught = int(np.sum((y == 1) & m))
    return float(caught / total_positives)


def value_caught(
    y_true: Union[Sequence[int], np.ndarray, pd.Series],
    amounts: Union[Sequence[float], np.ndarray, pd.Series],
    touched_mask: Union[Sequence[bool], np.ndarray, pd.Series],
) -> float:
    """Calculate transaction value of caught fraud cases."""
    y = np.asarray(y_true, dtype=int)
    amt = np.asarray(amounts, dtype=float)
    m = np.asarray(touched_mask, dtype=bool)
    if not (len(y) == len(amt) == len(m)):
        raise ValueError("Length mismatch between y_true, amounts, and touched_mask")
    return float(np.sum(amt[(y == 1) & m]))


def value_missed(
    y_true: Union[Sequence[int], np.ndarray, pd.Series],
    amounts: Union[Sequence[float], np.ndarray, pd.Series],
    touched_mask: Union[Sequence[bool], np.ndarray, pd.Series],
) -> float:
    """Calculate transaction value of missed fraud cases."""
    y = np.asarray(y_true, dtype=int)
    amt = np.asarray(amounts, dtype=float)
    m = np.asarray(touched_mask, dtype=bool)
    if not (len(y) == len(amt) == len(m)):
        raise ValueError("Length mismatch between y_true, amounts, and touched_mask")
    return float(np.sum(amt[(y == 1) & (~m)]))


def ece(
    y_true: Union[Sequence[int], np.ndarray, pd.Series],
    p_pred: Union[Sequence[float], np.ndarray, pd.Series],
    bins: int = 10,
) -> float:
    """Compute Expected Calibration Error (ECE) across equal-width bins."""
    y = np.asarray(y_true, dtype=float)
    p = np.asarray(p_pred, dtype=float)
    if len(y) != len(p):
        raise ValueError("Length mismatch between y_true and p_pred")
    n = len(y)
    if n == 0:
        return 0.0
    bin_boundaries = np.linspace(0.0, 1.0, bins + 1)
    ece_val = 0.0
    for i in range(bins):
        bin_lo = bin_boundaries[i]
        bin_hi = bin_boundaries[i + 1]
        if i == bins - 1:
            in_bin = (p >= bin_lo) & (p <= bin_hi)
        else:
            in_bin = (p >= bin_lo) & (p < bin_hi)
        bin_count = int(np.sum(in_bin))
        if bin_count > 0:
            bin_acc = float(np.mean(y[in_bin]))
            bin_conf = float(np.mean(p[in_bin]))
            ece_val += (bin_count / n) * abs(bin_acc - bin_conf)
    return float(ece_val)


def calculate_pr_auc(
    y_true: Union[Sequence[int], np.ndarray, pd.Series],
    scores: Union[Sequence[float], np.ndarray, pd.Series],
) -> float:
    """Calculate Precision-Recall Area Under Curve (PR-AUC)."""
    y = np.asarray(y_true, dtype=int)
    s = np.asarray(scores, dtype=float)
    if len(np.unique(y)) < 2:
        return 0.0
    precision_curve, recall_curve, _ = precision_recall_curve(y, s)
    return float(auc(recall_curve, precision_curve))


def calculate_binary_metrics(
    y_true: Union[Sequence[int], np.ndarray, pd.Series],
    escalated_mask: Union[Sequence[bool], np.ndarray, pd.Series],
) -> Dict[str, Any]:
    """Calculate standard binary contingency table metrics."""
    y = np.asarray(y_true, dtype=int)
    m = np.asarray(escalated_mask, dtype=bool)
    n = len(y)
    if n != len(m):
        raise ValueError("Length mismatch between y_true and escalated_mask")
    total_pos = int(np.sum(y == 1))
    total_neg = int(np.sum(y == 0))
    tp = int(np.sum((y == 1) & m))
    fp = int(np.sum((y == 0) & m))
    fn = int(np.sum((y == 1) & (~m)))
    tn = int(np.sum((y == 0) & (~m)))

    recall = float(tp / total_pos) if total_pos > 0 else 0.0
    missed_fraud_rate = float(fn / total_pos) if total_pos > 0 else 0.0
    precision = float(tp / (tp + fp)) if (tp + fp) > 0 else 0.0
    fpr = float(fp / total_neg) if total_neg > 0 else 0.0

    return {
        "total_transactions": n,
        "total_positives": total_pos,
        "total_negatives": total_neg,
        "prevalence": float(total_pos / n) if n > 0 else 0.0,
        "tp": tp,
        "fp": fp,
        "fn": fn,
        "tn": tn,
        "recall": recall,
        "missed_fraud_rate": missed_fraud_rate,
        "precision": precision,
        "fpr": fpr,
    }


def calculate_policy_metrics(
    y_true: Union[Sequence[int], np.ndarray, pd.Series],
    actions: Union[Sequence[str], np.ndarray, pd.Series],
    amounts: Optional[Union[Sequence[float], np.ndarray, pd.Series]] = None,
    p_scores: Optional[Union[Sequence[float], np.ndarray, pd.Series]] = None,
) -> Dict[str, Any]:
    """Calculate multi-action triage metrics and operational touched rate.

    Adheres strictly to the blueprint:
    - touched_rate = (ALERT + REVIEW) / total_transactions
    - Deferred cases are NOT counted as reviewed or routine; reported separately.
    - Confident-miss count = fraud cases routed to ROUTINE.
    - Routine fraud rate = fraud prevalence among ROUTINE cases.
    """
    y = np.asarray(y_true, dtype=int)
    act = np.asarray(actions, dtype=str)
    n = len(y)
    if n != len(act):
        raise ValueError("Length mismatch between y_true and actions")

    # Action counts
    alert_mask = act == "FRAUD_ALERT"
    review_mask = act == "MANUAL_REVIEW"
    routine_mask = act == "ROUTINE"
    deferred_mask = (act == "DEFERRED") | (act == "HELD")
    touched_mask = alert_mask | review_mask

    alert_count = int(np.sum(alert_mask))
    review_count = int(np.sum(review_mask))
    routine_count = int(np.sum(routine_mask))
    deferred_count = int(np.sum(deferred_mask))
    touched_count = alert_count + review_count

    total_pos = int(np.sum(y == 1))
    total_neg = int(np.sum(y == 0))
    prevalence = float(total_pos / n) if n > 0 else 0.0

    # Rates
    touched_rate = float(touched_count / n) if n > 0 else 0.0
    alert_rate = float(alert_count / n) if n > 0 else 0.0
    review_rate = float(review_count / n) if n > 0 else 0.0
    routine_rate = float(routine_count / n) if n > 0 else 0.0
    deferred_rate = float(deferred_count / n) if n > 0 else 0.0

    # Operational binary view (Escalated vs Not Escalated)
    # Escalated = touched (ALERT + REVIEW)
    tp = int(np.sum((y == 1) & touched_mask))
    fp = int(np.sum((y == 0) & touched_mask))
    fn = int(np.sum((y == 1) & (~touched_mask)))
    tn = int(np.sum((y == 0) & (~touched_mask)))

    recall = float(tp / total_pos) if total_pos > 0 else 0.0
    missed_fraud_rate = float(fn / total_pos) if total_pos > 0 else 0.0
    precision = float(tp / (tp + fp)) if (tp + fp) > 0 else 0.0
    fpr = float(fp / total_neg) if total_neg > 0 else 0.0

    # Lane-specific fraud counts
    fraud_in_alert = int(np.sum((y == 1) & alert_mask))
    fraud_in_review = int(np.sum((y == 1) & review_mask))
    fraud_in_routine = int(np.sum((y == 1) & routine_mask))
    fraud_in_deferred = int(np.sum((y == 1) & deferred_mask))

    # Confident misses: actual fraud explicitly classified as ROUTINE
    confident_miss_count = fraud_in_routine
    routine_fraud_rate = (
        float(fraud_in_routine / routine_count) if routine_count > 0 else 0.0
    )

    metrics: Dict[str, Any] = {
        "total_transactions": n,
        "total_fraud": total_pos,
        "total_non_fraud": total_neg,
        "fraud_prevalence": round(prevalence, 6),
        "alert_count": alert_count,
        "review_count": review_count,
        "routine_count": routine_count,
        "deferred_count": deferred_count,
        "touched_count": touched_count,
        "touched_rate": round(touched_rate, 6),
        "alert_rate": round(alert_rate, 6),
        "review_rate": round(review_rate, 6),
        "routine_rate": round(routine_rate, 6),
        "deferred_rate": round(deferred_rate, 6),
        "tp": tp,
        "fp": fp,
        "fn": fn,
        "tn": tn,
        "recall_at_touched": round(recall, 6),
        "missed_fraud_rate": round(missed_fraud_rate, 6),
        "precision": round(precision, 6),
        "fpr": round(fpr, 6),
        "fraud_in_alert": fraud_in_alert,
        "fraud_in_review": fraud_in_review,
        "fraud_in_routine": fraud_in_routine,
        "fraud_in_deferred": fraud_in_deferred,
        "confident_miss_count": confident_miss_count,
        "routine_fraud_rate": round(routine_fraud_rate, 6),
    }

    # Amount-weighted metrics
    if amounts is not None:
        amt = np.asarray(amounts, dtype=float)
        total_fraud_val = float(np.sum(amt[y == 1]))
        caught_fraud_val = float(np.sum(amt[(y == 1) & touched_mask]))
        missed_fraud_val = float(np.sum(amt[(y == 1) & (~touched_mask)]))
        routine_miss_val = float(np.sum(amt[(y == 1) & routine_mask]))
        deferred_miss_val = float(np.sum(amt[(y == 1) & deferred_mask]))
        val_recall = (
            float(caught_fraud_val / total_fraud_val) if total_fraud_val > 0 else 0.0
        )
        metrics["amount_total_fraud"] = round(total_fraud_val, 2)
        metrics["amount_fraud_caught"] = round(caught_fraud_val, 2)
        metrics["amount_fraud_missed"] = round(missed_fraud_val, 2)
        metrics["amount_routine_missed"] = round(routine_miss_val, 2)
        metrics["amount_deferred_missed"] = round(deferred_miss_val, 2)
        metrics["amount_caught_pct"] = round(val_recall, 6)

    # Probabilistic metrics
    if p_scores is not None:
        p = np.asarray(p_scores, dtype=float)
        metrics["pr_auc"] = round(calculate_pr_auc(y, p), 6)
        metrics["ece"] = round(ece(y, p), 6)

    return metrics
