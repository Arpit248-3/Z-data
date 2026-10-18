"""SignalGate IBM Architecture Integration — Feature Manifest and Quarantine Validator.

Governs the expected 391-feature specification (14 categorical, 377 numerical)
for the real IEEE-CIS Fraud Detection pipeline.
Enforces strict ground-truth quarantine (Master Spec § C2), rejecting target `isFraud`
and raw identifiers (`TransactionID`, `TransactionDT`) from model feature inputs.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Set
import pandas as pd
from pydantic import BaseModel, ConfigDict, Field

from integrations.ibm_architecture.exceptions import LeakageViolationError

MANIFEST_JSON_PATH = (
    Path(__file__).resolve().parent.parent.parent.parent
    / "results"
    / "ieee_cis_v1"
    / "feature_manifest.json"
)

# Quarantined columns that must NEVER enter feature matrices or scoring feature forms
QUARANTINED_COLUMNS: Set[str] = {
    "isFraud",
    "isfraud",
    "is_fraud",
    "target",
    "label",
    "true_label",
    "TransactionID",
    "transactionid",
    "transaction_id",
    "TransactionDT",
    "transactiondt",
    "transaction_dt",
}


class FeatureManifest(BaseModel):
    """Specification of the IEEE-CIS feature schema and quarantine boundaries."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    status: str = Field(
        default="SPECIFICATION_UNVALIDATED_AGAINST_RAW_DATA",
        description="Architecture specification status; marked unvalidated until raw data arrives",
    )
    specification_source: str = Field(
        default="reference/architecture/IBM-main/results/feature_manifest.json",
        description="Origin of the registered feature specification",
    )
    architecture_version: str = Field(default="ieee_cis_v1")
    target_column: str = Field(default="isFraud", description="Quarantined ground-truth label")
    excluded_columns: List[str] = Field(
        default_factory=lambda: ["TransactionDT", "TransactionID", "isFraud"],
        description="Columns strictly excluded from model feature matrices",
    )
    categorical_columns: List[str] = Field(
        default_factory=list,
        description="14 categorical feature columns",
    )
    numerical_columns: List[str] = Field(
        default_factory=list,
        description="377 numerical feature columns",
    )

    @property
    def feature_names(self) -> List[str]:
        """Return the exact ordered list of 391 feature names (numerical followed by categorical)."""
        return self.numerical_columns + self.categorical_columns

    @property
    def total_feature_count(self) -> int:
        """Total expected input feature dimension."""
        return len(self.feature_names)

    def validate_features(self, df: pd.DataFrame, context: str = "FeatureMatrix") -> None:
        """Validate that a DataFrame feature matrix contains ZERO quarantined columns.

        Raises LeakageViolationError if target labels or raw identifiers are detected.
        """
        detected_violations = [col for col in df.columns if col in QUARANTINED_COLUMNS or col.lower() in {q.lower() for q in QUARANTINED_COLUMNS}]
        if detected_violations:
            raise LeakageViolationError(
                f"Quarantine barrier breached in {context}: columns {detected_violations} "
                f"must never enter the feature matrix.",
                violated_fields=detected_violations,
                context=context,
            )

    def extract_features(
        self,
        df: pd.DataFrame,
        strict_columns: bool = True,
        context: str = "extract_features",
    ) -> pd.DataFrame:
        """Extract features conforming to the manifest in exact canonical column order.

        Enforces quarantine check before extraction.
        """
        self.validate_features(df, context=context)

        expected = self.feature_names
        if strict_columns:
            missing = [c for c in expected if c not in df.columns]
            if missing:
                raise ValueError(
                    f"Feature matrix is missing {len(missing)} required columns according to manifest. "
                    f"First missing: {missing[:5]}"
                )
            return df[expected].copy()
        else:
            present = [c for c in expected if c in df.columns]
            return df[present].copy()

    @classmethod
    def load(cls, manifest_path: Optional[Path] = None) -> "FeatureManifest":
        """Load manifest specification from JSON."""
        target_path = manifest_path or MANIFEST_JSON_PATH
        if not target_path.exists():
            raise FileNotFoundError(f"Feature manifest not found at: {target_path}")

        with open(target_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        return cls(
            status=data.get("status", "SPECIFICATION_UNVALIDATED_AGAINST_RAW_DATA"),
            specification_source=data.get("specification_source", ""),
            architecture_version=data.get("architecture_version", "ieee_cis_v1"),
            target_column=data.get("target_column", "isFraud"),
            excluded_columns=data.get("excluded_columns", ["TransactionDT", "TransactionID", "isFraud"]),
            categorical_columns=data.get("categorical_columns", []),
            numerical_columns=data.get("numerical_columns", []),
        )


# Global canonical instance
CANONICAL_FEATURE_MANIFEST: FeatureManifest = FeatureManifest.load()
