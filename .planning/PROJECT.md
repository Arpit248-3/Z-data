# SignalGate: Shift-Aware Fraud Triage Platform

## What This Is

SignalGate is an open, verifiable, shift-aware fraud triage platform that couples calibrated gradient-boosted risk estimation with epistemic disagreement measurement and hard operational capacity governance. This milestone integrates the reference architecture from `reference/architecture/IBM-main` into the existing production React + TypeScript + Vite + Three.js frontend and FastAPI backend, introducing genuine real IEEE-CIS data ingestion, governed agent supervisors/copilots, cryptographic HMAC-SHA256 audit chains, and human-approved replay gating without breaking or overwriting the working synthetic application.

## Core Value

Strictly bounded operational review capacity ($B = 130$ cases, $6.525\%$ touched rate) with zero silent clearance leaks under distribution shift, enforced through deterministic fail-closed policy routing and auditable evidence provenance.

## Business Context

- **Customer:** Fraud triage operations teams, risk engineering units, and financial security compliance officers operating under hard analyst review constraints.
- **Revenue model:** Open-source verifiable core for institutional risk compliance and decision-support auditing.
- **Success metric:** 100% capacity-bounded triage enforcement ($B=130$), zero unmonitored fraud leakage to routine clearance, and sub-50ms inference latency (AC5).
- **Strategy notes:** Governed by `docs/ibm_architecture_integration_master_spec.md` and `DESIGN.md`.

## Requirements

### Validated

- ✓ FastAPI REST backend serving health, status, overview, policies, replay rows, cases, and scoring sandbox — `backend/app/`
- ✓ HistGradientBoosting risk estimator with Platt Sigmoid probability calibration — `models/base.py`, `models/calibrate.py`
- ✓ Rank-residualized epistemic disagreement calculation ($u_2$) — `models/ensemble.py`
- ✓ Deterministic policy router with reason codes (R0-R6) and fail-closed safety — `policy/router.py`
- ✓ Analyst review capacity governor enforcing budget quota ($B=130$) with deferred queue shunting — `policy/governor.py`
- ✓ React 18 single-page dashboard with Dark Obsidian and Light Slate themes — `frontend/src/`
- ✓ 2.5D WebGL/Three.js Planar Radar disk (Signal Core) with SVG vector fallback — `frontend/src/components/SignalCoreScene.tsx`
- ✓ 3D WebGL Decision Orb for sandbox scoring — `frontend/src/components/SandboxDecisionOrb3D.tsx`
- ✓ Shift storm replay telemetry scrubber across 2,000 synthetic test rows — `frontend/src/features/shift-storm/`
- ✓ Automated regression test coverage with 109 passing Pytest tests and 21 passing Vitest tests — `tests/`, `frontend/src/components/__tests__/`

### Active

- [ ] Phase 1: Safe Baseline and Repository Inventory (`00_inventory.md`)
- [ ] Phase 2: Isolated Integration Package and Mode Contracts (`01_boundaries.md`)
- [ ] Phase 3: Real IEEE-CIS Data Ingestion, Leakage Checks and Temporal Partitions (`02_data.md`)
- [ ] Phase 4: Reproducible Model Training, Calibration and Artifacts (`03_model.md`)
- [ ] Phase 5: Dynamic Scoring, Baselines, Frozen Policy and Capacity Governance (`04_scoring_policy.md`)
- [ ] Phase 6: Governed Agents, Claim Verification and Cryptographic Audit Chain (`05_agents_audit.md`)
- [ ] Phase 7: Data-Driven Drift Monitoring, Advisory Proposals and Human-Approved Replay Gate (`06_drift_replay.md`)
- [ ] Phase 8: FastAPI Integration (`07_api.md`)
- [ ] Phase 9: Connect the Existing React Dashboards (`08_frontend.md`)
- [ ] Phase 10: Benchmark Validation, End-to-End Verification and Acceptance Gates (`09_evaluation_release.md` & `FINAL_INTEGRATION_REPORT.md`)

### Out of Scope

