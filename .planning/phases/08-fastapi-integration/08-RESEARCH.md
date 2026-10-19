# Phase 8: FastAPI Integration — Research & Technical Specifications

**Phase:** `08-fastapi-integration`
**Date:** 2026-10-18
**Governing Specification:** `docs/ibm_architecture_integration_master_spec.md` § C, § L
**Requirements Covered:** `APII-01`, `APII-02`, `APII-03`

---

## 1. Architectural Alignment & Safety Invariants

Phase 8 connects all integration components developed in Phases 2–7 (Data ingestion, Model bundle, Dynamic scoring, Governed agents, Claim verification, Cryptographic audit chain, Multi-metric drift monitor, and Human-approved Replay Gate) into the production FastAPI backend application (`backend/app/main.py`).

In strict compliance with the governing specification and review requirements:

### 1.1 Existing FastAPI Architecture Integration (`APII-01`, Master Spec § L)
- Directly integrates with the established FastAPI application (`backend/app/main.py`), routers, schemas, and dependency injection providers.
- Reuses existing compatible routers (`health.py`, `cases.py`, `scoring.py`, `audit.py`) while introducing clean integration routers (`integration.py` for mode, model card, drift, and governance) rather than duplicating endpoints or replacing FastAPI.
- Preserves all existing route paths, Pydantic request/response schemas, and behaviors for synthetic smoke mode.

### 1.2 Preservation of Three Explicit Operating Modes (`APII-01`, Master Spec § C1, § L)
- Maintains and exposes clear status for the three canonical evidence modes:
  - `SYNTHETIC_SMOKE_ONLY`: Baseline synthetic smoke test data and models.
  - `IEEE_CIS_OFFLINE_BENCHMARK`: Real IEEE-CIS data, trained model bundle (`models/artifacts/ieee_cis_v1/`), dynamic scoring, drift reports, and governed agents.
  - `LIVE_SOURCE_NOT_CONNECTED`: Truthful unready indicator confirming external live banking feeds are not attached.
- **Fail-Closed Integrity Invariant:**
  - Real-data mode reports `READY` **only** when the Phase 4 model bundle (ExtraTrees, LightGBM, Platt calibrator, feature manifest, splits) is cryptographically verified against SHA-256 hashes.
  - If any artifact is missing, incompatible, or altered, the endpoint fails closed with an actionable HTTP 503 / 400 error.
  - **No Silent Fallback:** The backend never silently degrades or falls back from real IEEE-CIS requests to synthetic data.
  - Synthetic demonstration mode remains fully functional and accessible.

### 1.3 Model & Policy Authority Invariance (`APII-02`, Master Spec § C, § L)
- The deterministic scoring service (`ScoringService`) and policy router (`RouterPolicyAdapter`) remain authoritative.
- Agents (Case Copilot, Supervisor, Sentinel) may explain evidence and generate advisory proposals, but **must never** alter authoritative fraud probabilities, policy thresholds, capacity decisions, model parameters, or active routing decisions.
- **Human Approval Gate Invariant:** Policy proposals emitted by Sentinel or Supervisor remain inert and require deterministic replay validation followed by explicit human approval (`approve_proposal`) before consideration.
- **Leakage Quarantine Invariant:** All scoring and simulation requests enforce recursive rejection of `isFraud`, `target`, `label`, `true_label`, `TransactionID`, and `TransactionDT` with HTTP 422 / 400.
- The held-out test partition is strictly forbidden from tuning policies or thresholds.

### 1.4 Security, Reliability & Cache Management (`APII-02`, `APII-03`)
- **Pydantic Validation & HTTP Status Codes:** Strongly typed request/response models with strict validation; structured HTTP error responses (400, 404, 409, 422, 503) without raw tracebacks or sensitive data exposure.
- **Explicit Artifact Caching:** The Phase 4 model bundle and feature pipeline are cached in memory via a singleton provider (`get_integration_service()`), avoiding expensive and slow model reloads on every inference request.
- **Concurrency & Reentrancy Safety:** Replay Gate and proposal lifecycle operations are thread-safe, preventing race conditions or unauthorized activation.
- **Cryptographic Audit Chain Provenance:** Real scoring requests and Replay Gate governance decisions are sealed into the cryptographic `AuditChain`.
- **Honest Security Claims:** No claims of external authentication or hardware WORM beyond what is implemented.

---

## 2. API Contract Specifications

### 2.1 Mode & Readiness Status (`APII-01`)
- **`GET /api/mode`**
  - Response:
    ```json
    {
      "active_mode": "SYNTHETIC_SMOKE_ONLY",
      "available_modes": [
        "SYNTHETIC_SMOKE_ONLY",
        "IEEE_CIS_OFFLINE_BENCHMARK",
        "LIVE_SOURCE_NOT_CONNECTED"
      ],
      "readiness": {
        "SYNTHETIC_SMOKE_ONLY": {"status": "READY", "details": {...}},
        "IEEE_CIS_OFFLINE_BENCHMARK": {"status": "READY", "bundle_verified": true, "details": {...}},
        "LIVE_SOURCE_NOT_CONNECTED": {"status": "UNAVAILABLE", "reason": "Live payment feed not connected"}
      }
    }
    ```
