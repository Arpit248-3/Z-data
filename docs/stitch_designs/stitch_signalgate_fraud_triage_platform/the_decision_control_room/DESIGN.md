---
name: The Decision Control Room
colors:
  surface: '#0f1419'
  surface-dim: '#0f1419'
  surface-bright: '#353a3f'
  surface-container-lowest: '#0a0f14'
  surface-container-low: '#171c21'
  surface-container: '#1b2025'
  surface-container-high: '#252a30'
  surface-container-highest: '#30353b'
  on-surface: '#dee3ea'
  on-surface-variant: '#bcc9c6'
  inverse-surface: '#dee3ea'
  inverse-on-surface: '#2c3137'
  outline: '#869391'
  outline-variant: '#3d4947'
  surface-tint: '#69d9cb'
  primary: '#86f5e7'
  on-primary: '#003732'
  primary-container: '#68d8cb'
  on-primary-container: '#005d55'
  inverse-primary: '#006a62'
  secondary: '#bcc8d5'
  on-secondary: '#27323c'
  secondary-container: '#3f4a55'
  on-secondary-container: '#aebac7'
  tertiary: '#e7ddff'
  on-tertiary: '#352071'
  tertiary-container: '#cdbdff'
  on-tertiary-container: '#584595'
  error: '#ffb4ab'
  on-error: '#690005'
  error-container: '#93000a'
  on-error-container: '#ffdad6'
  primary-fixed: '#86f5e8'
  primary-fixed-dim: '#69d9cb'
  on-primary-fixed: '#00201d'
  on-primary-fixed-variant: '#005049'
  secondary-fixed: '#d8e4f2'
  secondary-fixed-dim: '#bcc8d5'
  on-secondary-fixed: '#121d26'
  on-secondary-fixed-variant: '#3d4853'
  tertiary-fixed: '#e7deff'
  tertiary-fixed-dim: '#cdbdff'
  on-tertiary-fixed: '#1f025c'
  on-tertiary-fixed-variant: '#4c3989'
  background: '#0f1419'
  on-background: '#dee3ea'
  surface-variant: '#30353b'
typography:
  display:
    fontFamily: IBM Plex Sans
    fontSize: 1.75rem
    fontWeight: '700'
    lineHeight: 2.25rem
    letterSpacing: -0.02em
  headline-lg:
    fontFamily: IBM Plex Sans
    fontSize: 1.25rem
    fontWeight: '600'
    lineHeight: 1.75rem
    letterSpacing: -0.01em
  headline-md:
    fontFamily: IBM Plex Sans
    fontSize: 1.125rem
    fontWeight: '600'
    lineHeight: 1.5rem
  headline-sm:
    fontFamily: IBM Plex Sans
    fontSize: 1rem
    fontWeight: '600'
    lineHeight: 1.375rem
  body-lg:
    fontFamily: IBM Plex Sans
    fontSize: 0.9375rem
    fontWeight: '400'
    lineHeight: 1.375rem
  body-md:
    fontFamily: IBM Plex Sans
    fontSize: 0.875rem
    fontWeight: '400'
    lineHeight: 1.25rem
  body-sm:
    fontFamily: IBM Plex Sans
    fontSize: 0.8125rem
    fontWeight: '400'
    lineHeight: 1.125rem
  label-md:
    fontFamily: IBM Plex Sans
    fontSize: 0.75rem
    fontWeight: '600'
    lineHeight: 1rem
    letterSpacing: 0.04em
  label-sm:
    fontFamily: IBM Plex Sans
    fontSize: 0.6875rem
    fontWeight: '600'
    lineHeight: 0.875rem
    letterSpacing: 0.06em
  code-lg:
    fontFamily: Courier Prime
    fontSize: 0.875rem
    fontWeight: '500'
    lineHeight: 1.25rem
  code-md:
    fontFamily: Courier Prime
    fontSize: 0.8125rem
    fontWeight: '400'
    lineHeight: 1.125rem
  code-sm:
    fontFamily: Courier Prime
    fontSize: 0.6875rem
    fontWeight: '500'
    lineHeight: 0.875rem
    letterSpacing: 0.03em
rounded:
  sm: 0.125rem
  DEFAULT: 0.25rem
  md: 0.375rem
  lg: 0.5rem
  xl: 0.75rem
  full: 9999px
spacing:
  gutter: 0.75rem
  gutter-desktop: 1rem
  margin: 1rem
  margin-desktop: 1.5rem
  space-xs: 0.25rem
  space-sm: 0.5rem
  space-md: 0.75rem
  space-lg: 1rem
  space-xl: 1.5rem
