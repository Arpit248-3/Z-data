"""
SignalGate Dataset Schema Definition
Defines columns, data types, forbidden leakage features, and schema validation.
Compatible with IEEE-CIS Fraud Detection transaction schema.
"""

from typing import Dict, List, Tuple
import pandas as pd
import numpy as np

# Core target, ID, and ordering column names
TARGET_COLUMN = "isFraud"
ID_COLUMN = "TransactionID"
TIME_COLUMN = "TransactionDT"

# Forbidden columns that must NEVER enter model matrices
FORBIDDEN_MODEL_COLUMNS = [
    ID_COLUMN,
    TIME_COLUMN,
    TARGET_COLUMN,
    "true_label",
    "split",
    "partition",
]

# Primary categorical features
CATEGORICAL_COLUMNS = [
    "ProductCD",
    "card4",
    "card6",
    "P_emaildomain",
    "R_emaildomain",
    "M1",
    "M2",
    "M3",
    "M4",
    "M5",
    "M6",
    "M7",
    "M8",
    "M9",
]

# Segment evaluation columns (used for segment-level escalation checks, not leakage)
SEGMENT_COLUMNS = ["ProductCD", "card4"]

# Numeric feature definitions
NUMERIC_CARD_ADDR = [
    "TransactionAmt",
    "card1",
    "card2",
    "card3",
    "card5",
    "addr1",
    "addr2",
    "dist1",
]

C_COLUMNS = [f"C{i}" for i in range(1, 15)]
D_COLUMNS = [f"D{i}" for i in range(1, 16)]
V_SMOKE_COLUMNS = [f"V{i}" for i in range(1, 31)]

ALL_SMOKE_COLUMNS = (
    [ID_COLUMN, TARGET_COLUMN, TIME_COLUMN]
    + NUMERIC_CARD_ADDR
    + CATEGORICAL_COLUMNS
    + C_COLUMNS
    + D_COLUMNS
    + V_SMOKE_COLUMNS
)


def validate_schema(df: pd.DataFrame, is_synthetic: bool = False) -> Tuple[bool, List[str]]:
    """
    Validate that a DataFrame conforms to the expected SignalGate transaction schema.
    Returns (is_valid, error_messages).
    """
    errors = []

    # Check required core columns
    for col in [ID_COLUMN, TARGET_COLUMN, TIME_COLUMN]:
        if col not in df.columns:
            errors.append(f"Missing required core column: '{col}'")

    if errors:
        return False, errors

    # Check row count
    if len(df) == 0:
        errors.append("DataFrame is empty (0 rows)")

    # Check ID uniqueness
    if df[ID_COLUMN].duplicated().any():
        dup_count = int(df[ID_COLUMN].duplicated().sum())
        errors.append(f"TransactionID must be unique; found {dup_count} duplicate values")

    # Check target binary validity
    valid_targets = set(df[TARGET_COLUMN].dropna().unique())
    if not valid_targets.issubset({0, 1}):
        errors.append(f"isFraud values must be in {{0, 1}}; observed: {valid_targets}")

    # Check chronological ordering (or non-decreasing ordering)
    if not df[TIME_COLUMN].is_monotonic_increasing:
        errors.append("TransactionDT is not monotonically non-decreasing (chronological ordering violation)")

    # Check numeric types
    if not pd.api.types.is_numeric_dtype(df["TransactionAmt"]):
        errors.append("TransactionAmt must be numeric")

    return len(errors) == 0, errors


def get_feature_columns(df: pd.DataFrame) -> List[str]:
    """
    Returns the list of safe feature columns for model scoring,
    guaranteeing that all forbidden columns (ID, time, target, labels) are excluded.
    """
    return [col for col in df.columns if col not in FORBIDDEN_MODEL_COLUMNS]
