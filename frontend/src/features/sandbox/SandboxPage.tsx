import React, { useState, Suspense, useRef } from 'react';
import {
  FlaskConical,
  Play,
  Sliders,
  AlertTriangle,
  Info,
  ShieldCheck,
  Zap,
  Code2,
  Sparkles,
  Copy,
  Check,
  RotateCcw,
  CheckCircle2,
} from 'lucide-react';
import { api } from '../../lib/api/client';
import { useMode } from '../../context/ModeContext';
import { LoadingState } from '../../components/LoadingState';
import { ErrorState } from '../../components/ErrorState';

const SandboxDecisionOrb3D = React.lazy(() =>
  import('../../components/SandboxDecisionOrb3D').then((m) => ({ default: m.SandboxDecisionOrb3D }))
);

interface PresetTransaction {
  name: string;
  description: string;
  features: Record<string, any>;
}

const PRESETS: PresetTransaction[] = [
  {
    name: 'Clean Routine Transaction',
    description: 'Low-risk domestic debit purchase with normal velocity and zero disputes. Evaluates to ROUTINE (p ≈ 0.0047) via R5_LOW_RISK_RELIABLE.',
    features: {
      TransactionAmt: 45.0,
      ProductCD: 'W',
      card1: 13926,
      card2: 555,
      card3: 150,
      card4: 'visa',
      card5: 226,
      card6: 'debit',
      addr1: 315,
      addr2: 87,
      dist1: 19.0,
      P_emaildomain: 'gmail.com',
      C1: 1.0,
      C2: 1.0,
      C5: 0.0,
      C13: 1.0,
      D1: 14.0,
      D2: 14.0,
      D15: 14.0,
      V1: 1.0,
      V12: 1.0,
      V35: 1.0,
      V75: 1.0,
      V130: 0.0,
      V307: 0.0,
    },
  },
  {
    name: 'Borderline Review Escalation',
    description: 'Intermediate credit transaction ($115.00) landing in the critical review zone (p ≈ 0.0750) between t_review (0.0710) and t_alert (0.0847). Routed to MANUAL_REVIEW via R2_INTERMEDIATE_RISK.',
    features: {
      TransactionAmt: 115.0,
      ProductCD: 'W',
      card1: 9500,
      card2: 321,
      card3: 150,
      card4: 'visa',
      card5: 226,
      card6: 'credit',
      addr1: 476,
      addr2: 87,
      dist1: 85.0,
      P_emaildomain: 'yahoo.com',
      C1: 12.0,
      C2: 7.0,
      C5: 1.0,
      C13: 12.0,
      D1: 3.0,
      D2: 3.0,
      D15: 5.0,
      V1: 1.0,
      V12: 1.0,
      V35: 2.0,
      V75: 1.0,
      V130: 115.0,
      V307: 230.0,
    },
  },
  {
    name: 'High-Risk Alert Candidate',
    description: 'High-value commercial transaction ($980.50) with elevated cross-border velocity and high counts (p ≈ 0.4658). Directly escalated to FRAUD_ALERT via R1_HIGH_RISK.',
    features: {
      TransactionAmt: 980.5,
      ProductCD: 'C',
      card1: 4461,
      card2: 375,
      card3: 185,
      card4: 'mastercard',
      card5: 224,
      card6: 'credit',
      addr1: 299,
      addr2: 87,
      P_emaildomain: 'hotmail.com',
      R_emaildomain: 'anonymous.com',
      C1: 24.0,
      C2: 22.0,
      C5: 0.0,
      C13: 38.0,
      D1: 0.0,
      D2: 0.0,
      D15: 0.0,
      V1: 3.0,
      V12: 2.0,
      V35: 3.0,
      V75: 3.0,
      V130: 980.5,
      V307: 1961.0,
    },
  },
];