---

## Brand & Style

This design system establishes a disciplined, mission-critical operations environment engineered for fraud investigation units, financial security engineers, and intelligence analysts under active shift pressure. The visual posture rejects consumer SaaS decoration, superficial gradients, and neon illumination in favor of architectural precision, uncompromising legibility, and high-density telemetry.

The aesthetic fuses technical brutalism with calibrated modern utility:
- **Tone:** Authoritative, clinical, auditable, and unyielding.
- **Atmosphere:** Deep cockpit darkness calibrated to mitigate analyst cognitive fatigue during twelve-hour triage rotations.
- **Operational Cadence:** Dense metadata matrices, explicit provenance headers, and persistent triage routing rails designed for sub-second keyboard-driven navigation.
- **Integrity Signaling:** Every surface communicates verifiable state. Synthetic traces, sandbox runs, and simulated attack vectors carry mandatory, unambiguous indicators (such as `SYNTHETIC_SMOKE_ONLY`) to prevent cross-contamination with live production ledgers.

## Colors

The palette is strictly functional, mapping exact chromatic values to operational truth states:

- **Canvas & Background (`#0A0F14`):** Deep charcoal black baseline. Serves as the zero-elevation floor for the entire application viewport.
- **Primary Surface (`#111922`):** Technical dark slate for standard panels, data grids, inspection queues, and persistent rails.
- **Raised Surface (`#18232D`):** Elevated control surface applied to active inspector cards, flyout drawers, keyboard shortcuts palettes, and anchored filter toolbars.
- **Borders & Dividers (`#293743`):** Crisp 1px precision structural lines that segment data without blur or drop-shadow dependencies.
- **Primary Text (`#EDF2F6`):** Ice white text optimized for sharp reading contrast against slate surfaces (exceeding WCAG AAA for critical telemetry).
- **Secondary / Metadata Text (`#A2B0BC`):** Cool slate for column headers, micro-labels, inline keys, and secondary descriptors.
- **Primary Accent / Interactive (`#68D8CB`):** Surgical teal reserved strictly for active targets, system-confirmed interactions, focused states, and primary commit actions.

### Operational Semantic Spectrum
- **Fraud Alert / Critical Risk (`#F27870`):** Restrained coral alert. Signals high-confidence malicious velocity, token compromise, or rule detonations. Never rendered as pulsating or saturated neon; applied as solid perimeter outlines, badges, and delta fills.
- **Manual Review / Escalation (`#E8B35E`):** Controlled amber indicating human-in-the-loop intervention, KYC delta mismatch, or stepping-stone thresholds.
- **Model Disagreement / Uncertainty (`#B4A0F8`):** Muted violet indicating asynchronous ML divergence, pipeline anomaly flags, or classifier uncertainty.
- **Routine / Verified Cleared (`#68C99A`):** Technical sage green for baseline clearance, confirmed legitimate actors, and successful signature verifications.

## Typography

The type hierarchy prioritizes high scan-speed and informational density over expressive scale. All data-carrying views deploy tabular lining figures (`font-variant-numeric: tabular-nums`).

### Type Roles
- **Primary UI (`IBM Plex Sans`):** Carries all navigational controls, form inputs, table headers, and structural narrative text. Headings maintain a compact vertical footprint to preserve immediate screen real estate for incident data.
- **Telemetry & Identity Monospace (`Courier Prime`):** Applied systematically to immutable operational artifacts: transaction IDs, SHA-256 hashes, raw timestamps (UTC ISO-8601), IP CIDRs, device fingerprints, and categorical payload dumps.
- **Upper-Case Micro Labels:** Tokens designated under `label-sm` and `label-md` enforce uppercase transformation with tracked letter spacing for status pillars, shift metrics, and audit timestamps.

## Layout & Spacing

The layout is structured around an engineered, high-density 12-column fluid grid that adapts dynamically to multi-display security operations center (SOC) setups, ultra-wide monitors, and standard field laptops.

- **Grid Architecture:** Multi-pane tiled cockpit layout with non-collapsible global status bars, a persistent primary triage list (360px–420px), a central contextual investigation stage, and an expandable telemetry sidebar (400px).
- **Rhythm & Compaction:** Spacing tokens employ a disciplined 4px/8px module. Components default to dense internal vertical padding to minimize required scroll depth during triage.
- **Viewport Constraints:**
  - **Desktop (1440px+):** Full 3-pane split-screen investigation flow active simultaneously.
  - **Compact / Laptop (1024px - 1439px):** Central stage remains active; telemetry inspector collapses into an overlay drawer.
  - **Mobile / Field Tablet (<1024px):** Single-column stacked triage view with horizontal tab anchors switching between queue, detail, and decision dispatch.

