"""SignalGate IBM Architecture Integration — Memory-Conscious IEEE-CIS Data Loader.

Implements reproducible loading for the real IEEE-CIS Fraud Detection dataset:
- Memory-conscious reading on Windows AMD64 (8 GB RAM budget).
- Strict feature leakage quarantine (Master Spec § C2): target `isFraud` strictly
  separated; identifiers `TransactionID` and `TransactionDT` quarantined from feature matrices.
- Fails closed with ArtifactNotFoundError when raw CSV files are missing.
- Zero silent fallback to synthetic fixtures.
"""

from __future__ import annotations

import gc
import os
from pathlib import Path
from typing import Any, Dict, Iterator, Optional, Tuple, Union
import numpy as np
import pandas as pd

from integrations.ibm_architecture.exceptions import ArtifactNotFoundError, LeakageViolationError
from integrations.ibm_architecture.data.manifest import CANONICAL_FEATURE_MANIFEST, QUARANTINED_COLUMNS

DEFAULT_RAW_DIR = Path(__file__).resolve().parent.parent.parent.parent / "data" / "raw"


def get_memory_efficient_dtypes() -> Dict[str, str]:
    """Define downcasted data types to prevent out-of-memory errors on 8 GB host."""
    dtypes: Dict[str, str] = {
        "TransactionID": "int32",
        "TransactionDT": "int32",
        "isFraud": "int8",
        "ProductCD": "category",
        "card4": "category",
        "card6": "category",
        "P_emaildomain": "category",
        "R_emaildomain": "category",
        "DeviceType": "category",
    }
    # V-columns downcast to float32
    for i in range(1, 340):
        dtypes[f"V{i}"] = "float32"
    # C-columns downcast to float32
    for i in range(1, 15):
        dtypes[f"C{i}"] = "float32"
    # D-columns downcast to float32
    for i in range(1, 16):
        dtypes[f"D{i}"] = "float32"
    return dtypes


def load_ieee_cis(
    data_dir: Optional[Union[str, Path]] = None,
    nrows: Optional[int] = None,
    include_target: bool = False,
    include_metadata_cols: bool = False,
) -> Tuple[pd.DataFrame, Optional[pd.Series]]:
    """Load and join IEEE-CIS dataset with strict ground-truth quarantine.

    Parameters
    ----------
    data_dir : Path or str, optional
        Path to data/raw/ containing train_transaction.csv and train_identity.csv.
    nrows : int, optional
        Optional row limit for bounded memory loading / testing.
    include_target : bool, default False
        If True, returns target series `isFraud` as a separate, quarantined object.
        If False, target is completely excluded.
    include_metadata_cols : bool, default False
        If True, includes `TransactionID` and `TransactionDT` solely for sorting/splits.
        Never pass these into model training feature vectors.

    Returns
    -------
    Tuple[pd.DataFrame, Optional[pd.Series]]
        (feature_dataframe, target_series_or_None)

    Raises
    ------
    ArtifactNotFoundError
        If raw CSV files do not exist in the specified directory.
    LeakageViolationError
        If quarantined columns appear in the feature output.
    """
    raw_path = Path(data_dir) if data_dir else DEFAULT_RAW_DIR
    tx_file = raw_path / "train_transaction.csv"
    id_file = raw_path / "train_identity.csv"

    # 1. Fail-closed check: verify file existence without fabricating data
    missing_files = []
    if not tx_file.exists():
        missing_files.append(str(tx_file))
    if not id_file.exists():
        missing_files.append(str(id_file))

    if missing_files:
        raise ArtifactNotFoundError(
            artifact_path=", ".join(missing_files),
            expected_purpose=(
                "IEEE-CIS Fraud Detection raw dataset. Real-data benchmark mode cannot proceed. "
                "Download train_transaction.csv and train_identity.csv into data/raw/ to enable this mode. "
                "In compliance with Master Spec § C1, synthetic data will not be substituted."
            ),
        )

    # 2. Memory-conscious loading
    dtypes = get_memory_efficient_dtypes()

    # Load transactions
    df_tx = pd.read_csv(tx_file, nrows=nrows, dtype=dtypes, low_memory=True)
    initial_tx_count = len(df_tx)

    # Extract target if requested
    target_series: Optional[pd.Series] = None
    if "isFraud" in df_tx.columns:
        if include_target:
            target_series = df_tx["isFraud"].copy()
        df_tx = df_tx.drop(columns=["isFraud"])

    # Load identity table
    df_id = pd.read_csv(id_file, nrows=nrows, low_memory=True)

    # 3. Join identity data: left join on TransactionID with 1:1 merge cardinality check
    df_merged = pd.merge(df_tx, df_id, on="TransactionID", how="left")
    del df_tx, df_id
    gc.collect()

    # Verify merge cardinality: transaction count must be preserved exactly
    if len(df_merged) != initial_tx_count:
        raise ValueError(
            f"Merge cardinality mismatch: started with {initial_tx_count} transactions, "
            f"ended with {len(df_merged)} rows after identity join."
        )

    # 4. Enforce ground-truth quarantine on feature DataFrame
    if not include_metadata_cols:
        cols_to_drop = [c for c in ["TransactionID", "TransactionDT"] if c in df_merged.columns]
        if cols_to_drop:
            df_merged = df_merged.drop(columns=cols_to_drop)

    # Final quarantine check
    if not include_metadata_cols:
        CANONICAL_FEATURE_MANIFEST.validate_features(df_merged, context="load_ieee_cis")

    return df_merged, target_series


def process_mock_ieee_cis_fixture(
    mock_df: pd.DataFrame,
    include_target: bool = False,
    include_metadata_cols: bool = False,
) -> Tuple[pd.DataFrame, Optional[pd.Series]]:
    """Process an explicitly labeled mock fixture for unit testing data ingestion logic.

    Guarantees that test fixtures exercise exact transformation and quarantine paths
    without claiming real-data arrival.
    """
    working_df = mock_df.copy()
    target_series: Optional[pd.Series] = None

    if "isFraud" in working_df.columns:
        if include_target:
            target_series = working_df["isFraud"].copy()
        working_df = working_df.drop(columns=["isFraud"])

    if not include_metadata_cols:
        cols_to_drop = [c for c in ["TransactionID", "TransactionDT"] if c in working_df.columns]
        if cols_to_drop:
            working_df = working_df.drop(columns=cols_to_drop)
        CANONICAL_FEATURE_MANIFEST.validate_features(working_df, context="process_mock_ieee_cis_fixture")

    return working_df, target_series
