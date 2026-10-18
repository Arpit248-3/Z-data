# SignalGate: The Decision Control Room
## Authoritative Design System Specification & Visual Architecture

**Version:** 2.1.0-FINAL-CORRECTED  
**Phase:** Phase 7.5 — Authoritative Design System Consolidation (Final Accuracy Correction)  
**Target Platform:** SignalGate Shift-Aware Fraud Triage Platform  
**Target Codebase:** `frontend/` (React 18.3.1, TypeScript 5.6.3, Vite 5.4.11, Three.js / R3F v8, Vanilla CSS)  
**Status:** Canonical Design Specification (Documentation-Only, Read-Only Enforcement)

---

## 1. Executive Summary & Source-of-Truth Hierarchy

### 1.1 Product Design Identity
The visual identity for SignalGate is **"The Decision Control Room"**.

SignalGate is not an analytics dashboard where users passively browse vanity metrics, nor is it a Web3 terminal or science-fiction video game interface. It is an **active, auditable financial-security operations control room** engineered for fraud triage analysts, incident responders, and risk engineers operating under distribution shifts and strictly bounded human review budgets (primary evaluation budget: $1.5\times$ training prevalence $\approx 6.525\%$, evaluating to 130 manual reviews on the 2,000-row test partition; the Stitch mockup figure of 180 reviews was an illustrative visual placeholder).

The visual tone is **authoritative, clinical, auditable, and unyielding**:
- **Deep Cockpit Floor:** Neutral charcoal/slate zero-elevation baseline calibrated to mitigate cognitive fatigue during operational triage rotations.
- **Structural Precision:** Hairline 1px structural boundaries (`#293743`) and surface tiering without soft ambient drop shadows, blurred glows, or decorative button gradients.
- **Surgical Semantic Truth:** Decision colors (Coral, Amber, Muted Violet, Sage Green) map strictly to genuine operational routing outcomes and capacity states.
- **Tabular & Monospace Discipline:** Tabular figures for all real-time numbers; monospaced typography for machine identifiers, hashes, and mathematical expressions.
- **Dual 3D Purpose:** A compact, restrained architectural status anchor on the Overview page, contrasted with an immersive forensics stage on the Shift Storm Replay page.
- **Operational Reality:** Operates strictly on validated offline evaluation records and local synthetic fixtures (`SYNTHETIC_SMOKE_ONLY`). It is not air-gapped, is not connected to a live payment gateway, and does not process live payment network traffic.

### 1.2 Authoritative Source-of-Truth Hierarchy
When implementing frontend components, styles, and data bindings, developers and subagents must follow this strict five-tier resolution hierarchy:

```
+----------------------------------------------------------------------------------------------------+
|                               SOURCE-OF-TRUTH RESOLUTION HIERARCHY                                 |
+----------------------------------------------------------------------------------------------------+
| 1. STITCH EXPORTED SCREENS      | Actual screen exports define intended cockpit layouts & composition|
| 2. EXPORTED DESIGN TOKENS       | the_decision_control_room/DESIGN.md defines starting tokens        |
| 3. UI/UX PRO MAX AUDIT          | docs/ui_ux_audit.md sets component consistency & accessibility floor|
| 4. FRONTEND DESIGN REVIEW       | docs/frontend_design_review.md refines distinctiveness & anti-clichés|
| 5. BACKEND & DATA CONTRACTS     | docs/api_contract.md & results/*.json strictly constrain metrics   |
+----------------------------------------------------------------------------------------------------+
```

1. **Actual Stitch Screen Exports (`docs/stitch_designs/...`):** Establish the visual direction, 3-tier shell structure, and master-detail pane proportions.
2. **Exported Stitch Design System (`DESIGN.md` in Stitch folder):** Provides the starting surface, outline, and semantic color palette.
3. **UI/UX Pro Max Audit (`docs/ui_ux_audit.md`):** Establishes component modularity, spacing consistency, and WCAG accessibility requirements.
4. **Frontend Design Review (`docs/frontend_design_review.md`):** Refines distinctiveness, resolves audit conflicts, eliminates AI-generated clichés (such as uppercase overload and double-slash syntax clutter), and differentiates the 3D experiences.
5. **Existing React Routes & API Contracts (`docs/api_contract.md`, `config.yaml`, `policy/router.py`, `results/results.json`):** Constrains data binding. The frontend must never invent endpoints, live streaming data, SHAP explanations, analyst override writes, export actions, or performance metrics not supported by the verified backend.

---

## 2. Audit Conflict Resolutions & Visual Rules

Where previous audits or Stitch mockups exhibited stylistic or factual discrepancies, they are explicitly resolved as follows:

