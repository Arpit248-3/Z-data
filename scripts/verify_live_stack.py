"""SignalGate Live Stack & Real-Data Integration Verification Script

Executes live HTTP verification against:
- FastAPI running on http://127.0.0.1:8000
- Vite Frontend running on http://127.0.0.1:5173
- Real data sample scoring from data/raw/test_transaction.csv
- Mode disclosure, leakage rejection, and cryptographic audit-chain integrity.
"""

import json
import math
import sys
import urllib.error
import urllib.request
import pandas as pd
from pathlib import Path

BACKEND_BASE = "http://127.0.0.1:8000"
FRONTEND_BASE = "http://127.0.0.1:5173"
PROJECT_ROOT = Path(__file__).resolve().parent.parent

def http_get(url: str):
    req = urllib.request.Request(url, headers={"User-Agent": "SignalGate-Verifier/1.0"})
    with urllib.request.urlopen(req, timeout=10) as resp:
        body = resp.read().decode("utf-8")
        return resp.status, json.loads(body) if "application/json" in resp.headers.get("Content-Type", "") else body

def http_post_json(url: str, payload: dict):
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json", "User-Agent": "SignalGate-Verifier/1.0"},
        method="POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            body = resp.read().decode("utf-8")
            return resp.status, json.loads(body)
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8")
        try:
            parsed = json.loads(body)
        except Exception:
            parsed = body
        return e.code, parsed

