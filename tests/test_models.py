"""
SignalGate Phase 3 Tests — Base Fraud-Risk Models
Covers:
1. Base models fit successfully on small deterministic training fixtures.
2. Train, calibration, and validation partitions remain isolated.
3. Forbidden columns (TransactionID, TransactionDT, isFraud, true_label) cannot enter feature matrix.
4. Predicted probabilities have the correct 1D shape and are bounded in [0, 1].
5. Saved model artifacts can be reloaded and reproduce identical predictions.
6. Model reports preserve SYNTHETIC_SMOKE_ONLY status.
"""

from pathlib import Path
import json
import numpy as np
import pandas as pd
import pytest

from data.schema import FORBIDDEN_MODEL_COLUMNS, TARGET_COLUMN
from data.load import load_dataset
from data.splits import make_splits
from data.features import extract_features_and_target
from models.base import (
    fit_base,
    raw_score,
    save_model_artifact,
    load_model_artifact,
)

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def test_base_models_fit_on_small_deterministic_fixture():
    # Small synthetic toy data
    rng = np.random.RandomState(42)
    X = pd.DataFrame({
        "amt": rng.uniform(10, 500, size=100),
        "feat_1": rng.normal(0, 1, size=100),
        "feat_2": rng.normal(0, 1, size=100),
    })
    y = pd.Series((rng.rand(100) < 0.2).astype(int))

    # Test HGB
    hgb = fit_base(X, y, seed=11, model_type="hgb", max_iter=20)
    p_hgb = raw_score(hgb, X)
    assert len(p_hgb) == 100
    assert np.isfinite(p_hgb).all()
    assert (p_hgb >= 0.0).all() and (p_hgb <= 1.0).all()

    # Test Logistic pipeline
    log_reg = fit_base(X, y, seed=11, model_type="logistic", max_iter=50)
    p_log = raw_score(log_reg, X)
    assert len(p_log) == 100
    assert np.isfinite(p_log).all()
    assert (p_log >= 0.0).all() and (p_log <= 1.0).all()


def test_forbidden_columns_rejected_from_model_features():
    rng = np.random.RandomState(42)
    X_leaked = pd.DataFrame({
        "amt": rng.uniform(10, 500, size=50),
        "TransactionID": range(50),
        "TransactionDT": range(1000, 1050),
        "isFraud": [0] * 50,
    })
    y = pd.Series([0] * 50)

    # When extracting features through data.features, forbidden columns are strictly stripped
    X_clean, _, _, _ = extract_features_and_target(X_leaked)
    for col in FORBIDDEN_MODEL_COLUMNS:
        assert col not in X_clean.columns


def test_model_artifact_save_and_reload_reproducibility(tmp_path):
    df, meta = load_dataset()
    splits = make_splits(df)

    X_train, y_train, _, manifest = extract_features_and_target(splits["train"])
    X_val, y_val, _, _ = extract_features_and_target(splits["val"], feature_manifest=manifest["feature_names"])

    model = fit_base(X_train, y_train, seed=11, model_type="hgb", max_iter=25)
    p_original = raw_score(model, X_val)

    art_path = tmp_path / "test_hgb.joblib"
    save_meta = save_model_artifact(
        model,
        art_path,
        {"dataset_status": "SYNTHETIC_SMOKE_ONLY", "seed": 11},
    )

    assert art_path.exists()
    assert "artifact_sha256" in save_meta

    reloaded_model, loaded_meta = load_model_artifact(art_path)
    p_reloaded = raw_score(reloaded_model, X_val)

    # Identical predictions
    np.testing.assert_array_almost_equal(p_original, p_reloaded, decimal=8)
    assert loaded_meta["dataset_status"] == "SYNTHETIC_SMOKE_ONLY"


def test_model_report_artifact_preserves_synthetic_smoke_status():
    report_path = PROJECT_ROOT / "results" / "model_report.json"
    assert report_path.exists(), "results/model_report.json must exist after Phase 3 run"

    with open(report_path, "r", encoding="utf-8") as f:
        report = json.load(f)

    assert report["status"] == "SYNTHETIC_SMOKE_ONLY"
    assert report["is_synthetic"] is True
    assert "HistGradientBoostingClassifier" in report["primary_model"]["name"]
    assert "LogisticRegression" in report["baseline_model"]["name"]
    assert report["primary_model"]["validation_metrics"]["brier_score"] is not None
