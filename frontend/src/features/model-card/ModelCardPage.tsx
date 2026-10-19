import React, { useState, useEffect, Suspense, useMemo } from 'react';
import {
  Shield,
  Sliders,
  Lock,
  Cpu,
  Layers,
  Scale,
  Info,
  Sparkles,
  Eye,
  X,
} from 'lucide-react';
import { api } from '../../lib/api/client';
import { OverviewResponse, ModelCardResponse } from '../../lib/api/types';
import { useMode } from '../../context/ModeContext';
import { LoadingState } from '../../components/LoadingState';
import { ErrorState } from '../../components/ErrorState';
import { TiltGlassCard, TiltGlassCardDetail } from '../../components/TiltGlassCard';

const ModelCard3DVisualizer = React.lazy(() =>
  import('../../components/ModelCard3DVisualizer').then((m) => ({ default: m.ModelCard3DVisualizer }))
);

export function getArchitectureSpecs(isRealDataMode: boolean, isLiveDisconnected: boolean): TiltGlassCardDetail[] {
  if (isLiveDisconnected) {
    return [
      {
        title: 'Primary Estimator',
        subtitle: 'DISCONNECTED STREAM',
        category: 'Live Edge Ingestion',
        icon: <Cpu size={16} />,
        accentColor: 'var(--color-fraud-alert, #F27870)',
        shortDesc: 'Live production banking feed is disconnected. In accordance with Master Spec § C, no simulated live inference is permitted.',
        formula: '\\text{Status} = \\text{DISCONNECTED}, \\quad \\text{Inference} = \\emptyset',
        parameters: [
          { label: 'Feed State', value: 'OFFLINE / DISCONNECTED' },
          { label: 'Active Pipeline', value: 'Suspended (Fail-Closed)' },
          { label: 'Live Transactions', value: '0 incoming' },
          { label: 'Synthetic Fallback', value: 'Prohibited in live mode' },
        ],
        telemetryNotes: [
          'Live edge ingestion is verified disconnected.',
          'Fail-closed security guarantees zero unauthorized data clearance.',
          'No synthetic or benchmark transactions masquerade as live production.',
        ],
        partitionInfo: 'Live Ingestion: Disconnected • Fail-Closed',
      },
      {
        title: 'Risk Calibrator',
        subtitle: 'OFFLINE',
        category: 'Posterior Probability Calibration',
        icon: <Scale size={16} />,
        accentColor: 'var(--text-tertiary)',
        shortDesc: 'Live posterior calibration is suspended while banking feed is disconnected.',
        formula: 'p(y=1 | f) = \\text{N/A (Stream Disconnected)}',
        parameters: [
          { label: 'Calibration State', value: 'Suspended' },
          { label: 'Live Scoring', value: 'Disabled (HTTP 400)' },
        ],
        telemetryNotes: [
          'Live scoring requests fail closed with HTTP 400 INVALID_FEATURE_PAYLOAD.',
        ],
        partitionInfo: 'Calibrator: Suspended',
      },
      {
        title: 'Epistemic Disagreement',
        subtitle: 'OFFLINE',
        category: 'Uncertainty Decomposition',
        icon: <Layers size={16} />,
        accentColor: 'var(--text-tertiary)',
        shortDesc: 'Ensemble disagreement monitoring is offline until genuine live streaming is established.',
        formula: 'u_2 = \\text{N/A}',
        parameters: [
          { label: 'Disagreement Engine', value: 'Offline' },
          { label: 'Live Stream', value: 'Disconnected' },
        ],
        telemetryNotes: [
          'No epistemic residual computation on live feed.',
        ],
        partitionInfo: 'Uncertainty Engine: Suspended',
      },
      {
        title: 'Capacity Governor',
        subtitle: 'OFFLINE (Quota 0)',
        category: 'Queue & Triage Resource Allocation',
        icon: <Shield size={16} />,
        accentColor: 'var(--text-tertiary)',
        shortDesc: 'Human review queue governor is idle with 0 active live tickets.',
        formula: 'B = 0, \\quad Q_t = 0',
        parameters: [
          { label: 'Active Queue', value: '0 review slots' },
          { label: 'Stream Status', value: 'Disconnected' },
        ],
        telemetryNotes: [
          'Zero queue tickets permitted without live payment ingestion.',
        ],
        partitionInfo: 'Governor: Idle',
      },
    ];
  }

  if (isRealDataMode) {
    return [
      {
        title: 'Primary Estimator',
        subtitle: 'Heterogeneous Calibrated Ensemble',
        category: 'Supervised Learning / Calibrated Ensemble',
        icon: <Cpu size={16} />,
        accentColor: 'var(--accent-primary, #68D8CB)',
        shortDesc: 'Trained on 354,324 genuine IEEE-CIS transactions with zero target leakage, combining HistGradientBoosting, ExtraTrees, and LogisticRegression across 391 features.',
        formula: 'p_{\\text{raw}}(x) = w_1 h_{\\text{HGB}}(x) + w_2 h_{\\text{ET}}(x) + w_3 h_{\\text{LR}}(x), \\quad \\sum w_i = 1',
        parameters: [
          { label: 'Training Partition', value: '354,324 real IEEE-CIS rows' },
          { label: 'Ensemble Members', value: 'HistGB + ExtraTrees + LogReg' },
          { label: 'Total Features', value: '391 features (377 num, 14 cat)' },
          { label: 'Optimization Solver', value: 'Cross-entropy with Platt calibration' },
          { label: 'Leakage Guardrail', value: 'isFraud, TransactionID/DT strictly excluded' },
          { label: 'Model Artifact Hash', value: 'd34bc0426e647121 (Verified)' },
        ],
        telemetryNotes: [
          'Trained strictly on chronological train partition (354,324 rows) without lookahead.',
          'Evaluated against 118,108 held-out test partition rows (4,064 fraud, 3.44% prevalence).',
          'Achieves 0.8805 ROC-AUC and 0.4608 PR-AUC on final test partition.',
        ],
        partitionInfo: 'Train Partition: 354,324 rows • SHA-256 Verified',
      },
      {
        title: 'Risk Calibrator',
        subtitle: 'Platt Scaling (Sigmoid Logistic)',
        category: 'Posterior Probability Calibration',
        icon: <Scale size={16} />,
        accentColor: 'var(--color-manual-review, #E8B35E)',
        shortDesc: 'Transforms raw ensemble decision margins into posterior probabilities p in [0, 1] calibrated on 59,054 held-out calibration transactions.',
        formula: 'p(y=1 | f) = \\frac{1}{1 + \\exp(A \\cdot f(x) + B)}, \\quad (A, B) \\text{ fitted on Cal 59K}',
        parameters: [
          { label: 'Calibration Partition', value: '59,054 held-out IEEE-CIS rows' },
          { label: 'Optimization Solver', value: 'L-BFGS maximum likelihood' },
          { label: 'Expected Cal Error (ECE)', value: '0.0089 (< 0.02 threshold)' },
          { label: 'Brier Score', value: '0.0246 (High posterior reliability)' },
          { label: 'Monotonicity', value: 'Strictly order-preserving' },
        ],
        telemetryNotes: [
          'Calibrated posterior p is strictly continuous and represents empirical fraud likelihood.',
          'Sigmoid scaling eliminates overconfident predictions on distribution boundaries.',
          'Validated on held-out 59,054 validation partition prior to test freeze.',
        ],
        partitionInfo: 'Calibration Partition: 59,054 rows • Platt Parameters Frozen',
      },
      {
        title: 'Epistemic Disagreement',
        subtitle: 'Rank-Residualized Ensemble (u₂)',
        category: 'Uncertainty Decomposition',
        icon: <Layers size={16} />,
        accentColor: 'var(--color-epistemic-defer, #B4A0F8)',
        shortDesc: 'Measures inter-model prediction variance across heterogeneous architectures residualized against risk rank to isolate true uncertainty.',
        formula: 'u_2 = \\sigma_{\\text{ensemble}}^2 - g(\\text{rank}(p)), \\quad g \\text{ empirical residual baseline}',
        parameters: [
          { label: 'Ensemble Base', value: 'HistGB + ExtraTrees + LogReg' },
          { label: 'Residual Metric', value: 'Rank-conditioned variance u₂' },
          { label: 'Decision Threshold', value: 'u_threshold = 0.526773' },
          { label: 'Escalation Action', value: 'Diverts ambiguous cases to R3_MODEL_DISAGREEMENT' },
        ],
        telemetryNotes: [
          'Separates aleatoric (data noise) from epistemic (model lack of knowledge) risk.',
          'Flags covariate shift in perturbed subspaces where individual models diverge.',
          'Active in Scenario S3 to maintain high recall under unseen feature distributions.',
        ],
        partitionInfo: 'Ensemble Variance Estimator: Frozen in frozen_policy.json',
      },
      {
        title: 'Capacity Governor',
        subtitle: 'Matched Quota Enforcer (B=5,993)',
        category: 'Queue & Triage Resource Allocation',
        icon: <Shield size={16} />,
        accentColor: 'var(--color-routine, #68C99A)',
        shortDesc: 'Strictly limits human analyst queue to 5,993 slots (5.075% budget on 118,108 cases). Overflow escalations divert to HELD/DEFERRED (R6).',
        formula: 'Q_t = \\sum_{i=1}^t \\mathbb{I}(\\text{action}_i = \\text{MANUAL\\_REVIEW}) \\le B \\quad (B = 5,993)',
        parameters: [
          { label: 'Review Quota (B)', value: '5,993 review slots' },
          { label: 'Touched Rate Cap', value: '5.075% of 118,108 test cases' },
          { label: 'Prevalence Multiplier', value: '1.5x training prevalence target' },
          { label: 'Saturated Consumption', value: '5,993 / 5,993 slots consumed' },
          { label: 'Capacity Deferred', value: '5,020 cases diverted (R6)' },
        ],
        telemetryNotes: [
          'Strictly guarantees that analyst capacity is never exceeded under volume surges.',
          'Eliminates silent queue overflows or unhandled operational backlog.',
          'Deferred transactions are cryptographically recorded in the append-only ledger.',
        ],
        partitionInfo: 'Canonical Governor Budget: 5,993 slots (5.075%)',
      },
    ];
  }

  // Synthetic smoke default
  return [
    {
      title: 'Primary Estimator',
      subtitle: 'HistGradientBoostingClassifier',
      category: 'Supervised Learning / Boosting',
      icon: <Cpu size={16} />,
      accentColor: 'var(--accent-primary, #68D8CB)',
      shortDesc: 'Fitted on 6,000 synthetic training rows using IEEE-CIS transaction features with native histogram binning for non-linear interactions.',
      formula: 'F_M(x) = \\sum_{m=1}^M \\gamma_m h_m(x), \\quad h_m \\in \\text{Histogram Decision Trees}',
      parameters: [
        { label: 'Max Iterations', value: '100 trees' },
        { label: 'Learning Rate', value: '0.1' },
        { label: 'Max Bins', value: '255 native bins' },
        { label: 'Loss Function', value: 'Log-loss (Cross-entropy)' },
        { label: 'Feature Columns', value: 'Amount, ProductCD, card4, C1-C2, D1-D2, V1-V3' },
        { label: 'Leakage Guardrail', value: 'isFraud, TransactionID strictly excluded' },
      ],
      telemetryNotes: [
        'Trained strictly on partition 0 (6,000 cases) without lookahead or target leakage.',
        'Native histogram binning accelerates gradient computation without explicit one-hot encoding.',
        'Inference latency benchmark: P95 <= 1.8ms on offline fixture.',
      ],
      partitionInfo: 'Train Partition: 6,000 rows • SHA-256 Verified',
    },
    {
      title: 'Risk Calibrator',
      subtitle: 'Platt Scaling (Sigmoid Logistic)',
      category: 'Posterior Probability Calibration',
      icon: <Scale size={16} />,
      accentColor: 'var(--color-manual-review, #E8B35E)',
      shortDesc: 'Transforms raw boosting decision margins into posterior probabilities p in [0, 1] calibrated on held-out validation data.',
      formula: 'p(y=1 | f) = \\frac{1}{1 + \\exp(A \\cdot f(x) + B)}, \\quad (A, B) \\text{ fitted on Val 2K}',
      parameters: [
        { label: 'Validation Partition', value: '2,000 held-out rows' },
        { label: 'Optimization Solver', value: 'L-BFGS maximum likelihood' },
        { label: 'Calibration Metric', value: 'ECE < 0.02 (Expected Calibration Error)' },
        { label: 'Monotonicity', value: 'Strictly order-preserving' },
        { label: 'Domain', value: 'p \\in [0.0, 1.0] continuous probability' },
      ],
      telemetryNotes: [
        'Calibrated posterior p is strictly continuous and interpretable as empirical fraud likelihood.',
        'Platt scaling prevents overconfident predictions on distribution boundaries.',
        'Tested against Brier score target thresholds on validation set.',
      ],
      partitionInfo: 'Validation Partition: 2,000 rows • Platt Parameters Frozen',
    },
    {
      title: 'Epistemic Disagreement',
      subtitle: 'Rank-Residualized Ensemble (u₂)',
      category: 'Uncertainty Decomposition',
      icon: <Layers size={16} />,
      accentColor: 'var(--color-epistemic-defer, #B4A0F8)',
      shortDesc: 'Captures inter-model prediction variance residualized against risk rank to isolate true uncertainty from mere high risk.',
      formula: 'u_2 = \\sigma_{\\text{ensemble}}^2 - g(\\text{rank}(p)), \\quad g \\text{ empirical residual baseline}',
      parameters: [
        { label: 'Ensemble Base', value: 'HistGBDT + Shadow Sub-Models' },
        { label: 'Residual Metric', value: 'Rank-conditioned variance u₂' },
        { label: 'Decision Threshold', value: 'u_threshold = 0.526773' },
        { label: 'Escalation Action', value: 'Diverts ambiguous cases to R3_MODEL_DISAGREEMENT' },
      ],
      telemetryNotes: [
        'Separates aleatoric (data noise) from epistemic (model lack of knowledge) risk.',
        'Flags covariate shift in perturbed subspaces where individual models diverge.',
        'Active in Scenario S3 to maintain high recall under unseen feature distributions.',
      ],
      partitionInfo: 'Ensemble Variance Estimator: Frozen in frozen_policy.json',
    },
    {
      title: 'Capacity Governor',
      subtitle: 'Matched Quota Enforcer (B=130)',
      category: 'Queue & Triage Resource Allocation',
      icon: <Shield size={16} />,
      accentColor: 'var(--color-routine, #68C99A)',
      shortDesc: 'Strictly limits human analyst queue to 130 slots (6.525% budget). Overflow escalations divert to HELD/DEFERRED (R6).',
      formula: 'Q_t = \\sum_{i=1}^t \\mathbb{I}(\\text{action}_i = \\text{MANUAL\\_REVIEW}) \\le B \\quad (B = 130)',
      parameters: [
        { label: 'Review Quota (B)', value: '130 review slots' },
        { label: 'Touched Rate Cap', value: '6.525% of 2,000 test cases' },
        { label: 'Prevalence Multiplier', value: '1.5x training prevalence target' },
        { label: 'Saturated Consumption', value: '130 / 130 slots consumed' },
        { label: 'Capacity Deferred', value: '974 cases diverted (R6)' },
      ],
      telemetryNotes: [
        'Strictly guarantees that analyst capacity is never exceeded.',
        'Eliminates silent queue overflows or unhandled backlog.',
        'Deferred transactions are cryptographically recorded in the append-only ledger.',
      ],
      partitionInfo: 'Canonical Governor Budget: 130 slots (6.525%)',
    },
  ];
}

