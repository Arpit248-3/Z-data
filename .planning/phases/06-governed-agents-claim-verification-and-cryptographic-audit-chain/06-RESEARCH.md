# Phase 6: Governed Agents, Claim Verification and Cryptographic Audit Chain — Research & Technical Specifications

**Phase:** `06-governed-agents-claim-verification-and-cryptographic-audit-chain`
**Date:** 2026-10-18
**Governing Specification:** `docs/ibm_architecture_integration_master_spec.md` § C, § J
**Requirements Covered:** `AGNT-01`, `AGNT-02`, `AGNT-03`

---

## 1. Architectural Objectives & Invariants

Phase 6 implements the governed multi-agent triage, deterministic claim verification, and cryptographic audit provenance layer for the IEEE-CIS integration.

In strict compliance with the governing specification:
1. **Sanitized Input Boundary (`AGNT-01`, Master Spec § J1):**
   - Agents (Case Copilot, Drift Sentinel, Supervisor) must interact with case data **exclusively** through allowlisted, sanitized projections: `AgentCaseView`.
   - `AgentCaseView` exposes only: `record_id`, `p`, `u`, `u2`, `n`, `action`, `reason`, `record_hash`, `cfg_hash`, `split_hash`.
   - Agents must **never** receive raw feature matrices (the 391 tabular variables), target labels (`isFraud`, `target`, `label`), raw identifiers (`TransactionID`, `TransactionDT`), environment variables, or server local paths.
   - Any attempt to instantiate an `AgentCaseView` with quarantined attributes raises `LeakageViolationError`.
2. **Deterministic Dual-Mode Copilot (`AGNT-01`, Master Spec § J2):**
   - Implements `CaseCopilot` supporting two operational modes:
     - **Deterministic Offline-Template Mode (Default):** Generates structured analyst briefs from verified static templates populated with factual case fields.
     - **Optional Configured LLM Provider Mode:** An injectable provider interface (`LLMProvider`) that interfaces with a locally reachable Ollama or OpenAI-compatible endpoint when valid credentials and endpoint URLs are configured.
   - **Fail-Safe & Independence Invariant:** Agent functionality is strictly an advisory copilot. Agent failure, network timeout, or disablement must **never** mutate or block the deterministic routing action (`FRAUD_ALERT`, `MANUAL_REVIEW`, `ROUTINE`, `DEFERRED`) or reason code (`R0`–`R6`).
3. **Deterministic Claim Verification & Ledger (`AGNT-02`, Master Spec § J3):**
   - Agents may propose structured factual claims via the typed `Claim` schema (`field`, `operator`, `value`, `template_id`).
   - `ClaimVerifier` evaluates claims deterministically against source truth (`AgentCaseView`, `AuditRecord`, model manifests).
   - Under no circumstances is arbitrary free-form LLM prose rendered as established fact without deterministic verification.
   - All claims (accepted and rejected) are appended to a queryable `ClaimLedger`.
4. **Cryptographic HMAC-SHA256 Audit Chain (`AGNT-03`, Master Spec § J4):**
   - Decision records are sealed into an append-only cryptographic ledger (`AuditRecord`).
   - Each entry binds `seq`, `timestamp`, `prev_hash`, `record_hash = SHA-256(canonical_payload)`, and an HMAC-SHA256 signature.
   - Secret key handling: Read from environment variable `SIGNALGATE_AUDIT_KEY`. If key is unconfigured, audit verification status reports as unavailable rather than using a hardcoded or predictable default key.
   - Runtime audit entries for IEEE-CIS are persisted to `results/ieee_cis_v1/audit_chain.jsonl`, isolating them from the root synthetic audit log (`logs/audit.jsonl`).
   - Provides full tamper detection: validates sequence continuity, hash linkage, and signature validity, detecting record tampering, omissions, and insertions.

---

## 2. Component Specifications

### 2.1 AgentCaseView & Quarantine Enforcement (`agent_view.py`)
- Already established in Phase 2 and verified in `tests/test_ibm_boundaries.py`.
- In Phase 6, we bind `AgentCaseView.from_scoring_result(result: ScoringResult)` and `AgentCaseView.from_audit_record(record: AuditRecord)`.
- Validates that zero leakage occurs when transferring scoring decisions to agents.

### 2.2 Case Copilot & LLM Provider Interface (`agents/copilot.py`)
- **`CopilotBrief` Schema:**
  - `case_id: str`
  - `risk_assessment: str` (e.g. "Elevated Risk", "Borderline Review", "Low Risk Reliable")
  - `uncertainty_interpretation: str` (interprets $u$ and $u_2$ dispersion)
  - `suggested_investigation_focus: List[str]`
  - `mode: Literal["offline_template", "live_llm"]`
  - `provider_info: Dict[str, Any]`
  - `generated_at: str`
- **`LLMProvider` Protocol:**
  - `generate(prompt: str, case_view: AgentCaseView) -> str`
- **`OfflineTemplateProvider`:**
  - Formats structured text based on deterministic rules:
    - High-risk cases ($p \ge t_{\text{alert}}$): highlights critical priority, fast-track manual verification.
    - Ambiguous / Disagreement cases ($u \ge u_{\text{threshold}}$): highlights epistemic model divergence across tree vs linear estimators.
    - Routine low-risk cases ($p < t_{\text{review}}$): provides standard low-risk justification.
