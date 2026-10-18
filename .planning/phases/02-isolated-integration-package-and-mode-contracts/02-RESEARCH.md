# Phase 2: Isolated Integration Package and Mode Contracts — Research & Technical Specifications

**Phase:** `02-isolated-integration-package-and-mode-contracts`  
**Date:** 2026-10-18  
**Governing Specification:** `docs/ibm_architecture_integration_master_spec.md` § C, § F  
**Requirements Covered:** `BNDR-01`, `BNDR-02`, `BNDR-03`, `BNDR-04`  

---

## 1. Architectural Objectives & Isolation Boundaries

The objective of Phase 2 is to design and implement the foundation for all subsequent integration phases:
1. **Isolated Clean-Room Namespace:** Create `integrations/ibm_architecture/` as a self-contained, typed Python package.
   - Preserves all existing top-level modules (`data/`, `models/`, `policy/`, `results/`, `backend/app/`) intact.
   - Prevents namespace collisions between the reference repository's components and the existing production codebase.
2. **Explicit Evidence Mode Contracts:** Implement strongly typed enums and metadata models supporting:
   - `SYNTHETIC_SMOKE_ONLY`: Verified operational mode backed by `data/synthetic_smoke_fixture.csv`.
   - `IEEE_CIS_OFFLINE_BENCHMARK`: Real IEEE-CIS data mode that fails closed with explicit diagnostic reporting when raw data (`data/raw/`) or fitted checkpoints are absent.
   - `LIVE_SOURCE_NOT_CONNECTED`: Explicit unauthenticated / disconnected state for non-existent live transaction feeds.
3. **Non-Negotiable Ground-Truth Quarantine:**
   - Define `AgentCaseView`, `InferenceRequest`, and `ScoringPayload` schemas that enforce strict exclusion of `isFraud` (and equivalent labels) as well as raw identifiers (`TransactionID`, `TransactionDT`) from the ML feature matrix and agent/LLM reasoning contexts.
   - Use Pydantic V2 `model_validator` and `extra="forbid"` to actively raise `LeakageViolationError` (or `ValueError`) if quarantined fields are supplied.
4. **Fail-Closed Artifact & Mode Registry:**
   - Implement `ModeRegistry` and component readiness probes that verify required files, split hashes, and feature manifests.
   - Prohibit silent fallback from real benchmark mode to synthetic smoke data.
5. **Phase Deliverable:** Produce `docs/ibm_architecture_integration/01_boundaries.md` detailing all boundaries, schemas, and verification results.

---

## 2. Analysis of Existing & Reference Schemas

### 2.1 Existing Backend Schemas (`backend/app/schemas.py`)
- Defines FastAPI request/response models: `ReadinessStatusResponse`, `OverviewResponse`, `PolicyCompareResponse`, `ScoringResponse`, `DriftResponse`.
- Features strict leakage rejection on Sandbox scoring inputs:
  ```python
  @field_validator("features")
  @classmethod
  def reject_ground_truth_leakage(cls, features: Dict[str, Any]) -> Dict[str, Any]:
      quarantined = {"isFraud", "true_label", "label", "target"}
      intersection = quarantined.intersection(features.keys())
      if intersection:
          raise ValueError(f"Leakage violation: Quarantined fields {intersection} not allowed in scoring features.")
      return features
  ```
- Uses Pydantic V2 BaseModel with Field constraints.

### 2.2 Reference Architecture Schemas (`reference/architecture/IBM-main/schemas/`)
- `schemas/contracts.py`:
  - `Action`: Literal["ROUTINE", "FRAUD_ALERT", "MANUAL_REVIEW", "HELD", "DEFERRED"]
  - `ReasonCode`: Literal["R0_SIGNAL_UNAVAILABLE", "R1_HIGH_RISK", "R2_INTERMEDIATE_RISK", "R3_MODEL_DISAGREEMENT", "R4_UNFAMILIAR_INPUT", "R5_LOW_RISK_RELIABLE", "R6_QUEUE_CAPACITY"]
  - `AuditRecord`: Strongly validated Pydantic model with timezone-aware timestamp, sequence number, `prev_hash`, `record_hash`, `cfg_hash`, `split_hash`.
  - `Claim`: Verifiable assertion with field, operator (`eq`, `ne`, `lt`, `lte`, `gt`, `gte`, `in`), expected value, and template ID.
  - `AgentRecord`: Multi-agent output schema with status (`ok`, `unavailable`, `failed`, `timed_out`), claims, input hash, and timestamp.
  - `Proposal`: Policy adjustment advisory proposal with base config hash and rationale.
- `schemas/agent_view.py`:
  - `AgentCaseView`: Immutable, frozen view (`extra="forbid"`) containing only allowlisted fields: `record_id`, `p`, `u`, `u2`, `n`, `action`, `reason`, `record_hash`, `cfg_hash`, `split_hash`.
  - Built exclusively via `from_audit_record(record: AuditRecord)`.
  - Guarantees zero raw features or labels reach downstream agents or LLMs.

---

## 3. Package Structure for `integrations/ibm_architecture/`

To keep the integration clean, robust, and extensible across Phases 2 through 10, the package will be structured as follows:

```
integrations/
└── ibm_architecture/
    ├── __init__.py           # Package identity, version, public exports
    ├── exceptions.py         # LeakageViolationError, ModeUnavailableError, RegistryError
    ├── modes.py              # EvidenceMode enum, ModeStatus, ModeReadinessProbe
    ├── contracts.py          # Action, ReasonCode, AuditRecord, Claim, AgentRecord, Proposal
    ├── agent_view.py         # AgentCaseView, AgentView with strict quarantine
    └── registry.py           # ModeRegistry, ArtifactManifest, fail-closed resolution
```

