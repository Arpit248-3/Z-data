# Phase 9: Connect the Existing React Dashboards (Mode-Aware Cockpit)

## 1. Overview and Design Invariants

Phase 9 integrates the dynamic operating mode telemetry and backend governance services into the existing React + TypeScript + Vite frontend cockpit without disturbing the established visual identity, glassmorphic dark/light themes, or 3D WebGL assets.

### Core Architectural Invariants:
1. **Interactive 3-State Source Mode Switcher**:
   - `SYNTHETIC_SMOKE_ONLY`: Active operational demonstration mode (green indicator).
   - `IEEE_CIS_OFFLINE_BENCHMARK`: Explicitly labeled **DEFERRED** due to the host's 8 GB physical RAM limit (amber indicator).
   - `LIVE_SOURCE_NOT_CONNECTED`: Explicitly labeled **DISCONNECTED** (slate/neutral indicator).
2. **Strict Disclosure and Fail-Closed Modal**: Selecting an unavailable or deferred mode activates a transparent disclosure modal detailing why the mode cannot be activated. The application **never** silently substitutes synthetic data while displaying a real-data label.
3. **Preservation of 3D Visual Assets**: The Three.js Planar Radar (`ModelCard3DVisualizer.tsx`), 3D Decision Orb (`SandboxDecisionOrb3D.tsx`), and Signal Core GLTF pipeline remain fully functional with responsive fallbacks.
4. **Zero Regressions Across All 8 Routes**:
   - `/overview`: Executive KPI cards, workload multiple badges, and shift performance.
   - `/shift-storm`: Streaming playback across scenarios S0–S4.
   - `/case-explorer`: Case filtering and drill-down into signals and features.
   - `/policy-comparison`: Canonical B2 vs P5 benchmark comparison under identical review budgets.
   - `/sandbox`: Real-time transaction scoring with leakage rejection and audit logging.
   - `/drift-shift`: PSI/KS drift indicators and distribution divergence charts.
   - `/audit-trail`: Cryptographic audit log viewer with export capabilities.
   - `/model-card`: Provenance, feature manifests, and 3D decision boundary visualizer.

---

## 2. Implemented Components

### 2.1 Mode Switcher (`frontend/src/components/ModeSwitcher.tsx`)
- Mounted prominently in the persistent `TopBar` across all routes.
- Fetches real-time mode states from `/api/modes` via `api.getModes()`.
- Dropdown menu allows inspection of all 3 supported modes, their readiness states, and descriptions.
- Modal dialog triggers on clicking deferred IEEE-CIS mode or disconnected live feed, clearly citing the 8 GB host RAM constraint and offline forensic scope.

### 2.2 Extended Frontend API Layer (`frontend/src/lib/api/`)
- `frontend/src/lib/api/types.ts`: Added typed interfaces for `ModeDetail`, `ModesOverviewResponse`, `ModeSelectResponse`, `DriftReportResponse`, and `ReplayProposalRecord`.
- `frontend/src/lib/api/client.ts`: Added client endpoints:
  - `api.getModes()`: Queries mode readiness and active status.
  - `api.selectMode()`: Requests mode activation (fails closed with structured error).
  - `api.getDrift()`: Fetches scenario drift diagnostics.
  - `api.getProposals()`, `api.validateProposal()`, `api.approveProposal()`: Replay Gate governance.
  - `api.verifyAuditChain()`: Cryptographic audit integrity verification.

---

## 3. Verification and Test Results

Frontend build and test results:
- **Vitest Unit and Integration Tests**:
  - `src/components/__tests__/phase10_quality.test.ts`: 6 tests PASSED
  - `src/components/__tests__/pipeline_glb_integration.test.ts`: 6 tests PASSED
  - `src/components/__tests__/sandbox_instrument_glb_integration.test.ts`: 6 tests PASSED
  - `src/components/__tests__/status_and_metrics.test.ts`: 3 tests PASSED
  - **Total**: 21 of 21 Vitest tests passed.
- **TypeScript Compilation (`tsc`)**: Passed with 0 errors.
- **Vite Production Build (`vite build`)**: Transformed 2,440 modules, generated all CSS/JS bundles, chunked Three.js assets, and verified production distribution in `dist/`.
