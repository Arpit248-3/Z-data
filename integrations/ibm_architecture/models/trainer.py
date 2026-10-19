"""SignalGate IBM Architecture Integration — Memory-Controlled Training Orchestrator.

Orchestrates sequential, reproducible model training and calibration for IEEE-CIS:
- Dynamic pre-stage physical RAM checking (enforcing >= 6.0 GB available floor).
- Strict partition boundaries: estimators fit on train, Platt calibrator fits on calib,
  validation used only for permitted diagnostics, test held out strictly.
- Target isFraud and raw IDs (TransactionID, TransactionDT) quarantined from features.
- Cryptographic artifact bundle persistence with SHA-256 manifest tracking.
- Fail-closed execution: raises ArtifactNotFoundError if raw data is missing.
"""

from __future__ import annotations

import ctypes
import gc
import json
import logging
import os
from pathlib import Path
import sys
import time
from typing import Any, Callable, Dict, Optional, Tuple, Union

import numpy as np
import pandas as pd
from sklearn.metrics import brier_score_loss, roc_auc_score

from integrations.ibm_architecture.data.loader import DEFAULT_RAW_DIR, load_ieee_cis
from integrations.ibm_architecture.data.manifest import CANONICAL_FEATURE_MANIFEST
from integrations.ibm_architecture.data.splitter import ChronologicalSplitter
from integrations.ibm_architecture.exceptions import ArtifactNotFoundError
from integrations.ibm_architecture.models.baseline import BaselineB2
from integrations.ibm_architecture.models.bundle import (
    DEFAULT_ARTIFACT_DIR,
    ModelBundle,
    ModelBundleManifest,
    save_bundle,
)
from integrations.ibm_architecture.models.calibration import PlattCalibrator, calibration_ece
from integrations.ibm_architecture.models.ensemble import EraBaggedHeterogeneousEnsemble
from integrations.ibm_architecture.models.features import FeaturePipeline

logger = logging.getLogger(__name__)


def get_available_ram_gb() -> float:
    """Return available physical memory in GB across OS platforms."""
    if sys.platform == "win32":
        class MEMORYSTATUSEX(ctypes.Structure):
            _fields_ = [
                ("dwLength", ctypes.c_ulong),
                ("dwMemoryLoad", ctypes.c_ulong),
                ("ullTotalPhys", ctypes.c_ulonglong),
                ("ullAvailPhys", ctypes.c_ulonglong),
                ("ullTotalPageFile", ctypes.c_ulonglong),
                ("ullAvailPageFile", ctypes.c_ulonglong),
                ("ullTotalVirtual", ctypes.c_ulonglong),
                ("ullAvailVirtual", ctypes.c_ulonglong),
                ("ullAvailExtendedVirtual", ctypes.c_ulonglong),
            ]

        stat = MEMORYSTATUSEX()
        stat.dwLength = ctypes.sizeof(MEMORYSTATUSEX)
        if ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(stat)):
            return float(stat.ullAvailPhys) / (1024.0 ** 3)

    try:
        import psutil
        return float(psutil.virtual_memory().available) / (1024.0 ** 3)
    except ImportError:
        pass

    try:
        with open("/proc/meminfo", "r", encoding="utf-8") as f:
            for line in f:
                if line.startswith("MemAvailable:"):
                    return float(line.split()[1]) / (1024.0 ** 2)
    except Exception:
        pass

    return 16.0


def check_available_ram(min_free_gb: float = 6.0) -> float:
    """Check that available physical RAM meets or exceeds the specified safety floor.

    Raises
    ------
    MemoryError
        If available physical RAM is below the minimum threshold.
    """
    avail_gb = get_available_ram_gb()
    if avail_gb < min_free_gb:
        raise MemoryError(
            f"Pre-stage resource check failed: {avail_gb:.2f} GB available physical RAM, "
            f"which is below the required safety threshold of {min_free_gb:.2f} GB. "
            "Execution safely stopped to prevent system paging or out-of-memory termination."
        )
    return avail_gb


