"""
SignalGate Phase 3 Pipeline Execution Script
Fits:
1. Base models (HistGradientBoosting primary + LogisticRegression baseline) on train split.
2. Calibrators (sigmoid, isotonic) on calibration split using FrozenEstimator.
3. 3-member ensemble on train split.
4. Rank-residualizer u2 on calibration split.
Evaluates all diagnostics strictly on validation split (never test!).
Saves fitted artifacts to models/artifacts/ and reports to results/.
All artifacts are stamped SYNTHETIC_SMOKE_ONLY.
"""

import hashlib
import json
import os
import sys
import time
from pathlib import Path
import joblib
import numpy as np
import pandas as pd
import sklearn

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from data.load import load_dataset
from data.splits import make_splits
from data.features import extract_features_and_target
from models.base import fit_base, raw_score, save_model_artifact
from models.calibrate import (
    fit_calibrator,
    calibrated_p,
    compare_calibrators,
    evaluate_calibration,
)
from models.ensemble import (
    fit_ensemble,
    disagreement,
    fit_rank_residual,
    apply_rank_residual,
    compute_disagreement_diagnostics,
)


def compute_config_hash() -> str:
    cfg_path = PROJECT_ROOT / "config.yaml"
    if cfg_path.exists():
        hasher = hashlib.sha256()
        with open(cfg_path, "rb") as f:
            while chunk := f.read(65536):
                hasher.update(chunk)
        return hasher.hexdigest()
    return "unknown"


