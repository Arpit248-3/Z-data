"""Tests for SignalGate IBM Architecture Model Training, Ensemble, Calibration & Bundling.

Verifies:
- Learned feature pipeline and strict ground-truth quarantine.
- Baseline estimator B2.
- 5-member era-bagged heterogeneous ensemble with sequential fitting and n_jobs=1.
- Platt calibration partition governance (raises ValueError on validation/test).
- Epistemic disagreement signals (u >= 0, u2 >= 0).
- ModelBundle serialization, manifest tracking, and cryptographic checksum validation.
- Fail-closed training orchestration when raw data is missing.
- Pre-stage RAM safety checking.
"""

from __future__ import annotations

from pathlib import Path
import pytest
import numpy as np
import pandas as pd

from integrations.ibm_architecture.exceptions import (
    ArtifactNotFoundError,
    IncompatibleArtifactError,
    LeakageViolationError,
)
from integrations.ibm_architecture.data.manifest import CANONICAL_FEATURE_MANIFEST
from integrations.ibm_architecture.models.baseline import BaselineB2
from integrations.ibm_architecture.models.bundle import (
    ModelBundle,
    ModelBundleManifest,
    compute_file_sha256,
    load_bundle,
    save_bundle,
)
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
    compute_single_signals,
)
from integrations.ibm_architecture.models.trainer import (
    check_available_ram,
    train_mock_pipeline_for_testing,
    train_pipeline,
)


@pytest.fixture
def mock_labeled_df() -> pd.DataFrame:
    """Create a realistic labeled mock DataFrame for model testing."""
    np.random.seed(42)
    n = 100
    data = {
        "TransactionID": np.arange(1000, 1000 + n),
        "TransactionDT": np.arange(100, 100 + n),
        "isFraud": np.random.choice([0, 1], size=n, p=[0.8, 0.2]),
        "ProductCD": np.random.choice(["W", "C", "H", "R"], size=n),
        "card4": np.random.choice(["visa", "mastercard", "discover"], size=n),
        "card6": np.random.choice(["credit", "debit"], size=n),
        "P_emaildomain": np.random.choice(["gmail.com", "yahoo.com", "anonymous.com"], size=n),
        "R_emaildomain": np.random.choice(["gmail.com", "hotmail.com", "missing"], size=n),
        "DeviceType": np.random.choice(["desktop", "mobile"], size=n),
        "TransactionAmt": np.random.uniform(5.0, 500.0, size=n).astype(np.float32),
        "C1": np.random.poisson(2, size=n).astype(np.float32),
        "C2": np.random.poisson(1, size=n).astype(np.float32),
        "D1": np.random.uniform(0.0, 100.0, size=n).astype(np.float32),
        "V1": np.random.choice([0.0, 1.0, np.nan], size=n).astype(np.float32),
    }
    return pd.DataFrame(data)


def test_feature_pipeline_fit_transform_shape_and_quarantine(mock_labeled_df: pd.DataFrame):
    """Verify FeaturePipeline transforms inputs to (N, 391) and enforces quarantine."""
    fp = FeaturePipeline()
    X_df = mock_labeled_df.drop(columns=["isFraud", "TransactionID", "TransactionDT"])

    fp.fit(X_df)
    assert fp.is_fitted
    X_trans = fp.transform(X_df)

    assert isinstance(X_trans, np.ndarray)
    assert X_trans.shape == (len(mock_labeled_df), 391)
    assert X_trans.dtype == np.float32

    # Quarantine rejection tests
    for forbidden in ["isFraud", "TransactionID", "TransactionDT"]:
        bad_df = X_df.copy()
        bad_df[forbidden] = 1
        with pytest.raises(LeakageViolationError):
            fp.transform(bad_df)

        with pytest.raises(LeakageViolationError):
            FeaturePipeline().fit(bad_df)


