# Requirements: SignalGate IBM Architecture Integration

**Defined:** 2026-10-18  
**Core Value:** Strictly bounded operational review capacity ($B = 130$ cases, $6.525\%$ touched rate) with zero silent clearance leaks under distribution shift, enforced through deterministic fail-closed policy routing and auditable evidence provenance.

## v1 Requirements

Requirements for the IBM Architecture Integration milestone. Each maps to a specific roadmap phase.

### Inventory & Baseline (Phase 1)

- [x] **INVN-01**: Comprehensive read-only inventory of working tree, Git status, reference files, licenses, and existing synthetic artifact hashes recorded in `docs/ibm_architecture_integration/00_inventory.md`.
- [x] **INVN-02**: Reference repository license and attribution terms verified with clean preservation of existing working files.

### Boundaries & Contracts (Phase 2)

- [x] **BNDR-01**: Isolated integration namespace established (`integrations/ibm_architecture/`) without overwriting active top-level synthetic code.
- [x] **BNDR-02**: Strongly typed mode contracts distinguishing `SYNTHETIC_SMOKE_ONLY`, `IEEE_CIS_OFFLINE_BENCHMARK`, and `LIVE_SOURCE_NOT_CONNECTED`.
- [x] **BNDR-03**: Sanitized `AgentCaseView` schema enforcing ground-truth quarantine (no `isFraud`, raw IDs, or raw timestamps).
- [x] **BNDR-04**: Automated tests for source-mode resolution and fail-closed handling on missing artifacts.

### Real Data Ingestion & Splits (Phase 3)

- [x] **DATA-01**: Reproducible real IEEE-CIS data loader with strict ground-truth quarantine and feature manifest validation.
- [x] **DATA-02**: Chronological temporal split partitioner generating 60% train, 10% calibration, 10% validation, and 20% test splits.
- [x] **DATA-03**: Data validation reports, split counts, and partition fingerprints persisted in separate namespace `results/ieee_cis_v1/`.

### Model Training & Calibration (Phase 4)

- [ ] **MODL-01**: Reproducible estimator pipeline supporting HistGradientBoosting and era-bagged heterogeneous ensemble on training split.
- [ ] **MODL-02**: Platt sigmoid calibration fitted strictly on calibration partition with reliability curve metrics.
- [ ] **MODL-03**: Disagreement signal calculator ($u, u_2$) and serialized artifacts persisted under `models/artifacts/ieee_cis_v1/`.

### Dynamic Scoring & Policy Governance (Phase 5)

- [ ] **SCOR-01**: Deterministic policy adapters supporting the router state machine, B2 top-budget baseline, and reference P5 candidate.
- [ ] **SCOR-02**: Capacity governor enforcing strict review quota ($B=130$) with deferred queue shunting (`R6_CAPACITY_DEFERRED`).
- [ ] **SCOR-03**: Deterministic scoring service providing single-case and batch scoring with fail-closed safety.

### Governed Agents & Cryptographic Audit (Phase 6)

- [ ] **AGNT-01**: Agent supervisor and Case Copilot supporting offline deterministic templates and optional configured live LLM providers.
- [ ] **AGNT-02**: Deterministic Claim Verifier and Claim Ledger enforcing supported claim schemas and rejecting false claims.
- [ ] **AGNT-03**: HMAC-SHA256 cryptographic audit chain with local secret management and tamper-evident verification.

### Drift Monitoring & Replay Gate (Phase 7)

- [ ] **DRFT-01**: Data-driven drift calculation (PSI and KS statistics) over real-data feature windows.
- [ ] **DRFT-02**: Drift Sentinel generating advisory configuration proposals restricted to allowlisted parameters.
- [ ] **DRFT-03**: Replay Gate requiring deterministic validation replay and explicit human approval (`AWAITING_HUMAN_APPROVAL`).

### FastAPI Service Integration (Phase 8)

- [ ] **APII-01**: REST endpoints exposing mode readiness, real model identity, cases, replay rows, policy comparison, and drift status.
- [ ] **APII-02**: Scoring sandbox endpoint executing real-data inference with strict input leakage rejection.
- [ ] **APII-03**: Replay Gate proposal inspection and approval endpoints with structured error handling.

### React Dashboard Integration (Phase 9)

- [ ] **DASH-01**: Three-state source mode indicator and switcher mounted across all 8 cockpit views.
- [ ] **DASH-02**: Genuine data binding for Overview KPIs, Case Explorer, Policy Comparison, and 3D Scoring Sandbox.
- [ ] **DASH-03**: Streaming Shift Storm telemetry, calculated Drift & Shift diagnostics, and verified Audit Trail chain inspection.

### Evaluation, Verification & Release (Phase 10)

- [ ] **EVAL-01**: Pre-evaluation freeze verification and immutable record creation prior to test partition evaluation.
- [ ] **EVAL-02**: Matched-capacity benchmark evaluation of B2 vs P5 across registered budgets with 1,000 paired bootstrap resamples.
- [ ] **EVAL-03**: End-to-end verification passing all Pytest tests, Vitest tests, TypeScript compilation, and route checks.
- [ ] **EVAL-04**: Delivery of `docs/ibm_architecture_integration/FINAL_INTEGRATION_REPORT.md` with honest capability classification.

## Out of Scope

| Feature | Reason |
|---------|--------|
| Hardware-attested IBM Secure Execution | Host environment is Windows 11 AMD64; attestation code functions as evidence parser |
| Live payment gateway connection | System is an offline decision-support and benchmark platform |
| Direct LLM scoring / numerical inference | Deterministic Python backend owns all calculations; agents are purely advisory |
| Automatic unsupervised model activation | Replay Gate enforces mandatory human approval |
| Overwrite of synthetic root artifacts | Canonical synthetic artifacts remain frozen to preserve backward compatibility |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| INVN-01 | Phase 1 | Complete |
| INVN-02 | Phase 1 | Complete |
| BNDR-01 | Phase 2 | Complete |
| BNDR-02 | Phase 2 | Complete |
| BNDR-03 | Phase 2 | Complete |
| BNDR-04 | Phase 2 | Complete |
| DATA-01 | Phase 3 | Complete |
| DATA-02 | Phase 3 | Complete |
| DATA-03 | Phase 3 | Complete |
| MODL-01 | Phase 4 | Pending |
| MODL-02 | Phase 4 | Pending |
| MODL-03 | Phase 4 | Pending |
| SCOR-01 | Phase 5 | Pending |
| SCOR-02 | Phase 5 | Pending |
| SCOR-03 | Phase 5 | Pending |
| AGNT-01 | Phase 6 | Pending |
| AGNT-02 | Phase 6 | Pending |
| AGNT-03 | Phase 6 | Pending |
| DRFT-01 | Phase 7 | Pending |
| DRFT-02 | Phase 7 | Pending |
| DRFT-03 | Phase 7 | Pending |
| APII-01 | Phase 8 | Pending |
| APII-02 | Phase 8 | Pending |
| APII-03 | Phase 8 | Pending |
| DASH-01 | Phase 9 | Pending |
| DASH-02 | Phase 9 | Pending |
| DASH-03 | Phase 9 | Pending |
| EVAL-01 | Phase 10 | Pending |
| EVAL-02 | Phase 10 | Pending |
| EVAL-03 | Phase 10 | Pending |
| EVAL-04 | Phase 10 | Pending |

**Coverage:**
- v1 requirements: 30 total
- Mapped to phases: 30
- Unmapped: 0 ✓

---
*Requirements defined: 2026-10-18*
*Last updated: 2026-10-18 after updating phase indices to 1-10*
