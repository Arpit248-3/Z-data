# SignalGate: UI/UX Pro Max Design Audit & Cockpit Architecture Report

**Audit Type:** Static Reference vs. React Application Shell Design Audit (Read-Only)  
**Date:** 2026-10-17  
**Auditor:** Principal Design Systems Engineer & Security Operations UI Architect  
**Design Reference:** Stitch Design System (*"The Decision Control Room"*)  
**Target Codebase:** `frontend/` (React 18.3.1 + Vite 5.4.11 + Three.js / R3F v8 + Vanilla CSS)  
**Scope Notice:** Read-Only Audit. No application code, backend services, ML models, or evaluation artifacts have been modified.

---

## 1. Executive Summary & Design Posture

SignalGate is a mission-critical fraud triage decision intelligence platform engineered for security operations center (SOC) analysts, risk engineers, and fraud investigators operating under high shift pressures.

The exported Stitch designs establish a coherent, authoritative visual identity termed **"The Decision Control Room"**. This aesthetic combines **technical brutalism** with **calibrated modern utility**:
- Deep cockpit darkness calibrated to mitigate cognitive fatigue during 12-hour analyst triage rotations.
- High-density data matrices, hairline 1px structural boundaries, and zero reliance on soft shadows or superficial glows.
- Surgical semantic decision colors (Coral, Amber, Sage Green, and Muted Violet) mapped directly to operational truth states.
- Monospaced typography for immutable technical entities (hashes, seeds, timestamps, transaction IDs).
- Strict operational provenance signaling (e.g. `SYNTHETIC_SMOKE_ONLY`) to prevent cross-contamination between test fixtures and production ledgers.

While the current Phase 7 React implementation successfully established the foundational application shell, backend health connectivity, and WebGL 3D capability, it noticeably drifts from the Stitch references toward **generic consumer SaaS conventions** (e.g., standard vertical collapsible navigation, soft cyan glowing drop-shadows, 8px–16px rounded corners, and abstract orbiting 3D spheres rather than an operational routing flow).

This audit identifies the structural and visual differences across all four primary screens and formulates a **prioritised 5-pillar correction plan** to align the production frontend with the high-density SOC standard.

---

## 2. Inventory of Inspected Reference Artifacts

The audit conducted direct, side-by-side inspections of the following Stitch design exports and active frontend application files:

