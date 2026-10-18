"""SignalGate IBM Architecture Integration — Phase 4 Model Unit Tests.

Verifies:
- FeaturePipeline schema compliance, float32 output, and LeakageViolationError on quarantined columns.
- BaselineB2 gradient boosting estimator.
- EraBaggedHeterogeneousEnsemble era segmentation, omission, and consensus averaging.
- PlattCalibrator and IsotonicCalibrator partition protections and monotonic probability mapping.
- Diagnostic ECE metric calculation.
- Disagreement signals u (std dev) and u2 (MAD from median).
- ModelBundle serialization, manifest generation, cryptographic checksums, and deserialization.
- Memory preflight checks and split validation.
"""

from __future__ import annotations

import tempfile
from pathlib import Path
import numpy as np
import pandas as pd
import pytest

from integrations.ibm_architecture.data.manifest import CANONICAL_FEATURE_MANIFEST
from integrations.ibm_architecture.exceptions import LeakageViolationError, ModeUnavailableError
from integrations.ibm_architecture.models.baseline import BaselineB2
from integrations.ibm_architecture.models.bundle import (
    ModelBundle,
    ModelBundleManifest,
    get_model_bundle,
    load_bundle,
    load_synthetic_bundle,
    save_bundle,
)
from integrations.ibm_architecture.models.synthetic_adapter import SyntheticModelAdapter
from integrations.ibm_architecture.models.calibration import (
    IsotonicCalibrator,
    PlattCalibrator,
    calibration_ece,
    validate_calibration_partition,
)
from integrations.ibm_architecture.models.ensemble import (
    EraBaggedHeterogeneousEnsemble,
    MemberPredictions,
    compute_training_eras,
    get_era_omitted_indices,
)
from integrations.ibm_architecture.models.features import FeaturePipeline
from integrations.ibm_architecture.models.signals import (
    DisagreementSignalExtractor,
    DisagreementSignals,
    RobustDisagreementSignalExtractor,
    compute_signals,
)
from integrations.ibm_architecture.models.trainer import (
    check_memory_preflight,
    get_available_memory_mb,
    split_dev_cohort,
)


@pytest.fixture
def mock_feature_df() -> pd.DataFrame:
    """Create a minimal synthetic DataFrame containing all 391 manifest features."""
    np.random.seed(42)
    n_rows = 100
    data = {}

    # 377 numerical features
    for col in CANONICAL_FEATURE_MANIFEST.numerical_columns:
        data[col] = np.random.randn(n_rows).astype(np.float32)

    # 14 categorical features
    for col in CANONICAL_FEATURE_MANIFEST.categorical_columns:
        data[col] = np.random.choice(["A", "B", "C", "missing"], size=n_rows)

    return pd.DataFrame(data)


# ---------------------------------------------------------------------------
# FeaturePipeline Tests
# ---------------------------------------------------------------------------

def test_feature_pipeline_fit_transform_shape(mock_feature_df: pd.DataFrame) -> None:
    pipeline = FeaturePipeline()
    X = pipeline.fit_transform(mock_feature_df)

    assert pipeline.is_fitted
    assert X.shape == (100, 391)
    assert X.dtype == np.float32
    assert np.all(np.isfinite(X))


def test_feature_pipeline_unfitted_transform_raises(mock_feature_df: pd.DataFrame) -> None:
    pipeline = FeaturePipeline()
    with pytest.raises(RuntimeError, match="must be fitted"):
        pipeline.transform(mock_feature_df)


@pytest.mark.parametrize("bad_col", ["isFraud", "isfraud", "TransactionID", "TransactionDT", "target"])
def test_feature_pipeline_quarantine_rejection(mock_feature_df: pd.DataFrame, bad_col: str) -> None:
    pipeline = FeaturePipeline()
    leaky_df = mock_feature_df.copy()
    leaky_df[bad_col] = 1

    with pytest.raises(LeakageViolationError):
        pipeline.fit(leaky_df)

    # Fit clean first, then test transform
    pipeline.fit(mock_feature_df)
    with pytest.raises(LeakageViolationError):
        pipeline.transform(leaky_df)


