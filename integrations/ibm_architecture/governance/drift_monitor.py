"""SignalGate IBM Architecture Integration — Drift Monitoring Engine.

Implements multi-metric distribution drift calculation:
- Population Stability Index (PSI) using reference quantile binning and epsilon smoothing.
- Two-sample Kolmogorov-Smirnov (KS) test via scipy.stats.ks_2samp.
- Wasserstein Distance (Earth Mover's Distance) via scipy.stats.wasserstein_distance.
- Missingness rate deltas.
- Clear separation between feature drift, prediction-score drift, calibration degradation,
  and epistemic model disagreement.
- Strict ground-truth quarantine: isFraud, target, label, TransactionID, and TransactionDT
  are strictly rejected from feature monitoring.
- Non-negotiable discipline notice: drift indicators quantify covariate shift and epistemic
  uncertainty; they do NOT constitute proof of fraud and never automatically trigger fraud actions.

Governing Specification: docs/ibm_architecture_integration_master_spec.md § C, § K
"""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from typing import Any, Dict, List, Literal, Optional, Sequence, Union
import uuid

import numpy as np
import pandas as pd
from pydantic import BaseModel, ConfigDict, Field
from scipy.stats import ks_2samp, wasserstein_distance

from integrations.ibm_architecture.exceptions import LeakageViolationError

# Quarantined fields that must never be monitored as features
QUARANTINED_FIELDS = {
    "isFraud",
    "isfraud",
    "target",
    "label",
    "true_label",
    "TransactionID",
    "transactionid",
    "TransactionDT",
    "transactiondt",
}

DRIFT_DISCIPLINE_NOTICE = (
    "Distribution monitoring indicators (PSI/KS/Wasserstein) quantify covariate shift "
    "and epistemic uncertainty; they do not constitute proof of fraud or policy failure."
)


class FeatureDriftResult(BaseModel):
    """Calculated drift indicators for a single feature or score distribution."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    feature: str = Field(min_length=1, description="Feature or score column name")
    psi: Optional[float] = Field(default=None, description="Population Stability Index")
    ks_statistic: Optional[float] = Field(default=None, description="Kolmogorov-Smirnov two-sample statistic")
    ks_pvalue: Optional[float] = Field(default=None, description="Kolmogorov-Smirnov two-sample p-value")
    wasserstein_distance: Optional[float] = Field(default=None, description="1D Wasserstein Earth Mover's distance")
    drift_category: Literal["stable", "moderate_drift", "significant_drift", "unknown"] = Field(
        default="unknown", description="Categorical stability status based on PSI"
    )
    ref_sample_count: int = Field(ge=0, description="Valid reference sample count")
    act_sample_count: int = Field(ge=0, description="Valid comparison sample count")
    ref_missing_rate: float = Field(ge=0.0, le=1.0, description="Reference missing rate [0, 1]")
    act_missing_rate: float = Field(ge=0.0, le=1.0, description="Comparison missing rate [0, 1]")
    missing_rate_delta: float = Field(description="Missing rate change: act_missing_rate - ref_missing_rate")


class DriftReport(BaseModel):
    """Immutable, evidence-backed drift report capturing dataset and score divergence."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    report_id: str = Field(min_length=1, description="Unique drift report identifier")
    reference_window_id: str = Field(min_length=1, description="Reference baseline window/split ID")
    comparison_window_id: str = Field(min_length=1, description="Comparison evaluated window/split ID")
    features_monitored: int = Field(ge=0, description="Number of monitored feature columns")
    significant_drift_features: int = Field(ge=0, description="Count of features with PSI > 0.20")
    moderate_drift_features: int = Field(ge=0, description="Count of features with 0.10 <= PSI <= 0.20")
    mean_psi: float = Field(ge=0.0, description="Arithmetic mean PSI across monitored features")
    max_psi: float = Field(ge=0.0, description="Maximum PSI observed across monitored features")
    score_drift: Optional[FeatureDriftResult] = Field(
        default=None, description="Drift metrics on calibrated posterior probability p"
    )
    feature_reports: List[FeatureDriftResult] = Field(
        default_factory=list, description="Detailed feature-level drift metrics"
    )
    provenance_hash: str = Field(min_length=64, max_length=64, description="SHA-256 canonical hash of report")
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Timezone-aware UTC evaluation timestamp",
    )
    status: str = Field(default="IEEE_CIS_OFFLINE_BENCHMARK", description="Evidence mode or scenario tag")
    notice: str = Field(default=DRIFT_DISCIPLINE_NOTICE, description="Mandatory drift discipline statement")