def run_phase3_pipeline() -> dict:
    print("=" * 70)
    print("SignalGate Phase 3: Base Model, Calibration & Ensemble Fitting")
    print("=" * 70)

    # 1. Load data and make chronological splits
    df, meta = load_dataset()
    splits = make_splits(df)

    dataset_status = meta["status"]
    is_synthetic = meta["is_synthetic"]
    dataset_sha256 = meta["sha256"]
    cfg_hash = compute_config_hash()

    print(f"Dataset status: {dataset_status} | SHA-256: {dataset_sha256[:12]}...")
    print(f"Train rows: {len(splits['train'])} | Calib: {len(splits['calib'])} | Val: {len(splits['val'])} | Test: {len(splits['test'])} (UNTOUCHED)")

    # 2. Extract features using frozen train manifest
    X_train, y_train, _, train_manifest = extract_features_and_target(splits["train"])
    feature_names = train_manifest["feature_names"]
    feature_hash = hashlib.sha256(",".join(feature_names).encode("utf-8")).hexdigest()

    X_calib, y_calib, _, _ = extract_features_and_target(splits["calib"], feature_manifest=feature_names)
    X_val, y_val, _, _ = extract_features_and_target(splits["val"], feature_manifest=feature_names)

    artifacts_dir = PROJECT_ROOT / "models" / "artifacts"
    results_dir = PROJECT_ROOT / "results"
    os.makedirs(artifacts_dir, exist_ok=True)
    os.makedirs(results_dir, exist_ok=True)

    # Base common manifest attributes
    common_manifest = {
        "dataset_source": meta["source_path"],
        "dataset_status": dataset_status,
        "is_synthetic": is_synthetic,
        "dataset_sha256": dataset_sha256,
        "config_sha256": cfg_hash,
        "feature_count": len(feature_names),
        "feature_manifest_sha256": feature_hash,
        "train_rows": len(X_train),
        "calib_rows": len(X_calib),
        "val_rows": len(X_val),
        "scikit_learn_version": sklearn.__version__,
        "evidence_classification": "SYNTHETIC_DEVELOPMENT_EVIDENCE_ONLY" if is_synthetic else "REAL_EVIDENCE",
    }

    # =========================================================================
    # Step 1: Base Model Fitting
    # =========================================================================
    print("\n[1/4] Fitting base models on train partition...")
    t0 = time.perf_counter()
    hgb_model = fit_base(X_train, y_train, seed=11, model_type="hgb", max_iter=50)
    hgb_fit_ms = round((time.perf_counter() - t0) * 1000, 2)

    t0 = time.perf_counter()
    log_model = fit_base(X_train, y_train, seed=11, model_type="logistic", max_iter=100)
    log_fit_ms = round((time.perf_counter() - t0) * 1000, 2)

    # Validation diagnostics
    p_val_hgb = raw_score(hgb_model, X_val)
    val_metrics_hgb = evaluate_calibration(y_val, p_val_hgb)

    p_val_log = raw_score(log_model, X_val)
    val_metrics_log = evaluate_calibration(y_val, p_val_log)

    print(f"      HGB fit time: {hgb_fit_ms} ms | Val Brier: {val_metrics_hgb['brier_score']} | ROC-AUC: {val_metrics_hgb['roc_auc']}")
    print(f"      Logistic fit time: {log_fit_ms} ms | Val Brier: {val_metrics_log['brier_score']} | ROC-AUC: {val_metrics_log['roc_auc']}")

    # Save base artifacts
    hgb_manifest = {
        **common_manifest,
        "model_type": "HistGradientBoostingClassifier",
        "parameters": {"random_state": 11, "max_iter": 50, "min_samples_leaf": 20, "early_stopping": False},
        "fit_time_ms": hgb_fit_ms,
        "validation_metrics": val_metrics_hgb,
    }
    saved_hgb = save_model_artifact(hgb_model, artifacts_dir / "hgb_base.joblib", hgb_manifest)

    log_manifest = {
        **common_manifest,
        "model_type": "LogisticRegression_Pipeline",
        "parameters": {"random_state": 11, "max_iter": 100, "scaler": "StandardScaler", "imputer": "SimpleImputer(median)"},
        "fit_time_ms": log_fit_ms,
        "validation_metrics": val_metrics_log,
    }
    saved_log = save_model_artifact(log_model, artifacts_dir / "logistic_base.joblib", log_manifest)

    model_report = {
        "status": dataset_status,
        "is_synthetic": is_synthetic,
        "primary_model": {
            "name": "HistGradientBoostingClassifier",
            "artifact_path": saved_hgb["artifact_path"],
            "artifact_sha256": saved_hgb["artifact_sha256"],
            "fit_time_ms": hgb_fit_ms,
            "validation_metrics": val_metrics_hgb,
        },
        "baseline_model": {
            "name": "LogisticRegression_Pipeline",
            "artifact_path": saved_log["artifact_path"],
            "artifact_sha256": saved_log["artifact_sha256"],
            "fit_time_ms": log_fit_ms,
            "validation_metrics": val_metrics_log,
        },
        "metadata": common_manifest,
    }
    with open(results_dir / "model_report.json", "w", encoding="utf-8") as f:
        json.dump(model_report, f, indent=2)

    # =========================================================================
    # Step 2: Probability Calibration
    # =========================================================================
    print("\n[2/4] Fitting calibrators on calibration partition & comparing on validation...")
    calib_comparison, fitted_calibrators = compare_calibrators(
        hgb_model,
        X_calib,
        y_calib,
        X_val,
        y_val,
        methods=["uncalibrated", "sigmoid", "isotonic"],
    )

    selected_method = calib_comparison["selected_method"]
    print(f"      Selected calibration method: {selected_method.upper()}")
    for m, info in calib_comparison["methods_evaluated"].items():
        if info.get("validation_metrics"):
            vm = info["validation_metrics"]
            print(f"      - {m:<12}: Val Brier={vm['brier_score']:.6f} | ECE={vm['ece']:.6f} | ROC-AUC={vm['roc_auc']}")

    # Save calibration artifacts
    saved_calibrators = {}
    for m in ["sigmoid", "isotonic"]:
        cal_obj = fitted_calibrators.get(m)
        if cal_obj is not None:
            cal_manifest = {
                **common_manifest,
                "calibration_method": m,
                "base_model_artifact": saved_hgb["artifact_path"],
                "api_path": f"sklearn.frozen.FrozenEstimator + CalibratedClassifierCV(method='{m}')",
                "validation_metrics": calib_comparison["methods_evaluated"][m]["validation_metrics"],
            }
            saved_meta = save_model_artifact(cal_obj, artifacts_dir / f"calibrator_{m}.joblib", cal_manifest)
            saved_calibrators[m] = saved_meta

    calib_report = {
        "status": dataset_status,
        "is_synthetic": is_synthetic,
        "selected_method": selected_method,
        "selection_rule": calib_comparison["selection_criterion"],
        "comparison": calib_comparison["methods_evaluated"],
        "saved_artifacts": saved_calibrators,
        "metadata": common_manifest,
    }
    with open(results_dir / "calibration_report.json", "w", encoding="utf-8") as f:
        json.dump(calib_report, f, indent=2)

    # =========================================================================
    # Step 3: Ensemble Disagreement
    # =========================================================================
    print("\n[3/4] Fitting 3-member ensemble on train partition...")
    seeds = [11, 22, 33]
    t0 = time.perf_counter()
    ensemble_members = fit_ensemble(X_train, y_train, seeds=seeds)
    ensemble_fit_ms = round((time.perf_counter() - t0) * 1000, 2)
    print(f"      Ensemble fitted ({len(ensemble_members)} members) in {ensemble_fit_ms} ms")

    # Compute disagreement on validation
    u_val = disagreement(ensemble_members, X_val)
    p_val_selected = (
        calibrated_p(fitted_calibrators[selected_method], X_val)
        if selected_method != "uncalibrated"
        else p_val_hgb
    )

    # =========================================================================
    # Step 4: Rank-Residual Disagreement (u2)
    # =========================================================================
    print("\n[4/4] Fitting RankResidualizer u2 on calibration split...")
    u_calib = disagreement(ensemble_members, X_calib)
    p_calib_selected = (
        calibrated_p(fitted_calibrators[selected_method], X_calib)
        if selected_method != "uncalibrated"
        else raw_score(hgb_model, X_calib)
    )

    residualizer = fit_rank_residual(u_calib, p_calib_selected)
    u2_val = apply_rank_residual(residualizer, u_val, p_val_selected)

    disagree_diagnostics = compute_disagreement_diagnostics(p_val_selected, u_val, u2=u2_val)
    print(f"      Validation rho(p, raw_u) : {disagree_diagnostics['spearman_corr_p_raw_u']}")
    print(f"      Validation rho(p, u2)    : {disagree_diagnostics['spearman_corr_p_u2']}")
    print(f"      Decorrelation achieved   : {disagree_diagnostics['decorrelation_achieved']}")

    # Save ensemble & residualizer artifacts
    ensemble_manifest = {
        **common_manifest,
        "n_members": len(ensemble_members),
        "seeds": seeds,
        "fit_time_ms": ensemble_fit_ms,
        "disagreement_formula": "u = std(member_probabilities, axis=0, ddof=0)",
        "diagnostics": disagree_diagnostics,
    }
    saved_ensemble = save_model_artifact(ensemble_members, artifacts_dir / "ensemble_members.joblib", ensemble_manifest)

    res_manifest = {
        **common_manifest,
        "method": "RankResidualizer",
        "description": "Mapping from rank(p) to rank(u) on calibration split; residual u2 = r_u - hat{r}_u",
        "n_calib_points": len(u_calib),
        "spearman_corr_p_u2_val": disagree_diagnostics["spearman_corr_p_u2"],
    }
    saved_res = save_model_artifact(residualizer, artifacts_dir / "residualizer_u2.joblib", res_manifest)

    ensemble_report = {
        "status": dataset_status,
        "is_synthetic": is_synthetic,
        "ensemble_artifact": saved_ensemble["artifact_path"],
        "ensemble_sha256": saved_ensemble["artifact_sha256"],
        "residualizer_artifact": saved_res["artifact_path"],
        "residualizer_sha256": saved_res["artifact_sha256"],
        "seeds": seeds,
        "fit_time_ms": ensemble_fit_ms,
        "diagnostics": disagree_diagnostics,
        "metadata": common_manifest,
    }
    with open(results_dir / "ensemble_report.json", "w", encoding="utf-8") as f:
        json.dump(ensemble_report, f, indent=2)

    print("\n" + "=" * 70)
    print("Phase 3 Pipeline COMPLETED SUCCESSFULLY")
    print(f"Artifacts saved in: {artifacts_dir}")
    print(f"Reports saved in  : {results_dir}")
    print("=" * 70)

    return {
        "model_report": model_report,
        "calibration_report": calib_report,
        "ensemble_report": ensemble_report,
    }


if __name__ == "__main__":
    run_phase3_pipeline()