- Hardware-attested IBM Secure Execution / LinuxONE s390x execution — Host environment is Windows 11 AMD64; attestation verification is evaluated as an evidence parser (`security/tee_policy.py`), not a hardware hypervisor attestation.
- Live payment network connection or automated transaction blocking/settlement — System is an offline decision-support and benchmark control room (`SYNTHETIC_SMOKE_ONLY` / `IEEE_CIS_OFFLINE_BENCHMARK`).
- LLM direct numerical calculation — Language models are strictly advisory for summaries and explanations; deterministic backend Python code computes all numbers, scores, rankings, and decisions.
- Automatic unsupervised model activation — Drift Sentinel proposals require mandatory human approval through Replay Gate (`AWAITING_HUMAN_APPROVAL`).
- Overwriting existing synthetic artifacts — `config.yaml`, `policy/frozen_policy.json`, and `results/results.json` remain preserved in their original synthetic smoke state; real IEEE-CIS artifacts live in dedicated `ieee_cis_v1` namespaces.

## Context

- **Platform Environment:** Microsoft Windows 11, CPython 3.13.7, Node.js v20.20.0, Vite 5.4.11, React 18.3.1, Three.js 0.160.0.
- **Reference Codebase:** Located locally at `reference/architecture/IBM-main` (read-only reference containing candidate policies, agents, audit chains, drift sentinels, and evaluation protocols).
- **Existing Architecture Map:** Documented in 7 structured files under `.planning/codebase/` (`STACK.md`, `INTEGRATIONS.md`, `ARCHITECTURE.md`, `STRUCTURE.md`, `CONVENTIONS.md`, `TESTING.md`, `CONCERNS.md`).

## Constraints

- **Evidence Modes:** Must explicitly distinguish and report `SYNTHETIC_SMOKE_ONLY`, `IEEE_CIS_OFFLINE_BENCHMARK`, and `LIVE_SOURCE_NOT_CONNECTED`.
- **Ground-Truth Quarantine:** Target `isFraud` and identifiers `TransactionID`, `TransactionDT` must never enter the feature matrix, inference payloads, or agent views.
- **Deterministic Core:** Numerical scores, calibration, routing, and quota governance must execute deterministically; agent failure or disabled status must never alter case outcomes.
- **Frozen Evidence Protection:** Existing synthetic benchmarks, models, test-look ledgers, and configurations must remain intact without overwrite.
- **No Fabricated Telemetry:** Real-time data streams and live bank feeds must never be simulated; unverified metrics must display explicit unavailable states.

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Isolated Integration Namespace (`backend/app/integrations/ibm_architecture/`) | Prevents collision with existing working synthetic packages and models | — Pending |
| Separate IEEE-CIS Artifact Namespace (`models/artifacts/ieee_cis_v1/`, `results/ieee_cis_v1/`) | Protects canonical frozen synthetic evidence from accidental overwrite | — Pending |
| Fail-Closed Mode Selection | If real IEEE-CIS dataset or model bundle is missing, fail closed to safe error rather than silent synthetic fallback | — Pending |
| Sanitized `AgentCaseView` DTO | Ensures zero target label or sensitive raw feature leakage reaches LLM prompts | — Pending |
| HMAC-SHA256 Audit Chain with Local Secret | Cryptographically chains decision events while protecting secrets outside version control | — Pending |
| Mandatory Replay Gate Human Approval | Prevents automated model drift adaptation without human sign-off | — Pending |

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition** (via `/gsd-transition`):
1. Requirements invalidated? → Move to Out of Scope with reason
2. Requirements validated? → Move to Validated with phase reference
3. New requirements emerged? → Add to Active
4. Decisions to log? → Add to Key Decisions
5. "What This Is" still accurate? → Update if drifted

**After each milestone** (via `/gsd-complete-milestone`):
1. Full review of all sections
2. Core Value check — still the right priority?
3. Audit Out of Scope — reasons still valid?
4. Update Context with current state

---
*Last updated: 2026-10-18 after updating phase indices to 1-10*