# ---------------------------------------------------------------------------
# Baseline B2 Tests
# ---------------------------------------------------------------------------

def test_baseline_b2_fit_predict(mock_feature_df: pd.DataFrame) -> None:
    pipeline = FeaturePipeline()
    X = pipeline.fit_transform(mock_feature_df)
    y = np.array([0, 1] * 50, dtype=np.int8)

    baseline = BaselineB2(max_iter=10, random_state=11)
    baseline.fit(X, y)

    probas = baseline.predict_proba(X)
    assert len(probas) == 100
    assert np.all(probas >= 0.0)
    assert np.all(probas <= 1.0)
    assert baseline.member_id == "baseline_b2_hgbc_s11"


# ---------------------------------------------------------------------------
# EraBaggedHeterogeneousEnsemble Tests
# ---------------------------------------------------------------------------

def test_compute_training_eras() -> None:
    eras = compute_training_eras(100, n_eras=5)
    assert len(eras) == 5
    assert eras[0] == (0, 20)
    assert eras[-1] == (80, 100)


def test_get_era_omitted_indices() -> None:
    idx = get_era_omitted_indices(100, omit_era_idx=0, n_eras=5)
    assert len(idx) == 80
    assert 0 not in idx
    assert 19 not in idx
    assert 20 in idx


def test_era_bagged_ensemble_fit_predict(mock_feature_df: pd.DataFrame) -> None:
    pipeline = FeaturePipeline()
    X = pipeline.fit_transform(mock_feature_df)
    y = np.array([0, 1] * 50, dtype=np.int8)

    ensemble = EraBaggedHeterogeneousEnsemble(n_eras=5, mode="local_dev")
    ensemble.fit(X, y)

    assert ensemble.is_fitted
    assert ensemble.n_members == 5
    assert len(ensemble.member_ids) == 5

    mp = ensemble.predict_member_proba(X)
    assert isinstance(mp, MemberPredictions)
    assert mp.proba_matrix.shape == (100, 5)
    assert np.all(mp.proba_matrix >= 0.0)
    assert np.all(mp.proba_matrix <= 1.0)

    consensus = ensemble.predict_proba(X)
    assert len(consensus) == 100
    assert np.allclose(consensus, mp.proba_matrix.mean(axis=1))


# ---------------------------------------------------------------------------
# Calibration Tests
# ---------------------------------------------------------------------------

def test_validate_calibration_partition_prohibits_val_and_test() -> None:
    validate_calibration_partition("calibration")
    with pytest.raises(ValueError, match="NEVER be fitted on 'validation'"):
        validate_calibration_partition("validation")
    with pytest.raises(ValueError, match="NEVER be fitted on 'test'"):
        validate_calibration_partition("test")


def test_platt_calibrator_fit_predict() -> None:
    scores = np.linspace(0.1, 0.9, 100)
    labels = np.array([0] * 50 + [1] * 50, dtype=np.int8)

    calibrator = PlattCalibrator(max_iter=100)
    calibrator.fit(scores, labels, partition="calibration")

    calibrated = calibrator.predict_proba(scores)
    assert len(calibrated) == 100
    assert np.all(calibrated >= 0.0)
    assert np.all(calibrated <= 1.0)
    # Sigmoid mapping is monotonic
    assert np.all(calibrated[:-1] <= calibrated[1:])


def test_isotonic_calibrator_fit_predict() -> None:
    scores = np.linspace(0.1, 0.9, 100)
    labels = np.array([0] * 50 + [1] * 50, dtype=np.int8)

    calibrator = IsotonicCalibrator()
    calibrator.fit(scores, labels, partition="calibration")

    calibrated = calibrator.predict_proba(scores)
    assert len(calibrated) == 100
    assert np.all(calibrated >= 0.0)
    assert np.all(calibrated <= 1.0)


def test_calibration_ece_metric() -> None:
    scores = np.array([0.1, 0.2, 0.8, 0.9])
    labels = np.array([0, 0, 1, 1], dtype=np.int8)
    ece = calibration_ece(scores, labels, n_bins=5)
    assert ece >= 0.0
    assert isinstance(ece, float)


