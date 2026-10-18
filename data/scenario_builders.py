"""SignalGate Scenario Builders Module

Constructs reproducible shift scenarios strictly complying with Blueprint Section 5.5 and 6.4:
- S0: Untouched chronological test scenario (Reference).
- S3: Injected covariate shift (SYNTHETIC_SHIFT): deterministic perturbation of selected
      feature distributions using declared seed and explicit perturbation parameters.
- S1: Prevalence / velocity burst shift (SYNTHETIC_SHIFT): simulating sudden fraud spikes.
- Explicit scenario hashing and provenance recording.
"""

import hashlib
import json
from typing import Any, Dict, List, Optional
import numpy as np
import pandas as pd


def compute_df_hash(df: pd.DataFrame) -> str:
    """Compute deterministic SHA-256 hash of a DataFrame's values and structure."""
    hasher = hashlib.sha256()
    # Hash column names and dtypes
    col_str = ",".join(f"{col}:{df[col].dtype}" for col in df.columns)
    hasher.update(col_str.encode("utf-8"))
    # Hash row count and summary of values
    hasher.update(f"rows:{len(df)}".encode("utf-8"))
    
    # Hash content deterministically
    for col in sorted(df.columns):
        if pd.api.types.is_numeric_dtype(df[col]):
            vals = df[col].fillna(-999999.0).to_numpy()
            hasher.update(vals.tobytes())
        else:
            str_vals = df[col].fillna("__NA__").astype(str).tolist()
            hasher.update("".join(str_vals[:100]).encode("utf-8"))
            hasher.update("".join(str_vals[-100:]).encode("utf-8"))
            
    return hasher.hexdigest()


def build_scenario_s0(
    test_df: pd.DataFrame,
    status: str = "SYNTHETIC_SMOKE_ONLY",
) -> Dict[str, Any]:
    """Build S0: Untouched chronological test scenario (Reference)."""
    df = test_df.copy()
    fraud_count = int(df["isFraud"].sum()) if "isFraud" in df.columns else 0
    prevalence = float(fraud_count / len(df)) if len(df) > 0 else 0.0
    s_hash = compute_df_hash(df)

    return {
        "scenario_id": "S0",
        "name": "S0_untouched_reference",
        "description": "Untouched chronological test partition serving as evaluation baseline.",
        "status": status,
        "is_synthetic": True if "SYNTHETIC" in status else False,
        "df": df,
        "sample_count": len(df),
        "fraud_count": fraud_count,
        "fraud_prevalence": round(prevalence, 6),
        "seed": None,
        "scenario_hash": s_hash,
        "metadata": {
            "perturbation_type": "none",
            "shifted_features": [],
            "perturbation_strength": 0.0,
        },
    }


