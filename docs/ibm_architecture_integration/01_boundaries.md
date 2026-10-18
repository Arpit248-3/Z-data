# Phase 2: Isolated Integration Package and Mode Contracts

**Milestone:** SignalGate IBM Architecture Integration  
**Governing Specification:** `docs/ibm_architecture_integration_master_spec.md` § C, § F  
**Deliverable Document:** `docs/ibm_architecture_integration/01_boundaries.md`  
**Timestamp:** 2026-10-18T16:05:00+05:30  
**Requirements Satisfied:** `BNDR-01`, `BNDR-02`, `BNDR-03`, `BNDR-04`  
**Quality Gates Passed:** 123/123 Python pytest tests passing; 21/21 Vitest frontend tests passing.

---

## 1. Executive Summary

Phase 2 establishes the isolated architectural boundaries, typed data contracts, and fail-closed readiness protocols governing the integration of the IBM fraud triage reference architecture (`reference/architecture/IBM-main/`) into SignalGate.

In strict accordance with the non-negotiable invariants set forth in the governing specification:
1. **Zero Working Tree Contamination:** All integration contracts, schemas, and mode registries are housed entirely within the new clean-room package `integrations/ibm_architecture/`. No root packages (`data/`, `models/`, `policy/`, `results/`, `backend/app/`) were overwritten, mutated, or reset.
2. **Strict Ground-Truth Quarantine (Master Spec § C2):** Target fraud labels (`isFraud`, `target`, `label`, `true_label`) and raw transaction identifiers (`TransactionID`, `TransactionDT`) are quarantined. The sanitized `AgentCaseView` enforces strict compile-time and runtime rejection with `LeakageViolationError`, preventing covert leakage into downstream models or agents.
3. **Explicit Evidence Modes & Fail-Closed Gates (Master Spec § C1):** Defined three operational modes (`SYNTHETIC_SMOKE_ONLY`, `IEEE_CIS_OFFLINE_BENCHMARK`, `LIVE_SOURCE_NOT_CONNECTED`). When raw dataset inputs (`data/raw/`) or fitted checkpoints are absent, the system fails closed with explicit diagnostic reporting rather than silently degrading to synthetic smoke fixtures or inventing transaction metrics.
4. **Verified Deterministic Core (Master Spec § C3):** All routing decisions, sequence hashing, and audit ledger entries are modeled with strongly typed Pydantic V2 schemas and SHA-256 cryptographic sealing.

---

## 2. Clean-Room Architectural Boundaries & Namespace Map

The integration code is organized into a dedicated, modular package structure:

```
integrations/
├── __init__.py                                 # Top-level integrations package identity
└── ibm_architecture/                           # Isolated clean-room namespace
    ├── __init__.py                             # Public symbol exports and version definition
    ├── exceptions.py                           # Structured exception hierarchy
    ├── modes.py                                # EvidenceMode enum and ModeState contracts
    ├── contracts.py                            # Pydantic data contracts (AuditRecord, Claim, etc.)
    ├── agent_view.py                           # Sanitized AgentCaseView with quarantine barriers
    └── registry.py                             # ModeRegistry and fail-closed prerequisite checks
```

### 2.1 Isolation Guarantees
- **No Namespace Collisions:** Top-level application routes in `backend/app/` and root modules (`models/`, `policy/`, `data/`) remain untouched and continue to operate normally.
- **Reference Tree Immutability:** `reference/architecture/IBM-main/` remains strictly read-only.
- **Independent Testing:** Boundary tests in `tests/test_ibm_boundaries.py` run cleanly within the project's root pytest configuration without cross-package import conflicts.

---

## 3. Explicit Source & Evidence Mode Contracts (Master Spec § C1)

In compliance with Section C1, runtime source modes are explicitly distinguished from evidence classifications. The system supports three mutually exclusive operational modes:

