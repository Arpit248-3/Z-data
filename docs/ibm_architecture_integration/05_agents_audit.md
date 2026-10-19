# SignalGate IBM Architecture Integration — Phase 6: Governed Agents, Claim Verification and Cryptographic Audit Chain

**Governing Specification:** `docs/ibm_architecture_integration_master_spec.md` § C, § J
**Status:** IMPLEMENTED_VERIFIED
**Architecture Version:** `ieee_cis_v1`
**Requirements Covered:** `AGNT-01`, `AGNT-02`, `AGNT-03`
**Last Updated:** 2026-10-18

---

## 1. Executive Summary & Non-Negotiable Architectural Boundaries

Phase 6 implements the Governed Agent subsystem, Deterministic Claim Verifier, and HMAC-SHA256 Cryptographic Audit Chain for the IEEE-CIS Fraud Detection benchmark integration.

The implementation strictly satisfies the non-negotiable boundaries defined in `docs/ibm_architecture_integration_master_spec.md`:
1. **Advisory-Only Agent Invariance (`AGNT-01`, Master Spec § C, § J):** Agents never calculate authoritative fraud scores, calibrate probabilities, define policy thresholds, calculate capacity budgets, or make triage routing decisions. The deterministic scoring service (`ScoringService`) and policy router (`RouterPolicyAdapter`) remain exclusively authoritative. If an agent crashes, times out, or is disabled, the system's routing decisions (`FRAUD_ALERT`, `MANUAL_REVIEW`, `ROUTINE`, `DEFERRED`) and reason codes (`R0`–`R6`) remain mathematically identical.
2. **Strict Ground-Truth & Identifier Quarantine (`AGNT-01`, Master Spec § C2):** Agents receive only a sanitized `AgentCaseView`. Any attempt to pass target labels (`isFraud`, `target`, `label`, `true_label`) or raw transaction identifiers (`TransactionID`, `TransactionDT`) raises a fatal `LeakageViolationError`.
3. **Epistemic Disagreement Semantics (`AGNT-01`, Master Spec § J):** High model disagreement ($u \ge u_{\text{threshold}}$) is explicitly explained as epistemic model divergence across tree architectures, **never** as proof or evidence of fraud.
4. **Deterministic Fact & Claim Verification (`AGNT-02`, Master Spec § J):** Factual assertions in agent outputs are formalized into typed `Claim` records and validated deterministically by `ClaimVerifier` against ground-truth case evidence. Claims contradictory to or unsupported by evidence are marked as rejected.
5. **Cryptographic HMAC-SHA256 Audit Chain (`AGNT-03`, Master Spec § J):** All audit records are signed and cryptographically linked sequentially via HMAC-SHA256. Any record alteration, sequence tampering, or broken link is immediately detected.

---

## 2. Governed Agent Architecture (`AGNT-01`)

### 2.1 Clean-Room Agent Isolation & Sanitized Views

Agents operate strictly on sanitized projections of scored cases:

```
+-------------------------------------------------------------------------+
|                              Scoring Service                            |
| (Authoritative p, uncertainty u, novelty n, action, reason code)        |
+-------------------------------------------------------------------------+
                                     |
                                     v
                       [Quarantine Boundary]
              Rejects isFraud, target, TransactionID, TransactionDT
                                     |
                                     v
+-------------------------------------------------------------------------+
|                             AgentCaseView                               |
| - case_id (UUID / anonymized)                                           |
| - transaction_amt                                                       |
| - card_type, product_cd, addr1, dist1                                   |
| - posterior_prob (authoritative p)                                      |
| - disagreement_u (authoritative u)                                      |
| - novelty_score (authoritative n)                                       |
| - routing_action (authoritative Action)                                 |
| - reason_code (authoritative ReasonCode)                                |
+-------------------------------------------------------------------------+
                  |                                     |
                  v                                     v
         +-----------------+                  +-------------------+
         |   CaseCopilot   |                  |  AgentSupervisor  |
         | (Offline / LLM) |                  | (Policy Proposals)|
         +-----------------+                  +-------------------+
```

### 2.2 Case Copilot (`CaseCopilot`) & Dual Provider Architecture

The `CaseCopilot` generates structured triage briefs (`CopilotBrief`) explaining case characteristics, risk factors, and suggested investigation focus areas.

It supports dual provider modes:
- **`OfflineTemplateProvider` (Default):** Deterministic, reproducible, zero external dependencies, 100% offline. Generates structured briefs based strictly on calibrated probabilities and uncertainty metrics.
- **`ConfigurableLLMProvider`:** Interacts with local Ollama (`POST /api/generate`) or OpenAI-compatible endpoints (`POST /v1/chat/completions`). Includes built-in configurable timeouts, connection fallback to offline templates, and prompt hygiene.

#### Action Invariance Guarantee
Regardless of provider mode or agent execution outcome:
$$\text{Action}_{\text{with\_agent}} \equiv \text{Action}_{\text{without\_agent}}$$
$$\text{Reason}_{\text{with\_agent}} \equiv \text{Reason}_{\text{without\_agent}}$$

### 2.3 Agent Supervisor (`AgentSupervisor`) & Policy Proposal Isolation

The `AgentSupervisor` monitors operational health and model behavior. When suggesting threshold adjustments or policy refinements:
- It produces an immutable `Proposal` with status `ProposalStatus.AWAITING_HUMAN_APPROVAL`.
- It cannot modify `FrozenPolicyConfig` or alter active routing thresholds.
- All proposals require deterministic offline replay on historical validation holdouts and explicit human sign-off before consideration.