| Design Dimension | Stitch Mockup Trait | Audit Recommendation | Authoritative Resolution |
|:---|:---|:---|:---|
| **Primary Review Budget** | Hardcoded `180 cases/shift` or `180 cases/hr`. | Flagged capacity unverified against config. | **Canonical Evaluation Budget ($B = 0.06525$, 130 reviews):** Primary evaluation budget is strictly $1.5\times$ training prevalence ($4.35\%$) = $6.525\%$ touched rate (`primary_budget: 0.06525`), evaluating to **130 reviews** on the 2,000-row test partition (`results.json`). 180 reviews was an illustrative Stitch placeholder and must not be cited as the primary evaluation budget. |
| **Review Threshold ($t_{\text{review}}$)** | Early design reports and draft mockups cited $0.0400$ as an illustrative review threshold. | Discrepancy flagged against frozen policy tuning and actual router. | **Canonical Frozen Review Threshold ($t_{\text{review}} = 0.071002 \approx 0.0710$):** Canonical decision threshold tuning (`policy/frozen_policy.json`, `config.yaml`, `policy/router.py`, `results/results.json`) establishes $t_{\text{review}} = 0.071002$, $t_{\text{alert}} = 0.084705$, and $u_{\text{threshold}} = 0.526773$ under the primary $1.5\times$ workload budget ($B = 0.06525$). The value $0.0400$ was an early illustrative placeholder from exploratory drafts. All frontend components, radar HUDs, sandbox boundaries, and documentation strictly reflect $t_{\text{review}} = 0.071002$ ($0.0710$). |
| **Decision Semantics & Actions** | Labeled "BLOCK" and "CLEAR". | Map decision colors to 4 destination lanes. | **Decision-Support Action Enums:** High-risk routing ($p \ge t_{\text{alert}}$) produces `FRAUD_ALERT` (an operational escalation alert, not an automated direct block). Backend action enums are strictly `FRAUD_ALERT`, `MANUAL_REVIEW`, `ROUTINE`, `HELD`, and `DEFERRED`. Do not invent a `ROUTINE_CLEAR` enum (the backend enum is `ROUTINE`; user-facing label may be "Routine"). Keep `HELD` and `DEFERRED` distinct where exposed. |
| **Synthetic Recall & Benchmark Claims** | Highlighted `71.4%`, `82.6%`, `94.1%` recall, `+11.5% Delta`. | Prohibited copying mockup numbers. | **Synthetic Test-Look Reporting:** The metric $9.01\%$ (0.09009, 10 of 111 frauds caught) is a **synthetic evaluation test-look result** (`G3_LOOK_1` / `G5_LOOK_2_FINAL`) on the deterministic 2,000-row synthetic fixture (`SYNTHETIC_SMOKE_ONLY`). Point estimate delta vs. baseline B2 is $0.0\text{ pp}$ with an inconclusive 95% paired bootstrap CI $[-2.75\text{ pp}, +2.75\text{ pp}]$. It must never be cited as real-world performance or proof of superiority. |
| **Operational & Gateway Status** | Faux terminal tags: `AIR-GAPPED SANDBOX`, `GATEWAY v4.2`, live node cluster indicators. | Emphasized provenance accuracy. | **Honest Offline Status:** The system is an offline development environment running on synthetic fixtures. Do not claim it is air-gapped, processing live traffic, connected to a gateway, or running with verified audit integrity. Unverified telemetry, latency, seed, and infrastructure versions must display an `Unavailable` state or be omitted. |
| **Feature Functionality** | Rendered interactive SHAP bars, analyst override buttons, CSV export, live streaming. | Keep visual scaffolding distinct from real endpoints. | **Strict Feature Honesty:** SHAP explanations are disabled (`explanations.enabled: false`, API returns `DISABLED`). Analyst override writes have no backend write endpoint. Export actions have no backend endpoint. Replay streaming has no WebSocket/stream endpoint (only paginated row reads via `GET /api/replay/rows`). All such interactions must be displayed as disabled or static scaffolding. |
| **Heading Capitalization** | ALL CAPS everywhere (`INCOMING CASERATE`, `ANALYST QUEUE CAPACITY`). | Recommended tracked uppercase matching Stitch. | **Title Case for UI Headings:** Use clean Title Case (`Incoming Case Rate`, `Analyst Queue Capacity`, `Model Disagreement Spread`). Reserve uppercase strictly for machine acronyms (`UTC`, `AUC`, `RPS`, `SHAP`), system states (`FRAUD_ALERT`, `HELD`, `SYNTHETIC_SMOKE_ONLY`), and short code tokens. |
| **Terminal Syntax Clutter** | Double slashes (`//`) and middle dots (`•`) on all labels. | Preserved Stitch terminal formatting. | **Clean Structural Delimiters:** Remove faux-terminal `//` text strings. Use 1px vertical borders (`1px solid var(--border-default)`) or distinct badge containers. Use real CSS layout structure rather than keyboard characters. |
| **Routing Lane Colors** | All 4 lanes rendered in full saturated color simultaneously on the stage. | Mapped all 4 decision colors to destination lane cards. | **State-Dependent Accent Discipline:** Inactive destination lanes remain subdued in neutral slate (`#111922` with 1px border `#293743`). Only the *active target lane* (or selected filter state) carries its semantic border, badge, and color accent. Prevents the "circus dashboard" trap. |
| **3D Signal Core Scope** | Static 2D/3D flow mockup in Overview; separate stage in Replay. | Audit suggested replacing 3D spheres with a 3-stage flow HUD. | **Differentiated Dual 3D Footprint:** Retain Three.js/R3F in both screens with distinct roles: **Overview** uses a compact, restrained status anchor (~220–240px) integrated into the top flow; **Shift Storm Replay** uses an expansive 9-column trajectory particle stage synchronized with the timeline scrubber. |
| **Card Nesting & Corners** | Cards nested inside cards with 8px–16px rounded corners. | Standardized on 4px radius, flagged card sprawl. | **Flat Structural Tiering & 4px Radius:** Maximum corner radius of 4px (`0.25rem`) for cards, buttons, and tables; 2px for checkboxes and micro-badges; 6px maximum for dialogs. Eliminate nested card boxes in favor of borderless high-contrast panels. |
| **Information Density** | High density, but with microscopic 8px–10px text in places. | Emphasized high-density telemetry. | **Readable Density Floor:** Minimum font size of 11px (`0.6875rem`) for metadata, 13px (`0.8125rem`) for body text, with generous 16px–24px gutters between major functional zones. |

---

## 3. Authoritative Colour System

The color system is strictly functional, mapping exact hex values to operational truth states. Decorative gradients and ambient blurs are prohibited.

### 3.1 Surface & Structural Hierarchy
```css
/* Zero-Elevation Canvas Bedrock */
--bg-canvas: #0A0F14;                  /* Deep charcoal bedrock floor */

/* Tier 1 Surface: Standard Panels & Data Grids */
--bg-surface-primary: #111922;          /* Primary cockpit panel surface */

/* Tier 2 Raised Surface: Elevated Cards, Toolbars & Active Rows */
--bg-surface-raised: #18232D;           /* Inspection drawers, hovered rows, toolbars */

/* Tier 3 Elevated Surface: Modals & Flyouts */
--bg-surface-elevated: #222E3B;         /* Dialog dialogs, context popovers */

/* Subdued Surface: Code Blocks & Inset Wells */
--bg-surface-subdued: #0D131A;          /* Inset terminal wells, 3D canvas backing */

/* Header Surface: Anchored Panel Headers */
--bg-surface-header: #151F2A;          /* Anchored card title bars */

/* Modal Backdrop Veil */
--bg-overlay: rgba(10, 15, 20, 0.85);   /* Flat 85% opacity modal veil */

/* Precision Hairline Boundaries (Zero-Shadow Rule) */
--border-subtle: #1C2733;              /* Internal cell dividers */
--border-default: #293743;             /* 1px precision structural perimeter */
--border-active: #3E5060;              /* Hovered containers or interactive borders */
```

### 3.2 Primary Interactive Accent (Surgical Teal)
```css
--accent-primary: #68D8CB;             /* Primary interactive teal (buttons, active tabs) */
--accent-primary-bright: #86F5E7;      /* Focus rings, highlighted telemetry values */
--accent-primary-dim: #005D55;         /* Deep container borders / active fills */
--accent-primary-tint: rgba(104, 216, 203, 0.12); /* Subtle chip backgrounds */
```

### 3.3 Operational Semantic Spectrum (Decision Truth States)
```css
/* 1. Fraud Alert / High Risk Escalation (Restrained Coral) */
/* Backend Action Enum: FRAUD_ALERT | Reason: R1_HIGH_RISK */
/* Decision-support escalation alert, NOT an automated direct execution block */
--color-fraud-alert: #F27870;          /* Fraud alert, consensus high risk */
--color-fraud-alert-bright: #FFB4AB;   /* High-visibility alert text */
--color-fraud-alert-dim: #93000A;      /* Dark alert border */
--color-fraud-alert-tint: rgba(242, 120, 112, 0.12); /* Badge fill */

/* 2. Manual Review / Escalation (Controlled Amber) */
/* Backend Action Enum: MANUAL_REVIEW | Reasons: R0, R2, R3, R4 */
--color-manual-review: #E8B35E;        /* Human-in-the-loop review queue cost */
--color-manual-review-bright: #F5C678; /* Amber metric highlight */
--color-manual-review-dim: #5C4308;    /* Dark amber border */
--color-manual-review-tint: rgba(232, 179, 94, 0.12); /* Badge fill */

/* 3. Capacity Deferral & Discordance (Muted Violet) */
/* Backend Action Enums: HELD and DEFERRED | Reason: R6_CAPACITY_DEFERRED */
/* Distinguish HELD (queued / un-admitted) from DEFERRED (governor capacity shed) */
--color-epistemic-defer: #B4A0F8;      /* Discordance > tau, capacity shunted */
--color-epistemic-defer-bright: #CDBDFF;/* Violet telemetry highlight */
--color-epistemic-defer-dim: #352071;  /* Dark violet border */
--color-epistemic-defer-tint: rgba(180, 160, 248, 0.14); /* Badge fill */

/* 4. Routine / Consensus Low Risk (Technical Sage Green) */
/* Backend Action Enum: ROUTINE | Reason: R5_LOW_RISK_RELIABLE */
/* User-Facing Display Label: "Routine" (Do not use ROUTINE_CLEAR backend enum) */
--color-routine: #68C99A;              /* Frictionless clearance, consensus low risk */
--color-routine-bright: #84E0B2;       /* Green metric highlight */
--color-routine-dim: #004D36;          /* Dark green border */
--color-routine-tint: rgba(104, 201, 154, 0.12); /* Badge fill */
--color-routine-clear: #68C99A;        /* Display token alias */
--color-routine-clear-bright: #84E0B2;
--color-routine-clear-dim: #004D36;
--color-routine-clear-tint: rgba(104, 201, 154, 0.12);
```

