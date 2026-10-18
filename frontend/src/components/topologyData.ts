// ---------------------------------------------------------------------------
// Semantic Detail Definitions for Inspection Bar (Clean Title Case)
// ---------------------------------------------------------------------------
export interface TopologyElementDetail {
  key: string;
  stageName: string;
  title: string;
  badge: string;
  badgeVariant: 'cyan' | 'coral' | 'amber' | 'green' | 'violet' | 'default';
  role: string;
  formula?: string;
  caseCount?: string;
}

export const TOPOLOGY_DETAILS: Record<string, TopologyElementDetail> = {
  stage_input: {
    key: 'stage_input',
    stageName: 'Stage 1: Input Ingestion',
    title: 'Offline Evaluation Ingestion Node',
    badge: 'SYNTHETIC_SMOKE_ONLY',
    badgeVariant: 'cyan',
    role: 'Held-out test partition of 2,000 cases. Ingestion features are validated against strict zero-trust schemas; target and timestamp features are rejected.',
    formula: 'Features: V1–V339, Scaled Amount',
    caseCount: '2,000 Cases',
  },
  stage_core: {
    key: 'stage_core',
    stageName: 'Stage 2: Decision Core',
    title: 'Dual-Model Risk & Disagreement Decomposition',
    badge: 'EVALUATING',
    badgeVariant: 'cyan',
    role: 'Decomposes calibrated risk posterior p (via GBDT + Platt calibrator) against rank-residualized epistemic disagreement u₂ across the model ensemble.',
    formula: 'Risk p in [0,1] vs u₂ Residual',
    caseCount: 'Dual Inference',
  },
  lane_alert: {
    key: 'lane_alert',
    stageName: 'Stage 3: Fraud Alert Lane',
    title: 'Fraud Alert — High-Risk Operational Escalation',
    badge: 'R1_HIGH_RISK',
    badgeVariant: 'coral',
    role: 'Triggered when calibrated risk p >= t_alert (0.0847). High-confidence risk rule with high precision; exempt from analyst review quota. Never routed to routine.',
    formula: 'p >= 0.0847 (t_alert)',
    caseCount: '11 Cases',
  },
  lane_review: {
    key: 'lane_review',
    stageName: 'Stage 3: Manual Review Lane',
    title: 'Manual Review — Human-in-the-Loop Analyst Queue',
    badge: 'CAPACITY_REACHED',
    badgeVariant: 'amber',
    role: 'Triggered by intermediate risk (p >= t_review) or epistemic disagreement (u₂ >= u_th). Escalates to analyst queue up to the strict quota (119 slots filled).',
    formula: 'p >= 0.0710 OR u₂ >= 0.5268',
    caseCount: '119 Cases',
  },
  lane_routine: {
    key: 'lane_routine',
    stageName: 'Stage 3: Routine Clearance Lane',
    title: 'Routine — Consensus Low-Risk Clearance',
    badge: 'R5_LOW_RISK',
    badgeVariant: 'green',
    role: 'Triggered by low risk with confirmed low epistemic disagreement (R5). Fast-path transactions processed automatically with zero analyst friction.',
    formula: 'p < 0.0710 AND u₂ < 0.5268',
    caseCount: '896 Cases',
  },
  lane_deferred: {
    key: 'lane_deferred',
    stageName: 'Stage 3: Held / Deferred Lane',
    title: 'Held / Deferred — Capacity-Governed Deferral',
    badge: 'R6_DEFERRED',
    badgeVariant: 'violet',
    role: 'Triggered when review escalations exceed operational analyst capacity quota B (130 slots max). Staged for delayed audit; never silently cleared into routine.',
    formula: 'Review Queue Overflow > B',
    caseCount: '974 Cases',
  },
};