class DriftMonitor:
    """Deterministic, evidence-backed distribution drift monitor."""

    def __init__(self, epsilon: float = 1e-4, bins: int = 10) -> None:
        self.epsilon = epsilon
        self.bins = bins

    def calculate_psi(
        self,
        reference: Union[Sequence[float], np.ndarray, pd.Series],
        actual: Union[Sequence[float], np.ndarray, pd.Series],
        bins: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Compute Population Stability Index (PSI) using reference quantile binning."""
        n_bins = bins or self.bins
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

        # Quantile bin edges on reference
        quantiles = np.linspace(0.0, 1.0, n_bins + 1)
        bin_edges = np.unique(np.quantile(ref_clean, quantiles))

        if len(bin_edges) < 2:
            val = bin_edges[0] if len(bin_edges) == 1 else 0.0
            bin_edges = np.array([val - 1.0, val, val + 1.0])

        bin_edges[0] = -np.inf
        bin_edges[-1] = np.inf

        ref_counts, _ = np.histogram(ref_clean, bins=bin_edges)
        act_counts, _ = np.histogram(act_clean, bins=bin_edges)

        ref_props = ref_counts / len(ref_clean)
        act_props = act_counts / len(act_clean)

        # Epsilon smoothing
        ref_props = np.where(ref_props == 0, self.epsilon, ref_props)
        act_props = np.where(act_props == 0, self.epsilon, act_props)
        ref_props = ref_props / np.sum(ref_props)
        act_props = act_props / np.sum(act_props)

        psi_terms = (act_props - ref_props) * np.log(act_props / ref_props)
        psi_val = float(np.sum(psi_terms))
        psi_val = max(0.0, psi_val)

        if psi_val < 0.10:
            category = "stable"
        elif psi_val <= 0.20:
            category = "moderate_drift"
        else:
            category = "significant_drift"

        return {
            "psi": round(psi_val, 6),
            "category": category,
            "ref_valid_count": len(ref_clean),
            "act_valid_count": len(act_clean),
        }

    def calculate_ks(
        self,
        reference: Union[Sequence[float], np.ndarray, pd.Series],
        actual: Union[Sequence[float], np.ndarray, pd.Series],
    ) -> Tuple[Optional[float], Optional[float]]:
        """Compute two-sample Kolmogorov-Smirnov test."""
        ref = np.asarray(reference, dtype=float)
        act = np.asarray(actual, dtype=float)

        ref_clean = ref[np.isfinite(ref)]
        act_clean = act[np.isfinite(act)]

        if len(ref_clean) == 0 or len(act_clean) == 0:
            return None, None

        stat, pval = ks_2samp(ref_clean, act_clean)
        return round(float(stat), 6), round(float(pval), 6)

    def calculate_wasserstein(
        self,
        reference: Union[Sequence[float], np.ndarray, pd.Series],
        actual: Union[Sequence[float], np.ndarray, pd.Series],
    ) -> Optional[float]:
        """Compute 1D Wasserstein Earth Mover's Distance."""
        ref = np.asarray(reference, dtype=float)
        act = np.asarray(actual, dtype=float)

        ref_clean = ref[np.isfinite(ref)]
        act_clean = act[np.isfinite(act)]

        if len(ref_clean) == 0 or len(act_clean) == 0:
            return None

        dist = wasserstein_distance(ref_clean, act_clean)
        return round(float(dist), 6)

    def compute_feature_drift(
        self,
        reference: Union[Sequence[float], np.ndarray, pd.Series],
        actual: Union[Sequence[float], np.ndarray, pd.Series],
        feature_name: str,
        bins: Optional[int] = None,
    ) -> FeatureDriftResult:
        """Compute combined PSI, KS, Wasserstein, and missingness metrics for a feature."""
        # Quarantine check
        if feature_name in QUARANTINED_FIELDS:
            raise LeakageViolationError(
                f"Quarantine violation: '{feature_name}' cannot be evaluated in drift monitoring.",
                violated_fields=[feature_name],
                context="DriftMonitor.compute_feature_drift",
            )

        ref = np.asarray(reference, dtype=float)
        act = np.asarray(actual, dtype=float)

        ref_missing = float(np.mean(~np.isfinite(ref))) if len(ref) > 0 else 0.0
        act_missing = float(np.mean(~np.isfinite(act))) if len(act) > 0 else 0.0
        missing_delta = act_missing - ref_missing

        psi_res = self.calculate_psi(ref, act, bins=bins)
        ks_stat, ks_pval = self.calculate_ks(ref, act)
        w_dist = self.calculate_wasserstein(ref, act)

        return FeatureDriftResult(
            feature=feature_name,
            psi=psi_res.get("psi"),
            ks_statistic=ks_stat,
            ks_pvalue=ks_pval,
            wasserstein_distance=w_dist,
            drift_category=psi_res.get("category", "unknown"),
            ref_sample_count=psi_res.get("ref_valid_count", 0),
            act_sample_count=psi_res.get("act_valid_count", 0),
            ref_missing_rate=round(ref_missing, 4),
            act_missing_rate=round(act_missing, 4),
            missing_rate_delta=round(missing_delta, 4),
        )

    def compute_score_drift(
        self,
        reference_scores: Union[Sequence[float], np.ndarray, pd.Series],
        actual_scores: Union[Sequence[float], np.ndarray, pd.Series],
    ) -> FeatureDriftResult:
        """Compute distribution drift specifically over model prediction scores (calibrated posterior p)."""
        ref = np.asarray(reference_scores, dtype=float)
        act = np.asarray(actual_scores, dtype=float)

        ref_missing = float(np.mean(~np.isfinite(ref))) if len(ref) > 0 else 0.0
        act_missing = float(np.mean(~np.isfinite(act))) if len(act) > 0 else 0.0

        psi_res = self.calculate_psi(ref, act)
        ks_stat, ks_pval = self.calculate_ks(ref, act)
        w_dist = self.calculate_wasserstein(ref, act)

        return FeatureDriftResult(
            feature="calibrated_posterior_p",
            psi=psi_res.get("psi"),
            ks_statistic=ks_stat,
            ks_pvalue=ks_pval,
            wasserstein_distance=w_dist,
            drift_category=psi_res.get("category", "unknown"),
            ref_sample_count=psi_res.get("ref_valid_count", 0),
            act_sample_count=psi_res.get("act_valid_count", 0),
            ref_missing_rate=round(ref_missing, 4),
            act_missing_rate=round(act_missing, 4),
            missing_rate_delta=round(act_missing - ref_missing, 4),
        )

    def compute_drift_report(
        self,
        reference_df: pd.DataFrame,
        comparison_df: pd.DataFrame,
        features: Optional[List[str]] = None,
        reference_window_id: str = "reference_baseline",
        comparison_window_id: str = "comparison_window",
        status: str = "IEEE_CIS_OFFLINE_BENCHMARK",
        reference_scores: Optional[Union[Sequence[float], np.ndarray, pd.Series]] = None,
        actual_scores: Optional[Union[Sequence[float], np.ndarray, pd.Series]] = None,
    ) -> DriftReport:
        """Run comprehensive drift monitoring over feature sets and prediction scores."""
        # 1. Quarantine check on input columns
        requested_features = features or [c for c in reference_df.columns if c in comparison_df.columns]
        leaked_cols = [c for c in requested_features if c in QUARANTINED_FIELDS]
        if leaked_cols:
            raise LeakageViolationError(
                f"Quarantine violation: Attempted to compute drift on quarantined fields: {leaked_cols}",
                violated_fields=leaked_cols,
                context="DriftMonitor.compute_drift_report",
            )

        # Filter features to common numeric columns
        clean_features = [c for c in requested_features if c not in QUARANTINED_FIELDS]
        feature_results: List[FeatureDriftResult] = []
        valid_psis: List[float] = []
        significant_count = 0
        moderate_count = 0

        for feat in clean_features:
            if feat in reference_df.columns and feat in comparison_df.columns:
                res = self.compute_feature_drift(
                    reference_df[feat],
                    comparison_df[feat],
                    feature_name=feat,
                )
                feature_results.append(res)
                if res.psi is not None:
                    valid_psis.append(res.psi)
                    if res.drift_category == "significant_drift":
                        significant_count += 1
                    elif res.drift_category == "moderate_drift":
                        moderate_count += 1

        mean_psi = round(float(np.mean(valid_psis)), 6) if valid_psis else 0.0
        max_psi = round(float(np.max(valid_psis)), 6) if valid_psis else 0.0

        # Optional prediction score drift
        score_drift_res: Optional[FeatureDriftResult] = None
        if reference_scores is not None and actual_scores is not None:
            score_drift_res = self.compute_score_drift(reference_scores, actual_scores)

        # Provenance hash calculation
        report_id = f"drift_{uuid.uuid4().hex[:12]}"
        timestamp = datetime.now(timezone.utc)
        provenance_payload = {
            "report_id": report_id,
            "ref_id": reference_window_id,
            "comp_id": comparison_window_id,
            "features_monitored": len(feature_results),
            "mean_psi": mean_psi,
            "max_psi": max_psi,
            "significant_drift_features": significant_count,
            "score_psi": score_drift_res.psi if score_drift_res else None,
            "status": status,
        }
        canonical_str = json.dumps(provenance_payload, sort_keys=True, separators=(",", ":"))
        provenance_hash = hashlib.sha256(canonical_str.encode("utf-8")).hexdigest()

        return DriftReport(
            report_id=report_id,
            reference_window_id=reference_window_id,
            comparison_window_id=comparison_window_id,
            features_monitored=len(feature_results),
            significant_drift_features=significant_count,
            moderate_drift_features=moderate_count,
            mean_psi=mean_psi,
            max_psi=max_psi,
            score_drift=score_drift_res,
            feature_reports=feature_results,
            provenance_hash=provenance_hash,
            timestamp=timestamp,
            status=status,
            notice=DRIFT_DISCIPLINE_NOTICE,
        )