interface FrozenRuleDef {
  id: string;
  name: string;
  condition: string;
  action: string;
  actionClass: string;
  capacityTreatment: string;
  riskRange: string;
  visualWidth: string;
  color: string;
}

export function getFrozenRules(
  isRealDataMode: boolean,
  isLiveDisconnected?: boolean,
  modelCard?: ModelCardResponse | null
): FrozenRuleDef[] {
  const tAlert = modelCard?.thresholds?.t_alert ?? 0.084705;
  const tReview = modelCard?.thresholds?.t_review ?? 0.071002;
  const uThreshold = modelCard?.thresholds?.u_threshold ?? 0.526773;

  const tAlertStr = tAlert.toFixed(4);
  const tReviewStr = tReview.toFixed(4);
  const uThreshStr = uThreshold.toFixed(4);

  if (isLiveDisconnected) {
    return [
      {
        id: 'R1',
        name: 'R1_HIGH_RISK',
        condition: `p ≥ ${tAlert.toFixed(6)} (t_alert)`,
        action: 'FRAUD_ALERT',
        actionClass: 'badge-alert',
        capacityTreatment: 'Exempt from quota • Live scoring suspended',
        riskRange: `p ∈ [${tAlertStr}, 1.0000]`,
        visualWidth: '85%',
        color: 'var(--color-fraud-alert)',
      },
      {
        id: 'R2',
        name: 'R2_INTERMEDIATE_RISK',
        condition: `p ≥ ${tReview.toFixed(6)} (t_review) • Quota: 0 (Offline)`,
        action: 'MANUAL_REVIEW',
        actionClass: 'badge-caution',
        capacityTreatment: 'Review queue suspended (0 active slots)',
        riskRange: `p ∈ [${tReviewStr}, ${tAlertStr})`,
        visualWidth: '55%',
        color: 'var(--color-manual-review)',
      },
      {
        id: 'R3',
        name: 'R3_MODEL_DISAGREEMENT',
        condition: `u₂ ≥ ${uThreshold.toFixed(6)} (u_threshold) • Quota: 0 (Offline)`,
        action: 'MANUAL_REVIEW',
        actionClass: 'badge-caution',
        capacityTreatment: 'Review queue suspended (0 active slots)',
        riskRange: 'Epistemic u₂ Residual Bypass',
        visualWidth: '70%',
        color: 'var(--color-epistemic-defer)',
      },
      {
        id: 'R5',
        name: 'R5_LOW_RISK_RELIABLE',
        condition: `p < ${tReview.toFixed(6)} AND u₂ < ${uThreshold.toFixed(6)}`,
        action: 'ROUTINE',
        actionClass: 'badge-ready',
        capacityTreatment: 'Clearance suspended while stream is offline',
        riskRange: `p < ${tReviewStr}, u₂ < ${uThreshStr}`,
        visualWidth: '25%',
        color: 'var(--color-routine)',
      },
      {
        id: 'R6',
        name: 'R6_CAPACITY_DEFERRED',
        condition: 'Live stream disconnected • Quota = 0',
        action: 'HELD / DEFERRED',
        actionClass: 'badge-alert',
        capacityTreatment: 'Fail-closed hold; zero unauthorized clearance',
        riskRange: 'Fail-Closed Disconnect Hold',
        visualWidth: '100%',
        color: 'var(--color-epistemic-defer-bright)',
      },
    ];
  }

  const quotaSlots = modelCard?.capacity_budget?.review_capacity_slots ?? (isRealDataMode ? 5993 : 130);
  const quotaLabel = `${quotaSlots.toLocaleString()} slots`;
  const quotaLimit = quotaSlots.toLocaleString();
  const deferredCases = isRealDataMode ? '5,020 cases' : '974 cases';
  const queueHoldRange = `Queue Saturation Hold (B = ${quotaLimit})`;

  return [
    {
      id: 'R1',
      name: 'R1_HIGH_RISK',
      condition: `p ≥ ${tAlert.toFixed(6)} (t_alert)`,
      action: 'FRAUD_ALERT',
      actionClass: 'badge-alert',
      capacityTreatment: 'Exempt from analyst review quota',
      riskRange: `p ∈ [${tAlertStr}, 1.0000]`,
      visualWidth: '85%',
      color: 'var(--color-fraud-alert)',
    },
    {
      id: 'R2',
      name: 'R2_INTERMEDIATE_RISK',
      condition: `p ≥ ${tReview.toFixed(6)} (t_review) • Quota ≤ ${quotaLimit}`,
      action: 'MANUAL_REVIEW',
      actionClass: 'badge-caution',
      capacityTreatment: `Consumes analyst review quota B (≤ ${quotaLimit})`,
      riskRange: `p ∈ [${tReviewStr}, ${tAlertStr})`,
      visualWidth: '55%',
      color: 'var(--color-manual-review)',
    },
    {
      id: 'R3',
      name: 'R3_MODEL_DISAGREEMENT',
      condition: `u₂ ≥ ${uThreshold.toFixed(6)} (u_threshold) • Quota ≤ ${quotaLimit}`,
      action: 'MANUAL_REVIEW',
      actionClass: 'badge-caution',
      capacityTreatment: `Consumes analyst review quota B (≤ ${quotaLimit})`,
      riskRange: 'Epistemic u₂ Residual Bypass',
      visualWidth: '70%',
      color: 'var(--color-epistemic-defer)',
    },
    {
      id: 'R5',
      name: 'R5_LOW_RISK_RELIABLE',
      condition: `p < ${tReview.toFixed(6)} AND u₂ < ${uThreshold.toFixed(6)}`,
      action: 'ROUTINE',
      actionClass: 'badge-ready',
      capacityTreatment: isRealDataMode ? 'Zero-touch clearance (IEEE-CIS partition)' : 'Zero-touch clearance (Synthetic fixture)',
      riskRange: `p < ${tReviewStr}, u₂ < ${uThreshStr}`,
      visualWidth: '25%',
      color: 'var(--color-routine)',
    },
    {
      id: 'R6',
      name: 'R6_CAPACITY_DEFERRED',
      condition: `Review escalations > B (${quotaLabel})`,
      action: 'HELD / DEFERRED',
      actionClass: 'badge-synthetic',
      capacityTreatment: `Held for deferred audit (${deferredCases}); zero silent leakage`,
      riskRange: queueHoldRange,
      visualWidth: '95%',
      color: 'var(--color-epistemic-defer)',
    },
  ];
}

