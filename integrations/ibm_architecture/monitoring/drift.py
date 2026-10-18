"""SignalGate IBM Architecture Integration — Distribution Drift Monitoring Engine.

Computes Population Stability Index (PSI) and Kolmogorov-Smirnov (KS) test statistics
across feature windows without using ground-truth evaluation labels.

Key Invariants:
1. Ground-truth target `isFraud` and keys `TransactionID`, `TransactionDT` are strictly
   quarantined and rejected if passed for drift monitoring.
2. Quantile binning is derived strictly from the reference sample with epsilon smoothing.
3. Distribution indicators quantify covariate shift and do NOT assert fraud.
4. When operating in SYNTHETIC_SMOKE_ONLY, real-data benchmarks are explicitly marked DEFERRED.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Sequence, Union
import numpy as np
import pandas as pd
from scipy.stats import ks_2samp

from integrations.ibm_architecture.agent_view import check_for_quarantine_violations
from integrations.ibm_architecture.exceptions import GroundTruthQuarantineError


def calculate_psi(
    reference: Union[Sequence[float], np.ndarray, pd.Series],
    actual: Union[Sequence[float], np.ndarray, pd.Series],
    bins: int = 10,
    epsilon: float = 1e-4,
) -> Dict[str, Any]:
    """Compute Population Stability Index (PSI) using reference quantile bins.

    Args:
        reference: Reference feature sample (e.g. training/baseline partition).
        actual: Comparison feature sample (e.g. streaming window or scenario).
        bins: Number of quantile bins to establish on reference distribution.
        epsilon: Small positive smoothing constant for empty bins.

    Returns:
        Dict[str, Any]: PSI value, stability category, and bin metadata.
    """
    ref = np.asarray(reference, dtype=float)
    act = np.asarray(actual, dtype=float)

    ref_clean = ref[np.isfinite(ref)]
    act_clean = act[np.isfinite(act)]

    if len(ref_clean) == 0 or len(act_clean) == 0:
        return {
            "psi": None,
            "category": "unknown",
            "ref_valid_count": len(ref_clean),
            "act_valid_count": len(act_clean),
        }

    # Determine quantile bin edges from reference sample
    quantiles = np.linspace(0.0, 1.0, bins + 1)
    bin_edges = np.unique(np.quantile(ref_clean, quantiles))

    # Fallback for zero/low variance reference distributions
    if len(bin_edges) < 2:
        val = bin_edges[0] if len(bin_edges) == 1 else 0.0
        bin_edges = np.array([val - 1.0, val, val + 1.0])

    bin_edges[0] = -np.inf
    bin_edges[-1] = np.inf

    ref_counts, _ = np.histogram(ref_clean, bins=bin_edges)
    act_counts, _ = np.histogram(act_clean, bins=bin_edges)

    ref_props = ref_counts / len(ref_clean)
    act_props = act_counts / len(act_clean)

    # Epsilon smoothing to prevent division by zero or log(0)
    ref_props = np.where(ref_props == 0, epsilon, ref_props)
    act_props = np.where(act_props == 0, epsilon, act_props)
    ref_props = ref_props / np.sum(ref_props)
    act_props = act_props / np.sum(act_props)

    # PSI = sum((act - ref) * ln(act / ref))
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
    """Calculate combined PSI and two-sample Kolmogorov-Smirnov test for a single feature."""
    ref = np.asarray(reference, dtype=float)
    act = np.asarray(actual, dtype=float)

    ref_nan_rate = float(np.mean(np.isnan(ref))) if len(ref) > 0 else 0.0
    act_nan_rate = float(np.mean(np.isnan(act))) if len(act) > 0 else 0.0

    psi_res = calculate_psi(ref, act, bins=bins)

    ref_clean = ref[np.isfinite(ref)]
    act_clean = act[np.isfinite(act)]

    if len(ref_clean) > 0 and len(act_clean) > 0:
        ks_stat, ks_pval = ks_2samp(ref_clean, act_clean)
        ks_stat_val = round(float(ks_stat), 6)
        ks_pval_val = round(float(ks_pval), 6)
    else:
        ks_stat_val, ks_pval_val = None, None

    return {
        "feature": feature_name,
        "psi": psi_res.get("psi"),
        "drift_category": psi_res.get("category"),
        "ks_statistic": ks_stat_val,
        "ks_pvalue": ks_pval_val,
        "ref_sample_count": len(ref),
        "act_sample_count": len(act),
        "ref_missing_rate": round(ref_nan_rate, 4),
        "act_missing_rate": round(act_nan_rate, 4),
        "missing_rate_delta": round(act_nan_rate - ref_nan_rate, 4),
    }


class DistributionDriftCalculator:
    """Batch distribution drift calculator enforcing ground-truth quarantine and mode telemetry."""

    def __init__(self, bins: int = 10) -> None:
        self.bins = bins

    def compute_drift(
        self,
        reference_df: pd.DataFrame,
        comparison_df: pd.DataFrame,
        features: Optional[List[str]] = None,
        scenario_id: str = "S0_BASELINE",
        mode: str = "SYNTHETIC_SMOKE_ONLY",
    ) -> Dict[str, Any]:
        """Compute drift across allowed features between reference and comparison windows.

        Raises:
            GroundTruthQuarantineError: If `isFraud`, `TransactionID`, or `TransactionDT`
                are contained in the requested features list.
        """
        if features is None:
            # Default to numeric columns present in both, excluding quarantined columns
            common_cols = [
                c
                for c in reference_df.columns
                if c in comparison_df.columns
                and pd.api.types.is_numeric_dtype(reference_df[c])
            ]
            # Filter quarantine
            features = [
                c
                for c in common_cols
                if c.lower() not in {"isfraud", "transactionid", "transactiondt", "target"}
            ]

        # Enforce strict quarantine check on feature list
        for f in features:
            try:
                check_for_quarantine_violations({f: 0})
            except (ValueError, KeyError) as exc:
                raise GroundTruthQuarantineError(
                    f"Quarantined column '{f}' cannot be monitored for drift: {exc}"
                ) from exc

        results = []
        valid_psis = []
        significant_shift_features: List[str] = []
        moderate_shift_features: List[str] = []

        for feat in features:
            if feat in reference_df.columns and feat in comparison_df.columns:
                feat_res = calculate_feature_drift(
                    reference_df[feat],
                    comparison_df[feat],
                    feature_name=feat,
                    bins=self.bins,
                )
                results.append(feat_res)
                psi = feat_res.get("psi")
                if psi is not None:
                    valid_psis.append(psi)
                    cat = feat_res.get("drift_category")
                    if cat == "significant_drift":
                        significant_shift_features.append(feat)
                    elif cat == "moderate_drift":
                        moderate_shift_features.append(feat)

        mean_psi = float(np.mean(valid_psis)) if valid_psis else 0.0
        max_psi = float(np.max(valid_psis)) if valid_psis else 0.0
        overall_drift = len(significant_shift_features) > 0 or mean_psi >= 0.10

        return {
            "status": mode,
            "scenario_id": scenario_id,
            "features_monitored": len(results),
            "overall_drift_detected": overall_drift,
            "significant_shift_features": significant_shift_features,
            "moderate_shift_features": moderate_shift_features,
            "mean_psi": round(mean_psi, 6),
            "max_psi": round(max_psi, 6),
            "feature_drift_reports": results,
            "real_data_benchmark_status": (
                "DEFERRED" if mode == "SYNTHETIC_SMOKE_ONLY" else "EVALUATED"
            ),
            "notice": (
                "Distribution monitoring indicators (PSI/KS) quantify covariate shift "
                "and do not constitute proof of fraud or policy failure."
            ),
        }