def run_tests():
    print("=" * 70)
    print("SIGNALGATE LIVE STACK & REAL-DATA OPERATIONAL READINESS GATE")
    print("=" * 70)
    results = {}

    # 1. Health Endpoint
    print("\n[1] Checking GET /api/health ...")
    status_code, health = http_get(f"{BACKEND_BASE}/api/health")
    assert status_code == 200, f"Expected 200, got {status_code}"
    assert health["status"] == "HEALTHY", f"Unhealthy status: {health}"
    print(f"    -> Status 200 OK: Service={health['service_name']} Version={health['version']} Status={health['status']}")
    results["health"] = health

    # 2. Operating Modes Endpoint
    print("\n[2] Checking GET /api/mode ...")
    status_code, mode_resp = http_get(f"{BACKEND_BASE}/api/mode")
    assert status_code == 200
    print(f"    -> Active Mode: {mode_resp['active_mode']}")
    print(f"    -> Available Modes: {mode_resp['available_modes']}")
    for k, v in mode_resp.get("modes_detail", {}).items():
        notice_text = str(v.get('notice') or '')[:60]
        print(f"       [{k}] ready={v.get('ready')} status={v.get('status')} notice={notice_text}...")
    results["mode"] = mode_resp

    # 3. System Status Endpoint (all modes)
    print("\n[3] Checking GET /api/status for explicit modes ...")
    # 3a. Synthetic
    _, status_synth = http_get(f"{BACKEND_BASE}/api/status?mode=SYNTHETIC_SMOKE_ONLY")
    print(f"    -> Mode SYNTHETIC_SMOKE_ONLY: evidence_status={status_synth.get('evidence_status')}")
    # 3b. IEEE_CIS_OFFLINE_BENCHMARK
    _, status_ieee = http_get(f"{BACKEND_BASE}/api/status?mode=IEEE_CIS_OFFLINE_BENCHMARK")
    ieee_bundle_ready = status_ieee.get("dependencies", {}).get("ieee_cis_bundle", {}).get("ready", False)
    print(f"    -> Mode IEEE_CIS_OFFLINE_BENCHMARK: overall_status={status_ieee.get('overall_status')} ieee_cis_bundle_ready={ieee_bundle_ready}")
    assert ieee_bundle_ready is True, "IEEE-CIS bundle should report ready=True on this machine!"
    results["status_ieee"] = status_ieee

    # 4. Model Card Metadata
    print("\n[4] Checking GET /api/model/card?mode=IEEE_CIS_OFFLINE_BENCHMARK ...")
    status_code, model_card = http_get(f"{BACKEND_BASE}/api/model/card?mode=IEEE_CIS_OFFLINE_BENCHMARK")
    assert status_code == 200
    print(f"    -> Architecture: {model_card.get('architecture_type')}")
    print(f"    -> Ensemble Members / Submodels: {model_card.get('sub_models')}")
    print(f"    -> Feature Count: {model_card.get('feature_count')}")
    print(f"    -> Calibrator: {model_card.get('calibrator_type')}")
    print(f"    -> Manifest Hash: {model_card.get('manifest_hash')}")
    assert model_card.get("feature_count") == 391, f"Expected 391 features, got {model_card.get('feature_count')}"
    results["model_card"] = model_card

    # 5. Drift Report
    print("\n[5] Checking GET /api/drift/report?mode=IEEE_CIS_OFFLINE_BENCHMARK ...")
    status_code, drift_resp = http_get(f"{BACKEND_BASE}/api/drift/report?mode=IEEE_CIS_OFFLINE_BENCHMARK")
    assert status_code == 200
    print(f"    -> Drift Status: {drift_resp.get('status')}")
    print(f"    -> Monitored Features: {drift_resp.get('features_monitored')}")
    print(f"    -> Mean PSI: {drift_resp.get('mean_psi')} | Max PSI: {drift_resp.get('max_psi')}")
    print(f"    -> Significant Drift Features: {drift_resp.get('significant_drift_features')}")
    results["drift"] = drift_resp

    # 6. Audit Chain Integrity Verification (Initial)
    print("\n[6] Checking GET /api/audit/verify ...")
    status_code, audit_resp = http_get(f"{BACKEND_BASE}/api/audit/verify")
    assert status_code == 200
    print(f"    -> Chain Valid: {audit_resp.get('is_valid')} Total Records: {audit_resp.get('record_count')}")
    assert audit_resp.get("is_valid") is True, f"Audit chain invalid: {audit_resp}"
    results["initial_audit"] = audit_resp

    # 7. Synthetic Mode Scoring
    print("\n[7] Scoring via Synthetic Mode (POST /api/score-sandbox?mode=SYNTHETIC_SMOKE_ONLY) ...")
    synth_payload = {
        "mode": "SYNTHETIC_SMOKE_ONLY",
        "features": {
            "TransactionAmt": 150.00,
            "ProductCD": "W",
            "card1": 13926,
            "card4": "discover",
            "C1": 1.0,
            "C2": 1.0,
            "D1": 14.0
        }
    }
    status_code, synth_score = http_post_json(f"{BACKEND_BASE}/api/score-sandbox", synth_payload)
    assert status_code == 200, f"Synthetic scoring failed with {status_code}: {synth_score}"
    print(f"    -> Decision ID: {synth_score['decision_id']}")
    print(f"    -> Signals: p={synth_score['signals']['p']} u={synth_score['signals']['u']}")
    print(f"    -> Decision: action={synth_score['decision']['action']} reason={synth_score['decision']['reason_code']}")
    print(f"    -> Latency: {synth_score['latency_ms']} ms")
    results["synth_score"] = synth_score

    # 8. Real IEEE-CIS Data Sampling & Offline Inference
    print("\n[8] Sampling Real Unlabeled Rows from data/raw/test_transaction.csv ...")
    test_csv_path = PROJECT_ROOT / "data" / "raw" / "test_transaction.csv"
    assert test_csv_path.exists(), f"Raw test CSV not found at {test_csv_path}"

    # Read top 5 rows
    df_sample = pd.read_csv(test_csv_path, nrows=5)
    print(f"    -> Successfully read 5 rows from {test_csv_path.name}. Total columns: {len(df_sample.columns)}")
    assert "isFraud" not in df_sample.columns, "CRITICAL: isFraud must not be in test_transaction.csv!"
    assert "target" not in df_sample.columns
    assert "label" not in df_sample.columns

    # Test scoring 3 real transactions
    ieee_scores = []
    for idx in range(3):
        row = df_sample.iloc[idx].to_dict()
        tid = row.get("TransactionID")
        # Strict exclusion of forbidden/identifier fields
        row.pop("TransactionID", None)
        row.pop("TransactionDT", None)

        # Convert NaNs to None for valid JSON serialization
        clean_features = {
            k: (None if (isinstance(v, float) and (math.isnan(v) or math.isinf(v))) else v)
            for k, v in row.items()
        }

        print(f"    -> Scoring Row {idx+1} (Source TransactionID: {tid}) ...")
        ieee_payload = {
            "mode": "IEEE_CIS_OFFLINE_BENCHMARK",
            "features": clean_features
        }
        status_code, score_resp = http_post_json(f"{BACKEND_BASE}/api/score-sandbox", ieee_payload)
        assert status_code == 200, f"IEEE-CIS scoring failed for row {idx+1}: {score_resp}"

        signals = score_resp["signals"]
        decision = score_resp["decision"]
        governor = score_resp["governor"]
        provenance = score_resp["provenance"]

        print(f"       [Result {idx+1}] Calibrated p={signals['p']:.6f} | Disagreement u={signals.get('u')} | u2={signals.get('u2')}")
        print(f"                        Action: {decision['action']} | Reason: {decision['reason_code']}")
        print(f"                        Governor: {governor['governor_status']} | Audit Logged: {score_resp['audit_logged']}")
        print(f"                        Backend: {provenance['model_backend']}")

        assert 0.0 <= signals["p"] <= 1.0, f"Probability out of bounds: {signals['p']}"
        assert decision["action"] in ("ROUTINE", "MANUAL_REVIEW", "FRAUD_ALERT", "HELD", "DEFERRED"), f"Invalid action: {decision['action']}"
        ieee_scores.append(score_resp)

    results["ieee_scores"] = ieee_scores

    # 9. Leakage & Forbidden Field Rejection Integrity
    print("\n[9] Testing Strict Leakage and Forbidden Field Rejection ...")
    # 9a. isFraud
    forbidden_payload_1 = {
        "mode": "IEEE_CIS_OFFLINE_BENCHMARK",
        "features": {"TransactionAmt": 100.0, "isFraud": 1}
    }
    code_1, resp_1 = http_post_json(f"{BACKEND_BASE}/api/score-sandbox", forbidden_payload_1)
    assert code_1 == 422, f"Expected 422 for isFraud leakage, got {code_1}"
    print(f"    -> Leakage rejection 'isFraud': HTTP {code_1} - {resp_1['error']['message']}")

    # 9b. TransactionID
    forbidden_payload_2 = {
        "mode": "IEEE_CIS_OFFLINE_BENCHMARK",
        "features": {"TransactionAmt": 100.0, "TransactionID": 3663550}
    }
    code_2, resp_2 = http_post_json(f"{BACKEND_BASE}/api/score-sandbox", forbidden_payload_2)
    assert code_2 == 422, f"Expected 422 for TransactionID, got {code_2}"
    print(f"    -> Leakage rejection 'TransactionID': HTTP {code_2} - {resp_2['error']['message']}")

    # 9c. TransactionDT
    forbidden_payload_3 = {
        "mode": "IEEE_CIS_OFFLINE_BENCHMARK",
        "features": {"TransactionAmt": 100.0, "TransactionDT": 18400000}
    }
    code_3, resp_3 = http_post_json(f"{BACKEND_BASE}/api/score-sandbox", forbidden_payload_3)
    assert code_3 == 422, f"Expected 422 for TransactionDT, got {code_3}"
    print(f"    -> Leakage rejection 'TransactionDT': HTTP {code_3} - {resp_3['error']['message']}")

    # 10. Audit Chain Integrity Verification (Post-Scoring)
    print("\n[10] Verifying Audit Chain Cryptographic Hash Integrity Post-Scoring ...")
    status_code, audit_post = http_get(f"{BACKEND_BASE}/api/audit/verify")
    assert status_code == 200
    print(f"    -> Post-scoring Chain Valid: {audit_post.get('is_valid')} Total Records: {audit_post.get('record_count')}")
    assert audit_post.get("is_valid") is True, f"Audit chain corrupted: {audit_post}"
    results["post_audit"] = audit_post

    # 11. Frontend Live Server Reachability
    print("\n[11] Verifying Vite Frontend Dev Server at http://127.0.0.1:5173/ ...")
    status_code, html_content = http_get(FRONTEND_BASE)
    assert status_code == 200, f"Frontend returned status {status_code}"
    assert "<div id=\"root\"></div>" in html_content, "Frontend index.html missing root div element"
    assert "Vite" in html_content or "SignalGate" in html_content or "src=\"/src/main.tsx\"" in html_content
    print("    -> Vite dev server responded HTTP 200 OK with root application container.")

    print("\n" + "=" * 70)
    print("ALL OPERATIONAL AND REAL-DATA INFERENCE CHECKS PASSED SUCCESSFULLY!")
    print("=" * 70)
    return results

if __name__ == "__main__":
    try:
        run_tests()
    except Exception as e:
        print(f"\n[FATAL ERROR] {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
