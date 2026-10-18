# Roadmap: SignalGate IBM Architecture Integration

## Overview

This roadmap defines the complete, dependency-aware integration of the reference architecture from `reference/architecture/IBM-main` into the existing SignalGate platform. Across 10 sequential phases, the integration establishes safe isolated boundaries, ingests real IEEE-CIS data with strict ground-truth quarantine, fits and calibrates reproducible ensemble models, connects governed policy routers and capacity governors, integrates agent supervisors with cryptographic audit chains, implements human-gated replay mechanisms, and connects dynamic backend services to the React 3D dashboard without replacing or breaking the existing synthetic application.

## Phases

- [x] **Phase 1: Safe Baseline and Repository Inventory** - Inventory Git state, existing synthetic artifacts, reference files, licenses, and environment baselines (`docs/ibm_architecture_integration/00_inventory.md`).
- [x] **Phase 2: Isolated Integration Package and Mode Contracts** - Establish isolated namespace (`integrations/ibm_architecture/`) and typed contracts for source modes, models, and sanitized agent views (`docs/ibm_architecture_integration/01_boundaries.md`).
- [ ] **Phase 3: Real IEEE-CIS Data Ingestion and Temporal Partitions** - Implement reproducible data loading, strict feature leakage quarantine, and chronological temporal splits (`docs/ibm_architecture_integration/02_data.md`).
- [ ] **Phase 4: Reproducible Model Training, Calibration and Artifacts** - Train HistGradientBoosting and era-bagged ensembles, fit Platt calibration on calib split, and serialize versioned artifacts (`docs/ibm_architecture_integration/03_model.md`).
- [ ] **Phase 5: Dynamic Scoring, Baselines, Frozen Policy and Capacity Governance** - Implement multi-policy adapters (router, B2, P5), review capacity quotas ($B=130$), and fail-closed scoring services (`docs/ibm_architecture_integration/04_scoring_policy.md`).
- [ ] **Phase 6: Governed Agents, Claim Verification and Cryptographic Audit Chain** - Integrate sanitized `AgentCaseView`, Case Copilot, deterministic Claim Ledger, and HMAC-SHA256 audit chain (`docs/ibm_architecture_integration/05_agents_audit.md`).
- [ ] **Phase 7: Data-Driven Drift Monitoring and Human-Approved Replay Gate** - Calculate feature-window PSI/KS drift, generate advisory proposals, and enforce Replay Gate human approvals (`docs/ibm_architecture_integration/06_drift_replay.md`).
- [ ] **Phase 8: FastAPI Integration** - Expose mode readiness, real models, cases, replay telemetry, drift diagnostics, and sandbox scoring via FastAPI (`docs/ibm_architecture_integration/07_api.md`).
- [ ] **Phase 9: Connect the Existing React Dashboards** - Wire all 8 dashboard routes to dynamic endpoints, add mode switcher, and preserve 3D WebGL assets and themes (`docs/ibm_architecture_integration/08_frontend.md`).
- [ ] **Phase 10: Benchmark Validation, End-to-End Verification and Acceptance Gates** - Execute pre-evaluation freeze, paired bootstrap benchmarks, full-suite verification, and publish final report (`docs/ibm_architecture_integration/09_evaluation_release.md` & `FINAL_INTEGRATION_REPORT.md`).

---

## Phase Details

### Phase 1: Safe Baseline and Repository Inventory
**Goal**: Establish a complete, verified baseline of the existing working repository, Git status, reference architecture files, licenses, and synthetic artifact hashes.  
**Depends on**: Nothing (first phase)  
**Requirements**: INVN-01, INVN-02  
**Success Criteria** (what must be TRUE):
  1. Complete inventory written to `docs/ibm_architecture_integration/00_inventory.md` recording working tree status, Git HEAD, and hashes.
  2. Reference architecture license, attribution requirements, and local dependencies verified.
  3. Safe integration branch or checkpoint established with zero modification to working synthetic code.
**Plans**: 1 plan
- [x] 01-01: Execute repository inventory, license check, and artifact hash auditing.

### Phase 2: Isolated Integration Package and Mode Contracts
**Goal**: Design and implement the isolated integration package and type-safe data contracts for multi-source evidence and sanitized agent views.  
**Depends on**: Phase 1  
**Requirements**: BNDR-01, BNDR-02, BNDR-03, BNDR-04  
**Success Criteria** (what must be TRUE):
  1. Isolated package directory created without overwriting active top-level modules.
  2. Typed contracts define explicit modes (`SYNTHETIC_SMOKE_ONLY`, `IEEE_CIS_OFFLINE_BENCHMARK`, `LIVE_SOURCE_NOT_CONNECTED`).
  3. `AgentCaseView` schema strictly excludes target `isFraud` and raw transaction identifiers.
  4. Unit tests pass verifying fail-closed mode resolution and missing artifact handling.
  5. Deliverable written to `docs/ibm_architecture_integration/01_boundaries.md`.