## Elevation & Depth

This design system avoids soft atmospheric shadows and ambient blurs. Depth is achieved entirely through structural surface tiering and sharp 1px hairline boundaries.

- **Base Floor (`#0A0F14`):** Canvas bedrock. Holds background viewports and divider gutters.
- **Tier 1 Surface (`#111922`):** Default panel plane for event tables, search matrix grids, and workflow queues. Outlined by `1px solid #293743`.
- **Tier 2 Raised Control Surface (`#18232D`):** Applied to focused inspection panels, hovered list rows, context menus, and modals. Outlined by `1px solid #293743` or highlighted with a single `1px solid #68D8CB` border when selected.
- **Zero-Shadow Rule:** No fuzzy drop shadows or box blurs are permitted on core UI elements. Transient menus and modal overlays utilize a flat `0 0 0 1px #293743` perimeter shield combined with a 65% opacity backing veil (`#0A0F14A6`).

## Shapes

The shape system is strictly squared and disciplined, rejecting consumer-style rounded bubbles and circular buttons.

- **Base Corners:** All buttons, cards, status badges, table containers, and text fields use a standard 4px (`0.25rem`) corner radius.
- **Expanded Enclosures:** Larger modal dialogs and detached diagnostic floating sheets use a maximum radius of 6px (`0.375rem`).
- **Telemetry Indicators:** System pulse lights and provenance icons remain geometric: 4px micro-squares or pure 1px square borders, reinforcing an industrial instrument aesthetic.

## Components

### Buttons & Action Dispatchers
- **Primary Interactive:** Filled `#68D8CB` background with `#0A0F14` bold text. Radius 4px. Height 32px (compact) or 36px (standard). No shadows.
- **Secondary / Tactical:** Outlined with `1px solid #293743`, background `#18232D`, text `#EDF2F6`. Hover triggers border transition to `#68D8CB`.
- **Destructive / Reject:** Outlined `1px solid #F27870`, background transparent, text `#F27870`. Hover shifts background to `rgba(242, 120, 112, 0.12)`.
- **Focus Rings:** Distinct 2px offset border in `#68D8CB`, with 2px gap (`#0A0F14`).

### Operational Provenance Banners & Badges
- **Synthetic Flag Banner:** High-priority banner across synthetic/test datasets displaying `SYNTHETIC_SMOKE_ONLY` in `Courier Prime` uppercase. Background is `#111922` with a diagonal warning stripe perimeter or dashed border in `#B4A0F8`.
- **Triage Status Badges:** Monospace compact chips (height 20px) composed of a 1px border and 10% opacity tinted fill matching the semantic color (Coral, Amber, Violet, Sage). Text size `0.6875rem` (`code-sm`).

### Data Tables & Event Telemetry Grids
- **Header Rows:** Background `#18232D`, border-bottom `1px solid #293743`, typography `label-sm` in `#A2B0BC`.
- **Cells:** Dense padding (`0.5rem 0.75rem`), vertical alignment centered, monospaced columns for numeric entities and hashes.
- **Row States:** Default background `#111922`. Hover background `#18232D`. Active/selected row features an uninterrupted 2px left border accent in `#68D8CB`.

### Input Fields & Filter Controllers
- **Structure:** Height 32px, background `#0A0F14`, border `1px solid #293743`, text `#EDF2F6`. Placeholder text `#A2B0BC` at 60% opacity.
- **Prefix Anchors:** Dedicated monospace slot for query syntax (e.g., `rule:`, `ip:`, `hash:`) set in `#68D8CB`.

### Form Controls (Checkboxes & Radios)
- **Checkboxes:** 14px × 14px square, radius 2px, border `1px solid #293743`, background `#0A0F14`. Checked state displays a solid `#68D8CB` fill with an `#0A0F14` checkmark.
- **Radio Buttons:** 14px × 14px square with a centered 6px inner solid square on selection (avoiding circular motifs).

### Cards & Inspector Panels
- **Structure:** Background `#111922`, border `1px solid #293743`, radius 4px. 
- **Header Anchor:** Dedicated top bar with a solid `#18232D` background, 28px height, containing a categorical monospace title and timestamp in UTC.