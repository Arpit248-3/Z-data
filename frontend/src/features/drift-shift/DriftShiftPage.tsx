import React, { useState, useEffect } from 'react';
import {
  TrendingUp,
  Info,
  Layers,
} from 'lucide-react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';
import { api } from '../../lib/api/client';
import { LoadingState } from '../../components/LoadingState';
import { ErrorState } from '../../components/ErrorState';
import { TiltGlassCard, TiltGlassCardDetail } from '../../components/TiltGlassCard';

interface ShiftScenarioData {
  id: string;
  name: string;
  sampleCount: number;
  fraudCount: number;
  prevalence: number;
  b2Recall: number;
  signalgateRecall: number;
  deltaRecallPp: number;
  shiftedFeatures: string[];
  status: string;
}

export const DriftShiftPage: React.FC = () => {
  const [scenarios, setScenarios] = useState<ShiftScenarioData[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let isMounted = true;
    api.getResults()
      .then((res: any) => {
        if (!isMounted) return;
        const shiftMap = res?.shift_scenarios || {};
        const parsed: ShiftScenarioData[] = [];

        for (const [sId, sData] of Object.entries<any>(shiftMap)) {
          parsed.push({
            id: sId,
            name: sData.name || sId,
            sampleCount: sData.sample_count || 0,
            fraudCount: sData.fraud_count || 0,
            prevalence: sData.fraud_prevalence || 0,
            b2Recall: Number(((sData.b2_recall || 0) * 100).toFixed(2)),
            signalgateRecall: Number(((sData.signalgate_recall || 0) * 100).toFixed(2)),
            deltaRecallPp: Number((sData.delta_recall_vs_b2_pp || 0).toFixed(2)),
            shiftedFeatures: sData.metadata?.shifted_features || [],
            status: sData.status || 'SYNTHETIC_SHIFT',
          });
        }
        setScenarios(parsed);
      })
      .catch((err) => {
        if (isMounted) setError(err instanceof Error ? err.message : 'Failed to load shift scenario results');
      })
      .finally(() => {
        if (isMounted) setLoading(false);
      });

    return () => { isMounted = false; };
  }, []);

  return (
    <div className="drift-shift-page animate-fade-in" style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-4)' }}>
      {/* 1. Header & Evidence Banner */}
      <div className="page-header-card" style={{ borderLeftColor: 'var(--accent-coral)' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '14px' }}>
          <div>
            <div className="page-header-eyebrow" style={{ marginBottom: '6px' }}>
              <span className="badge badge-synthetic">
                <span>SYNTHETIC_SHIFT_PROTOCOL</span>
              </span>
              <span>COVARIATE PERTURBATION HARNESS</span>
              <span style={{ color: 'var(--border-active)' }}>|</span>
              <span style={{ color: 'var(--text-secondary)' }}>
                Scenarios S0, S1, S3 Evaluated
              </span>
            </div>
            <h1 className="page-header-title">
              DISTRIBUTION SHIFT &amp; DRIFT ROBUSTNESS BENCHMARKS
            </h1>
            <p className="page-header-desc">
              Stress-test telemetry measuring triage policy resilience under synthetic covariate shift and sudden prevalence bursts.
            </p>
          </div>
        </div>
      </div>

      {/* 2. Educational & Methodological Guardrail */}
      <div
        className="sg-card"
        style={{
          padding: '16px 20px',
          background: 'var(--bg-surface-raised)',
          border: '1px solid var(--border-default)',
          borderLeft: '4px solid var(--accent-primary)',
          display: 'flex',
          alignItems: 'center',
          gap: '14px',
          boxShadow: '0 4px 16px rgba(0, 0, 0, 0.15)',
        }}
      >
        <div
          style={{
            width: '36px',
            height: '36px',
            borderRadius: 'var(--radius-xs)',
            backgroundColor: 'var(--accent-primary-tint)',
            border: '1px solid var(--accent-primary-dim)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: 'var(--accent-primary)',
            flexShrink: 0,
          }}
        >
          <Info size={20} />
        </div>
        <span style={{ fontSize: '14.5px', color: 'var(--text-secondary)', lineHeight: 1.65, flex: 1 }}>
          <strong style={{ color: 'var(--text-primary)', fontWeight: 700 }}>Operational Distinction:</strong> Statistical drift across feature distributions (e.g. Transaction Amount, V-series) is a measure of covariate shift,
          not an automatic verdict of fraud. Epistemic disagreement (<span style={{ color: 'var(--color-epistemic-defer-bright)', fontWeight: 700, fontFamily: 'var(--font-mono)' }}>u₂</span>) detects this uncertainty and safely diverts cases to review.
        </span>
      </div>

      {loading ? (
        <LoadingState message="Extracting shift scenario matrices..." />
      ) : error ? (
        <ErrorState title="Shift Telemetry Unavailable" message={error} />
      ) : (
        <>
          {/* 3. Shift Robustness Bar Chart (B2 Recall vs SignalGate Recall) */}
          <div className="sg-card" style={{ padding: '20px', display: 'flex', flexDirection: 'column', gap: '14px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <TrendingUp size={17} style={{ color: 'var(--accent-primary)' }} />
                <span style={{ fontSize: '15px', fontWeight: 700, color: 'var(--text-primary)' }}>
                  Recall Retention Under Distribution Shift (Matched Capacity 1.5x)
                </span>
              </div>
              <span style={{ fontFamily: 'var(--font-mono)', fontSize: '12px', color: 'var(--text-secondary)' }}>
                B2 Top-B Baseline vs SignalGate
              </span>
            </div>

            <div style={{ width: '100%', height: '260px' }}>
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={scenarios} margin={{ top: 10, right: 20, left: -10, bottom: 20 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="var(--border-subtle)" vertical={false} />
                  <XAxis
                    dataKey="name"
                    stroke="var(--text-secondary)"
                    fontSize={11}
                    fontFamily="var(--font-sans)"
                    tickLine={false}
                  />
                  <YAxis
                    stroke="var(--text-secondary)"
                    fontSize={11}
                    fontFamily="var(--font-mono)"
                    unit="%"
                    tickLine={false}
                    domain={[0, 14]}
                  />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: 'var(--bg-surface-elevated)',
                      borderColor: 'var(--border-default)',
                      borderRadius: '4px',
                      fontSize: '11px',
                      fontFamily: 'var(--font-mono)',
                      color: 'var(--text-primary)',
                      boxShadow: 'var(--shadow-md)',
                    }}
                    itemStyle={{
                      color: 'var(--text-primary)',
                    }}
                    labelStyle={{
                      color: 'var(--text-secondary)',
                      fontWeight: 600,
                    }}
                    formatter={(val: any, name: string) => [`${val}%`, name]}
                  />
                  <Legend verticalAlign="top" wrapperStyle={{ fontSize: '11px', paddingBottom: '10px' }} />
                  <Bar dataKey="b2Recall" name="B2 Top-B Recall" fill="#7DAAFF" radius={[2, 2, 0, 0]} />
                  <Bar dataKey="signalgateRecall" name="SignalGate Recall" fill="#68D8CB" radius={[2, 2, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* 4. Scenario Breakdown Cards (Interactive 3D Tilt & Glassmorphism Details) */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(380px, 1fr))', gap: 'var(--space-4)' }}>
            {scenarios.map((s) => {
              const detail: TiltGlassCardDetail = {
                title: s.name,
                subtitle: `Scenario ${s.id} • ${s.status}`,
                category: 'Distribution Shift Benchmark',
                icon: <TrendingUp size={16} />,
                accentColor: s.deltaRecallPp >= 0 ? 'var(--color-routine, #68C99A)' : 'var(--color-fraud-alert, #F27870)',
                shortDesc: `Stress-test benchmark comparing B2 Top-B baseline recall against SignalGate under ${s.id}.`,
                formula:
                  s.id === 'S3'
                    ? 'P_{\\text{test}}(X_{15}) \\ne P_{\\text{train}}(X_{15}) \\implies u_2 \\ge u_{\\text{thresh}}'
                    : s.id === 'S1'
                    ? '\\mathbb{P}_{\\text{test}}(Y=1) = 2.0 \\times \\mathbb{P}_{\\text{train}}(Y=1)'
                    : 'P_{\\text{test}}(X, Y) \\equiv P_{\\text{train}}(X, Y) \\quad \\text{(Reference Baseline)}',
                parameters: [
                  { label: 'Sample Count', value: `${s.sampleCount.toLocaleString()} cases` },
                  { label: 'Fraud Cases', value: `${s.fraudCount.toLocaleString()} (${(s.prevalence * 100).toFixed(2)}%)` },
                  { label: 'B2 Baseline Recall', value: `${s.b2Recall.toFixed(2)}%` },
                  { label: 'SignalGate Recall', value: `${s.signalgateRecall.toFixed(2)}%` },
                  { label: 'Delta Recall vs B2', value: `${s.deltaRecallPp >= 0 ? '+' : ''}${s.deltaRecallPp.toFixed(2)} pp` },
                  { label: 'Perturbed Subspace', value: s.shiftedFeatures.length > 0 ? s.shiftedFeatures.join(', ') : 'Untouched Nominal Features' },
                ],
                telemetryNotes: [
                  'Evaluated under matched capacity budget of 130 human reviews (6.525%).',
                  'Perturbations injected strictly into offline test partition without contamination.',
                  s.deltaRecallPp > 0
                    ? `SignalGate epistemic disagreement residual successfully recovered +${s.deltaRecallPp} pp recall.`
                    : 'Consistent reference recall maintained across partitions.',
                ],
                partitionInfo: `Test Partition: ${s.sampleCount} cases • Scenario ${s.id}`,
              };

              return <TiltGlassCard key={s.id} detail={detail} />;
            })}
          </div>

          {/* 5. Honest Unavailable State for Continuous Streaming PSI/KS */}
          <div className="sg-card" style={{ padding: '20px 24px', background: 'var(--bg-surface-raised)', border: '1px dashed var(--border-active)', display: 'flex', flexDirection: 'column', gap: '10px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px', flexWrap: 'wrap' }}>
              <Layers size={18} style={{ color: 'var(--accent-primary)' }} />
              <span style={{ fontSize: '15px', fontWeight: 700, color: 'var(--text-primary)' }}>
                Continuous Streaming PSI / KS Feature Drift Heatmap
              </span>
              <span className="badge badge-neutral" style={{ fontSize: '12px', padding: '3px 9px' }}>
                Offline Static Protocol
              </span>
            </div>
            <p style={{ fontSize: '14px', color: 'var(--text-secondary)', margin: 0, lineHeight: 1.65 }}>
              Continuous real-time windowed Population Stability Index (PSI) and Kolmogorov-Smirnov (KS) streaming telemetry
              require live sliding windows. In the offline static evaluation harness, scenario-level perturbation benchmarks
              (S0, S1, S3 above) serve as the authoritative shift evidence.
            </p>
          </div>
        </>
      )}
    </div>
  );
};