### 3.4 High-Contrast Typography Palette
```css
--text-primary: #EDF2F6;               /* Primary ice white (contrast 13.5:1 against #111922) */
--text-secondary: #A2B0BC;             /* Cool slate for headers and labels (contrast 6.8:1) */
--text-tertiary: #6E7E8D;              /* Subdued micro-metadata */
--text-disabled: #424F5C;              /* Disabled controls */
--text-on-accent: #0A0F14;             /* High contrast dark text on surgical teal */
```

### 3.5 Component State Rules
- **Hover State:** Border transitions from `--border-default` (`#293743`) to `--border-active` (`#3E5060`) over `150ms`. No vertical translate or drop-shadow jump.
- **Selected State:** Uninterrupted `2px solid var(--accent-primary)` left accent tab, with background `#18232D` and primary text `#EDF2F6`.
- **Focus State:** Strict visible focus ring: `outline: 2px solid var(--accent-primary); outline-offset: 2px;`. Zero blur.
- **Disabled State:** Opacity `0.45`, cursor `not-allowed`, border `--border-subtle`, text `--text-disabled`.
- **Measured Contrast Compliance:** Normal body text must achieve $\ge 4.5:1$ against its background; large metrics must achieve $\ge 3:1$. Contrast ratios must be verified with tools during implementation rather than relying on unverified blanket claims.

---

## 4. Typography & Geometry Specifications

### 4.1 Font Pairings & Offline Strategy
```
+----------------------------------------------------------------------------------------------------+
|                                    TYPOGRAPHIC ROLES & PAIRING                                     |
+----------------------------------------------------------------------------------------------------+
| IBM PLEX SANS      | Nav headers, section titles, explanatory text, buttons, table headers         |
| COURIER PRIME      | Case IDs, hashes, timestamps, tabular telemetry, math formulas, status tags   |
+----------------------------------------------------------------------------------------------------+
```

1. **`IBM Plex Sans` (Interface Face):** Technical, engineered, open counters, highly legible at small sizes. Weights: 400 (Regular), 500 (Medium), 600 (SemiBold), 700 (Bold).
2. **`Courier Prime` (Machine Telemetry Face):** Monospaced, crisp geometric forms, high x-height. Weights: 400 (Regular), 700 (Bold).
3. **Offline Font Strategy:**
   - The application must not break or block rendering if a live Google Fonts request is unavailable.
   - Fonts must be loaded locally using Vite assets (`@font-face` with local WOFF2 files in `frontend/src/assets/fonts/` or self-hosted `@fontsource/ibm-plex-sans` and `@fontsource/courier-prime`).
   - Fallback font stack must be declared:
     ```css
     --font-sans: 'IBM Plex Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
     --font-mono: 'Courier Prime', SFMono-Regular, Consolas, 'Liberation Mono', Menlo, monospace;
     ```
4. **Tabular Figures Discipline:**
   - All tables, KPI values, latency numbers, timestamps, and coordinates must declare:
     ```css
     font-variant-numeric: tabular-nums lining-nums;
     ```

### 4.2 Type Scale
| Token | Font Family | Size | Line Height | Tracking | Weight | Role |
|:---|:---|:---:|:---:|:---:|:---:|:---|
| `--text-display` | `IBM Plex Sans` | `1.75rem` (28px) | `2.25rem` (36px) | `-0.02em` | 700 | Main screen titles |
| `--text-headline-lg` | `IBM Plex Sans` | `1.25rem` (20px) | `1.75rem` (28px) | `-0.01em` | 600 | Card & section headings |
| `--text-headline-md` | `IBM Plex Sans` | `1.125rem` (18px) | `1.5rem` (24px) | `0em` | 600 | Panel sub-headings |
| `--text-headline-sm` | `IBM Plex Sans` | `1.0rem` (16px) | `1.375rem` (22px) | `0em` | 600 | Block titles, list items |
| `--text-body-lg` | `IBM Plex Sans` | `0.9375rem` (15px) | `1.375rem` (22px) | `0em` | 400 | Primary explanatory text |
| `--text-body-md` | `IBM Plex Sans` | `0.875rem` (14px) | `1.25rem` (20px) | `0em` | 400 | Standard body, table data |
| `--text-body-sm` | `IBM Plex Sans` | `0.8125rem` (13px) | `1.125rem` (18px) | `0em` | 400 | Secondary metadata descriptors |
| `--text-label-md` | `IBM Plex Sans` | `0.75rem` (12px) | `1.0rem` (16px) | `0.04em` | 600 | Button labels, tabs |
| `--text-label-sm` | `IBM Plex Sans` | `0.6875rem` (11px) | `0.875rem` (14px) | `0.05em` | 600 | Micro-labels (selective uppercase) |
| `--text-code-lg` | `Courier Prime` | `0.875rem` (14px) | `1.25rem` (20px) | `0em` | 700 | Key metrics, large hashes |
| `--text-code-md` | `Courier Prime` | `0.8125rem` (13px) | `1.125rem` (18px) | `0em` | 400/700 | Table IDs, timestamps, delta $p$ |
| `--text-code-sm` | `Courier Prime` | `0.6875rem` (11px) | `0.875rem` (14px) | `0.04em` | 500/700 | Status chips, seeds, code tags |

### 4.3 Disciplined Geometry & Spacing
- **Corner Radii:**
  - Standard panels, cards, inputs, buttons: `4px` (`0.25rem`).
  - Micro-chips, checkboxes, status tags: `2px` (`0.125rem`).
  - Modal dialogs, floating sheets: `6px` (`0.375rem`).
  - Circular pills and bubbly buttons are prohibited.
- **Spacing Scale (4px/8px Module):**
  - `--space-1`: `4px` (`0.25rem`)
  - `--space-2`: `8px` (`0.5rem`)
  - `--space-3`: `12px` (`0.75rem`)
  - `--space-4`: `16px` (`1rem`)
  - `--space-5`: `20px` (`1.25rem`)
  - `--space-6`: `24px` (`1.5rem`)
  - `--space-8`: `32px` (`2rem`)

---

## 5. Shared Application Shell Architecture

```
+----------------------------------------------------------------------------------------------------+
| TOP HEADER (64px)                                                                                  |
| [LOGO] SIGNALGATE   [EVIDENCE: SYNTHETIC_SMOKE_ONLY] | Overview | Replay | Explorer | Policy | [v0.1.0] |
+-------------------------------------+--------------------------------------------------------------+
| OPERATIONAL CONTEXT RAIL (256px)    | MAIN COCKPIT VIEWPORT (Fluid 12-Column Grid)                 |
|                                     |                                                              |
| [Offline Evaluation Budget: 130 Cap]|                                                              |
| [Queue Pressure Status: Muted/Unav] |                                                              |
|                                     |                                                              |
| [Investigation Rails Sub-Nav]       |                                                              |
| > Overview & Control Stage          |                                                              |
| > Shift Storm Replay (Forensics)    |                                                              |
| > Case Explorer (Predictions)       |                                                              |
| > Policy Comparison (Benchmarks)    |                                                              |
|                                     |                                                              |
| [Offline Scoring Sandbox Card]      |                                                              |
+-------------------------------------+--------------------------------------------------------------+
| PROVENANCE FOOTER (28px): DATASET: SYNTHETIC_SMOKE_ONLY | HASH: 8d3f02ca | BENCHMARK p95: 0.17ms   |
+----------------------------------------------------------------------------------------------------+
```

