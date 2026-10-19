"""SignalGate IBM Architecture Integration — Feature Preprocessing Pipeline.

Implements feature transformation for the 391-feature IEEE-CIS fraud detection schema:
- 14 categorical features: OrdinalEncoder (handles unknown and missing values with -1)
- 377 numerical features: SimpleImputer (median imputation)
- Enforces strict ground-truth quarantine: raises LeakageViolationError on forbidden fields
- Training-only fitting: learners fit strictly on training partition, transform to float32
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Sequence, Union
import numpy as np
import pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import OrdinalEncoder

from integrations.ibm_architecture.exceptions import LeakageViolationError
from integrations.ibm_architecture.data.manifest import (
    CANONICAL_FEATURE_MANIFEST,
    FeatureManifest,
    QUARANTINED_COLUMNS,
)


class FeaturePipeline:
    """Preprocesses IEEE-CIS tabular features to float32 model input matrices."""

    def __init__(self, manifest: Optional[FeatureManifest] = None) -> None:
        self.manifest = manifest or CANONICAL_FEATURE_MANIFEST
        self.categorical_columns: List[str] = list(self.manifest.categorical_columns)
        self.numerical_columns: List[str] = list(self.manifest.numerical_columns)
        self.expected_feature_names: List[str] = (
            self.manifest.numerical_columns + self.manifest.categorical_columns
        )

        self.ordinal_encoder = OrdinalEncoder(
            handle_unknown="use_encoded_value",
            unknown_value=-1,
            encoded_missing_value=-1,
            dtype=np.float32,
        )
        self.medians_: np.ndarray = np.zeros(len(self.numerical_columns), dtype=np.float32)
        self.is_fitted: bool = False

    def _check_quarantine(self, df: pd.DataFrame) -> None:
        """Reject quarantined ground-truth target or raw identifiers."""
        cols_lower = {str(c).lower(): c for c in df.columns}
        violations = set()
        for q in QUARANTINED_COLUMNS:
            if q.lower() in cols_lower:
                violations.add(cols_lower[q.lower()])
        if violations:
            sorted_v = sorted(violations)
            raise LeakageViolationError(
                f"Quarantined fields detected in feature inputs: {sorted_v}",
                violated_fields=sorted_v,
                context="FeaturePipeline.validate_features",
            )

    def fit(self, df: pd.DataFrame) -> FeaturePipeline:
        """Fit encoders and compute medians strictly on training partition data."""
        self._check_quarantine(df)

        # 1. Compute median for numerical columns
        medians = []
        for col in self.numerical_columns:
            if col in df.columns:
                series = pd.to_numeric(df[col], errors="coerce")
                val = series.median()
                medians.append(float(val) if pd.notna(val) else 0.0)
            else:
                medians.append(0.0)
        self.medians_ = np.array(medians, dtype=np.float32)

        # 2. Fit categorical encoder
        cat_dict = {}
        for col in self.categorical_columns:
            if col in df.columns:
                cat_dict[col] = df[col].astype(str)
            else:
                cat_dict[col] = pd.Series(["__missing__"] * len(df), dtype=str)
        cat_df = pd.DataFrame(cat_dict, index=df.index)
        self.ordinal_encoder.fit(cat_df)

        self.is_fitted = True
        return self

    def transform(self, df: pd.DataFrame) -> np.ndarray:
        """Transform input DataFrame into a contiguous float32 array of shape (N, 391)."""
        if not self.is_fitted:
            raise RuntimeError("FeaturePipeline must be fitted before calling transform().")

        self._check_quarantine(df)
        n_rows = len(df)

        # 1. Numerical matrix extraction and imputation
        num_matrix = np.empty((n_rows, len(self.numerical_columns)), dtype=np.float32)
        for i, col in enumerate(self.numerical_columns):
            if col in df.columns:
                s = pd.to_numeric(df[col], errors="coerce").to_numpy(dtype=np.float32)
                nan_mask = np.isnan(s)
                if nan_mask.any():
                    num_matrix[:, i] = np.where(nan_mask, self.medians_[i], s)
                else:
                    num_matrix[:, i] = s
            else:
                num_matrix[:, i] = self.medians_[i]

        # 2. Categorical encoding
        cat_dict = {}
        for col in self.categorical_columns:
            if col in df.columns:
                cat_dict[col] = df[col].astype(str)
            else:
                cat_dict[col] = pd.Series(["__missing__"] * n_rows, dtype=str)
        cat_df = pd.DataFrame(cat_dict, index=df.index)
        cat_encoded = self.ordinal_encoder.transform(cat_df).astype(np.float32)

        # Concatenate in deterministic order (numericals then categoricals)
        X_out = np.hstack([num_matrix, cat_encoded]).astype(np.float32)
        assert X_out.shape == (n_rows, len(self.expected_feature_names))
        return X_out

    def fit_transform(self, df: pd.DataFrame) -> np.ndarray:
        """Convenience method to fit on training data and return transformed matrix."""
        return self.fit(df).transform(df)