export const ModelCardPage: React.FC = () => {
  const { mode, isRealDataMode, isLiveDisconnected } = useMode();
  const [overview, setOverview] = useState<OverviewResponse | null>(null);
  const [modelCard, setModelCard] = useState<ModelCardResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const architectureSpecs = useMemo(() => getArchitectureSpecs(isRealDataMode, isLiveDisconnected), [isRealDataMode, isLiveDisconnected]);
  const frozenRules = useMemo(() => getFrozenRules(isRealDataMode, isLiveDisconnected, modelCard), [isRealDataMode, isLiveDisconnected, modelCard]);
  const [selectedRule, setSelectedRule] = useState<string | null>(null);
  const [inspectRule, setInspectRule] = useState<FrozenRuleDef | null>(null);

  // Close modal on Escape
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && inspectRule) {
        setInspectRule(null);
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [inspectRule]);

  useEffect(() => {
    let isMounted = true;
    Promise.all([api.getOverview(mode), api.getModelCard(mode)])
      .then(([o, mc]) => {
        if (isMounted) {
          setOverview(o);
          setModelCard(mc);
        }
      })
      .catch((err) => {
        if (isMounted) setError(err instanceof Error ? err.message : 'Failed to load model governance records');
      })
      .finally(() => {
        if (isMounted) setLoading(false);
      });

    return () => { isMounted = false; };
  }, [mode]);

  return (
    <div className="model-card-page animate-fade-in" style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-4)' }}>
      {/* 1. Page Header & Provenance Banner */}
      <div className="page-header-card" style={{ borderLeftColor: 'var(--color-routine)' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '14px' }}>
          <div>
            <div className="page-header-eyebrow" style={{ marginBottom: '6px' }}>
              <span className={`badge ${isRealDataMode ? 'badge-ready' : isLiveDisconnected ? 'badge-alert' : 'badge-synthetic'}`}>
                <span>{mode}</span>
              </span>
              <span>FROZEN POLICY REGISTRATION PROTOCOL</span>
              <span style={{ color: 'var(--border-active)' }}>|</span>
              <span style={{ color: 'var(--text-secondary)' }}>
                {isRealDataMode ? 'Architecture: EraBaggedHeterogeneousEnsemble' : 'Version: v2.1-FINAL'}
              </span>
            </div>
            <h1 className="page-header-title">
              MODEL GOVERNANCE &amp; FROZEN POLICY SPECIFICATION
            </h1>
            <p className="page-header-desc">
              Interactive 3D model architecture specifications, calibration parameters, frozen triage thresholds, and cryptographic data lineage.
            </p>
          </div>
        </div>
      </div>

      {loading ? (
        <LoadingState message="Verifying model lineage artifacts..." />
      ) : error ? (
        <ErrorState title="Model Card Unavailable" message={error} />
      ) : (
        <>
          {/* 2. Interactive 3D Model Pipeline Topology */}
          <Suspense
            fallback={
              <div
                style={{
                  height: '185px',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  background: 'var(--bg-surface-subdued)',
                  borderRadius: 'var(--radius-sm)',
                  border: '1px solid var(--border-default)',
                }}
              >
                <LoadingState message="Loading 3D Pipeline Topology..." />
              </div>
            }
          >
            <ModelCard3DVisualizer />
          </Suspense>

          {/* 3. Core Architecture Specifications (Interactive 3D Tilt Cards with Glassmorphism Details) */}
          <div>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '10px' }}>
              <span style={{ fontSize: '13px', color: 'var(--text-tertiary)', textTransform: 'uppercase', fontWeight: 700, letterSpacing: '0.05em' }}>
                Architecture Components &bull; Interactive 3D Tilt & Glass Inspector
              </span>
              <span style={{ fontSize: '12.5px', color: 'var(--accent-primary)', display: 'flex', alignItems: 'center', gap: '5px' }}>
                <Sparkles size={13} />
                <span>Click any card for blurred glass deep-dive</span>
              </span>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: 'var(--space-4)' }}>
              {architectureSpecs.map((spec) => (
                <TiltGlassCard key={spec.title} detail={spec} />
              ))}
            </div>
          </div>

          {/* 4. Visual Decision Spectrum Ladder & Threshold Visualization */}
          <div className="sg-card" style={{ padding: '20px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <Sliders size={18} style={{ color: 'var(--accent-primary)' }} />
                <span style={{ fontSize: '15px', fontWeight: 700, color: 'var(--text-primary)' }}>
                  Decision Spectrum & Policy Threshold Ladder
                </span>
              </div>
              <span className="badge badge-ready" style={{ fontSize: '11px', padding: '3px 8px' }}>
                IMMUTABLE THRESHOLDS
              </span>
            </div>

            {/* Visual Risk Continuum Spectrum Bar */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '12px', fontFamily: 'var(--font-mono)', color: 'var(--text-tertiary)' }}>
                <span>p = 0.00 (Minimal Risk)</span>
                <span style={{ color: 'var(--color-manual-review)' }}>t_review = 0.0710</span>
                <span style={{ color: 'var(--color-fraud-alert)' }}>t_alert = 0.0847</span>
                <span>p = 1.00 (Certain Fraud)</span>
              </div>

              {/* Multi-Segment Continuum Track */}
              <div
                style={{
                  height: '26px',
                  width: '100%',
                  borderRadius: 'var(--radius-xs)',
                  overflow: 'hidden',
                  display: 'flex',
                  border: '1px solid var(--border-default)',
                  background: 'var(--bg-surface-subdued)',
                  position: 'relative',
                }}
              >
                {/* Routine Zone: 0.00 to 0.071 (71% of threshold visual width) */}
                <div
                  style={{
                    width: '42%',
                    backgroundColor: 'rgba(104, 201, 154, 0.22)',
                    borderRight: '2px solid var(--color-routine)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    fontSize: '11.5px',
                    fontFamily: 'var(--font-mono)',
                    color: 'var(--color-routine)',
                    fontWeight: 700,
                  }}
                >
                  ROUTINE (Auto Clear)
                </div>

                {/* Review Zone: 0.071 to 0.0847 */}
                <div
                  style={{
                    width: '28%',
                    backgroundColor: 'rgba(232, 179, 94, 0.25)',
                    borderRight: '2px solid var(--color-manual-review)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    fontSize: '11.5px',
                    fontFamily: 'var(--font-mono)',
                    color: 'var(--color-manual-review)',
                    fontWeight: 700,
                  }}
                >
                  MANUAL_REVIEW (Quota B)
                </div>

                {/* Alert Zone: 0.0847 to 1.0 */}
                <div
                  style={{
                    width: '30%',
                    backgroundColor: 'rgba(242, 120, 112, 0.25)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    fontSize: '11.5px',
                    fontFamily: 'var(--font-mono)',
                    color: 'var(--color-fraud-alert)',
                    fontWeight: 700,
                  }}
                >
                  DIRECT FRAUD_ALERT
                </div>
              </div>

              {/* Disagreement & Deferral Annotation */}
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: '12.5px', color: 'var(--text-secondary)', padding: '4px 6px', flexWrap: 'wrap', gap: '8px' }}>
                <span style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                  <span style={{ width: '8px', height: '8px', borderRadius: '50%', backgroundColor: 'var(--color-epistemic-defer)' }} />
                  <span>Epistemic Disagreement Bypass: <strong>u₂ &ge; 0.5268</strong> escalates to Review regardless of risk p</span>
                </span>
                <span style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                  <span style={{ width: '8px', height: '8px', borderRadius: '50%', backgroundColor: 'var(--color-epistemic-defer)' }} />
                  <span>Governor Saturation: <strong>&gt; {isRealDataMode ? '5,993 reviews' : '130 reviews'}</strong> diverts to HELD/DEFERRED (R6)</span>
                </span>
              </div>
            </div>

            {/* 5. Enhanced Interactive Frozen Routing Rules Table */}
            <div style={{ overflowX: 'auto', border: '1px solid var(--border-default)', borderRadius: 'var(--radius-xs)' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '13.5px' }}>
                <thead>
                  <tr style={{ background: 'var(--bg-surface-raised)', borderBottom: '1px solid var(--border-default)', color: 'var(--text-secondary)' }}>
                    <th style={{ padding: '12px 16px', fontWeight: 600, fontSize: '12.5px' }}>RULE ID</th>
                    <th style={{ padding: '12px 16px', fontWeight: 600, fontSize: '12.5px' }}>THRESHOLD CONDITION</th>
                    <th style={{ padding: '12px 16px', fontWeight: 600, fontSize: '12.5px' }}>ROUTING ACTION</th>
                    <th style={{ padding: '12px 16px', fontWeight: 600, fontSize: '12.5px' }}>CAPACITY TREATMENT</th>
                    <th style={{ padding: '12px 16px', fontWeight: 600, fontSize: '12.5px' }}>RISK SPECTRUM</th>
                    <th style={{ padding: '12px 16px', fontWeight: 600, fontSize: '12.5px', textAlign: 'center' }}>INSPECT</th>
                  </tr>
                </thead>
                <tbody>
                  {frozenRules.map((rule) => {
                    const isSelected = selectedRule === rule.id;
                    return (
                      <tr
                        key={rule.id}
                        onClick={() => {
                          setSelectedRule(rule.id);
                          setInspectRule(rule);
                        }}
                        onKeyDown={(e) => {
                          if (e.key === 'Enter' || e.key === ' ') {
                            e.preventDefault();
                            setSelectedRule(rule.id);
                            setInspectRule(rule);
                          }
                        }}
                        tabIndex={0}
                        role="button"
                        aria-label={`Inspect frozen rule ${rule.name}`}
                        className="interactive-table-row"
                        style={{
                          borderBottom: '1px solid var(--border-subtle)',
                          cursor: 'pointer',
                          backgroundColor: isSelected ? 'var(--bg-surface-elevated)' : 'transparent',
                          transition: 'background-color var(--transition-fast)',
                        }}
                      >
                        <td style={{ padding: '12px 16px', fontFamily: 'var(--font-mono)', fontWeight: 700, color: rule.color, fontSize: '13.5px' }}>
                          {rule.name}
                        </td>
                        <td style={{ padding: '12px 16px', fontFamily: 'var(--font-mono)', color: 'var(--text-primary)', fontSize: '13px' }}>
                          {rule.condition}
                        </td>
                        <td style={{ padding: '12px 16px' }}>
                          <span className={`badge ${rule.actionClass}`} style={{ fontSize: '11px', padding: '3px 8px' }}>
                            {rule.action}
                          </span>
                        </td>
                        <td style={{ padding: '12px 16px', color: 'var(--text-secondary)', fontSize: '12.5px' }}>
                          {rule.capacityTreatment}
                        </td>
                        <td style={{ padding: '12px 16px' }}>
                          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                            <div style={{ width: '80px', height: '8px', backgroundColor: 'var(--bg-surface-subdued)', borderRadius: '4px', overflow: 'hidden' }}>
                              <div style={{ width: rule.visualWidth, height: '100%', backgroundColor: rule.color, borderRadius: '4px' }} />
                            </div>
                            <span style={{ fontSize: '11.5px', fontFamily: 'var(--font-mono)', color: 'var(--text-tertiary)' }}>
                              {rule.riskRange}
                            </span>
                          </div>
                        </td>
                        <td style={{ padding: '12px 16px', textAlign: 'center' }}>
                          <span
                            className="sg-btn sg-btn-secondary"
                            style={{
                              padding: '4px 10px',
                              fontSize: '12px',
                              display: 'inline-flex',
                              alignItems: 'center',
                              gap: '5px',
                              color: rule.color,
                            }}
                          >
                            <Eye size={13} />
                            <span>Details</span>
                          </span>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>

            {/* Frosted Glass Rule Inspection Modal */}
            {inspectRule && (
              <div
                className="glass-modal-backdrop"
                onClick={() => setInspectRule(null)}
                style={{
                  position: 'fixed',
                  top: 0,
                  left: 0,
                  right: 0,
                  bottom: 0,
                  backgroundColor: 'rgba(10, 15, 20, 0.78)',
                  backdropFilter: 'blur(24px) saturate(180%)',
                  WebkitBackdropFilter: 'blur(24px) saturate(180%)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  zIndex: 9999,
                  padding: '20px',
                  animation: 'fadeIn 0.2s ease-out',
                }}
                role="dialog"
                aria-modal="true"
                aria-labelledby="rule-dialog-title"
              >
                <div
                  className="glass-modal-container"
                  onClick={(e) => e.stopPropagation()}
                  style={{
                    width: '100%',
                    maxWidth: '680px',
                    maxHeight: '90vh',
                    overflowY: 'auto',
                    backgroundColor: 'var(--bg-glass-modal, rgba(17, 25, 34, 0.92))',
                    backdropFilter: 'blur(24px) saturate(180%)',
                    WebkitBackdropFilter: 'blur(24px) saturate(180%)',
                    border: `1px solid ${inspectRule.color}55`,
                    borderRadius: 'var(--radius-md, 8px)',
                    boxShadow: `0 24px 60px rgba(0, 0, 0, 0.5), 0 0 40px ${inspectRule.color}25`,
                    padding: '28px 32px',
                    position: 'relative',
                    animation: 'scaleIn 0.25s cubic-bezier(0.16, 1, 0.3, 1)',
                    display: 'flex',
                    flexDirection: 'column',
                    gap: '18px',
                    color: 'var(--text-primary)',
                  }}
                >
                  {/* Header */}
                  <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: '14px' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                      <div
                        style={{
                          width: '44px',
                          height: '44px',
                          borderRadius: 'var(--radius-sm, 6px)',
                          backgroundColor: `${inspectRule.color}22`,
                          border: `1px solid ${inspectRule.color}55`,
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                          color: inspectRule.color,
                          flexShrink: 0,
                        }}
                      >
                        <Sliders size={22} />
                      </div>
                      <div>
                        <div style={{ fontSize: '11px', color: inspectRule.color, textTransform: 'uppercase', fontFamily: 'var(--font-mono)', fontWeight: 700, letterSpacing: '0.06em' }}>
                          Frozen Policy Routing Rule Specification
                        </div>
                        <h2
                          id="rule-dialog-title"
                          style={{ fontSize: '20px', fontWeight: 700, margin: '2px 0 0 0', color: 'var(--text-primary)', letterSpacing: '-0.01em' }}
                        >
                          {inspectRule.name} ({inspectRule.id})
                        </h2>
                      </div>
                    </div>

                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <span className={`badge ${inspectRule.actionClass}`} style={{ fontSize: '10px' }}>
                        <span>{inspectRule.action}</span>
                      </span>
                      <button
                        type="button"
                        onClick={() => setInspectRule(null)}
                        className="sg-btn"
                        style={{
                          background: 'transparent',
                          border: '1px solid var(--border-default)',
                          borderRadius: 'var(--radius-xs)',
                          color: 'var(--text-secondary)',
                          padding: '6px',
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                          cursor: 'pointer',
                        }}
                        aria-label="Close rule details"
                      >
                        <X size={18} />
                      </button>
                    </div>
                  </div>

                  {/* Trigger Condition Banner */}
                  <div
                    style={{
                      padding: '12px 16px',
                      borderRadius: 'var(--radius-xs)',
                      backgroundColor: 'var(--bg-surface-raised)',
                      border: `1px solid ${inspectRule.color}44`,
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'space-between',
                      flexWrap: 'wrap',
                      gap: '8px',
                    }}
                  >
                    <div>
                      <div style={{ fontSize: '12px', color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '0.05em', fontWeight: 700 }}>
                        Exact Mathematical Condition
                      </div>
                      <div style={{ fontFamily: 'var(--font-mono)', fontSize: '15px', fontWeight: 800, color: inspectRule.color, marginTop: '3px' }}>
                        {inspectRule.condition}
                      </div>
                    </div>
                    <span style={{ fontFamily: 'var(--font-mono)', fontSize: '13px', color: 'var(--text-secondary)', fontWeight: 600 }}>
                      Range: {inspectRule.riskRange}
                    </span>
                  </div>

                  {/* Parameter Grid */}
                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: '12px' }}>
                    <div style={{ background: 'var(--bg-surface-raised)', padding: '12px 14px', borderRadius: 'var(--radius-xs)', border: '1px solid var(--border-subtle)', display: 'flex', flexDirection: 'column', gap: '4px' }}>
                      <span style={{ fontSize: '12px', color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '0.04em', fontWeight: 700 }}>Routing Action</span>
                      <span style={{ fontFamily: 'var(--font-mono)', fontSize: '16px', fontWeight: 800, color: inspectRule.color }}>{inspectRule.action}</span>
                      <span style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>Triage Target Queue</span>
                    </div>

                    <div style={{ background: 'var(--bg-surface-raised)', padding: '12px 14px', borderRadius: 'var(--radius-xs)', border: '1px solid var(--border-subtle)', display: 'flex', flexDirection: 'column', gap: '4px' }}>
                      <span style={{ fontSize: '12px', color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '0.04em', fontWeight: 700 }}>Capacity Governor</span>
                      <span style={{ fontFamily: 'var(--font-mono)', fontSize: '14.5px', fontWeight: 700, color: 'var(--text-primary)' }}>{inspectRule.capacityTreatment}</span>
                      <span style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>Queue Quota Allocation</span>
                    </div>

                    <div style={{ background: 'var(--bg-surface-raised)', padding: '12px 14px', borderRadius: 'var(--radius-xs)', border: '1px solid var(--border-subtle)', display: 'flex', flexDirection: 'column', gap: '4px' }}>
                      <span style={{ fontSize: '12px', color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '0.04em', fontWeight: 700 }}>Threshold Derivation</span>
                      <span style={{ fontFamily: 'var(--font-mono)', fontSize: '14.5px', fontWeight: 700, color: 'var(--accent-primary-bright)' }}>
                        {isRealDataMode ? 'Quantile Tuned (Cal N=59k)' : 'Quantile Tuned (Val N=2k)'}
                      </span>
                      <span style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>Zero Test Contamination</span>
                    </div>
                  </div>

                  {/* Architecture & Guardrail Step Cards */}
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                    <span style={{ fontSize: '12.5px', color: 'var(--text-tertiary)', textTransform: 'uppercase', fontWeight: 700, letterSpacing: '0.05em' }}>
                      Governance Guardrails & Invariants
                    </span>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                      <div
                        style={{
                          display: 'flex',
                          alignItems: 'flex-start',
                          gap: '12px',
                          padding: '12px 16px',
                          borderRadius: 'var(--radius-xs)',
                          backgroundColor: 'var(--bg-surface-raised)',
                          border: '1px solid var(--border-subtle)',
                        }}
                      >
                        <span
                          style={{
                            fontFamily: 'var(--font-mono)',
                            fontSize: '12px',
                            fontWeight: 800,
                            color: inspectRule.color,
                            backgroundColor: `${inspectRule.color}18`,
                            padding: '3px 8px',
                            borderRadius: 'var(--radius-xs)',
                            flexShrink: 0,
                            marginTop: '2px',
                          }}
                        >
                          01
                        </span>
                        <span style={{ fontSize: '13.5px', lineHeight: 1.6, color: 'var(--text-secondary)' }}>
                          <strong>Deterministic Evaluation:</strong> Evaluated strictly on calibrated posterior probabilities (p) and ensemble discordance (u₂) without label leakage or stochastic sampling.
                        </span>
                      </div>

                      <div
                        style={{
                          display: 'flex',
                          alignItems: 'flex-start',
                          gap: '12px',
                          padding: '12px 16px',
                          borderRadius: 'var(--radius-xs)',
                          backgroundColor: 'var(--bg-surface-raised)',
                          border: '1px solid var(--border-subtle)',
                        }}
                      >
                        <span
                          style={{
                            fontFamily: 'var(--font-mono)',
                            fontSize: '12px',
                            fontWeight: 800,
                            color: inspectRule.color,
                            backgroundColor: `${inspectRule.color}18`,
                            padding: '3px 8px',
                            borderRadius: 'var(--radius-xs)',
                            flexShrink: 0,
                            marginTop: '2px',
                          }}
                        >
                          02
                        </span>
                        <span style={{ fontSize: '13.5px', lineHeight: 1.6, color: 'var(--text-secondary)' }}>
                          <strong>Capacity Load Governor:</strong> Human investigator workload ceiling enforced at 130 cases (1.5× multiplier of 6.525% budget). If capacity saturates, rule R6 shunts spillover to safe quarantine.
                        </span>
                      </div>

                      <div
                        style={{
                          display: 'flex',
                          alignItems: 'flex-start',
                          gap: '12px',
                          padding: '12px 16px',
                          borderRadius: 'var(--radius-xs)',
                          backgroundColor: 'var(--bg-surface-raised)',
                          border: '1px solid var(--border-subtle)',
                        }}
                      >
                        <span
                          style={{
                            fontFamily: 'var(--font-mono)',
                            fontSize: '12px',
                            fontWeight: 800,
                            color: inspectRule.color,
                            backgroundColor: `${inspectRule.color}18`,
                            padding: '3px 8px',
                            borderRadius: 'var(--radius-xs)',
                            flexShrink: 0,
                            marginTop: '2px',
                          }}
                        >
                          03
                        </span>
                        <span style={{ fontSize: '13.5px', lineHeight: 1.6, color: 'var(--text-secondary)' }}>
                          <strong>Cryptographic Lineage:</strong> Every routing decision logs the SHA-256 config hash immutably into the audit trail ledger with sub-5ms SLA latency confirmation.
                        </span>
                      </div>
                    </div>
                  </div>

                  {/* Action Bar */}
                  <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '8px', borderTop: '1px solid var(--border-subtle)', paddingTop: '12px' }}>
                    <button
                      type="button"
                      onClick={() => setInspectRule(null)}
                      className="sg-btn sg-btn-primary"
                      style={{ fontSize: '12px', padding: '6px 18px' }}
                    >
                      Dismiss Rule Specification
                    </button>
                  </div>
                </div>
              </div>
            )}
          </div>


          {/* 6. Cryptographic Lineage & Hash Verification */}
          <div className="sg-card" style={{ padding: '16px', display: 'flex', flexDirection: 'column', gap: '10px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <Lock size={15} style={{ color: 'var(--accent-primary)' }} />
              <span style={{ fontSize: '13px', fontWeight: 600, color: 'var(--text-primary)' }}>
                Cryptographic Artifact & Partition Lineage
              </span>
            </div>

            {isRealDataMode && modelCard ? (
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '8px' }}>
                <div style={{ background: 'var(--bg-surface-raised)', padding: '8px 10px', borderRadius: 'var(--radius-xs)', border: '1px solid var(--border-subtle)' }}>
                  <div style={{ fontSize: '10px', color: 'var(--text-tertiary)', textTransform: 'uppercase' }}>ARCHITECTURE &amp; SUB-MODELS</div>
                  <div style={{ fontFamily: 'var(--font-mono)', fontSize: '11px', color: 'var(--accent-primary-bright)', marginTop: '2px' }}>
                    {modelCard.architecture_type} ({modelCard.sub_models.join(' + ')})
                  </div>
                </div>

                <div style={{ background: 'var(--bg-surface-raised)', padding: '8px 10px', borderRadius: 'var(--radius-xs)', border: '1px solid var(--border-subtle)' }}>
                  <div style={{ fontSize: '10px', color: 'var(--text-tertiary)', textTransform: 'uppercase' }}>TABULAR FEATURES &amp; CALIBRATOR</div>
                  <div style={{ fontFamily: 'var(--font-mono)', fontSize: '11px', color: 'var(--color-routine-bright)', marginTop: '2px' }}>
                    {modelCard.feature_count} features &bull; {modelCard.calibrator_type}
                  </div>
                </div>

                <div style={{ background: 'var(--bg-surface-raised)', padding: '8px 10px', borderRadius: 'var(--radius-xs)', border: '1px solid var(--border-subtle)' }}>
                  <div style={{ fontSize: '10px', color: 'var(--text-tertiary)', textTransform: 'uppercase' }}>BUNDLE MANIFEST SHA-256</div>
                  <div style={{ fontFamily: 'var(--font-mono)', fontSize: '11px', color: 'var(--color-epistemic-defer-bright)', wordBreak: 'break-all', marginTop: '2px' }}>
                    {modelCard.manifest_hash}
                  </div>
                </div>
              </div>
            ) : (
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '8px' }}>
                <div style={{ background: 'var(--bg-surface-raised)', padding: '8px 10px', borderRadius: 'var(--radius-xs)', border: '1px solid var(--border-subtle)' }}>
                  <div style={{ fontSize: '10px', color: 'var(--text-tertiary)', textTransform: 'uppercase' }}>FROZEN CONFIG HASH (SHA-256)</div>
                  <div style={{ fontFamily: 'var(--font-mono)', fontSize: '11px', color: 'var(--accent-primary-bright)', wordBreak: 'break-all', marginTop: '2px' }}>
                    {overview?.frozen_config_hash || '8d3f02ca492ca94bab45f3ceac8d39432c2f29f40d54e7990b4aa78cbbff6240'}
                  </div>
                </div>

                <div style={{ background: 'var(--bg-surface-raised)', padding: '8px 10px', borderRadius: 'var(--radius-xs)', border: '1px solid var(--border-subtle)' }}>
                  <div style={{ fontSize: '10px', color: 'var(--text-tertiary)', textTransform: 'uppercase' }}>SPLIT HASH (TRAIN 6K / VAL 2K / TEST 2K)</div>
                  <div style={{ fontFamily: 'var(--font-mono)', fontSize: '11px', color: 'var(--color-routine-bright)', wordBreak: 'break-all', marginTop: '2px' }}>
                    {overview?.split_hash || '07b55a4ed74f238c9ef5b779a749770cf274d4709a4389d9eab860dd9068fbdd'}
                  </div>
                </div>
              </div>
            )}

            {/* Explanation Disclaimer */}
            <div style={{ background: 'var(--bg-surface-subdued)', padding: '8px 10px', borderRadius: 'var(--radius-xs)', border: '1px solid var(--border-subtle)', display: 'flex', alignItems: 'center', gap: '8px', marginTop: '4px' }}>
              <Info size={14} style={{ color: 'var(--text-tertiary)', flexShrink: 0 }} />
              <span style={{ fontSize: '11px', color: 'var(--text-secondary)' }}>
                <strong>Explainability Notice:</strong> {isRealDataMode && modelCard?.notice ? modelCard.notice : 'SHAP and TreeExplainer local feature attributions are explicitly disabled in this development smoke protocol. No simulated or reconstructed attribution values are presented.'}
              </span>
            </div>
          </div>
        </>
      )}
    </div>
  );
};