### 5.1 Fixed Top Header (64px)
- **Position & Sizing:** Fixed top, `height: 64px`, `z-index: 50`, background `#111922`, bottom border `1px solid #293743`.
- **Left Zone:** Brand logo (`SIGNALGATE`), subtitle (`SHIFT-AWARE FRAUD TRIAGE`), vertical divider, and authoritative evidence status badge (`SYNTHETIC_SMOKE_ONLY`).
- **Center Zone (Primary Navigation):** 4 persistent horizontal tab links:
  1. `Overview` (`/overview`)
  2. `Shift Storm Replay` (`/shift-storm`)
  3. `Case Explorer` (`/case-explorer`)
  4. `Policy Comparison` (`/policy-comparison`)
  - Active tab styling: background `#18232D`, text `#86F5E7`, bottom indicator `2px solid #68D8CB`.
- **Right Zone:** Active evaluation budget indicator ($B = 0.06525$, 130 reviews), service version (`v0.1.0` from `/api/health`), and analyst profile badge. Do not display unverified gateway tags or claims of live traffic.

### 5.2 Operational Context Rail (256px)
- **Position & Sizing:** Fixed left below header, `width: 256px`, bottom offset `28px`, background `#111922`, right border `1px solid #293743`. Visible on screens $\ge 1024\text{px}$.
- **Section 1: Evaluation Budget & Capacity State:**
  - Evaluated capacity cap: 130 reviews on the 2,000-row test partition ($6.525\%$).
  - Live ingestion counters and anomaly velocity rates are unbacked by live streams; render as `Unavailable` in offline synthetic mode.
- **Section 2: Investigation Rails:**
  - Fast cross-stage anchor links: Overview (`/overview`), Case Explorer (`/case-explorer`), Shift Storm Replay (`/shift-storm`), Policy Comparison (`/policy-comparison`).
- **Section 3: Offline Scoring Sandbox Card:**
  - Security posture indicator stating that the scoring sandbox runs locally via FastAPI with strict recursive feature leakage rejection (rejecting `isFraud`, `TransactionDT`, `TransactionID`). Explicitly note: Not connected to external payment gateways or live ledgers.

### 5.3 Persistent Provenance Footer (28px)
- **Position & Sizing:** Fixed bottom, `height: 28px`, `z-index: 50`, background `#111922`, top border `1px solid #293743`.
- **Honest Data Rule:** Displays verifiable provenance from validated project artifacts:
  - Dataset Evidence Status: `SYNTHETIC_SMOKE_ONLY` (from `config.yaml` / `/api/overview`).
  - Frozen Config Hash: `8d3f02ca...` (from `config.yaml` and `frozen_policy.json`).
  - Benchmark Latency: Evaluated offline single-transaction $p95 = 0.17\text{ms}$ (from `results/results.json`).
  - Split Hash: `07b55a4e...` (from `results/split_report.json`).
- **Unavailable State:** Unverified live telemetry, live gateway connectivity, live node cluster status, or unverified live audit integrity must display an explicit `Unavailable` status or be omitted.

---

## 6. Detailed Screen Specifications

### 6.1 Operational Overview Screen

```
OPERATIONAL OVERVIEW COCKPIT LAYOUT:
+----------------------------------------------------------------------------------------------------+
| [Evidence Banner: SYNTHETIC_SMOKE_ONLY // Offline Evaluation Fixture Protocol]                     |
| Title: Operational Overview & Decision Telemetry                       [Topology Lock] [Calibrate] |
+----------------------------------------------------------------------------------------------------+
| 4-CARD KPI BAND                                                                                    |
| [Incoming Caserate]    [Review Capacity]       [Deferral Ratio]        [Precision @ Touched]       |
| (Unavailable - Offline)(130 Reviews / 6.525%)  (48.7% Deferred Rate)   (7.69% Precision / 9.01% Rec)|
+----------------------------------------------------------------------------------------------------+
| SIGNAL CORE ROUTING TOPOLOGY (Max Height 220-240px)                                                |
| [Stage 1: Raw Ingest] ---> [Stage 2: Dual-Model Matrix] ---> [Stage 3: Capacity Gate & 4 Lanes]   |
| Lanes: FRAUD_ALERT (Coral) | MANUAL_REVIEW (Amber) | DEFERRED (Violet) | ROUTINE (Sage Green)      |
+----------------------------------------------------------------------------------------------------+
| LOWER TRI-PANE OPERATIONAL GRID (3 x 4 Columns)                                                    |
| [Human Review Capacity]     | [Active Scenario Profile]     | [Case Prediction Sentinel]           |
| - Bounded Cap: 130 slots    | - Disagreement threshold u_th | - Offline test partition cases       |
| - 11 Alerts / 119 Reviews   | - Reason distribution (R1-R6) | - Paged from results/cases.jsonl     |
+----------------------------------------------------------------------------------------------------+
```

1. **Header & Contextual Banner:**
   - Top notification ribbon displaying active evidence mode: `SYNTHETIC_SMOKE_ONLY: Offline Evaluation Protocol Active`.
   - Title: `Operational Overview & Decision Telemetry`, with frozen config hash and evaluation timestamp.
2. **KPI Telemetry Band (4 Compact Cards):**
   - *Incoming Case Rate:* Unverified live ingestion is not active; renders an honest italicized `Unavailable (Offline)` indicator.
   - *Review Capacity:* Bounded evaluation capacity: 130 reviews ($6.525\%$ primary budget on 2,000 test cases). Admitted: 11 alerts, 119 manual reviews (130/130 slots consumed; capacity exhausted).
   - *Deferral Ratio (Held/Deferred):* Bounded governor deferrals: 974 cases deferred ($48.7\%$ deferred rate on the test set).
   - *Precision @ Touched:* Precision on synthetic test split: $7.69\%$ ($10/130$), with synthetic evaluation test-look recall of $9.01\%$ ($10/111$ caught).
   - *Data Rule:* Real numbers come from `GET /api/overview` and `results/results.json`. Unbacked fields must display `Unavailable`.
3. **Compact Signal Core Routing Topology (~220–240px Height):**
   - Directional horizontal pipeline (Stage 1: Ingestion $\to$ Stage 2: Dual-Model Decomposition $\to$ Stage 3: Capacity Gate & 4 Lanes).
   - Destination lanes map to genuine backend action codes: `FRAUD_ALERT` (Coral), `MANUAL_REVIEW` (Amber), `DEFERRED` (Violet), and `ROUTINE` (Sage Green).
   - Only active or filtered lanes carry full color; inactive lanes remain neutral slate.
4. **Lower Tri-Pane Cockpit (3 Columns x 4 Grid Units):**
   - *Col 1: Human Review Capacity:* 10-segment stepped bar showing capacity consumption (130 admitted escalations: 11 alerts + 119 reviews).
   - *Col 2: Active Scenario Profile:* Disagreement distribution with threshold marker ($u_{\text{threshold}} = 0.5268$), reason code breakdown (R1 high risk, R2 intermediate, R3 disagreement, R5 routine, R6 deferred).
   - *Col 3: Case Prediction Sentinel:* High-priority cases paged from genuine offline prediction records (`results/cases.jsonl`).

