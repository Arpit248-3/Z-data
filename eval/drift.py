"""SignalGate Distribution Drift Monitoring Module

Implements Population Stability Index (PSI) and Kolmogorov-Smirnov (KS) tests,
strictly complying with Blueprint Section 5.5 and 6.3:
- Reference quantiles computed from training partition.
- Robust quantile binning with epsilon smoothing to prevent divide-by-zero or log-of-zero.
- Standard stability thresholds:
    PSI < 0.10: Stable (negligible drift)
    0.10 <= PSI <= 0.20: Moderate drift
    PSI > 0.20: Significant distribution shift
- Two-sample Kolmogorov-Smirnov test via scipy.stats.ks_2samp.
- Explicit discipline: PSI and KS are distribution-monitoring indicators, not fraud assertions.
"""

from typing import Any, Dict, List, Optional, Sequence, Union
import numpy as np
import pandas as pd
from scipy.stats import ks_2samp


def calculate_psi(
    reference: Union[Sequence[float], np.ndarray, pd.Series],
    actual: Union[Sequence[float], np.ndarray, pd.Series],
    bins: int = 10,
    epsilon: float = 1e-4,
) -> Dict[str, Any]:
    """Compute Population Stability Index (PSI) using reference quantile bins.

    Args:
        reference: Reference feature sample (e.g. from training partition).
        actual: Comparison feature sample (e.g. from test or shift scenario).
        bins: Number of quantile bins to establish on reference distribution.
        epsilon: Small positive smoothing constant for empty bins.

    Returns:
        Dict[str, Any]: PSI value, stability category, and bin-level frequency table.
    """
    ref = np.asarray(reference, dtype=float)
    act = np.asarray(actual, dtype=float)

    # Filter out NaNs and infs for distributional calculation
    ref_clean = ref[np.isfinite(ref)]
    act_clean = act[np.isfinite(act)]

    if len(ref_clean) == 0 or len(act_clean) == 0:
        return {
            "psi": None,
            "status": "UNAVAILABLE_INSUFFICIENT_FINITE_DATA",
            "category": "unknown",
            "ref_valid_count": len(ref_clean),
            "act_valid_count": len(act_clean),
        }

    # Determine quantile bin edges from reference
    quantiles = np.linspace(0.0, 1.0, bins + 1)
    bin_edges = np.unique(np.quantile(ref_clean, quantiles))

    # If distribution has low variance (e.g. all values equal), construct fallback bins
    if len(bin_edges) < 2:
        val = bin_edges[0] if len(bin_edges) == 1 else 0.0
        bin_edges = np.array([val - 1.0, val, val + 1.0])

    # Extend boundaries to infinity to capture out-of-range comparison values
    bin_edges[0] = -np.inf
    bin_edges[-1] = np.inf

    # Compute frequency in each bin
    ref_counts, _ = np.histogram(ref_clean, bins=bin_edges)
    act_counts, _ = np.histogram(act_clean, bins=bin_edges)

    # Convert to proportions with epsilon smoothing
    ref_props = ref_counts / len(ref_clean)
    act_props = act_counts / len(act_clean)

    # Apply epsilon smoothing and renormalize
    ref_props = np.where(ref_props == 0, epsilon, ref_props)
    act_props = np.where(act_props == 0, epsilon, act_props)
    ref_props = ref_props / np.sum(ref_props)
    act_props = act_props / np.sum(act_props)

    # PSI formula: sum((act - ref) * ln(act / ref))
    psi_terms = (act_props - ref_props) * np.log(act_props / ref_props)
    psi_val = float(np.sum(psi_terms))

    if psi_val < 0.10:
        category = "stable"
    elif psi_val <= 0.20:
        category = "moderate_drift"
    else:
        category = "significant_drift"

    return {
        "psi": round(psi_val, 6),
        "category": category,
        "n_bins": len(ref_counts),
        "ref_valid_count": len(ref_clean),
        "act_valid_count": len(act_clean),
    }


def calculate_feature_drift(
    reference: Union[Sequence[float], np.ndarray, pd.Series],
    actual: Union[Sequence[float], np.ndarray, pd.Series],
    feature_name: str,
    bins: int = 10,
) -> Dict[str, Any]:
    """Calculate combined PSI and two-sample Kolmogorov-Smirnov test for a feature."""
    ref = np.asarray(reference, dtype=float)
    act = np.asarray(actual, dtype=float)

    ref_nan_rate = float(np.mean(np.isnan(ref))) if len(ref) > 0 else 0.0
    act_nan_rate = float(np.mean(np.isnan(act))) if len(act) > 0 else 0.0

    psi_res = calculate_psi(ref, act, bins=bins)

    ref_clean = ref[np.isfinite(ref)]
    act_clean = act[np.isfinite(act)]

    if len(ref_clean) > 0 and len(act_clean) > 0:
        ks_stat, ks_pval = ks_2samp(ref_clean, act_clean)
        ks_stat = float(ks_stat)
        ks_pval = float(ks_pval)
    else:
        ks_stat, ks_pval = None, None

    return {
        "feature": feature_name,
        "psi": psi_res.get("psi"),
        "drift_category": psi_res.get("category"),
        "ks_statistic": round(ks_stat, 6) if ks_stat is not None else None,
        "ks_pvalue": round(ks_pval, 6) if ks_pval is not None else None,
        "ref_sample_count": len(ref),
        "act_sample_count": len(act),
        "ref_missing_rate": round(ref_nan_rate, 4),
        "act_missing_rate": round(act_nan_rate, 4),
        "missing_rate_delta": round(act_nan_rate - ref_nan_rate, 4),
    }


def monitor_dataset_drift(
    reference_df: pd.DataFrame,
    comparison_df: pd.DataFrame,
    features: List[str],
    scenario_id: str = "S0",
    status: str = "SYNTHETIC_SMOKE_ONLY",
) -> Dict[str, Any]:
    """Run comprehensive drift monitoring across selected features."""
    results = []
    valid_psis = []
    significant_count = 0
    moderate_count = 0

    for feat in features:
        if feat in reference_df.columns and feat in comparison_df.columns:
            feat_drift = calculate_feature_drift(
                reference_df[feat],
                comparison_df[feat],
                feature_name=feat,
            )
            results.append(feat_drift)
            psi = feat_drift.get("psi")
            if psi is not None:
                valid_psis.append(psi)
                cat = feat_drift.get("drift_category")
                if cat == "significant_drift":
                    significant_count += 1
                elif cat == "moderate_drift":
                    moderate_count += 1

    mean_psi = float(np.mean(valid_psis)) if valid_psis else 0.0
    max_psi = float(np.max(valid_psis)) if valid_psis else 0.0

    return {
        "status": status,
        "scenario_id": scenario_id,
        "features_monitored": len(results),
        "significant_drift_features": significant_count,
        "moderate_drift_features": moderate_count,
        "mean_psi": round(mean_psi, 6),
        "max_psi": round(max_psi, 6),
        "feature_drift_reports": results,
        "notice": (
            "Distribution monitoring indicators (PSI/KS) quantify covariate shift "
            "and do not constitute proof of fraud or policy failure."
        ),
    }
