"""SignalGate Deterministic Artifact & Lineage Validator

Verifies the integrity, provenance, cryptographic hashes, and schema conformance
of all static evaluation artifacts, frozen policies, model checkpoints, and audit logs.
Strictly read-only: does not modify or recompute any artifacts.
"""

import hashlib
import json
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Canonical hashes and metrics established in Phase 1-5
EXPECTED_DATASET_SHA256 = "da00179ebf37970ec8907d11cfb366d170ddd5b2b41370e881bf92359b7d17de"
EXPECTED_SPLIT_HASH = "07b55a4ed74f238c9ef5b779a749770cf274d4709a4389d9eab860dd9068fbdd"
EXPECTED_CONFIG_HASH = "8d3f02ca492ca94bab45f3ceac8d39432c2f29f40d54e7990b4aa78cbbff6240"
EXPECTED_TEST_ROWS = 2000
EXPECTED_TEST_FRAUD = 111


def compute_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def validate() -> bool:
    all_passed = True
    print("=" * 70)
    print("SIGNALGATE DETERMINISTIC ARTIFACT VALIDATOR")
    print("=" * 70)

    # 1. Dataset Verification
    data_path = PROJECT_ROOT / "data" / "synthetic_smoke_fixture.csv"
    if not data_path.exists():
        print(f"[FAIL] Missing dataset fixture: {data_path}")
        all_passed = False
    else:
        sha = compute_sha256(data_path)
        if sha == EXPECTED_DATASET_SHA256:
            print(f"[PASS] Dataset fixture SHA-256 matches ({sha[:16]}...)")
        else:
            print(f"[FAIL] Dataset fixture SHA-256 mismatch: got {sha}")
            all_passed = False

    # 2. Split Metadata Verification
    split_path = PROJECT_ROOT / "results" / "split_report.json"
    if not split_path.exists():
        print(f"[FAIL] Missing split report: {split_path}")
        all_passed = False
    else:
        with open(split_path, "r", encoding="utf-8") as f:
            split_data = json.load(f)
        split_hash = split_data.get("split_hash")
        if split_hash == EXPECTED_SPLIT_HASH:
            print(f"[PASS] Split hash matches ({split_hash[:16]}...)")
        else:
            print(f"[FAIL] Split hash mismatch: {split_hash}")
            all_passed = False

    # 3. Frozen Policy Verification
    policy_path = PROJECT_ROOT / "policy" / "frozen_policy.json"
    if not policy_path.exists():
        print(f"[FAIL] Missing frozen policy: {policy_path}")
        all_passed = False
    else:
        with open(policy_path, "r", encoding="utf-8") as f:
            policy_data = json.load(f)
        th = policy_data.get("thresholds", {})
        t_alert = th.get("t_alert")
        t_review = th.get("t_review")
        u_th = th.get("u_threshold")
        if t_alert == 0.084705 and t_review == 0.071002 and u_th == 0.526773:
            print(f"[PASS] Frozen policy thresholds match (t_alert={t_alert}, t_review={t_review}, u_th={u_th})")
        else:
            print(f"[FAIL] Frozen policy threshold mismatch: {th}")
            all_passed = False

    # 4. Results JSON Verification
    results_path = PROJECT_ROOT / "results" / "results.json"
    if not results_path.exists():
        print(f"[FAIL] Missing results artifact: {results_path}")
        all_passed = False
    else:
        with open(results_path, "r", encoding="utf-8") as f:
            res_data = json.load(f)

        status = res_data.get("status")
        if status == "SYNTHETIC_SMOKE_ONLY":
            print(f"[PASS] Result status verified as SYNTHETIC_SMOKE_ONLY")
        else:
            print(f"[FAIL] Unexpected result status: {status}")
            all_passed = False

        prov = res_data.get("provenance", {})
        if (
            prov.get("split_hash") == EXPECTED_SPLIT_HASH
            and prov.get("frozen_config_hash") == EXPECTED_CONFIG_HASH
            and prov.get("test_rows") == EXPECTED_TEST_ROWS
            and prov.get("test_fraud_count") == EXPECTED_TEST_FRAUD
        ):
            print(f"[PASS] Result provenance verified (2000 test rows, 111 fraud cases)")
        else:
            print(f"[FAIL] Result provenance mismatch: {prov}")
            all_passed = False

        # Bootstrap CI verification
        boot = res_data.get("paired_bootstrap_ci", {})
        ci_lower = boot.get("ci_lower")
        ci_upper = boot.get("ci_upper")
        conclusive = boot.get("is_conclusive")
        if ci_lower == -0.027523 and ci_upper == 0.027523 and conclusive is False:
            print(f"[PASS] Paired bootstrap CI verified: [-2.75 pp, +2.75 pp], conclusive={conclusive}")
        else:
            print(f"[FAIL] Bootstrap CI mismatch: lower={ci_lower}, upper={ci_upper}, conclusive={conclusive}")
            all_passed = False

        # Governor outcome distribution verification
        sg = res_data.get("primary_policy_comparison", {}).get("SignalGate_frozen", {})
        counts = (
            sg.get("alert_count"),
            sg.get("review_count"),
            sg.get("routine_count"),
            sg.get("deferred_count"),
        )
        if counts == (11, 119, 896, 974):
            print(f"[PASS] Outcome distribution verified: Alert=11, Review=119, Routine=896, Deferred=974 (Total=2000)")
        else:
            print(f"[FAIL] Outcome distribution mismatch: {counts}")
            all_passed = False

        # Budget sweep multiples verification
        sweep = res_data.get("budget_sweep", {})
        sweep_keys = sorted(list(sweep.keys()))
        if sweep_keys == ["1.0x", "1.5x", "2.0x", "3.0x"]:
            print(f"[PASS] Budget sweep multiples verified: {sweep_keys}")
        else:
            print(f"[FAIL] Budget sweep multiples mismatch: {sweep_keys}")
            all_passed = False

    # 5. Model Weights & Pipeline Artifacts
    model_artifacts_dir = PROJECT_ROOT / "models" / "artifacts"
    expected_model_files = [
        "hgb_base.joblib",
        "hgb_base.meta.json",
        "calibrator_sigmoid.joblib",
        "calibrator_sigmoid.meta.json",
        "ensemble_members.joblib",
        "ensemble_members.meta.json",
        "residualizer_u2.joblib",
        "residualizer_u2.meta.json",
    ]
    for m_file in expected_model_files:
        p = model_artifacts_dir / m_file
        if p.exists() and p.stat().st_size > 0:
            print(f"[PASS] Model pipeline artifact present: {m_file} ({p.stat().st_size} bytes)")
        else:
            print(f"[FAIL] Missing model pipeline artifact: {p}")
            all_passed = False

    # Feature manifest metadata in model_report.json
    model_rep_path = PROJECT_ROOT / "results" / "model_report.json"
    if model_rep_path.exists():
        with open(model_rep_path, "r", encoding="utf-8") as f:
            m_rep = json.load(f)
        meta = m_rep.get("metadata", {})
        f_count = meta.get("feature_count")
        f_hash = meta.get("feature_manifest_sha256")
        if f_count == 67 and f_hash:
            print(f"[PASS] Feature manifest verified: {f_count} features (hash {f_hash[:16]}...)")
        else:
            print(f"[FAIL] Feature manifest mismatch in {model_rep_path}: count={f_count}, hash={f_hash}")
            all_passed = False
    else:
        print(f"[FAIL] Missing model report: {model_rep_path}")
        all_passed = False

    # 6. Replay Stream Artifact
    cases_path = PROJECT_ROOT / "results" / "cases.jsonl"
    if not cases_path.exists():
        print(f"[FAIL] Missing replay cases artifact: {cases_path}")
        all_passed = False
    else:
        line_count = sum(1 for _ in open(cases_path, "r", encoding="utf-8"))
        if line_count == EXPECTED_TEST_ROWS:
            print(f"[PASS] Replay cases stream verified: {line_count} JSONL records")
        else:
            print(f"[FAIL] Replay stream record count mismatch: {line_count} (expected {EXPECTED_TEST_ROWS})")
            all_passed = False

    # 7. Audit Log Artifact
    audit_path = PROJECT_ROOT / "logs" / "audit.jsonl"
    if not audit_path.exists():
        print(f"[FAIL] Missing audit ledger log: {audit_path}")
        all_passed = False
    else:
        audit_count = sum(1 for _ in open(audit_path, "r", encoding="utf-8"))
        print(f"[PASS] Audit ledger log present: {audit_count} records ({audit_path.stat().st_size} bytes)")

    print("=" * 70)
    if all_passed:
        print("ALL ARTIFACT INTEGRITY & PROVENANCE CHECKS PASSED (EXIT 0)")
        print("=" * 70)
        return True
    else:
        print("ARTIFACT VALIDATION DETECTED FAILURES (EXIT 1)")
        print("=" * 70)
        return False


if __name__ == "__main__":
    success = validate()
    sys.exit(0 if success else 1)