---

### 6.2 Shift Storm Replay Screen

```
SHIFT STORM REPLAY COCKPIT (SPLIT 9-COL CANVAS / 3-COL INSPECTION DOSSIER):
+----------------------------------------------------------------------------------------------------+
| CONTROL STRIP: [Scenario: S0 Baseline] [Reset | Step-Back | RUN REPLAY | Step-Fwd] [0.5x 1x 2x 5x] |
| [Timeline Scrubber: Step Index / Total Rows] [Capacity Budget: 130 Slots] [Status: STATIC SCAFFOLD]|
+---------------------------------------------------------------------+------------------------------+
| 3D FORENSICS TOPOLOGY CANVAS (9 COLS)                               | CASE FORENSIC DOSSIER (3C)   |
|                                                                     |                              |
| [Active Packet HUD: #case_test_000042 | Offline Row Index 42]       | Case: #case_test_000042      |
|                                                                     | Action: HELD / DEFERRED      |
| +-----------------------------------------------------------------+ | Reason: R6_CAPACITY_DEFERRED |
| | Directional 3D Particle Conduits                                | | Risk p: 0.089                |
| | Ingestion ---> Dual-Model Disagreement ---> 4 Destination Lanes | | Disagreement u: 0.124        |
| |                                           (DEFERRED Highlighted)| |                              |
| +-----------------------------------------------------------------+ | Evaluation Status: SYNTHETIC |
|                                                                     |                              |
| [Bottom Event Preview: #41 ROUTINE | #42 DEFERRED | #43 FRAUD_ALERT]| [Explanations: Disabled]     |
|                                                                     | [Overrides: Read-Only]       |
+---------------------------------------------------------------------+------------------------------+
```

1. **Replay Control Strip:**
   - Scenario selector bound to `/api/scenarios` (S0, S1, S2, S3).
   - Transport controls: Reset, Step-Back, `RUN REPLAY` (teal button), Step-Forward.
   - Timeline scrubber bound to deterministic row indices.
   - Capacity budget indicator showing the 130-review primary evaluation limit.
2. **Interactive Topology Canvas (9 Columns):**
   - Dark grid plane (`#0D131A` with subtle 24px dot grid).
   - 3D particle trajectories representing transaction streams entering destination conduits (`FRAUD_ALERT`, `MANUAL_REVIEW`, `DEFERRED`, `ROUTINE`).
   - Active packet bifurcation at the epistemic discordance threshold ($u \ge u_{\text{threshold}}$).
   - Bottom event preview rendering genuine case rows with actual backend actions.
3. **Deep Inspection Dossier (3 Columns):**
   - Non-collapsing right panel displaying the inspected case ID, composite risk $p$, rank-residual disagreement $u$, reason code, and SHA-256 hash.
   - **Explanations:** Explicitly marked `Disabled` (bound to `config.yaml` `explanations.enabled: false` and API status `DISABLED`).
   - **Overrides:** Override buttons are read-only / non-functional (no backend database write endpoint exists).
4. **Data Integrity & Feature Honesty Rule:**
   - Replay streaming is **not functional** (the backend does not provide a WebSocket or real-time event stream).
   - In Phase 7.5, render the visual scaffolding with static topology and an explicit `"Awaiting Phase 8 Replay Stream"` state badge.
   - Real replay data bind to paginated batch records via `GET /api/replay/rows` in Phase 8.

---

### 6.3 Case Explorer Screen

```
CASE EXPLORER COCKPIT (SPLIT 65% TABLE / 35% DETAIL DOSSIER):
+----------------------------------------------------------------------------------------------------+
| TELEMETRY SPARK BAND: [Test Batch: 2,000] [Frauds: 111] [Capacity: 130] [Deferred: 974] [p95: 0.17ms]|
+----------------------------------------------------------------------------------------------------+
| TOOLBAR: [query: reason:R3_MODEL_DISAGREEMENT (Cmd+K)]  [Presets: High Risk, Disagreement] [EXPORT]|
| STATUS PILLS: [ALL 2,000] [FRAUD_ALERT 11] [MANUAL_REVIEW 119] [DEFERRED 974] [ROUTINE 896]       |
+-------------------------------------------------------------+--------------------------------------+
| HIGH-DENSITY PREDICTION TABLE (65% / 8 COLS)                | CASE DOSSIER (35% / 4 COLS)          |
|                                                             |                                      |
| [x] CASE ID        TIMESTAMP     AMOUNT     p      ACTION   | Case Dossier #case_test_000042       |
| [ ] case_test_001  326480        $142.50    0.094  ALERT    | Action: FRAUD_ALERT                  |
| [ ] case_test_002  326495        $48.00     0.078  REVIEW   | Reason: R1_HIGH_RISK                 |
| [*] case_test_003* 326512        $1,290.00  0.089  DEFERRED | Risk p: 0.0892 | Disagreement u: 0.12|
|     (Teal 2px left border on selected row)                  | Features: TransactionAmt, ProductCD  |
| [ ] case_test_004  326540        $38.25     0.012  ROUTINE  | Explanations: Disabled               |
|                                                             | Overrides: Non-functional (Read-Only)|
| [Pagination: Rows per page 25 | 1-25 of 2,000 cases | < 1 2 >]| Cryptographic SHA-256 Provenance     |
+-------------------------------------------------------------+--------------------------------------+
```

1. **Telemetry Spark Band:**
   - 5 verifiable metrics derived from `results/results.json`: Evaluated Test Rows (2,000), Total Frauds (111), Primary Capacity (130), Deferred Cases (974), Benchmark Latency $p95$ (0.17ms).
2. **Search & Filter Strip:**
   - Syntax input bar with `query:` prefix and `⌘K` keyboard badge.
   - Filter presets matching genuine backend parameters: `action`, `reason_code`, `risk_min`, `risk_max`, `scenario`.
   - Action utilities: Export button (must be displayed as `Disabled / Non-functional`; no backend export endpoint exists).
   - Status pills filtering by genuine backend `Action` enum:
     - `ALL` (2,000)
     - `FRAUD_ALERT` (11) — User-friendly label: "Fraud Alert"
     - `MANUAL_REVIEW` (119) — User-friendly label: "Manual Review"
     - `DEFERRED` (974) — User-friendly label: "Deferred"
     - `ROUTINE` (896) — User-friendly label: "Routine"
3. **Master-Detail 65/35 Split Layout:**
   - *Left (65%):* High-density audit table with multi-select checkboxes, Case ID, timestamp, transaction amount, risk $p$, rank-residual disagreement $u$, route action badge (`FRAUD_ALERT`, `MANUAL_REVIEW`, `DEFERRED`, `ROUTINE`), reason code (R0–R6), and cryptographic hash.
   - *Right (35%):* Case Dossier panel bound to `GET /api/cases/{case_id}`.
   - *Feature Honesty Rule:* Explanations are marked `Disabled` (API returns `{"status": "disabled", "attributions": None}`). Analyst override buttons are read-only / non-functional (no database write endpoint).
4. **Pagination Controls:**
   - Rows per page selector (`25`, `50`, `100`), entity range indicator, and accessible page buttons.

---

### 6.4 Policy Comparison Screen