### 3.1 Submodule Specifications

#### `integrations/ibm_architecture/exceptions.py`
- `LeakageViolationError(ValueError)`: Raised when `isFraud`, `TransactionID`, `TransactionDT`, or target labels are detected in inference or agent payloads.
- `ModeUnavailableError(RuntimeError)`: Raised when an unavailable or unconfigured mode is selected.
- `ArtifactNotFoundError(FileNotFoundError)`: Raised when a required model artifact or dataset partition is missing.
- `IncompatibleArtifactError(ValueError)`: Raised when an artifact hash does not match registered expectations.

#### `integrations/ibm_architecture/modes.py`
- `EvidenceMode(str, Enum)`:
  - `SYNTHETIC_SMOKE_ONLY = "SYNTHETIC_SMOKE_ONLY"`
  - `IEEE_CIS_OFFLINE_BENCHMARK = "IEEE_CIS_OFFLINE_BENCHMARK"`
  - `LIVE_SOURCE_NOT_CONNECTED = "LIVE_SOURCE_NOT_CONNECTED"`
- `ModeState(BaseModel)`:
  - `mode: EvidenceMode`
  - `available: bool`
  - `readiness: str` ("READY", "UNAVAILABLE_MISSING_RAW_DATA", "NOT_CONNECTED", etc.)
  - `description: str`
  - `prerequisites_met: bool`
  - `missing_prerequisites: list[str]`
  - `diagnostics: dict[str, Any]`

#### `integrations/ibm_architecture/contracts.py`
- Extends and unifies the contracts from reference architecture with SignalGate conventions:
  - Strongly typed `Action` and `ReasonCode` literals matching Blueprint Section 7.
  - `AuditRecord` with SHA-256 regex enforcement (`^[0-9a-f]{64}$`), timezone-aware timestamps, and deterministic hash computation.
  - `Claim`, `AgentRecord`, and `Proposal` contracts.

#### `integrations/ibm_architecture/agent_view.py`
- `AgentCaseView(BaseModel)`:
  - `model_config = ConfigDict(extra="forbid", frozen=True)`
  - Permitted fields: `record_id: str`, `p: float | None`, `u: float | None`, `u2: float | None`, `n: float | None`, `action: Action`, `reason: ReasonCode`, `record_hash: str`, `cfg_hash: str`, `split_hash: str`.
  - Explicit validator rejecting any dictionary or kwargs containing `isFraud`, `TransactionID`, `TransactionDT`, `target`, or `true_label`.

#### `integrations/ibm_architecture/registry.py`
- `ModeRegistry`:
  - Central manager for source/evidence modes and component readiness checks.
  - Startup check verifies physical presence of `data/synthetic_smoke_fixture.csv` (passes) vs `data/raw/train_transaction.csv` (absent).
  - Method `resolve_mode(mode: EvidenceMode) -> ModeState`:
    - For `SYNTHETIC_SMOKE_ONLY`: Returns `available=True, readiness="READY"`.
    - For `IEEE_CIS_OFFLINE_BENCHMARK`: Returns `available=False, readiness="UNAVAILABLE_MISSING_RAW_DATA", missing_prerequisites=["data/raw/train_transaction.csv", "data/raw/train_identity.csv"]`.
    - For `LIVE_SOURCE_NOT_CONNECTED`: Returns `available=False, readiness="NOT_CONNECTED"`.
  - Method `get_scoring_service(mode: EvidenceMode)`:
    - Fails closed with `ModeUnavailableError` if called with `IEEE_CIS_OFFLINE_BENCHMARK` while raw prerequisites are absent.

---

## 4. Test Strategy (`tests/test_ibm_boundaries.py`)

A comprehensive unit test suite will be written to verify all Phase 2 requirements:
1. **Namespace Isolation:** Confirm `integrations.ibm_architecture` imports cleanly without mutating any root module or global configuration.
2. **Mode Resolution:**
   - Test that `SYNTHETIC_SMOKE_ONLY` resolves to active and ready.
   - Test that `IEEE_CIS_OFFLINE_BENCHMARK` fails closed when `data/raw/` is missing, providing explicit diagnostics.
   - Test that `LIVE_SOURCE_NOT_CONNECTED` reports explicit disconnected status.
3. **Quarantine Enforcement:**
   - Test that `AgentCaseView` accepts allowlisted audit fields.
   - Test that passing `isFraud`, `TransactionID`, `TransactionDT`, or un-whitelisted extra fields raises an immediate error.
4. **Contract Invariants:**
   - Test `AuditRecord` validates SHA-256 patterns and timezone-aware timestamps.
   - Test `Claim`, `AgentRecord`, and `Proposal` serialization and validation.
5. **No Regression:**
   - Existing 109 backend tests and 21 frontend tests must continue to pass 100%.

---

## 5. Deliverable Requirements (`01_boundaries.md`)

`docs/ibm_architecture_integration/01_boundaries.md` will document:
- Clean-room architectural boundary diagram and namespace map.
- Complete data contracts and Pydantic schemas.
- Evidence mode state machine and fail-closed resolution rules.
- Ground-truth quarantine specifications and verification results.
- Test execution outputs and quality gate confirmation.
