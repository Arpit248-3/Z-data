"""
SignalGate Phase 4 Policy Execution Pipeline
Executes:
1. Validation-only threshold optimization across budget sweep (1.0x, 1.5x, 2.0x, 3.0x).
2. Matched-budget comparison of B1, B2, B3a, B4, and SignalGate variants on validation split.
3. Signal discipline: keep/drop evaluation of disagreement u and u2.
4. Policy configuration freezing and cryptographic hashing.
5. Recording of planned G3 test look in logs/test_looks.log.
6. Execution of the pre-registered G3 test look on test split (SYNTHETIC_SMOKE_ONLY).
7. Emission of validated JSONL audit trail records to logs/audit.jsonl.
"""

import hashlib
import json
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Tuple

import numpy as np
import pandas as pd
import yaml

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from data.load import load_dataset
from data.splits import make_splits, compute_split_hash
from data.features import extract_features_and_target
from models.base import load_model_artifact, raw_score
from models.calibrate import calibrated_p
from models.ensemble import disagreement, apply_rank_residual
from policy.router import route, route_batch, Action, ReasonCode
from policy.governor import CapacityGovernor, govern_decisions
from policy.thresholds import (
    ThresholdConfig,
    select_thresholds,
    sweep_thresholds_across_budgets,
)
from policy.baselines import (
    baseline_top_b,
    evaluate_policies_matched_budget,
)
from policy.audit import AuditLogger, AuditRecord, validate_audit_record


def compute_file_hash(filepath: Path) -> str:
    hasher = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()