```
POLICY COMPARISON COCKPIT:
+----------------------------------------------------------------------------------------------------+
| SUB-HEADER: Evaluation Suite: OFFLINE BENCHMARK // SYNTHETIC_SMOKE_ONLY // Seed: 42               |
| Title: Policy Comparison & Workload-Matched Benchmark       [Re-Simulate (Disabled)] [Export (Dis)]|
+----------------------------------------------------------------------------------------------------+
| 3-COLUMN BENCHMARK ARCHITECTURE CARDS (Primary Budget Multiple 1.5x / B = 0.06525 / Cap = 130)     |
| +--------------------------+ +--------------------------+ +--------------------------------------+ |
| | Policy A: Fixed Cutoff   | | Policy B: Top-Budget (B2)| | SignalGate Architecture (Candidate)  | |
| | Touched Count: 126       | | Touched Count: 130       | | Touched Count: 130 (11 Alert/119 Rev)| |
| | Synthetic Recall: 9.01%* | | Synthetic Recall: 9.01%* | | Synthetic Recall: 9.01%*             | |
| | Caught: 10 / Missed: 101 | | Caught: 10 / Missed: 101 | | Caught: 10 / Missed: 101             | |
| | Queue Risk: OVERRUN RISK | | Queue Risk: SATURATED    | | Deferred: 974 (Managed Capacity)     | |
| +--------------------------+ +--------------------------+ +--------------------------------------+ |
+----------------------------------------------------------------------------------------------------+
| MATCHED-BUDGET DISCRETE SWEEP MATRIX                                                               |
| [Genuine Evaluated Points: 1.0x (87 Cap) | 1.5x (130 Cap) | 2.0x (174 Cap) | 3.0x (261 Cap)]       |
| Status: Continuous trade-off curve is UNAVAILABLE (Requires multi-point synthetic resimulation).   |
| Discrete Sweep Table: Displays genuine recall & touched rates from results.json / frozen_policy.   |
+----------------------------------------------------------------------------------------------------+
| DECISION FUNCTION FORMULATION & STATISTICAL COMPARISON (Split 7 Cols / 5 Cols)                     |
| [Deterministic Policy Decision Function (router.py)] | [Paired Bootstrap Hypothesis Test (results)]|
+----------------------------------------------------------------------------------------------------+
```

1. **Header & Context:**
   - Sub-header specifying matched-workload evaluation protocol: Primary Budget Multiple $1.5\times$ training prevalence ($B = 0.06525$), evaluating to **130 reviews** on the 2,000-row test partition.
   - Action buttons: `Re-Simulate` and `Export Seeds` must be rendered as disabled/non-functional visual scaffolding (no backend simulation or export endpoint exists).
2. **3-Column Architecture Comparison Cards:**
   - *Card 1 (Arch-01 Fixed Threshold B1):* Fixed score threshold ($p \ge 0.0698$), touched rate $6.30\%$ (126 cases), caught 10 of 111 frauds ($9.01\%$ recall), precision $7.94\%$.
   - *Card 2 (Arch-02 Top-B Risk B2):* Top-$B$ ranking, touched rate $6.50\%$ (130 cases), caught 10 of 111 frauds ($9.01\%$ recall), precision $7.69\%$.
   - *Card 3 (Arch-03 SignalGate Candidate):* Shift-Aware Router + Capacity Governor. Touched rate $6.50\%$ (130 admitted: 11 alerts, 119 reviews), deferred 974, caught 10 of 111 frauds ($9.01\%$ recall), precision $7.69\%$. Delta vs B2: $0.0\text{ pp}$. Highlighted with Surgical Teal border and `ACTIVE CANDIDATE` badge.
   - *Data Honesty Rule:* Stitch mockup claims (71.4%, 82.6%, 94.1% recall, +11.5% delta) are strictly prohibited. All numbers derive directly from `results/results.json`.
3. **Matched-Budget Discrete Sweep Matrix & Curve Policy:**
   - **Genuine Available Sweep Points:** The backend and frozen policy (`frozen_policy.json` and `results.json`) pre-register and evaluate strictly 4 discrete budget multiples:
     - `1.0x`: Target budget $4.35\%$ ($87$ capacity on test partition)
     - `1.5x`: Target budget $6.525\%$ ($130$ capacity on test partition — Primary Budget)
     - `2.0x`: Target budget $8.70\%$ ($174$ capacity on test partition)
     - `3.0x`: Target budget $13.05\%$ ($261$ capacity on test partition)
   - **Continuous Curve Policy:** The data in the repository do **not** support a continuous trade-off curve across arbitrary budgets (e.g. 50 to 250 cases), nor a 180-review fixed capacity marker. The UI must render the genuine discrete sweep comparison table or, if a continuous curve is rendered, explicitly mark the uncomputed regions as `Unavailable — Continuous Curve Uncomputed` with missing evidence documented. The fixed vertical budget marker must be anchored strictly at **130 reviews** ($B = 0.06525$).
4. **Decision Function Formulation & Statistical Rigor Matrix:**
   - *Left (7 cols):* Monospace mathematical formulation reflecting the genuine router logic in `policy/router.py`:
     $$\text{Decision}(x) = \begin{cases} \text{FRAUD\_ALERT} & \text{if } p \ge t_{\text{alert}} \\ \text{MANUAL\_REVIEW} & \text{if } p \ge t_{\text{review}} \text{ or } u \ge u_{\text{threshold}} \\ \text{DEFERRED / HELD} & \text{if queue capacity } C_{\text{max}} \text{ exhausted} \\ \text{ROUTINE} & \text{otherwise (reliable low risk)} \end{cases}$$
   - *Right (5 cols):* Paired Bootstrap Confidence Interval Table from `results/results.json`:
     - Test rows: 2,000 | Frauds: 111 | Bootstrap resamples: 1,000
     - Point estimate difference vs. B2: $0.0\text{ percentage points}$
     - $95\%$ Paired Bootstrap CI: $[-2.75\text{ pp}, +2.75\text{ pp}]$
     - $p$-value: $1.0$ | Empirical Conclusion: **Inconclusive (spans zero; superiority not established on synthetic fixture)**.

---

## 7. The 3D Design System (Three.js & React Three Fiber v8)

### 7.1 Architecture & Stack Constraint
- **Framework Constraint:** Must use the existing `@react-three/fiber` 8.17.10 and `three` 0.160.0 installation. No additional 3D libraries or heavy physics engines may be introduced.
- **Performance Budget:** Maximum 60 draw calls, polygon count $<15,000$ triangles, frame rate locked to 60fps on modest integrated GPUs.

### 7.2 Overview: Compact Architectural Status Anchor (~220–240px Height)
- **Role:** Subordinate status anchor docked within the 3-stage routing flow header.
- **3D Composition:**
  - Orthographic or shallow-perspective camera view.
  - Directional signal flow from left (Ingestion) to center (Decision Core) to right (4 Destination Lane Conduits).
  - Center Gyro: Concentric geometric rings rotating smoothly ($0.25\,\text{rad/s}$), color-keyed to active system health (Surgical Teal when healthy; pulsing Amber if capacity exceeds 90%).
  - Right conduits feed visually into the four destination lanes (`FRAUD_ALERT`, `MANUAL_REVIEW`, `DEFERRED`, `ROUTINE`).
- **Interaction:** Hovering a destination lane in the DOM highlights the corresponding 3D outflow conduit. Mouse scroll wheel is non-capturing (does not hijack page scrolling).