# ---------------------------------------------------------------------------
# Disagreement Signals Tests
# ---------------------------------------------------------------------------

def test_disagreement_signals_calculation() -> None:
    # 3 samples, 5 members
    probas = np.array([
        [0.2, 0.2, 0.2, 0.2, 0.2],  # Zero disagreement
        [0.1, 0.2, 0.3, 0.4, 0.5],  # Spread
        [0.0, 0.1, 0.1, 0.1, 0.9],  # One outlier
    ])
    mp = MemberPredictions(proba_matrix=probas, member_ids=[f"m{i}" for i in range(5)])

    signals = compute_signals(mp)
    assert signals.shape == (3,)
    assert signals["n"][0] == 5.0

    # Row 0: zero std and zero MAD
    assert signals["u"][0] == 0.0
    assert signals["u2"][0] == 0.0
    assert signals["p"][0] == 0.2

    # Row 1: strictly positive
    assert signals["u"][1] > 0.0
    assert signals["u2"][1] > 0.0


# ---------------------------------------------------------------------------
# ModelBundle Serialization Tests
# ---------------------------------------------------------------------------

def test_model_bundle_save_and_load(mock_feature_df: pd.DataFrame) -> None:
    pipeline = FeaturePipeline()
    X = pipeline.fit_transform(mock_feature_df)
    y = np.array([0, 1] * 50, dtype=np.int8)

    baseline = BaselineB2(max_iter=5)
    baseline.fit(X, y)

    ensemble = EraBaggedHeterogeneousEnsemble(n_eras=2, mode="local_dev")
    ensemble.fit(X, y)

    calibrator = PlattCalibrator(max_iter=10)
    calibrator.fit(np.linspace(0.1, 0.9, 100), y, partition="calibration")

    manifest = ModelBundleManifest(
        architecture_version="ieee_cis_v1",
        execution_mode="RESOURCE_CONSTRAINED_LOCAL_DEV",
        benchmark_comparable=False,
        row_counts={"train": 100},
    )
    bundle = ModelBundle(pipeline, baseline, ensemble, calibrator, manifest)

    with tempfile.TemporaryDirectory() as tmp_dir:
        saved_manifest = save_bundle(bundle, tmp_dir)
        assert len(saved_manifest.component_checksums) == 4
        assert "feature_pipeline.joblib" in saved_manifest.component_checksums

        loaded_bundle = load_bundle(tmp_dir)
        assert loaded_bundle.manifest.execution_mode == "RESOURCE_CONSTRAINED_LOCAL_DEV"
        assert loaded_bundle.manifest.benchmark_comparable is False

        # Verify scoring outputs match
        scores_orig = bundle.score_features(mock_feature_df)
        scores_loaded = loaded_bundle.score_features(mock_feature_df)
        assert np.allclose(scores_orig["p_cal"], scores_loaded["p_cal"])
        assert np.allclose(scores_orig["u"], scores_loaded["u"])


# ---------------------------------------------------------------------------
# Memory Preflight & Split Tests
# ---------------------------------------------------------------------------

def test_memory_preflight_check() -> None:
    avail_mb = get_available_memory_mb()
    assert avail_mb > 0.0

    status = check_memory_preflight(min_free_mb=10.0, stage="test_preflight")
    assert status["sufficient"] is True