| Evidence Mode | Operational Status | Readiness Code | Required Prerequisites | Behavior When Unavailable |
|---|---|---|---|---|
| `SYNTHETIC_SMOKE_ONLY` | **Available / Active** | `READY` | `data/synthetic_smoke_fixture.csv`<br>`policy/frozen_policy.json` | N/A (Verified and operational) |
| `IEEE_CIS_OFFLINE_BENCHMARK` | **Blocked / Fail-Closed** | `UNAVAILABLE_MISSING_RAW_DATA` | `data/raw/train_transaction.csv`<br>`data/raw/train_identity.csv` | **Fails closed with `ModeUnavailableError`**; reports missing file paths and operator instructions. Zero silent fallback to synthetic data. |
| `LIVE_SOURCE_NOT_CONNECTED` | **Disconnected / Inactive** | `NOT_CONNECTED` | Payment gateway API credentials<br>Core banking Kafka streaming feed | Reports unauthenticated / disconnected status. Forensic evaluation only. |

### 3.1 Mode State Contract (`integrations/ibm_architecture/modes.py`)

```python
class EvidenceMode(str, Enum):
    SYNTHETIC_SMOKE_ONLY = "SYNTHETIC_SMOKE_ONLY"
    IEEE_CIS_OFFLINE_BENCHMARK = "IEEE_CIS_OFFLINE_BENCHMARK"
    LIVE_SOURCE_NOT_CONNECTED = "LIVE_SOURCE_NOT_CONNECTED"

class ModeReadiness(str, Enum):
    READY = "READY"
    UNAVAILABLE_MISSING_RAW_DATA = "UNAVAILABLE_MISSING_RAW_DATA"
    UNAVAILABLE_MISSING_CHECKPOINTS = "UNAVAILABLE_MISSING_CHECKPOINTS"
    NOT_CONNECTED = "NOT_CONNECTED"
    INCOMPATIBLE = "INCOMPATIBLE"

class ModeState(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    mode: EvidenceMode
    available: bool
    readiness: ModeReadiness
    description: str
    prerequisites_met: bool
    missing_prerequisites: List[str] = Field(default_factory=list)
    diagnostics: Dict[str, Any] = Field(default_factory=dict)
```

### 3.2 Fail-Closed Registry (`integrations/ibm_architecture/registry.py`)

The `ModeRegistry` inspects local filesystem state upon demand:
- `SYNTHETIC_SMOKE_ONLY`: Evaluated against `data/synthetic_smoke_fixture.csv` (confirmed present, 6,057,352 bytes). Returns `available=True, readiness=READY`.
- `IEEE_CIS_OFFLINE_BENCHMARK`: Evaluated against `data/raw/train_transaction.csv` and `data/raw/train_identity.csv`. When absent, returns `available=False, readiness=UNAVAILABLE_MISSING_RAW_DATA` and lists missing files.
- Calling `assert_mode_ready(mode)` raises `ModeUnavailableError` if `state.available` is False, enforcing the fail-closed invariant.

---

## 4. Ground-Truth Quarantine Barrier (Master Spec § C2)

Section C2 mandates that `isFraud` (or any equivalent label) and raw transaction identifiers (`TransactionID`, `TransactionDT`) must never enter:
- The ML feature matrix.
- Calibration or inference request data.
- Scoring feature forms.
- Routing decisions.
- `AgentCaseView`.
- LLM prompts.
- Drift-adaptation decisions.
- Online operational behavior.

### 4.1 Quarantine Implementation (`integrations/ibm_architecture/agent_view.py`)

Quarantine enforcement is active at both model initialization and instantiation:

```python
QUARANTINED_FIELDS: Set[str] = {
    "isfraud", "is_fraud", "true_label", "target", "label", "ground_truth",
    "transactionid", "transaction_id", "transactiondt", "transaction_dt",
}

def check_for_quarantine_violations(data: Any, context: str = "AgentCaseView") -> None:
    if isinstance(data, dict):
        keys_lower = {str(k).lower(): k for k in data.keys()}
        violations = [keys_lower[q] for q in QUARANTINED_FIELDS if q in keys_lower]
        if violations:
            raise LeakageViolationError(
                f"Ground-truth quarantine violation in {context}. "
                f"Fields {violations} are evaluation-only and strictly prohibited.",
                violated_fields=violations,
                context=context,
            )
```

### 4.2 Sanitized `AgentCaseView` Contract

`AgentCaseView` enforces `model_config = ConfigDict(extra="forbid", frozen=True)`. It permits only allowlisted fields derived from cryptographically sealed `AuditRecords`:

