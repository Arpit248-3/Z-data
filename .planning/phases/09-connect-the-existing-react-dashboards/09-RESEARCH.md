# Phase 9: Connect the Existing React Dashboards — Research & Architecture Analysis

**Governing Specification:** `docs/ibm_architecture_integration_master_spec.md` § C, § L
**Requirements:** `DASH-01`, `DASH-02`, `DASH-03`
**Target Directory:** `frontend/`

---

## 1. Existing Frontend Architecture

### Structure:
- **Build / Tooling:** Vite 5.4 + React 18.3 + TypeScript 5.6 + Vitest 2.1.
- **Styling:** CSS variables and modular stylesheets (`tokens.css`, `layout.css`, `components.css`, `global.css`, `animations.css`).
- **3D Assets:** Three.js 0.160 + React Three Fiber 8.17.
  - `frontend/public/models/model-pipeline.glb` (465 KB)
  - `frontend/public/models/sandbox-decision-orb.glb` (1.48 MB)
  - Both visualizers (`ModelCard3DVisualizer.tsx` and `SandboxDecisionOrb3D.tsx`) lazy-load with graceful fallbacks.
  - Vitest test suite (`pipeline_glb_integration.test.ts` and `sandbox_instrument_glb_integration.test.ts`) strictly asserts that `PIPELINE_STAGES` and parameters match canonical frozen specifications.
- **Routing:** React Router DOM 6.28 with 8 cockpit routes:
  1. `/overview` (`OverviewPage.tsx`)
  2. `/shift-storm` (`ShiftStormPage.tsx`)
  3. `/case-explorer` (`CaseExplorerPage.tsx`)
  4. `/policy-comparison` (`PolicyComparisonPage.tsx`)
  5. `/drift-shift` (`DriftShiftPage.tsx`)
  6. `/audit-trail` (`AuditTrailPage.tsx`)
  7. `/model-card` (`ModelCardPage.tsx`)
  8. `/sandbox` (`SandboxPage.tsx`)
- **API Client:** `frontend/src/lib/api/client.ts` with typed error handling via `ApiClientError`.
- **Baseline Test State:** 21 / 21 Vitest tests passing in 2.39s; `tsc --noEmit` exits with 0 errors.

---

## 2. Requirement Gap Analysis

| Requirement | Current State | Required Implementation |
| :--- | :--- | :--- |
| `DASH-01` (3-State Mode Indicator & Switcher) | Header (`TopBar.tsx`) and footer (`AppShell.tsx`) hardcode `SYNTHETIC_SMOKE_ONLY`. | Create `ModeContext.tsx` and `ModeSwitcher.tsx`. Expose `SYNTHETIC_SMOKE_ONLY`, `IEEE_CIS_OFFLINE_BENCHMARK`, and `LIVE_SOURCE_NOT_CONNECTED`. Mount switcher in `TopBar.tsx` across all 8 cockpit views. |
| `DASH-02` (Genuine Data Binding: Overview, Cases, Policies, Sandbox) | Pages call endpoints without `mode` parameter; sandbox uses synthetic baseline only. | Wire `mode` context into `OverviewPage`, `CaseExplorerPage`, `PolicyComparisonPage`, and `SandboxPage`. In `IEEE_CIS_OFFLINE_BENCHMARK` mode, sandbox executes real ensemble inference and displays versioned audit sequence. |
| `DASH-03` (Shift Storm, Drift Diagnostics, Audit Chain Inspection) | `DriftShiftPage` only renders static scenarios; `AuditTrailPage` lacks live cryptographic verification button. | Connect `GET /api/drift/report` to `DriftShiftPage` (showing live PSI, KS, Wasserstein distance, score drift, and notice). Connect `GET /api/audit/verify` to `AuditTrailPage` (providing live verification badge and error audit). |

---

## 3. Preservation Invariants

1. **3D Assets & Stage Definitions:**
   - Do NOT modify `PIPELINE_STAGES` in `ModelCard3DVisualizer.tsx` (tested by `pipeline_glb_integration.test.ts`).
   - Do NOT overwrite GLB files in `frontend/public/models/`.
2. **Zero Leakage Invariant:**
   - Case Explorer and Sandbox views must never display or accept `isFraud`, `target`, `label`, `TransactionID`, or `TransactionDT` in live scoring inputs.
3. **Fail-Closed Truthful Display:**
   - When `LIVE_SOURCE_NOT_CONNECTED` is selected, display truthful banner stating no live banking connection is active.
   - When backend is offline or bundle unverified, display clear actionable diagnostics.
4. **Regression Protection:**
   - All 21 existing Vitest tests must continue passing 100%.
   - Full TypeScript build (`tsc --noEmit`) must compile with zero errors.

---

## 4. Implementation Plan Outline

1. **Task 1: Extend API Types & Client Functions (`types.ts`, `client.ts`):**
   - Add contracts for `ModeReadinessResponse`, `ModelCardResponse`, `DriftReportResponse`, `AuditVerifyResponse`, and governance proposals.
   - Add client methods `getMode()`, `getModelCard(mode)`, `getDriftReport(mode)`, `verifyAuditChain()`, and pass `mode` to `scoreSandbox` and `getCases`.
2. **Task 2: Implement Mode Context & Switcher Component (`context/ModeContext.tsx`, `components/ModeSwitcher.tsx`):**
   - Build React Context managing 3-state operating mode with `localStorage` persistence and `/api/mode` readiness sync.
   - Mount `ModeSwitcher` in `TopBar.tsx` and update `AppShell.tsx` footer.
3. **Task 3: Dynamic Data Binding in Overview, Case Explorer, Policy Comparison, and Sandbox (`DASH-02`):**
   - Bind `mode` parameter to `CaseExplorerPage` and `SandboxPage`.
   - In Sandbox, display dual-mode inference telemetry, calibrated $p$, $u_2$, and audit sequence number.
4. **Task 4: Dynamic Drift Diagnostics & Cryptographic Audit Verification (`DASH-03`):**
   - Add live multi-metric drift monitor panel to `DriftShiftPage` connected to `/api/drift/report`.
   - Add cryptographic ledger verification panel to `AuditTrailPage` connected to `/api/audit/verify`.
   - Connect dynamic model card details to `ModelCardPage` while preserving `ModelCard3DVisualizer`.
5. **Task 5: Author Frontend Test Suite & Run Full Verifications:**
   - Author `frontend/src/components/__tests__/mode_switcher_and_api.test.ts`.
   - Verify all Vitest tests pass (25+ tests) and `npx tsc --noEmit` passes.
   - Run backend regression suite (all 215 tests pass).
6. **Task 6: Author Authoritative Deliverable Documentation:**
   - Author `docs/ibm_architecture_integration/08_frontend.md`.