def test_baseline_b2_fit_predict(mock_labeled_df: pd.DataFrame):
    """Verify Baseline B2 fits on training data and generates calibrated probabilities."""
    fp = FeaturePipeline()
    X_df = mock_labeled_df.drop(columns=["isFraud", "TransactionID", "TransactionDT"])
    X_trans = fp.fit_transform(X_df)
    y = mock_labeled_df["isFraud"].to_numpy(dtype=np.int8)

    b2 = BaselineB2(max_iter=10)
    b2.fit(X_trans, y)
    assert b2.is_fitted

    proba = b2.predict_proba(X_trans)
    assert proba.shape == (len(mock_labeled_df), 2)
    assert np.all(proba >= 0.0) and np.all(proba <= 1.0)
    np.testing.assert_allclose(proba.sum(axis=1), 1.0, atol=1e-5)

    pos_proba = b2.predict_positive_proba(X_trans)
    assert pos_proba.shape == (len(mock_labeled_df),)
    np.testing.assert_allclose(pos_proba, proba[:, 1], atol=1e-6)


def test_ensemble_eras_and_sequential_fit(mock_labeled_df: pd.DataFrame):
    """Verify EraBaggedHeterogeneousEnsemble era segmentation, n_jobs=1, and sequential fitting."""
    eras = compute_training_eras(100, n_eras=5)
    assert len(eras) == 5
    assert eras[0] == (0, 20)
    assert eras[4] == (80, 100)

    # Test era omission
    omitted = get_era_omitted_indices(100, omit_era_idx=2, n_eras=5)
    assert len(omitted) == 80
    assert not np.any((omitted >= 40) & (omitted < 60))

    # Test sequential fit with n_jobs=1
    ensemble = EraBaggedHeterogeneousEnsemble(extra_trees_n_jobs=1)
    assert ensemble.members["era2_omit_et_s11"].n_jobs == 1

    fp = FeaturePipeline()
    X_df = mock_labeled_df.drop(columns=["isFraud", "TransactionID", "TransactionDT"])
    X_trans = fp.fit_transform(X_df)
    y = mock_labeled_df["isFraud"].to_numpy(dtype=np.int8)

    stages_checked = []
    def record_stage(stage: str):
        stages_checked.append(stage)

    ensemble.fit(X_trans, y, pre_stage_ram_check=record_stage)
    assert ensemble.is_fitted
    assert len(stages_checked) == 5

    # Predictions
    mp = ensemble.predict_member_proba(X_trans)
    assert mp.proba_matrix.shape == (len(mock_labeled_df), 5)
    assert len(mp.member_ids) == 5

    p_cons = ensemble.predict_positive_proba(X_trans)
    assert p_cons.shape == (len(mock_labeled_df),)
    np.testing.assert_allclose(p_cons, np.mean(mp.proba_matrix, axis=1), atol=1e-6)


def test_platt_and_isotonic_calibration_partition_guards():
    """Verify PlattCalibrator partition governance and diagnostic ECE."""
    raw_scores = np.array([0.1, 0.3, 0.4, 0.7, 0.85, 0.9])
    y_calib = np.array([0, 0, 0, 1, 1, 1], dtype=np.int8)

    # Prohibited partition checks
    for bad_partition in ["validation", "val", "test", "holdout"]:
        with pytest.raises(ValueError, match="Prohibited partition for calibration"):
            validate_calibration_partition(bad_partition)
        with pytest.raises(ValueError):
            PlattCalibrator().fit(raw_scores, y_calib, partition=bad_partition)

    # Permitted fit on calibration
    calibrator = PlattCalibrator()
    calibrator.fit(raw_scores, y_calib, partition="calibration")
    assert calibrator.is_fitted

    calib_probs = calibrator.predict(raw_scores)
    assert calib_probs.shape == (6,)
    assert np.all(calib_probs >= 0.0) and np.all(calib_probs <= 1.0)
    # Monotonicity: higher raw risk score produces higher calibrated probability
    assert np.all(np.diff(calib_probs) >= 0)

    # Expected Calibration Error calculation
    ece = calibration_ece(calib_probs, y_calib, n_bins=5)
    assert isinstance(ece, float)
    assert ece >= 0.0