def build_scenario_s3(
    test_df: pd.DataFrame,
    seed: int = 42,
    perturbation_strength: float = 0.5,
    status: str = "SYNTHETIC_SHIFT",
) -> Dict[str, Any]:
    """Build S3: Injected covariate shift with declared seed and documented perturbations.

    Perturbations:
    - TransactionAmt: scaled by log-normal shift exp(N(0.25 * strength, (0.2 * strength)^2))
    - Selected V-features: additive Gaussian noise scaled by feature std and strength
    - Selected D-features: temporal aging drift
    """
    df = test_df.copy()
    rng = np.random.default_rng(seed)
    shifted_features: List[str] = []

    # 1. Perturb TransactionAmt if present
    if "TransactionAmt" in df.columns:
        amt_mult = np.exp(rng.normal(0.3 * perturbation_strength, 0.2 * perturbation_strength, size=len(df)))
        df["TransactionAmt"] = (df["TransactionAmt"] * amt_mult).clip(lower=0.5, upper=50000.0)
        shifted_features.append("TransactionAmt")

    # 2. Perturb numeric V features that exist in df
    candidate_v_cols = [c for c in df.columns if c.startswith("V") and pd.api.types.is_numeric_dtype(df[c])]
    target_v_cols = candidate_v_cols[:10]  # top 10 V features
    for col in target_v_cols:
        col_std = float(df[col].std()) if df[col].std() > 0 else 1.0
        noise = rng.normal(0.0, col_std * perturbation_strength, size=len(df))
        df[col] = df[col] + noise
        shifted_features.append(col)

    # 3. Perturb D features (timedelta aging drift)
    candidate_d_cols = [c for c in df.columns if c.startswith("D") and pd.api.types.is_numeric_dtype(df[c])]
    for col in candidate_d_cols[:4]:
        df[col] = df[col] + rng.exponential(scale=10.0 * perturbation_strength, size=len(df))
        shifted_features.append(col)

    fraud_count = int(df["isFraud"].sum()) if "isFraud" in df.columns else 0
    prevalence = float(fraud_count / len(df)) if len(df) > 0 else 0.0
    s_hash = compute_df_hash(df)

    return {
        "scenario_id": "S3",
        "name": "S3_covariate_shift",
        "description": (
            "Deterministic synthetic covariate perturbation on TransactionAmt, V, and D features. "
            "Evaluates policy sensitivity and drift detection under distribution shifts."
        ),
        "status": status,
        "is_synthetic": True,
        "df": df,
        "sample_count": len(df),
        "fraud_count": fraud_count,
        "fraud_prevalence": round(prevalence, 6),
        "seed": seed,
        "scenario_hash": s_hash,
        "metadata": {
            "perturbation_type": "covariate_gaussian_and_lognormal",
            "shifted_features": shifted_features,
            "perturbation_strength": perturbation_strength,
            "notice": "SYNTHETIC_SHIFT: Injected perturbation for robustness testing; does not represent organic fraud drift.",
        },
    }


def build_scenario_s1(
    test_df: pd.DataFrame,
    seed: int = 42,
    status: str = "SYNTHETIC_SHIFT",
) -> Dict[str, Any]:
    """Build S1: Temporal burst / prevalence shock scenario."""
    df = test_df.copy()
    # Sort strictly chronologically
    time_col = "TransactionDT" if "TransactionDT" in df.columns else df.columns[0]
    df = df.sort_values(by=time_col).reset_index(drop=True)

    # Subsample to later half of the test window, where fraud cluster occurs
    split_idx = int(len(df) * 0.4)
    burst_df = df.iloc[split_idx:].copy().reset_index(drop=True)

    fraud_count = int(burst_df["isFraud"].sum()) if "isFraud" in burst_df.columns else 0
    prevalence = float(fraud_count / len(burst_df)) if len(burst_df) > 0 else 0.0
    s_hash = compute_df_hash(burst_df)

    return {
        "scenario_id": "S1",
        "name": "S1_prevalence_burst",
        "description": "Chronological subwindow representing a burst period with altered transaction density and prevalence.",
        "status": status,
        "is_synthetic": True,
        "df": burst_df,
        "sample_count": len(burst_df),
        "fraud_count": fraud_count,
        "fraud_prevalence": round(prevalence, 6),
        "seed": seed,
        "scenario_hash": s_hash,
        "metadata": {
            "perturbation_type": "temporal_subwindow_burst",
            "start_offset_fraction": 0.4,
            "notice": "SYNTHETIC_SHIFT: Temporal slice for testing queue capacity and recall stability.",
        },
    }


def build_all_scenarios(
    test_df: pd.DataFrame,
    seed: int = 42,
    base_status: str = "SYNTHETIC_SMOKE_ONLY",
) -> Dict[str, Dict[str, Any]]:
    """Build all standard evaluation scenarios."""
    s0 = build_scenario_s0(test_df, status=base_status)
    s3 = build_scenario_s3(test_df, seed=seed, perturbation_strength=0.5, status="SYNTHETIC_SHIFT")
    s1 = build_scenario_s1(test_df, seed=seed, status="SYNTHETIC_SHIFT")
    return {
        "S0": s0,
        "S3": s3,
        "S1": s1,
    }