### 7.3 Shift Storm Replay: Forensics Topology Stage (9-Column Canvas)
- **Role:** Primary visual centerpiece for analyzing distribution shift dynamics.
- **3D Composition:**
  - 3D particle accelerator and trajectory matrix over a subtle 24px dot grid (`#0D131A`).
  - Luminous data packets travel along splines from Ingestion, through the Dual-Model Matrix, into destination lanes.
  - At the epistemic divergence boundary ($u \ge u_{\text{threshold}}$), packet trajectory bifurcates, showing why the case is shunted into the deferred buffer.
- **Timeline Synchronization:**
  - Scrubbing the timeline or clicking Step-Forward / Step-Back advances the deterministic frame index and positions the packet at that exact stage, updating the right-hand Case Dossier.
- **Static Scaffolding Rule:** In Phase 7.5, render the visual topology in a static paused state with clear `"Awaiting Replay Integration"` badges until Phase 8 connects `GET /api/replay/rows`. Do not simulate live streaming or fabricate synthetic motion.

### 7.4 Accessibility & Fallback Guarantees
- **Reduced Motion:** If `prefers-reduced-motion: reduce` is active, the 3D canvas is automatically bypassed and replaces itself with `SignalCoreFallback.tsx` (an SVG architectural pipeline diagram) with zero motion.
- **WebGL Failure Recovery:** The canvas is wrapped in `WebGLErrorBoundary`. If WebGL context is lost or unsupported, it falls back gracefully to the 2D vector pipeline without crashing the application shell.
- **Offline Reliability:** All shaders and geometries use Three.js built-in primitives (`icosahedronGeometry`, `torusGeometry`, `cylinderGeometry`, `boxGeometry`). No external 3D asset downloads (`.gltf`, `.bin`, textures) are permitted.

---

## 8. Strict Data-Integrity Requirements

To maintain scientific rigor and prevent misleading operational claims, the frontend must adhere to these inviolable data-integrity rules:

### 8.1 Development Evidence Status
The development environment operates strictly under:
$$\text{EVIDENCE: }\mathbf{SYNTHETIC\_SMOKE\_ONLY}$$
This label must be visibly rendered in the header provenance banner and API status indicators.

### 8.2 Prohibited Mockup Metrics & Feature Prohibitions
The numbers and features shown in the Stitch design exports are **illustrative visual placeholders**. They must **never** be hardcoded into React components or treated as verified operational benchmarks:

| Item | Stitch Placeholder / Mockup Claim | Authoritative Repository Truth & Data Source |
|:---|:---:|:---|
| **Incoming Caserate** | `14,820 / hr` | Prohibited. Must be marked `Unavailable (Offline)` unless bound to a live ingestion stream. |
| **Review Capacity Cap** | `180 cases/hr` or `180 / shift` | Prohibited as primary budget. Canonical primary budget is **130 reviews** ($B = 0.06525 \times 2,000$ test rows) from `policy/frozen_policy.json` and `results/results.json`. |
| **Precision @ Recall 90%** | `98.14%` | Prohibited. True evaluated test precision is $7.69\%$ from `results/results.json`. |
| **Model AUC Values** | `0.988` (A) / `0.991` (B) | Prohibited. Evaluated PR-AUC on synthetic test partition is $0.0629$ from `results/results.json`. |
| **Policy Recall Claims** | `71.4%`, `82.6%`, `94.1%` | Prohibited. Evaluated synthetic test-look recall is $9.01\%$ (10 of 111 caught) at primary budget ($B = 0.06525$). |
| **Fraud Capture Improvement** | `+11.5% Delta` | Prohibited. Genuine evaluated difference vs. B2 is $0.0\text{ pp}$ with inconclusive 95% CI $[-2.75\text{ pp}, +2.75\text{ pp}]$. |
| **Air-Gapped / Live Gateway** | `AIR-GAPPED SANDBOX`, `GATEWAY v4.2` | Prohibited. System is a local offline test environment with no gateway connection and no live audit engine. |
| **SHAP Feature Attributions** | `+0.34 IP Velocity` bars | Prohibited as functional. Marked `DISABLED` in `config.yaml` and `/api/status`. Must render as `Disabled`. |
| **Analyst Override Writes** | "Override to Routine", "Confirm Alert" | Prohibited as functional. No database write endpoint exists. Must render as read-only / disabled. |
| **Replay Event Streaming** | Live WebSocket / streaming replay | Prohibited as functional. Backend only provides paginated row reads (`GET /api/replay/rows`). |
| **Data Export Actions** | `[EXPORT]` CSV / PDF buttons | Prohibited as functional. No export endpoint exists. Must render as disabled visual scaffolding. |
| **Fake Case IDs & Hashes** | `#SYNTH-8921-003` | Prohibited. Must use genuine case identifiers from `results/cases.jsonl` (e.g. `case_test_000042`). |

### 8.3 Zero Fabrication Policy
1. If a backend endpoint is missing, returning an error, or marked `DISABLED`, the UI must render an honest, descriptive indicator (e.g., *“Feature explanations disabled in current release”* or *“Deferred to Phase 8”*).
2. Defaulting missing metrics to `0`, `0.00%`, or hardcoded dummy statistics is strictly prohibited.

---

## 9. Responsive, Accessibility & Performance Rules

### 9.1 Responsive Breakpoint Grid
- **Wide SOC Cockpit ($\ge 1440\text{px}$):**
  - Full 3-pane multi-column layouts active simultaneously.
  - Case Explorer: 65% table / 35% detail dossier.
  - Shift Storm: 9-column trajectory canvas / 3-column deep dossier.
  - Policy Comparison: 3 architecture cards + discrete sweep matrix + 7/5 formulation block.
- **Field Laptops ($1024\text{px} - 1439\text{px}$):**
  - Main stages retain primary emphasis.
  - Detail inspection dossiers collapse into an anchored slide-over drawer triggered by clicking any case row or packet node.
- **Tablets & Mobile ($< 1024\text{px}$):**
  - Sidebar collapses into an overlay drawer accessible via the mobile menu button.
  - Master-detail views switch to a segmented tab bar: `[Event Queue]`, `[Case Dossier]`, `[Actions]`.
  - Tables enable horizontal scrolling (`overflow-x: auto`) with sticky Case ID columns.
  - Zero horizontal page overflow allowed (`overflow-x: hidden` on root container).

### 9.2 Accessibility (WCAG 2.2 AA / AAA Floor)
1. **Focus Ring Standard:** Every interactive button, input, link, and checkbox must display a high-contrast focus ring:
   ```css
   :focus-visible {
     outline: 2px solid var(--accent-primary);
     outline-offset: 2px;
   }
   ```
2. **Keyboard Navigation:**
   - Search input must focus immediately on `⌘K` / `Ctrl+K`.
   - Table rows must be traversable using Arrow Up / Arrow Down keys, with Enter opening the dossier.
   - Modal dialogs must trap focus and close on `Escape`.
3. **Screen Reader Semantics:**
   - Decorative icons and pulse dots must declare `aria-hidden="true"`.
   - Dynamic telemetry updates (queue saturation alerts) must be wrapped in `aria-live="polite"` or `role="status"`.
   - Icon-only buttons must have descriptive `aria-label` attributes.

---

## 10. Phased Implementation Roadmap & Acceptance Criteria

