"""
SignalGate Chronological Splitting Module
Implements time-ordered, leakage-safe chronological partitioning:
- Train:       0% - 60% (earliest)
- Calibration: 60% - 70%
- Validation:  70% - 80%
- Test:        80% - 100% (latest)

Rules:
- Strictly chronological ordering; no random shuffling.
- Reject missing, non-finite, or invalid chronological values.
- Deterministic boundary and tie-breaking policy.
- Zero row or identifier overlap across partitions.
- Output results/split_report.json with full provenance and split hash.
"""

import hashlib
import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import numpy as np
import pandas as pd

from data.schema import (
    TARGET_COLUMN,
    ID_COLUMN,
    TIME_COLUMN,
)

PROJECT_ROOT = Path(__file__).resolve().parent.parent

SPLIT_PROPORTIONS = {
    "train": 0.60,
    "calib": 0.10,
    "val": 0.10,
    "test": 0.20,
}

TIE_POLICY_DESCRIPTION = (
    "Primary ordering is chronological (time_col ascending). In case of identical timestamps, "
    "deterministic tie-breaking is enforced by secondary sorting on id_col ascending (or original stable "
    "row index). Partition cut-points are calculated by exact row fractions (60/10/10/20). "
    "Every row is deterministically allocated to exactly one partition with zero overlap."
)


def compute_split_hash(splits: Dict[str, pd.DataFrame], id_col: str = ID_COLUMN) -> str:
    """
    Compute a deterministic SHA-256 fingerprint representing the exact split partitioning.
    """
    hasher = hashlib.sha256()
    for name in ["train", "calib", "val", "test"]:
        part_df = splits[name]
        hasher.update(name.encode("utf-8"))
        hasher.update(str(len(part_df)).encode("utf-8"))
        if id_col in part_df.columns:
            # Hash IDs in order
            ids_str = ",".join(part_df[id_col].astype(str).tolist())
            hasher.update(ids_str.encode("utf-8"))
        elif TIME_COLUMN in part_df.columns:
            ts_str = ",".join(part_df[TIME_COLUMN].astype(str).tolist())
            hasher.update(ts_str.encode("utf-8"))
    return hasher.hexdigest()


def make_splits(
    df: pd.DataFrame,
    time_col: str = TIME_COLUMN,
    id_col: str = ID_COLUMN,
) -> Dict[str, pd.DataFrame]:
    """
    Create chronological 60/10/10/20 train/calibration/validation/test splits.

    Parameters:
    - df: Source transaction DataFrame.
    - time_col: Column name representing transaction timestamp.
    - id_col: Column name representing unique transaction identifier.

    Returns:
    - Dict mapping partition name ('train', 'calib', 'val', 'test') to partitioned DataFrame.
    """
    if len(df) == 0:
        raise ValueError("Cannot split an empty DataFrame (0 rows).")

    if time_col not in df.columns:
        raise ValueError(f"Time column '{time_col}' not found in DataFrame columns: {list(df.columns)}")

    # Reject non-finite, null, or missing chronological values
    time_series = df[time_col]
    if time_series.isna().any():
        nan_count = int(time_series.isna().sum())
        raise ValueError(f"Chronological column '{time_col}' contains {nan_count} NaN/null values.")

    if not pd.api.types.is_numeric_dtype(time_series):
        raise ValueError(f"Chronological column '{time_col}' must be numeric, got dtype {time_series.dtype}.")

    if np.isinf(time_series.to_numpy(dtype=float)).any():
        raise ValueError(f"Chronological column '{time_col}' contains infinite values.")

    # Sort deterministically: primary by time_col, secondary by id_col (if present)
    sort_cols = [time_col]
    if id_col in df.columns:
        # Check ID validity
        if df[id_col].isna().any():
            raise ValueError(f"Identifier column '{id_col}' contains NaN values.")
        if df[id_col].duplicated().any():
            raise ValueError(f"Identifier column '{id_col}' contains duplicate values.")
        sort_cols.append(id_col)

    # Deterministic stable sort
    sorted_df = df.sort_values(by=sort_cols, ascending=True, kind="mergesort").copy().reset_index(drop=True)

    n_total = len(sorted_df)

    # Calculate row cut-points: 60%, 10%, 10%, 20%
    n_train = int(round(n_total * SPLIT_PROPORTIONS["train"]))
    n_calib = int(round(n_total * SPLIT_PROPORTIONS["calib"]))
    n_val = int(round(n_total * SPLIT_PROPORTIONS["val"]))
    # Ensure exact sum equals n_total
    n_test = n_total - (n_train + n_calib + n_val)

    if n_train == 0 or n_calib == 0 or n_val == 0 or n_test == 0:
        raise ValueError(
            f"Dataset too small ({n_total} rows) to create 60/10/10/20 splits: "
            f"train={n_train}, calib={n_calib}, val={n_val}, test={n_test}"
        )

    idx_train_end = n_train
    idx_calib_end = idx_train_end + n_calib
    idx_val_end = idx_calib_end + n_val

    splits = {
        "train": sorted_df.iloc[:idx_train_end].copy().reset_index(drop=True),
        "calib": sorted_df.iloc[idx_train_end:idx_calib_end].copy().reset_index(drop=True),
        "val": sorted_df.iloc[idx_calib_end:idx_val_end].copy().reset_index(drop=True),
        "test": sorted_df.iloc[idx_val_end:].copy().reset_index(drop=True),
    }

    # Chronology validation: later partitions must not start earlier than earlier partitions
    prev_max_time = None
    for name in ["train", "calib", "val", "test"]:
        part = splits[name]
        part_min_time = part[time_col].min()
        part_max_time = part[time_col].max()

        if prev_max_time is not None:
            if part_min_time < prev_max_time:
                raise ValueError(
                    f"Chronological violation in partition '{name}': min time {part_min_time} "
                    f"is strictly earlier than previous partition max time {prev_max_time}."
                )
        prev_max_time = part_max_time

    # Disjointness validation (no row ID overlap)
    if id_col in sorted_df.columns:
        seen_ids = set()
        for name, part in splits.items():
            part_ids = set(part[id_col])
            overlap = seen_ids.intersection(part_ids)
            if overlap:
                raise ValueError(f"Partition '{name}' shares {len(overlap)} IDs with earlier partitions!")
            seen_ids.update(part_ids)

    return splits


