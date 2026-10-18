# Phase 8: FastAPI Integration (Explicit Operating Mode Telemetry)

## 1. Overview and Design Invariants

Phase 8 connects the SignalGate IBM Architecture Integration services directly into the existing FastAPI backend application (`backend/app/main.py`), exposing explicit operating mode telemetry and human-in-the-loop governance without replacing existing routes or breaking existing frontend contracts.

### Core Architectural Invariants:
1. **Explicit Operating Mode Telemetry**: The API distinguishes runtime operational source modes:
   - `SYNTHETIC_SMOKE_ONLY`: Active and fully operational (`available: true`, `status: READY`).
   - `IEEE_CIS_OFFLINE_BENCHMARK`: Deferred on 8 GB RAM host (`available: false`, `status: UNAVAILABLE_MISSING_CHECKPOINTS`, `real_data_training_status: DEFERRED`).
   - `LIVE_SOURCE_NOT_CONNECTED`: Disconnected (`available: false`, `status: NOT_CONNECTED`).
2. **Fail-Closed Mode Selection**: Attempting to switch to an unavailable or deferred mode returns HTTP 409 Conflict with structured diagnostic information; the system **never** silently falls back to synthetic data while claiming real data.
3. **Scoring Sandbox Quarantine & Provenance**: The scoring sandbox enforces recursive rejection of forbidden fields (`isFraud`, `TransactionID`, `TransactionDT`), writes validated decisions to the audit trail, and returns explicit execution metadata (`source_mode: SYNTHETIC_SMOKE_ONLY`, `real_data_benchmark_status: DEFERRED`).
4. **Replay Gate Lifecycle & Human Sign-off**: Replay validation leaves proposals in `AWAITING_HUMAN_APPROVAL`. Operational activation strictly requires explicit human sign-off via `/api/governance/proposals/approve`.
5. **Cryptographic Audit Verification**: Exposes `/api/governance/audit-chain/verify` to validate HMAC-SHA256 authenticated hash-chain continuity.

---

## 2. Integrated API Routers and Endpoints

### 2.1 Mode Registry Router (`backend/app/routers/modes.py`)
- `GET /api/modes`: Lists all supported operational modes, active mode designation, hardware requirement disclosures (8 GB physical host vs $\ge 16$ GB required for full IEEE-CIS), and readiness states.
- `GET /api/modes/{mode_id}`: Detailed readiness and diagnostic inspect for an individual mode. Returns HTTP 404 for unknown modes.
- `POST /api/modes/select`: Mode switching endpoint. Returns HTTP 200 for `SYNTHETIC_SMOKE_ONLY`. Fails closed with HTTP 409 Conflict when requesting `IEEE_CIS_OFFLINE_BENCHMARK` or `LIVE_SOURCE_NOT_CONNECTED`.

### 2.2 Governance & Replay Gate Router (`backend/app/routers/governance.py`)
- `GET /api/governance/drift`: Computes distribution drift (PSI and KS statistics) across synthetic shift scenarios (S0–S4) without evaluation labels.
- `POST /api/governance/drift/propose`: Feeds drift summaries to `DriftSentinel` to emit advisory typed `Proposal` records.
- `GET /api/governance/proposals`: Lists all proposals evaluated by the Replay Gate.
- `POST /api/governance/proposals/validate`: Deterministically replays proposals against validation splits, enforcing `AWAITING_HUMAN_APPROVAL` status.
- `POST /api/governance/proposals/approve`: Applies human sign-off, transitioning proposal to `APPROVED_ACTIVE` and recording approver metadata.
- `POST /api/governance/proposals/reject`: Rejects proposal with reviewer and rationale.
- `POST /api/governance/copilot/brief`: Constructs case brief containing only verified factual claims from `AgentCaseView`. Rejects quarantined inputs with HTTP 400.
- `GET /api/governance/audit-chain/verify`: Verifies HMAC-SHA256 cryptographic audit chain integrity.

### 2.3 Scoring Sandbox (`backend/app/routers/scoring.py` & `backend/app/services/scoring.py`)
- `POST /api/score-sandbox`: Enhanced to return `provenance.source_mode = "SYNTHETIC_SMOKE_ONLY"` and `provenance.real_data_benchmark_status = "DEFERRED"`, while maintaining sub-50ms execution latency.

---

## 3. Verification and Test Results

Executed API test suite:
- `tests/test_api_integration_modes.py`: 8 tests passed.
- `tests/test_api.py`: 11 tests passed.
- `tests/test_api_artifacts.py`: 2 tests passed.
- `tests/test_api_scoring.py`: 3 tests passed.
- `tests/test_api_security.py`: 25 tests passed.

**Total**: 49 of 49 API integration and security tests passed with zero failures or regressions.
