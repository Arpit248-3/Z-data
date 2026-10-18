"""Generate Row-Level Replay and Case Artifacts for SignalGate Backend

Generates:
- results/replay_rows.jsonl: chronological test partition rows with frozen model signals,
  operational decisions, governor states, and offline true labels.
- results/cases.jsonl: case details with full feature metadata for the case explorer.
"""

import json
from pathlib import Path
import numpy as np
import pandas as pd

import sys
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from data.load import load_dataset
from data.splits import make_splits
from data.features import extract_features_and_target
from models.base import load_model_artifact
from models.calibrate import calibrated_p
from models.ensemble import disagreement, apply_rank_residual
from policy.router import route_batch
from policy.governor import govern_decisions


def generate_replay_artifacts():
    print("Generating row-level replay and case artifacts from test partition...")
    df, meta = load_dataset()
    splits = make_splits(df)
    test_df = splits["test"]

    # Extract features using frozen train manifest
    _, _, _, train_manifest = extract_features_and_target(splits["train"])
    feature_names = train_manifest["feature_names"]
    X_test, y_test, eval_test, _ = extract_features_and_target(test_df, feature_manifest=feature_names)

    # Load frozen model artifacts
    artifacts_dir = PROJECT_ROOT / "models" / "artifacts"
    calibrator, _ = load_model_artifact(artifacts_dir / "calibrator_sigmoid.joblib")
    ensemble, _ = load_model_artifact(artifacts_dir / "ensemble_members.joblib")
    residualizer, _ = load_model_artifact(artifacts_dir / "residualizer_u2.joblib")

    # Load frozen policy
    with open(PROJECT_ROOT / "policy" / "frozen_policy.json", "r", encoding="utf-8") as f:
        frozen_policy = json.load(f)

    cfg = frozen_policy["thresholds"]
    primary_budget = frozen_policy["primary_budget"]
    capacity = int(len(X_test) * primary_budget)  # 130

    # Model inference
    p_test = calibrated_p(calibrator, X_test)
    raw_u = disagreement(ensemble, X_test)
    u2_test = apply_rank_residual(residualizer, raw_u, p_test)

    # Route & govern
    raw_decisions = route_batch(P=p_test, U=u2_test, cfg=cfg, stage2_status="computed")
    gov_decisions, _ = govern_decisions(raw_decisions, capacity=capacity, priority_col="p")

    results_dir = PROJECT_ROOT / "results"
    results_dir.mkdir(parents=True, exist_ok=True)

    replay_rows_path = results_dir / "replay_rows.jsonl"
    cases_path = results_dir / "cases.jsonl"

    from data.scenario_builders import build_all_scenarios
    scenarios = build_all_scenarios(test_df, seed=42, base_status="SYNTHETIC_SMOKE_ONLY")

    replay_records = []
    case_records = []

    for s_id, s_data in scenarios.items():
        s_df = s_data["df"]
        s_status = s_data["status"]
        s_X, s_y, s_eval, _ = extract_features_and_target(s_df, feature_manifest=feature_names)

        s_p = calibrated_p(calibrator, s_X)
        s_raw_u = disagreement(ensemble, s_X)
        s_u2 = apply_rank_residual(residualizer, s_raw_u, s_p)
        s_raw_decisions = route_batch(P=s_p, U=s_u2, cfg=cfg, stage2_status="computed")
        s_capacity = int(len(s_X) * primary_budget)
        s_gov_decisions, _ = govern_decisions(s_raw_decisions, capacity=s_capacity, priority_col="p")

        for i in range(len(s_df)):
            tx_id = str(s_eval["TransactionID"].iloc[i]) if "TransactionID" in s_eval.columns else f"tx_{s_id}_{i:04d}"
            tx_dt = int(s_eval["TransactionDT"].iloc[i]) if "TransactionDT" in s_eval.columns else 0
            tx_amt = float(s_df["TransactionAmt"].iloc[i]) if "TransactionAmt" in s_df.columns else 0.0
            product_cd = str(s_eval["ProductCD"].iloc[i]) if "ProductCD" in s_eval.columns else "W"
            card4 = str(s_eval["card4"].iloc[i]) if "card4" in s_eval.columns else "visa"
            true_lbl = int(s_y.iloc[i]) if s_y is not None else 0

            p_val = float(s_p[i])
            u_val = float(s_u2[i])
            action = str(s_gov_decisions["action"].iloc[i])
            reason = str(s_gov_decisions["reason"].iloc[i])
            gov_status = str(s_gov_decisions["governor_status"].iloc[i])
            lane_rank = int(s_gov_decisions["lane_rank"].iloc[i]) if pd.notna(s_gov_decisions["lane_rank"].iloc[i]) else None

            replay_rec = {
                "row_id": len(replay_records) + 1,
                "case_id": tx_id,
                "timestamp": tx_dt,
                "transaction_id": tx_id,
                "amount": round(tx_amt, 2),
                "product_cd": product_cd,
                "card4": card4,
                "p": round(p_val, 6),
                "u": round(u_val, 6),
                "u_method": "u2_rank_residual",
                "action": action,
                "reason_code": reason,
                "governor_status": gov_status,
                "lane_rank": lane_rank,
                "scenario_id": s_id,
                "status": s_status,
                "offline_ground_truth": {
                    "is_fraud": true_lbl,
                    "label_type": "offline_held_out_evaluation_only",
                    "notice": "Never used as an input to live scoring or router policy.",
                },
            }
            replay_records.append(replay_rec)

            # Generate cases.jsonl strictly for the primary S0 evaluation test look (2,000 records)
            if s_id == "S0":
                feature_dict = {
                    "TransactionAmt": round(tx_amt, 2),
                    "ProductCD": product_cd,
                    "card4": card4,
                }
                for f_name in ["C1", "C2", "D1", "D2", "V1", "V2", "V3"]:
                    if f_name in s_X.columns:
                        val = s_X[f_name].iloc[i]
                        feature_dict[f_name] = round(float(val), 4) if pd.notna(val) else None

                case_rec = {
                    "case_id": tx_id,
                    "timestamp": tx_dt,
                    "amount": round(tx_amt, 2),
                    "scenario_id": "S0",
                    "status": "SYNTHETIC_SMOKE_ONLY",
                    "signals": {
                        "p": round(p_val, 6),
                        "u": round(u_val, 6),
                        "u_method": "u2_rank_residual",
                        "novelty": None,
                        "novelty_status": "disabled",
                    },
                    "decision": {
                        "action": action,
                        "reason_code": reason,
                        "stage2_status": "computed",
                        "governor_status": gov_status,
                        "lane_rank": lane_rank,
                        "policy_version": "v2.1",
                        "config_hash": "8d3f02ca492ca94bab45f3ceac8d39432c2f29f40d54e7990b4aa78cbbff6240",
                    },
                    "features": feature_dict,
                    "offline_evaluation": {
                        "is_fraud": true_lbl,
                        "disclaimer": "Offline labelled replay evidence; not an input to live scoring.",
                    },
                    "explanations": {
                        "status": "disabled",
                        "attributions": None,
                    },
                }
                case_records.append(case_rec)

    with open(replay_rows_path, "w", encoding="utf-8") as f:
        for r in replay_records:
            f.write(json.dumps(r) + "\n")

    with open(cases_path, "w", encoding="utf-8") as f:
        for c in case_records:
            f.write(json.dumps(c) + "\n")

    print(f"Generated {len(replay_records)} replay records -> {replay_rows_path}")
    print(f"Generated {len(case_records)} case records -> {cases_path}")


if __name__ == "__main__":
    generate_replay_artifacts()