def generate_split_report(
    splits: Dict[str, pd.DataFrame],
    dataset_metadata: Dict[str, Any],
    output_path: Optional[str] = "results/split_report.json",
    time_col: str = TIME_COLUMN,
    id_col: str = ID_COLUMN,
) -> Dict[str, Any]:
    """
    Generate split report summarizing partition counts, fraud prevalence,
    chronological boundaries, dataset provenance, and split hash.
    """
    total_rows = sum(len(part) for part in splits.values())
    split_hash = compute_split_hash(splits, id_col=id_col)

    is_synthetic = dataset_metadata.get("is_synthetic", False)
    status = "SYNTHETIC_SMOKE_ONLY" if is_synthetic else "READY"

    partitions_summary = {}
    for name in ["train", "calib", "val", "test"]:
        part = splits[name]
        n_rows = len(part)
        fraud_count = int(part[TARGET_COLUMN].sum()) if TARGET_COLUMN in part.columns else None
        fraud_prev = round(float(fraud_count / n_rows), 6) if fraud_count is not None and n_rows > 0 else None

        min_time = int(part[time_col].min()) if time_col in part.columns and n_rows > 0 else None
        max_time = int(part[time_col].max()) if time_col in part.columns and n_rows > 0 else None

        partitions_summary[name] = {
            "rows": n_rows,
            "pct_of_total": round((n_rows / total_rows) * 100, 2) if total_rows > 0 else 0.0,
            "fraud_count": fraud_count,
            "fraud_prevalence": fraud_prev,
            "time_range": {
                "min": min_time,
                "max": max_time,
                "span_seconds": (max_time - min_time) if (min_time is not None and max_time is not None) else None,
            },
        }

    report = {
        "status": status,
        "is_synthetic": is_synthetic,
        "dataset_source": dataset_metadata.get("source_path", "unknown"),
        "dataset_sha256": dataset_metadata.get("sha256", "unknown"),
        "split_hash": split_hash,
        "total_rows": total_rows,
        "time_column": time_col,
        "id_column": id_col,
        "split_policy": {
            "proportions": SPLIT_PROPORTIONS,
            "tie_policy": TIE_POLICY_DESCRIPTION,
        },
        "partitions": partitions_summary,
        "notice": (
            "SYNTHETIC_SMOKE_ONLY: Partition metrics reflect synthetic fixture development data. "
            "Never cite these numbers as real benchmark performance."
            if is_synthetic
            else "REAL_IEEE_CIS: Chronological partition boundaries established on genuine dataset."
        ),
    }

    if output_path is not None:
        out_file = Path(output_path)
        if not out_file.is_absolute():
            out_file = PROJECT_ROOT / out_file
        os.makedirs(out_file.parent, exist_ok=True)
        with open(out_file, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)

    return report
