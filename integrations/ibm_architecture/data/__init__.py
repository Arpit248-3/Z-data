"""SignalGate IBM Architecture Integration — Data Ingestion & Partitioning Package.

Provides reproducible data loading, 391-feature manifest validation,
chronological 60/10/10/20 partitioning, and fail-closed dataset validation.

Governing Specification: docs/ibm_architecture_integration_master_spec.md § C, § G
"""

from integrations.ibm_architecture.data.manifest import (
    FeatureManifest,
    CANONICAL_FEATURE_MANIFEST,
    QUARANTINED_COLUMNS,
)
from integrations.ibm_architecture.data.splitter import (
    ChronologicalSplitter,
    PartitionMetadata,
    compute_partition_hash,
    DEFAULT_SPLIT_RATIOS,
)
from integrations.ibm_architecture.data.loader import (
    load_ieee_cis,
    process_mock_ieee_cis_fixture,
    get_memory_efficient_dtypes,
)
from integrations.ibm_architecture.data.validator import (
    validate_dataset_directory,
    compute_file_sha256,
)

__all__ = [
    # Manifest
    "FeatureManifest",
    "CANONICAL_FEATURE_MANIFEST",
    "QUARANTINED_COLUMNS",
    # Splitter
    "ChronologicalSplitter",
    "PartitionMetadata",
    "compute_partition_hash",
    "DEFAULT_SPLIT_RATIOS",
    # Loader
    "load_ieee_cis",
    "process_mock_ieee_cis_fixture",
    "get_memory_efficient_dtypes",
    # Validator
    "validate_dataset_directory",
    "compute_file_sha256",
]
