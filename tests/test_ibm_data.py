"""Unit and boundary tests for SignalGate IEEE-CIS Data Ingestion (Phase 3).

Validates:
1. 391-feature manifest specification (14 categorical, 377 numerical).
2. Strict ground-truth quarantine: rejection of isFraud, TransactionID, and TransactionDT from feature matrices.
3. Chronological 60/10/10/20 partitioning, strict temporal monotonicity, and tie-breaking.
4. Complete partition disjointness with zero ID overlap.
5. Deterministic SHA-256 partition hashing.
6. Fail-closed data loader error handling when raw CSVs are missing in data/raw/.
7. Memory-conscious dtype definitions and merge cardinality verification.
"""

from pathlib import Path
import numpy as np
import pandas as pd
import pytest

from integrations.ibm_architecture.exceptions import (
    ArtifactNotFoundError,
    LeakageViolationError,
)
from integrations.ibm_architecture.data import (
    CANONICAL_FEATURE_MANIFEST,
    FeatureManifest,
    ChronologicalSplitter,
    compute_partition_hash,
    load_ieee_cis,
    process_mock_ieee_cis_fixture,
    validate_dataset_directory,
    get_memory_efficient_dtypes,
)


# =============================================================================
# 1. Feature Manifest & Quarantine Tests
# =============================================================================
def test_canonical_manifest_feature_counts():
    """Verify exact 391-feature specification: 14 categorical and 377 numerical."""
    manifest = CANONICAL_FEATURE_MANIFEST
    assert manifest.total_feature_count == 391
    assert len(manifest.categorical_columns) == 14
    assert len(manifest.numerical_columns) == 377
    assert manifest.target_column == "isFraud"
    assert "isFraud" in manifest.excluded_columns
    assert "TransactionID" in manifest.excluded_columns
    assert "TransactionDT" in manifest.excluded_columns


def test_manifest_validate_features_rejects_isfraud():
    """Manifest validator must raise LeakageViolationError if isFraud is present."""
    bad_df = pd.DataFrame({
        "ProductCD": ["W", "C"],
        "TransactionAmt": [50.0, 100.0],
        "isFraud": [0, 1],
    })
    with pytest.raises(LeakageViolationError) as exc_info:
        CANONICAL_FEATURE_MANIFEST.validate_features(bad_df)
    assert "isFraud" in exc_info.value.violated_fields


def test_manifest_validate_features_rejects_transaction_identifiers():
    """Manifest validator must raise LeakageViolationError if TransactionID or TransactionDT is present."""
    bad_df_id = pd.DataFrame({
        "ProductCD": ["W"],
        "TransactionID": [1000],
    })
    with pytest.raises(LeakageViolationError) as exc_info:
        CANONICAL_FEATURE_MANIFEST.validate_features(bad_df_id)
    assert "TransactionID" in exc_info.value.violated_fields

    bad_df_dt = pd.DataFrame({
        "ProductCD": ["W"],
        "TransactionDT": [86400],
    })
    with pytest.raises(LeakageViolationError) as exc_info:
        CANONICAL_FEATURE_MANIFEST.validate_features(bad_df_dt)
    assert "TransactionDT" in exc_info.value.violated_fields


def test_manifest_extract_features_enforces_exact_order():
    """extract_features must order columns according to the canonical 391-feature manifest."""
    # Build minimal mock dataframe with first 3 categorical and first 2 numerical
    cols = ["TransactionAmt", "card1", "ProductCD", "card4", "card6"]
    df = pd.DataFrame({
        "card1": [100.0],
        "ProductCD": ["W"],
        "TransactionAmt": [50.0],
        "card6": ["debit"],
        "card4": ["visa"],
    })

    manifest = FeatureManifest(
        categorical_columns=["ProductCD", "card4", "card6"],
        numerical_columns=["TransactionAmt", "card1"],
    )

    extracted = manifest.extract_features(df, strict_columns=True)
    expected_order = ["TransactionAmt", "card1", "ProductCD", "card4", "card6"]
    assert list(extracted.columns) == expected_order


# =============================================================================
# 2. Chronological Splitting & Partition Tests
# =============================================================================
def test_chronological_splitter_proportions_and_bounds():
    """Verify exact 60/10/10/20 proportions and monotonic chronological boundaries."""
    n_rows = 1000
    mock_df = pd.DataFrame({
        "TransactionID": range(2000, 2000 + n_rows),
        "TransactionDT": [i * 60 for i in range(n_rows)],
        "TransactionAmt": [float(i % 100) for i in range(n_rows)],
        "isFraud": [1 if i % 25 == 0 else 0 for i in range(n_rows)],
    })

    splitter = ChronologicalSplitter()
    splits = splitter.split(mock_df)

    assert len(splits["train"]) == 600
    assert len(splits["calibration"]) == 100
    assert len(splits["validation"]) == 100
    assert len(splits["test"]) == 200

    # Strict chronological monotonicity: max(prev) <= min(next)
    assert splits["train"]["TransactionDT"].max() <= splits["calibration"]["TransactionDT"].min()
    assert splits["calibration"]["TransactionDT"].max() <= splits["validation"]["TransactionDT"].min()
    assert splits["validation"]["TransactionDT"].max() <= splits["test"]["TransactionDT"].min()


