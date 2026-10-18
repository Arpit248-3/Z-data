"""
SignalGate Feature Matrix Safeguards and Builder
Constructs leakage-safe model feature matrices with:
- Strict exclusion of identifiers (TransactionID) and raw timestamps (TransactionDT).
- Separation of ground-truth target labels (isFraud, true_label).
- Segregation of segment columns (ProductCD, card4) into an evaluation-only structure.
- Safe numeric downcasting (float64 -> float32) without silent data corruption.
- Deterministic handling of infinite values (mapped to NaN per HGB native handling policy).
- Frozen, reproducible feature column ordering and manifest recording.
"""

from typing import Dict, List, Optional, Tuple, Any
import numpy as np
import pandas as pd

from data.schema import (
    TARGET_COLUMN,
    ID_COLUMN,
    TIME_COLUMN,
    FORBIDDEN_MODEL_COLUMNS,
    SEGMENT_COLUMNS,
    CATEGORICAL_COLUMNS,
)

# Canonical reasons for column exclusion
EXCLUSION_REASONS = {
    ID_COLUMN: "Identifier column: strictly forbidden from model features to prevent memorization leakage",
    TIME_COLUMN: "Temporal ordering column: raw timestamp strictly forbidden to prevent chronological leakage",
    TARGET_COLUMN: "Ground-truth target: strictly forbidden from model features",
    "true_label": "Evaluation label: strictly forbidden from model features",
    "split": "Partition metadata: forbidden from model features",
    "partition": "Partition metadata: forbidden from model features",
}


def build_evaluation_metadata(df: pd.DataFrame) -> pd.DataFrame:
    """
    Extract evaluation-only metadata structure (IDs, timestamps, segment attributes, labels).
    Kept separate from the model feature matrix throughout the pipeline.
    """
    eval_cols = []
    for col in [ID_COLUMN, TIME_COLUMN, TARGET_COLUMN] + SEGMENT_COLUMNS:
        if col in df.columns:
            eval_cols.append(col)

    eval_df = df[eval_cols].copy()
    return eval_df


def identify_numeric_features(df: pd.DataFrame, excluded_cols: List[str]) -> List[str]:
    """
    Identify safe numeric features in stable order, excluding all forbidden and segment columns.
    """
    numeric_features = []
    for col in df.columns:
        if col in excluded_cols:
            continue
        if pd.api.types.is_numeric_dtype(df[col]):
            numeric_features.append(col)
    return numeric_features


def sanitize_numeric_values(
    df_features: pd.DataFrame,
    downcast_float32: bool = True,
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Sanitize numeric features:
    1. Replace +/- infinite values with np.nan (documented policy for tree-based models).
    2. Safely downcast float64 to float32 to optimize memory footprint.
    """
    df_clean = df_features.copy()
    stats = {"inf_replaced_count": 0, "downcasted_cols": []}

    for col in df_clean.columns:
        # Check for infinite values in numeric columns
        if pd.api.types.is_float_dtype(df_clean[col]):
            inf_mask = np.isinf(df_clean[col].to_numpy())
            if inf_mask.any():
                n_infs = int(inf_mask.sum())
                stats["inf_replaced_count"] += n_infs
                df_clean.loc[inf_mask, col] = np.nan

            if downcast_float32 and df_clean[col].dtype == np.float64:
                df_clean[col] = df_clean[col].astype(np.float32)
                stats["downcasted_cols"].append(col)

        elif pd.api.types.is_integer_dtype(df_clean[col]):
            if downcast_float32 and df_clean[col].dtype == np.int64:
                # Downcast to int32 if within safe integer range
                c_min = df_clean[col].min()
                c_max = df_clean[col].max()
                if c_min >= np.iinfo(np.int32).min and c_max <= np.iinfo(np.int32).max:
                    df_clean[col] = df_clean[col].astype(np.int32)
                    stats["downcasted_cols"].append(col)

    return df_clean, stats


def extract_features_and_target(
    df: pd.DataFrame,
    feature_manifest: Optional[List[str]] = None,
    downcast_float32: bool = True,
    exclude_segments_from_model: bool = True,
) -> Tuple[pd.DataFrame, Optional[pd.Series], pd.DataFrame, Dict[str, Any]]:
    """
    Build safe model feature matrix X, separate target y, and evaluation metadata eval_df.

    Parameters:
    - df: Input transaction DataFrame.
    - feature_manifest: Optional frozen list of feature column names. If None, derived from df.
    - downcast_float32: Whether to downcast float64 to float32.
    - exclude_segments_from_model: Whether to isolate segment columns into eval_df (default True).

    Returns:
    - X: Clean feature DataFrame containing only safe features in frozen order.
    - y: Target Series (or None if TARGET_COLUMN not present).
    - eval_df: Separate evaluation DataFrame (TransactionID, TransactionDT, segments, target).
    - manifest_info: Dictionary detailing feature manifest and exclusion documentation.
    """
    if len(df) == 0:
        raise ValueError("Cannot extract features from an empty DataFrame (0 rows).")

    # 1. Separate evaluation metadata
    eval_df = build_evaluation_metadata(df)

    # 2. Separate target
    y = df[TARGET_COLUMN].copy() if TARGET_COLUMN in df.columns else None

    # 3. Build exclusion list
    excluded = set(FORBIDDEN_MODEL_COLUMNS)
    reasons = dict(EXCLUSION_REASONS)

    if exclude_segments_from_model:
        for seg_col in SEGMENT_COLUMNS:
            excluded.add(seg_col)
            reasons[seg_col] = "Segment column: segregated into eval_df for post-hoc reporting"

    # Also document categorical exclusions if starting from numeric baseline
    for col in df.columns:
        if col not in excluded and not pd.api.types.is_numeric_dtype(df[col]):
            excluded.add(col)
            reasons[col] = f"Categorical column '{col}': excluded from numeric baseline feature matrix"

    # 4. Determine feature columns
    if feature_manifest is not None:
        # Use frozen feature manifest
        feature_cols = list(feature_manifest)
        # Verify no forbidden column is in the manifest
        for col in feature_cols:
            if col in FORBIDDEN_MODEL_COLUMNS:
                raise ValueError(f"CRITICAL LEAKAGE: Forbidden column '{col}' is present in feature manifest!")
            if exclude_segments_from_model and col in SEGMENT_COLUMNS:
                raise ValueError(f"CRITICAL LEAKAGE: Segment column '{col}' is present in feature manifest!")
            if col not in df.columns:
                raise ValueError(f"Required feature '{col}' from manifest is missing in DataFrame!")
    else:
        # Discover safe numeric features in stable alphabetical / column order
        feature_cols = identify_numeric_features(df, list(excluded))

    # Extract feature matrix
    X_raw = df[feature_cols].copy()

    # Sanitize numeric values and downcast
    X, sanitize_stats = sanitize_numeric_values(X_raw, downcast_float32=downcast_float32)

    manifest_info = {
        "feature_count": len(feature_cols),
        "feature_names": feature_cols,
        "excluded_columns": {c: reasons.get(c, "Excluded by policy") for c in df.columns if c not in feature_cols},
        "nan_policy": "HistGradientBoosting natively handles missing values (NaN) during split evaluation",
        "inf_policy": "Infinite values (+/- inf) mapped to np.nan",
        "downcast_policy": "float64 safely downcasted to float32" if downcast_float32 else "none",
        "sanitize_stats": sanitize_stats,
    }

    return X, y, eval_df, manifest_info
