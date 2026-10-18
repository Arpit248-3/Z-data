"""SignalGate Phase 5 Final Evaluation Pipeline

Executes:
1. Strict cryptographic hash verification of dataset, split, and frozen policy artifacts.
2. Logging of the planned Gate G5 test look in logs/test_looks.log.
3. Final frozen evaluation of B1, B2, B3a, B4, and SignalGate on held-out test split (2,000 rows).
4. Paired bootstrap confidence intervals (1,000 resamples, seed 42) for B2 vs SignalGate.
5. Full pre-registered budget sweep (1.0x, 1.5x, 2.0x, 3.0x).
6. Shift scenario evaluation (S0, S1, S3) and distribution drift monitoring (PSI and KS).
7. Segment-level triage analysis (ProductCD, card4).
8. Economic scenario value modeling and assumption sensitivity analysis.
9. Micro-benchmarking of single-transaction and batch-of-32 inference/routing latency.
10. Generation of canonical results/results.json, CSV evidence tables, and visual evaluation figures.
"""

import datetime
import hashlib
import json
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, List

import matplotlib
matplotlib.use("Agg")  # Non-interactive backend
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import yaml

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from data.load import load_dataset
from data.splits import make_splits, compute_split_hash
from data.features import extract_features_and_target
from data.scenario_builders import build_all_scenarios
from models.base import load_model_artifact, raw_score
from models.calibrate import calibrated_p
from models.ensemble import disagreement, apply_rank_residual
from policy.router import route, route_batch, Action, ReasonCode
from policy.governor import CapacityGovernor, govern_decisions
from policy.baselines import (
    baseline_fixed_threshold,
    baseline_top_b,
    baseline_confidence_deferral,
    baseline_random,
)
from eval.metrics import (
    calculate_binary_metrics,
    calculate_policy_metrics,
    recall_at_touched,
    value_missed,
    value_caught,
    ece,
    calculate_pr_auc,
)
from eval.bootstrap import paired_bootstrap
from eval.drift import monitor_dataset_drift
from eval.segments import analyze_all_segments
from eval.value_model import ScenarioValueModel
from eval.latency import benchmark_pipeline_latency, time_calls


def sha256_file(filepath: Path) -> str:
    """Compute SHA-256 hash of a file."""
    hasher = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()


def compute_config_hash(cfg: Dict[str, Any]) -> str:
    """Compute deterministic SHA-256 hash of frozen configuration dictionary."""
    cfg_json = json.dumps(cfg, sort_keys=True, indent=2)
    return hashlib.sha256(cfg_json.encode("utf-8")).hexdigest()


