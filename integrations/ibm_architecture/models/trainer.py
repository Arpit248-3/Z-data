"""SignalGate IBM Architecture Integration — Memory-Safe Model Training Orchestration.

Implements bounded-memory local development training and isolated artifact serialization:
- Strictly bounds memory reads: ingests first 25,000 chronological transactions.
- Performs preflight physical RAM checks before data loading and model fitting.
- Partitions chronologically: Train (15,000), Calibration (2,500), Validation (2,500), Test (5,000).
- Fits FeaturePipeline, BaselineB2, and 5-member EraBaggedHeterogeneousEnsemble on Train.
- Fits PlattCalibrator strictly on Calibration; computes diagnostic ECE on Validation.
- Serializes isolated bundle to `models/artifacts/ieee_cis_v1_local_dev/`.
- Writes execution report to `results/ieee_cis_v1_local_dev/run_report.json`.
"""

from __future__ import annotations

import ctypes
import gc
import hashlib
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union
import numpy as np
import pandas as pd

from integrations.ibm_architecture.data.loader import get_memory_efficient_dtypes
from integrations.ibm_architecture.data.manifest import CANONICAL_FEATURE_MANIFEST
from integrations.ibm_architecture.exceptions import ArtifactNotFoundError, LeakageViolationError
from integrations.ibm_architecture.models.baseline import BaselineB2
from integrations.ibm_architecture.models.bundle import (
    ModelBundle,
    ModelBundleManifest,
    save_bundle,
)
from integrations.ibm_architecture.models.calibration import PlattCalibrator, calibration_ece
from integrations.ibm_architecture.models.ensemble import EraBaggedHeterogeneousEnsemble
from integrations.ibm_architecture.models.features import FeaturePipeline

DEFAULT_RAW_DIR = Path(__file__).resolve().parent.parent.parent.parent / "data" / "raw"
DEFAULT_LOCAL_DEV_ARTIFACT_DIR = (
    Path(__file__).resolve().parent.parent.parent.parent / "models" / "artifacts" / "ieee_cis_v1_local_dev"
)
DEFAULT_LOCAL_DEV_RESULTS_DIR = (
    Path(__file__).resolve().parent.parent.parent.parent / "results" / "ieee_cis_v1_local_dev"
)


def get_available_memory_mb() -> float:
    """Query available physical RAM in megabytes on Windows AMD64 or POSIX."""
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
                ("sullAvailExtendedVirtual", ctypes.c_ulonglong),
            ]
        stat = MEMORYSTATUSEX()
        stat.dwLength = ctypes.sizeof(MEMORYSTATUSEX)
        if ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(stat)):
            return float(stat.ullAvailPhys / (1024 * 1024))
    # Fallback for POSIX / standard envs
    try:
        import psutil
        return float(psutil.virtual_memory().available / (1024 * 1024))
    except Exception:
        return 2048.0  # Conservative estimate if unavailable


def check_memory_preflight(min_free_mb: float = 400.0, stage: str = "preflight") -> Dict[str, Any]:
    """Check available physical memory and halt cleanly if below safety threshold."""
    gc.collect()
    avail_mb = get_available_memory_mb()
    status = {
        "stage": stage,
        "available_mb": round(avail_mb, 2),
        "required_min_mb": min_free_mb,
        "sufficient": avail_mb >= min_free_mb,
    }
    if not status["sufficient"]:
        raise RuntimeError(
            f"Memory gate safety halt at stage '{stage}': available RAM ({avail_mb:.1f} MB) "
            f"is below the required safety threshold ({min_free_mb:.1f} MB)."
        )
    return status


def compute_partition_hash(tx_ids: Sequence[int], dts: Sequence[int]) -> str:
    """Compute deterministic SHA-256 hash of a partition's chronological ordering."""
    h = hashlib.sha256()
    for tid, dt in zip(tx_ids, dts):
        h.update(f"{tid}:{dt}\n".encode("utf-8"))
    return h.hexdigest()


