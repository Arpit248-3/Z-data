# SignalGate API Contract & Interface Specification

**Document Version:** 1.0.0  
**Phase:** Phase 6 — Production-Structured FastAPI Backend  
**Specification Target:** SignalGate v2.1 Blueprint & React3D Dashboard Integration  
**Base URL:** `http://127.0.0.1:8000` (API routes mounted under `/api`)  
**Data Status:** `SYNTHETIC_SMOKE_ONLY` (Preserved across all endpoints)

---

## 1. Architectural Principles & System Lifecycle

### 1.1 Ground Truth Leakage Prevention
- **Absolute Rule:** Target labels (`isFraud`, `true_label`, `target`, `label`, `y_true`, `ground_truth`), raw transaction IDs (`TransactionID`), and raw transaction timestamps (`TransactionDT`) are strictly forbidden in scoring and routing inputs.
- The `POST /api/score-sandbox` endpoint validates feature payloads recursively and rejects forbidden fields with HTTP `422 Unprocessable Entity`.
- Where offline evaluation artifacts contain ground-truth labels for retrospective replay analysis, responses explicitly distinguish offline held-out replay labels from live scoring signals.

### 1.2 Authoritative Source of Truth
- The API never retrains models, tunes thresholds, or recomputes policy benchmarks on GET requests or server startup.
- The backend reads exclusively from validated saved artifacts:
  - `results/results.json`: Consolidated evaluation benchmark and shift experiment results.
  - `policy/frozen_policy.json`: Cryptographically frozen decision router configuration and thresholds.
  - `results/cases.jsonl`: 2,000 evaluated test partition transactions with model signals and rationale.
  - `results/replay_rows.jsonl`: Ordered sequential replay rows for frontend 3D queue stream simulation.
  - `logs/audit.jsonl`: Append-only JSONL decision audit trail.
  - `models/`: Frozen HistGradientBoosting base model, sigmoid calibrator, ensemble members, and rank-residualizer.

### 1.3 Caching & Mutation Safety
- The artifact service employs file modification time (`mtime`) validation. Artifacts are cached in-memory and invalidated automatically when their underlying file changes on disk.
- All GET endpoints are strictly read-only and idempotent. Repeated requests do not alter filesystem timestamps, hashes, or evaluation results.

### 1.4 Error Response Envelope
All error responses adhere to a uniform, structured shape:

```json
{
  "error": {
    "code": "ERROR_CODE_STRING",
    "message": "Human-readable explanation of failure.",
    "details": {}
  }
}
```

No raw Python tracebacks, internal filesystem paths, or environment secrets are exposed to clients.

---

## 2. Global Error Codes

| HTTP Status | Error Code | Description |
|:---|:---|:---|
| `400 Bad Request` | `INVALID_FEATURE_PAYLOAD` | Feature values violate numeric constraints or formatting. |
| `400 Bad Request` | `INVALID_BUDGET_MULTIPLE` | Requested budget multiple is not available in pre-registered sweep. |
| `404 Not Found` | `CASE_NOT_FOUND` | Specified case ID was not found in saved prediction artifacts. |
| `422 Unprocessable Entity` | `VALIDATION_ERROR` | Schema validation error (e.g., forbidden field leakage, pagination bounds). |
| `503 Service Unavailable` | `ARTIFACT_UNAVAILABLE` | Required evaluation or replay artifact is missing or corrupted. |
| `503 Service Unavailable` | `MODEL_ARTIFACTS_UNAVAILABLE` | Base model, calibrator, ensemble, or frozen policy could not be loaded. |
| `500 Internal Server Error` | `INTERNAL_SERVER_ERROR` | Unhandled server exception. |

---

## 3. Endpoints Specification

### 3.1 Health & Status

#### GET `/api/health`
- **Description:** Reports API process liveness and server status independently of data readiness.
- **Parameters:** None
- **Response `200 OK`:**
  ```json
  {
    "service_name": "SignalGate Fraud Triage API",
    "version": "2.1.0",
    "status": "HEALTHY",
    "timestamp": "2026-10-17T04:32:15Z"
  }
  ```