- **`OllamaLLMProvider` / `OpenAILLMProvider`:**
  - Optional provider with bounded timeouts ($\le 5\text{s}$) and safe fallback to offline template if network fails or response is malformed.

### 2.3 Agent Supervisor (`agents/supervisor.py`)
- Coordinates dispatching of `AgentCaseView` to Copilot and Claim Verifier.
- Wraps execution in exception guards: if copilot raises any error, supervisor captures the error, returns the offline template brief, and logs an `AgentRecord` with `status="failed"`.

### 2.4 Claim Verifier & Ledger (`governance/claim_verifier.py`, `governance/claim_ledger.py`)
- **Supported Comparison Operators:**
  - `eq`: `fact == claim.value`
  - `ne`: `fact != claim.value`
  - `lt`: `fact < claim.value`
  - `lte`: `fact <= claim.value`
  - `gt`: `fact > claim.value`
  - `gte`: `fact >= claim.value`
  - `in`: `fact in claim.value`
- **Verification Rule:**
  - Resolves target field on `AgentCaseView` or `AuditRecord`. If field does not exist, verification fails with reason `"Field not found on source record"`.
  - Compares fact with claim value using numeric tolerance for floats ($10^{-5}$).
  - Returns `VerificationResult(claim=claim, is_verified=bool, observed_value=fact, reason=str)`.
- **`ClaimLedger`:**
  - Thread-safe or serial append-only collection.
  - Queries claims by `record_id`, `template_id`, `is_verified` status.

### 2.5 Cryptographic HMAC-SHA256 Audit Chain (`governance/audit_chain.py`)
- **Block Structure:**
  - `seq: int` (0, 1, 2, ...)
  - `timestamp: datetime` (UTC, timezone-aware)
  - `prev_hash: str` (64 hex characters)
  - `p, u, u2, n, action, reason, cfg_hash, split_hash`
  - `record_hash: str` (SHA-256 over canonical JSON)
  - `signature: str` (HMAC-SHA256(secret_key, record_hash))
- **`AuditChain` Class:**
  - `append(record: AuditRecord) -> AuditRecord` (calculates `prev_hash`, `record_hash`, signs with HMAC, and appends).
  - `verify_chain() -> Tuple[bool, List[str]]` (audits sequence order, unbroken hash chain, and HMAC signatures).
  - `dump_jsonl(path: Path)` / `load_jsonl(path: Path) -> AuditChain`.
- **Tamper Resistance:**
  - Any altered probability, reason code, or sequence breaks the hash chain.
  - Any altered record hash breaks the HMAC signature.

---

## 3. Directory Layout & Isolated Namespaces

```
integrations/ibm_architecture/
├── agent_view.py                  (sanitized view schemas, existing)
├── contracts.py                   (data contracts, existing)
├── agents/
│   ├── __init__.py                (exports supervisor, copilot, providers)
│   ├── copilot.py                 (CaseCopilot, CopilotBrief, OfflineTemplateProvider)
│   ├── providers.py               (LLMProvider protocol, OllamaProvider, FallbackProvider)
│   └── supervisor.py              (AgentSupervisor, dispatch rules, safe guards)
├── governance/
│   ├── __init__.py                (exports claim verifier, ledger, audit chain)
│   ├── claim_verifier.py          (ClaimVerifier, VerificationResult)
│   ├── claim_ledger.py            (ClaimLedger, query and persistence)
│   └── audit_chain.py             (AuditChain, HMAC-SHA256 seal, verification)
```

Existing root files remain untouched:
- `policy/audit.py`
- `logs/audit.jsonl`
- `backend/app/services/audit.py`

---

## 4. Testing Strategy (`tests/test_ibm_agents.py`)

1. **Quarantine Barrier Tests:**
   - Attempting to pass `isFraud`, `TransactionID`, or `TransactionDT` to `AgentCaseView` or `CaseCopilot` raises `LeakageViolationError`.
2. **Offline Template Tests:**
   - CaseCopilot produces valid `CopilotBrief` across high-risk, intermediate-risk, disagreement, and routine cases.
3. **Provider Fallback & Timeout Tests:**
   - Simulating an LLM provider crash or timeout seamlessly produces the offline template brief without raising an uncaught exception.
4. **Action Invariance Tests:**
   - Deterministic action and reason code are identical before and after agent invocation, even when the agent provider is disabled or errors.
5. **Claim Verifier Tests:**
   - Correct assertions (e.g. `p > 0.08` for alert case) verify as `True`.
   - Seeded false assertions (e.g. `action == 'ROUTINE'` for alert case) verify as `False`.
   - Missing fields fail gracefully.
6. **Claim Ledger Tests:**
   - Appending claims, querying by case ID, and calculating acceptance rates.
7. **HMAC Audit Chain Tests:**
   - Sequential block appending with correct `seq` and `prev_hash`.
   - Cryptographic verification passes on un-tampered chain.
   - Tamper detection: modifying a payload, dropping a block, or inserting a forged block fails verification with diagnostic error.
   - Key absence handling: chain operates cleanly with unsigned notice when no key is configured.
