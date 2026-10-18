"""
SignalGate Phase 3 Tests — Ensemble Disagreement & Rank-Residual u2
Covers:
1. Ensemble predictions reproducible under fixed seeds.
2. Disagreement scores match a hand-calculated toy example.
3. Constant ensemble predictions produce zero disagreement.
4. Rank-residualizer u2 fitting on calibration data and frozen before evaluation.
5. RankResidualizer raises error if transformed before being fitted.
6. Reloaded ensemble artifacts produce identical predictions on validation rows.
7. Preservation of SYNTHETIC_SMOKE_ONLY status in ensemble report.
"""

from pathlib import Path
import json
import numpy as np
import pandas as pd
import pytest

from models.base import save_model_artifact, load_model_artifact
from models.ensemble import (
    fit_ensemble,
    predict_ensemble_proba,
    disagreement,
    RankResidualizer,
    fit_rank_residual,
    apply_rank_residual,
    compute_disagreement_diagnostics,
)

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def test_disagreement_hand_calculated_toy_example():
    # Mock ensemble with predictable outputs
    class MockModel:
        def __init__(self, probs):
            self.probs = np.array(probs)

        def predict_proba(self, X):
            return np.column_stack([1.0 - self.probs, self.probs])

    # 3 members with probabilities for 2 samples:
    # Sample 0: [0.1, 0.2, 0.3] -> mean=0.2, std(ddof=0)=sqrt(((0.01+0+0.01)/3)) = sqrt(0.02/3) ~ 0.081649658
    # Sample 1: [0.5, 0.5, 0.5] -> mean=0.5, std(ddof=0)=0.0
    m1 = MockModel([0.1, 0.5])
    m2 = MockModel([0.2, 0.5])
    m3 = MockModel([0.3, 0.5])
    mock_ensemble = [m1, m2, m3]

    dummy_X = np.zeros((2, 3))
    u = disagreement(mock_ensemble, dummy_X, ddof=0)

    expected_0 = np.sqrt(0.02 / 3.0)
    expected_1 = 0.0

    assert np.isclose(u[0], expected_0, atol=1e-6)
    assert np.isclose(u[1], expected_1, atol=1e-6)


def test_ensemble_fitting_and_seed_reproducibility():
    rng = np.random.RandomState(42)
    X = pd.DataFrame({"feat_1": rng.normal(0, 1, 80), "feat_2": rng.normal(0, 1, 80)})
    y = pd.Series((rng.rand(80) < 0.25).astype(int))

    ensemble_a = fit_ensemble(X, y, seeds=[11, 22, 33])
    ensemble_b = fit_ensemble(X, y, seeds=[11, 22, 33])

    u_a = disagreement(ensemble_a, X)
    u_b = disagreement(ensemble_b, X)

    np.testing.assert_array_almost_equal(u_a, u_b, decimal=8)


def test_rank_residualizer_fit_and_transform_behavior():
    rng = np.random.RandomState(42)
    n = 100
    p_cal = rng.beta(1, 10, n)
    # Strongly correlated disagreement
    raw_u_cal = 0.5 * p_cal + rng.normal(0, 0.02, n)

    residualizer = RankResidualizer(degree=3, alpha=1.0)

    # Cannot transform before fitting
    with pytest.raises(RuntimeError, match="must be fitted on calibration data"):
        residualizer.transform(raw_u_cal, p_cal)

    residualizer.fit(raw_u_cal, p_cal)
    assert residualizer.is_fitted

    # Transform validation sample
    p_val = rng.beta(1, 10, 50)
    raw_u_val = 0.5 * p_val + rng.normal(0, 0.02, 50)
    u2_val = residualizer.transform(raw_u_val, p_val)

    assert len(u2_val) == 50
    assert np.isfinite(u2_val).all()


def test_ensemble_artifact_save_and_reload(tmp_path):
    rng = np.random.RandomState(42)
    X = pd.DataFrame({"feat_1": rng.normal(0, 1, 60), "feat_2": rng.normal(0, 1, 60)})
    y = pd.Series((rng.rand(60) < 0.2).astype(int))

    ensemble = fit_ensemble(X, y, seeds=[11, 22, 33])
    u_original = disagreement(ensemble, X)

    art_path = tmp_path / "test_ensemble.joblib"
    save_meta = save_model_artifact(
        ensemble,
        art_path,
        {"dataset_status": "SYNTHETIC_SMOKE_ONLY", "n_members": 3},
    )

    reloaded_ensemble, loaded_meta = load_model_artifact(art_path)
    u_reloaded = disagreement(reloaded_ensemble, X)

    np.testing.assert_array_almost_equal(u_original, u_reloaded, decimal=8)
    assert loaded_meta["n_members"] == 3


def test_ensemble_report_preserves_synthetic_smoke_status():
    report_path = PROJECT_ROOT / "results" / "ensemble_report.json"
    assert report_path.exists(), "results/ensemble_report.json must exist"

    with open(report_path, "r", encoding="utf-8") as f:
        report = json.load(f)

    assert report["status"] == "SYNTHETIC_SMOKE_ONLY"
    assert report["is_synthetic"] is True
    assert "spearman_corr_p_raw_u" in report["diagnostics"]
    assert "spearman_corr_p_u2" in report["diagnostics"]
    assert report["diagnostics"]["decorrelation_achieved"] > 0.0