def test_chronological_splitter_deterministic_tie_breaking():
    """Verify deterministic secondary tie-breaking on TransactionID when TransactionDT is identical."""
    # 4 transactions at exact same timestamp
    mock_df = pd.DataFrame({
        "TransactionID": [1004, 1001, 1003, 1002],
        "TransactionDT": [500, 500, 500, 500],
    })

    splitter = ChronologicalSplitter({
        "train": (0.0, 0.50),
        "calibration": (0.50, 0.75),
        "validation": (0.75, 1.00),
        "test": (1.00, 1.00),
    })

    splits = splitter.split(mock_df, sort=True)
    # Train should have admitted 1001 and 1002 first due to ascending TransactionID tie-breaking
    assert list(splits["train"]["TransactionID"]) == [1001, 1002]
    assert list(splits["calibration"]["TransactionID"]) == [1003]
    assert list(splits["validation"]["TransactionID"]) == [1004]


def test_chronological_splitter_disjointness():
    """Verify zero ID overlap across all generated partitions."""
    n_rows = 500
    mock_df = pd.DataFrame({
        "TransactionID": range(5000, 5000 + n_rows),
        "TransactionDT": range(1000, 1000 + n_rows),
    })

    splitter = ChronologicalSplitter()
    splits = splitter.split(mock_df)

    train_ids = set(splits["train"]["TransactionID"])
    calib_ids = set(splits["calibration"]["TransactionID"])
    val_ids = set(splits["validation"]["TransactionID"])
    test_ids = set(splits["test"]["TransactionID"])

    assert train_ids.isdisjoint(calib_ids)
    assert train_ids.isdisjoint(val_ids)
    assert train_ids.isdisjoint(test_ids)
    assert calib_ids.isdisjoint(val_ids)
    assert calib_ids.isdisjoint(test_ids)
    assert val_ids.isdisjoint(test_ids)


def test_compute_partition_hash_determinism():
    """Verify SHA-256 partition fingerprinting is deterministic and sensitive to order."""
    ids_a = [101, 102, 103, 104]
    ids_b = [101, 102, 103, 104]
    ids_c = [104, 103, 102, 101]

    hash_a = compute_partition_hash(ids_a)
    hash_b = compute_partition_hash(ids_b)
    hash_c = compute_partition_hash(ids_c)

    assert len(hash_a) == 64
    assert hash_a == hash_b
    assert hash_a != hash_c


# =============================================================================
# 3. Fail-Closed Data Loading & Validation Tests
# =============================================================================
def test_load_ieee_cis_fails_closed_when_raw_csv_missing(tmp_path):
    """load_ieee_cis must raise ArtifactNotFoundError when raw CSVs are absent."""
    empty_dir = tmp_path / "empty_raw"
    empty_dir.mkdir()

    with pytest.raises(ArtifactNotFoundError) as exc_info:
        load_ieee_cis(data_dir=empty_dir)

    err = exc_info.value
    assert "train_transaction.csv" in err.artifact_path
    assert "Master Spec § C1" in err.expected_purpose


def test_validate_dataset_directory_reports_missing_files(tmp_path):
    """validate_dataset_directory must return structured UNAVAILABLE report when files are missing."""
    empty_dir = tmp_path / "raw"
    empty_dir.mkdir()
    out_dir = tmp_path / "results"

    report = validate_dataset_directory(data_dir=empty_dir, output_dir=out_dir)
    assert report["status"] == "UNAVAILABLE_MISSING_RAW_FILES"
    assert report["ready_for_ingestion"] is False
    assert len(report["missing_files"]) == 4
    assert "train_transaction.csv" in report["missing_files"]

    report_file = out_dir / "dataset_validation_report.json"
    assert report_file.exists()


def test_process_mock_ieee_cis_fixture_quarantine():
    """process_mock_ieee_cis_fixture must separate target and exclude identifiers."""
    mock_df = pd.DataFrame({
        "TransactionID": [101, 102],
        "TransactionDT": [86400, 86450],
        "isFraud": [0, 1],
        "ProductCD": ["W", "C"],
        "TransactionAmt": [25.0, 75.0],
    })

    # 1. include_target=False: target is dropped, features are sanitized
    feat_df, target = process_mock_ieee_cis_fixture(mock_df, include_target=False, include_metadata_cols=False)
    assert target is None
    assert "isFraud" not in feat_df.columns
    assert "TransactionID" not in feat_df.columns
    assert "TransactionDT" not in feat_df.columns
    assert set(feat_df.columns) == {"ProductCD", "TransactionAmt"}

    # 2. include_target=True: target is returned separately as Series
    feat_df2, target2 = process_mock_ieee_cis_fixture(mock_df, include_target=True, include_metadata_cols=False)
    assert target2 is not None
    assert list(target2) == [0, 1]
    assert "isFraud" not in feat_df2.columns


def test_memory_efficient_dtypes_configuration():
    """Verify memory downcasting dtypes dict contains V, C, D, and categorical mappings."""
    dtypes = get_memory_efficient_dtypes()
    assert dtypes["TransactionID"] == "int32"
    assert dtypes["TransactionDT"] == "int32"
    assert dtypes["isFraud"] == "int8"
    assert dtypes["ProductCD"] == "category"
    assert dtypes["V1"] == "float32"
    assert dtypes["V339"] == "float32"
    assert dtypes["C1"] == "float32"
    assert dtypes["D1"] == "float32"
