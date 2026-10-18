"""
SignalGate Data Loader
Loads either the genuine IEEE-CIS Fraud Detection dataset (if present and valid)
or the deterministic SYNTHETIC_SMOKE_ONLY development fixture.

Guarantees:
- Never silently substitutes synthetic data while claiming to use IEEE-CIS.
- Rejects malformed or corrupted real data with clear errors.
- Reports detailed dataset provenance, metadata, class balance, and checksums.
- Never presents synthetic results as benchmark results.
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
    validate_schema,
)
from data.generate_fixture import (
    generate_and_save_fixture,
    compute_file_sha256,
    FIXTURE_STATUS,
)

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def inspect_dataset_provenance(df: pd.DataFrame, source_path: str, is_synthetic: bool) -> Dict[str, Any]:
    """
    Generate comprehensive dataset provenance report without printing raw row data.
    """
    row_count = len(df)
    col_count = len(df.columns)

    fraud_count = int(df[TARGET_COLUMN].sum()) if TARGET_COLUMN in df.columns else 0
    fraud_prevalence = float(fraud_count / row_count) if row_count > 0 and TARGET_COLUMN in df.columns else 0.0

    target_counts = (
        {int(k): int(v) for k, v in df[TARGET_COLUMN].value_counts().to_dict().items()}
        if TARGET_COLUMN in df.columns
        else {}
    )

    # Missingness summary
    missing_counts = df.isna().sum()
    missingness = {
        col: {
            "missing_count": int(missing_counts[col]),
            "missing_pct": round(float(missing_counts[col] / row_count) * 100, 2),
        }
        for col in df.columns
        if missing_counts[col] > 0
    }

    # Timestamp range
    time_min = int(df[TIME_COLUMN].min()) if TIME_COLUMN in df.columns and len(df) > 0 else None
    time_max = int(df[TIME_COLUMN].max()) if TIME_COLUMN in df.columns and len(df) > 0 else None
    time_span = (time_max - time_min) if (time_min is not None and time_max is not None) else None

    file_hash = compute_file_sha256(source_path) if os.path.exists(source_path) else None

    status = FIXTURE_STATUS if is_synthetic else "READY"
    dataset_type = "SYNTHETIC_SMOKE_FIXTURE" if is_synthetic else "REAL_IEEE_CIS"

    return {
        "dataset_type": dataset_type,
        "status": status,
        "source_path": str(source_path),
        "sha256": file_hash,
        "rows": row_count,
        "columns": col_count,
        "column_names": list(df.columns),
        "target_column": TARGET_COLUMN,
        "target_counts": target_counts,
        "fraud_count": fraud_count,
        "fraud_prevalence": round(fraud_prevalence, 6),
        "timestamp_range": {
            "min": time_min,
            "max": time_max,
            "span_seconds": time_span,
        },
        "missingness": missingness,
        "is_synthetic": is_synthetic,
        "benchmark_claims_allowed": not is_synthetic,
        "notice": (
            "SYNTHETIC_SMOKE_ONLY: This dataset is a deterministic synthetic development fixture. "
            "Evaluations on this dataset must never be presented as real benchmark claims."
            if is_synthetic
            else "REAL_IEEE_CIS: Authorized for scientific evaluation and benchmark claims."
        ),
    }


def load_dataset(
    file_path: Optional[str] = None,
    enforce_schema: bool = True,
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Load dataset with strict provenance and integrity checks.

    Priority:
    1. If explicit `file_path` is passed, load and validate that specific path.
    2. Otherwise, check for genuine IEEE-CIS `data/train_transaction.csv`.
       - If genuine file exists, validate it. If it fails schema/integrity, RAISE an error.
         DO NOT silently fall back to synthetic data.
    3. If genuine file does not exist, load the deterministic synthetic smoke fixture.
    """
    target_path: Optional[Path] = None
    is_synthetic: bool = False

    if file_path is not None:
        target_path = Path(file_path).resolve()
        if not target_path.exists():
            raise FileNotFoundError(f"Requested dataset file does not exist: {target_path}")
        is_synthetic = "synthetic" in target_path.name.lower()
    else:
        # Check standard IEEE-CIS paths
        real_candidates = [
            PROJECT_ROOT / "data" / "train_transaction.csv",
            PROJECT_ROOT / "train_transaction.csv",
        ]
        for candidate in real_candidates:
            if candidate.exists() and candidate.is_file():
                target_path = candidate
                is_synthetic = False
                break

        # If no real dataset found, use synthetic fixture
        if target_path is None:
            synthetic_path = PROJECT_ROOT / "data" / "synthetic_smoke_fixture.csv"
            if not synthetic_path.exists():
                generate_and_save_fixture(n_rows=10000, seed=42, output_dir=str(PROJECT_ROOT / "data"))
            target_path = synthetic_path
            is_synthetic = True

    # Read data
    try:
        df = pd.read_csv(target_path)
    except Exception as e:
        raise ValueError(f"Failed to read CSV at {target_path}: {e}") from e

    # Schema & integrity validation
    if enforce_schema:
        is_valid, errors = validate_schema(df, is_synthetic=is_synthetic)
        if not is_valid:
            error_msg = f"Dataset at '{target_path}' failed schema validation:\n" + "\n".join(f"- {err}" for err in errors)
            # Critical integrity rule: NEVER silently fall back if a real dataset was corrupted/malformed
            raise ValueError(error_msg)

    # Basic input checks
    if len(df) == 0:
        raise ValueError(f"Dataset at '{target_path}' is empty (0 rows).")

    for req_col in [ID_COLUMN, TARGET_COLUMN, TIME_COLUMN]:
        if req_col not in df.columns:
            raise ValueError(f"Required column '{req_col}' is missing from {target_path}.")
        if df[req_col].isna().any():
            nan_count = int(df[req_col].isna().sum())
            raise ValueError(f"Required column '{req_col}' contains {nan_count} NaN/null values in {target_path}.")

    # Generate metadata
    metadata = inspect_dataset_provenance(df, str(target_path), is_synthetic=is_synthetic)

    return df, metadata