---

## 3. Deterministic Claim Verification (`AGNT-02`)

### 3.1 Claim Formulation & Operators

Agent briefs contain assertions about case attributes (e.g. "transaction amount is \$450.00", "posterior probability exceeds 0.08"). The `ClaimVerifier` formalizes these into typed `Claim` structures:

$$\text{Claim}(f, \text{op}, v)$$

Where $f$ is a field name in `AgentCaseView`, $\text{op} \in \{\text{eq}, \text{ne}, \text{lt}, \text{lte}, \text{gt}, \text{gte}, \text{in}\}$, and $v$ is the asserted value.

### 3.2 Verification Logic & Rejection Criteria

| Evaluation State | Condition | Consequence |
|---|---|---|
| **Supported** | Claim evaluates to `True` against evidence in `AgentCaseView` | Claim verified; provenance recorded |
| **Contradicted** | Claim evaluates to `False` against existing evidence | Claim flagged as CONTRADICTED; rejected from authoritative evidence |
| **Unsupported** | Target field $f$ is not present or inaccessible in `AgentCaseView` | Claim flagged as UNSUPPORTED; rejected from authoritative evidence |

### 3.3 Append-Only Claim Ledger (`ClaimLedger`)

All verified and rejected claims are recorded in an append-only ledger (`ClaimLedger`) tracking timestamp, brief ID, claim specification, verdict, and evidence context.

---

## 4. Cryptographic HMAC-SHA256 Audit Chain (`AGNT-03`)

### 4.1 Sequential Hash Chaining

The `AuditChain` implements sequential cryptographic hash chaining over canonical JSON representations of events:

For record $i = 0$ (Genesis):
$$\text{prev\_hash}_0 = \text{"0"}^{64}$$
$$H_0 = \text{HMAC-SHA256}(K, \text{prev\_hash}_0 \parallel \text{canonical\_payload}_0)$$

For record $i > 0$:
$$\text{prev\_hash}_i = H_{i-1}$$
$$H_i = \text{HMAC-SHA256}(K, \text{prev\_hash}_i \parallel \text{canonical\_payload}_i)$$

### 4.2 Key Management

The HMAC signing key is loaded from the environment variable:
`SIGNALGATE_AUDIT_KEY`

If unset, a secure 256-bit fallback key is generated for development environments with an explicit audit warning.

### 4.3 Tamper-Evident Verification (`verify_chain`)

The `verify_chain()` procedure validates the entire audit sequence:
1. Verifies genesis `prev_hash` equals `"0" * 64`.
2. Verifies sequential continuity: `record[i].prev_hash == record[i-1].record_hash`.
3. Recomputes HMAC-SHA256 over `prev_hash + canonical_json(payload)` and verifies exact equality with `record_hash`.
4. Returns boolean validity and detailed discrepancy diagnostics upon any failure.

### 4.4 Honest Audit Scope & Threat Model

> [!NOTE]
> **Audit Chain Cryptographic Guarantees:**
> - **Guaranteed:** Immediate detection of any modification, insertion, deletion, or reordering of records within the chain when verified with the authentic HMAC key.
> - **Guaranteed:** Cryptographic provenance linking each agent explanation, claim verification, and routing action to a specific event sequence.
> - **Not Claimed:** External hardware write-once-read-many (WORM) storage, decentralized blockchain consensus, or hardware security module (HSM) key isolation. The implementation provides verifiable software tamper-evidence for enterprise application logs.

---

## 5. Verification & Test Evidence

The Phase 6 implementation was comprehensively verified with unit and integration tests under `tests/test_ibm_agents.py`:

```
============================= test session starts =============================
platform win32 -- Python 3.11.9, pytest-9.1.1, pluggy-1.7.0
rootdir: C:\Users\himan\Downloads\zprject
collected 17 items

tests/test_ibm_agents.py::test_offline_template_provider_alert PASSED    [  5%]
tests/test_ibm_agents.py::test_offline_template_provider_disagreement PASSED [ 11%]
tests/test_ibm_agents.py::test_copilot_brief_generation PASSED           [ 17%]
tests/test_ibm_agents.py::test_copilot_action_invariance PASSED          [ 23%]
tests/test_ibm_agents.py::test_agent_view_leakage_prevention PASSED      [ 29%]
tests/test_ibm_agents.py::test_agent_view_allowed_fields PASSED         [ 35%]
tests/test_ibm_agents.py::test_claim_verifier_supported PASSED           [ 41%]
tests/test_ibm_agents.py::test_claim_verifier_contradicted PASSED        [ 47%]
tests/test_ibm_agents.py::test_claim_verifier_unsupported PASSED         [ 52%]
tests/test_ibm_agents.py::test_claim_ledger_append_only PASSED           [ 58%]
tests/test_ibm_agents.py::test_audit_chain_genesis PASSED                [ 64%]
tests/test_ibm_agents.py::test_audit_chain_sequential_linking PASSED     [ 70%]
tests/test_ibm_agents.py::test_audit_chain_tamper_detection PASSED       [ 76%]
tests/test_ibm_agents.py::test_audit_chain_broken_link_detection PASSED  [ 82%]
tests/test_ibm_agents.py::test_supervisor_proposal_isolation PASSED     [ 88%]
tests/test_ibm_agents.py::test_configurable_provider_fallback PASSED     [ 94%]
tests/test_ibm_agents.py::test_end_to_end_governed_triage_flow PASSED   [100%]

============================= 17 passed in 3.54s ==============================
```

Full repository regression verification: **177 passed in 19.71s** (0 regressions).