**Plans**: 1 plan
- [x] 02-01: Implement isolated integration namespace, mode enums, Pydantic schemas, and boundary tests.

### Phase 3: Real IEEE-CIS Data Ingestion and Temporal Partitions
**Goal**: Verify raw data availability, implement reproducible loading with ground-truth quarantine, and generate deterministic chronological splits.  
**Depends on**: Phase 2  
**Requirements**: DATA-01, DATA-02, DATA-03  
**Success Criteria** (what must be TRUE):
  1. Real IEEE-CIS data loader parses features with strict column exclusion (`isFraud`, `TransactionID`, `TransactionDT` quarantined).
  2. Chronological 60/10/10/20 train/calib/val/test splits generated deterministically.
  3. Validation reports and partition manifests stored in separate namespace `results/ieee_cis_v1/`.
  4. Deliverable written to `docs/ibm_architecture_integration/02_data.md`.
**Plans**: 1 plan
- [x] 03-01: Build IEEE-CIS data loader, feature manifest validator, temporal splitter, and split tests.

### Phase 4: Reproducible Model Training, Calibration and Artifacts
**Goal**: Train the verified base estimator and era-bagged ensemble on training data, fit Platt calibration on calibration split, and persist versioned artifacts.  
**Depends on**: Phase 3  
**Requirements**: MODL-01, MODL-02, MODL-03  
**Success Criteria** (what must be TRUE):
  1. Estimator pipeline fitted strictly on training partition without target or ID leakage.
  2. Platt sigmoid calibrator fitted strictly on calibration partition with reliability curves.
  3. Disagreement signals ($u, u_2$) computed and serialized to `models/artifacts/ieee_cis_v1/`.
  4. Deliverable written to `docs/ibm_architecture_integration/03_model.md`.
**Plans**: 1 plan
- [ ] 04-01: Implement training pipeline, ensemble fitting, calibration, and artifact serialization.

### Phase 5: Dynamic Scoring, Baselines, Frozen Policy and Capacity Governance
**Goal**: Implement policy adapters for deterministic routing, B2 top-budget baseline, and P5 candidate, with strict review capacity quotas.  
**Depends on**: Phase 4  
**Requirements**: SCOR-01, SCOR-02, SCOR-03  
**Success Criteria** (what must be TRUE):
  1. Policy adapters accurately evaluate router logic, baseline B2, and reference P5.
  2. Capacity governor enforces review quota ($B=130$) with deferred queue assignment (R6).
  3. Scoring service evaluates single-case and batch inputs, failing closed on invalid features.
  4. Deliverable written to `docs/ibm_architecture_integration/04_scoring_policy.md`.
**Plans**: 1 plan
- [ ] 05-01: Implement policy adapters, capacity governor integration, scoring service, and policy tests.

### Phase 6: Governed Agents, Claim Verification and Cryptographic Audit Chain
**Goal**: Integrate the agent supervisor, Case Copilot, deterministic Claim Ledger, and HMAC-SHA256 cryptographic audit chain.  
**Depends on**: Phase 5  
**Requirements**: AGNT-01, AGNT-02, AGNT-03  
**Success Criteria** (what must be TRUE):
  1. Case Copilot generates structured briefs from sanitized `AgentCaseView` without leakage.
  2. Claim Verifier accepts true verified claims and rejects seeded false claims.
  3. HMAC-SHA256 audit chain securely links decision events with tamper-evident verification.
  4. Agent failure or disabled status leaves deterministic case actions unchanged.
  5. Deliverable written to `docs/ibm_architecture_integration/05_agents_audit.md`.
**Plans**: 1 plan
- [ ] 06-01: Implement agent supervisor, copilot briefs, claim ledger, and cryptographic audit chain.

### Phase 7: Data-Driven Drift Monitoring and Human-Approved Replay Gate
**Goal**: Implement real-data PSI/KS drift monitoring, advisory configuration proposals, and human-approved Replay Gate validation.  
**Depends on**: Phase 6  
**Requirements**: DRFT-01, DRFT-02, DRFT-03  
**Success Criteria** (what must be TRUE):
  1. Drift engine computes PSI/KS statistics across feature windows without using ground-truth labels.
  2. Drift Sentinel produces advisory proposals restricted to allowlisted parameters.
  3. Replay Gate deterministically replays proposals against validation data and requires explicit human sign-off.
  4. Deliverable written to `docs/ibm_architecture_integration/06_drift_replay.md`.
