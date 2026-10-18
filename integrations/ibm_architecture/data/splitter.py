"""SignalGate IBM Architecture Integration — Chronological Temporal Splitter.

Implements strict chronological partitioning for IEEE-CIS transactions:
- 60% Train, 10% Calibration, 10% Validation, 20% Test (60/10/10/20).
- Monotonic sorting on TransactionDT ascending.
- Secondary deterministic tie-breaking on TransactionID ascending.
- Complete partition disjointness with zero ID overlap.
- Cryptographic SHA-256 partition fingerprinting.

Governing Specification: docs/ibm_architecture_integration_master_spec.md § C, § G
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional, Tuple, Union
import numpy as np
import pandas as pd
from pydantic import BaseModel, ConfigDict, Field

PartitionName = Literal["train", "calibration", "validation", "test"]

DEFAULT_SPLIT_RATIOS: Dict[PartitionName, Tuple[float, float]] = {
    "train": (0.0, 0.60),
    "calibration": (0.60, 0.70),
    "validation": (0.70, 0.80),
    "test": (0.80, 1.00),
}


class PartitionMetadata(BaseModel):
    """Audit metadata for one chronological partition."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    name: str = Field(description="Partition name (train, calibration, validation, test)")
    start_idx: int = Field(ge=0, description="Start row index (inclusive)")
    end_idx: int = Field(ge=0, description="End row index (exclusive)")
    row_count: int = Field(ge=0, description="Total rows in partition")
    dt_min: int = Field(description="Minimum TransactionDT timestamp in partition")
    dt_max: int = Field(description="Maximum TransactionDT timestamp in partition")
    fraud_count: Optional[int] = Field(default=None, description="Positive fraud count if target present")
    non_fraud_count: Optional[int] = Field(default=None, description="Non-fraud count if target present")
    prevalence: Optional[float] = Field(default=None, description="Fraud prevalence rate")
    split_hash: str = Field(description="SHA-256 fingerprint over partition TransactionIDs")


def compute_partition_hash(ids: Union[pd.Series, np.ndarray, List[int]]) -> str:
    """Compute a deterministic SHA-256 fingerprint for a sequence of TransactionIDs.

    IDs are formatted as comma-separated ASCII integer representations.
    """
    id_bytes = ",".join(str(int(x)) for x in ids).encode("ascii")
    return hashlib.sha256(id_bytes).hexdigest()


class ChronologicalSplitter:
    """Partitions transactions chronologically by TransactionDT with zero lookahead."""

    def __init__(
        self,
        ratios: Optional[Dict[PartitionName, Tuple[float, float]]] = None,
    ) -> None:
        self.ratios = ratios or DEFAULT_SPLIT_RATIOS

    def split(
        self,
        df: pd.DataFrame,
        sort: bool = True,
    ) -> Dict[PartitionName, pd.DataFrame]:
        """Split DataFrame into 4 chronological partitions (60/10/10/20).

        Requires TransactionDT and TransactionID for ordering and tie-breaking.
        """
        if "TransactionDT" not in df.columns:
            raise ValueError("DataFrame must contain 'TransactionDT' for chronological sorting")
        if "TransactionID" not in df.columns:
            raise ValueError("DataFrame must contain 'TransactionID' for tie-breaking and tracking")

        if sort:
            # Primary sort on TransactionDT ascending; secondary tie-breaking on TransactionID ascending
            working_df = df.sort_values(
                by=["TransactionDT", "TransactionID"],
                ascending=[True, True],
                kind="mergesort",
            ).reset_index(drop=True)
        else:
            working_df = df.copy().reset_index(drop=True)

        n = len(working_df)
        partitions: Dict[PartitionName, pd.DataFrame] = {}

        for name, (start_ratio, end_ratio) in self.ratios.items():
            start_idx = int(round(n * start_ratio))
            end_idx = int(round(n * end_ratio))
            partition_df = working_df.iloc[start_idx:end_idx].copy().reset_index(drop=True)
            partitions[name] = partition_df

        # Verify disjointness: ensure no ID overlap
        seen_ids: set[int] = set()
        for p_name, p_df in partitions.items():
            current_ids = set(p_df["TransactionID"].astype(int))
            overlap = seen_ids.intersection(current_ids)
            if overlap:
                raise ValueError(
                    f"Partition disjointness violation: {len(overlap)} IDs duplicated across partitions. "
                    f"First overlap: {list(overlap)[:5]}"
                )
            seen_ids.update(current_ids)

        return partitions

    def get_metadata(
        self,
        partitions: Dict[PartitionName, pd.DataFrame],
    ) -> Dict[str, PartitionMetadata]:
        """Calculate audit metadata and cryptographic split hashes for each partition."""
        meta: Dict[str, PartitionMetadata] = {}
        for name, p_df in partitions.items():
            row_count = len(p_df)
            dt_min = int(p_df["TransactionDT"].min()) if row_count > 0 else 0
            dt_max = int(p_df["TransactionDT"].max()) if row_count > 0 else 0

            fraud_count: Optional[int] = None
            non_fraud_count: Optional[int] = None
            prevalence: Optional[float] = None

            if "isFraud" in p_df.columns:
                fraud_count = int((p_df["isFraud"] == 1).sum())
                non_fraud_count = int((p_df["isFraud"] == 0).sum())
                prevalence = float(fraud_count / row_count) if row_count > 0 else 0.0

            split_hash = compute_partition_hash(p_df["TransactionID"])

            # Compute indices
            start_idx = int(round(sum(len(partitions[p]) for p in self.ratios if self.ratios[p][1] <= self.ratios[name][0])))
            end_idx = start_idx + row_count

            meta[name] = PartitionMetadata(
                name=name,
                start_idx=start_idx,
                end_idx=end_idx,
                row_count=row_count,
                dt_min=dt_min,
                dt_max=dt_max,
                fraud_count=fraud_count,
                non_fraud_count=non_fraud_count,
                prevalence=prevalence,
                split_hash=split_hash,
            )

        return meta

    def generate_split_manifest(
        self,
        partitions: Dict[PartitionName, pd.DataFrame],
        status: str = "SPECIFICATION_MOCK_VERIFIED",
    ) -> Dict[str, Any]:
        """Generate structured partition manifest dictionary."""
        meta = self.get_metadata(partitions)
        total_rows = sum(len(p) for p in partitions.values())
        return {
            "status": status,
            "architecture_version": "ieee_cis_v1",
            "total_rows": total_rows,
            "split_policy": {
                "train_fraction": 0.60,
                "calibration_fraction": 0.10,
                "validation_fraction": 0.10,
                "test_fraction": 0.20,
                "sorting": "TransactionDT ascending, secondary tie-breaking on TransactionID ascending",
            },
            "partitions": {name: m.model_dump() for name, m in meta.items()},
        }
