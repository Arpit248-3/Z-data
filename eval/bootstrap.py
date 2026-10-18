"""SignalGate Paired Bootstrap Module

Implements paired bootstrap resampling for policy comparison on identical rows,
strictly adhering to Blueprint Section 6.4 and 8.2:
- Resamples identical row indices across policies in each replicate.
- Computes paired differences: metric(Policy A) - metric(Policy B).
- Constructs 95% empirical percentile confidence intervals.
- Handles degenerate resamples (e.g. zero fraud labels in resample) with documented skipping.
- Assesses statistical conclusiveness: labeled inconclusive if 95% CI spans zero.
"""

from typing import Any, Callable, Dict, Optional, Sequence, Tuple, Union
import numpy as np
import pandas as pd


def default_recall_metric(y: np.ndarray, mask: np.ndarray) -> float:
    """Calculate recall on a sample."""
    pos = np.sum(y == 1)
    if pos == 0:
        return np.nan
    return float(np.sum((y == 1) & mask) / pos)


def paired_bootstrap(
    y_true: Union[Sequence[int], np.ndarray, pd.Series],
    mask_a: Union[Sequence[bool], np.ndarray, pd.Series],
    mask_b: Union[Sequence[bool], np.ndarray, pd.Series],
    metric: Optional[Callable[[np.ndarray, np.ndarray], float]] = None,
    n_resamples: int = 1000,
    seed: int = 42,
    alpha: float = 0.05,
    status: str = "SYNTHETIC_SMOKE_ONLY",
) -> Dict[str, Any]:
    """Perform paired bootstrap resampling on identical rows for two policies.

    Args:
        y_true: Binary ground-truth labels (0 or 1).
        mask_a: Boolean escalation mask for candidate policy A (e.g. SignalGate).
        mask_b: Boolean escalation mask for baseline policy B (e.g. B2 Top-B).
        metric: Metric function with signature (y_sample, mask_sample) -> float.
                Defaults to recall.
        n_resamples: Number of bootstrap iterations (default 1000).
        seed: Random seed for deterministic reproducibility.
        alpha: Significance level for 100*(1 - alpha)% confidence interval (default 0.05 -> 95% CI).
        status: Dataset status string.

    Returns:
        Dict[str, Any] containing point estimate, CI bounds, and diagnostic metadata.
    """
    y = np.asarray(y_true, dtype=int)
    mA = np.asarray(mask_a, dtype=bool)
    mB = np.asarray(mask_b, dtype=bool)
    n = len(y)

    if not (len(mA) == n and len(mB) == n):
        raise ValueError(f"Length mismatch: y ({n}), mask_a ({len(mA)}), mask_b ({len(mB)})")

    if metric is None:
        eval_fn = default_recall_metric
    else:
        eval_fn = metric

    # Calculate observed point estimates on original data
    val_a = eval_fn(y, mA)
    val_b = eval_fn(y, mB)
    if np.isnan(val_a) or np.isnan(val_b):
        raise ValueError("Cannot compute point estimate: zero positive labels in dataset")

    point_estimate_diff = float(val_a - val_b)

    rng = np.random.default_rng(seed)
    diffs = []
    degenerate_count = 0

    for _ in range(n_resamples):
        boot_idx = rng.integers(0, n, size=n)
        y_boot = y[boot_idx]
        mA_boot = mA[boot_idx]
        mB_boot = mB[boot_idx]

        score_a = eval_fn(y_boot, mA_boot)
        score_b = eval_fn(y_boot, mB_boot)

        # Handle degenerate resample (e.g. 0 positive labels)
        if np.isnan(score_a) or np.isnan(score_b):
            degenerate_count += 1
            continue

        diffs.append(score_a - score_b)

    diffs_arr = np.asarray(diffs, dtype=float)
    valid_count = len(diffs_arr)

    min_valid_threshold = min(100, max(10, int(0.80 * n_resamples)))
    if valid_count < min_valid_threshold:
        raise ValueError(
            f"Insufficient valid bootstrap resamples ({valid_count}/{n_resamples}). "
            "Data sample size or fraud prevalence is too small for meaningful bootstrap."
        )

    # Compute empirical percentiles for (1 - alpha) CI
    lo_pct = (alpha / 2.0) * 100.0
    hi_pct = (1.0 - alpha / 2.0) * 100.0
    ci_lower = float(np.percentile(diffs_arr, lo_pct))
    ci_upper = float(np.percentile(diffs_arr, hi_pct))

    # Empirical two-sided p-value against null hypothesis (diff == 0)
    # Fraction of resampled differences on the opposite side of zero from point estimate
    if point_estimate_diff > 0:
        p_val = 2.0 * float(np.mean(diffs_arr <= 0))
    elif point_estimate_diff < 0:
        p_val = 2.0 * float(np.mean(diffs_arr >= 0))
    else:
        p_val = 1.0
    p_val = min(1.0, max(0.0, p_val))

    # Conclusive if zero is NOT in the 95% confidence interval
    is_conclusive = bool(ci_lower > 0.0 or ci_upper < 0.0)

    return {
        "status": status,
        "method": "paired_percentile_bootstrap",
        "seed": seed,
        "n_resamples_requested": n_resamples,
        "n_resamples_valid": valid_count,
        "degenerate_resamples": degenerate_count,
        "alpha": alpha,
        "confidence_level": 1.0 - alpha,
        "metric_name": "recall",
        "policy_a_observed": round(float(val_a), 6),
        "policy_b_observed": round(float(val_b), 6),
        "point_estimate_diff": round(point_estimate_diff, 6),
        "ci_lower": round(ci_lower, 6),
        "ci_upper": round(ci_upper, 6),
        "p_value_two_sided": round(p_val, 6),
        "is_conclusive": is_conclusive,
        "conclusion": (
            "Statistically distinguishable difference at 95% confidence."
            if is_conclusive
            else "Inconclusive: 95% confidence interval spans zero. Do not claim superiority."
        ),
    }


def paired_bootstrap_tuple(
    y_true: Union[Sequence[int], np.ndarray, pd.Series],
    mask_a: Union[Sequence[bool], np.ndarray, pd.Series],
    mask_b: Union[Sequence[bool], np.ndarray, pd.Series],
    metric: Optional[Callable[[np.ndarray, np.ndarray], float]] = None,
    n_resamples: int = 1000,
    seed: int = 42,
) -> Tuple[float, float, float]:
    """Compatibility tuple signature: (diff, lo, hi)."""
    res = paired_bootstrap(
        y_true=y_true,
        mask_a=mask_a,
        mask_b=mask_b,
        metric=metric,
        n_resamples=n_resamples,
        seed=seed,
    )
    return res["point_estimate_diff"], res["ci_lower"], res["ci_upper"]