**Plans**: 1 plan
- [ ] 07-01: Implement drift calculator, sentinel proposals, replay gate validator, and approval lifecycle.

### Phase 8: FastAPI Integration
**Goal**: Connect the new integration services into the existing FastAPI backend application under verified endpoints.  
**Depends on**: Phase 7  
**Requirements**: APII-01, APII-02, APII-03  
**Success Criteria** (what must be TRUE):
  1. Endpoints provide verified access to mode readiness, real model identity, cases, replay telemetry, drift reports, and sandbox scoring.
  2. Sandbox scoring endpoint enforces recursive leakage rejection and writes to audit log.
  3. Replay Gate inspection and approval endpoints operate with strict validation.
  4. Backend integration test suite passes with zero regressions to existing endpoints.
  5. Deliverable written to `docs/ibm_architecture_integration/07_api.md`.
**Plans**: 1 plan
- [ ] 08-01: Mount integration routers, extend Pydantic schemas, wire services, and execute API test suite.

### Phase 9: Connect the Existing React Dashboards
**Goal**: Connect all 8 React dashboard routes to dynamic API endpoints, add the 3-state source mode switcher, and preserve 3D visualizers and styling.  
**Depends on**: Phase 8  
**Requirements**: DASH-01, DASH-02, DASH-03  
**Success Criteria** (what must be TRUE):
  1. Three-state mode switcher (`SYNTHETIC_SMOKE_ONLY`, `IEEE_CIS_OFFLINE_BENCHMARK`, `LIVE_SOURCE_NOT_CONNECTED`) mounted and functional across all routes.
  2. Overview, Case Explorer, Policy Comparison, Sandbox, Replay, Drift, Audit, and Model Card views display real API data.
  3. Three.js Planar Radar and 3D Decision Orb animate properly with responsive fallbacks.
  4. Vitest tests and TypeScript compilation pass with zero errors.
  5. Deliverable written to `docs/ibm_architecture_integration/08_frontend.md`.
**Plans**: 1 plan
- [ ] 09-01: Update frontend API clients, add mode switcher, bind data to pages, and verify UI components.

### Phase 10: Benchmark Validation, End-to-End Verification and Acceptance Gates
**Goal**: Execute pre-evaluation freeze verification, paired bootstrap benchmark evaluation, full-stack verification, and deliver the final release report.  
**Depends on**: Phase 9  
**Requirements**: EVAL-01, EVAL-02, EVAL-03, EVAL-04  
**Success Criteria** (what must be TRUE):
  1. Pre-evaluation freeze record verified prior to test set evaluation.
  2. B2 vs P5 evaluated under identical test records and budgets with 1,000 paired bootstrap resamples.
  3. Full verification passes (Pytest, Vitest, TypeScript, build, demo start/stop scripts).
  4. `docs/ibm_architecture_integration/09_evaluation_release.md` and `FINAL_INTEGRATION_REPORT.md` delivered with accurate capability status.
**Plans**: 1 plan
- [ ] 10-01: Execute final benchmark evaluation, run full test suites, verify demo launcher, and publish release report.

---

## Progress

**Execution Order:**
Phases execute in numeric order: 1 → 2 → 3 → 4 → 5 → 6 → 7 → 8 → 9 → 10

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| Phase 1: Safe Baseline and Repository Inventory | 0/1 | Not started | - |
| Phase 2: Isolated Integration Package and Mode Contracts | 0/1 | Not started | - |
| Phase 3: Real IEEE-CIS Data Ingestion and Temporal Partitions | 0/1 | Not started | - |
| Phase 4: Reproducible Model Training, Calibration and Artifacts | 0/1 | Not started | - |
| Phase 5: Dynamic Scoring, Baselines, Frozen Policy and Capacity Governance | 0/1 | Not started | - |
| Phase 6: Governed Agents, Claim Verification and Cryptographic Audit Chain | 0/1 | Not started | - |
| Phase 7: Data-Driven Drift Monitoring and Human-Approved Replay Gate | 0/1 | Not started | - |
| Phase 8: FastAPI Integration | 0/1 | Not started | - |
| Phase 9: Connect the Existing React Dashboards | 0/1 | Not started | - |
| Phase 10: Benchmark Validation, End-to-End Verification and Acceptance Gates | 0/1 | Not started | - |

---
*Roadmap defined: 2026-10-18*
*Governed by: docs/ibm_architecture_integration_master_spec.md*