```python
class AgentCaseView(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    record_id: str = Field(min_length=1)
    p: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    u: Optional[float] = None
    u2: Optional[float] = None
    n: Optional[float] = Field(default=None, ge=0.0)
    action: Action
    reason: ReasonCode
    record_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    cfg_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    split_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
```

Attempting to instantiate an `AgentCaseView` with any quarantined key (`isFraud`, `TransactionID`, etc.) or un-whitelisted extra fields raises an immediate `LeakageViolationError` or `ValidationError`.

---

## 5. Validated Data Contracts (`integrations/ibm_architecture/contracts.py`)

### 5.1 `AuditRecord` & Cryptographic Chaining
- Represents one deterministic routing decision.
- Fields: `id`, `timestamp` (strictly timezone-aware UTC), `seq`, `prev_hash`, `p`, `u`, `u2`, `n`, `u_method`, `action`, `reason`, `cfg_hash`, `split_hash`, `record_hash`, `signature`.
- Deterministic hashing: `compute_record_hash()` serializes canonical key-sorted JSON and produces SHA-256 fingerprint; `seal()` binds the hash to the record.

### 5.2 `Claim` & `AgentRecord`
- `Claim`: Verifiable factual assertion for the `ClaimVerifierAgent` with comparison operator (`eq`, `ne`, `lt`, `lte`, `gt`, `gte`, `in`), field, expected value, and template ID.
- `AgentRecord`: Captures multi-agent status (`ok`, `unavailable`, `failed`, `timed_out`), asserted claims, input hash, and config hash.

### 5.3 `Proposal` (Advisory State Only)
- Captures advisory policy adjustments generated by the Drift Sentinel or Supervisor.
- Per Master Spec § C3, proposals are advisory only and cannot mutate active policy without external human approval.

---

## 6. Verification & Test Suite Execution

A dedicated unit test suite was authored in `tests/test_ibm_boundaries.py` with 14 test cases covering all boundary requirements.

### 6.1 Test Suite Results
```bash
python -m pytest -o "pythonpath=." tests/test_ibm_boundaries.py
```
**Result:** **14 passed** in 0.18s (100% pass rate).

### 6.2 Full Regression Test Suite Results
```bash
python -m pytest -o "pythonpath=." tests/
```
**Result:** **123 passed** in 19.61s (100% pass rate; 109 prior tests + 14 boundary tests).

### 6.3 Frontend Quality Gate
```bash
npm --prefix frontend test -- --run
```
**Result:** **21 passed** in 2.55s across 4 test suites (100% pass rate).

---

## 7. Requirements Compliance Matrix

| Requirement | Description | Implementation Status | Evidence / Verification |
|---|---|---|---|
| `BNDR-01` | Safe isolated namespace `integrations/ibm_architecture/` created without overwriting existing root packages | **SATISFIED** | `integrations/ibm_architecture/` established; `backend/app/` and root modules remain untouched |
| `BNDR-02` | Source/evidence mode enum and contracts supporting `SYNTHETIC_SMOKE_ONLY`, `IEEE_CIS_OFFLINE_BENCHMARK`, and `LIVE_SOURCE_NOT_CONNECTED` | **SATISFIED** | `integrations/ibm_architecture/modes.py` and `ModeRegistry` operational |
| `BNDR-03` | Strict ground-truth quarantine schema: `AgentCaseView` strictly excludes `isFraud`, `TransactionID`, and `TransactionDT` | **SATISFIED** | `integrations/ibm_architecture/agent_view.py` actively raises `LeakageViolationError`; verified by unit tests |
| `BNDR-04` | Fail-closed mode resolution: missing raw files or checkpoints trigger explicit error statuses rather than silent fallback | **SATISFIED** | `ModeRegistry.assert_mode_ready` raises `ModeUnavailableError` on missing `data/raw/` CSVs |

---

## 8. Conclusion & Sign-Off

Phase 2 is complete. The isolated integration package `integrations/ibm_architecture/` is fully operational with validated contracts, strict quarantine barriers, and fail-closed mode resolution. All existing test suites pass cleanly.

The repository is now ready for **Phase 3: Real IEEE-CIS Data Ingestion and Temporal Partitions** (`DATA-01`, `DATA-02`, `DATA-03`).