def test_split_dev_cohort() -> None:
    n_total = 25000
    df = pd.DataFrame({"feat1": np.zeros(n_total, dtype=np.float32)})
    y = pd.Series([0, 1] * (n_total // 2))
    dt = pd.Series(np.arange(1000, 1000 + n_total))
    tids = pd.Series(np.arange(2000, 2000 + n_total))

    parts = split_dev_cohort(df, y, dt, tids, train_n=15000, cal_n=2500, val_n=2500, test_n=5000)
    assert parts["train"]["row_count"] == 15000
    assert parts["calibration"]["row_count"] == 2500
    assert parts["validation"]["row_count"] == 2500
    assert parts["test"]["row_count"] == 5000
    assert len(parts["train"]["split_hash"]) == 64


# ---------------------------------------------------------------------------
# Synthetic Model Adapter & Bundle Tests (SYNTHETIC_SMOKE_ONLY)
# ---------------------------------------------------------------------------

def test_synthetic_model_adapter_loading_and_manifest() -> None:
    adapter = SyntheticModelAdapter.load()
    assert adapter.execution_mode == "SYNTHETIC_SMOKE_ONLY"
    assert adapter.is_synthetic is True
    assert adapter.real_data_training_status == "DEFERRED"
    assert adapter.manifest.benchmark_comparable is False
    assert len(adapter.feature_names) == 67
    assert len(adapter.ensemble_members) == 3
    assert len(adapter.manifest.component_checksums) == 4


def test_synthetic_model_adapter_quarantine() -> None:
    adapter = SyntheticModelAdapter.load()
    df_leak = pd.DataFrame({"isFraud": [0, 1], "TransactionAmt": [10.0, 20.0]})
    with pytest.raises(LeakageViolationError):
        adapter.score_features(df_leak)

    df_id_leak = pd.DataFrame({"TransactionID": [100, 101], "TransactionAmt": [10.0, 20.0]})
    with pytest.raises(LeakageViolationError):
        adapter.score_features(df_id_leak)

    df_dt_leak = pd.DataFrame({"TransactionDT": [86400, 86401], "TransactionAmt": [10.0, 20.0]})
    with pytest.raises(LeakageViolationError):
        adapter.score_features(df_dt_leak)


def test_synthetic_model_adapter_inference() -> None:
    adapter = SyntheticModelAdapter.load()
    # Read first 5 rows from synthetic smoke fixture
    df_fixture = pd.read_csv("data/synthetic_smoke_fixture.csv", nrows=5)
    # Strip forbidden columns before passing to feature scoring
    clean_df = df_fixture.drop(columns=["isFraud", "TransactionID", "TransactionDT"], errors="ignore")

    results = adapter.score_features(clean_df)
    assert "p_raw" in results
    assert "p_cal" in results
    assert "u" in results
    assert "u2" in results
    assert "n" in results
    assert "p_b2" in results
    assert results["n"] == 3
    assert results["execution_mode"] == "SYNTHETIC_SMOKE_ONLY"
    assert results["benchmark_comparable"] is False
    assert results["real_data_training_status"] == "DEFERRED"

    # Value checks
    assert len(results["p_raw"]) == 5
    assert np.all(results["p_raw"] >= 0.0) and np.all(results["p_raw"] <= 1.0)
    assert np.all(results["p_cal"] >= 0.0) and np.all(results["p_cal"] <= 1.0)
    assert np.all(results["p_b2"] >= 0.0) and np.all(results["p_b2"] <= 1.0)
    assert np.all(results["u"] >= 0.0)
    assert np.all(np.isfinite(results["u2"]))


def test_load_synthetic_bundle_and_factory() -> None:
    bundle = load_synthetic_bundle()
    assert bundle.execution_mode == "SYNTHETIC_SMOKE_ONLY"
    assert bundle.is_synthetic is True
    assert bundle.real_data_training_status == "DEFERRED"

    # Factory in SYNTHETIC_SMOKE_ONLY mode
    b_syn = get_model_bundle("SYNTHETIC_SMOKE_ONLY")
    assert b_syn.execution_mode == "SYNTHETIC_SMOKE_ONLY"

    # Factory in IEEE_CIS_OFFLINE_BENCHMARK mode fails closed with explicit error
    with pytest.raises(ModeUnavailableError) as exc_info:
        get_model_bundle("IEEE_CIS_OFFLINE_BENCHMARK")
    assert "DEFERRED" in str(exc_info.value)
    assert "16" in str(exc_info.value)  # mentions 16 GB requirement

    # Factory in LIVE_SOURCE_NOT_CONNECTED mode fails closed
    with pytest.raises(ModeUnavailableError) as exc_info_live:
        get_model_bundle("LIVE_SOURCE_NOT_CONNECTED")
    assert "DISCONNECTED" in str(exc_info_live.value)

