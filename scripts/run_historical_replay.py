#!/usr/bin/env python3
"""
SignalGate — Historical Replay CLI Runner & Controller (Stage A)
==============================================================
Controls and monitors the local Historical Replay Worker against the real
IEEE-CIS raw dataset, loaded model bundle, and deterministic decision policy.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.error
import urllib.request
from typing import Any, Dict, Optional


def make_request(base_url: str, endpoint: str, method: str = "GET", data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    url = f"{base_url.rstrip('/')}{endpoint}"
    headers = {"Accept": "application/json"}
    body = None
    if data is not None:
        body = json.dumps(data).encode("utf-8")
        headers["Content-Type"] = "application/json"

    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            content = resp.read().decode("utf-8")
            return json.loads(content)
    except urllib.error.HTTPError as e:
        err_msg = e.read().decode("utf-8")
        print(f"[ERROR] HTTP {e.code}: {err_msg}", file=sys.stderr)
        sys.exit(1)
    except urllib.error.URLError as e:
        print(f"[ERROR] Connection failed: {e.reason}", file=sys.stderr)
        print(f"        Ensure FastAPI backend is running on {base_url}.", file=sys.stderr)
        sys.exit(1)


def cmd_status(base_url: str) -> None:
    status = make_request(base_url, "/api/replay/status")
    print(json.dumps(status, indent=2))


def cmd_stop(base_url: str) -> None:
    res = make_request(base_url, "/api/replay/stop", method="POST")
    print(f"[*] Replay worker stopped: {res.get('message', 'OK')}")
    print(f"    State: {res.get('state')} | Scored count: {res.get('scored_count')}")


def cmd_reset(base_url: str) -> None:
    res = make_request(base_url, "/api/replay/reset", method="POST")
    print(f"[*] Replay worker reset: {res.get('message', 'OK')}")


def cmd_step(base_url: str) -> None:
    res = make_request(base_url, "/api/replay/step", method="POST")
    event = res.get("event")
    if event:
        print(f"[SUCCESS] Scored Event {event['event_id']}")
        print(f"          Txn ID:        {event['transaction_id']}")
        print(f"          Provenance:    {event['data_provenance']}")
        print(f"          Model Prob p:  {event['score']:.4f}")
        print(f"          Disagreement:  {event['disagreement']:.4f}")
        print(f"          Action:        {event['action']}")
        print(f"          Reason Code:   {event['reason_code']}")
        print(f"          Latency:       {event['latency_ms']:.2f} ms")
        print(f"          Audit Hash:    Appended to audit_chain.jsonl")
    else:
        print(f"[*] Step response: {res.get('message') or res.get('error') or 'No event'}")


def cmd_stream(base_url: str, limit: int, delay_ms: int) -> None:
    print("=" * 70)
    print("SIGNALGATE — HISTORICAL REPLAY WORKER STREAM")
    print("=" * 70)
    print(f"Target URL:    {base_url}")
    print(f"Record Limit:  {limit}")
    print(f"Record Delay:  {delay_ms} ms")
    print(f"Provenance:    HISTORICAL_REPLAY (data/raw/test_transaction.csv)")
    print("=" * 70)

    # Check status first
    status = make_request(base_url, "/api/replay/status")
    mr = status.get("model_readiness")
    model_ready = mr if isinstance(mr, bool) else (mr.get("is_ready", False) if isinstance(mr, dict) else False)
    if not model_ready:
        print(f"[WARN] Local model pipeline reported NOT READY. Proceed with caution.", file=sys.stderr)

    start_res = make_request(base_url, "/api/replay/start", method="POST", data={"limit": limit, "delay_ms": delay_ms})
    print(f"[*] {start_res.get('message')}")
    print("[*] Streaming started. Press Ctrl+C to halt gracefully.\n")

    try:
        last_scored = -1
        while True:
            st = make_request(base_url, "/api/replay/status")
            scored = st.get("scored_count", 0)
            rate = st.get("recent_caserate", 0.0)
            state = st.get("state", "IDLE")
            last_ev = st.get("last_scored_event")

            if scored != last_scored and last_ev:
                last_scored = scored
                print(
                    f"[{state}] Scored: {scored:5d} | "
                    f"Rate: {rate:4.1f} evt/s | "
                    f"Last Latency: {st.get('last_latency_ms', 0.0):5.1f}ms | "
                    f"Txn: {last_ev.get('transaction_id')} -> {last_ev.get('action')} "
                    f"(p={last_ev.get('score', 0.0):.4f}, u2={last_ev.get('disagreement', 0.0):.4f}, {last_ev.get('reason_code')})"
                )

            if not st.get("is_running", False):
                print(f"\n[*] Replay run finished with state: {state}")
                print(f"    Total Read:     {st.get('received_count')}")
                print(f"    Total Accepted: {st.get('accepted_count')}")
                print(f"    Total Scored:   {st.get('scored_count')}")
                print(f"    Duplicates:     {st.get('duplicate_count')}")
                print(f"    Mean Latency:   {st.get('avg_latency_ms', 0.0):.2f} ms")
                break

            time.sleep(0.5)

    except KeyboardInterrupt:
        print("\n[*] Interrupted by user. Safely halting replay worker...")
        stop_res = make_request(base_url, "/api/replay/stop", method="POST")
        print(f"[*] Stopped: {stop_res.get('message')}")
        final_st = make_request(base_url, "/api/replay/status")
        print(f"[*] Final scored records: {final_st.get('scored_count')}")


def main() -> None:
    parser = argparse.ArgumentParser(description="SignalGate Historical Replay Controller")
    parser.add_argument("--url", default="http://127.0.0.1:8000", help="Base URL of FastAPI backend")
    parser.add_argument("--status", action="store_true", help="Print current replay status JSON and exit")
    parser.add_argument("--stop", action="store_true", help="Stop replay worker and exit")
    parser.add_argument("--reset", action="store_true", help="Reset replay worker cursor and counters")
    parser.add_argument("--step", action="store_true", help="Score exactly 1 historical record and exit")
    parser.add_argument("--limit", type=int, default=100, help="Max records to replay (default: 100)")
    parser.add_argument("--delay", type=int, default=100, help="Delay between records in milliseconds (default: 100)")

    args = parser.parse_args()

    if args.status:
        cmd_status(args.url)
    elif args.stop:
        cmd_stop(args.url)
    elif args.reset:
        cmd_reset(args.url)
    elif args.step:
        cmd_step(args.url)
    else:
        cmd_stream(args.url, limit=args.limit, delay_ms=args.delay)


if __name__ == "__main__":
    main()