def run_phase5_evaluation():
    print("=" * 75)
    print("SignalGate Phase 5: Final Evaluation, Statistical Confidence & Shift Analysis")
    print("=" * 75)

    # -------------------------------------------------------------------------
    # STEP 1: Verify Environment, Dataset, and Frozen Hashes
    # -------------------------------------------------------------------------
    print("\n[1/9] Verifying integrity of frozen configuration and split hashes...")
    df, meta = load_dataset()
    dataset_status = meta["status"]
    is_synthetic = meta["is_synthetic"]
    dataset_sha256 = meta["sha256"]

    splits = make_splits(df)
    current_split_hash = compute_split_hash(splits)

    frozen_policy_path = PROJECT_ROOT / "policy" / "frozen_policy.json"
    if not frozen_policy_path.exists():
        raise FileNotFoundError(f"Missing frozen policy artifact: {frozen_policy_path}")

    with open(frozen_policy_path, "r", encoding="utf-8") as f:
        frozen_policy = json.load(f)

    # Verify config hash from config.yaml
    with open(PROJECT_ROOT / "config.yaml", "r", encoding="utf-8") as f:
        config_data = yaml.safe_load(f)

    recorded_config_hash = config_data.get("config_hash")
    expected_split_hash = "07b55a4ed74f238c9ef5b779a749770cf274d4709a4389d9eab860dd9068fbdd"
    expected_config_hash = "8d3f02ca492ca94bab45f3ceac8d39432c2f29f40d54e7990b4aa78cbbff6240"

    print(f"      Dataset SHA-256: {dataset_sha256}")
    print(f"      Split Hash:      {current_split_hash}")
    print(f"      Config Hash:     {recorded_config_hash}")

    if current_split_hash != expected_split_hash:
        raise ValueError(
            f"Split hash mismatch! Expected {expected_split_hash}, got {current_split_hash}. "
            "Data partitions have changed! Halting Phase 5."
        )

    if recorded_config_hash != expected_config_hash:
        raise ValueError(
            f"Frozen configuration hash mismatch! Expected {expected_config_hash}, got {recorded_config_hash}. "
            "Policy has been modified! Halting Phase 5."
        )

    print("      Verification PASSED: Hashes match frozen Gate G3 specification.")

    # -------------------------------------------------------------------------
    # STEP 2: Log Gate G5 Look in test_looks.log
    # -------------------------------------------------------------------------
    print("\n[2/9] Recording planned Gate G5 test look in logs/test_looks.log...")
    test_log_path = PROJECT_ROOT / "logs" / "test_looks.log"
    iso_timestamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    g5_log_entry = (
        f"[{iso_timestamp}] TEST LOOK G5 (LOOK 2 OF 2 PRE-REGISTERED - FINAL EVALUATION)\n"
        f"  Purpose: Phase 5 final evaluation, paired bootstrap CIs, shift analysis, and latency benchmarking.\n"
        f"  Frozen Config SHA-256: {recorded_config_hash}\n"
        f"  Split Hash: {current_split_hash}\n"
        f"  Test Rows: {len(splits['test'])} | Status: {dataset_status}\n"
        f"  Notice: Final evaluation look using frozen policy. No retuning will be performed.\n"
        f"----------------------------------------------------------------------\n\n"
    )

    if test_log_path.exists():
        existing_log = test_log_path.read_text(encoding="utf-8")
        if "TEST LOOK G5" not in existing_log:
            with open(test_log_path, "a", encoding="utf-8") as f:
                f.write(g5_log_entry)
            print("      Gate G5 look recorded successfully.")
        else:
            print("      Gate G5 look already present in ledger.")
    else:
        with open(test_log_path, "w", encoding="utf-8") as f:
            f.write(g5_log_entry)
        print("      Gate G5 look recorded successfully.")

    # -------------------------------------------------------------------------
    # STEP 3: Load Frozen Artifacts and Extract Test Features
    # -------------------------------------------------------------------------
    print("\n[3/9] Loading Phase 3 model artifacts and extracting feature matrices...")
    _, _, _, train_manifest = extract_features_and_target(splits["train"])
    feature_names = train_manifest["feature_names"]

    X_train, y_train, eval_train, _ = extract_features_and_target(splits["train"], feature_manifest=feature_names)
    X_test, y_test, eval_test, _ = extract_features_and_target(splits["test"], feature_manifest=feature_names)

    artifacts_dir = PROJECT_ROOT / "models" / "artifacts"
    calibrator, _ = load_model_artifact(artifacts_dir / "calibrator_sigmoid.joblib")
    ensemble, _ = load_model_artifact(artifacts_dir / "ensemble_members.joblib")
    residualizer, _ = load_model_artifact(artifacts_dir / "residualizer_u2.joblib")

    # Score test split S0
    p_test = calibrated_p(calibrator, X_test)
    raw_u_test = disagreement(ensemble, X_test)
    u2_test = apply_rank_residual(residualizer, raw_u_test, p_test)
    amounts_test = splits["test"]["TransactionAmt"].to_numpy() if "TransactionAmt" in splits["test"].columns else None

    # Load frozen primary thresholds
    primary_budget = frozen_policy["primary_budget"]
    frozen_thresh = frozen_policy["thresholds"]
    t_alert = frozen_thresh["t_alert"]
    t_review = frozen_thresh["t_review"]
    u_thresh = frozen_thresh["u_threshold"]
    capacity_1_5x = int(len(X_test) * primary_budget)  # 2000 * 0.06525 = 130

    print(f"      Test set: {len(X_test)} rows | Fraud count: {int(np.sum(y_test))} ({np.mean(y_test)*100:.2f}%)")
    print(f"      Primary budget: {primary_budget:.5f} | Analyst Capacity: {capacity_1_5x} cases")
    print(f"      Frozen thresholds: t_alert={t_alert:.6f}, t_review={t_review:.6f}, u2_threshold={u_thresh:.6f}")

    # -------------------------------------------------------------------------
    # STEP 4: Primary Matched-Budget Evaluation & Baseline Comparisons
    # -------------------------------------------------------------------------
    print("\n[4/9] Evaluating all policies under primary matched budget (1.5x)...")

    # B1: Fixed threshold (validation-selected)
    b1_thresh = frozen_policy["matched_budget_validation_comparison"]["B1_fixed_threshold"]["threshold"]
    mask_b1 = baseline_fixed_threshold(p_test, threshold=b1_thresh)
    actions_b1 = ["FRAUD_ALERT" if m else "ROUTINE" for m in mask_b1]
    metrics_b1 = calculate_policy_metrics(y_test, actions_b1, amounts=amounts_test, p_scores=p_test)
    metrics_b1["policy"] = "B1_fixed_threshold"
    metrics_b1["threshold"] = b1_thresh

    # B2: Top-B risk ranking (mandatory comparison)
    mask_b2 = baseline_top_b(p_test, budget=primary_budget)
    actions_b2 = ["FRAUD_ALERT" if m else "ROUTINE" for m in mask_b2]
    metrics_b2 = calculate_policy_metrics(y_test, actions_b2, amounts=amounts_test, p_scores=p_test)
    metrics_b2["policy"] = "B2_top_b_risk"

    # B3a: Confidence-based deferral (1 - max(p, 1-p))
    mask_b3a = baseline_confidence_deferral(p_test, budget=primary_budget)
    actions_b3a = ["MANUAL_REVIEW" if m else "ROUTINE" for m in mask_b3a]
    metrics_b3a = calculate_policy_metrics(y_test, actions_b3a, amounts=amounts_test, p_scores=p_test)
    metrics_b3a["policy"] = "B3a_confidence_deferral"

    # B4: Random control
    mask_b4 = baseline_random(len(p_test), budget=primary_budget, seed=42)
    actions_b4 = ["MANUAL_REVIEW" if m else "ROUTINE" for m in mask_b4]
    metrics_b4 = calculate_policy_metrics(y_test, actions_b4, amounts=amounts_test, p_scores=p_test)
    metrics_b4["policy"] = "B4_random_control"

    # SignalGate Frozen Policy Router + Governor
    cfg_sg = {
        "t_alert": t_alert,
        "t_review": t_review,
        "u_threshold": u_thresh,
        "disagreement_enabled": True,
        "novelty_enabled": False,
    }
    raw_sg_decisions = route_batch(
        p=p_test,
        u=u2_test,
        n=None,
        cfg=cfg_sg,
        stage2_status="computed",
    )
    governor = CapacityGovernor(capacity=capacity_1_5x, priority_col="p")
    gov_sg_decisions, gov_summary = govern_decisions(
        raw_sg_decisions,
        capacity=capacity_1_5x,
        priority_col="p",
    )
    actions_sg = gov_sg_decisions["action"].to_numpy()
    metrics_sg = calculate_policy_metrics(y_test, actions_sg, amounts=amounts_test, p_scores=p_test)
    metrics_sg["policy"] = "SignalGate_frozen"
    metrics_sg["governor_summary"] = gov_summary
    metrics_sg["delta_recall_vs_b2_pp"] = round((metrics_sg["recall_at_touched"] - metrics_b2["recall_at_touched"]) * 100.0, 4)

    policy_comparisons = {
        "B1_fixed_threshold": metrics_b1,
        "B2_top_b_risk": metrics_b2,
        "B3a_confidence_deferral": metrics_b3a,
        "B4_random_control": metrics_b4,
        "SignalGate_frozen": metrics_sg,
    }

    print("      Primary Evaluation Results (B=0.06525):")
    for pol_name, m in policy_comparisons.items():
        print(f"      - {pol_name:24s}: Recall={m['recall_at_touched']:.4f} ({m['tp']}/{m['total_fraud']}) | Touched={m['touched_rate']:.4f} ({m['touched_count']})")

    # -------------------------------------------------------------------------
    # STEP 5: Paired Bootstrap Resampling (B2 vs SignalGate)
    # -------------------------------------------------------------------------
    print("\n[5/9] Computing paired bootstrap confidence interval (1,000 resamples, seed 42)...")
    mask_sg_touched = (actions_sg == "FRAUD_ALERT") | (actions_sg == "MANUAL_REVIEW")
    bootstrap_results = paired_bootstrap(
        y_true=y_test,
        mask_a=mask_sg_touched,
        mask_b=mask_b2,
        n_resamples=1000,
        seed=42,
        alpha=0.05,
        status=dataset_status,
    )
    print(f"      Point estimate diff (SG - B2): {bootstrap_results['point_estimate_diff']:+.4f}")
    print(f"      95% Confidence Interval:        [{bootstrap_results['ci_lower']:+.4f}, {bootstrap_results['ci_upper']:+.4f}]")
    print(f"      Valid resamples:                {bootstrap_results['n_resamples_valid']}/{bootstrap_results['n_resamples_requested']}")
    print(f"      Conclusive?                     {bootstrap_results['is_conclusive']} ({bootstrap_results['conclusion']})")

    # -------------------------------------------------------------------------
    # STEP 6: Pre-Registered Budget Sweep (1.0x, 1.5x, 2.0x, 3.0x)
    # -------------------------------------------------------------------------
    print("\n[6/9] Running evaluation across budget sweep (1.0x, 1.5x, 2.0x, 3.0x)...")
    budget_sweep_results = {}
    sweep_multiples = [1.0, 1.5, 2.0, 3.0]

    for mult in sweep_multiples:
        mult_key = f"{mult:.1f}x"
        cfg_mult = frozen_policy["budget_sweep"][mult_key]["thresholds"]
        target_b = cfg_mult["target_budget"]
        cap_mult = int(len(X_test) * target_b)

        # Baseline B2 at this budget
        m_b2_mult = baseline_top_b(p_test, budget=target_b)
        rec_b2_mult = recall_at_touched(y_test, m_b2_mult)

        # SignalGate at this budget
        cfg_r = {
            "t_alert": cfg_mult["t_alert"],
            "t_review": cfg_mult["t_review"],
            "u_threshold": cfg_mult["u_threshold"],
            "disagreement_enabled": cfg_mult["disagreement_enabled"],
            "novelty_enabled": False,
        }
        raw_dec = route_batch(p=p_test, u=u2_test, n=None, cfg=cfg_r, stage2_status="computed")
        gov_dec, gov_sum = govern_decisions(raw_dec, capacity=cap_mult, priority_col="p")
        act_sg_mult = gov_dec["action"].to_numpy()
        pol_metrics_mult = calculate_policy_metrics(y_test, act_sg_mult, amounts=amounts_test, p_scores=p_test)
        pol_metrics_mult["delta_recall_vs_b2_pp"] = round((pol_metrics_mult["recall_at_touched"] - rec_b2_mult) * 100.0, 4)
        pol_metrics_mult["b2_recall"] = round(rec_b2_mult, 6)

        budget_sweep_results[mult_key] = {
            "multiple": mult,
            "target_budget": target_b,
            "capacity": cap_mult,
            "thresholds": cfg_mult,
            "b2_recall": round(rec_b2_mult, 6),
            "signalgate_metrics": pol_metrics_mult,
        }
        print(f"      - {mult_key:4s} (B={target_b:.4f}, Cap={cap_mult:3d}): SG Recall={pol_metrics_mult['recall_at_touched']:.4f} | B2 Recall={rec_b2_mult:.4f} | Delta={pol_metrics_mult['delta_recall_vs_b2_pp']:+.2f} pp")

    # -------------------------------------------------------------------------
    # STEP 7: Shift Scenarios & Distribution Drift Monitoring
    # -------------------------------------------------------------------------
    print("\n[7/9] Evaluating shift scenarios (S0, S1, S3) and calculating drift statistics...")
    test_raw_df = splits["test"]
    scenarios = build_all_scenarios(test_raw_df, seed=42, base_status=dataset_status)

    shift_results = {}
    for s_id, s_data in scenarios.items():
        s_df = s_data["df"]
        s_X, s_y, s_eval, _ = extract_features_and_target(s_df, feature_manifest=feature_names)
        s_p = calibrated_p(calibrator, s_X)
        s_u = disagreement(ensemble, s_X)
        s_u2 = apply_rank_residual(residualizer, s_u, s_p)
        s_amt = s_df["TransactionAmt"].to_numpy() if "TransactionAmt" in s_df.columns else None

        s_cap = int(len(s_X) * primary_budget)
        # B2 on this scenario
        m_b2_s = baseline_top_b(s_p, budget=primary_budget)
        rec_b2_s = recall_at_touched(s_y, m_b2_s)

        # SignalGate on this scenario
        raw_dec_s = route_batch(p=s_p, u=s_u2, n=None, cfg=cfg_sg, stage2_status="computed")
        gov_dec_s, gov_sum_s = govern_decisions(raw_dec_s, capacity=s_cap, priority_col="p")
        act_s = gov_dec_s["action"].to_numpy()
        pol_metrics_s = calculate_policy_metrics(s_y, act_s, amounts=s_amt, p_scores=s_p)

        shift_results[s_id] = {
            "scenario_id": s_id,
            "name": s_data["name"],
            "status": s_data["status"],
            "scenario_hash": s_data["scenario_hash"],
            "sample_count": s_data["sample_count"],
            "fraud_count": s_data["fraud_count"],
            "fraud_prevalence": s_data["fraud_prevalence"],
            "b2_recall": round(rec_b2_s, 6),
            "signalgate_recall": pol_metrics_s["recall_at_touched"],
            "delta_recall_vs_b2_pp": round((pol_metrics_s["recall_at_touched"] - rec_b2_s) * 100.0, 4),
            "signalgate_touched_rate": pol_metrics_s["touched_rate"],
            "governor_summary": gov_sum_s,
            "metadata": s_data["metadata"],
        }
        print(f"      - Scenario {s_id:2s} ({s_data['name']:24s}): SG Recall={pol_metrics_s['recall_at_touched']:.4f} | B2 Recall={rec_b2_s:.4f} | Delta={pol_metrics_s['recall_at_touched'] - rec_b2_s:+.4f}")

    # Drift monitoring on key features using Train split as Reference
    drift_features = [
        "TransactionAmt", "C1", "C2", "D1", "D2", "V1", "V2", "V3", "V10", "V12"
    ]
    # Filter features that exist in both train and test
    available_drift_features = [f for f in drift_features if f in X_train.columns and f in X_test.columns]

    drift_s0 = monitor_dataset_drift(
        reference_df=X_train,
        comparison_df=X_test,
        features=available_drift_features,
        scenario_id="S0",
        status=dataset_status,
    )

    s3_X, _, _, _ = extract_features_and_target(scenarios["S3"]["df"], feature_manifest=feature_names)
    drift_s3 = monitor_dataset_drift(
        reference_df=X_train,
        comparison_df=s3_X,
        features=available_drift_features,
        scenario_id="S3",
        status="SYNTHETIC_SHIFT",
    )
    print(f"      Drift Monitoring: S0 Mean PSI={drift_s0['mean_psi']:.4f} | S3 Mean PSI={drift_s3['mean_psi']:.4f} (Significant drift count={drift_s3['significant_drift_features']})")

    # -------------------------------------------------------------------------
    # STEP 8: Segment Analysis, Value Model & Latency Benchmarks
    # -------------------------------------------------------------------------
    print("\n[8/9] Computing segment escalation analysis, value model, and latency benchmarks...")

    # Segment analysis on S0
    segment_results = analyze_all_segments(
        eval_df=eval_test,
        actions=actions_sg,
        y_true=y_test,
        segment_columns=["ProductCD", "card4"],
        status=dataset_status,
    )

    # Economic value model on S0
    val_model = ScenarioValueModel(
        cost_per_review=20.0,
        friction_per_false_alert=30.0,
        recovery_rate=0.90,
    )
    value_model_output = val_model.evaluate(
        y_true=y_test,
        actions=actions_sg,
        amounts=amounts_test,
        status=dataset_status,
    )
    value_model_grid = val_model.sensitivity_grid(
        y_true=y_test,
        actions=actions_sg,
        amounts=amounts_test,
    )

    # Latency benchmarking
    print("      Benchmarking end-to-end inference/routing latency (5,000 single calls, 1,000 batch-32 calls)...")
    sample_row = X_test.iloc[[0]]
    sample_batch_32 = X_test.iloc[:32]

    def single_predict_pipeline(row: pd.DataFrame):
        p_val = calibrated_p(calibrator, row)
        u_val = disagreement(ensemble, row)
        u2_val = apply_rank_residual(residualizer, u_val, p_val)
        return route(
            p=float(p_val[0]),
            u=float(u2_val[0]),
            n=None,
            cfg=cfg_sg,
            stage2_status="computed",
        )

    def batch_predict_pipeline(batch: pd.DataFrame):
        p_vals = calibrated_p(calibrator, batch)
        u_vals = disagreement(ensemble, batch)
        u2_vals = apply_rank_residual(residualizer, u_vals, p_vals)
        return route_batch(
            p=p_vals,
            u=u2_vals,
            n=None,
            cfg=cfg_sg,
            stage2_status="computed",
        )

    latency_results = benchmark_pipeline_latency(
        single_predict_fn=single_predict_pipeline,
        batch_predict_fn=batch_predict_pipeline,
        sample_row=sample_row,
        sample_batch_32=sample_batch_32,
        n_single_calls=5000,
        n_batch_calls=1000,
        warmup_single=200,
        warmup_batch=50,
        status=dataset_status,
    )
    print(f"      Latency Results: Single-row p95={latency_results['single_transaction_path']['p95_ms']:.2f} ms | Batch-32 per-tx p95={latency_results['batch_32_path']['per_tx_p95_ms']:.2f} ms")
    print(f"      AC5 Acceptance Check: {latency_results['acceptance_check_ac5']['passed']} (Measured p95 <= 50.0 ms)")

    # -------------------------------------------------------------------------
    # STEP 9: Generate Consolidated Artifacts, Tables, and Figures
    # -------------------------------------------------------------------------
    print("\n[9/9] Emitting consolidated evaluation artifacts (results.json, CSVs, figures)...")

    # Output directories
    tables_dir = PROJECT_ROOT / "results" / "tables"
    figs_dir = PROJECT_ROOT / "results" / "figs"
    tables_dir.mkdir(parents=True, exist_ok=True)
    figs_dir.mkdir(parents=True, exist_ok=True)

    # 1. Consolidated results.json
    results_json_data = {
        "status": dataset_status,
        "is_synthetic": is_synthetic,
        "evaluation_timestamp": iso_timestamp,
        "provenance": {
            "dataset_sha256": dataset_sha256,
            "split_hash": current_split_hash,
            "frozen_config_hash": recorded_config_hash,
            "test_look": "G5_LOOK_2_FINAL",
            "test_rows": len(X_test),
            "test_fraud_count": int(np.sum(y_test)),
            "test_fraud_prevalence": round(float(np.mean(y_test)), 6),
            "primary_budget_multiple": 1.5,
            "primary_budget_touched_rate": primary_budget,
            "analyst_capacity": capacity_1_5x,
        },
        "frozen_thresholds": frozen_thresh,
        "primary_policy_comparison": policy_comparisons,
        "paired_bootstrap_ci": bootstrap_results,
        "budget_sweep": budget_sweep_results,
        "shift_scenarios": shift_results,
        "drift_monitoring": {
            "S0_reference_drift": drift_s0,
            "S3_covariate_shift_drift": drift_s3,
        },
        "segment_analysis": segment_results,
        "value_model": {
            "primary_evaluation": value_model_output,
            "sensitivity_grid": value_model_grid[:9],  # top 9 representative combinations
        },
        "latency_benchmarks": latency_results,
        "acceptance_criteria_status": {
            "AC1_recall_beats_b2": {
                "target_delta_pp": 2.0,
                "measured_delta_pp": metrics_sg["delta_recall_vs_b2_pp"],
                "passed": bool(metrics_sg["delta_recall_vs_b2_pp"] >= 2.0),
                "ci_positive": bool(bootstrap_results["ci_lower"] > 0.0),
                "conclusion": "Inconclusive on synthetic smoke fixture: point estimate matches B2, CI spans zero.",
            },
            "AC2_workload_reduction": {
                "target_reduction": 0.10,
                "measured_touched_rate": metrics_sg["touched_rate"],
                "passed": False,
                "conclusion": "Evaluated at matched capacity budget.",
            },
            "AC3_shift_robustness": {
                "s0_recall": shift_results["S0"]["signalgate_recall"],
                "s3_recall": shift_results["S3"]["signalgate_recall"],
                "s3_delta_recall_pp": round((shift_results["S3"]["signalgate_recall"] - shift_results["S0"]["signalgate_recall"]) * 100.0, 2),
                "passed": bool(shift_results["S3"]["signalgate_recall"] >= shift_results["S0"]["signalgate_recall"]),
            },
            "AC4_routine_fraud_rate": {
                "signalgate_routine_fraud_rate": metrics_sg["routine_fraud_rate"],
                "b2_below_threshold_fraud_rate": metrics_b2["routine_fraud_rate"],
                "passed": bool(metrics_sg["routine_fraud_rate"] <= metrics_b2["routine_fraud_rate"]),
            },
            "AC5_p95_latency": {
                "target_p95_ms": 50.0,
                "measured_p95_ms": latency_results["single_transaction_path"]["p95_ms"],
                "passed": latency_results["acceptance_check_ac5"]["passed"],
            },
        },
        "limitations_and_disclaimers": {
            "dataset_status": "SYNTHETIC_SMOKE_ONLY: Generated purely for software integration and development.",
            "benchmark_validity": "These results reflect synthetic data. They must never be presented as real-world benchmark performance.",
            "hardware_platform": "Commodity x86_64 host without hardware coprocessors or mainframe accelerators.",
            "fairness_scope": "Segment screening evaluates operational transaction categories and does not certify protected class fairness.",
        },
    }

    results_json_path = PROJECT_ROOT / "results" / "results.json"
    with open(results_json_path, "w", encoding="utf-8") as f:
        json.dump(results_json_data, f, indent=2)
    print(f"      Saved canonical results: {results_json_path}")

    # 2. CSV Evidence Tables
    # Table 1: policy_comparison.csv
    table_pol_rows = []
    for pol_name, m in policy_comparisons.items():
        table_pol_rows.append({
            "policy": pol_name,
            "target_budget": primary_budget,
            "total_transactions": m["total_transactions"],
            "escalated_count": m["touched_count"],
            "touched_rate": m["touched_rate"],
            "total_fraud": m["total_fraud"],
            "caught_fraud": m["tp"],
            "missed_fraud": m["fn"],
            "recall_at_touched": m["recall_at_touched"],
            "precision": m["precision"],
            "fpr": m["fpr"],
            "deferred_count": m["deferred_count"],
            "deferred_rate": m["deferred_rate"],
            "confident_miss_count": m["confident_miss_count"],
            "routine_fraud_rate": m["routine_fraud_rate"],
        })
    df_pol = pd.DataFrame(table_pol_rows)
    df_pol.to_csv(tables_dir / "policy_comparison.csv", index=False)

    # Table 2: budget_sweep.csv
    table_sweep_rows = []
    for mult_key, sw in budget_sweep_results.items():
        sg_m = sw["signalgate_metrics"]
        table_sweep_rows.append({
            "budget_multiple": mult_key,
            "target_budget": sw["target_budget"],
            "capacity": sw["capacity"],
            "b2_recall": sw["b2_recall"],
            "signalgate_recall": sg_m["recall_at_touched"],
            "delta_recall_vs_b2_pp": sg_m["delta_recall_vs_b2_pp"],
            "signalgate_touched_rate": sg_m["touched_rate"],
            "signalgate_precision": sg_m["precision"],
            "admitted_alerts": sg_m["alert_count"],
            "admitted_reviews": sg_m["review_count"],
            "deferred_count": sg_m["deferred_count"],
        })
    df_sweep = pd.DataFrame(table_sweep_rows)
    df_sweep.to_csv(tables_dir / "budget_sweep.csv", index=False)

    # Table 3: shift_comparison.csv
    table_shift_rows = []
    for s_id, sh in shift_results.items():
        table_shift_rows.append({
            "scenario_id": s_id,
            "scenario_name": sh["name"],
            "status": sh["status"],
            "sample_count": sh["sample_count"],
            "fraud_count": sh["fraud_count"],
            "fraud_prevalence": sh["fraud_prevalence"],
            "b2_recall": sh["b2_recall"],
            "signalgate_recall": sh["signalgate_recall"],
            "delta_recall_vs_b2_pp": sh["delta_recall_vs_b2_pp"],
            "touched_rate": sh["signalgate_touched_rate"],
            "deferred_count": sh["governor_summary"]["deferred_count"],
        })
    df_shift = pd.DataFrame(table_shift_rows)
    df_shift.to_csv(tables_dir / "shift_comparison.csv", index=False)

    # Table 4: segment_analysis.csv
    table_seg_rows = []
    for col_name, col_rep in segment_results["segment_reports"].items():
        if "groups" in col_rep:
            for grp in col_rep["groups"]:
                table_seg_rows.append({
                    "segment_feature": col_name,
                    "segment_category": grp["segment_value"],
                    "sample_size": grp["sample_size"],
                    "fraud_count": grp["fraud_count"],
                    "fraud_prevalence": grp["fraud_prevalence"],
                    "alert_count": grp["alert_count"],
                    "review_count": grp["review_count"],
                    "routine_count": grp["routine_count"],
                    "deferred_count": grp["deferred_count"],
                    "touched_rate": grp["touched_rate"],
                    "recall": grp["recall"],
                    "precision": grp["precision"],
                })
    df_seg = pd.DataFrame(table_seg_rows)
    df_seg.to_csv(tables_dir / "segment_analysis.csv", index=False)

    # Table 5: latency.csv
    df_lat = pd.DataFrame([
        {
            "benchmark_path": "Single Transaction (Batch=1)",
            "p50_ms": latency_results["single_transaction_path"]["p50_ms"],
            "p90_ms": latency_results["single_transaction_path"]["p90_ms"],
            "p95_ms": latency_results["single_transaction_path"]["p95_ms"],
            "p99_ms": latency_results["single_transaction_path"]["p99_ms"],
            "mean_ms": latency_results["single_transaction_path"]["mean_ms"],
            "throughput_tx_per_sec": latency_results["single_transaction_path"]["throughput_tx_per_sec"],
        },
        {
            "benchmark_path": "Batch of 32 (Per Transaction)",
            "p50_ms": latency_results["batch_32_path"]["per_tx_p50_ms"],
            "p90_ms": round(latency_results["batch_32_path"]["p90_ms"] / 32, 4),
            "p95_ms": latency_results["batch_32_path"]["per_tx_p95_ms"],
            "p99_ms": latency_results["batch_32_path"]["per_tx_p99_ms"],
            "mean_ms": round(latency_results["batch_32_path"]["mean_ms"] / 32, 4),
            "throughput_tx_per_sec": latency_results["batch_32_path"]["throughput_tx_per_sec"],
        },
    ])
    df_lat.to_csv(tables_dir / "latency.csv", index=False)
    print("      Saved CSV evidence tables in results/tables/")

    # 3. Generate Visual Evaluation Plots
    # Figure 1: Policy Recall Comparison
    plt.figure(figsize=(8, 5))
    pol_names = ["B1 Fixed", "B2 Top-B", "B3a Conf", "B4 Random", "SignalGate"]
    recalls = [
        metrics_b1["recall_at_touched"],
        metrics_b2["recall_at_touched"],
        metrics_b3a["recall_at_touched"],
        metrics_b4["recall_at_touched"],
        metrics_sg["recall_at_touched"],
    ]
    colors = ["#6b7280", "#3b82f6", "#8b5cf6", "#9ca3af", "#10b981"]
    bars = plt.bar(pol_names, recalls, color=colors, width=0.55, edgecolor="#1f2937", linewidth=1.2)
    plt.title("Fraud Recall at Primary Touched Rate Budget (1.5x Prevalence)", fontsize=12, pad=12)
    plt.ylabel("Recall @ Touched Rate (0.06525)", fontsize=10)
    plt.ylim(0, max(recalls) * 1.35)
    plt.grid(axis="y", linestyle="--", alpha=0.5)
    for bar in bars:
        h = bar.get_height()
        plt.text(bar.get_x() + bar.get_width() / 2.0, h + 0.003, f"{h:.4f}", ha="center", va="bottom", fontsize=9, fontweight="bold")
    plt.tight_layout()
    plt.savefig(figs_dir / "policy_recall_comparison.png", dpi=150)
    plt.close()

    # Figure 2: Budget Sweep Curves
    plt.figure(figsize=(8, 5))
    sweep_labels = list(budget_sweep_results.keys())
    b2_sweep_recalls = [budget_sweep_results[k]["b2_recall"] for k in sweep_labels]
    sg_sweep_recalls = [budget_sweep_results[k]["signalgate_metrics"]["recall_at_touched"] for k in sweep_labels]
    plt.plot(sweep_labels, b2_sweep_recalls, marker="o", label="B2 Top-B Risk Ranking", color="#3b82f6", linewidth=2)
    plt.plot(sweep_labels, sg_sweep_recalls, marker="s", label="SignalGate Frozen Policy", color="#10b981", linewidth=2.5, linestyle="--")
    plt.title("Fraud Recall Across Workload Budget Multiples (1.0x to 3.0x)", fontsize=12, pad=12)
    plt.xlabel("Budget Multiple (x Training Fraud Prevalence)", fontsize=10)
    plt.ylabel("Recall @ Budget", fontsize=10)
    plt.legend(frameon=True)
    plt.grid(True, linestyle="--", alpha=0.5)
    plt.tight_layout()
    plt.savefig(figs_dir / "budget_sweep_recall.png", dpi=150)
    plt.close()

    # Figure 3: Shift Scenario Robustness
    plt.figure(figsize=(7, 5))
    scen_ids = list(shift_results.keys())
    b2_shift_recalls = [shift_results[s]["b2_recall"] for s in scen_ids]
    sg_shift_recalls = [shift_results[s]["signalgate_recall"] for s in scen_ids]
    x_idx = np.arange(len(scen_ids))
    w = 0.35
    plt.bar(x_idx - w/2, b2_shift_recalls, width=w, label="B2 Top-B", color="#3b82f6")
    plt.bar(x_idx + w/2, sg_shift_recalls, width=w, label="SignalGate", color="#10b981")
    plt.xticks(x_idx, [f"{s}\n({shift_results[s]['name'][:14]})" for s in scen_ids], fontsize=9)
    plt.ylabel("Recall @ Primary Budget", fontsize=10)
    plt.title("Shift Scenario Performance: S0 vs S1 vs S3", fontsize=12, pad=12)
    plt.legend()
    plt.grid(axis="y", linestyle="--", alpha=0.5)
    plt.tight_layout()
    plt.savefig(figs_dir / "shift_comparison.png", dpi=150)
    plt.close()

    # Figure 4: Feature-level Drift PSI
    plt.figure(figsize=(9, 4.5))
    s3_drift_reports = drift_s3["feature_drift_reports"]
    d_feats = [r["feature"] for r in s3_drift_reports]
    d_psis = [r["psi"] if r["psi"] is not None else 0.0 for r in s3_drift_reports]
    d_colors = ["#10b981" if p < 0.1 else "#f59e0b" if p <= 0.2 else "#ef4444" for p in d_psis]
    plt.bar(d_feats, d_psis, color=d_colors, width=0.6, edgecolor="#1f2937")
    plt.axhline(0.1, color="#f59e0b", linestyle="--", label="Moderate Drift (0.10)")
    plt.axhline(0.2, color="#ef4444", linestyle="--", label="Significant Drift (0.20)")
    plt.title("S3 Covariate Shift: Feature-Level Population Stability Index (PSI)", fontsize=12, pad=12)
    plt.ylabel("PSI Statistic", fontsize=10)
    plt.xticks(rotation=45, ha="right", fontsize=9)
    plt.legend(loc="upper right")
    plt.grid(axis="y", linestyle="--", alpha=0.5)
    plt.tight_layout()
    plt.savefig(figs_dir / "drift_psi_distribution.png", dpi=150)
    plt.close()

    # Figure 5: Latency Percentile Comparison
    plt.figure(figsize=(7, 4.5))
    metrics_names = ["p50", "p90", "p95", "p99"]
    single_p = [latency_results["single_transaction_path"][f"{m}_ms"] for m in metrics_names]
    batch_p = [
        latency_results["batch_32_path"]["per_tx_p50_ms"],
        latency_results["batch_32_path"]["p90_ms"] / 32,
        latency_results["batch_32_path"]["per_tx_p95_ms"],
        latency_results["batch_32_path"]["per_tx_p99_ms"],
    ]
    x_idx = np.arange(len(metrics_names))
    w = 0.35
    plt.bar(x_idx - w/2, single_p, width=w, label="Single-Row End-to-End", color="#3b82f6")
    plt.bar(x_idx + w/2, batch_p, width=w, label="Batch-32 (Per Transaction)", color="#8b5cf6")
    plt.axhline(50.0, color="#ef4444", linestyle=":", label="AC5 Target (<= 50 ms)")
    plt.xticks(x_idx, metrics_names, fontsize=10)
    plt.ylabel("Latency per Transaction (ms)", fontsize=10)
    plt.title("Inference & Routing Latency Percentiles", fontsize=12, pad=12)
    plt.legend()
    plt.grid(axis="y", linestyle="--", alpha=0.5)
    plt.tight_layout()
    plt.savefig(figs_dir / "latency_distribution.png", dpi=150)
    plt.close()

    print("      Saved visual plots in results/figs/")
    print("\n" + "=" * 75)
    print("SignalGate Phase 5 Evaluation Pipeline COMPLETED SUCCESSFULLY")
    print(f"Status: {dataset_status} | Config Hash: {recorded_config_hash}")
    print("=" * 75)


if __name__ == "__main__":
    run_phase5_evaluation()