def train_pipeline(
    data_dir: Optional[Union[str, Path]] = None,
    output_dir: Optional[Union[str, Path]] = None,
    nrows: Optional[int] = None,
    min_free_ram_gb: float = 6.0,
    extra_trees_n_jobs: int = 1,
) -> ModelBundle:
    """Execute complete end-to-end sequential training and calibration pipeline.

    Parameters
    ----------
    data_dir : Path or str, optional
        Path to raw data directory containing IEEE-CIS CSV files.
    output_dir : Path or str, optional
        Destination directory for serialized model bundle artifacts.
    nrows : int, optional
        Optional row limit (for integration testing). If None, fits full dataset.
    min_free_ram_gb : float, default 6.0
        Safety floor for available physical RAM before every expensive stage.
    extra_trees_n_jobs : int, default 1
        Worker count for ExtraTreesClassifier. Default 1 guarantees bounded RAM.

    Returns
    -------
    ModelBundle
        The fitted and verified model bundle.
    """
    start_time = time.time()
    raw_dir = Path(data_dir) if data_dir else DEFAULT_RAW_DIR
    out_dir = Path(output_dir) if output_dir else DEFAULT_ARTIFACT_DIR

    # 1. Fail-closed check: verify raw data existence
    tx_file = raw_dir / "train_transaction.csv"
    id_file = raw_dir / "train_identity.csv"
    if not tx_file.exists() or not id_file.exists():
        missing = [str(f) for f in [tx_file, id_file] if not f.exists()]
        raise ArtifactNotFoundError(
            artifact_path=", ".join(missing),
            expected_purpose=(
                "IEEE-CIS Fraud Detection dataset files for real-data benchmark training. "
                "Training aborted fail-closed without fabricating weights or data."
            ),
        )

    # 2. Pre-ingestion RAM check
    start_avail_ram = check_available_ram(min_free_ram_gb)
    min_observed_ram = start_avail_ram

    def monitor_ram(stage_name: str) -> None:
        nonlocal min_observed_ram
        avail = check_available_ram(min_free_ram_gb)
        if avail < min_observed_ram:
            min_observed_ram = avail
        logger.info("Pre-stage RAM verified for %s: %.2f GB available.", stage_name, avail)

    # 3. Load raw transactions and identities
    logger.info("Loading IEEE-CIS raw dataset from %s...", raw_dir)
    df_features, target_series = load_ieee_cis(
        data_dir=raw_dir,
        nrows=nrows,
        include_target=True,
        include_metadata_cols=True,
    )
    if target_series is None:
        raise ValueError("Ground-truth target 'isFraud' must be present for training.")

    # 4. Attach target for synchronized chronological splitting
    df_features["isFraud"] = target_series.values
    del target_series
    gc.collect()

    logger.info("Performing chronological 60/10/10/20 partitioning on %d rows...", len(df_features))
    splitter = ChronologicalSplitter()
    splits = splitter.split(df_features, sort=True)
    split_meta = splitter.get_metadata(splits)
    del df_features
    gc.collect()

    # 5. Extract partitioned feature matrices and target vectors
    # Train
    train_df = splits["train"]
    y_train = train_df["isFraud"].to_numpy(dtype=np.int8)
    X_train_df = train_df.drop(columns=["isFraud", "TransactionID", "TransactionDT"])
    del train_df

    # Calibration
    calib_df = splits["calibration"]
    y_calib = calib_df["isFraud"].to_numpy(dtype=np.int8)
    X_calib_df = calib_df.drop(columns=["isFraud", "TransactionID", "TransactionDT"])
    del calib_df

    # Validation
    val_df = splits["validation"]
    y_val = val_df["isFraud"].to_numpy(dtype=np.int8)
    X_val_df = val_df.drop(columns=["isFraud", "TransactionID", "TransactionDT"])
    del val_df

    # Test
    test_df = splits["test"]
    y_test = test_df["isFraud"].to_numpy(dtype=np.int8)
    X_test_df = test_df.drop(columns=["isFraud", "TransactionID", "TransactionDT"])
    del test_df
    del splits
    gc.collect()

    # 6. Fit Feature Pipeline strictly on Training partition
    monitor_ram("fit_feature_pipeline")
    logger.info("Fitting FeaturePipeline on %d training rows...", len(X_train_df))
    feature_pipeline = FeaturePipeline()
    feature_pipeline.fit(X_train_df)

    logger.info("Transforming train, calibration, validation, and test partitions...")
    X_train = feature_pipeline.transform(X_train_df)
    del X_train_df
    gc.collect()

    X_calib = feature_pipeline.transform(X_calib_df)
    del X_calib_df
    gc.collect()

    X_val = feature_pipeline.transform(X_val_df)
    del X_val_df
    gc.collect()

    X_test = feature_pipeline.transform(X_test_df)
    del X_test_df
    gc.collect()

    # 7. Fit Standalone Baseline Estimator B2 on Training partition
    monitor_ram("fit_baseline_b2")
    logger.info("Fitting Baseline B2 (HistGradientBoostingClassifier)...")
    baseline_b2 = BaselineB2()
    baseline_b2.fit(X_train, y_train)
    gc.collect()

    # 8. Fit Heterogeneous Ensemble Sequentially with Pre-Stage Checks
    monitor_ram("fit_ensemble_start")
    logger.info("Fitting EraBaggedHeterogeneousEnsemble (n_jobs=%d)...", extra_trees_n_jobs)
    ensemble = EraBaggedHeterogeneousEnsemble(extra_trees_n_jobs=extra_trees_n_jobs)

    ensemble.fit(X_train, y_train, pre_stage_ram_check=monitor_ram)
    del X_train, y_train
    gc.collect()

    # 9. Fit Platt Calibrator strictly on Calibration partition
    monitor_ram("fit_calibrator")
    logger.info("Extracting raw ensemble predictions on calibration partition...")
    calib_mp = ensemble.predict_member_proba(X_calib)
    p_calib_raw = np.mean(calib_mp.proba_matrix, axis=1)
    del X_calib, calib_mp
    gc.collect()

    logger.info("Fitting PlattCalibrator strictly on calibration split...")
    calibrator = PlattCalibrator()
    calibrator.fit(p_calib_raw, y_calib, partition="calibration")
    del p_calib_raw, y_calib
    gc.collect()

    # 10. Compute Validation Diagnostic Metrics (Permitted diagnostics only)
    monitor_ram("eval_validation")
    logger.info("Computing validation diagnostic metrics...")
    val_mp = ensemble.predict_member_proba(X_val)
    p_val_raw = np.mean(val_mp.proba_matrix, axis=1)
    p_val_calib = calibrator.predict(p_val_raw)
    p_b2_val = baseline_b2.predict_positive_proba(X_val)
    del X_val, val_mp
    gc.collect()

    val_auc_ensemble = float(roc_auc_score(y_val, p_val_calib))
    val_auc_b2 = float(roc_auc_score(y_val, p_b2_val))
    val_brier_ensemble = float(brier_score_loss(y_val, p_val_calib))
    val_ece_ensemble = float(calibration_ece(p_val_calib, y_val))
    del y_val, p_val_raw, p_val_calib, p_b2_val
    gc.collect()

    # 11. Compute Held-Out Test Evaluation
    monitor_ram("eval_test")
    logger.info("Evaluating on held-out test partition...")
    test_mp = ensemble.predict_member_proba(X_test)
    p_test_raw = np.mean(test_mp.proba_matrix, axis=1)
    p_test_calib = calibrator.predict(p_test_raw)
    p_b2_test = baseline_b2.predict_positive_proba(X_test)
    del X_test, test_mp
    gc.collect()

    test_auc_ensemble = float(roc_auc_score(y_test, p_test_calib))
    test_auc_b2 = float(roc_auc_score(y_test, p_b2_test))
    test_brier_ensemble = float(brier_score_loss(y_test, p_test_calib))
    test_ece_ensemble = float(calibration_ece(p_test_calib, y_test))
    del y_test, p_test_raw, p_test_calib, p_b2_test
    gc.collect()

    duration = time.time() - start_time
    peak_memory_drop_mb = max(0.0, (start_avail_ram - min_observed_ram) * 1024.0)

    # 12. Assemble Manifest and Persist Bundle
    metrics = {
        "validation": {
            "ensemble_roc_auc": val_auc_ensemble,
            "baseline_b2_roc_auc": val_auc_b2,
            "ensemble_brier": val_brier_ensemble,
            "ensemble_ece": val_ece_ensemble,
        },
        "test": {
            "ensemble_roc_auc": test_auc_ensemble,
            "baseline_b2_roc_auc": test_auc_b2,
            "ensemble_brier": test_brier_ensemble,
            "ensemble_ece": test_ece_ensemble,
        },
    }

    manifest = ModelBundleManifest(
        architecture_version="ieee_cis_v1",
        execution_concurrency="sequential",
        member_concurrency={"extra_trees_n_jobs": extra_trees_n_jobs},
        feature_count=391,
        split_hashes={name: m.split_hash for name, m in split_meta.items()},
        row_counts={name: m.row_count for name, m in split_meta.items()},
        training_duration_seconds=round(duration, 2),
        memory_peak_mb=round(peak_memory_drop_mb, 2),
        metrics=metrics,
    )

    bundle = ModelBundle(
        feature_pipeline=feature_pipeline,
        baseline_b2=baseline_b2,
        ensemble=ensemble,
        calibrator=calibrator,
        manifest=manifest,
    )

    hashes = save_bundle(bundle, output_dir=out_dir)
    logger.info("Model bundle persisted to %s. Hashes: %s", out_dir, hashes)

    # Save summary report in results directory
    results_dir = Path("results") / "ieee_cis_v1"
    results_dir.mkdir(parents=True, exist_ok=True)
    report_file = results_dir / "training_report.json"
    report_data = {
        "status": "TRAINING_COMPLETED",
        "timestamp_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "execution_concurrency": "sequential",
        "duration_seconds": round(duration, 2),
        "manifest": manifest.model_dump(),
    }
    with open(report_file, "w", encoding="utf-8") as f:
        json.dump(report_data, f, indent=2)

    return bundle


