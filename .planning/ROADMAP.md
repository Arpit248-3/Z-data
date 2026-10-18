# Roadmap: SignalGate IBM Architecture Integration

## Overview

This roadmap defines the complete, dependency-aware integration of the reference architecture from `reference/architecture/IBM-main` into the existing SignalGate platform.

### Strategic Execution Update: Synthetic-First Continuation
Due to physical memory constraints on the local development host (7.75 GB total physical RAM) and upcoming project submission deadlines, full IEEE-CIS model training and large-scale dataset preprocessing are temporarily **DEFERRED**. The integration milestone proceeds using a **Synthetic-First** strategy:
- Phases 4 through 10 implement and validate all architectural components (model adapters, policy routers, capacity governors, governed agents, claim verifiers, cryptographic audit chains, drift sentinels, replay gates, FastAPI endpoints, and React 3D dashboards) using the existing, verified synthetic-mode models, fixtures, and frozen policies.
- Real-data requirements and full benchmark evaluation remain explicitly marked **DEFERRED** or **BLOCKED** behind hardware preflight gates.
- Operating modes remain strictly separate: `SYNTHETIC_SMOKE_ONLY` (active), `IEEE_CIS_OFFLINE_BENCHMARK` (deferred), and `LIVE_SOURCE_NOT_CONNECTED` (disconnected). Never silently fall back between modes, and never report synthetic outputs as real-data benchmark results.

## Phases

- [x] **Phase 1: Safe Baseline and Repository Inventory** - Inventory Git state, existing synthetic artifacts, reference files, licenses, and environment baselines (`docs/ibm_architecture_integration/00_inventory.md`).
- [x] **Phase 2: Isolated Integration Package and Mode Contracts** - Establish isolated namespace (`integrations/ibm_architecture/`) and typed contracts for source modes, models, and sanitized agent views (`docs/ibm_architecture_integration/01_boundaries.md`).
- [x] **Phase 3: Real IEEE-CIS Data Ingestion and Temporal Partitions** - Implement reproducible data loading, strict feature leakage quarantine, and chronological temporal splits (`docs/ibm_architecture_integration/02_data.md`).
- [x] **Phase 4: Synthetic-First Model Integration Interfaces & Safe Bundle Adapters** - Implement model adapters, Platt calibration, disagreement signals, safe bundle loader, and provenance manifests using verified synthetic artifacts; defer full IEEE-CIS ensemble training (`docs/ibm_architecture_integration/03_model.md`).
- [x] **Phase 5: Dynamic Scoring, Baselines, Frozen Policy and Capacity Governance (Synthetic Mode)** - Implement multi-policy adapters (router, B2, P5), review capacity quotas ($B=130$), and fail-closed scoring services adapting existing frozen policies and synthetic models (`docs/ibm_architecture_integration/04_scoring_policy.md`).
- [ ] **Phase 6: Governed Agents, Claim Verification and Cryptographic Audit Chain (Synthetic Mode)** - Integrate sanitized `AgentCaseView`, Case Copilot, deterministic Claim Ledger, and HMAC-SHA256 audit chain using synthetic transaction streams (`docs/ibm_architecture_integration/05_agents_audit.md`).
- [ ] **Phase 7: Drift Monitoring and Controlled Scenario Replay (Synthetic Mode)** - Calculate feature-window PSI/KS drift, generate advisory proposals, and enforce Replay Gate human approvals across synthetic shift scenarios (`docs/ibm_architecture_integration/06_drift_replay.md`).
- [ ] **Phase 8: FastAPI Integration (Explicit Operating Mode Telemetry)** - Expose mode readiness, synthetic models, cases, replay telemetry, drift diagnostics, and sandbox scoring via FastAPI with explicit deferred status for real data (`docs/ibm_architecture_integration/07_api.md`).
- [ ] **Phase 9: Connect the Existing React Dashboards (Mode-Aware Cockpit)** - Wire all 8 dashboard routes to dynamic endpoints, add 3-state source mode switcher, and preserve 3D WebGL assets and themes (`docs/ibm_architecture_integration/08_frontend.md`).
- [ ] **Phase 10: Synthetic-Mode End-to-End Validation, Final Report & Acceptance Gates** - Execute synthetic-mode pre-evaluation freeze, paired bootstrap benchmarks, full-suite verification, and publish final report with explicit deferred benchmark disclosures (`docs/ibm_architecture_integration/09_evaluation_release.md` & `FINAL_INTEGRATION_REPORT.md`).

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

