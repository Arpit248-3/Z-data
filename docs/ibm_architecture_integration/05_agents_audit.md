# Phase 6: Governed Agents, Deterministic Claim Verification, and Cryptographic Audit Chain

## 1. Overview and Design Invariants

Phase 6 implements the Governed AI Agent and Cryptographic Audit Chain layer under the SignalGate IBM Architecture Integration specification. It establishes strict guardrails preventing unverified model claims, hallucinations, or routing overrides by automated or LLM agents.

### Core Architectural Invariants:
1. **Target and Key Quarantine**: Agents receive exclusively `AgentCaseView`. Neither `isFraud`, `TransactionID`, nor `TransactionDT` are accessible to agent components or templates.
2. **Deterministic Claim Verification**: No freeform LLM prose reaches the fraud analyst. Statements are generated exclusively by registered templates ($T1-T9$) populated with verified facts evaluated against `AgentCaseView`.
3. **Routing Invariance Under Failure**: If an LLM or provider fails or times out, the system fails gracefully to an offline deterministic brief. Routing actions and reasons assigned by deterministic policy remain strictly invariant.
4. **Cryptographic Tamper-Evident Audit Chain**: Every scored case is recorded into an append-only hash chain where record $i$ commits to the HMAC-SHA256 hash of record $i-1$. Any modification, omission, or truncation breaks the chain verification.
5. **Separation of Concerns**: Claims are stored in a `ClaimLedger` distinguishing verified factual claims from rejected unverified statements.

---

## 2. Implemented Components

### 2.1 Deterministic Claim Verifier (`integrations/ibm_architecture/governance/claim_verifier.py`)
- **Registered Templates**:
  - `T1_CALIBRATED_RISK`: Calibrated fraud risk score ($p$)
  - `T2_MODEL_DISAGREEMENT`: Ensemble disagreement spread ($u$)
  - `T3_ROUTING_ACTION`: Assigned deterministic action and reason code
  - `T4_HIGH_RISK_THRESHOLD`: Risk comparison against threshold
  - `T5_MODERATE_RISK_RANGE`: Intermediate risk boundary verification
  - `T6_ELEVATED_DISAGREEMENT`: Elevated disagreement spread verification
  - `T7_ROBUST_MAD_SIGNAL`: Robust median absolute deviation ($u_2$)
  - `T8_RECORD_PROVENANCE`: Config and partition split hash verification
  - `T9_MEMBER_COUNT`: Active ensemble model member count
- **Evaluation Engine**: Validates operator compatibility (`eq`, `ne`, `lt`, `lte`, `gt`, `gte`) with floating point tolerance ($\epsilon = 10^{-4}$). Rejects unregistered templates, illegal operators, and missing fields.

### 2.2 Governed Case Copilot (`integrations/ibm_architecture/governance/copilot.py`)
- Constructs deterministic case briefs consisting only of verified statements.
- Operates offline deterministically by default without external network dependencies.
- Enforces strict target and key quarantine: attempting to construct an `AgentCaseView` with forbidden fields raises `KeyError`.

### 2.3 Cryptographic Audit Chain (`integrations/ibm_architecture/governance/audit_chain.py`)
- Genesis block initialized with zero-vector parent hash ($64$ zeros).
- Each block records:
  - Sequence index, ISO-8601 UTC timestamp, record ID
  - HMAC-SHA256 payload signature using secret key
  - Chained record hash: $\text{SHA256}(\text{prev\_hash} \parallel \text{payload\_sig} \parallel \text{seq} \parallel \text{record\_id})$
- `verify_chain(blocks, secret_key)` walks the chain to verify sequence continuity, HMAC integrity, and cryptographic linkage.

### 2.4 Claim Ledger (`integrations/ibm_architecture/governance/claim_ledger.py`)
- In-memory structured ledger tracking verified vs rejected claims.
- Supports querying by record ID and computing acceptance statistics.

---

## 3. Verification and Test Results

Phase 6 unit tests in `tests/test_ibm_agents_audit.py`:
- `test_claim_verifier_accepts_valid_factual_claims`: PASSED
- `test_claim_verifier_rejects_false_and_unregistered_claims`: PASSED
- `test_case_copilot_offline_brief`: PASSED
- `test_case_copilot_quarantine_enforcement`: PASSED
- `test_case_copilot_routing_invariance`: PASSED
- `test_claim_ledger`: PASSED
- `test_audit_chain_append_and_verify`: PASSED
- `test_audit_chain_tamper_detection`: PASSED

Full regression test suite:
- **176 of 176 Pytest unit and regression tests passing** across all modules.