#### GET `/api/status`
- **Description:** Granular readiness report for all pipeline dependencies, model artifacts, frozen policies, and evaluation files.
- **Parameters:** None
- **Response `200 OK`:**
  ```json
  {
    "service_name": "SignalGate Fraud Triage API",
    "version": "2.1.0",
    "overall_status": "READY",
    "evidence_status": "SYNTHETIC_SMOKE_ONLY",
    "dependencies": {
      "dataset": { "status": "SYNTHETIC_SMOKE_ONLY", "details": "Deterministic 10,000-row synthetic fixture." },
      "model_artifacts": { "status": "READY", "details": "Base model, calibrator, ensemble, and residualizer verified." },
      "frozen_policy": { "status": "READY", "details": "Frozen policy verified against hash 8d3f02ca492c..." },
      "consolidated_results": { "status": "READY", "details": "Consolidated evaluation artifact validated." },
      "explanations": { "status": "DISABLED", "details": "SHAP/feature attributions disabled in current release." }
    },
    "timestamp": "2026-10-17T04:32:15Z"
  }
  ```

---

### 3.2 Overview & Benchmark Results

#### GET `/api/overview`
- **Description:** Key performance metrics at primary workload budget (1.5x) from validated evaluation artifacts.
- **Parameters:** None
- **Response `200 OK`:**
  ```json
  {
    "dataset_status": "SYNTHETIC_SMOKE_ONLY",
    "evaluation_status": "COMPLETED",
    "total_tested_transactions": 2000,
    "available_fraud_count": 111,
    "primary_budget": 0.06525,
    "b2_recall": 0.09009,
    "signalgate_recall": 0.09009,
    "delta_recall_pp": 0.0,
    "ci_conclusive": false,
    "ci_lower_pp": 0.0,
    "ci_upper_pp": 0.0,
    "touched_rate": 0.065,
    "alert_rate": 0.007,
    "review_rate": 0.058,
    "deferred_rate": 0.0,
    "confident_misses": 0,
    "frozen_config_hash": "8d3f02ca492ca94bab45f3ceac8d39432c2f29f40d54e7990b4aa78cbbff6240",
    "split_hash": "07b55a4ed74f238c9ef5b779a749770cf274d4709a4389d9eab860dd9068fbdd",
    "status_fields": {
      "results_json": "READY",
      "disagreement_variant": "u2_rank_residual",
      "novelty": "DISABLED"
    }
  }
  ```

#### GET `/api/results`
- **Description:** Full consolidated evaluation summary including bootstrap intervals, budget sweeps, drift monitoring, and value models.
- **Parameters:** None
- **Response `200 OK`:**
  Returns complete content of `results/results.json`.

#### GET `/api/policies/compare`
- **Description:** Matched-budget policy comparisons across B1 (Random), B2 (Top-B Risk), B3a (Alert-Only), B4 (Risk + Raw Disagreement), and SignalGate.
- **Query Parameters:**
  - `budget_multiple` *(string, optional)*: Specific budget level from sweep (`"1.0x"`, `"1.5x"`, `"2.0x"`, `"3.0x"`). Defaults to `"1.5x"`.
- **Response `200 OK`:**
  ```json
  {
    "budget_multiple": "1.5x",
    "target_budget": 0.06525,
    "status": "SYNTHETIC_SMOKE_ONLY",
    "policies": [
      {
        "policy": "B1_random",
        "touched_rate": 0.065,
        "recall": 0.06306,
        "precision": 0.05385,
        "missed_fraud": 104,
        "ci_recall_lower": 0.02703,
        "ci_recall_upper": 0.10811
      },
      {
        "policy": "B2_top_b_risk",
        "touched_rate": 0.065,
        "recall": 0.09009,
        "precision": 0.07692,
        "missed_fraud": 101,
        "ci_recall_lower": 0.04505,
        "ci_recall_upper": 0.14414
      },
      {
        "policy": "SignalGate_frozen",
        "touched_rate": 0.065,
        "recall": 0.09009,
        "precision": 0.07692,
        "missed_fraud": 101,
        "ci_recall_lower": 0.04505,
        "ci_recall_upper": 0.14414
      }
    ]
  }
  ```

---

### 3.3 Scenarios & Replay