- **`GET /api/status?mode=IEEE_CIS_OFFLINE_BENCHMARK`**
  - Checks model bundle components, feature manifest (391 features), calibration, and audit key status.
  - Returns `READY` with verified hashes, or actionable error details if unready.

### 2.2 Model Card & Provenance (`APII-01`)
- **`GET /api/model/card?mode=IEEE_CIS_OFFLINE_BENCHMARK`**
  - Response: Model architecture (`EraBaggedHeterogeneousEnsemble`: ExtraTrees + LightGBM), calibrator (`PlattCalibrator`), feature count (391), bundle component SHA-256 hashes, split hash, and training metadata.
- **`GET /api/model/card?mode=SYNTHETIC_SMOKE_ONLY`**
  - Response: Synthetic baseline LightGBM model metadata.

### 2.3 Case Explorer with Mode Selection (`APII-01`)
- **`GET /api/cases?mode=IEEE_CIS_OFFLINE_BENCHMARK&limit=50&offset=0`**
  - Serves real-data cases projected through sanitized `AgentCaseView` (no target labels or raw identifiers).

### 2.4 Multi-Metric Drift Monitoring API (`APII-01`)
- **`GET /api/drift/report?mode=IEEE_CIS_OFFLINE_BENCHMARK`**
  - Returns evidence-backed drift report: `mean_psi`, `max_psi`, `significant_drift_features`, `score_drift`, `notice`, and feature-level metrics (PSI, KS, Wasserstein distance, missing rate deltas).

### 2.5 Scoring Sandbox (`APII-02`)
- **`POST /api/score-sandbox`**
  - Request Body:
    ```json
    {
      "features": {"TransactionAmt": 150.0, "ProductCD": "W", "card4": "visa", ...},
      "mode": "IEEE_CIS_OFFLINE_BENCHMARK"
    }
    ```
  - Behavior:
    - Recursively inspects features for leakage fields (`isFraud`, `TransactionID`, etc.); rejects with HTTP 422 if detected.
    - If `mode == "IEEE_CIS_OFFLINE_BENCHMARK"`: executes feature pipeline transform over 391 features, runs ExtraTrees + LightGBM ensemble, applies Platt calibration, evaluates `RouterPolicyAdapter`, seals decision to `AuditChain`.
    - If `mode == "SYNTHETIC_SMOKE_ONLY"`: maintains exact historical synthetic pipeline execution.
  - Response:
    ```json
    {
      "decision_id": "TX_SANDBOX_...",
      "timestamp": "2026-10-18T22:00:00Z",
      "audit_logged": true,
      "latency_ms": 12.4,
      "signals": {"p": 0.0452, "u": 0.2104, "u2": 0.2315, "u_method": "u2_rank_residual", "novelty_status": "disabled"},
      "decision": {"action": "ROUTINE", "reason_code": "R5_LOW_RISK_RELIABLE", "config_hash": "..."},
      "governor": {"governor_status": "PASSED_UNCONSTRAINED", "semantics": "PASSED_UNCONSTRAINED"},
      "mode": "IEEE_CIS_OFFLINE_BENCHMARK",
      "model_id": "ieee_cis_v1_ensemble",
      "audit_seq": 42
    }
    ```

### 2.6 Replay Gate Governance & Human Authorization (`APII-03`)
- **`GET /api/governance/proposals`**: Lists all advisory policy change proposals and their lifecycle status (`PENDING`, `AWAITING_HUMAN_APPROVAL`, `APPROVED`, `REJECTED`).
- **`GET /api/governance/proposals/{proposal_id}`**: Returns proposal detail, changes, base configuration hash, and validation metrics.
- **`POST /api/governance/proposals/{proposal_id}/replay`**: Triggers deterministic validation replay on validation partition, computing touches, churn count, and capacity compliance.
- **`POST /api/governance/proposals/{proposal_id}/approve`**: Authenticated human approval endpoint requiring `approver` ID and rationale; transitions status to `APPROVED` and seals to `AuditChain`.
- **`POST /api/governance/proposals/{proposal_id}/reject`**: Rejection endpoint transitioning status to `REJECTED`.

---

## 3. Preservation & Security Safeguards

1. **Target Quarantine:** Enforces recursive label checks on all scoring and simulation endpoints.
2. **Immutable Active Policy:** Replay Gate and proposal endpoints never auto-activate changes.
3. **No Retraining via GET:** No endpoint initiates model training or file deletion.
4. **Bounded Pagination:** All listing endpoints enforce `limit = min(max_limit, max(1, limit))`.
5. **Audit Chain Persistence:** All governance decisions and real inference scores append to `AuditChain`.
6. **Zero Regression:** All 195 existing tests must continue to pass with 100% success rate.
