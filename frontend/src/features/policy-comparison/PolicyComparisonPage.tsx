import React, { useState, useEffect, useCallback } from 'react';
import {
  Scale,
  BarChart2,
  Eye,
  X,
  Info,
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
import { PolicyCompareResponse, PolicyComparisonItem } from '../../lib/api/types';
import { LoadingState } from '../../components/LoadingState';
import { ErrorState } from '../../components/ErrorState';

export const PolicyComparisonPage: React.FC = () => {
  const [budgetMultiple, setBudgetMultiple] = useState<string>('1.5x');
  const [data, setData] = useState<PolicyCompareResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedPolicy, setSelectedPolicy] = useState<PolicyComparisonItem | null>(null);

  // Close modal on Escape
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && selectedPolicy) {
        setSelectedPolicy(null);
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [selectedPolicy]);

  const fetchComparison = useCallback(async (multiple: string) => {
    setLoading(true);
    setError(null);
    try {
      const res = await api.getPoliciesCompare(multiple);
      setData(res);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to retrieve policy comparison data');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchComparison(budgetMultiple);
  }, [budgetMultiple, fetchComparison]);

  const policies: PolicyComparisonItem[] = data?.policies || [];

  // Transform data for Recharts
  const chartData = policies.map((p) => {
    let displayName = p.policy;
    if (p.policy === 'B1_fixed_threshold') displayName = 'B1 Fixed Thresh';
    else if (p.policy === 'B2_top_b_risk') displayName = 'B2 Top-B Risk';
    else if (p.policy === 'B3a_confidence_deferral') displayName = 'B3a Conf Defer';
    else if (p.policy === 'B4_random_control') displayName = 'B4 Random';
    else if (p.policy === 'SignalGate_frozen' || p.policy === 'SignalGate_candidate') displayName = 'SignalGate (Ours)';

    return {
      name: displayName,
      rawPolicy: p.policy,
      recallPct: Number(((p.recall || p.recall_at_touched || 0) * 100).toFixed(2)),
      precisionPct: Number(((p.precision || 0) * 100).toFixed(2)),
      touchedPct: Number(((p.touched_rate || 0) * 100).toFixed(2)),
      caughtCount: p.caught_fraud || 0,
      deferredCount: p.deferred_count || 0,
    };
  });

  return (
    <div className="policy-comparison-page animate-fade-in" style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-4)' }}>
      {/* 1. Header & Evidence Banner */}
      <div className="page-header-card" style={{ borderLeftColor: 'var(--accent-amber)' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '14px' }}>
          <div>
            <div className="page-header-eyebrow" style={{ marginBottom: '6px' }}>
              <span className="badge badge-synthetic">
                <span>{data?.status || 'SYNTHETIC_SMOKE_ONLY'}</span>
              </span>
              <span>CONTROLLED BENCHMARK HARNESS</span>
              <span style={{ color: 'var(--border-active)' }}>|</span>
              <span style={{ color: 'var(--text-secondary)' }}>
                Test Partition: 2,000 txns &bull; 111 Total Fraud
              </span>
            </div>
            <h1 className="page-header-title">
              POLICY COMPARISON &amp; MATCHED WORKLOAD BENCHMARK
            </h1>
            <p className="page-header-desc">
              Controlled evaluation comparing SignalGate against B1, B2, B3a, and B4 under matched analyst capacity budgets.
            </p>
          </div>

          {/* Budget Multiple Selector */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', background: 'var(--bg-surface-raised)', padding: '6px 12px', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-subtle)' }}>
            <span style={{ fontSize: '13px', color: 'var(--text-secondary)', fontWeight: 600 }}>Review Budget:</span>
            <div style={{ display: 'flex', gap: '6px' }}>
              {['1.0x', '1.5x', '2.0x', '3.0x'].map((b) => (
                <button
                  key={b}
                  type="button"
                  onClick={() => setBudgetMultiple(b)}
                  className="sg-btn"
                  style={{
                    padding: '5px 12px',
                    fontSize: '13px',
                    fontFamily: 'var(--font-mono)',
                    background: budgetMultiple === b ? 'var(--accent-primary)' : 'var(--bg-surface-subdued)',
                    color: budgetMultiple === b ? '#0A0F14' : 'var(--text-secondary)',
                    fontWeight: budgetMultiple === b ? 700 : 500,
                    borderColor: budgetMultiple === b ? 'var(--accent-primary)' : 'var(--border-subtle)',
                    borderRadius: 'var(--radius-xs)',
                  }}
                >
                  {b} {b === '1.5x' && '★'}
                </button>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* 2. Scientific Integrity & Paired Bootstrap CI Notice */}
      <div
        className="sg-card"
        style={{
          padding: '16px 20px',
          background: 'var(--bg-surface-raised)',
          border: '1px solid var(--border-default)',
          borderLeft: '4px solid var(--color-manual-review)',
          boxShadow: '0 4px 16px rgba(0, 0, 0, 0.15)',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'flex-start', gap: '14px' }}>
          <div
            style={{
              width: '36px',
              height: '36px',
              borderRadius: 'var(--radius-xs)',
              backgroundColor: 'var(--color-manual-review-tint)',
              border: '1px solid var(--color-manual-review-dim)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: 'var(--color-manual-review)',
              flexShrink: 0,
              marginTop: '2px',
            }}
          >
            <Scale size={20} />
          </div>
          <div style={{ flex: 1 }}>
            <div style={{ fontSize: '15px', fontWeight: 700, color: 'var(--text-primary)', marginBottom: '4px' }}>
              Empirical Evaluation Finding: Inconclusive Superiority (Smoke Protocol)
            </div>
            <p style={{ fontSize: '14px', color: 'var(--text-secondary)', margin: 0, lineHeight: 1.6 }}>
              At the primary evaluation budget of 1.5&times; prevalence (<strong>B = 130 reviews, 6.525% capacity</strong>),
              SignalGate and B2 Top-B Risk both achieve identical recall of <strong style={{ color: 'var(--accent-primary-bright)' }}>9.01%</strong> (10 of 111 test fraud caught)
              with precision of <strong style={{ color: 'var(--accent-primary-bright)' }}>7.69%</strong> (10 of 130 reviews).
              Paired bootstrap 95% confidence interval is <strong style={{ color: 'var(--text-primary)', fontFamily: 'var(--font-mono)' }}>[-2.75 pp, +2.75 pp]</strong> with conclusive gain flag: <strong style={{ color: 'var(--color-fraud-alert)', fontFamily: 'var(--font-mono)' }}>false</strong>.
              SignalGate does not claim superior recall on this development fixture; its distinction is capacity-aware deferral routing (<strong>974 deferred</strong>).
            </p>
          </div>
        </div>
      </div>

      {loading ? (
        <LoadingState message="Calculating matched-budget policy metrics..." />
      ) : error ? (
        <ErrorState title="Policy Comparison Failed" message={error} onRetry={() => fetchComparison(budgetMultiple)} />
      ) : (
        <>
          {/* 3. Recharts Visual Comparison Bar Chart */}
          <div className="sg-card" style={{ padding: '16px', display: 'flex', flexDirection: 'column', gap: '12px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                <BarChart2 size={15} style={{ color: 'var(--accent-primary)' }} />
                <span style={{ fontSize: '13px', fontWeight: 600, color: 'var(--text-primary)' }}>
                  Performance Metrics by Triage Policy ({budgetMultiple} Budget Multiple)
                </span>
              </div>
              <span style={{ fontFamily: 'var(--font-mono)', fontSize: '11px', color: 'var(--text-secondary)' }}>
                Target Capacity: {data?.target_budget ? `${(data.target_budget * 100).toFixed(3)}%` : '6.525%'}
              </span>
            </div>

            <div style={{ width: '100%', height: '260px' }}>
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={chartData} margin={{ top: 10, right: 20, left: -10, bottom: 20 }}>
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
                    domain={[0, 12]}
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
                  <Legend
                    verticalAlign="top"
                    wrapperStyle={{ fontSize: '11px', paddingBottom: '10px' }}
                  />
                  <Bar dataKey="recallPct" name="Recall @ Touched" fill="#68D8CB" radius={[2, 2, 0, 0]} />
                  <Bar dataKey="precisionPct" name="Precision" fill="#7DAAFF" radius={[2, 2, 0, 0]} />
                  <Bar dataKey="touchedPct" name="Touched Rate" fill="#E8B35E" radius={[2, 2, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* 4. Complete Metrics Table with Rich Visual Gauges */}
          <div className="sg-card" style={{ padding: '0', overflow: 'hidden' }}>
            <div style={{ padding: '14px 18px', borderBottom: '1px solid var(--border-default)', background: 'var(--bg-surface-raised)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div>
                <span style={{ fontSize: '15px', fontWeight: 700, color: 'var(--text-primary)' }}>
                  Detailed Policy Evaluation Records &amp; Visual Micro-Metrics
                </span>
                <div style={{ fontSize: '13px', color: 'var(--text-secondary)', marginTop: '3px' }}>
                  2,000 Test Look Transactions &bull; Evaluated against matched human review budget B = 130
                </div>
              </div>
              <span style={{ fontFamily: 'var(--font-mono)', fontSize: '11px', color: 'var(--text-tertiary)' }}>
                /api/policies/compare?budget_multiple={budgetMultiple}
              </span>
            </div>

            <div style={{ overflowX: 'auto' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '13.5px' }}>
                <thead>
                  <tr style={{ background: 'var(--bg-surface-primary)', borderBottom: '1px solid var(--border-default)', color: 'var(--text-secondary)' }}>
                    <th style={{ padding: '14px 16px', fontWeight: 700, fontSize: '13px', letterSpacing: '0.04em' }}>POLICY CANDIDATE</th>
                    <th style={{ padding: '14px 16px', fontWeight: 700, fontSize: '13px', letterSpacing: '0.04em' }}>TOUCHED RATE (BUDGET B)</th>
                    <th style={{ padding: '14px 16px', fontWeight: 700, fontSize: '13px', letterSpacing: '0.04em' }}>CAUGHT FRAUD</th>
                    <th style={{ padding: '14px 16px', fontWeight: 700, fontSize: '13px', letterSpacing: '0.04em' }}>RECALL @ TOUCHED</th>
                    <th style={{ padding: '14px 16px', fontWeight: 700, fontSize: '13px', letterSpacing: '0.04em' }}>PRECISION</th>
                    <th style={{ padding: '14px 16px', fontWeight: 700, fontSize: '13px', letterSpacing: '0.04em' }}>DEFERRED ESCALATIONS</th>
                    <th style={{ padding: '14px 16px', fontWeight: 700, fontSize: '13px', letterSpacing: '0.04em', textAlign: 'center' }}>INSPECT</th>
                  </tr>
                </thead>
                <tbody>
                  {policies.map((p) => {
                    const isSignalGate = p.policy.toLowerCase().includes('signalgate');
                    const recall = p.recall || p.recall_at_touched || 0;
                    const caught = p.caught_fraud || 0;
                    const totalFraud = p.total_fraud || 111;
                    const touched = p.touched_rate || 0;
                    const precision = p.precision || 0;

                    return (
                      <tr
                        key={p.policy}
                        onClick={() => setSelectedPolicy(p)}
                        onKeyDown={(e) => {
                          if (e.key === 'Enter' || e.key === ' ') {
                            e.preventDefault();
                            setSelectedPolicy(p);
                          }
                        }}
                        tabIndex={0}
                        role="button"
                        aria-label={`Inspect policy ${p.policy}`}
                        className="interactive-table-row"
                        style={{
                          borderBottom: '1px solid var(--border-subtle)',
                          background: isSignalGate ? 'rgba(104, 216, 203, 0.05)' : 'transparent',
                          cursor: 'pointer',
                          transition: 'background-color var(--transition-fast)',
                        }}
                      >
                        {/* Policy Candidate */}
                        <td style={{ padding: '14px 16px' }}>
                          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                            {isSignalGate ? (
                              <div style={{ width: '9px', height: '9px', borderRadius: '50%', backgroundColor: 'var(--accent-primary)', flexShrink: 0 }} />
                            ) : (
                              <div style={{ width: '7px', height: '7px', borderRadius: '50%', backgroundColor: 'var(--text-tertiary)', flexShrink: 0 }} />
                            )}
                            <div>
                              <div style={{ fontFamily: 'var(--font-mono)', fontWeight: isSignalGate ? 700 : 600, color: isSignalGate ? 'var(--accent-primary-bright)' : 'var(--text-primary)', fontSize: '14px' }}>
                                {p.policy}
                              </div>
                              <div style={{ fontSize: '12.5px', color: 'var(--text-secondary)', marginTop: '2px' }}>
                                {isSignalGate ? 'Dual-Model + Epistemic Deferral' : p.policy.includes('top_b') ? 'Ranked Risk Greedy Cutoff' : p.policy.includes('fixed') ? 'Static Threshold' : 'Baseline Control'}
                              </div>
                            </div>
                            {isSignalGate && (
                              <span className="badge badge-ready" style={{ fontSize: '11px', padding: '2px 7px', marginLeft: 'auto' }}>
                                FROZEN
                              </span>
                            )}
                          </div>
                        </td>

                        {/* Touched Rate with Micro-Meter */}
                        <td style={{ padding: '14px 16px' }}>
                          <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
                            <div style={{ display: 'flex', justifyContent: 'space-between', fontFamily: 'var(--font-mono)', fontSize: '12.5px' }}>
                              <span style={{ color: touched >= 0.065 ? 'var(--color-manual-review)' : 'var(--text-primary)', fontWeight: 700 }}>
                                {(touched * 100).toFixed(2)}%
                              </span>
                              <span style={{ fontSize: '11.5px', color: 'var(--text-tertiary)' }}>/ 6.525%</span>
                            </div>
                            <div style={{ width: '90px', height: '6px', backgroundColor: 'var(--bg-surface-subdued)', borderRadius: '3px', overflow: 'hidden' }}>
                              <div
                                style={{
                                  width: `${Math.min(100, (touched / 0.06525) * 100)}%`,
                                  height: '100%',
                                  backgroundColor: touched >= 0.065 ? 'var(--color-manual-review)' : 'var(--color-routine)',
                                }}
                              />
                            </div>
                          </div>
                        </td>

                        {/* Caught / Total Fraud */}
                        <td style={{ padding: '14px 16px' }}>
                          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                            <span style={{ fontFamily: 'var(--font-mono)', fontWeight: 700, color: 'var(--text-primary)', fontSize: '13.5px' }}>
                              {caught} / {totalFraud}
                            </span>
                          </div>
                        </td>

                        {/* Recall @ Touched */}
                        <td style={{ padding: '14px 16px' }}>
                          <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
                            <span style={{ fontFamily: 'var(--font-mono)', fontWeight: 700, color: 'var(--accent-primary-bright)', fontSize: '13.5px' }}>
                              {(recall * 100).toFixed(2)}%
                            </span>
                            <div style={{ width: '90px', height: '6px', backgroundColor: 'var(--bg-surface-subdued)', borderRadius: '3px', overflow: 'hidden' }}>
                              <div style={{ width: `${Math.min(100, (recall / 0.12) * 100)}%`, height: '100%', backgroundColor: 'var(--accent-primary)' }} />
                            </div>
                          </div>
                        </td>

                        {/* Precision */}
                        <td style={{ padding: '14px 16px' }}>
                          <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
                            <span style={{ fontFamily: 'var(--font-mono)', color: 'var(--chart-blue)', fontWeight: 700, fontSize: '13.5px' }}>
                              {p.precision !== null ? `${(precision * 100).toFixed(2)}%` : '—'}
                            </span>
                            <div style={{ width: '90px', height: '6px', backgroundColor: 'var(--bg-surface-subdued)', borderRadius: '3px', overflow: 'hidden' }}>
                              <div style={{ width: `${Math.min(100, (precision / 0.12) * 100)}%`, height: '100%', backgroundColor: 'var(--chart-blue)' }} />
                            </div>
                          </div>
                        </td>

                        {/* Deferred Count */}
                        <td style={{ padding: '14px 16px' }}>
                          {p.deferred_count ? (
                            <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                              <span
                                style={{
                                  fontFamily: 'var(--font-mono)',
                                  fontSize: '12.5px',
                                  fontWeight: 700,
                                  color: 'var(--color-epistemic-defer-bright)',
                                  padding: '3px 8px',
                                  borderRadius: 'var(--radius-xs)',
                                  backgroundColor: 'rgba(180, 160, 248, 0.12)',
                                  border: '1px solid rgba(180, 160, 248, 0.3)',
                                }}
                              >
                                {p.deferred_count} cases
                              </span>
                              <span style={{ fontSize: '11.5px', color: 'var(--text-secondary)' }}>(48.7%)</span>
                            </div>
                          ) : (
                            <span style={{ fontFamily: 'var(--font-mono)', fontSize: '12.5px', color: 'var(--text-tertiary)' }}>
                              0 cases (None)
                            </span>
                          )}
                        </td>

                        {/* Action Inspect Button */}
                        <td style={{ padding: '14px 16px', textAlign: 'center' }}>
                          <span
                            className="sg-btn sg-btn-secondary"
                            style={{
                              padding: '5px 12px',
                              fontSize: '12.5px',
                              display: 'inline-flex',
                              alignItems: 'center',
                              gap: '6px',
                              color: isSignalGate ? 'var(--accent-primary-bright)' : 'var(--text-secondary)',
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
          </div>

          {/* Centered Frosted-Glass Modal on Row Click */}
          {selectedPolicy && (() => {
            const isSignalGate = selectedPolicy.policy.toLowerCase().includes('signalgate');
            const recall = selectedPolicy.recall || selectedPolicy.recall_at_touched || 0;
            const caught = selectedPolicy.caught_fraud || 0;
            const totalFraud = selectedPolicy.total_fraud || 111;
            const touched = selectedPolicy.touched_rate || 0;
            const precision = selectedPolicy.precision || 0;
            const accentColor = isSignalGate ? 'var(--accent-primary)' : 'var(--chart-blue)';

            return (
              <div
                className="glass-modal-backdrop"
                onClick={() => setSelectedPolicy(null)}
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
                aria-labelledby="policy-dialog-title"
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
                    border: `1px solid ${accentColor}55`,
                    borderRadius: 'var(--radius-md, 8px)',
                    boxShadow: `0 24px 60px rgba(0, 0, 0, 0.5), 0 0 40px ${accentColor}25`,
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
                          backgroundColor: `${accentColor}22`,
                          border: `1px solid ${accentColor}55`,
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                          color: accentColor,
                          flexShrink: 0,
                        }}
                      >
                        <Scale size={22} />
                      </div>
                      <div>
                        <div style={{ fontSize: '11px', color: accentColor, textTransform: 'uppercase', fontFamily: 'var(--font-mono)', fontWeight: 700, letterSpacing: '0.06em' }}>
                          Candidate Policy Architecture Evaluation
                        </div>
                        <h2
                          id="policy-dialog-title"
                          style={{ fontSize: '20px', fontWeight: 700, margin: '2px 0 0 0', color: 'var(--text-primary)', letterSpacing: '-0.01em' }}
                        >
                          {selectedPolicy.policy}
                        </h2>
                      </div>
                    </div>

                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      {isSignalGate ? (
                        <span className="badge badge-ready" style={{ fontSize: '10px' }}>
                          <span>FROZEN CANDIDATE</span>
                        </span>
                      ) : (
                        <span className="badge badge-neutral" style={{ fontSize: '10px' }}>
                          <span>BASELINE BENCHMARK</span>
                        </span>
                      )}
                      <button
                        type="button"
                        onClick={() => setSelectedPolicy(null)}
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
                        aria-label="Close policy inspection"
                      >
                        <X size={18} />
                      </button>
                    </div>
                  </div>

                  {/* Subtitle / Operational Strategy Banner */}
                  <div
                    style={{
                      padding: '10px 14px',
                      borderRadius: 'var(--radius-xs)',
                      backgroundColor: 'var(--bg-surface-raised)',
                      border: '1px solid var(--border-default)',
                      fontFamily: 'var(--font-mono)',
                      fontSize: '13px',
                      fontWeight: 600,
                      color: accentColor,
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'space-between',
                    }}
                  >
                    <span>
                      {isSignalGate
                        ? 'Shift-Aware Dual-Model Gate with Epistemic Deferral Buffer'
                        : selectedPolicy.policy.includes('top_b')
                        ? 'Greedy Ranked Risk Cutoff without Uncertainty Estimation'
                        : 'Fixed Static Risk Threshold Strategy'}
                    </span>
                    <span style={{ fontSize: '11px', color: 'var(--text-secondary)' }}>Budget: {budgetMultiple} (130 slots)</span>
                  </div>

                  {/* Benchmark Performance Grid */}
                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))', gap: '12px' }}>
                    <div style={{ background: 'var(--bg-surface-raised)', padding: '12px 14px', borderRadius: 'var(--radius-xs)', border: '1px solid var(--border-subtle)', display: 'flex', flexDirection: 'column', gap: '4px' }}>
                      <span style={{ fontSize: '12px', color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '0.04em', fontWeight: 700 }}>Touched Rate</span>
                      <span style={{ fontFamily: 'var(--font-mono)', fontSize: '20px', fontWeight: 800, color: 'var(--text-primary)' }}>{(touched * 100).toFixed(2)}%</span>
                      <span style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>Cap: 6.525% (130 / 2000)</span>
                    </div>

                    <div style={{ background: 'var(--bg-surface-raised)', padding: '12px 14px', borderRadius: 'var(--radius-xs)', border: '1px solid var(--border-subtle)', display: 'flex', flexDirection: 'column', gap: '4px' }}>
                      <span style={{ fontSize: '12px', color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '0.04em', fontWeight: 700 }}>Caught Fraud</span>
                      <span style={{ fontFamily: 'var(--font-mono)', fontSize: '20px', fontWeight: 800, color: 'var(--color-routine-bright)' }}>{caught} / {totalFraud}</span>
                      <span style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>True Positive Yield</span>
                    </div>

                    <div style={{ background: 'var(--bg-surface-raised)', padding: '12px 14px', borderRadius: 'var(--radius-xs)', border: '1px solid var(--border-subtle)', display: 'flex', flexDirection: 'column', gap: '4px' }}>
                      <span style={{ fontSize: '12px', color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '0.04em', fontWeight: 700 }}>Recall @ Touched</span>
                      <span style={{ fontFamily: 'var(--font-mono)', fontSize: '20px', fontWeight: 800, color: 'var(--accent-primary-bright)' }}>{(recall * 100).toFixed(2)}%</span>
                      <span style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>Intervention Coverage</span>
                    </div>

                    <div style={{ background: 'var(--bg-surface-raised)', padding: '12px 14px', borderRadius: 'var(--radius-xs)', border: '1px solid var(--border-subtle)', display: 'flex', flexDirection: 'column', gap: '4px' }}>
                      <span style={{ fontSize: '12px', color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '0.04em', fontWeight: 700 }}>Precision</span>
                      <span style={{ fontFamily: 'var(--font-mono)', fontSize: '20px', fontWeight: 800, color: 'var(--chart-blue)' }}>{(precision * 100).toFixed(2)}%</span>
                      <span style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>Review Concentration</span>
                    </div>
                  </div>

                  {/* Epistemic Deferrals Breakdown */}
                  <div
                    style={{
                      background: 'var(--bg-surface-subdued)',
                      padding: '14px 16px',
                      borderRadius: 'var(--radius-xs)',
                      border: '1px solid var(--border-default)',
                      display: 'flex',
                      flexDirection: 'column',
                      gap: '8px',
                    }}
                  >
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <span style={{ fontSize: '12.5px', color: 'var(--text-tertiary)', textTransform: 'uppercase', fontWeight: 700, letterSpacing: '0.05em' }}>
                        Epistemic Deferral Buffer &amp; Isolation Volume
                      </span>
                      <span style={{ fontFamily: 'var(--font-mono)', fontSize: '12.5px', fontWeight: 800, color: 'var(--color-epistemic-defer-bright)' }}>
                        {selectedPolicy.deferred_count ? `${selectedPolicy.deferred_count} cases (48.7%)` : '0 cases (Disabled)'}
                      </span>
                    </div>
                    <p style={{ fontSize: '13.5px', color: 'var(--text-secondary)', margin: 0, lineHeight: 1.6 }}>
                      {isSignalGate
                        ? 'SignalGate isolates 974 ambiguous or saturated transactions into a safe held queue, preventing catastrophic false-negative leaks under distribution shift while matching baseline recall.'
                        : 'Baseline policies lack epistemic uncertainty gating; all non-touched cases default directly to automated approval without safety quarantine.'}
                    </p>
                  </div>

                  {/* Paired Bootstrap CI Notice */}
                  <div
                    style={{
                      padding: '12px 16px',
                      borderRadius: 'var(--radius-xs)',
                      backgroundColor: 'var(--bg-surface-raised)',
                      border: '1px solid var(--border-subtle)',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '12px',
                      fontSize: '13px',
                      color: 'var(--text-secondary)',
                      lineHeight: 1.55,
                    }}
                  >
                    <Info size={16} style={{ flexShrink: 0, color: 'var(--accent-amber)' }} />
                    <span>
                      <strong style={{ color: 'var(--text-primary)' }}>Scientific Integrity Finding:</strong> Paired bootstrap 95% CI is [-2.75 pp, +2.75 pp] with conclusive superiority flag: <strong style={{ color: 'var(--color-fraud-alert)' }}>false</strong>.
                      SignalGate does not claim superior recall on this development fixture; its distinction is capacity-aware deferral routing.
                    </span>
                  </div>

                  {/* Action Bar */}
                  <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '8px', borderTop: '1px solid var(--border-subtle)', paddingTop: '12px' }}>
                    <button
                      type="button"
                      onClick={() => setSelectedPolicy(null)}
                      className="sg-btn sg-btn-primary"
                      style={{ fontSize: '12px', padding: '6px 18px' }}
                    >
                      Dismiss Policy Details
                    </button>
                  </div>
                </div>
              </div>
            );
          })()}
        </>
      )}
    </div>
  );
};