### Stitch Design Export References
| Reference File | Type | Key Role & Content Inspected |
|:---|:---:|:---|
| [`the_decision_control_room/DESIGN.md`](file:///c:/Users/arpit/Desktop/project/docs/stitch_designs/stitch_signalgate_fraud_triage_platform/the_decision_control_room/DESIGN.md) | Markdown | Authoritative tokens: surface hierarchy, semantic decision palette, type scales (`IBM Plex Sans` + `Courier Prime`), zero-shadow rule, 4px corner radius discipline. |
| [`operational_overview/screen.png`](file:///c:/Users/arpit/Desktop/project/docs/stitch_designs/stitch_signalgate_fraud_triage_platform/operational_overview/screen.png) | Image | Visual ground truth: Top navigation header, operational context sidebar, 4-card KPI band, 3-stage Signal Core Routing Topology, and 3-column tri-pane operational grid. |
| [`operational_overview/code.html`](file:///c:/Users/arpit/Desktop/project/docs/stitch_designs/stitch_signalgate_fraud_triage_platform/operational_overview/code.html) | HTML/CSS | Structural markup: Tailwind CSS token configurations, 12-column layout grid, gauge meters, SVG distribution sparkline, and persistent bottom telemetry footer. |
| [`shift_storm_replay/screen.png`](file:///c:/Users/arpit/Desktop/project/docs/stitch_designs/stitch_signalgate_fraud_triage_platform/shift_storm_replay/screen.png) | Image | Visual ground truth: Replay timeline scrubber with storm spike markers, playback speed bar, interactive journey topology canvas, and right-hand deep inspection dossier. |
| [`shift_storm_replay/code.html`](file:///c:/Users/arpit/Desktop/project/docs/stitch_designs/stitch_signalgate_fraud_triage_platform/shift_storm_replay/code.html) | HTML/CSS | Structural markup: Split 2-pane stage (9 cols) vs deep dossier (3 cols), packet flow SVG stream layer, 4 destination lanes, and bottom micro-event stream preview. |
| [`case_explorer/screen.png`](file:///c:/Users/arpit/Desktop/project/docs/stitch_designs/stitch_signalgate_fraud_triage_platform/case_explorer/screen.png) | Image | Visual ground truth: 65/35 master-detail table-to-dossier split, query syntax input (`query:`), status filter chips, active row highlighting, and SHAP explainability bars. |
| [`case_explorer/code.html`](file:///c:/Users/arpit/Desktop/project/docs/stitch_designs/stitch_signalgate_fraud_triage_platform/case_explorer/code.html) | HTML/CSS | Structural markup: High-density event table, tabular lining figures, pagination controls, cryptographic verification badges, and analyst decision override action buttons. |
| [`policy_comparison/screen.png`](file:///c:/Users/arpit/Desktop/project/docs/stitch_designs/stitch_signalgate_fraud_triage_platform/policy_comparison/screen.png) | Image | Visual ground truth: 3-column architecture benchmark cards, matched-capacity trade-off curve (Recall vs. Shift Budget), and epistemic uncertainty formulation block. |
| [`policy_comparison/code.html`](file:///c:/Users/arpit/Desktop/project/docs/stitch_designs/stitch_signalgate_fraud_triage_platform/policy_comparison/code.html) | HTML/CSS | Structural markup: Vector SVG coordinate chart with confidence bands, budget cap boundary marker at 180 reviews, and 5-fold cross-validation metric matrix. |

### Active React Frontend Implementation Files
| Target File | Language | Inspected Scope |
|:---|:---:|:---|
| [`frontend/src/styles/tokens.css`](file:///c:/Users/arpit/Desktop/project/frontend/src/styles/tokens.css) | CSS | Surface colors, border tokens, glow shadows, typography definitions, radius scale. |
| [`frontend/src/styles/global.css`](file:///c:/Users/arpit/Desktop/project/frontend/src/styles/global.css) | CSS | Reset rules, scrollbar styling, focus outlines, `prefers-reduced-motion`. |
| [`frontend/src/styles/layout.css`](file:///c:/Users/arpit/Desktop/project/frontend/src/styles/layout.css) | CSS | App shell, sidebar layout, top bar layout, content padding, responsive breakpoints. |
| [`frontend/src/styles/components.css`](file:///c:/Users/arpit/Desktop/project/frontend/src/styles/components.css) | CSS | Card primitives, metric cards, status badges, button gradients, 3D container styling. |
| [`frontend/src/app/AppShell.tsx`](file:///c:/Users/arpit/Desktop/project/frontend/src/app/AppShell.tsx) | TSX | Application layout framing, mobile drawer trigger, outlet positioning. |
| [`frontend/src/components/Sidebar.tsx`](file:///c:/Users/arpit/Desktop/project/frontend/src/components/Sidebar.tsx) | TSX | Vertical navigation grouping (Operations, Intelligence, Governance), backend status box. |
| [`frontend/src/components/TopBar.tsx`](file:///c:/Users/arpit/Desktop/project/frontend/src/components/TopBar.tsx) | TSX | Breadcrumb hierarchy, local system clock, API status indicator. |
| [`frontend/src/components/SignalCoreScene.tsx`](file:///c:/Users/arpit/Desktop/project/frontend/src/components/SignalCoreScene.tsx) | TSX | Three.js / R3F 3D canvas, orbiting signal spheres, threshold rings, destination cubes. |
| [`frontend/src/components/SignalCoreFallback.tsx`](file:///c:/Users/arpit/Desktop/project/frontend/src/components/SignalCoreFallback.tsx) | TSX | 2D SVG vector fallback, concentric threshold rings, node selection states. |
| [`frontend/src/features/overview/OverviewPage.tsx`](file:///c:/Users/arpit/Desktop/project/frontend/src/features/overview/OverviewPage.tsx) | TSX | Active hero card, 3D container, readiness grid, 4-stage pipeline sequence, metric cards. |
| [`frontend/src/features/shift-storm/ShiftStormPage.tsx`](file:///c:/Users/arpit/Desktop/project/frontend/src/features/shift-storm/ShiftStormPage.tsx) | TSX | Deferred placeholder state. |
| [`frontend/src/features/case-explorer/CaseExplorerPage.tsx`](file:///c:/Users/arpit/Desktop/project/frontend/src/features/case-explorer/CaseExplorerPage.tsx) | TSX | Deferred placeholder state. |
| [`frontend/src/features/policy-comparison/PolicyComparisonPage.tsx`](file:///c:/Users/arpit/Desktop/project/frontend/src/features/policy-comparison/PolicyComparisonPage.tsx) | TSX | Deferred placeholder state. |

---

## 3. Screen-by-Screen Design Comparison

### 3.1. Global Cockpit Shell (Sidebar, Top Navigation & Persistent Status Bar)

```
STITCH DESIGN SHELL:
+-------------------------------------------------------------------------------------------------------------------------+
| [LOGO] SIGNALGATE   [SYNTHETIC_SMOKE_ONLY]  | OVERVIEW | SHIFT STORM | CASE EXPLORER | POLICY COMP |  [SHIFT CAPACITY] [USER]| (64px Top Header)
+-------------------------------------------------------------------------------------------------------------------------+
| OPERATIONAL CONTEXT |                                                                                                   |
| Queue: 142 Pending  |   MAIN COCKPIT STAGE                                                                              |
| Anomaly: +14.8%     |   (High-Density Multi-Pane 12-Column Grid)                                                        |
|---------------------|                                                                                                   |
| INVESTIGATION RAILS |                                                                                                   |
| > Control Stage     |                                                                                                   |
| > Telemetry Insp.   |                                                                                                   |
| > Simulation Engine |                                                                                                   |
| > Threshold Matrix  |                                                                                                   |
|---------------------|                                                                                                   |
| [Air-Gapped Sandbox]|                                                                                                   |
+-------------------------------------------------------------------------------------------------------------------------+
| EVALUATION DATASET: SYNTH_SMOKE_BATCH_8921 // LATENCY: 4.2ms // SEED: 0x9F4A // AUDIT INTEGRITY: VERIFIED     [CLUSTER_04] | (28px Bottom Bar)
+-------------------------------------------------------------------------------------------------------------------------+
```

- **Stitch Reference Architecture:**
  - **Top Header (`h-16` / 64px):** Serves as the primary horizontal navigation bar (`Overview`, `Shift Storm Replay`, `Case Explorer`, `Policy Comparison`). Houses brand identity, active dataset flag (`EVIDENCE: SYNTHETIC_SMOKE_ONLY`), active shift throughput load (`SHIFT-04: PEAK ASIA-PACIFIC / CAPACITY 84% ACTIVE`), gateway version (`GATEWAY v2.4-STABLE`), quick audit trigger, and analyst profile.
  - **Left Rail Sidebar (`w-64` / 256px):** Acts as a dedicated **Operational Context & Sub-Stage Rail**. Contains real-time queue pressure badges (`TRIAGE QUEUE: 142 PENDING`, `ANOMALY RATE: +14.8%`), investigation rail selector (Control Stage, Telemetry Inspector, Simulation Engine, Threshold Matrix), and an unyielding **Air-Gapped Sandbox** status block.
  - **Persistent Telemetry Footer (`h-7` / 28px):** Fixed bottom status bar providing tamper-evident operational provenance (`EVALUATION DATASET: SYNTH_SMOKE_BATCH_8921 // LATENCY: 4.2ms // SEED: 0x9F4A // AUDIT INTEGRITY: VERIFIED`) and active cluster identification.
- **Current React Application:**
  - **Sidebar:** Implements a standard SaaS collapsible sidebar containing 8 vertical links organized into accordion groups (*Operations*, *Intelligence*, *Governance*). It lacks the operational context queue telemetry and air-gapped status container.
  - **TopBar:** Contains only breadcrumbs, a local digital clock, and a tiny API health pill. Primary navigation is completely absent from the top bar.
  - **Footer:** Completely missing. No persistent provenance footer exists.
- **Impact & Gap:** The React layout functions as a standard web application rather than an industrial operations console. Analysts lose continuous visibility over shift budget saturation, environment air-gapping, and audit verification hashes while navigating across views.

---

### 3.2. Operational Overview Screen

- **Stitch Reference (`operational_overview`):**
  - **Top Banner:** High-priority warning ribbon (`ENVIRONMENT: SYNTHETIC_SMOKE_ONLY // Deterministic Seed: 0x9F4A_B89`) with terminal icon.
  - **KPI Telemetry Band:** 4 compact cards with dual data lines:
    1. *Incoming Caserate:* Current rate (`14,820 / hr`), delta (`+4.8%`), micro-progress bar, baseline vs. peak telemetry.
    2. *Analyst Queue Capacity:* Critical saturation alert (`180 cases/hr`, `94.2% [SATURATED]`, red progress bar, headroom `10/hr`).
    3. *Deferral Ratio (Held):* Violet indicator (`12.4%`, `1,840 cases`, dampener buffer status).
    4. *Precision @ Recall 90%:* Teal indicator (`98.14%`, `±0.04% SEED`).
  - **Signal Core Routing Topology:** Horizontal 3-stage flow visual:
    - *Stage 01 // Raw Ingestion:* Batch ID, median RPS, payload fail rate.
    - *Stage 02 // Dual-Model Decomposition:* Model A (GBDT, AUC 0.988) vs Model B (Transformer, AUC 0.991) progress bars; Epistemic Disagreement ($\Delta\text{Spread} = 0.384$) vs Threshold ($\tau = 0.42$).
    - *Stage 03 // Capacity-Aware Gate Router:* 4 distinct destination lane cards (Fraud Alert coral `#F27870`, Manual Review amber `#E8B35E`, Routine Clear green `#68C99A`, Held/Deferred violet `#B4A0F8`).
  - **Tri-Pane Lower Operational Stage:**
    - *Col 1 (4 cols):* Human Review Capacity gauge (10-segment stepped bar with pulsing saturation block, dynamic dampener status, latency SLA comparison).
    - *Col 2 (4 cols):* Active Scenario Profile (Disagreement spread distribution curve with $\tau = 0.42$ threshold marker line, top synthesized reason vectors: Geo Mismatch 42%, Velocity Spike 31%, Device Anomaly 27%).
    - *Col 3 (4 cols):* Live Case Sentinel (Compact table of high-urgency synthetic queue entities with status dot indicators and case scores).
- **Current React Application (`OverviewPage.tsx`):**
  - Displays a large hero card with gradient borders, followed by the 3D canvas container (`SignalCoreScene`), a dependency readiness grid, a 4-step linear block row, a 4-card outcome grid, and a 4-card metric section at the bottom.
  - Metrics render simple labels without micro-progress bars, baseline comparison subtext, or capacity saturation meters.
  - Lacks the 3-column operational cockpit (Human Review Capacity gauge, SVG disagreement curve, and Live Case Sentinel).
- **Impact & Gap:** The React overview is organized as a promotional dashboard rather than an actionable triage cockpit. High-priority telemetry (analyst queue saturation, disagreement distribution, and live urgent cases) is missing from the primary viewport.

---

### 3.3. Shift Storm Replay Screen

- **Stitch Reference (`shift_storm_replay`):**
  - **Replay Control Strip:**
    - Scenario selector dropdown (`SYNTH_PEAK_SURGE_CROSS_BORDER_BURST`).
    - Dedicated transport controls: Reset, Step-Back, `RUN REPLAY` (bold teal action button), Step-Forward.
    - Speed multiplier selector: `0.5x`, `1x`, `2x`, `5x`, `MAX`.
    - High-density timeline scrubber: Frame counter (`482 / 1200`), simulation time (`00:14:32 / 01:00:00`), interactive progress track with color-coded **storm spike markers** (red for bursts, violet for capacity saturation, slate for tail drift).
    - Shift budget gauge: `12 / 180 SLOTS FREE`, `ACTIVE DISPATCH: CAPACITY-SENSITIVE`.
  - **Dual-Pane Cockpit Split (9 cols Canvas / 3 cols Dossier):**
    - *Left Stage:* Multi-stage journey matrix with dot-grid canvas background, SVG packet stream pipeline, and active highlighted route lane (`LANE 03: HELD / DEFERRED`). Includes bottom mini-event preview strip (`#EVT-78399` to `#EVT-78403`).
    - *Right Dossier Panel:* Deep dossier inspection panel showing Packet ID `#SYNTH-EVT-78401`, composite risk (`0.684`), dual-model comparison bars, reason code diagnostics (`RC-702`), SHAP feature attribution bars, cryptographic audit hash with copy affordance, and action overrides (Accept Deferral, Force Manual Escalation).
- **Current React Application (`ShiftStormPage.tsx`):**
  - A static placeholder card with a clock icon stating `"Deferred to Phase 8"`.
  - No timeline scrubber, no transport bar, no scenario selector, and no split layout scaffolding.
- **Impact & Gap:** While deferral to Phase 8 was planned, the screen currently lacks the CSS layout grid, timeline component shell, and dossier inspection container required to house the Phase 8 engine seamlessly.

---

### 3.4. Case Explorer & Audit Triage Screen

- **Stitch Reference (`case_explorer`):**
  - **Telemetry Spark Band:** 6 dense metrics across the header (Eval Batch, Triage Velocity 14.8 req/s, Mean Disagreement 0.321 [HIGH], Capacity Shedding 38.4%, Audit Congruence 99.982%, Latency p99 6.14ms).
  - **Query & Utility Toolbar:**
    - Syntax query input (`query: disagreement:>0.30 status:ANY`) with dedicated `query:` prefix and `⌘K` keyboard shortcut badge.
    - Quick-filter preset pills (`Δ > 0.30`, `p > 0.70`, `SHIFT-04 PEAK`).
    - Action utilities: Export CSV, Re-Eval, Column Layout toggle.
  - **Status Triage Filter Chips:** Horizontal filter bar with count pills: `ALL` (1,200), `FRAUD ALERT` (342, red dot), `MANUAL REVIEW` (171, amber dot), `HELD / DEFERRED` (1,840, violet dot), `ROUTINE CLEAR` (12,467, green dot).
  - **Master-Detail 65/35 Split Layout:**
    - *Left (65% / 8 cols):* Dense data table with checkbox selection, Case ID, UTC timestamp, nominal value, risk $p$, disagreement $\Delta$, route action badge, reason code, and SHA-256 provenance verification icon. Active selected row features an uninterrupted surgical teal left accent indicator (`2px solid #68D8CB`).
    - *Right (35% / 4 cols):* Fixed Case Dossier card displaying batch provenance, dual-model decomposition bars, shift capacity shunt context, SHAP attribution vector bars, verifiable SHA-256 string, and analyst decision override action buttons.
  - **Footer:** Pagination controls with rows-per-page selector, entity count (`1-8 of 1,200 entities`), and numbered page buttons.
- **Current React Application (`CaseExplorerPage.tsx`):**
  - A static placeholder card stating `"Deferred to Phase 8"`.
  - Missing the 65/35 master-detail container, query syntax input bar, filter pill strip, and high-density table styles.
- **Impact & Gap:** When Phase 8 backend endpoints (`/api/cases`, `/api/cases/:id`) are wired, the frontend will require the complete 65/35 layout structure and table component hierarchy to match the reference.

---

### 3.5. Policy Comparison & Workload-Matched Benchmark Screen

- **Stitch Reference (`policy_comparison`):**
  - **Header & Action Strip:** Sub-header identifying evaluation suite and matched-capacity methodology (180 reviews/shift), with `Re-Simulate (n=12k)` and `Export Seeds & Runbook` buttons.
  - **3-Column Benchmark Architecture Cards:**
    - *Card 1 (Arch-01 Baseline):* Policy A Fixed Threshold ($p \ge 0.80$), Fraud Recall 71.4%, Critical Spill risk tag, unreviewed expiry explanation.
    - *Card 2 (Arch-02 Budget-Aware):* Policy B Top-Budget Ranking (B2), Fraud Recall 82.6%, Zero Overrun tag, silent drop explanation.
    - *Card 3 (Arch-03 Active Candidate):* SignalGate Architecture (Shift-Aware + Disagreement Buffer), Fraud Recall 94.1%, Managed (170/180) tag, epistemic queue explanation, highlighted in primary teal with `ACTIVE CANDIDATE` ribbon.
  - **Matched-Capacity Trade-off Chart:** Full-width vector SVG chart displaying Recall % vs. Shift Review Budget (50 to 250 cases/shift):
    - Background 40px grid pattern.
    - Y-axis guides (50% to 100%).
    - Vertical dashed boundary line at `BUDGET CAP: 180` (current capacity).
    - SignalGate confidence band polygon with teal gradient fill.
    - Three comparative curves: Policy A (dashed grey), Policy B (solid slate), SignalGate (bold teal).
    - Data callout badge at Budget 180: `+11.5% FRAUD CAPTURE DELTA` (94.1% vs 82.6%).
    - Micro-KPI summary row: Estimated Shift Friction, False Discovery Rate, Deferred Retention Accuracy.
  - **Epistemic Uncertainty & Formulation Deep Dive:**
    - *Left (7 cols):* Mathematical formulation block rendering the deterministic gate decision function in Courier Prime monospace.
    - *Right (5 cols):* Metric Benchmark Matrix comparing Policy B vs SignalGate across Fraud Recall, Analyst Precision, Max Shift Backlog, Silent Drop Rate, and Deferred Cases.
- **Current React Application (`PolicyComparisonPage.tsx`):**
  - A static placeholder card stating `"Deferred to Phase 8"`.
  - Missing the 3-column card grid, chart container, mathematical equation block, and metric comparison table.
- **Impact & Gap:** The core value proposition of SignalGate—workload-matched capacity comparison against frozen baselines B1–B4—has no visual presentation scaffolding.

---

## 4. The Five Highest-Impact Design Improvements

To elevate the SignalGate frontend from a generic prototype to an authoritative, SOC-grade operations console, the following five architectural improvements must be prioritized:

```
+----------------------------------------------------------------------------------------------------+
|                               THE 5 HIGHEST-IMPACT IMPROVEMENTS                                    |
+----------------------------------------------------------------------------------------------------+
| 1. Cockpit Shell Architecture: Unify Top Navigation, Operational Rail & Provenance Footer         |
| 2. Design System Tokens: Surgical Teal, Neutral Slate Surfaces & Zero-Shadow Discipline            |
| 3. Typography & Numerical Calibration: IBM Plex Sans, Courier Prime & Tabular Lining Figures       |
| 4. Signal Core Evolution: Transition from Abstract Orbiting 3D to 3-Stage Routing Flow HUD         |
| 5. Master-Detail Scaffolding: 65/35 & 9/3 Cockpit Split Containers for Phase 8 Data               |
+----------------------------------------------------------------------------------------------------+
```

### Improvement 1: Adopt the Unified Decision Control Room Cockpit Shell
- **Problem:** The current React app uses a standard SaaS collapsible left navigation bar with 8 vertical links and a top bar containing only breadcrumbs. This breaks analyst workflow by hiding the core operational modes and completely omitting shift capacity headroom, air-gapped status, and audit provenance.
- **Solution:** Re-architect `AppShell.tsx`, `Sidebar.tsx`, and `TopBar.tsx` into the 3-tier Stitch Control Room Shell:
  1. **Top Control Header (64px):** Move the 4 primary operational routes (`Overview`, `Shift Storm Replay`, `Case Explorer`, `Policy Comparison`) into horizontal top navigation tabs with an active bottom border (`2px solid #68D8CB`). Integrate the persistent `EVIDENCE: SYNTHETIC_SMOKE_ONLY` flag, shift load badge (`SHIFT-04: CAPACITY 84%`), gateway version tag, and analyst identity block.
  2. **Operational Rail Sidebar (256px):** Re-purpose the sidebar from a link list into an operational monitoring rail. Display live triage queue pending counts (142), anomaly velocity (+14.8%), investigation sub-rail anchors, and an immutable **Air-Gapped Sandbox** assurance card.
  3. **Fixed Telemetry Footer (28px):** Introduce a global bottom bar displaying dataset batch, seed, latency (4.2ms), and cryptographic hash chain verification.
- **Impact:** Eliminates navigation friction, aligns visual identity with SOC standards, and provides persistent operational context across all screens.

### Improvement 2: Calibrate Color Palette, Surface Tiering & Enforce the Zero-Shadow Rule
- **Problem:** The current CSS tokens rely on electric cyan (`#42E8F0`), blue-tinted surfaces (`#101624`), heavy ambient drop shadows (`--shadow-md`, `--shadow-lg`), glowing box-shadows, gradient buttons, and large rounded corners (8px, 12px, 16px). This creates a consumer SaaS or Web3 gaming aesthetic that contradicts the clinical, auditable tone mandated in `DESIGN.md`. Furthermore, HELD/DEFERRED is incorrectly styled in slate instead of the designated Muted Violet (`#B4A0F8`).
- **Solution:**
  1. Replace electric cyan with **Surgical Teal (`#68D8CB` / `#86F5E7`)** as the primary interactive accent.
  2. Map surfaces to neutral technical charcoal: Canvas `#0A0F14`, Tier 1 Surface `#111922`, Tier 2 Raised `#18232D`.
  3. Enforce the **Zero-Shadow Rule**: Remove all fuzzy box-shadows and glowing perimeters. Achieve visual depth strictly through 1px hairline boundaries (`#293743`) and surface contrast.
  4. Enforce strict **4px Corner Radius (`--radius-sm: 0.25rem`)** across all cards, badges, and action buttons (2px for checkboxes/micro-chips, 6px maximum for modals). Eliminate pill-shaped buttons.
  5. Correct the operational semantic decision colors:
     - **Fraud Alert / Critical Risk:** Restrained Coral (`#F27870` / `#FFB4AB`)
     - **Manual Review / Escalation:** Controlled Amber (`#E8B35E`)
     - **Epistemic Disagreement / Deferral:** Muted Violet (`#B4A0F8` / `#CDBDFF`)
     - **Routine / Verified Cleared:** Technical Sage Green (`#68C99A`)
- **Impact:** Instantly transforms the interface into a professional, high-precision security console while preserving high contrast (WCAG AAA compliant primary text `#EDF2F6`).

### Improvement 3: Implement Typography Hierarchy, Font Pairings & Tabular Figures
- **Problem:** The React app currently falls back to system sans-serif (`Segoe UI`, `-apple-system`) and generic monospace (`JetBrains Mono`, `Consolas`). Neither `IBM Plex Sans` nor `Courier Prime` is imported in `index.html`. Furthermore, numeric telemetry lacks `tabular-nums`, resulting in visual layout shift when values update.
- **Solution:**
  1. Add Google Fonts preconnect and import for `IBM Plex Sans` (weights 400, 500, 600, 700) and `Courier Prime` (weights 400, 700) to `frontend/index.html`.
  2. Update `tokens.css` to assign `IBM Plex Sans` to `--font-sans` and `Courier Prime` to `--font-mono`.
  3. Apply `font-variant-numeric: tabular-nums` globally to all tables, metric cards, timestamps, coordinates, and telemetry tickers.
  4. Establish tracked uppercase micro-labels (`0.6875rem` / 11px, `letter-spacing: 0.05em`) for category headers, badges, and status pillars.
- **Impact:** Enhances scan-speed during high-velocity incident triage and eliminates horizontal text wobble during real-time data updates.

### Improvement 4: Evolve Signal Core from Abstract Orbiting Spheres into an Actionable Routing Flow HUD
- **Problem:** The current 3D Signal Core (`SignalCoreScene.tsx`) renders an abstract solar system of orbiting colored spheres around an icosahedron. While visually smooth, it communicates zero operational value to an analyst—there are no ingestion statistics, model comparison bars, disagreement spreads, or capacity bounds visible in the 3D viewport.
- **Solution:**
  1. **Re-architect the 3D Scene:** Transform the scene layout from a radial orbit into a **directional stage-pipeline topology**:
     - *Inflow Zone:* Ingestion particle emitters representing transaction velocity ($84/\text{sec}$).
     - *Center Core:* Dual-model evaluation stage with visible comparison metrics and the epistemic divergence boundary ring ($\tau = 0.42$).
     - *Outflow Rails:* 4 physical destination conduits corresponding to the decision lanes (Fraud Alert, Manual Review, Routine Clear, Held/Deferred).
  2. **Telemetry HUD Overlay:** Overlay HTML/SVG telemetry callouts directly onto the canvas (similar to Stitch Stage 01–03), displaying packet IDs, model agreement bars, and queue saturation in real time.
  3. **Align 2D Fallback:** Update `SignalCoreFallback.tsx` from concentric circles to the exact 3-stage horizontal flow diagram specified in Stitch `operational_overview/code.html`.
- **Impact:** Converts an ornamental 3D animation into an authoritative visual decision router that explains *why* transactions are routed or deferred.

### Improvement 5: Scaffold High-Density Master-Detail Grids for Operations Screens
- **Problem:** `ShiftStormPage`, `CaseExplorerPage`, and `PolicyComparisonPage` are currently empty deferred placeholder cards. When Phase 8 commences, implementing both the data fetching logic and complex UI layouts simultaneously will introduce architectural bloat and design inconsistency.
- **Solution:** Implement the structural CSS grid layouts and UI scaffolding now:
  1. **Case Explorer:** Scaffold the 65/35 split grid with the high-density table container, query syntax input bar (`query:` prefix, `⌘K`), status filter pill strip, and right-hand dossier container (`#SYNTH-8921-003`).
  2. **Shift Storm Replay:** Scaffold the transport control bar (play/pause, step, speed selector, frame scrubber with storm spike marks) and the 9-column journey canvas + 3-column dossier split.
  3. **Policy Comparison:** Scaffold the 3-column architecture card grid, the SVG/Recharts capacity trade-off curve container (Recall vs. Budget Cap 180), and the mathematical formulation equation block.
- **Impact:** Decouples UI/UX presentation from backend integration, ensuring Phase 8 can connect data endpoints directly into validated, pixel-precise cockpit containers.

---

## 5. Recommended Shared Design Tokens

The following design tokens represent the definitive synthesis of the Stitch `"The Decision Control Room"` specification and modern CSS variable architecture, ready to replace `tokens.css`:

```css
:root {
  /* ==========================================================================
     1. Surface & Elevation Hierarchy (Neutral Charcoal / Slate Bedrock)
     ========================================================================== */
  --bg-canvas: #0A0F14;                  /* Zero-elevation bedrock floor */
  --bg-surface-primary: #111922;          /* Standard panel / grid plane */
  --bg-surface-raised: #18232D;           /* Elevated cards, drawers, toolbars */
  --bg-surface-elevated: #222E3B;         /* Active modals, popovers */
  --bg-surface-subdued: #0D131A;          /* Inset wells, code blocks, dark inputs */
  --bg-surface-header: #151F2A;          /* Anchored panel headers */
  --bg-overlay: rgba(10, 15, 20, 0.85);   /* Flat 85% opacity modal veil */

  /* ==========================================================================
     2. Hairline Structural Boundaries (Zero-Shadow Rule)
     ========================================================================== */
  --border-subtle: #1C2733;              /* Internal cell dividers */
  --border-default: #293743;             /* 1px precision card/table perimeter */
  --border-active: #3E5060;              /* Hovered or focused containers */
  --border-accent: #68D8CB;              /* Active selection indicator */

  /* ==========================================================================
     3. Primary Interactive Accent (Surgical Teal)
     ========================================================================== */
  --accent-primary: #68D8CB;             /* Primary interactive teal */
  --accent-primary-bright: #86F5E7;      /* Bright telemetry / hover state */
  --accent-primary-dim: #005D55;         /* Deep container fill */
  --accent-primary-tint: rgba(104, 216, 203, 0.12); /* Subtle badge tint */

  /* ==========================================================================
     4. Operational Semantic Spectrum (Decision Truth States)
     ========================================================================== */
  /* Fraud Alert / Critical Risk (Restrained Coral) */
  --color-fraud-alert: #F27870;
  --color-fraud-alert-dim: #93000A;
  --color-fraud-alert-tint: rgba(242, 120, 112, 0.12);

  /* Manual Review / Escalation (Controlled Amber) */
  --color-manual-review: #E8B35E;
  --color-manual-review-dim: #5C4308;
  --color-manual-review-tint: rgba(232, 179, 94, 0.12);

  /* Model Disagreement / Epistemic Deferral (Muted Violet) */
  --color-epistemic-defer: #B4A0F8;
  --color-epistemic-defer-dim: #352071;
  --color-epistemic-defer-tint: rgba(180, 160, 248, 0.14);

  /* Routine Cleared / Verified (Technical Sage Green) */
  --color-routine-clear: #68C99A;
  --color-routine-clear-dim: #004D36;
  --color-routine-clear-tint: rgba(104, 201, 154, 0.12);

  /* Secondary Telemetry / Neutral Slate */
  --color-telemetry-slate: #A2B0BC;
  --color-telemetry-dim: #3D4853;

  /* ==========================================================================
     5. Typography Scales & Roles
     ========================================================================== */
  --font-sans: 'IBM Plex Sans', -apple-system, BlinkMacSystemFont, sans-serif;
  --font-mono: 'Courier Prime', monospace;

  /* Text Sizes & Line Heights */
  --text-display: 1.75rem;     /* 28px / line-height: 2.25rem / tracking: -0.02em */
  --text-headline-lg: 1.25rem; /* 20px / line-height: 1.75rem / tracking: -0.01em */
  --text-headline-md: 1.125rem;/* 18px / line-height: 1.5rem */
  --text-headline-sm: 1rem;    /* 16px / line-height: 1.375rem */
  --text-body-lg: 0.9375rem;   /* 15px / line-height: 1.375rem */
  --text-body-md: 0.875rem;    /* 14px / line-height: 1.25rem */
  --text-body-sm: 0.8125rem;   /* 13px / line-height: 1.125rem */
  --text-label-md: 0.75rem;    /* 12px / line-height: 1rem / tracking: 0.04em */
  --text-label-sm: 0.6875rem;  /* 11px / line-height: 0.875rem / tracking: 0.06em */

  /* Text Colors (High Contrast) */
  --text-primary: #EDF2F6;     /* Ice white, WCAG AAA compliant */
  --text-secondary: #A2B0BC;   /* Cool slate for column headers and descriptions */
  --text-tertiary: #6E7E8D;    /* Muted micro-labels */
  --text-disabled: #424F5C;    /* Inactive states */
  --text-on-accent: #0A0F14;   /* High contrast dark text on surgical teal */

  /* ==========================================================================
     6. Disciplined Geometry & Spacing
     ========================================================================== */
  --radius-xs: 2px;            /* Checkboxes, indicator micro-pills */
  --radius-sm: 4px;            /* Standard for buttons, cards, inputs, table rows */
  --radius-md: 6px;            /* Maximum radius for dialogs and modals */

  /* 4px/8px Spacing Module */
  --space-1: 0.25rem;          /* 4px */
  --space-2: 0.5rem;           /* 8px */
  --space-3: 0.75rem;          /* 12px */
  --space-4: 1rem;             /* 16px */
  --space-5: 1.25rem;          /* 20px */
  --space-6: 1.5rem;           /* 24px */
  --space-8: 2rem;             /* 32px */

  /* ==========================================================================
     7. Elevation (Zero-Shadow Rule)
     ========================================================================== */
  --shadow-none: none;
  --elevation-ring: 0 0 0 1px var(--border-default);
  --elevation-ring-active: 0 0 0 1px var(--accent-primary);
  --elevation-modal: 0 0 0 1px var(--border-default);

  /* Layout Dimensions */
  --header-height: 64px;
  --sidebar-width: 256px;
  --footer-height: 28px;
}
```

---

## 6. Typography, Component & Spacing Rules

### 6.1. Typography Rules
1. **Lining Figures for All Metrics:** All tables, KPI values, latency badges, and timestamps must declare `font-variant-numeric: tabular-nums` to guarantee fixed character widths.
2. **Strict Monospace Categorization:** `Courier Prime` (`--font-mono`) is exclusively applied to:
   - System seeds (e.g., `0x9F4A_B89`) and SHA-256 hashes.
   - Transaction IDs (e.g., `#SYNTH-8921-003`) and Case IDs.
   - Raw UTC ISO timestamps (e.g., `14:02:18.102`).
   - Decision mathematical expressions (e.g., $\Delta\text{Spread} = 0.384$, $\tau = 0.42$).
   - Operational mode tags (e.g., `SYNTHETIC_SMOKE_ONLY`).
3. **Uppercase Micro-Labels:** Elements with `--text-label-sm` (11px) must enforce `text-transform: uppercase` and `letter-spacing: 0.05em`.

### 6.2. Component Architecture Rules
1. **Button Primitives:**
   - *Primary Interactive:* Solid background `#68D8CB`, text `#0A0F14` bold, radius 4px, height 32px or 36px. No shadows, no gradients.
   - *Tactical / Secondary:* Outlined with `1px solid #293743`, background `#18232D`, text `#EDF2F6`. Hover border transitions to `#68D8CB`.
   - *Destructive / Reject:* Outlined `1px solid #F27870`, background transparent, text `#F27870`. Hover shifts background to `rgba(242, 120, 112, 0.12)`.
2. **Status Badges & Decision Chips:**
   - Height fixed at 20px or 22px.
   - Composed of a 1px border and a 10% opacity tinted fill matching the semantic color.
   - Text size `0.6875rem` (11px) monospaced uppercase.
3. **Data Tables & Event Grids:**
   - Dedicated table header bar in `#18232D` with bottom border `1px solid #293743`.
   - Compact row height (36px–40px), dense vertical padding (`0.5rem 0.75rem`).
   - Active/selected row features an uninterrupted `2px solid #68D8CB` left accent tab.
4. **Cards & Inspector Panels:**
   - Flat background `#111922`, perimeter border `1px solid #293743`, radius 4px.
   - Dedicated anchored top bar with solid `#18232D` background (height 28px) containing categorical title and UTC timestamp.

### 6.3. Spacing Rhythm
- **Grid Module:** Pure 4px / 8px incremental spacing scale (`--space-1` = 4px, `--space-2` = 8px, `--space-3` = 12px, `--space-4` = 16px).
- **Zero Margins on Outer Containers:** Viewport outer gutters standardized at 16px (`1rem`) on desktop, 12px on compact laptops.

---

## 7. Responsive & Accessibility Requirements

### 7.1. Accessibility (WCAG 2.2 AA / AAA Compliance)
1. **Contrast Standards:**
   - Primary text (`#EDF2F6`) on surface slate (`#111922` / `#0A0F14`) achieves a contrast ratio of **13.5:1**, far exceeding WCAG AAA (7:1).
   - Secondary text (`#A2B0BC`) achieves **6.8:1**, comfortably exceeding WCAG AA (4.5:1).
   - Avoid using `#869391` on `#1B2025` for readable text; reserve it only for disabled or decorative guides.
2. **Keyboard Navigation & Visible Focus:**
   - Implement custom focus rings: `outline: 2px solid #68D8CB; outline-offset: 2px;` with zero blur.
   - The query search input must respond to the global `⌘K` / `Ctrl+K` keyboard shortcut to immediately focus the filter input.
   - Master-detail table rows must be fully traversable using Arrow Up / Arrow Down keys, with Space/Enter selecting the active case.
3. **Screen Reader Semantics:**
   - Decorative status dots (e.g. pulse indicators) must include `aria-hidden="true"`.
   - Dynamic telemetry updates (e.g. queue saturation warnings) must be wrapped in `aria-live="polite"` or `role="status"`.
   - Interactive icon-only buttons must have descriptive `aria-label` attributes (e.g., `aria-label="Export CSV"`, `aria-label="Reset Replay"`).

### 7.2. Reduced-Motion & Fallback Behaviour
1. **`prefers-reduced-motion: reduce` Support:**
   - Disable all pulsing animations (`animate-pulse`, `animate-ping`) on status indicators.
   - Automatically bypass the Three.js 3D canvas and render the 2D vector fallback (`SignalCoreFallback`) without requiring user intervention.
   - Ensure all CSS transitions snap immediately (`transition-duration: 0.01ms !important`).
2. **WebGL Fallback Robustness:**
   - Maintain the `WebGLErrorBoundary` wrapper around the 3D canvas. When WebGL context is lost or unavailable, automatically degrade to the high-density SVG pipeline without layout collapse.

### 7.3. Responsive Breakpoint Matrix
- **Wide SOC Monitors (1440px+):** Full 3-pane investigation flow active simultaneously. Split grids render at 65%/35% (Case Explorer) and 9 cols/3 cols (Shift Storm).
- **Field Laptops (1024px – 1439px):** Central stage remains prominent; the deep telemetry dossier collapses into a slide-over drawer triggered by clicking an inspection row.
- **Tablets / Field Mobile (<1024px):** Single-column stacked triage view with horizontal tab anchors switching between queue list, detail dossier, and decision dispatch actions.

---

## 8. Prioritised Correction Plan

To guide Phase 7.5 and prepare the foundation for Phase 8 without modifying production backend or evaluation data, the following phased execution roadmap is recommended:

| Priority | Action Item | Target Components / Files | Objective & Deliverable |
|:---:|:---|:---|:---|
| **P1** | **Global Design Tokens & Zero-Shadow Migration** | `frontend/src/styles/tokens.css`, `components.css`, `global.css` | Replace electric cyan with surgical teal (`#68D8CB`), neutral charcoal surfaces (`#0A0F14`, `#111922`, `#18232D`), remove glowing box-shadows, enforce 4px radius, map 4 semantic decision colors. |
| **P2** | **Typography Imports & Tabular Lining Numbers** | `frontend/index.html`, `frontend/src/styles/tokens.css` | Load Google Fonts `IBM Plex Sans` + `Courier Prime`. Enforce `font-variant-numeric: tabular-nums` globally across all telemetry and tables. |
| **P3** | **Cockpit Shell Architecture (Header, Rail & Footer)** | `frontend/src/app/AppShell.tsx`, `Sidebar.tsx`, `TopBar.tsx`, `layout.css` | Transform top bar into horizontal tab navigation (`Overview`, `Shift Storm`, `Case Explorer`, `Policy Comparison`) with shift capacity meter; re-purpose sidebar into operational rail; add 28px bottom provenance footer. |
| **P4** | **Signal Core Routing HUD Alignment** | `frontend/src/components/SignalCoreScene.tsx`, `SignalCoreFallback.tsx` | Align 3D scene and 2D vector fallback with the 3-stage routing flow (Ingestion $\to$ Decomposition $\to$ Capacity Gate Lanes) and add telemetry HUD overlays. |
| **P5** | **Cockpit Scaffolding for Deferred Pages** | `frontend/src/features/case-explorer/`, `shift-storm/`, `policy-comparison/` | Scaffold the 65/35 master-detail grid, replay timeline transport bar, and policy comparison chart containers so Phase 8 can connect data endpoints directly. |

---

## 9. Conclusion & Acceptance Verification

This design audit confirms that the static Stitch design references (`operational_overview`, `shift_storm_replay`, `case_explorer`, `policy_comparison`, and `DESIGN.md`) provide a comprehensive, aesthetically superior blueprint for financial security operations. 

By executing the **5 Highest-Impact Improvements** outlined above, SignalGate will shed its generic SaaS appearance and fully realize its intended identity: an authoritative, high-density, auditable **Decision Control Room**.

*Audit completed under strict read-only compliance. All existing tests and models remain untouched.*