#### GET `/api/scenarios`
- **Description:** Returns metadata for all genuine evaluation scenarios present in artifacts.
- **Parameters:** None
- **Response `200 OK`:**
  ```json
  {
    "scenarios": [
      {
        "scenario_id": "S0",
        "name": "Chronological In-Distribution Test",
        "status": "SYNTHETIC_SMOKE_ONLY",
        "description": "Held-out test partition in natural chronological sequence.",
        "sample_count": 2000,
        "fraud_count": 111,
        "is_synthetic": true
      },
      {
        "scenario_id": "S1",
        "name": "Sudden Fraud Spikes",
        "status": "SYNTHETIC_SHIFT",
        "description": "Bursts of fraud concentrated in short temporal windows.",
        "sample_count": 2000,
        "fraud_count": 166,
        "is_synthetic": true
      },
      {
        "scenario_id": "S3",
        "name": "Coordinated Attack Storm",
        "status": "SYNTHETIC_SHIFT",
        "description": "Compound shift combining fraud surge, feature corruption, and high disagreement.",
        "sample_count": 2000,
        "fraud_count": 178,
        "is_synthetic": true
      }
    ]
  }
  ```

#### GET `/api/replay/rows`
- **Description:** Bounded chronological stream of transaction decisions for frontend 3D queue playback.
- **Query Parameters:**
  - `scenario` *(string, optional, default `"S0"`)*: Scenario identifier.
  - `offset` *(integer, optional, default `0`, `ge=0`)*: Row offset.
  - `limit` *(integer, optional, default `100`, `ge=1`, `le=500`)*: Number of rows to stream.
- **Response `200 OK`:**
  ```json
  {
    "total_rows": 2000,
    "offset": 0,
    "limit": 2,
    "scenario_id": "S0",
    "status": "SYNTHETIC_SMOKE_ONLY",
    "rows": [
      {
        "row_id": 1,
        "case_id": "case_test_000000",
        "timestamp": 86400,
        "transaction_id": "tx_test_000000",
        "amount": 250.75,
        "product_cd": "W",
        "card4": "visa",
        "p": 0.05421,
        "u": -0.21045,
        "u_method": "u2_rank_residual",
        "action": "ROUTINE",
        "reason_code": "R5_LOW_RISK_RELIABLE",
        "governor_status": "not_applicable",
        "lane_rank": null,
        "scenario_id": "S0",
        "status": "SYNTHETIC_SMOKE_ONLY",
        "offline_ground_truth": {
          "is_fraud": 0,
          "notice": "Offline held-out replay label for retrospective evaluation only. Never used in live triage."
        }
      }
    ]
  }
  ```

---

### 3.4 Case Explorer

#### GET `/api/cases`
- **Description:** Paginated case listing with multi-field search and risk filtering.
- **Query Parameters:**
  - `limit` *(integer, default `50`, `ge=1`, `le=200`)*: Maximum cases to return.
  - `offset` *(integer, default `0`, `ge=0`)*: Pagination offset.
  - `action` *(string, optional)*: Filter by triage action (`FRAUD_ALERT`, `MANUAL_REVIEW`, `ROUTINE`).
  - `reason_code` *(string, optional)*: Filter by reason code (`R1_HIGH_RISK`, `R2_INTERMEDIATE_RISK`, etc.).
  - `scenario` *(string, optional, default `"S0"`)*: Scenario identifier.
  - `risk_min` *(float, optional, `ge=0.0`, `le=1.0`)*: Minimum probability threshold.
  - `risk_max` *(float, optional, `ge=0.0`, `le=1.0`)*: Maximum probability threshold.
  - `search` *(string, optional)*: Case identifier substring match.
- **Response `200 OK`:**
  ```json
  {
    "total_cases": 2000,
    "limit": 50,
    "offset": 0,
    "scenario_id": "S0",
    "cases": [
      {
        "case_id": "case_test_000000",
        "timestamp": 86400,
        "amount": 250.75,
        "p": 0.05421,
        "u": -0.21045,
        "action": "ROUTINE",
        "reason_code": "R5_LOW_RISK_RELIABLE",
        "governor_status": "not_applicable",
        "lane_rank": null,
        "offline_is_fraud": 0
      }
    ]
  }
  ```

#### GET `/api/cases/{case_id}`
- **Description:** Full case inspection including raw signals, thresholds applied, and raw features.
- **Parameters:**
  - `case_id` *(path parameter, string)*: Case identifier (e.g., `"case_test_000042"`).
