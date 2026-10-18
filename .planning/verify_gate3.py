"""Gate 3 Runtime and Safety Verification Script.

Tests live runtime endpoints against the running server at http://127.0.0.1:8000.
"""

import json
import urllib.request
import urllib.error
import sys

BASE_URL = "http://127.0.0.1:8000"

def test_request(method, path, body=None):
    url = f"{BASE_URL}{path}"
    data = json.dumps(body).encode("utf-8") if body is not None else None
    headers = {"Content-Type": "application/json"} if body is not None else {}
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req) as resp:
            return resp.status, json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        raw = e.read().decode("utf-8")
        try:
            parsed = json.loads(raw)
        except Exception:
            parsed = raw
        return e.code, parsed

def run_checks():
    print("======================================================================")
    print("GATE 3 — RUNTIME AND SAFETY CHECKS")
    print("======================================================================")

    # 1. Synthetic scoring returns a valid response
    score_payload = {
        "features": {
            "TransactionAmt": 150.0,
            "card1": 12345,
            "C1": 1.0,
            "C2": 1.0,
            "D1": 0.0,
            "V1": 1.0,
            "TransactionHour": 14,
            "card1_tx_count_1d": 3
        }
    }
    status, score_resp = test_request("POST", "/api/score-sandbox", score_payload)
    assert status == 200, f"Expected 200, got {status}: {score_resp}"
    assert "signals" in score_resp and "decision" in score_resp
    p_val = score_resp["signals"]["p"]
    action_val = score_resp["decision"]["action"]
    assert action_val in ["ALERT", "REVIEW", "ROUTINE", "DEFERRED"]
    print(f"[PASS] 1. Synthetic scoring returns valid response: action={action_val}, p={p_val:.4f}, latency={score_resp['latency_ms']:.2f}ms")

    # 2. Provenance explicitly identifies synthetic data
    assert "provenance" in score_resp, "Missing provenance in score response"
    prov = score_resp["provenance"]
    assert prov.get("dataset_status") == "SYNTHETIC_SMOKE_ONLY"
    assert prov.get("real_data_benchmark_status") == "DEFERRED"
    print(f"[PASS] 2. Provenance explicitly identifies synthetic data: {prov}")

    # 3. Real-data benchmark status remains deferred
    status, modes_resp = test_request("GET", "/api/modes")
    assert status == 200, f"Expected 200 from /api/modes, got {status}"
    ieee_mode = next((m for m in modes_resp["supported_modes"] if m["mode"] == "IEEE_CIS_OFFLINE_BENCHMARK"), None)
    assert ieee_mode is not None, "IEEE_CIS_OFFLINE_BENCHMARK mode not found in /api/modes"
    assert ieee_mode["available"] is False, "IEEE_CIS mode must NOT be available"
    diag = ieee_mode.get("diagnostics", {})
    assert diag.get("real_data_training_status") == "DEFERRED", f"Expected DEFERRED status, got: {diag}"
    print(f"[PASS] 3. Real-data benchmark status remains deferred: {diag.get('real_data_training_status')} - {diag.get('reason')}")

    # 4. IEEE-CIS mode fails closed when required checkpoints are missing
    status, sel_resp = test_request("POST", "/api/modes/select", {"mode": "IEEE_CIS_OFFLINE_BENCHMARK"})
    assert status == 409, f"Expected 409 Conflict, got {status}: {sel_resp}"
    print(f"[PASS] 4. IEEE-CIS mode fails closed (HTTP 409): {sel_resp.get('error', {}).get('code')}")

    # 5. Live-source mode remains disconnected
    live_mode = next((m for m in modes_resp["supported_modes"] if m["mode"] == "LIVE_SOURCE_NOT_CONNECTED"), None)
    assert live_mode is not None, "LIVE_SOURCE_NOT_CONNECTED mode not found"
    assert live_mode["available"] is False
    assert live_mode["status"] == "NOT_CONNECTED"
    status, sel_live = test_request("POST", "/api/modes/select", {"mode": "LIVE_SOURCE_NOT_CONNECTED"})
    assert status == 409, f"Expected 409 Conflict for live mode switch, got {status}: {sel_live}"
    print(f"[PASS] 5. Live-source mode remains disconnected and fails closed (HTTP 409): {live_mode['status']}")

    # 6. Leakage rejection and audit-chain safeguards continue to work
    leakage_payload = {
        "features": {
            "TransactionAmt": 150.0,
            "isFraud": 1,  # Target leakage attempt
        }
    }
    status, leak_resp = test_request("POST", "/api/score-sandbox", leakage_payload)
    assert status in [400, 422], f"Expected 400/422 for target leakage, got {status}: {leak_resp}"
    err_str = str(leak_resp)
    assert "LEAKAGE VIOLATION" in err_str or "isFraud" in err_str
    print(f"[PASS] 6a. Target leakage rejection safeguard verified: HTTP {status} ({err_str[:90]}...)")

    status, chain_resp = test_request("GET", "/api/governance/audit-chain/verify")
    assert status == 200, f"Expected 200 for audit chain verify, got {status}: {chain_resp}"
    assert chain_resp.get("verified") is True, f"Audit chain verification failed: {chain_resp}"
    assert chain_resp.get("tamper_detected") is False, f"Tamper detected in audit chain: {chain_resp}"
    print(f"[PASS] 6b. Cryptographic HMAC-SHA256 audit-chain verified: verified={chain_resp.get('verified')}, length={chain_resp.get('chain_length')}")

    # 7. Frontend Vite server is serving the production/dev bundle cleanly
    with urllib.request.urlopen("http://127.0.0.1:5173/sandbox") as resp:
        html = resp.read().decode("utf-8")
        assert resp.status == 200
        assert "<div id=\"root\">" in html or "<html" in html
    print("[PASS] 7. Frontend dev/production server responds with valid HTML on /sandbox")

    print("======================================================================")
    print("ALL GATE 3 RUNTIME AND SAFETY CHECKS PASSED (EXIT 0)")
    print("======================================================================")

if __name__ == "__main__":
    run_checks()