### Phase 4: Synthetic-First Model Integration Interfaces & Safe Bundle Adapters
**Goal**: Implement and validate model integration interfaces in `SYNTHETIC_SMOKE_ONLY` mode reusing existing verified synthetic artifacts (`hgb_base.joblib`, `calibrator_sigmoid.joblib`, `ensemble_members.joblib`, `residualizer_u2.joblib`); defer full IEEE-CIS model training due to physical RAM limitations.  
**Depends on**: Phase 3  
**Requirements**: MODL-01, MODL-02, MODL-03  
**Success Criteria** (what must be TRUE):
  1. `SyntheticModelAdapter` safely loads existing canonical synthetic artifacts without retraining or modifying canonical files.
  2. Ground-truth quarantine strictly enforced, prohibiting `isFraud`, `TransactionID`, and `TransactionDT` from model feature inputs.
  3. Prediction interfaces emit bounded probabilities in [0, 1] for baseline, consensus ensemble, Platt calibration, and non-negative disagreement signals ($u, u_2$).
  4. Model bundle manifest explicitly records `execution_mode: SYNTHETIC_SMOKE_ONLY`, `benchmark_comparable: false`, and `real_data_training_status: DEFERRED`.
  5. Full IEEE-CIS benchmark training is gated behind hardware preflight check in `scripts/train_full_benchmark.py` and marked DEFERRED/BLOCKED.
  6. Unit tests pass with 100% coverage of synthetic model integration interfaces and zero regression on existing suites.
  7. Deliverable written to `docs/ibm_architecture_integration/03_model.md`.
**Plans**: 1 plan
- [x] 04-01: Implement synthetic model adapter, safe bundle loader, explicit mode manifest, and integration tests.

### Phase 5: Dynamic Scoring, Baselines, Frozen Policy and Capacity Governance (Synthetic Mode)
**Goal**: Implement policy adapters for deterministic routing, B2 top-budget baseline, and P5 candidate, with strict review capacity quotas ($B=130$) adapting existing frozen policies and synthetic models.  
**Depends on**: Phase 4  
**Requirements**: SCOR-01, SCOR-02, SCOR-03  
**Success Criteria** (what must be TRUE):
  1. Policy adapters accurately evaluate router logic, baseline B2, and reference P5 using synthetic model predictions.
  2. Capacity governor enforces review quota ($B=130$) with deferred queue assignment (`R6_CAPACITY_DEFERRED`).
  3. Scoring service evaluates single-case and batch inputs, failing closed on invalid features.
  4. Real-data policy evaluation explicitly marked DEFERRED.
  5. Deliverable written to `docs/ibm_architecture_integration/04_scoring_policy.md`.
**Plans**: 1 plan
- [x] 05-01: Implement policy adapters, capacity governor integration, scoring service, and policy tests.

### Phase 6: Governed Agents, Claim Verification and Cryptographic Audit Chain (Synthetic Mode)
**Goal**: Integrate the agent supervisor, Case Copilot, deterministic Claim Ledger, and HMAC-SHA256 cryptographic audit chain using synthetic case streams.  
**Depends on**: Phase 5  
**Requirements**: AGNT-01, AGNT-02, AGNT-03  
**Success Criteria** (what must be TRUE):
  1. Case Copilot generates structured briefs from sanitized `AgentCaseView` without leakage.
  2. Claim Verifier accepts true verified claims and rejects seeded false claims.
  3. HMAC-SHA256 audit chain securely links decision events with tamper-evident verification.
  4. Agent failure or disabled status leaves deterministic case actions unchanged.
  5. Deliverable written to `docs/ibm_architecture_integration/05_agents_audit.md`.
**Plans**: 1 plan
- [x] 06-01: Implement agent supervisor, copilot briefs, claim ledger, and cryptographic audit chain.

### Phase 7: Drift Monitoring and Controlled Scenario Replay (Synthetic Mode)
**Goal**: Implement PSI/KS drift monitoring, advisory configuration proposals, and human-approved Replay Gate validation across synthetic shift scenarios (S1–S4).  
**Depends on**: Phase 6  
**Requirements**: DRFT-01, DRFT-02, DRFT-03  
**Success Criteria** (what must be TRUE):
  1. Drift engine computes PSI/KS statistics across feature windows without using ground-truth labels.
  2. Drift Sentinel produces advisory proposals restricted to allowlisted parameters.
  3. Replay Gate deterministically replays proposals against synthetic scenario data and requires explicit human sign-off.
  4. Real-data drift benchmarks explicitly marked DEFERRED.
  5. Deliverable written to `docs/ibm_architecture_integration/06_drift_replay.md`.
**Plans**: 1 plan
- [x] 07-01: Implement drift calculator, sentinel proposals, replay gate validator, and approval lifecycle.