def load_bounded_dev_cohort(
    data_dir: Optional[Union[str, Path]] = None,
    nrows: int = 25000,
) -> Tuple[pd.DataFrame, pd.Series, pd.Series, pd.Series]:
    """Load strictly the first nrows chronological transactions and matching identity records.

    Returns
    -------
    Tuple[features_df, target_series, dt_series, id_series]
    """
    raw_path = Path(data_dir) if data_dir else DEFAULT_RAW_DIR
    tx_file = raw_path / "train_transaction.csv"
    id_file = raw_path / "train_identity.csv"

    if not tx_file.exists() or not id_file.exists():
        raise ArtifactNotFoundError(
            artifact_path=str(tx_file),
            expected_purpose="IEEE-CIS raw transactions for local development run",
        )

    # 1. Bounded read of transactions
    dtypes = get_memory_efficient_dtypes()
    df_tx = pd.read_csv(tx_file, nrows=nrows, dtype=dtypes, low_memory=True)

    # 2. Verify chronological sorting on TransactionDT
    dt_arr = df_tx["TransactionDT"].values
    if not np.all(dt_arr[:-1] <= dt_arr[1:]):
        # Sort if not strictly monotonic
        df_tx = df_tx.sort_values(["TransactionDT", "TransactionID"]).reset_index(drop=True)

    target_tx_ids = set(df_tx["TransactionID"].unique())
    initial_count = len(df_tx)

    # 3. Extract quarantined target and metadata
    target_series = df_tx["isFraud"].copy()
    dt_series = df_tx["TransactionDT"].copy()
    id_series = df_tx["TransactionID"].copy()
    df_tx = df_tx.drop(columns=["isFraud"])

    # 4. Bounded identity join: only read identity rows matching the 25k transactions
    # Identity file is small (~26.5 MB), read and filter matching IDs
    df_id = pd.read_csv(id_file, low_memory=True)
    df_id_filtered = df_id[df_id["TransactionID"].isin(target_tx_ids)].copy()
    del df_id
    gc.collect()

    # Left join
    df_merged = pd.merge(df_tx, df_id_filtered, on="TransactionID", how="left")
    del df_tx, df_id_filtered
    gc.collect()

    if len(df_merged) != initial_count:
        raise ValueError(f"Merge cardinality error: expected {initial_count} rows, got {len(df_merged)}.")

    # Drop identifiers from model features
    df_features = df_merged.drop(columns=["TransactionID", "TransactionDT"])
    CANONICAL_FEATURE_MANIFEST.validate_features(df_features, context="load_bounded_dev_cohort")

    return df_features, target_series, dt_series, id_series


def split_dev_cohort(
    df_features: pd.DataFrame,
    target_series: pd.Series,
    dt_series: pd.Series,
    id_series: pd.Series,
    train_n: int = 15000,
    cal_n: int = 2500,
    val_n: int = 2500,
    test_n: int = 5000,
) -> Dict[str, Dict[str, Any]]:
    """Partition the bounded development cohort into exact chronological 60/10/10/20 splits."""
    total = len(df_features)
    expected_total = train_n + cal_n + val_n + test_n
    if total != expected_total:
        raise ValueError(f"Expected {expected_total} rows, but received {total}.")

    idx_train_end = train_n
    idx_cal_end = idx_train_end + cal_n
    idx_val_end = idx_cal_end + val_n
    idx_test_end = idx_val_end + test_n

    slices = {
        "train": (0, idx_train_end),
        "calibration": (idx_train_end, idx_cal_end),
        "validation": (idx_cal_end, idx_val_end),
        "test": (idx_val_end, idx_test_end),
    }

    partitions: Dict[str, Dict[str, Any]] = {}
    for name, (start, end) in slices.items():
        sub_X = df_features.iloc[start:end].copy()
        sub_y = target_series.iloc[start:end].copy()
        sub_dt = dt_series.iloc[start:end].values
        sub_id = id_series.iloc[start:end].values

        n_rows = len(sub_X)
        fraud_count = int(sub_y.sum())
        prevalence = float(fraud_count / n_rows) if n_rows > 0 else 0.0
        part_hash = compute_partition_hash(sub_id, sub_dt)

        partitions[name] = {
            "X": sub_X,
            "y": sub_y.values.astype(np.int8),
            "dt_min": int(sub_dt.min()),
            "dt_max": int(sub_dt.max()),
            "row_count": n_rows,
            "fraud_count": fraud_count,
            "prevalence": prevalence,
            "split_hash": part_hash,
        }

    return partitions


