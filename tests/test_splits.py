"""
SignalGate Phase 2 Tests — Chronological Splits
Covers:
1. Exact partition proportions (60/10/10/20) and rounding.
2. Strict chronological ordering across partitions.
3. Complete partition disjointness (zero ID or row overlap).
4. Correct handling of timestamp ties at boundaries.
5. Deterministic reproducibility of splits and split hashes.
6. Rejection of missing, NaN, or infinite chronological values.
7. Correct target-to-row alignment after sorting and splitting.
8. Propagation of SYNTHETIC_SMOKE_ONLY in split report.
"""

from pathlib import Path
import numpy as np
import pandas as pd
import pytest

from data.splits import (
    make_splits,
    compute_split_hash,
    generate_split_report,
    SPLIT_PROPORTIONS,
)
from data.schema import (
    TARGET_COLUMN,
    ID_COLUMN,
    TIME_COLUMN,
)
from data.load import load_dataset

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def test_partition_proportions_and_counts_on_synthetic_fixture():
    df, meta = load_dataset()
    splits = make_splits(df)

    total_rows = len(df)
    assert len(splits["train"]) == 6000
    assert len(splits["calib"]) == 1000
    assert len(splits["val"]) == 1000
    assert len(splits["test"]) == 2000
    assert sum(len(s) for s in splits.values()) == total_rows


def test_partition_proportions_on_small_custom_fixture():
    # 100 rows test fixture
    n_rows = 100
    custom_df = pd.DataFrame({
        ID_COLUMN: range(1, n_rows + 1),
        TIME_COLUMN: [i * 10 for i in range(1, n_rows + 1)],
        TARGET_COLUMN: [1 if i % 20 == 0 else 0 for i in range(1, n_rows + 1)],
    })

    splits = make_splits(custom_df)
    assert len(splits["train"]) == 60
    assert len(splits["calib"]) == 10
    assert len(splits["val"]) == 10
    assert len(splits["test"]) == 20


def test_chronological_ordering_and_disjointness():
    df, meta = load_dataset()
    splits = make_splits(df)

    # 1. Non-overlapping ID sets
    train_ids = set(splits["train"][ID_COLUMN])
    calib_ids = set(splits["calib"][ID_COLUMN])
    val_ids = set(splits["val"][ID_COLUMN])
    test_ids = set(splits["test"][ID_COLUMN])

    assert train_ids.isdisjoint(calib_ids)
    assert train_ids.isdisjoint(val_ids)
    assert train_ids.isdisjoint(test_ids)
    assert calib_ids.isdisjoint(val_ids)
    assert calib_ids.isdisjoint(test_ids)
    assert val_ids.isdisjoint(test_ids)

    # 2. Chronological non-decreasing boundaries
    assert splits["train"][TIME_COLUMN].max() <= splits["calib"][TIME_COLUMN].min()
    assert splits["calib"][TIME_COLUMN].max() <= splits["val"][TIME_COLUMN].min()
    assert splits["val"][TIME_COLUMN].max() <= splits["test"][TIME_COLUMN].min()


def test_duplicate_timestamps_at_boundaries_tie_handling():
    # Construct a dataset where rows at boundaries share identical timestamps
    # 100 rows: rows 58, 59, 60, 61, 62 all have timestamp = 600
    times = []
    for i in range(100):
        if 58 <= i <= 62:
            times.append(600)
        else:
            times.append(i * 10)

    tied_df = pd.DataFrame({
        ID_COLUMN: range(1000, 1100),
        TIME_COLUMN: times,
        TARGET_COLUMN: [0] * 100,
    })

    splits = make_splits(tied_df)

    # Verify counts remain exact: 60, 10, 10, 20
    assert len(splits["train"]) == 60
    assert len(splits["calib"]) == 10
    assert len(splits["val"]) == 10
    assert len(splits["test"]) == 20

    # Verify disjointness
    assert set(splits["train"][ID_COLUMN]).isdisjoint(set(splits["calib"][ID_COLUMN]))

    # Verify tie-breaking sorted by ID when time is equal
    tied_train = splits["train"][splits["train"][TIME_COLUMN] == 600]
    tied_calib = splits["calib"][splits["calib"][TIME_COLUMN] == 600]
    assert tied_train[ID_COLUMN].max() < tied_calib[ID_COLUMN].min()


def test_split_reproducibility_and_deterministic_hash():
    df, meta = load_dataset()
    splits_1 = make_splits(df)
    splits_2 = make_splits(df)

    hash_1 = compute_split_hash(splits_1)
    hash_2 = compute_split_hash(splits_2)

    assert hash_1 == hash_2
    for part in ["train", "calib", "val", "test"]:
        pd.testing.assert_frame_equal(splits_1[part], splits_2[part])


def test_rejection_of_invalid_or_missing_chronological_values():
    # Missing time column
    bad_df = pd.DataFrame({ID_COLUMN: [1, 2], TARGET_COLUMN: [0, 1]})
    with pytest.raises(ValueError, match="Time column 'TransactionDT' not found"):
        make_splits(bad_df)

    # NaN in time column
    nan_time_df = pd.DataFrame({
        ID_COLUMN: [1, 2, 3, 4],
        TIME_COLUMN: [100.0, np.nan, 300.0, 400.0],
        TARGET_COLUMN: [0, 1, 0, 0],
    })
    with pytest.raises(ValueError, match="contains 1 NaN/null values"):
        make_splits(nan_time_df)

    # Infinite value in time column
    inf_time_df = pd.DataFrame({
        ID_COLUMN: [1, 2, 3, 4],
        TIME_COLUMN: [100.0, np.inf, 300.0, 400.0],
        TARGET_COLUMN: [0, 1, 0, 0],
    })
    with pytest.raises(ValueError, match="contains infinite values"):
        make_splits(inf_time_df)


def test_target_to_row_alignment_preserved():
    # Create dataset with specific unique amounts associated with specific targets and IDs
    n = 50
    df = pd.DataFrame({
        ID_COLUMN: [100 + i for i in range(n)],
        TIME_COLUMN: [1000 - i for i in range(n)], # Reverse order to test sorting
        TARGET_COLUMN: [1 if i % 5 == 0 else 0 for i in range(n)],
        "TransactionAmt": [float(i * 10) for i in range(n)],
    })

    splits = make_splits(df)

    # Verify that for every row in every partition, TransactionAmt matches (ID - 100) * 10
    for name, part in splits.items():
        expected_amts = (part[ID_COLUMN] - 100) * 10.0
        assert np.allclose(part["TransactionAmt"], expected_amts)
        expected_targets = ((part[ID_COLUMN] - 100) % 5 == 0).astype(int)
        assert (part[TARGET_COLUMN] == expected_targets).all()


def test_split_report_generation_and_synthetic_status(tmp_path):
    df, meta = load_dataset()
    splits = make_splits(df)

    report_path = tmp_path / "test_split_report.json"
    report = generate_split_report(splits, meta, output_path=str(report_path))

    assert report["status"] == "SYNTHETIC_SMOKE_ONLY"
    assert report["is_synthetic"] is True
    assert report["total_rows"] == 10000
    assert report["partitions"]["train"]["rows"] == 6000
    assert report["partitions"]["test"]["rows"] == 2000
    assert report["split_hash"] is not None
    assert report_path.exists()