def test_disagreement_signals_mathematical_properties():
    """Verify epistemic disagreement signals u and u2 match statistical properties."""
    extractor_u = DisagreementSignalExtractor()
    extractor_u2 = RobustDisagreementSignalExtractor()

    # Consensus case: identical predictions across all members
    identical_preds = [0.42, 0.42, 0.42, 0.42, 0.42]
    assert extractor_u.extract(identical_preds) == 0.0
    assert extractor_u2.extract(identical_preds) == 0.0

    # Divergent case
    divergent_preds = [0.1, 0.3, 0.5, 0.7, 0.9]
    u = extractor_u.extract(divergent_preds)
    u2 = extractor_u2.extract(divergent_preds)
    assert u > 0.0
    assert u2 > 0.0
    np.testing.assert_allclose(u, np.std(divergent_preds, ddof=0), atol=1e-6)

    # Vectorized compute_signals
    proba_matrix = np.array([
        [0.1, 0.1, 0.1, 0.1, 0.1],
        [0.2, 0.3, 0.4, 0.5, 0.6],
    ], dtype=np.float32)
    mp = MemberPredictions(proba_matrix=proba_matrix, member_ids=[f"m{i}" for i in range(5)])

    signals = compute_signals(mp)
    assert len(signals) == 2
    assert signals[0]["u"] == 0.0
    assert signals[1]["u"] > 0.0
    assert signals[0]["n"] == 5.0


def test_bundle_serialization_roundtrip_and_checksum_verification(tmp_path: Path, mock_labeled_df: pd.DataFrame):
    """Verify ModelBundle save, load, checksum validation, and tamper-resistance."""
    bundle = train_mock_pipeline_for_testing(mock_labeled_df, output_dir=tmp_path / "bundle")

    # Verify manifest fields
    assert bundle.manifest.execution_concurrency == "sequential"
    assert bundle.manifest.member_concurrency == {"extra_trees_n_jobs": 1}
    assert bundle.manifest.feature_count == 391
    assert "baseline_b2.joblib" in bundle.manifest.artifact_hashes

    # Reload bundle from disk
    reloaded = load_bundle(tmp_path / "bundle")
    assert reloaded.manifest.execution_concurrency == "sequential"
    assert reloaded.manifest.artifact_hashes == bundle.manifest.artifact_hashes

    # Verify identical inference between original and reloaded
    X_df = mock_labeled_df.drop(columns=["isFraud", "TransactionID", "TransactionDT"])
    X_orig = bundle.feature_pipeline.transform(X_df)
    X_reloaded = reloaded.feature_pipeline.transform(X_df)
    np.testing.assert_array_equal(X_orig, X_reloaded)

    p_orig = bundle.ensemble.predict_positive_proba(X_orig)
    p_reloaded = reloaded.ensemble.predict_positive_proba(X_reloaded)
    np.testing.assert_allclose(p_orig, p_reloaded, atol=1e-6)

    # Tamper detection: modifying a joblib artifact must raise IncompatibleArtifactError
    artifact_to_tamper = tmp_path / "bundle" / "baseline_b2.joblib"
    with open(artifact_to_tamper, "ab") as f:
        f.write(b"CORRUPTED_BYTES")

    with pytest.raises(IncompatibleArtifactError):
        load_bundle(tmp_path / "bundle")


def test_train_pipeline_fail_closed_on_missing_csvs(tmp_path: Path):
    """Verify train_pipeline fails closed with ArtifactNotFoundError when raw CSVs are missing."""
    empty_dir = tmp_path / "empty_raw"
    empty_dir.mkdir(parents=True, exist_ok=True)

    with pytest.raises(ArtifactNotFoundError) as exc_info:
        train_pipeline(data_dir=empty_dir)

    assert "train_transaction.csv" in str(exc_info.value)


def test_pre_stage_ram_safety_check():
    """Verify check_available_ram behaves safely and enforces threshold."""
    # Tiny threshold should pass on any running host
    avail = check_available_ram(min_free_gb=0.01)
    assert avail > 0.01

    # Impossible threshold should raise MemoryError
    with pytest.raises(MemoryError, match="Pre-stage resource check failed"):
        check_available_ram(min_free_gb=9999999.0)
