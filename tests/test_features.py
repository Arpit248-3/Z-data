"""
SignalGate Phase 2 Tests — Feature Matrix Builder & Leakage Safeguards
Covers:
1. Strict exclusion of TransactionID, raw TransactionDT, isFraud, true_label from X.
2. Segregation of segment columns (ProductCD, card4) to eval_df.
3. Separation of target vector y from feature matrix X.
4. Consistent feature ordering across train/calib/val/test splits.
5. Safe handling of NaN and infinite (+/- inf) values without silent corruption.
6. Safe numeric downcasting (float64 -> float32).
7. Loader failure when an invalid real dataset is present (no silent fallback).
8. Loader validation of required schema columns.
"""

from pathlib import Path
import numpy as np
import pandas as pd
import pytest

from data.schema import (
    TARGET_COLUMN,
    ID_COLUMN,
    TIME_COLUMN,
    FORBIDDEN_MODEL_COLUMNS,
    SEGMENT_COLUMNS,
)
from data.load import load_dataset
from data.splits import make_splits
from data.features import (
    extract_features_and_target,
    sanitize_numeric_values,
)

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def test_forbidden_columns_excluded_from_feature_matrix():
    df, meta = load_dataset()
    X, y, eval_df, manifest = extract_features_and_target(df)

    # 1. Check all forbidden columns
    for forbidden in FORBIDDEN_MODEL_COLUMNS:
        assert forbidden not in X.columns, f"Forbidden column '{forbidden}' leaked into feature matrix!"

    # 2. Check segment columns are excluded from X by default
    for seg in SEGMENT_COLUMNS:
        assert seg not in X.columns, f"Segment column '{seg}' leaked into feature matrix!"
        assert seg in eval_df.columns, f"Segment column '{seg}' missing from eval_df!"

    # 3. Target is separated
    assert y is not None
    assert len(y) == len(X)
    assert TARGET_COLUMN not in X.columns


def test_consistent_feature_ordering_across_partitions():
    df, meta = load_dataset()
    splits = make_splits(df)

    # Extract features on train first to obtain frozen manifest
    X_train, y_train, eval_train, train_manifest = extract_features_and_target(splits["train"])
    frozen_feature_names = train_manifest["feature_names"]

    # Apply frozen manifest to all other partitions
    for part_name in ["calib", "val", "test"]:
        part_df = splits[part_name]
        X_part, y_part, eval_part, part_manifest = extract_features_and_target(
            part_df,
            feature_manifest=frozen_feature_names,
        )

        assert list(X_part.columns) == frozen_feature_names, (
            f"Feature ordering mismatch in partition '{part_name}'!"
        )
        assert len(X_part) == len(part_df)
        assert len(y_part) == len(part_df)
        assert len(eval_part) == len(part_df)


def test_infinite_values_mapped_to_nan_policy():
    df_sample = pd.DataFrame({
        "feature_a": [1.0, np.inf, 3.0, -np.inf],
        "feature_b": [10.0, 20.0, 30.0, 40.0],
    })

    df_clean, stats = sanitize_numeric_values(df_sample, downcast_float32=True)

    assert stats["inf_replaced_count"] == 2
    assert np.isnan(df_clean.loc[1, "feature_a"])
    assert np.isnan(df_clean.loc[3, "feature_a"])
    assert df_clean.loc[0, "feature_a"] == 1.0
    assert not np.isinf(df_clean.to_numpy()).any()


def test_float64_safe_downcasting_to_float32():
    df_sample = pd.DataFrame({
        "col_float": np.array([1.5, 2.75, 3.125], dtype=np.float64),
        "col_int": np.array([100, 200, 300], dtype=np.int64),
    })

    df_clean, stats = sanitize_numeric_values(df_sample, downcast_float32=True)

    assert df_clean["col_float"].dtype == np.float32
    assert df_clean["col_int"].dtype == np.int32
    assert np.allclose(df_clean["col_float"], [1.5, 2.75, 3.125])


def test_feature_manifest_rejects_forbidden_columns():
    df, meta = load_dataset()
    corrupted_manifest = ["TransactionAmt", "card1", "TransactionID"] # Leaking ID

    with pytest.raises(ValueError, match="CRITICAL LEAKAGE: Forbidden column 'TransactionID'"):
        extract_features_and_target(df, feature_manifest=corrupted_manifest)


def test_loader_rejects_missing_required_columns(tmp_path):
    # CSV missing isFraud target column
    corrupt_csv = tmp_path / "corrupted_transaction.csv"
    pd.DataFrame({
        ID_COLUMN: [1, 2, 3],
        TIME_COLUMN: [100, 200, 300],
        "TransactionAmt": [10.0, 20.0, 30.0],
    }).to_csv(corrupt_csv, index=False)

    with pytest.raises(ValueError, match="Missing required core column: 'isFraud'"):
        load_dataset(file_path=str(corrupt_csv), enforce_schema=True)


def test_loader_fails_on_invalid_real_dataset_without_silent_synthetic_fallback(tmp_path, monkeypatch):
    # Create an invalid "real" dataset in the project data directory
    fake_real_path = PROJECT_ROOT / "data" / "train_transaction.csv"

    # Write a malformed real file (non-monotonic timestamps and missing target)
    malformed_df = pd.DataFrame({
        ID_COLUMN: [1, 2],
        TIME_COLUMN: [200, 100], # Violated monotonicity
        # Missing isFraud
    })
    malformed_df.to_csv(fake_real_path, index=False)

    try:
        # load_dataset should fail explicitly and NOT silently fall back to synthetic
        with pytest.raises(ValueError, match="failed schema validation"):
            load_dataset()
    finally:
        # Clean up temporary test file so we do not leave invalid files behind
        if fake_real_path.exists():
            fake_real_path.unlink()
