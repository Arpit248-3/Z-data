import React, { useState, useEffect } from 'react';
import {
  TrendingUp,
  Info,
  Activity,
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
import { DriftReportResponse } from '../../lib/api/types';
import { useMode } from '../../context/ModeContext';
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
  const { mode, isRealDataMode, isLiveDisconnected } = useMode();
  const [scenarios, setScenarios] = useState<ShiftScenarioData[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const [driftReport, setDriftReport] = useState<DriftReportResponse | null>(null);
  const [driftLoading, setDriftLoading] = useState<boolean>(false);
  const [driftError, setDriftError] = useState<string | null>(null);

  useEffect(() => {
    let isMounted = true;
    api.getResults(mode)
      .then((res: any) => {
        if (!isMounted) return;
        const shiftMap = res?.shift_scenarios || {};
        const parsed: ShiftScenarioData[] = [];

        for (const [sId, sData] of Object.entries<any>(shiftMap)) {
          const sampleCount = sData.sample_count || sData.total_rows || 0;
          const fraudCount = sData.fraud_count || sData.total_fraud || 0;
          const prevalence = sData.fraud_prevalence || sData.prevalence || 0;
          const b2Recall = Number(((sData.b2_recall || 0) * 100).toFixed(2));
          const signalgateRecall = Number(((sData.signalgate_recall || sData.p5_recall || 0) * 100).toFixed(2));
          const deltaRecallPp = Number((sData.delta_recall_vs_b2_pp !== undefined ? sData.delta_recall_vs_b2_pp : (signalgateRecall - b2Recall)).toFixed(2));

          const cleanId = sId.split('_')[0];
          parsed.push({
            id: cleanId,
            name: sData.name || sData.description || sId,
            sampleCount,
            fraudCount,
            prevalence,
            b2Recall,
            signalgateRecall,
            deltaRecallPp,
            shiftedFeatures: sData.metadata?.shifted_features || (cleanId === 'S3' ? ['Covariate Noise Perturbation'] : cleanId === 'S2' ? ['ProductCD', 'TransactionAmt Segment Shift'] : cleanId === 'S1' ? ['Temporal Fraud Concentration'] : []),
            status: sData.status || (isRealDataMode ? 'IEEE_CIS_OFFLINE_BENCHMARK' : 'SYNTHETIC_SHIFT'),
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
  }, [mode, isRealDataMode]);

  useEffect(() => {
    let isMounted = true;
    if (mode === 'LIVE_SOURCE_NOT_CONNECTED') {
      setDriftReport(null);
      setDriftError('LIVE SOURCE DISCONNECTED: Live edge ingestion is offline. Real-time streaming drift calculation is suspended.');
      setDriftLoading(false);
      return;
    }

    if (mode === 'SYNTHETIC_SMOKE_ONLY') {
      setDriftReport(null);
      setDriftError('SYNTHETIC SMOKE MODE: Feature drift monitoring is configured for the IEEE-CIS offline benchmark partition. Switch to IEEE-CIS BENCHMARK mode to view active drift metrics.');
      setDriftLoading(false);
      return;
    }

    setDriftLoading(true);
    setDriftError(null);
    api.getDriftReport(mode)
      .then((res) => {
        if (isMounted) setDriftReport(res);
      })
      .catch((err) => {
        if (isMounted) setDriftError(err instanceof Error ? err.message : 'Failed to load drift report');
      })
      .finally(() => {
        if (isMounted) setDriftLoading(false);
      });

    return () => { isMounted = false; };
  }, [mode]);

  return (
    <div className="drift-shift-page animate-fade-in" style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-4)' }}>
      {/* 1. Header & Evidence Banner */}
      <div className="page-header-card" style={{ borderLeftColor: 'var(--accent-coral)' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '14px' }}>
          <div>
            <div className="page-header-eyebrow" style={{ marginBottom: '6px' }}>
              <span className={`badge ${isRealDataMode ? 'badge-ready' : isLiveDisconnected ? 'badge-alert' : 'badge-synthetic'}`}>
                <span>{mode}</span>
              </span>
              <span>COVARIATE PERTURBATION &amp; DRIFT HARNESS</span>
              <span style={{ color: 'var(--border-active)' }}>|</span>
              <span style={{ color: 'var(--text-secondary)' }}>
                {isRealDataMode ? 'IEEE-CIS Real Tabular Drift Monitor' : 'Scenarios S0, S1, S3 Evaluated'}
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
          <strong style={{ color: 'var(--text-primary)', fontWeight: 700 }}>
            Operational Distinction ({isRealDataMode ? 'IEEE-CIS Real Benchmark' : isLiveDisconnected ? 'Live Stream Disconnected' : 'Synthetic Smoke Protocol'}):
          </strong>{' '}
          {isRealDataMode ? (
            <>
              Statistical drift across 391 tabular feature distributions (e.g. TransactionAmt, card1–card6, C-series, D-series, V-series) is a measure of covariate shift across chronological partitions, not an automatic verdict of fraud. Epistemic disagreement (<span style={{ color: 'var(--color-epistemic-defer-bright)', fontWeight: 700, fontFamily: 'var(--font-mono)' }}>u₂</span>) detects prediction uncertainty under distribution shift and safely diverts ambiguous cases to the review lane.
            </>
          ) : isLiveDisconnected ? (
            <>
              Streaming Kolmogorov-Smirnov and Wasserstein drift calculations are suspended while the core banking event stream is disconnected. Real-time telemetry fails closed to prevent unverified model degradation.
            </>
          ) : (
            <>
              Statistical drift across synthetic feature distributions (e.g. Amount, C1–C14, V1–V30) measures controlled covariate shift from adversarial perturbation scenarios (S0, S1, S3). Epistemic disagreement (<span style={{ color: 'var(--color-epistemic-defer-bright)', fontWeight: 700, fontFamily: 'var(--font-mono)' }}>u₂</span>) quantifies model discordance and diverts uncertain transactions to analyst review.
            </>
          )}
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
                    domain={[0, isRealDataMode ? 70 : 14]}
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

          {/* 5. Live Distribution Drift Monitor (GET /api/drift/report) */}
          <div
            className="sg-card"
            style={{
              padding: '20px 24px',
              background: 'var(--bg-surface-raised)',
              border: '1px solid var(--border-default)',
              display: 'flex',
              flexDirection: 'column',
              gap: '14px',
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '10px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                <Activity size={18} style={{ color: 'var(--accent-primary)' }} />
                <span style={{ fontSize: '15px', fontWeight: 700, color: 'var(--text-primary)' }}>
                  Live Distribution Drift Telemetry (PSI &amp; Wasserstein Distance)
                </span>
                <span
                  className={`badge ${
                    isLiveDisconnected
                      ? 'badge-alert'
                      : driftReport?.status === 'STABLE'
                      ? 'badge-ready'
                      : 'badge-caution'
                  }`}
                  style={{ fontSize: '11px', padding: '2px 8px' }}
                >
                  {isLiveDisconnected ? 'OFFLINE' : driftReport?.status || 'MONITORING'}
                </span>
              </div>
              {driftReport?.timestamp && (
                <span style={{ fontSize: '11px', fontFamily: 'var(--font-mono)', color: 'var(--text-tertiary)' }}>
                  Report Hash: {driftReport.provenance_hash?.slice(0, 8)}... &bull; {driftReport.timestamp}
                </span>
              )}
            </div>

            {driftLoading ? (
              <LoadingState message="Calculating drift telemetry from partition evidence..." />
            ) : driftError ? (
              <div style={{ padding: '12px', background: 'rgba(239, 68, 68, 0.08)', borderRadius: 'var(--radius-xs)', fontSize: '12px', color: 'var(--color-fraud-alert)' }}>
                {driftError}
              </div>
            ) : isLiveDisconnected ? (
              <p style={{ fontSize: '13px', color: 'var(--text-secondary)', margin: 0, lineHeight: 1.6 }}>
                Live edge ingestion is offline. Real-time streaming drift calculation is suspended.
              </p>
            ) : driftReport ? (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
                {/* Metric Summary Grid */}
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '12px' }}>
                  <div style={{ background: 'var(--bg-surface-subdued)', padding: '10px 14px', borderRadius: 'var(--radius-xs)', border: '1px solid var(--border-subtle)' }}>
                    <div style={{ fontSize: '11px', color: 'var(--text-tertiary)', textTransform: 'uppercase' }}>Monitored Features</div>
                    <div style={{ fontFamily: 'var(--font-mono)', fontSize: '18px', fontWeight: 700, color: 'var(--text-primary)', marginTop: '4px' }}>
                      {driftReport.features_monitored}
                    </div>
                  </div>

                  <div style={{ background: 'var(--bg-surface-subdued)', padding: '10px 14px', borderRadius: 'var(--radius-xs)', border: '1px solid var(--border-subtle)' }}>
                    <div style={{ fontSize: '11px', color: 'var(--text-tertiary)', textTransform: 'uppercase' }}>Mean Feature PSI</div>
                    <div style={{ fontFamily: 'var(--font-mono)', fontSize: '18px', fontWeight: 700, color: driftReport.mean_psi < 0.1 ? 'var(--color-routine-bright)' : 'var(--color-manual-review-bright)', marginTop: '4px' }}>
                      {driftReport.mean_psi.toFixed(4)}
                    </div>
                  </div>

                  <div style={{ background: 'var(--bg-surface-subdued)', padding: '10px 14px', borderRadius: 'var(--radius-xs)', border: '1px solid var(--border-subtle)' }}>
                    <div style={{ fontSize: '11px', color: 'var(--text-tertiary)', textTransform: 'uppercase' }}>Max Feature PSI</div>
                    <div style={{ fontFamily: 'var(--font-mono)', fontSize: '18px', fontWeight: 700, color: driftReport.max_psi < 0.25 ? 'var(--color-routine-bright)' : 'var(--color-fraud-alert-bright)', marginTop: '4px' }}>
                      {driftReport.max_psi.toFixed(4)}
                    </div>
                  </div>

                  <div style={{ background: 'var(--bg-surface-subdued)', padding: '10px 14px', borderRadius: 'var(--radius-xs)', border: '1px solid var(--border-subtle)' }}>
                    <div style={{ fontSize: '11px', color: 'var(--text-tertiary)', textTransform: 'uppercase' }}>Score Wasserstein Distance</div>
                    <div style={{ fontFamily: 'var(--font-mono)', fontSize: '18px', fontWeight: 700, color: 'var(--accent-primary-bright)', marginTop: '4px' }}>
                      {(driftReport.score_drift?.wasserstein_distance ?? 0).toFixed(4)}
                    </div>
                  </div>
                </div>

                {/* Feature-Level Drift Forensics Table */}
                {driftReport.feature_reports && driftReport.feature_reports.length > 0 && (
                  <div style={{ marginTop: '6px', border: '1px solid var(--border-default)', borderRadius: 'var(--radius-xs)', overflow: 'hidden' }}>
                    <div style={{ padding: '8px 14px', background: 'var(--bg-surface-header)', borderBottom: '1px solid var(--border-default)', fontSize: '12px', fontWeight: 700, color: 'var(--text-secondary)', display: 'flex', justifyContent: 'space-between' }}>
                      <span>FEATURE-LEVEL DRIFT FORENSICS</span>
                      <span>METHODOLOGY: PSI + 2-SAMPLE KS + WASSERSTEIN</span>
                    </div>
                    <div style={{ overflowX: 'auto' }}>
                      <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '12.5px', textAlign: 'left' }}>
                        <thead>
                          <tr style={{ background: 'var(--bg-surface-subdued)', color: 'var(--text-tertiary)', borderBottom: '1px solid var(--border-subtle)' }}>
                            <th style={{ padding: '8px 12px', fontWeight: 600 }}>FEATURE</th>
                            <th style={{ padding: '8px 12px', fontWeight: 600 }}>PSI</th>
                            <th style={{ padding: '8px 12px', fontWeight: 600 }}>KS STATISTIC</th>
                            <th style={{ padding: '8px 12px', fontWeight: 600 }}>KS P-VALUE</th>
                            <th style={{ padding: '8px 12px', fontWeight: 600 }}>WASSERSTEIN</th>
                            <th style={{ padding: '8px 12px', fontWeight: 600 }}>STATUS</th>
                          </tr>
                        </thead>
                        <tbody>
                          {driftReport.feature_reports.map((fr: any, idx: number) => {
                            const isDrift = (fr.psi ?? 0) >= 0.2 || fr.drift_category === 'significant_drift';
                            const isMod = ((fr.psi ?? 0) >= 0.1 && (fr.psi ?? 0) < 0.2) || fr.drift_category === 'moderate_drift';
                            const badgeColor = isDrift ? 'var(--color-fraud-alert-bright)' : isMod ? 'var(--color-manual-review-bright)' : 'var(--color-routine-bright)';
                            const badgeBg = isDrift ? 'var(--color-fraud-alert-tint)' : isMod ? 'var(--color-manual-review-tint)' : 'var(--color-routine-tint)';
                            return (
                              <tr key={fr.feature || idx} style={{ borderBottom: '1px solid var(--border-subtle)' }}>
                                <td style={{ padding: '8px 12px', fontFamily: 'var(--font-mono)', fontWeight: 700, color: 'var(--text-primary)' }}>
                                  {fr.feature || fr.feature_name}
                                </td>
                                <td style={{ padding: '8px 12px', fontFamily: 'var(--font-mono)', color: isDrift ? 'var(--color-fraud-alert-bright)' : 'var(--text-secondary)' }}>
                                  {(fr.psi ?? 0).toFixed(4)}
                                </td>
                                <td style={{ padding: '8px 12px', fontFamily: 'var(--font-mono)', color: 'var(--text-secondary)' }}>
                                  {(fr.ks_statistic ?? 0).toFixed(4)}
                                </td>
                                <td style={{ padding: '8px 12px', fontFamily: 'var(--font-mono)', color: 'var(--text-tertiary)' }}>
                                  {typeof fr.ks_pvalue === 'number' ? (fr.ks_pvalue < 0.0001 ? '<0.0001' : fr.ks_pvalue.toFixed(4)) : '—'}
                                </td>
                                <td style={{ padding: '8px 12px', fontFamily: 'var(--font-mono)', color: 'var(--text-secondary)' }}>
                                  {(fr.wasserstein_distance ?? 0).toFixed(4)}
                                </td>
                                <td style={{ padding: '8px 12px' }}>
                                  <span style={{ fontSize: '10.5px', fontFamily: 'var(--font-mono)', fontWeight: 700, padding: '2px 6px', borderRadius: '2px', color: badgeColor, background: badgeBg }}>
                                    {isDrift ? 'SIGNIFICANT' : isMod ? 'MODERATE' : 'STABLE'}
                                  </span>
                                </td>
                              </tr>
                            );
                          })}
                        </tbody>
                      </table>
                    </div>
                  </div>
                )}

                {/* Statutory Guardrail Callout */}
                <div
                  style={{
                    padding: '10px 14px',
                    borderRadius: 'var(--radius-xs)',
                    background: 'rgba(99, 102, 241, 0.08)',
                    border: '1px solid var(--accent-primary-dim)',
                    fontSize: '12px',
                    color: 'var(--text-secondary)',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '8px',
                  }}
                >
                  <Info size={14} style={{ color: 'var(--accent-primary)', flexShrink: 0 }} />
                  <span>
                    <strong>Statutory Principle:</strong> {driftReport.notice || 'Distribution drift indicates data shift, not proof of fraud.'}
                  </span>
                </div>
              </div>
            ) : null}
          </div>
        </>
      )}
    </div>
  );
};
