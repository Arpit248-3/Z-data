"""SignalGate IBM Architecture Integration — Feature Preprocessing Pipeline.

Fitted strictly on the training partition in compliance with Master Spec § C2 and § H:
- 14 categorical columns encoded via OrdinalEncoder(handle_unknown='use_encoded_value', unknown_value=-1, encoded_missing_value=-1).
- 377 numerical columns imputed via SimpleImputer(strategy='median').
- Strict quarantine barrier: raises LeakageViolationError if `isFraud`, `TransactionID`,
  or `TransactionDT` (or case-insensitive variants) enter the pipeline.
- Output: Contiguous np.float32 matrix of shape (N, 391) matching CANONICAL_FEATURE_MANIFEST.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from typing import List, Optional, Tuple, Union
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import OrdinalEncoder

from integrations.ibm_architecture.data.manifest import (
    CANONICAL_FEATURE_MANIFEST,
    QUARANTINED_COLUMNS,
    FeatureManifest,
)
from integrations.ibm_architecture.exceptions import LeakageViolationError


class FeaturePipeline:
    """Deterministic, leakage-quarantined feature preprocessor for IEEE-CIS data.

    Must be fitted strictly on the training partition.
    """

    def __init__(self, manifest: Optional[FeatureManifest] = None) -> None:
        self.manifest: FeatureManifest = manifest or CANONICAL_FEATURE_MANIFEST
        self.numerical_cols: List[str] = list(self.manifest.numerical_columns)
        self.categorical_cols: List[str] = list(self.manifest.categorical_columns)
        self.expected_features: List[str] = self.numerical_cols + self.categorical_cols

        self._num_imputer = SimpleImputer(strategy="median")
        self._cat_encoder = OrdinalEncoder(
            handle_unknown="use_encoded_value",
            unknown_value=-1,
            encoded_missing_value=-1,
        )
        self.is_fitted: bool = False

    def _validate_quarantine(self, df: pd.DataFrame, context: str = "FeaturePipeline") -> None:
        """Enforce strict quarantine barrier against target labels and transaction identifiers."""
        detected = [
            c for c in df.columns
            if c in QUARANTINED_COLUMNS or c.lower() in {q.lower() for q in QUARANTINED_COLUMNS}
        ]
        if detected:
            raise LeakageViolationError(
                f"Quarantine barrier breached in {context}: columns {detected} "
                f"are strictly prohibited from entering feature preprocessing.",
                violated_fields=detected,
                context=context,
            )

    def fit(self, df: pd.DataFrame) -> "FeaturePipeline":
        """Fit median imputers and ordinal encoders strictly on the training partition."""
        self._validate_quarantine(df, context="FeaturePipeline.fit")

        # Check required columns are present
        missing = [c for c in self.expected_features if c not in df.columns]
        if missing:
            raise ValueError(
                f"Training DataFrame is missing {len(missing)} required features from manifest. "
                f"First missing: {missing[:5]}"
            )

        # Fit numerical imputer
        num_data = df[self.numerical_cols]
        self._num_imputer.fit(num_data)

        # Fit categorical encoder
        cat_data = df[self.categorical_cols].astype(str)
        self._cat_encoder.fit(cat_data)

        self.is_fitted = True
        return self

    def transform(self, df: pd.DataFrame) -> np.ndarray:
        """Transform a feature DataFrame into contiguous float32 array of shape (N, 391)."""
        if not self.is_fitted:
            raise RuntimeError("FeaturePipeline must be fitted on training data before calling transform().")

        self._validate_quarantine(df, context="FeaturePipeline.transform")

        missing = [c for c in self.expected_features if c not in df.columns]
        if missing:
            raise ValueError(
                f"DataFrame is missing {len(missing)} required features from manifest. "
                f"First missing: {missing[:5]}"
            )

        # Impute numerical features (produce float32)
        num_data = df[self.numerical_cols]
        num_arr = self._num_imputer.transform(num_data).astype(np.float32)

        # Encode categorical features (produce float32)
        cat_data = df[self.categorical_cols].astype(str)
        cat_arr = self._cat_encoder.transform(cat_data).astype(np.float32)

        # Stack into contiguous float32 array: (N, 377 + 14) = (N, 391)
        X = np.ascontiguousarray(np.hstack([num_arr, cat_arr]), dtype=np.float32)
        return X

    def fit_transform(self, df: pd.DataFrame) -> np.ndarray:
        """Fit on training data and return transformed float32 matrix."""
        return self.fit(df).transform(df)

    @property
    def feature_count(self) -> int:
        return len(self.expected_features)