### Phase 8: FastAPI Integration (Explicit Operating Mode Telemetry)
**Goal**: Connect the integration services into the existing FastAPI backend application, exposing explicit mode status and telemetry.  
**Depends on**: Phase 7  
**Requirements**: APII-01, APII-02, APII-03  
**Success Criteria** (what must be TRUE):
  1. Endpoints provide verified access to mode readiness (`SYNTHETIC_SMOKE_ONLY` active, `IEEE_CIS_OFFLINE_BENCHMARK` deferred, `LIVE_SOURCE_NOT_CONNECTED` disconnected).
  2. Scoring sandbox endpoint enforces recursive leakage rejection and writes to audit log.
  3. Replay Gate inspection and approval endpoints operate with strict validation.
  4. Backend integration test suite passes with zero regressions to existing endpoints.
  5. Deliverable written to `docs/ibm_architecture_integration/07_api.md`.
**Plans**: 1 plan
- [x] 08-01: Mount integration routers, extend Pydantic schemas, wire services, and execute API test suite.

### Phase 9: Connect the Existing React Dashboards (Mode-Aware Cockpit)
**Goal**: Connect all 8 React dashboard routes to dynamic API endpoints, add the 3-state source mode switcher, and preserve 3D visualizers and styling.  
**Depends on**: Phase 8  
**Requirements**: DASH-01, DASH-02, DASH-03  
**Success Criteria** (what must be TRUE):
  1. Three-state mode switcher (`SYNTHETIC_SMOKE_ONLY`, `IEEE_CIS_OFFLINE_BENCHMARK`, `LIVE_SOURCE_NOT_CONNECTED`) mounted and functional across all routes with clear deferred disclosure for IEEE-CIS.
  2. Overview, Case Explorer, Policy Comparison, Sandbox, Replay, Drift, Audit, and Model Card views display real API data from active synthetic mode.
  3. Three.js Planar Radar and 3D Decision Orb animate properly with responsive fallbacks.
  4. Vitest tests and TypeScript compilation pass with zero errors.
  5. Deliverable written to `docs/ibm_architecture_integration/08_frontend.md`.
**Plans**: 1 plan
- [x] 09-01: Update frontend API clients, add mode switcher, bind data to pages, and verify UI components.

### Phase 10: Synthetic-Mode End-to-End Validation, Final Report & Acceptance Gates
**Goal**: Execute synthetic-mode pre-evaluation freeze verification, paired bootstrap benchmark evaluation, full-stack verification, and deliver the final release report with honest capability disclosures.  
**Depends on**: Phase 9  
**Requirements**: EVAL-01, EVAL-02, EVAL-03, EVAL-04  
**Success Criteria** (what must be TRUE):
  1. Pre-evaluation freeze record verified prior to test set evaluation.
  2. B2 vs P5 evaluated under identical synthetic test records and budgets with 1,000 paired bootstrap resamples.
  3. Full verification passes (Pytest, Vitest, TypeScript, build, demo start/stop scripts).
  4. `docs/ibm_architecture_integration/09_evaluation_release.md` and `FINAL_INTEGRATION_REPORT.md` delivered with accurate capability status and explicit deferred status for real-data benchmark.
**Plans**: 1 plan
- [x] 10-01: Execute synthetic benchmark evaluation, run full test suites, verify demo launcher, and publish release report.

---

## Progress

**Execution Order:**
Phases execute in numeric order: 1 → 2 → 3 → 4 → 5 → 6 → 7 → 8 → 9 → 10

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| Phase 1: Safe Baseline and Repository Inventory | 1/1 | Complete | 2026-10-18 |
| Phase 2: Isolated Integration Package and Mode Contracts | 1/1 | Complete | 2026-10-18 |
| Phase 3: Real IEEE-CIS Data Ingestion and Temporal Partitions | 1/1 | Complete | 2026-10-18 |
| Phase 4: Synthetic-First Model Integration Interfaces & Safe Bundle Adapters | 1/1 | Complete | 2026-10-18 |
| Phase 5: Dynamic Scoring, Baselines, Frozen Policy and Capacity Governance (Synthetic Mode) | 1/1 | Complete | 2026-10-18 |
| Phase 6: Governed Agents, Claim Verification and Cryptographic Audit Chain (Synthetic Mode) | 1/1 | Complete | 2026-10-18 |
| Phase 7: Drift Monitoring and Controlled Scenario Replay (Synthetic Mode) | 1/1 | Complete | 2026-10-18 |
| Phase 8: FastAPI Integration (Explicit Operating Mode Telemetry) | 1/1 | Complete | 2026-10-18 |
| Phase 9: Connect the Existing React Dashboards (Mode-Aware Cockpit) | 1/1 | Complete | 2026-10-18 |
| Phase 10: Synthetic-Mode End-to-End Validation, Final Report & Acceptance Gates | 1/1 | Complete | 2026-10-18 |

---
*Roadmap updated: 2026-10-18 (Synthetic-First GSD Continuation - Milestone Complete)*  
*Governed by: docs/ibm_architecture_integration_master_spec.md*