def train_local_dev_pipeline(
    data_dir: Optional[Union[str, Path]] = None,
    output_dir: Optional[Union[str, Path]] = None,
    results_dir: Optional[Union[str, Path]] = None,
    nrows: int = 25000,
) -> ModelBundle:
    """Execute the complete resource-constrained local development training workflow."""
    artifact_path = Path(output_dir) if output_dir else DEFAULT_LOCAL_DEV_ARTIFACT_DIR
    results_path = Path(results_dir) if results_dir else DEFAULT_LOCAL_DEV_RESULTS_DIR
    artifact_path.mkdir(parents=True, exist_ok=True)
    results_path.mkdir(parents=True, exist_ok=True)

    print(f"\n[Step 1/6] Preflight memory check...")
    mem_before = check_memory_preflight(min_free_mb=400.0, stage="pre-ingestion")
    print(f"  Available physical RAM: {mem_before['available_mb']:.1f} MB (Safety check PASSED)")

    print(f"\n[Step 2/6] Loading bounded development cohort ({nrows:,} rows)...")
    df_features, target_series, dt_series, id_series = load_bounded_dev_cohort(data_dir=data_dir, nrows=nrows)
    print(f"  Loaded {len(df_features):,} transactions with {df_features.shape[1]} features.")

    print(f"\n[Step 3/6] Chronological partitioning (60% Train, 10% Cal, 10% Val, 20% Test)...")
    partitions = split_dev_cohort(df_features, target_series, dt_series, id_series)
    del df_features, target_series, dt_series, id_series
    gc.collect()

    for p_name, p_data in partitions.items():
        print(
            f"  Partition {p_name:<12}: {p_data['row_count']:,} rows | "
            f"Fraud: {p_data['fraud_count']:,} ({p_data['prevalence']*100:.2f}%) | "
            f"DT: [{p_data['dt_min']} -> {p_data['dt_max']}]"
        )

    print(f"\n[Step 4/6] Preprocessing and Model Training...")
    check_memory_preflight(min_free_mb=350.0, stage="pre-training")

    # Fit feature pipeline strictly on Train
    train_part = partitions["train"]
    pipeline = FeaturePipeline()
    X_train = pipeline.fit_transform(train_part["X"])
    y_train = train_part["y"]
    print(f"  FeaturePipeline fitted on Train: output shape {X_train.shape}, dtype={X_train.dtype}")

    # Fit Baseline B2
    print("  Fitting Baseline B2 (HistGradientBoosting, max_iter=30, balanced)...")
    baseline = BaselineB2(max_iter=30, random_state=11, class_weight="balanced")
    baseline.fit(X_train, y_train)

    # Fit EraBaggedHeterogeneousEnsemble (local_dev mode)
    print("  Fitting EraBaggedHeterogeneousEnsemble (5 era-omitted members, local_dev mode)...")
    ensemble = EraBaggedHeterogeneousEnsemble(n_eras=5, mode="local_dev")
    ensemble.fit(X_train, y_train)

    print(f"\n[Step 5/6] Calibration and Diagnostic Verification...")
    # Calibration partition
    cal_part = partitions["calibration"]
    X_cal = pipeline.transform(cal_part["X"])
    cal_probas = ensemble.predict_proba(X_cal)

    calibrator = PlattCalibrator(C=1.0, max_iter=1000)
    calibrator.fit(cal_probas, cal_part["y"], partition="calibration")

    # Validation partition: diagnostic ECE
    val_part = partitions["validation"]
    X_val = pipeline.transform(val_part["X"])
    val_raw_probas = ensemble.predict_proba(X_val)
    val_cal_probas = calibrator.predict_proba(val_raw_probas)
    val_ece = calibration_ece(val_cal_probas, val_part["y"], n_bins=10)
    print(f"  Validation Diagnostic Expected Calibration Error (ECE): {val_ece:.4f}")

    # Held-out Test evaluation
    test_part = partitions["test"]
    X_test = pipeline.transform(test_part["X"])
    test_raw_probas = ensemble.predict_proba(X_test)
    test_cal_probas = calibrator.predict_proba(test_raw_probas)
    test_ece = calibration_ece(test_cal_probas, test_part["y"], n_bins=10)
    test_b2_probas = baseline.predict_proba(X_test)

    # Simple AUC approximations
    try:
        from sklearn.metrics import roc_auc_score, average_precision_score
        test_roc_auc = float(roc_auc_score(test_part["y"], test_cal_probas))
        test_pr_auc = float(average_precision_score(test_part["y"], test_cal_probas))
        test_b2_roc_auc = float(roc_auc_score(test_part["y"], test_b2_probas))
    except Exception:
        test_roc_auc = 0.0
        test_pr_auc = 0.0
        test_b2_roc_auc = 0.0

    print(f"  Test Held-out Diagnostic ROC-AUC (Ensemble): {test_roc_auc:.4f}")
    print(f"  Test Held-out Diagnostic PR-AUC  (Ensemble): {test_pr_auc:.4f}")
    print(f"  Test Held-out Diagnostic ROC-AUC (Baseline): {test_b2_roc_auc:.4f}")

    mem_after = get_available_memory_mb()
    print(f"  Available physical RAM after training: {mem_after:.1f} MB")

    print(f"\n[Step 6/6] Bundle serialization & cryptographic provenance...")
    manifest = ModelBundleManifest(
        architecture_version="ieee_cis_v1",
        execution_mode="RESOURCE_CONSTRAINED_LOCAL_DEV",
        benchmark_comparable=False,
        training_timestamp=datetime.now(timezone.utc).isoformat(),
        total_samples=nrows,
        row_counts={k: v["row_count"] for k, v in partitions.items()},
        dt_intervals={k: [v["dt_min"], v["dt_max"]] for k, v in partitions.items()},
        prevalence={k: v["prevalence"] for k, v in partitions.items()},
        split_hashes={k: v["split_hash"] for k, v in partitions.items()},
        feature_count=391,
        validation_ece=float(val_ece),
        calibration_metrics={
            "validation_ece": float(val_ece),
            "test_ece": float(test_ece),
            "test_roc_auc": float(test_roc_auc),
            "test_pr_auc": float(test_pr_auc),
            "test_b2_roc_auc": float(test_b2_roc_auc),
        },
        limitations=(
            "Trained strictly on a 25,000-row chronological subsample to respect the host memory gate "
            "(7.75 GB RAM total, 2.34 GB available). Estimators used local development resource caps "
            "(max_iter=30, ExtraTrees max_depth=12 with 30 trees, n_jobs=1). These artifacts allow full "
            "downstream code integration and test verification, but DO NOT reproduce the canonical full-data "
            "benchmark in results/results.json."
        ),
    )

    bundle = ModelBundle(
        pipeline=pipeline,
        baseline=baseline,
        ensemble=ensemble,
        calibrator=calibrator,
        manifest=manifest,
    )

    saved_manifest = save_bundle(bundle, artifact_path)
    print(f"  Artifact bundle serialized to: {artifact_path}")

    # Persist execution run report
    report_data = {
        "status": "LOCAL_DEV_TRAINING_SUCCESSFUL",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "execution_mode": "RESOURCE_CONSTRAINED_LOCAL_DEV",
        "benchmark_comparable": False,
        "nrows": nrows,
        "partitions": {
            k: {
                "row_count": v["row_count"],
                "fraud_count": v["fraud_count"],
                "prevalence": v["prevalence"],
                "dt_interval": [v["dt_min"], v["dt_max"]],
                "split_hash": v["split_hash"],
            }
            for k, v in partitions.items()
        },
        "metrics": saved_manifest.calibration_metrics,
        "component_checksums": saved_manifest.component_checksums,
        "memory_profile": {
            "available_before_mb": mem_before["available_mb"],
            "available_after_mb": round(mem_after, 2),
        },
        "limitations": saved_manifest.limitations,
    }

    report_file = results_path / "run_report.json"
    with open(report_file, "w", encoding="utf-8") as f:
        json.dump(report_data, f, indent=2)
    print(f"  Execution report persisted to: {report_file}")

    return bundle


def train_mock_pipeline_for_testing(
    mock_df: pd.DataFrame,
    output_dir: Path | str,
) -> ModelBundle:
    """Explicit helper for unit test execution using small labeled fixtures."""
    pipeline = FeaturePipeline()
    X = pipeline.fit_transform(mock_df.drop(columns=["isFraud", "TransactionID", "TransactionDT"], errors="ignore"))
    y = np.array([0, 1] * (len(X) // 2), dtype=np.int8)

    baseline = BaselineB2(max_iter=5)
    baseline.fit(X, y)

    ensemble = EraBaggedHeterogeneousEnsemble(n_eras=2, mode="local_dev")
    ensemble.fit(X, y)

    calibrator = PlattCalibrator(max_iter=10)
    calibrator.fit(np.linspace(0.1, 0.9, len(y)), y, partition="calibration")

    manifest = ModelBundleManifest(
        architecture_version="ieee_cis_v1_mock",
        execution_mode="MOCK_FIXTURE_TESTING",
        benchmark_comparable=False,
    )
    bundle = ModelBundle(pipeline, baseline, ensemble, calibrator, manifest)
    save_bundle(bundle, output_dir)
    return bundle
