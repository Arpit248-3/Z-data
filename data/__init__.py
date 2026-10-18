"""
SignalGate Data Package
Provides dataset schemas, loaders, chronological splitters, and feature matrix builders.
"""

from .schema import (
    TARGET_COLUMN,
    ID_COLUMN,
    TIME_COLUMN,
    FORBIDDEN_MODEL_COLUMNS,
    CATEGORICAL_COLUMNS,
    SEGMENT_COLUMNS,
    validate_schema,
    get_feature_columns,
)
from .load import (
    load_dataset,
    inspect_dataset_provenance,
)
from .splits import (
    make_splits,
    generate_split_report,
    compute_split_hash,
)
from .features import (
    extract_features_and_target,
    build_evaluation_metadata,
    sanitize_numeric_values,
)

__all__ = [
    "TARGET_COLUMN",
    "ID_COLUMN",
    "TIME_COLUMN",
    "FORBIDDEN_MODEL_COLUMNS",
    "CATEGORICAL_COLUMNS",
    "SEGMENT_COLUMNS",
    "validate_schema",
    "get_feature_columns",
    "load_dataset",
    "inspect_dataset_provenance",
    "make_splits",
    "generate_split_report",
    "compute_split_hash",
    "extract_features_and_target",
    "build_evaluation_metadata",
    "sanitize_numeric_values",
]
