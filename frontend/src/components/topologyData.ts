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

export function getTopologyDetails(mode?: string): Record<string, TopologyElementDetail> {
  const m = (mode || '').toUpperCase();
  const isReal = m.includes('IEEE') || m.includes('BENCHMARK') || m.includes('REAL');
  const isLive = m.includes('LIVE') || m.includes('DISCONNECTED');

  if (isLive) {
    return {
      stage_input: {
        key: 'stage_input',
        stageName: 'Stage 1: Input Ingestion',
        title: 'Live Streaming Ingestion Gateway',
        badge: 'DISCONNECTED',
        badgeVariant: 'coral',
        role: 'Live streaming event broker is disconnected (fail-closed). Ingestion pipeline safely paused to prevent unverified processing.',
        formula: 'External Broker: Disconnected',
        caseCount: '0 Cases (Offline)',
      },
      stage_core: {
        key: 'stage_core',
        stageName: 'Stage 2: Decision Core',
        title: 'Dual-Model Risk & Disagreement Decomposition',
        badge: 'IDLE',
        badgeVariant: 'default',
        role: 'GBDT and Platt calibrator stand ready for streaming telemetry. Zero active inferences during disconnected state.',
        formula: 'Risk p in [0,1] vs u₂ Residual',
        caseCount: 'Inference Idle',
      },
      lane_alert: {
        key: 'lane_alert',
        stageName: 'Stage 3: Fraud Alert Lane',
        title: 'Fraud Alert — High-Risk Operational Escalation',
        badge: 'DISCONNECTED',
        badgeVariant: 'coral',
        role: 'High-risk direct alert lane. Inactive while live streaming bus is disconnected.',
        formula: 'p >= 0.0847 (t_alert)',
        caseCount: '0 Cases',
      },
      lane_review: {
        key: 'lane_review',
        stageName: 'Stage 3: Manual Review Lane',
        title: 'Manual Review — Human-in-the-Loop Analyst Queue',
        badge: 'DISCONNECTED',
        badgeVariant: 'amber',
        role: 'Human-in-the-loop analyst review queue. Zero active workload items while stream is disconnected.',
        formula: 'p >= 0.0710 OR u₂ >= 0.5268',
        caseCount: '0 Cases',
      },
      lane_routine: {
        key: 'lane_routine',
        stageName: 'Stage 3: Routine Clearance Lane',
        title: 'Routine — Consensus Low-Risk Clearance',
        badge: 'DISCONNECTED',
        badgeVariant: 'green',
        role: 'Automated settlement fast path. No transactions cleared while ingestion stream is offline.',
        formula: 'p < 0.0710 AND u₂ < 0.5268',
        caseCount: '0 Cases',
      },
      lane_deferred: {
        key: 'lane_deferred',
        stageName: 'Stage 3: Held / Deferred Lane',
        title: 'Held / Deferred — Capacity-Governed Deferral',
        badge: 'DISCONNECTED',
        badgeVariant: 'violet',
        role: 'Operational capacity governor. Fail-closed state ensures zero unmonitored transaction leaks.',
        formula: 'Fail-Closed Disconnect Hold',
        caseCount: '0 Cases',
      },
    };
  }

  if (isReal) {
    return {
      stage_input: {
        key: 'stage_input',
        stageName: 'Stage 1: Input Ingestion',
        title: 'IEEE-CIS Chronological Benchmark Partition',
        badge: 'IEEE_CIS_BENCHMARK',
        badgeVariant: 'cyan',
        role: 'Chronological test partition of 118,108 cases. Schema-verified with zero-trust payload guardrails; target and timestamp features strictly rejected.',
        formula: 'Features: V1–V339, Scaled Amount',
        caseCount: '118,108 Cases',
      },
      stage_core: {
        key: 'stage_core',
        stageName: 'Stage 2: Decision Core',
        title: 'Dual-Model Risk & Disagreement Decomposition',
        badge: 'EVALUATING',
        badgeVariant: 'cyan',
        role: 'Decomposes calibrated risk posterior p (via LightGBM/CatBoost + Platt calibrator) against rank-residualized epistemic disagreement u₂ across 118,108 transactions.',
        formula: 'Risk p in [0,1] vs u₂ Residual',
        caseCount: 'Dual Inference',
      },
      lane_alert: {
        key: 'lane_alert',
        stageName: 'Stage 3: Fraud Alert Lane',
        title: 'Fraud Alert — High-Risk Operational Escalation',
        badge: 'R1_HIGH_RISK',
        badgeVariant: 'coral',
        role: 'Triggered when calibrated risk p >= t_alert (0.0847). 1,280 high-confidence benchmark fraud cases routed directly to immediate freeze.',
        formula: 'p >= 0.0847 (t_alert)',
        caseCount: '1,280 Cases',
      },
      lane_review: {
        key: 'lane_review',
        stageName: 'Stage 3: Manual Review Lane',
        title: 'Manual Review — Human-in-the-Loop Analyst Queue',
        badge: 'CAPACITY_REACHED',
        badgeVariant: 'amber',
        role: 'Triggered by intermediate risk (p >= t_review) or epistemic disagreement (u₂ >= u_th). Escalates 4,713 cases to analyst queue up to the primary capacity cap.',
        formula: 'p >= 0.0710 OR u₂ >= 0.5268',
        caseCount: '4,713 Cases',
      },
      lane_routine: {
        key: 'lane_routine',
        stageName: 'Stage 3: Routine Clearance Lane',
        title: 'Routine — Consensus Low-Risk Clearance',
        badge: 'R5_LOW_RISK',
        badgeVariant: 'green',
        role: 'Triggered by low risk with confirmed low epistemic disagreement (R5). 109,787 fast-path transactions processed automatically with zero analyst friction.',
        formula: 'p < 0.0710 AND u₂ < 0.5268',
        caseCount: '109,787 Cases',
      },
      lane_deferred: {
        key: 'lane_deferred',
        stageName: 'Stage 3: Held / Deferred Lane',
        title: 'Held / Deferred — Capacity-Governed Deferral',
        badge: 'R6_DEFERRED',
        badgeVariant: 'violet',
        role: 'Triggered when review escalations exceed operational analyst capacity quota B (5,993 slots max). 2,328 cases (1.97%) staged for delayed audit; zero silent leakage.',
        formula: 'Review Queue Overflow > B',
        caseCount: '2,328 Cases',
      },
    };
  }

  // Default synthetic smoke fixture
  return TOPOLOGY_DETAILS;
}