def train_mock_pipeline_for_testing(
    mock_df: pd.DataFrame,
    output_dir: Optional[Union[str, Path]] = None,
    extra_trees_n_jobs: int = 1,
) -> ModelBundle:
    """Fast training fixture for unit tests using mock labeled DataFrames.

    Guarantees end-to-end component fit and bundle serialization without
    requiring the full multi-hundred megabyte raw dataset.
    """
    out_path = Path(output_dir) if output_dir else Path("tmp_mock_artifacts")
    out_path.mkdir(parents=True, exist_ok=True)

    # Ensure required columns exist
    if "isFraud" not in mock_df.columns:
        raise ValueError("mock_df must contain 'isFraud' target")
    if "TransactionID" not in mock_df.columns:
        mock_df["TransactionID"] = np.arange(1000, 1000 + len(mock_df))
    if "TransactionDT" not in mock_df.columns:
        mock_df["TransactionDT"] = np.arange(100, 100 + len(mock_df))

    splitter = ChronologicalSplitter()
    splits = splitter.split(mock_df, sort=True)
    split_meta = splitter.get_metadata(splits)

    # Train
    y_train = splits["train"]["isFraud"].to_numpy(dtype=np.int8)
    X_train_df = splits["train"].drop(columns=["isFraud", "TransactionID", "TransactionDT"])

    # Calibration
    y_calib = splits["calibration"]["isFraud"].to_numpy(dtype=np.int8)
    X_calib_df = splits["calibration"].drop(columns=["isFraud", "TransactionID", "TransactionDT"])

    # Validation
    y_val = splits["validation"]["isFraud"].to_numpy(dtype=np.int8)
    X_val_df = splits["validation"].drop(columns=["isFraud", "TransactionID", "TransactionDT"])

    # Test
    y_test = splits["test"]["isFraud"].to_numpy(dtype=np.int8)
    X_test_df = splits["test"].drop(columns=["isFraud", "TransactionID", "TransactionDT"])

    feature_pipeline = FeaturePipeline()
    feature_pipeline.fit(X_train_df)

    X_train = feature_pipeline.transform(X_train_df)
    X_calib = feature_pipeline.transform(X_calib_df)
    X_val = feature_pipeline.transform(X_val_df)
    X_test = feature_pipeline.transform(X_test_df)

    baseline_b2 = BaselineB2(max_iter=10)
    baseline_b2.fit(X_train, y_train)

    ensemble = EraBaggedHeterogeneousEnsemble(extra_trees_n_jobs=extra_trees_n_jobs)
    ensemble.fit(X_train, y_train)

    calib_mp = ensemble.predict_member_proba(X_calib)
    p_calib_raw = np.mean(calib_mp.proba_matrix, axis=1)

    calibrator = PlattCalibrator(max_iter=100)
    calibrator.fit(p_calib_raw, y_calib, partition="calibration")

    # Diagnostics on validation
    val_mp = ensemble.predict_member_proba(X_val)
    p_val_raw = np.mean(val_mp.proba_matrix, axis=1)
    p_val_calib = calibrator.predict(p_val_raw)
    val_ece = float(calibration_ece(p_val_calib, y_val))

    # Test
    test_mp = ensemble.predict_member_proba(X_test)
    p_test_raw = np.mean(test_mp.proba_matrix, axis=1)
    p_test_calib = calibrator.predict(p_test_raw)
    test_ece = float(calibration_ece(p_test_calib, y_test))

    manifest = ModelBundleManifest(
        architecture_version="ieee_cis_v1_mock",
        execution_concurrency="sequential",
        member_concurrency={"extra_trees_n_jobs": extra_trees_n_jobs},
        feature_count=391,
        split_hashes={name: m.split_hash for name, m in split_meta.items()},
        row_counts={name: m.row_count for name, m in split_meta.items()},
        metrics={
            "validation": {"ensemble_ece": val_ece},
            "test": {"ensemble_ece": test_ece},
        },
    )

    bundle = ModelBundle(
        feature_pipeline=feature_pipeline,
        baseline_b2=baseline_b2,
        ensemble=ensemble,
        calibrator=calibrator,
        manifest=manifest,
    )

    save_bundle(bundle, output_dir=out_path)
    return bundle


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%H:%M:%S",
    )
    print("=================================================================")
    print("Starting IEEE-CIS Sequential Training Pipeline (Full 590,540 rows)")
    print("=================================================================")
    bundle = train_pipeline()
    print("=================================================================")
    print("IEEE-CIS Training Pipeline Complete!")
    print(f"Duration: {bundle.manifest.training_duration_seconds}s")
    print(f"Peak Memory Drop: {bundle.manifest.memory_peak_mb} MB")
    print("Metrics:")
    print(json.dumps(bundle.manifest.metrics, indent=2))
    print("Artifact Hashes:")
    print(json.dumps(bundle.manifest.artifact_hashes, indent=2))
    print("=================================================================")