```
+----------------------------------------------------------------------------------------------------+
|                                    PHASED IMPLEMENTATION SEQUENCE                                  |
+----------------------------------------------------------------------------------------------------+
| STEP 1: Design Tokens, Typography & Shared Component Primitives                                    |
| STEP 2: Application Cockpit Shell (Top Header, Operational Rail, Provenance Footer)                |
| STEP 3: Overview Layout & Compact 220px Signal Core HUD                                            |
| STEP 4: Structural Visual Scaffolding for Deferred Screens (Replay, Explorer, Comparison)          |
| STEP 5: Interactive 3D & Replay Integration (Connected to Phase 8 Endpoints)                       |
| STEP 6: Visual Quality Verification & Design Polish                                                |
| STEP 7: Responsive, Accessibility, Performance & Production Build Validation                       |
+----------------------------------------------------------------------------------------------------+
```

### 10.1 Implementation Steps
1. **Step 1 — Design Tokens, Typography & Component Primitives:**
   - Update `tokens.css` with authoritative surfaces, hairline borders, surgical teal, and 4 semantic decision colors (`--color-fraud-alert`, `--color-manual-review`, `--color-epistemic-defer`, `--color-routine`).
   - Configure local font loading for `IBM Plex Sans` and `Courier Prime`; apply `tabular-nums` globally.
   - Standardize buttons, cards, and badges on the 4px radius, zero-shadow specification.
2. **Step 2 — Application Cockpit Shell:**
   - Re-architect `AppShell.tsx`, `Sidebar.tsx`, and `TopBar.tsx` into the 3-tier shell (64px Top Header with 4 horizontal tabs, 256px Operational Rail, 28px Provenance Footer).
   - Display honest `SYNTHETIC_SMOKE_ONLY` flag and offline scoring sandbox status (no air-gap or live gateway claims).
3. **Step 3 — Operational Overview Layout & Compact Signal Core:**
   - Refactor `OverviewPage.tsx` to match the verified KPI band, compact ~220px Signal Core 3-stage flow, and lower tri-pane operational cockpit.
   - Primary review capacity anchored to 130 reviews ($B = 0.06525$).
4. **Step 4 — Cockpit Scaffolding for Operations Screens:**
   - Build structural grid containers for `CaseExplorerPage` (65/35 table-to-dossier), `ShiftStormPage` (9/3 trajectory-to-dossier), and `PolicyComparisonPage` (3-card grid + discrete sweep table).
   - Prohibit functional SHAP, override writes, export actions, or live streaming.
5. **Step 5 — Interactive 3D & Replay Integration:**
   - Connect 3D trajectory particles to `GET /api/replay/rows` in Phase 8 without fabricating data.
6. **Step 6 — Visual Verification & Design Polish:**
   - Perform side-by-side browser comparisons against Stitch PNGs to verify typography, alignment, and hover states.
7. **Step 7 — Responsive, Accessibility & Build Verification:**
   - Validate TypeScript (`tsc --noEmit`), production build (`npm run build`), unit tests (`npm test`), and WCAG contrast compliance.

---

### 10.2 Concrete Acceptance Criteria

#### Global Application Shell
- [ ] Top header is fixed at 64px and displays brand identity, `SYNTHETIC_SMOKE_ONLY` flag, 4 horizontal tabs, and evaluated budget readout (130 capacity / 6.525%).
- [ ] Operational rail is fixed at 256px on screens $\ge 1024\text{px}$ and displays evaluation budget counters and the Offline Scoring Sandbox card (no air-gap claims).
- [ ] Provenance footer is fixed at 28px and renders genuine dataset batch, seed, frozen config hash, and benchmark latency ($p95 = 0.17\text{ms}$) without fabricated claims.
- [ ] Zero drop-shadows, zero glowing borders, and zero button gradients across the application.
- [ ] All interactive buttons and cards use 4px corner radius; micro-chips and checkboxes use 2px.

#### Typography & Colors
- [ ] `IBM Plex Sans` renders for all UI narrative text; `Courier Prime` renders for case IDs, hashes, and code tags.
- [ ] The application renders correctly offline without requiring an active Google Fonts network request.
- [ ] `font-variant-numeric: tabular-nums` is active on all metrics and tables; numbers do not shift width when updating.
- [ ] Primary interactive elements use Surgical Teal (`#68D8CB`); inactive destination lanes remain neutral slate (`#111922`).
- [ ] The 4 semantic decision colors are strictly applied: Coral (`FRAUD_ALERT`), Amber (`MANUAL_REVIEW`), Muted Violet (`HELD` / `DEFERRED`), Sage Green (`ROUTINE`).
- [ ] Backend action enum `ROUTINE` is respected (no fabricated `ROUTINE_CLEAR` enum in API models); user-friendly labels are rendered cleanly.

#### Operational Overview
- [ ] Total height of the 3D Signal Core container is constrained to approximately 220px–240px and does not dominate the page.
- [ ] The routing flow clearly presents Stage 1 (Ingestion) $\to$ Stage 2 (Decomposition) $\to$ Stage 3 (Capacity Gate & 4 Lanes).
- [ ] Metric cards show verified numbers from `GET /api/overview` ($B = 0.06525$, 130 review capacity) or render an explicit `Unavailable` status.

#### Shift Storm Replay
- [ ] Displays the 9/3 split layout on desktop (trajectory canvas on left, deep inspection dossier on right).
- [ ] Control strip includes scenario selector, playback transport controls, speed selector, and timeline scrubber.
- [ ] In Phase 7.5, displays static topology and an honest `Awaiting Phase 8 Replay Stream` state badge without fake particle streaming.
- [ ] Dossier marks feature explanations as `Disabled` and override actions as read-only / non-functional.

#### Case Explorer
- [ ] Displays the 65/35 split layout on desktop (high-density table on left, detail dossier on right).
- [ ] Search input supports `query:` syntax and `⌘K` keyboard shortcut.
- [ ] Status pills filter by genuine backend action enums: `FRAUD_ALERT`, `MANUAL_REVIEW`, `HELD`, `DEFERRED`, `ROUTINE`.
- [ ] Active selected row displays an uninterrupted `2px solid #68D8CB` left accent tab.
- [ ] Dossier displays genuine case signals from `GET /api/cases/{case_id}` and marks SHAP feature explanations as `Disabled`.
- [ ] Export button and analyst override actions are documented and rendered as non-functional / disabled.

#### Policy Comparison
- [ ] Displays 3-column architecture cards comparing Fixed Cutoff B1, Top-Budget B2, and SignalGate candidate with genuine evaluation numbers ($9.01\%$ synthetic recall, $0.0\text{ pp}$ delta).
- [ ] Primary capacity is anchored to 130 reviews ($B = 0.06525$). Remove any assumption of 180 reviews as the primary evaluation budget.
- [ ] Matched-budget comparison renders the genuine discrete sweep points (`1.0x` / 87, `1.5x` / 130, `2.0x` / 174, `3.0x` / 261). Continuous curves are rendered as `Unavailable` documenting missing multi-point evidence.
- [ ] Mathematical gate decision function reflects `policy/router.py` action codes (`FRAUD_ALERT`, `MANUAL_REVIEW`, `HELD`/`DEFERRED`, `ROUTINE`).
- [ ] Zero fabricated recall claims; all numbers derive from validated evaluation artifacts with inconclusive bootstrap confidence interval clearly reported.

#### Accessibility & Performance
- [ ] All interactive elements feature visible 2px solid teal focus rings with zero blur.
- [ ] `prefers-reduced-motion: reduce` automatically bypasses 3D canvas and renders 2D vector fallback.
- [ ] WebGL error boundary prevents application crash on 3D initialization failure.
- [ ] Production bundle compiles with zero TypeScript errors and zero lint warnings.

---

*This document serves as the permanent, authoritative design system specification for SignalGate. Phase 7.5 and Phase 8 implementation must adhere strictly to these standards.*