- **Response `200 OK`:**
  ```json
  {
    "case_id": "case_test_000042",
    "timestamp": 87200,
    "amount": 1450.00,
    "scenario_id": "S0",
    "status": "SYNTHETIC_SMOKE_ONLY",
    "signals": {
      "p": 0.08945,
      "u": 0.12450,
      "u_method": "u2_rank_residual",
      "novelty": null,
      "novelty_status": "disabled"
    },
    "decision": {
      "action": "FRAUD_ALERT",
      "reason_code": "R1_HIGH_RISK",
      "stage2_status": "computed",
      "policy_version": "v2.1",
      "config_hash": "8d3f02ca492ca94bab45f3ceac8d39432c2f29f40d54e7990b4aa78cbbff6240"
    },
    "features": {
      "TransactionAmt": 1450.00,
      "ProductCD": "W",
      "C1": 15.0
    },
    "offline_evaluation": {
      "is_fraud": 1,
      "notice": "Offline held-out replay label for retrospective evaluation only. Never used in live triage."
    },
    "explanations": {
      "status": "DISABLED",
      "notice": "Feature attribution disabled in current prototype."
    }
  }
  ```
- **Response `404 Not Found`:** Case identifier does not exist.

---

### 3.5 Audit Trail

#### GET `/api/audit`
- **Description:** Filtered retrieval of sequential JSONL audit logs.
- **Query Parameters:**
  - `limit` *(integer, default `50`, `ge=1`, `le=200`)*: Page limit.
  - `offset` *(integer, default `0`, `ge=0`)*: Record offset.
  - `action` *(string, optional)*: Filter by action.
  - `reason_code` *(string, optional)*: Filter by reason code.
  - `case_id` *(string, optional)*: Filter by case identifier.
- **Response `200 OK`:**
  ```json
  {
    "total_records": 154,
    "offset": 0,
    "limit": 50,
    "skipped_records": 0,
    "records": [
      {
        "id": "sandbox_4b772c91df8a",
        "ts": 1776400335,
        "p": 0.0622,
        "u": -0.271588,
        "u_method": "u2_rank_residual",
        "action": "ROUTINE",
        "reason": "R5_LOW_RISK_RELIABLE",
        "latency_ms": 2.45,
        "stage2_status": "computed",
        "governor_status": "not_applicable"
      }
    ]
  }
  ```

#### GET `/api/audit/export`
- **Description:** Downloads filtered audit records as JSONL (`application/x-ndjson`) or CSV (`text/csv`).
- **Query Parameters:**
  - `format` *(string, default `"jsonl"`, regex pattern `^(jsonl|csv)$`)*: Export format.
  - Filters matching `GET /api/audit`.
- **Response `200 OK`:** File attachment stream.

---

### 3.6 Scoring Sandbox

#### POST `/api/score-sandbox`
- **Description:** Real-time scoring simulation passing an arbitrary feature vector through the live fitted ML pipeline (`calibrated_p`, `disagreement`, `apply_rank_residual`, and `route()`).
- **Security Guard:** Strictly rejects all ground-truth labels and raw identifiers, even inside nested structures.
- **Request Body:**
  ```json
  {
    "features": {
      "TransactionAmt": 125.50,
      "C1": 1.0,
      "C2": 1.0,
      "D1": 14.0,
      "D2": 14.0,
      "V1": 1.0,
      "V2": 1.0,
      "V3": 1.0
    }
  }
  ```
- **Response `200 OK`:**
  ```json
  {
    "decision_id": "sandbox_a65239e248b1",
    "timestamp": "2026-10-17T04:32:15Z",
    "signals": {
      "p": 0.0622,
      "u": -0.271588,
      "u_method": "u2_rank_residual",
      "raw_disagreement": 0.005635,
      "novelty": null,
      "novelty_status": "disabled"
    },
    "decision": {
      "action": "ROUTINE",
      "reason_code": "R5_LOW_RISK_RELIABLE",
      "stage2_status": "computed",
      "policy_version": "v2.1",
      "config_hash": "8d3f02ca492ca94bab45f3ceac8d39432c2f29f40d54e7990b4aa78cbbff6240",
      "thresholds_applied": {
        "t_alert": 0.084705,
        "t_review": 0.071002,
        "u_threshold": 0.526773
      }
    },
    "governor": {
      "governor_status": "not_applicable",
      "lane_rank": null,
      "semantics": "Single-row sandbox simulation. Aggregate queue guarantees require full chronological replay."
    },
    "latency_ms": 2.87,
    "provenance": {
      "dataset_status": "SYNTHETIC_SMOKE_ONLY",
      "is_synthetic": true
    },
    "audit_logged": true,
    "notice": "Decision-support simulation only. Never alters live financial transactions."
  }
  ```
