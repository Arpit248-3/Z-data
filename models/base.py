"""
SignalGate Base Fraud-Risk Models
Implements:
1. Primary candidate: HistGradientBoostingClassifier.
2. Sanity baseline: LogisticRegression (with train-fitted imputer & standardizer).
3. Prediction interfaces emitting strictly finite probabilities in [0, 1].
4. Joblib artifact serialization with cryptographic hashes and provenance manifests.
"""

import hashlib
import json
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import joblib
import numpy as np
import pandas as pd
import sklearn
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def fit_base(
    X_train: Union[pd.DataFrame, np.ndarray],
    y_train: Union[pd.Series, np.ndarray],
    seed: int = 11,
    model_type: str = "hgb",
    max_iter: int = 50,
    backend: str = "sklearn",
) -> Any:
    """
    Fit base fraud-risk classifier strictly on training partition.

    Parameters:
    - X_train: Training feature matrix (must not contain forbidden columns or labels).
    - y_train: Ground truth target labels (0 or 1).
    - seed: Random seed from config.yaml.
    - model_type: 'hgb' (HistGradientBoosting) or 'logistic' (LogisticRegression).
    - max_iter: Maximum iterations / trees.
    - backend: 'sklearn' (Snap ML disabled on x86).

    Returns:
    - Fitted model instance or pipeline.
    """
    if len(X_train) == 0 or len(y_train) == 0:
        raise ValueError("Cannot fit model on empty training data.")

    if len(X_train) != len(y_train):
        raise ValueError(f"Feature count {len(X_train)} does not match label count {len(y_train)}.")

    y_arr = np.asarray(y_train)
    unique_labels = np.unique(y_arr)
    if not set(unique_labels).issubset({0, 1}):
        raise ValueError(f"Labels must be binary in {{0, 1}}, observed: {unique_labels}")

    if model_type == "hgb":
        # early_stopping=False avoids an internal random validation split that would violate temporal chronology
        model = HistGradientBoostingClassifier(
            random_state=seed,
            max_iter=max_iter,
            min_samples_leaf=20,
            early_stopping=False,
        )
        model.fit(X_train, y_arr)
        return model

    elif model_type == "logistic":
        # LogisticRegression requires scaling and missing-value imputation
        pipeline = Pipeline([
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
            ("clf", LogisticRegression(random_state=seed, max_iter=max_iter, solver="lbfgs")),
        ])
        pipeline.fit(X_train, y_arr)
        return pipeline

    else:
        raise ValueError(f"Unsupported model_type '{model_type}'. Choose 'hgb' or 'logistic'.")


def raw_score(model: Any, X: Union[pd.DataFrame, np.ndarray]) -> np.ndarray:
    """
    Compute raw fraud risk probability P(Y=1) for feature matrix X.

    Returns:
    - 1D numpy array of probabilities bounded in [0, 1].
    """
    if len(X) == 0:
        return np.array([], dtype=float)

    if not hasattr(model, "predict_proba"):
        raise AttributeError("Model must provide a predict_proba method.")

    probs = model.predict_proba(X)

    if probs.ndim != 2 or probs.shape[1] < 2:
        raise ValueError(f"Unexpected predict_proba output shape: {probs.shape}")

    p = probs[:, 1]

    # Validate output finite bounds
    if not np.isfinite(p).all():
        raise ValueError("Model emitted non-finite (NaN or Inf) predicted probabilities.")

    if (p < 0.0).any() or (p > 1.0).any():
        raise ValueError(f"Predicted probabilities out of bounds [0, 1]: min={p.min()}, max={p.max()}")

    return p


def compute_file_sha256(filepath: str) -> str:
    """Compute SHA-256 hash of a file."""
    hasher = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()


def save_model_artifact(
    model: Any,
    filepath: Union[str, Path],
    manifest: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Atomically save a fitted model and companion manifest using joblib.
    """
    out_path = Path(filepath)
    if not out_path.is_absolute():
        out_path = PROJECT_ROOT / out_path
    os.makedirs(out_path.parent, exist_ok=True)

    # Write model artifact
    temp_path = out_path.with_suffix(".tmp")
    joblib.dump({"model": model, "manifest": manifest}, temp_path, compress=3)

    # Atomic rename
    temp_path.replace(out_path)

    # Compute checksum
    artifact_hash = compute_file_sha256(str(out_path))
    manifest_updated = dict(manifest)
    manifest_updated["artifact_sha256"] = artifact_hash
    manifest_updated["artifact_path"] = str(out_path)
    manifest_updated["saved_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

    # Write companion manifest JSON
    manifest_json_path = out_path.with_suffix(".meta.json")
    with open(manifest_json_path, "w", encoding="utf-8") as f:
        json.dump(manifest_updated, f, indent=2)

    return manifest_updated


def load_model_artifact(filepath: Union[str, Path]) -> Tuple[Any, Dict[str, Any]]:
    """
    Load saved model artifact and its manifest.
    """
    in_path = Path(filepath)
    if not in_path.is_absolute():
        in_path = PROJECT_ROOT / in_path

    if not in_path.exists():
        raise FileNotFoundError(f"Model artifact not found at {in_path}")

    data = joblib.load(in_path)
    if isinstance(data, dict) and "model" in data and "manifest" in data:
        return data["model"], data["manifest"]
    else:
        # Fallback if bare model was saved
        manifest_json_path = in_path.with_suffix(".meta.json")
        manifest = {}
        if manifest_json_path.exists():
            with open(manifest_json_path, "r", encoding="utf-8") as f:
                manifest = json.load(f)
        return data, manifest