def run_phase4_pipeline():
    print("=" * 70)
    print("SignalGate Phase 4: Decision Router, Baselines & Capacity Governor")
    print("=" * 70)

    # 1. Load active dataset and splits
    df, meta = load_dataset()
    splits = make_splits(df)
    dataset_status = meta["status"]
    is_synthetic = meta["is_synthetic"]
    dataset_sha256 = meta["sha256"]

    # Load split report to extract frozen training prevalence
    split_report_path = PROJECT_ROOT / "results" / "split_report.json"
    with open(split_report_path, "r", encoding="utf-8") as f:
        split_report = json.load(f)

    train_prevalence = split_report["partitions"]["train"]["fraud_prevalence"]
    split_hash = split_report["split_hash"]
    print(f"Dataset status: {dataset_status} | SHA-256: {dataset_sha256[:12]}...")
    print(f"Training Fraud Prevalence: {train_prevalence:.4f} ({train_prevalence*100:.2f}%)")
    print(f"Split Hash: {split_hash[:16]}...")

    # Primary touched-rate budget (1.5x training prevalence)
    primary_budget = round(float(train_prevalence * 1.5), 6)
    print(f"Primary Pre-Registered Budget (1.5x): {primary_budget:.6f} ({primary_budget*100:.3f}% touched rate)")

    # 2. Extract features using frozen train manifest
    _, _, _, train_manifest = extract_features_and_target(splits["train"])
    feature_names = train_manifest["feature_names"]

    X_val, y_val, eval_val, _ = extract_features_and_target(splits["val"], feature_manifest=feature_names)
    X_test, y_test, eval_test, _ = extract_features_and_target(splits["test"], feature_manifest=feature_names)

    # 3. Load Phase 3 fitted model artifacts
    artifacts_dir = PROJECT_ROOT / "models" / "artifacts"
    calibrator, cal_meta = load_model_artifact(artifacts_dir / "calibrator_sigmoid.joblib")
    ensemble, ens_meta = load_model_artifact(artifacts_dir / "ensemble_members.joblib")
    residualizer, res_meta = load_model_artifact(artifacts_dir / "residualizer_u2.joblib")

    # 4. Predict signals on validation partition
    print("\n[1/5] Scoring validation split and computing signals...")
    t0 = time.perf_counter()
    p_val = calibrated_p(calibrator, X_val)
    u_val = disagreement(ensemble, X_val)
    u2_val = apply_rank_residual(residualizer, u_val, p_val)
    score_latency_ms = round((time.perf_counter() - t0) * 1000 / len(X_val), 3)
    print(f"      Validation samples scored: {len(X_val)} | Latency per sample: {score_latency_ms} ms")

    # 5. Validation-only threshold selection & budget sweep
    print("\n[2/5] Running validation-only threshold optimization across budget sweep...")
    budget_multiples = [1.0, 1.5, 2.0, 3.0]
    sweep_results = sweep_thresholds_across_budgets(
        p_val=p_val,
        y_val=y_val,
        training_prevalence=train_prevalence,
        budget_multiples=budget_multiples,
        u_val=u2_val,
        use_disagreement=True,
        disagreement_variant="u2_rank_residual",
    )

    for k, res in sweep_results.items():
        if res["feasible"]:
            th = res["thresholds"]
            m = th["validation_metrics"]
            print(f"      - Budget {k} ({res['target_budget']:.4f}): t_alert={th['t_alert']:.4f}, t_review={th['t_review']:.4f}, recall={m['recall']:.4f}, touched={m['touched_rate']:.4f}")

    # 6. Signal Discipline: Compare Risk-Only vs Raw U vs U2 at primary budget (1.5x)
    print("\n[3/5] Evaluating signal discipline (keep/drop) at primary budget (1.5x)...")
    cfg_risk, _ = select_thresholds(p_val, y_val, target_budget=primary_budget, use_disagreement=False)
    cfg_u, _ = select_thresholds(p_val, y_val, target_budget=primary_budget, u_val=u_val, use_disagreement=True, disagreement_variant="raw_u")
    cfg_u2, _ = select_thresholds(p_val, y_val, target_budget=primary_budget, u_val=u2_val, use_disagreement=True, disagreement_variant="u2_rank_residual")

    comp_risk = evaluate_policies_matched_budget(p_val, y_val, budget=primary_budget, threshold_cfg=cfg_risk.to_dict())
    comp_u = evaluate_policies_matched_budget(p_val, y_val, budget=primary_budget, u=u_val, threshold_cfg=cfg_u.to_dict())
    comp_u2 = evaluate_policies_matched_budget(p_val, y_val, budget=primary_budget, u=u2_val, threshold_cfg=cfg_u2.to_dict())

    b2_recall = comp_risk["B2_top_b_risk"]["recall_at_touched"]
    risk_recall = comp_risk["SignalGate_candidate"]["recall_at_touched"]
    u_recall = comp_u["SignalGate_candidate"]["recall_at_touched"]
    u2_recall = comp_u2["SignalGate_candidate"]["recall_at_touched"]

    print(f"      B2 Top-B Baseline Recall       : {b2_recall:.4f}")
    print(f"      B1 Fixed-Threshold Recall      : {comp_risk['B1_fixed_threshold']['recall_at_touched']:.4f}")
    print(f"      B3a Confidence Deferral Recall : {comp_risk['B3a_confidence_deferral']['recall_at_touched']:.4f}")
    print(f"      B4 Random Control Recall       : {comp_risk['B4_random_control']['recall_at_touched']:.4f}")
    print(f"      SignalGate (Risk Only) Recall  : {risk_recall:.4f}")
    print(f"      SignalGate + Raw u Recall      : {u_recall:.4f}")
    print(f"      SignalGate + u2 Residual Recall: {u2_recall:.4f}")

    # Keep/drop rule: u2 improves recall over risk-only baseline
    chosen_cfg = cfg_u2 if u2_recall >= risk_recall else cfg_risk
    print(f"      Chosen Policy Configuration    : {'SignalGate + u2' if chosen_cfg == cfg_u2 else 'SignalGate (Risk Only)'}")

    # 7. Freeze Policy Configuration
    print("\n[4/5] Freezing policy configuration and computing cryptographic hash...")
    policy_dir = PROJECT_ROOT / "policy"
    frozen_policy_path = policy_dir / "frozen_policy.json"

    frozen_dict = {
        "status": dataset_status,
        "is_synthetic": is_synthetic,
        "primary_budget": primary_budget,
        "training_prevalence": train_prevalence,
        "thresholds": chosen_cfg.to_dict(),
        "budget_sweep": sweep_results,
        "matched_budget_validation_comparison": {
            "B1_fixed_threshold": comp_risk["B1_fixed_threshold"],
            "B2_top_b_risk": comp_risk["B2_top_b_risk"],
            "B3a_confidence_deferral": comp_risk["B3a_confidence_deferral"],
            "B4_random_control": comp_risk["B4_random_control"],
            "SignalGate_risk_only": comp_risk["SignalGate_candidate"],
            "SignalGate_raw_u": comp_u["SignalGate_candidate"],
            "SignalGate_u2": comp_u2["SignalGate_candidate"],
        },
        "frozen_timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }

    with open(frozen_policy_path, "w", encoding="utf-8") as f:
        json.dump(frozen_dict, f, indent=2)

    cfg_hash = compute_file_hash(frozen_policy_path)
    print(f"      Frozen Configuration Path: {frozen_policy_path}")
    print(f"      Frozen Configuration Hash: {cfg_hash}")

    # Update config.yaml with frozen thresholds and hash
    config_yaml_path = PROJECT_ROOT / "config.yaml"
    with open(config_yaml_path, "r", encoding="utf-8") as f:
        cfg_yaml = yaml.safe_load(f)

    cfg_yaml["thresholds"] = chosen_cfg.to_dict()
    cfg_yaml["config_hash"] = cfg_hash
    cfg_yaml["phase"] = "PHASE_4_POLICY_ROUTER"

    with open(config_yaml_path, "w", encoding="utf-8") as f:
        yaml.dump(cfg_yaml, f, sort_keys=False)

    # Save comprehensive policy report
    results_dir = PROJECT_ROOT / "results"
    with open(results_dir / "policy_report.json", "w", encoding="utf-8") as f:
        json.dump(frozen_dict, f, indent=2)

    # =========================================================================
    # Step 8: Pre-registered G3 Test Look Execution (Strictly Non-Iterative)
    # =========================================================================
    print("\n[5/5] Executing pre-registered G3 test look on test split...")
    logs_dir = PROJECT_ROOT / "logs"
    test_looks_log_path = logs_dir / "test_looks.log"

    look_entry = (
        f"[{time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}] TEST LOOK G3 (LOOK 1 OF 2 PRE-REGISTERED)\n"
        f"  Purpose: Blueprint Gate G3 frozen policy validation check on held-out test split.\n"
        f"  Frozen Config SHA-256: {cfg_hash}\n"
        f"  Split Hash: {split_hash}\n"
        f"  Test Rows: {len(X_test)} | Primary Budget: {primary_budget} ({primary_budget*100:.3f}%)\n"
        f"  Dataset Status: {dataset_status}\n"
        f"  Notice: Strictly non-iterative test look; no thresholds or model features will be tuned in response.\n"
        f"{'-'*70}\n"
    )

    with open(test_looks_log_path, "a", encoding="utf-8") as f:
        f.write(look_entry)

    # Score test split (strictly for offline G3 evaluation)
    p_test = calibrated_p(calibrator, X_test)
    u_test = disagreement(ensemble, X_test)
    u2_test = apply_rank_residual(residualizer, u_test, p_test)

    # Evaluate B2 and SignalGate on identical test rows at matched budget
    g3_comparison = evaluate_policies_matched_budget(
        p=p_test,
        y_true=y_test,
        budget=primary_budget,
        threshold_cfg=chosen_cfg.to_dict(),
        u=u2_test if chosen_cfg.disagreement_enabled else None,
        seed=11,
    )

    g3_report = {
        "status": dataset_status,
        "is_synthetic": is_synthetic,
        "test_look": "G3_LOOK_1",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "frozen_config_hash": cfg_hash,
        "split_hash": split_hash,
        "primary_budget": primary_budget,
        "test_rows": len(X_test),
        "test_fraud_count": int(np.sum(y_test)),
        "comparison_on_identical_test_rows": g3_comparison,
        "notice": (
            "SYNTHETIC_SMOKE_ONLY: These test look metrics reflect synthetic development fixture data. "
            "They must never be cited or presented as real-world benchmark performance."
        ),
    }

    with open(results_dir / "g3_test_look.json", "w", encoding="utf-8") as f:
        json.dump(g3_report, f, indent=2)

    print(f"      Test B2 Recall      : {g3_comparison['B2_top_b_risk']['recall_at_touched']:.4f}")
    print(f"      Test SignalGate Recall: {g3_comparison['SignalGate_candidate']['recall_at_touched']:.4f}")
    print(f"      Delta vs B2 (pp)    : {g3_comparison['SignalGate_candidate']['delta_recall_vs_B2_pp']:+.2f} pp")

    # =========================================================================
    # Step 9: Emit Validated JSONL Audit Records
    # =========================================================================
    print("\n[+] Emitting validated JSONL decision audit records...")
    audit_logger = AuditLogger(logs_dir / "audit.jsonl")

    # Generate audit records for a sample of 100 validation rows
    routed_sample = route_batch(P=p_val[:100], U=u2_val[:100], cfg=chosen_cfg.to_dict())
    k_cap = int(np.floor(100 * primary_budget))
    governed_sample, _ = govern_decisions(routed_sample, capacity=max(1, k_cap), priority_col="p")

    audit_records = []
    for i in range(len(governed_sample)):
        row = governed_sample.iloc[i]
        trans_id = str(eval_val.iloc[i]["TransactionID"])
        trans_dt = int(eval_val.iloc[i]["TransactionDT"])

        rec = AuditRecord(
            id=trans_id,
            ts=trans_dt,
            p=round(float(row["p"]), 6) if pd.notna(row["p"]) else None,
            u=round(float(row["u"]), 6) if pd.notna(row["u"]) else None,
            u_method="u2_rank_residual" if chosen_cfg.disagreement_enabled else None,
            n=None,
            stage2_status="computed",
            action=str(row["action"]),
            reason=str(row["reason"]),
            latency_ms=score_latency_ms,
            explanation_status="not_computed",
            feature_attributions=None,
            cfg_hash=cfg_hash,
            split_hash=split_hash,
            lane_rank=int(row["lane_rank"]) if pd.notna(row["lane_rank"]) else None,
            governor_status=str(row["governor_status"]),
            synthetic_scenario=True,
        )
        audit_records.append(rec)

    audit_logger.log_batch(audit_records)
    print(f"      Logged {len(audit_records)} validated audit records to: {logs_dir / 'audit.jsonl'}")

    print("\n" + "=" * 70)
    print("SignalGate Phase 4 COMPLETED SUCCESSFULLY")
    print(f"Frozen Config Hash : {cfg_hash}")
    print(f"Reports Generated  : results/policy_report.json, results/g3_test_look.json")
    print(f"Audit Trail        : logs/audit.jsonl")
    print(f"Test Looks Log     : logs/test_looks.log")
    print("=" * 70)


if __name__ == "__main__":
    run_phase4_pipeline()