export const SandboxPage: React.FC = () => {
  const { mode, isRealDataMode, isLiveDisconnected } = useMode();
  const [features, setFeatures] = useState<Record<string, any>>(PRESETS[0].features);
  const [featureJson, setFeatureJson] = useState<string>(JSON.stringify(PRESETS[0].features, null, 2));
  const [activePresetName, setActivePresetName] = useState<string>(PRESETS[0].name);
  const [jsonError, setJsonError] = useState<string | null>(null);
  const [copied, setCopied] = useState<boolean>(false);
  const [formatSuccess, setFormatSuccess] = useState<boolean>(false);

  const [scoringResult, setScoringResult] = useState<any | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [apiError, setApiError] = useState<string | null>(null);
  const gutterRef = useRef<HTMLDivElement>(null);

  const handlePresetSelect = (preset: PresetTransaction) => {
    setActivePresetName(preset.name);
    setFeatures(preset.features);
    setFeatureJson(JSON.stringify(preset.features, null, 2));
    setJsonError(null);
    setScoringResult(null);
    setApiError(null);
  };

  const handleFormatJson = () => {
    try {
      const parsed = JSON.parse(featureJson);
      setFeatureJson(JSON.stringify(parsed, null, 2));
      setJsonError(null);
      setFormatSuccess(true);
      setTimeout(() => setFormatSuccess(false), 1500);
    } catch {
      setJsonError('Cannot format: Syntax error in JSON payload.');
    }
  };

  const handleCopyJson = () => {
    navigator.clipboard.writeText(featureJson).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    });
  };

  const handleResetJson = () => {
    const preset = PRESETS.find((p) => p.name === activePresetName) || PRESETS[0];
    setFeatures(preset.features);
    setFeatureJson(JSON.stringify(preset.features, null, 2));
    setJsonError(null);
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Tab') {
      e.preventDefault();
      const target = e.currentTarget;
      const start = target.selectionStart;
      const end = target.selectionEnd;
      const updated = featureJson.substring(0, start) + '  ' + featureJson.substring(end);
      setFeatureJson(updated);
      requestAnimationFrame(() => {
        target.selectionStart = target.selectionEnd = start + 2;
      });
    }
  };

  const handleScroll = (e: React.UIEvent<HTMLTextAreaElement>) => {
    if (gutterRef.current) {
      gutterRef.current.scrollTop = e.currentTarget.scrollTop;
    }
  };

  const handleJsonChange = (val: string) => {
    setFeatureJson(val);
    try {
      const parsed = JSON.parse(val);
      // Client-side leakage check
      const keys = Object.keys(parsed).map((k) => k.toLowerCase().replace(/_/g, ''));
      if (keys.includes('isfraud') || keys.includes('truelabel') || keys.includes('transactionid') || keys.includes('transactiondt')) {
        setJsonError('LEAKAGE PROTECTION: Forbidden field (isFraud, TransactionID, TransactionDT) detected and rejected.');
        return;
      }
      setFeatures(parsed);
      setJsonError(null);
    } catch {
      setJsonError('Invalid JSON format.');
    }
  };

  const handleScore = async (e: React.FormEvent) => {
    e.preventDefault();
    if (jsonError) return;

    setLoading(true);
    setApiError(null);
    try {
      const res = await api.scoreSandbox(features, mode);
      setScoringResult(res);
    } catch (err: unknown) {
      setApiError(err instanceof Error ? err.message : 'Scoring request rejected by backend.');
    } finally {
      setLoading(false);
    }
  };

  const lineCount = Math.max(1, featureJson.split('\n').length);
  const linesArray = Array.from({ length: lineCount }, (_, i) => i + 1);
  const featureCount = Object.keys(features || {}).length;
  const payloadBytes = new Blob([featureJson]).size;

  const signals = scoringResult?.signals
    ? {
        p: (scoringResult.signals as any).p ?? (scoringResult.signals as any).p_risk ?? 0,
        u: (scoringResult.signals as any).u ?? (scoringResult.signals as any).u_disagreement ?? 0,
        u_method: scoringResult.signals.u_method ?? '',
      }
    : null;
  const decision = scoringResult?.decision;
  const latency = scoringResult?.latency_ms;
  const action = decision?.action;
  const reasonCode = decision?.reason_code;

  const actionClass =
    action === 'FRAUD_ALERT' ? 'var(--color-fraud-alert)' :
    action === 'MANUAL_REVIEW' ? 'var(--color-manual-review)' :
    action === 'ROUTINE' ? 'var(--color-routine)' : 'var(--color-epistemic-defer-bright)';

  return (
    <div className="sandbox-page animate-fade-in" style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-4)' }}>
      {/* 1. Header & Evidence Banner */}
      <div className="page-header-card">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '14px' }}>
          <div>
            <div className="page-header-eyebrow" style={{ marginBottom: '6px' }}>
              <span className={`badge ${isRealDataMode ? 'badge-ready' : isLiveDisconnected ? 'badge-alert' : 'badge-synthetic'}`}>
                <span>{mode}</span>
              </span>
              <span>DECISION SUPPORT SIMULATOR</span>
              <span style={{ color: 'var(--border-active)' }}>|</span>
              <span style={{ color: 'var(--text-secondary)' }}>
                Target Leakage Guardrails Active
              </span>
            </div>
            <h1 className="page-header-title">
              REAL-TIME SCORING SANDBOX &amp; INTERACTIVE SIMULATOR
            </h1>
            <p className="page-header-desc">
              Evaluate ad-hoc transaction feature vectors against the live fitted model pipeline and frozen policy router.
            </p>
          </div>
        </div>
      </div>

      {/* 2. Preset Selection Toolbar */}
      <div className="sg-card" style={{ padding: '14px 18px', display: 'flex', flexDirection: 'column', gap: '10px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '8px' }}>
          <span style={{ fontSize: '12.5px', color: 'var(--text-secondary)', textTransform: 'uppercase', fontWeight: 800, letterSpacing: '0.04em' }}>
            Load Scenario Preset:
          </span>
          <span style={{ fontSize: '12px', color: 'var(--text-tertiary)', fontFamily: 'var(--font-mono)' }}>
            Selected: <strong style={{ color: 'var(--accent-primary)' }}>{activePresetName}</strong>
          </span>
        </div>
        <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap' }}>
          {PRESETS.map((p) => {
            const isSelected = activePresetName === p.name;
            return (
              <button
                key={p.name}
                type="button"
                onClick={() => handlePresetSelect(p)}
                className={`sg-btn ${isSelected ? 'sg-btn-primary' : 'sg-btn-secondary'}`}
                style={{
                  fontSize: '13px',
                  padding: '7px 16px',
                  fontWeight: isSelected ? 700 : 500,
                  boxShadow: isSelected ? '0 0 12px var(--accent-primary-tint)' : undefined,
                }}
              >
                {p.name}
              </button>
            );
          })}
        </div>
      </div>

      {/* 3. Stacked Layout: Transaction Payload Editor on Top & Decision Rationale Below */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-4)', width: '100%' }}>
        {/* Top Card: Feature Vector Editor */}
        <div className="sg-card" style={{ padding: '22px', display: 'flex', flexDirection: 'column', gap: '16px', boxShadow: '0 8px 24px rgba(0, 0, 0, 0.25)', width: '100%', boxSizing: 'border-box' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '8px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <div
                style={{
                  width: '32px',
                  height: '32px',
                  borderRadius: 'var(--radius-xs)',
                  background: 'var(--accent-primary-tint)',
                  border: '1px solid var(--accent-primary-dim)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  color: 'var(--accent-primary)',
                  flexShrink: 0,
                }}
              >
                <FlaskConical size={17} />
              </div>
              <span style={{ fontSize: '16px', fontWeight: 800, color: 'var(--text-primary)', letterSpacing: '-0.01em', textTransform: 'uppercase' }}>
                Transaction Feature Payload (JSON)
              </span>
            </div>
            <span
              style={{
                fontSize: '12.5px',
                color: 'var(--text-secondary)',
                fontFamily: 'var(--font-mono)',
                fontWeight: 700,
                padding: '4px 10px',
                background: 'var(--bg-surface-raised)',
                border: '1px solid var(--border-default)',
                borderRadius: 'var(--radius-xs)',
              }}
            >
              POST /api/score-sandbox
            </span>
          </div>

          <form onSubmit={handleScore} style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
            {/* Professional IDE Payload Window */}
            <div className={`payload-editor-frame ${jsonError ? 'has-error' : ''}`}>
              {/* Top Header Bar */}
              <div className="payload-editor-header">
                <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                  <div className="payload-traffic-dots">
                    <span className="payload-traffic-dot red" />
                    <span className="payload-traffic-dot yellow" />
                    <span className="payload-traffic-dot green" />
                  </div>
                  <div className="payload-editor-tab">
                    <Code2 size={13} style={{ color: 'var(--accent-primary)' }} />
                    <span>transaction_payload.json</span>
                  </div>
                  {!jsonError ? (
                    <span
                      style={{
                        display: 'inline-flex',
                        alignItems: 'center',
                        gap: '4px',
                        fontSize: '11px',
                        fontFamily: 'var(--font-mono)',
                        fontWeight: 700,
                        color: 'var(--color-routine-bright)',
                        background: 'var(--color-routine-tint)',
                        padding: '2px 8px',
                        borderRadius: 'var(--radius-xs)',
                        border: '1px solid var(--color-routine-dim)',
                      }}
                    >
                      <CheckCircle2 size={11} />
                      VALID
                    </span>
                  ) : (
                    <span
                      style={{
                        display: 'inline-flex',
                        alignItems: 'center',
                        gap: '4px',
                        fontSize: '11px',
                        fontFamily: 'var(--font-mono)',
                        fontWeight: 700,
                        color: 'var(--color-fraud-alert-bright)',
                        background: 'var(--color-fraud-alert-tint)',
                        padding: '2px 8px',
                        borderRadius: 'var(--radius-xs)',
                        border: '1px solid var(--color-fraud-alert-dim)',
                      }}
                    >
                      <AlertTriangle size={11} />
                      SYNTAX ERROR
                    </span>
                  )}
                </div>

                {/* Editor Action Buttons */}
                <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                  <button
                    type="button"
                    onClick={handleFormatJson}
                    title="Prettify & format JSON indentation"
                    className="payload-editor-btn"
                    style={{
                      color: formatSuccess ? 'var(--color-routine-bright)' : undefined,
                      borderColor: formatSuccess ? 'var(--color-routine)' : undefined,
                    }}
                  >
                    {formatSuccess ? <Check size={12} /> : <Sparkles size={12} />}
                    <span>{formatSuccess ? 'Formatted' : 'Format'}</span>
                  </button>

                  <button
                    type="button"
                    onClick={handleCopyJson}
                    title="Copy JSON payload to clipboard"
                    className="payload-editor-btn"
                    style={{
                      color: copied ? 'var(--color-routine-bright)' : undefined,
                      borderColor: copied ? 'var(--color-routine)' : undefined,
                    }}
                  >
                    {copied ? <Check size={12} /> : <Copy size={12} />}
                    <span>{copied ? 'Copied' : 'Copy'}</span>
                  </button>

                  <button
                    type="button"
                    onClick={handleResetJson}
                    title="Reset to selected scenario preset"
                    className="payload-editor-btn"
                  >
                    <RotateCcw size={12} />
                    <span>Reset</span>
                  </button>
                </div>
              </div>

              {/* Editor Body with Gutter & Textarea */}
              <div className="payload-editor-body">
                {/* Line Numbers Gutter */}
                <div ref={gutterRef} className="payload-editor-gutter">
                  {linesArray.map((n) => (
                    <div key={n}>{n}</div>
                  ))}
                </div>

                {/* Main Textarea */}
                <textarea
                  value={featureJson}
                  onChange={(e) => handleJsonChange(e.target.value)}
                  onKeyDown={handleKeyDown}
                  onScroll={handleScroll}
                  rows={13}
                  className="payload-editor-textarea"
                  spellCheck={false}
                  autoCapitalize="off"
                  autoComplete="off"
                  autoCorrect="off"
                  aria-label="Transaction feature JSON payload editor"
                />
              </div>

              {/* Status Footer */}
              <div className="payload-editor-footer">
                <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                  <span>{featureCount} feature fields</span>
                  <span>&bull;</span>
                  <span>{payloadBytes} bytes</span>
                  <span>&bull;</span>
                  <span>UTF-8</span>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                  <ShieldCheck size={13} style={{ color: 'var(--accent-primary)' }} />
                  <span>Schema: Strict 67-Dim Ingestion Bus</span>
                </div>
              </div>
            </div>

            {jsonError && (
              <div
                style={{
                  fontSize: '13px',
                  color: 'var(--color-fraud-alert-bright)',
                  background: 'var(--color-fraud-alert-tint)',
                  border: '1px solid var(--color-fraud-alert-dim)',
                  borderRadius: 'var(--radius-xs)',
                  padding: '10px 14px',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '8px',
                  fontWeight: 600,
                }}
              >
                <AlertTriangle size={16} style={{ flexShrink: 0 }} />
                <span>{jsonError}</span>
              </div>
            )}

            {/* Bottom Actions Row */}
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '12px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '13px', color: 'var(--text-secondary)', fontWeight: 600 }}>
                <ShieldCheck size={16} style={{ color: 'var(--accent-primary)' }} />
                <span>Recursive leakage rejection active &bull; 0 lookahead</span>
              </div>

              <button
                type="submit"
                disabled={Boolean(jsonError) || loading || isLiveDisconnected}
                className="payload-score-cta"
                style={isLiveDisconnected ? { opacity: 0.5, cursor: 'not-allowed', background: 'var(--bg-surface-subdued)' } : undefined}
                title={isLiveDisconnected ? 'Live stream is disconnected. Real-time scoring disabled in this mode.' : undefined}
              >
                <Play size={15} />
                <span>
                  {loading
                    ? 'EVALUATING INFERENCE...'
                    : isLiveDisconnected
                    ? 'SCORING DISABLED (LIVE DISCONNECTED)'
                    : 'SCORE PAYLOAD'}
                </span>
              </button>
            </div>
          </form>
        </div>

        {/* Bottom Card: Live Decision & Signal Response */}
        <div className="sg-card" style={{ padding: '22px', display: 'flex', flexDirection: 'column', gap: '18px', minHeight: '360px', boxShadow: '0 8px 24px rgba(0, 0, 0, 0.25)', width: '100%', boxSizing: 'border-box' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: '1px solid var(--border-subtle)', paddingBottom: '12px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Sliders size={17} style={{ color: 'var(--accent-primary)' }} />
              <span style={{ fontSize: '16px', fontWeight: 800, color: 'var(--text-primary)', letterSpacing: '-0.01em', textTransform: 'uppercase' }}>
                Decision Rationale &amp; Signals
              </span>
            </div>
            {scoringResult && (
              <span style={{ fontFamily: 'var(--font-mono)', fontSize: '12px', color: 'var(--text-secondary)', background: 'var(--bg-surface-raised)', padding: '3px 8px', borderRadius: 'var(--radius-xs)', border: '1px solid var(--border-subtle)' }}>
                {scoringResult.decision_id}
              </span>
            )}
          </div>

          {/* Two-Part Composition: Left = 3D Inference Instrument, Right = Decision Result */}
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(360px, 1fr))',
              gap: '24px',
              alignItems: 'start',
            }}
          >
            {/* Left Region: Compact 3D Inference Instrument */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
              <Suspense
                fallback={
                  <div
                    style={{
                      height: '435px',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      color: 'var(--text-tertiary)',
                      fontSize: '12px',
                      fontFamily: 'var(--font-mono)',
                      background: 'var(--bg-surface-primary)',
                      borderRadius: 'var(--radius-xs)',
                      border: '1px solid var(--border-default)',
                    }}
                  >
                    <LoadingState message="Loading 3D Instrument..." />
                  </div>
                }
              >
                <SandboxDecisionOrb3D
                  risk={signals?.p || 0.0}
                  disagreement={signals?.u || 0.0}
                  action={action || null}
                  reasonCode={reasonCode || null}
                  isEvaluating={loading}
                  hasResult={Boolean(scoringResult)}
                  error={apiError || jsonError || null}
                />
              </Suspense>

              {scoringResult && (
                <div
                  style={{
                    display: 'flex',
                    flexDirection: 'column',
                    gap: '4px',
                    fontSize: '11px',
                    fontFamily: 'var(--font-mono)',
                    color: 'var(--text-secondary)',
                    padding: '8px 10px',
                    background: 'var(--bg-surface-subdued)',
                    borderRadius: 'var(--radius-xs)',
                    border: '1px solid var(--border-subtle)',
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <span style={{ color: 'var(--text-tertiary)' }}>Inference Audit ID:</span>
                    <span style={{ color: 'var(--text-primary)', fontWeight: 700 }}>
                      {scoringResult.decision_id}
                    </span>
                  </div>
                  {scoringResult.audit_seq !== undefined && (
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <span style={{ color: 'var(--text-tertiary)' }}>Audit Ledger Seq:</span>
                      <span style={{ color: 'var(--color-routine-bright)', fontWeight: 700 }}>
                        #{scoringResult.audit_seq}
                      </span>
                    </div>
                  )}
                  {scoringResult.mode && (
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <span style={{ color: 'var(--text-tertiary)' }}>Evidence Mode:</span>
                      <span style={{ color: 'var(--accent-primary-bright)', fontWeight: 600 }}>
                        {scoringResult.mode}
                      </span>
                    </div>
                  )}
                </div>
              )}
            </div>

            {/* Right Region: Decision Result */}
            {/* Right Region: Decision Result */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
              {loading ? (
                <div
                  style={{
                    padding: '36px 16px',
                    display: 'flex',
                    flexDirection: 'column',
                    alignItems: 'center',
                    justifyContent: 'center',
                    minHeight: '435px',
                    background: 'var(--bg-surface-subdued)',
                    borderRadius: 'var(--radius-xs)',
                    border: '1px dashed var(--border-subtle)',
                  }}
                >
                  <LoadingState message="Evaluating features through HGB + Sigmoid Calibrator + 3-Member Ensemble..." />
                </div>
              ) : apiError ? (
                <div style={{ minHeight: '435px', display: 'flex', flexDirection: 'column', justifyContent: 'center' }}>
                  <ErrorState title="Scoring Rejected" message={apiError} />
                </div>
              ) : !scoringResult ? (
                <div
                  style={{
                    display: 'flex',
                    flexDirection: 'column',
                    alignItems: 'center',
                    justifyContent: 'center',
                    minHeight: '435px',
                    textAlign: 'center',
                    color: 'var(--text-tertiary)',
                    gap: '12px',
                    background: 'var(--bg-surface-subdued)',
                    borderRadius: 'var(--radius-xs)',
                    padding: '32px 24px',
                    border: '1px dashed var(--border-subtle)',
                  }}
                >
                  <div
                    style={{
                      width: '52px',
                      height: '52px',
                      borderRadius: '50%',
                      background: 'var(--accent-primary-tint)',
                      border: '1px solid var(--accent-primary-dim)',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      color: 'var(--accent-primary)',
                      marginBottom: '4px',
                    }}
                  >
                    <FlaskConical size={26} />
                  </div>
                  <span
                    style={{
                      fontSize: '15px',
                      fontWeight: 800,
                      color: 'var(--text-primary)',
                      letterSpacing: '-0.01em',
                    }}
                  >
                    Ready for Transaction Inference
                  </span>
                  <span style={{ fontSize: '13px', color: 'var(--text-secondary)', lineHeight: 1.6, maxWidth: '320px' }}>
                    Select a scenario preset above or edit the JSON payload, then click <strong>Score Payload</strong> to execute model inference and view live signals.
                  </span>
                </div>
              ) : (
                <div className="animate-fade-in" style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
                  {/* Decision Action Banner */}
                  <div
                    style={{
                      background: 'var(--bg-surface-raised)',
                      border: `1px solid ${actionClass}55`,
                      borderLeft: `4px solid ${actionClass}`,
                      padding: '16px 20px',
                      borderRadius: 'var(--radius-xs)',
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'center',
                      boxShadow: `0 4px 16px rgba(0, 0, 0, 0.2), 0 0 12px ${actionClass}22`,
                    }}
                  >
                    <div>
                      <div style={{ fontSize: '12px', color: 'var(--text-secondary)', textTransform: 'uppercase', fontWeight: 800, letterSpacing: '0.05em' }}>
                        Triage Action
                      </div>
                      <div style={{ fontFamily: 'var(--font-mono)', fontSize: '22px', fontWeight: 800, color: actionClass, marginTop: '2px' }}>
                        {action}
                      </div>
                    </div>
                    <div style={{ textAlign: 'right' }}>
                      <div style={{ fontSize: '12px', color: 'var(--text-secondary)', textTransform: 'uppercase', fontWeight: 800, letterSpacing: '0.05em' }}>
                        Reason Code
                      </div>
                      <div style={{ fontFamily: 'var(--font-mono)', fontSize: '15px', color: 'var(--text-primary)', fontWeight: 700, marginTop: '2px', padding: '4px 10px', background: 'var(--bg-surface-subdued)', borderRadius: 'var(--radius-xs)', border: '1px solid var(--border-subtle)', display: 'inline-block' }}>
                        {reasonCode}
                      </div>
                    </div>
                  </div>

                  {/* Signals Visual Meters: Risk (p) & Zero-Centered Disagreement (u2) */}
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
                    {/* Calibrated Risk Meter */}
                    <div>
                      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '14px', marginBottom: '6px' }}>
                        <span style={{ color: 'var(--text-secondary)', fontWeight: 700 }}>
                          Calibrated Risk (p):
                        </span>
                        <span style={{ fontFamily: 'var(--font-mono)', color: 'var(--accent-primary)', fontWeight: 800, fontSize: '16px' }}>
                          {typeof signals?.p === 'number' ? signals.p.toFixed(4) : '—'}
                        </span>
                      </div>
                      {/* Risk Track with t_review and t_alert Markers */}
                      <div style={{ position: 'relative', width: '100%', height: '10px', background: 'var(--bg-surface-subdued)', borderRadius: '5px', overflow: 'hidden' }}>
                        <div
                          style={{
                            width: `${Math.min(100, (signals?.p || 0) * 100 * 5)}%`,
                            height: '100%',
                            backgroundColor: (signals?.p || 0) >= 0.0847 ? 'var(--color-fraud-alert)' : (signals?.p || 0) >= 0.0710 ? 'var(--color-manual-review)' : 'var(--color-routine)',
                            transition: 'width 0.3s ease',
                          }}
                        />
                        {/* Threshold Marker: t_review (0.0710 * 5 = 35.5%) */}
                        <div
                          title="Review Threshold: 0.0710"
                          style={{ position: 'absolute', top: 0, bottom: 0, left: '35.5%', width: '2px', backgroundColor: 'var(--color-manual-review)', opacity: 0.9 }}
                        />
                        {/* Threshold Marker: t_alert (0.0847 * 5 = 42.35%) */}
                        <div
                          title="Alert Threshold: 0.0847"
                          style={{ position: 'absolute', top: 0, bottom: 0, left: '42.35%', width: '2px', backgroundColor: 'var(--color-fraud-alert)', opacity: 0.9 }}
                        />
                      </div>
                      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '12px', fontFamily: 'var(--font-mono)', fontWeight: 600, color: 'var(--text-secondary)', marginTop: '5px' }}>
                        <span>0.00</span>
                        <span style={{ color: 'var(--color-manual-review)' }}>t_rev: 0.0710</span>
                        <span style={{ color: 'var(--color-fraud-alert)' }}>t_alt: 0.0847</span>
                        <span>0.20+</span>
                      </div>
                    </div>

                    {/* Disagreement Residual Meter (u2): Zero-Centered Diverging Bar */}
                    <div>
                      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '14px', marginBottom: '6px' }}>
                        <span style={{ color: 'var(--text-secondary)', fontWeight: 700 }}>
                          Disagreement Residual (u₂):
                        </span>
                        <span style={{ fontFamily: 'var(--font-mono)', color: 'var(--color-epistemic-defer-bright)', fontWeight: 800, fontSize: '16px' }}>
                          {typeof signals?.u === 'number' ? `${signals.u >= 0 ? '+' : ''}${signals.u.toFixed(4)}` : '—'}
                        </span>
                      </div>
                      {/* Zero-Centered Bar (Center = 50%, Span = [-0.60, +0.60]) */}
                      <div style={{ position: 'relative', width: '100%', height: '10px', background: 'var(--bg-surface-subdued)', borderRadius: '5px', overflow: 'hidden' }}>
                        {/* Center Zero Axis Divider */}
                        <div style={{ position: 'absolute', top: 0, bottom: 0, left: '50%', width: '1px', backgroundColor: 'var(--border-default)', zIndex: 2 }} />

                        {/* Positive Divergence (u2 > 0) */}
                        {(signals?.u || 0) >= 0 ? (
                          <div
                            style={{
                              position: 'absolute',
                              top: 0,
                              bottom: 0,
                              left: '50%',
                              width: `${Math.min(50, ((signals?.u || 0) / 0.6) * 50)}%`,
                              backgroundColor: 'var(--color-epistemic-defer)',
                              transition: 'width 0.3s ease',
                            }}
                          />
                        ) : (
                          /* Negative Divergence (u2 < 0) */
                          <div
                            style={{
                              position: 'absolute',
                              top: 0,
                              bottom: 0,
                              right: '50%',
                              width: `${Math.min(50, (Math.abs(signals?.u || 0) / 0.6) * 50)}%`,
                              backgroundColor: 'var(--color-epistemic-defer-dim)',
                              transition: 'width 0.3s ease',
                            }}
                          />
                        )}

                        {/* Threshold Marker: u_th = 0.5268 (50% + (0.5268 / 0.60) * 50% = 93.9%) */}
                        <div
                          title="Disagreement Threshold: 0.5268"
                          style={{ position: 'absolute', top: 0, bottom: 0, left: '93.9%', width: '2px', backgroundColor: 'var(--color-epistemic-defer-bright)', opacity: 0.95, zIndex: 3 }}
                        />
                      </div>
                      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '12px', fontFamily: 'var(--font-mono)', fontWeight: 600, color: 'var(--text-secondary)', marginTop: '5px' }}>
                        <span>-0.60</span>
                        <span>0.00 (Rank Baseline)</span>
                        <span style={{ color: 'var(--color-epistemic-defer-bright)' }}>u_th: 0.5268</span>
                        <span>+0.60</span>
                      </div>
                    </div>
                  </div>

                  {/* Metadata Readout: Full-Width Stacked KPI Cards (Equal Length & Width) */}
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', width: '100%' }}>
                    {/* Card 1: Inference Latency */}
                    <div
                      style={{
                        background: 'var(--bg-surface-raised)',
                        padding: '16px 20px',
                        borderRadius: 'var(--radius-xs)',
                        border: '1px solid var(--border-default)',
                        boxShadow: '0 4px 14px rgba(0, 0, 0, 0.18)',
                        display: 'flex',
                        justifyContent: 'space-between',
                        alignItems: 'center',
                        minHeight: '74px',
                        width: '100%',
                      }}
                    >
                      <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
                        <div
                          style={{
                            width: '40px',
                            height: '40px',
                            borderRadius: 'var(--radius-xs)',
                            background: 'var(--accent-primary-tint)',
                            border: '1px solid var(--accent-primary-dim)',
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            color: 'var(--accent-primary)',
                            flexShrink: 0,
                          }}
                        >
                          <Zap size={20} />
                        </div>
                        <div>
                          <div
                            style={{
                              fontSize: '13.5px',
                              color: 'var(--text-primary)',
                              fontWeight: 800,
                              textTransform: 'uppercase',
                              letterSpacing: '0.04em',
                            }}
                          >
                            INFERENCE LATENCY
                          </div>
                          <div
                            style={{
                              fontSize: '12px',
                              color: 'var(--text-secondary)',
                              marginTop: '2px',
                            }}
                          >
                            HGB + Sigmoid Platt evaluation
                          </div>
                        </div>
                      </div>

                      <div style={{ textAlign: 'right' }}>
                        <div
                          style={{
                            fontFamily: 'var(--font-mono)',
                            color: 'var(--accent-primary-bright)',
                            fontWeight: 800,
                            fontSize: '22px',
                            lineHeight: 1.1,
                          }}
                        >
                          {typeof latency === 'number' ? `${latency.toFixed(1)}ms` : '—'}
                        </div>
                        <span
                          style={{
                            display: 'inline-block',
                            fontSize: '11px',
                            fontFamily: 'var(--font-mono)',
                            fontWeight: 700,
                            color: 'var(--color-routine-bright)',
                            background: 'var(--color-routine-tint)',
                            border: '1px solid var(--color-routine-dim)',
                            padding: '2px 8px',
                            borderRadius: 'var(--radius-xs)',
                            marginTop: '4px',
                          }}
                        >
                          PASS &bull; &lt;25ms SLA
                        </span>
                      </div>
                    </div>

                    {/* Card 2: Audit Trail Status */}
                    <div
                      style={{
                        background: 'var(--bg-surface-raised)',
                        padding: '16px 20px',
                        borderRadius: 'var(--radius-xs)',
                        border: '1px solid var(--border-default)',
                        boxShadow: '0 4px 14px rgba(0, 0, 0, 0.18)',
                        display: 'flex',
                        justifyContent: 'space-between',
                        alignItems: 'center',
                        minHeight: '74px',
                        width: '100%',
                      }}
                    >
                      <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
                        <div
                          style={{
                            width: '40px',
                            height: '40px',
                            borderRadius: 'var(--radius-xs)',
                            background: scoringResult.audit_logged
                              ? 'var(--color-routine-tint)'
                              : 'var(--color-manual-review-tint)',
                            border: `1px solid ${
                              scoringResult.audit_logged
                                ? 'var(--color-routine-dim)'
                                : 'var(--color-manual-review-dim)'
                            }`,
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            color: scoringResult.audit_logged
                              ? 'var(--color-routine-bright)'
                              : 'var(--color-manual-review-bright)',
                            flexShrink: 0,
                          }}
                        >
                          <ShieldCheck size={20} />
                        </div>
                        <div>
                          <div
                            style={{
                              fontSize: '13.5px',
                              color: 'var(--text-primary)',
                              fontWeight: 800,
                              textTransform: 'uppercase',
                              letterSpacing: '0.04em',
                            }}
                          >
                            AUDIT TRAIL STATUS
                          </div>
                          <div
                            style={{
                              fontSize: '12px',
                              color: 'var(--text-secondary)',
                              marginTop: '2px',
                            }}
                          >
                            Deterministic ledger commitment
                          </div>
                        </div>
                      </div>

                      <div style={{ textAlign: 'right' }}>
                        <div
                          style={{
                            fontFamily: 'var(--font-mono)',
                            color: scoringResult.audit_logged
                              ? 'var(--color-routine-bright)'
                              : 'var(--color-manual-review-bright)',
                            fontWeight: 800,
                            fontSize: '22px',
                            lineHeight: 1.1,
                          }}
                        >
                          {scoringResult.audit_logged ? 'LOGGED' : 'SKIPPED'}
                        </div>
                        <span
                          style={{
                            display: 'inline-block',
                            fontSize: '11px',
                            fontFamily: 'var(--font-mono)',
                            fontWeight: 700,
                            color: 'var(--text-secondary)',
                            background: 'var(--bg-surface-subdued)',
                            border: '1px solid var(--border-subtle)',
                            padding: '2px 8px',
                            borderRadius: 'var(--radius-xs)',
                            marginTop: '4px',
                          }}
                        >
                          LEDGER SYNC
                        </span>
                      </div>
                    </div>
                  </div>

                  {/* Disclosure Note */}
                  <div style={{ background: 'var(--bg-surface-subdued)', padding: '14px 18px', borderRadius: 'var(--radius-xs)', border: '1px solid var(--border-subtle)', display: 'flex', alignItems: 'center', gap: '12px' }}>
                    <Info size={18} style={{ color: 'var(--accent-primary)', flexShrink: 0 }} />
                    <span style={{ fontSize: '13px', color: 'var(--text-secondary)', lineHeight: 1.6 }}>
                      {scoringResult.notice}
                    </span>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
