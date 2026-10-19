import React, { useState, useEffect, useCallback } from 'react';
import {
  Search,
  ChevronLeft,
  ChevronRight,
  FileText,
  X,
  Download,
  Info,
} from 'lucide-react';
import { api } from '../../lib/api/client';
import { CaseDetailResponse, CaseListItem } from '../../lib/api/types';
import { useMode } from '../../context/ModeContext';
import { LoadingState } from '../../components/LoadingState';
import { ErrorState } from '../../components/ErrorState';

const PAGE_SIZE = 25;

export const CaseExplorerPage: React.FC = () => {
  const { mode, isRealDataMode, isLiveDisconnected } = useMode();
  const [cases, setCases] = useState<CaseListItem[]>([]);
  const [totalCases, setTotalCases] = useState<number>(0);
  const [offset, setOffset] = useState<number>(0);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Filters
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [actionFilter, setActionFilter] = useState<string>('ALL');
  const [reasonFilter, setReasonFilter] = useState<string>('ALL');

  // Selected Case Detail
  const [selectedCaseId, setSelectedCaseId] = useState<string | null>(null);
  const [caseDetail, setCaseDetail] = useState<CaseDetailResponse | null>(null);
  const [detailLoading, setDetailLoading] = useState<boolean>(false);
  const [detailError, setDetailError] = useState<string | null>(null);

  const fetchCases = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await api.getCases({
        scenario: 'S0',
        search: searchQuery.trim() || undefined,
        action: actionFilter !== 'ALL' ? actionFilter : undefined,
        reason_code: reasonFilter !== 'ALL' ? reasonFilter : undefined,
        offset,
        limit: PAGE_SIZE,
        mode,
      });
      setCases(res.cases || []);
      setTotalCases(res.total_cases || 0);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to retrieve cases');
    } finally {
      setLoading(false);
    }
  }, [searchQuery, actionFilter, reasonFilter, offset, mode]);

  useEffect(() => {
    fetchCases();
  }, [fetchCases]);

  // Load single case details when selected
  useEffect(() => {
    if (!selectedCaseId) {
      setCaseDetail(null);
      return;
    }
    let isMounted = true;
    setDetailLoading(true);
    setDetailError(null);
    api.getCaseDetail(selectedCaseId, mode)
      .then((detail) => {
        if (isMounted) setCaseDetail(detail);
      })
      .catch((err) => {
        if (isMounted) setDetailError(err instanceof Error ? err.message : 'Failed to load case dossier');
      })
      .finally(() => {
        if (isMounted) setDetailLoading(false);
      });

    return () => { isMounted = false; };
  }, [selectedCaseId, mode]);

  // Close modal on Escape key
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        setSelectedCaseId(null);
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setOffset(0);
    fetchCases();
  };

  const handleResetFilters = () => {
    setSearchQuery('');
    setActionFilter('ALL');
    setReasonFilter('ALL');
    setOffset(0);
  };

  const totalPages = Math.ceil(totalCases / PAGE_SIZE) || 1;
  const currentPage = Math.floor(offset / PAGE_SIZE) + 1;

  return (
    <div className="case-explorer-page animate-fade-in" style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-4)' }}>
      {/* 1. Page Header & Provenance Banner */}
      <div className="page-header-card" style={{ borderLeftColor: 'var(--accent-cyan)' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '14px' }}>
          <div>
            <div className="page-header-eyebrow" style={{ marginBottom: '6px' }}>
              <span className={`badge ${isRealDataMode ? 'badge-ready' : isLiveDisconnected ? 'badge-alert' : 'badge-synthetic'}`}>
                <span>{mode}</span>
              </span>
              <span>AUDITED TRANSACTION REPOSITORY</span>
              <span style={{ color: 'var(--border-active)' }}>|</span>
              <span style={{ color: 'var(--text-secondary)' }}>
                {totalCases.toLocaleString()} Total Evaluated Records
              </span>
            </div>
            <h1 className="page-header-title">
              AUDITED TRANSACTION CASE EXPLORER &amp; DOSSIERS
            </h1>
            <p className="page-header-desc">
              Detailed multi-attribute query tool for auditing risk scores (<span style={{ color: 'var(--accent-primary)', fontWeight: 600 }}>p</span>),
              disagreement residuals (<span style={{ color: 'var(--color-epistemic-defer-bright)', fontWeight: 600 }}>u₂</span>),
              and capacity-governed decisions with visual micro-gauges.
            </p>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <button
              type="button"
              disabled
              className="sg-btn sg-btn-secondary"
              title="CSV export disabled in smoke evaluation protocol"
              style={{ opacity: 0.6, cursor: 'not-allowed', display: 'flex', alignItems: 'center', gap: '6px', fontSize: '13px', padding: '6px 12px' }}
            >
              <Download size={14} />
              <span>Export CSV (Offline)</span>
            </button>
          </div>
        </div>
      </div>

      {/* 2. Filter & Query Controls Bar */}
      <div className="sg-card" style={{ padding: '14px 18px' }}>
        <form onSubmit={handleSearchSubmit} style={{ display: 'flex', gap: '12px', alignItems: 'center', flexWrap: 'wrap' }}>
          <div style={{ flex: '1 1 260px', position: 'relative', minWidth: '220px' }}>
            <Search size={15} style={{ position: 'absolute', left: '12px', top: '50%', transform: 'translateY(-50%)', color: 'var(--text-tertiary)' }} />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search by Case ID or Transaction..."
              style={{
                width: '100%',
                background: 'var(--bg-surface-raised)',
                color: 'var(--text-primary)',
                border: '1px solid var(--border-default)',
                borderRadius: 'var(--radius-xs)',
                padding: '7px 12px 7px 34px',
                fontSize: '13px',
                outline: 'none',
                boxSizing: 'border-box',
              }}
              aria-label="Search cases"
            />
          </div>

          {/* Action Filter */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span style={{ fontSize: '12px', color: 'var(--text-tertiary)', textTransform: 'uppercase', fontWeight: 600 }}>ACTION:</span>
            <select
              value={actionFilter}
              onChange={(e) => {
                setActionFilter(e.target.value);
                setOffset(0);
              }}
              style={{
                background: 'var(--bg-surface-raised)',
                color: 'var(--text-primary)',
                border: '1px solid var(--border-default)',
                borderRadius: 'var(--radius-xs)',
                padding: '5px 10px',
                fontSize: '13px',
                fontFamily: 'var(--font-mono)',
              }}
            >
              <option value="ALL">All Actions</option>
              <option value="FRAUD_ALERT">FRAUD_ALERT</option>
              <option value="MANUAL_REVIEW">MANUAL_REVIEW</option>
              <option value="ROUTINE">ROUTINE</option>
              <option value="DEFERRED">DEFERRED</option>
            </select>
          </div>

          {/* Reason Code Filter */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span style={{ fontSize: '12px', color: 'var(--text-tertiary)', textTransform: 'uppercase', fontWeight: 600 }}>REASON:</span>
            <select
              value={reasonFilter}
              onChange={(e) => {
                setReasonFilter(e.target.value);
                setOffset(0);
              }}
              style={{
                background: 'var(--bg-surface-raised)',
                color: 'var(--text-primary)',
                border: '1px solid var(--border-default)',
                borderRadius: 'var(--radius-xs)',
                padding: '5px 10px',
                fontSize: '13px',
                fontFamily: 'var(--font-mono)',
              }}
            >
              <option value="ALL">All Reason Codes</option>
              <option value="R1_HIGH_RISK">R1_HIGH_RISK</option>
              <option value="R2_INTERMEDIATE_RISK">R2_INTERMEDIATE_RISK</option>
              <option value="R3_MODEL_DISAGREEMENT">R3_MODEL_DISAGREEMENT</option>
              <option value="R5_LOW_RISK_RELIABLE">R5_LOW_RISK_RELIABLE</option>
              <option value="R6_CAPACITY_DEFERRED">R6_CAPACITY_DEFERRED</option>
            </select>
          </div>

          <button type="submit" className="sg-btn sg-btn-primary" style={{ padding: '6px 14px', fontSize: '13px' }}>
            Apply Query
          </button>

          {(searchQuery || actionFilter !== 'ALL' || reasonFilter !== 'ALL') && (
            <button
              type="button"
              onClick={handleResetFilters}
              className="sg-btn sg-btn-secondary"
              style={{ padding: '6px 10px', fontSize: '13px' }}
            >
              Reset
            </button>
          )}
        </form>
      </div>

      {/* 3. Main Data Content Area (Full-Width Unsplit Table) */}
      <div style={{ width: '100%' }}>
        {/* Cases Table Panel */}
        <div className="sg-card" style={{ padding: '0', overflow: 'hidden', display: 'flex', flexDirection: 'column' }}>
          {loading ? (
            <div style={{ padding: '40px' }}>
              <LoadingState message="Querying case index..." />
            </div>
          ) : error ? (
            <div style={{ padding: '24px' }}>
              <ErrorState title="Case Query Failed" message={error} onRetry={fetchCases} />
            </div>
          ) : cases.length === 0 ? (
            <div style={{ padding: '36px', textAlign: 'center', color: 'var(--text-secondary)' }}>
              {isLiveDisconnected
                ? 'LIVE SOURCE DISCONNECTED: Real-time event streaming is disconnected. No live cases to display. Switch to IEEE-CIS BENCHMARK or SYNTHETIC FIXTURE to inspect cases.'
                : 'No transactions match the applied query parameters.'}
            </div>
          ) : (
            <div style={{ overflowX: 'auto' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '13.5px' }}>
                <thead>
                  <tr style={{ background: 'var(--bg-surface-raised)', borderBottom: '1px solid var(--border-default)', color: 'var(--text-secondary)' }}>
                    <th style={{ padding: '14px 16px', fontWeight: 700, fontSize: '13px', letterSpacing: '0.04em' }}>CASE ID</th>
                    <th style={{ padding: '14px 16px', fontWeight: 700, fontSize: '13px', letterSpacing: '0.04em' }}>AMOUNT</th>
                    <th style={{ padding: '14px 16px', fontWeight: 700, fontSize: '13px', letterSpacing: '0.04em' }}>CARD / PROD</th>
                    <th style={{ padding: '14px 16px', fontWeight: 700, fontSize: '13px', letterSpacing: '0.04em' }}>RISK (p) METER</th>
                    <th style={{ padding: '14px 16px', fontWeight: 700, fontSize: '13px', letterSpacing: '0.04em' }}>DISAGREE (u₂) METER</th>
                    <th style={{ padding: '14px 16px', fontWeight: 700, fontSize: '13px', letterSpacing: '0.04em' }}>ACTION</th>
                    <th style={{ padding: '14px 16px', fontWeight: 700, fontSize: '13px', letterSpacing: '0.04em' }}>REASON</th>
                    <th style={{ padding: '14px 16px', fontWeight: 700, fontSize: '13px', letterSpacing: '0.04em' }}>GROUND TRUTH</th>
                  </tr>
                </thead>
                <tbody>
                  {cases.map((c) => {
                    const isSelected = selectedCaseId === c.case_id;
                    const safeAmount = typeof c.amount === 'number' ? c.amount : 0;
                    const safeP = typeof c.p === 'number' ? c.p : (typeof (c as any).p_risk === 'number' ? (c as any).p_risk : 0);
                    const safeU = typeof c.u === 'number' ? c.u : (typeof (c as any).u_disagreement === 'number' ? (c as any).u_disagreement : null);

                    const actionClass =
                      c.action === 'FRAUD_ALERT' ? 'var(--color-fraud-alert)' :
                      c.action === 'MANUAL_REVIEW' ? 'var(--color-manual-review)' :
                      c.action === 'ROUTINE' ? 'var(--color-routine)' : 'var(--color-epistemic-defer-bright)';

                    const riskColor =
                      safeP >= 0.0847 ? 'var(--color-fraud-alert)' :
                      safeP >= 0.071 ? 'var(--color-manual-review)' : 'var(--color-routine)';

                    return (
                      <tr
                        key={c.case_id}
                        onClick={() => setSelectedCaseId(isSelected ? null : c.case_id)}
                        style={{
                          borderBottom: '1px solid var(--border-subtle)',
                          background: isSelected ? 'rgba(104, 216, 203, 0.08)' : 'transparent',
                          cursor: 'pointer',
                          transition: 'background-color 0.15s ease',
                        }}
                        className="sg-table-row"
                      >
                        <td style={{ padding: '14px 16px', fontFamily: 'var(--font-mono)', fontWeight: 700, color: 'var(--text-primary)', fontSize: '14px' }}>
                          {c.case_id}
                        </td>
                        <td style={{ padding: '14px 16px', fontFamily: 'var(--font-mono)', fontWeight: 700, fontSize: '14px' }}>
                          ${safeAmount.toFixed(2)}
                        </td>
                        <td style={{ padding: '14px 16px', color: 'var(--text-secondary)', fontSize: '13.5px' }}>
                          {c.card4 ? c.card4.toUpperCase() : 'UNKNOWN'} &bull; {c.product_cd || 'W'}
                        </td>

                        {/* Risk (p) Visual Meter */}
                        <td style={{ padding: '14px 16px' }}>
                          <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
                            <span style={{ fontFamily: 'var(--font-mono)', fontSize: '13.5px', fontWeight: 700, color: riskColor }}>
                              {safeP.toFixed(4)}
                            </span>
                            <div style={{ width: '90px', height: '7px', backgroundColor: 'var(--bg-surface-subdued)', borderRadius: '3.5px', overflow: 'hidden' }}>
                              <div
                                style={{
                                  width: `${Math.min(100, (safeP / 0.12) * 100)}%`,
                                  height: '100%',
                                  backgroundColor: riskColor,
                                }}
                              />
                            </div>
                          </div>
                        </td>

                        {/* Disagree (u2) Visual Meter */}
                        <td style={{ padding: '14px 16px' }}>
                          <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
                            <span style={{ fontFamily: 'var(--font-mono)', fontSize: '13.5px', fontWeight: 700, color: (safeU || 0) >= 0.5268 ? 'var(--color-epistemic-defer-bright)' : 'var(--text-secondary)' }}>
                              {safeU !== null ? safeU.toFixed(4) : '—'}
                            </span>
                            {safeU !== null && (
                              <div style={{ width: '90px', height: '7px', backgroundColor: 'var(--bg-surface-subdued)', borderRadius: '3.5px', overflow: 'hidden' }}>
                                <div
                                  style={{
                                    width: `${Math.min(100, Math.max(0, ((safeU + 0.5) / 1.5) * 100))}%`,
                                    height: '100%',
                                    backgroundColor: (safeU || 0) >= 0.5268 ? 'var(--color-epistemic-defer-bright)' : 'var(--border-active)',
                                  }}
                                />
                              </div>
                            )}
                          </div>
                        </td>

                        <td style={{ padding: '14px 16px' }}>
                          <span style={{
                            display: 'inline-block',
                            padding: '4px 9px',
                            borderRadius: 'var(--radius-xs)',
                            fontFamily: 'var(--font-mono)',
                            fontSize: '12px',
                            fontWeight: 700,
                            color: actionClass,
                            border: `1px solid ${actionClass}44`,
                            background: `${actionClass}15`,
                            whiteSpace: 'nowrap',
                          }}>
                            {c.action}
                          </span>
                        </td>
                        <td style={{ padding: '14px 16px', fontFamily: 'var(--font-mono)', fontSize: '12.5px', color: 'var(--text-secondary)' }}>
                          {c.reason_code}
                        </td>
                        <td style={{ padding: '14px 16px' }}>
                          {c.offline_is_fraud === 1 ? (
                            <span style={{ display: 'inline-flex', alignItems: 'center', gap: '6px', color: 'var(--color-fraud-alert)', fontFamily: 'var(--font-mono)', fontSize: '12.5px', fontWeight: 700 }}>
                              <span style={{ width: '8px', height: '8px', borderRadius: '50%', backgroundColor: 'var(--color-fraud-alert)' }} />
                              <span>FRAUD (1)</span>
                            </span>
                          ) : (
                            <span style={{ display: 'inline-flex', alignItems: 'center', gap: '6px', color: 'var(--text-tertiary)', fontFamily: 'var(--font-mono)', fontSize: '12.5px' }}>
                              <span style={{ width: '8px', height: '8px', borderRadius: '50%', backgroundColor: 'var(--color-routine)' }} />
                              <span>LEGIT (0)</span>
                            </span>
                          )}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}

          {/* Pagination Controls Footer */}
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '12px 18px', background: 'var(--bg-surface-primary)', borderTop: '1px solid var(--border-default)', flexWrap: 'wrap', gap: '8px' }}>
            <span style={{ fontSize: '13px', color: 'var(--text-secondary)' }}>
              Showing {cases.length > 0 ? offset + 1 : 0}–{Math.min(offset + PAGE_SIZE, totalCases)} of {totalCases.toLocaleString()} cases
            </span>

            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <button
                type="button"
                onClick={() => setOffset(Math.max(0, offset - PAGE_SIZE))}
                disabled={offset === 0}
                className="sg-btn sg-btn-secondary"
                style={{ padding: '5px 10px' }}
                aria-label="Previous page"
              >
                <ChevronLeft size={14} />
              </button>
              <span style={{ fontFamily: 'var(--font-mono)', fontSize: '13px', color: 'var(--text-primary)', padding: '0 6px', fontWeight: 600 }}>
                Page {currentPage} / {totalPages}
              </span>
              <button
                type="button"
                onClick={() => setOffset(offset + PAGE_SIZE)}
                disabled={offset + PAGE_SIZE >= totalCases}
                className="sg-btn sg-btn-secondary"
                style={{ padding: '5px 10px' }}
                aria-label="Next page"
              >
                <ChevronRight size={14} />
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* 4. Centered Frosted-Glass Blurred Case Dossier Modal (Does not split table) */}
      {selectedCaseId && (
        <div
          className="glass-modal-backdrop"
          onClick={() => setSelectedCaseId(null)}
          role="dialog"
          aria-modal="true"
          aria-labelledby={`dossier-title-${selectedCaseId}`}
        >
          <div
            className="glass-modal-container"
            onClick={(e) => e.stopPropagation()}
            style={{
              maxWidth: '740px',
              border: '1px solid var(--accent-primary-dim)',
              boxShadow: '0 24px 60px rgba(0, 0, 0, 0.55), 0 0 40px rgba(104, 216, 203, 0.18)',
            }}
          >
            {/* Modal Header */}
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: '1px solid var(--border-subtle)', paddingBottom: '14px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                <div
                  style={{
                    width: '40px',
                    height: '40px',
                    borderRadius: 'var(--radius-sm)',
                    backgroundColor: 'var(--accent-primary-tint)',
                    border: '1px solid var(--accent-primary-dim)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    color: 'var(--accent-primary)',
                  }}
                >
                  <FileText size={20} />
                </div>
                <div>
                  <div style={{ fontSize: '11px', color: 'var(--accent-primary)', textTransform: 'uppercase', fontFamily: 'var(--font-mono)', fontWeight: 700, letterSpacing: '0.05em' }}>
                    Audited Case Dossier
                  </div>
                  <h2
                    id={`dossier-title-${selectedCaseId}`}
                    style={{ fontSize: '18px', fontWeight: 700, margin: '2px 0 0 0', color: 'var(--text-primary)' }}
                  >
                    Transaction #{selectedCaseId}
                  </h2>
                </div>
              </div>
              <button
                type="button"
                onClick={() => setSelectedCaseId(null)}
                className="sg-btn"
                style={{
                  background: 'transparent',
                  border: '1px solid var(--border-default)',
                  borderRadius: 'var(--radius-xs)',
                  color: 'var(--text-secondary)',
                  padding: '6px 8px',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  cursor: 'pointer',
                }}
                aria-label="Close dossier modal"
              >
                <X size={16} />
              </button>
            </div>

            {detailLoading ? (
              <div style={{ padding: '36px 0' }}>
                <LoadingState message="Loading case telemetry & feature vector..." />
              </div>
            ) : detailError ? (
              <ErrorState title="Dossier Error" message={detailError} />
            ) : caseDetail ? (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
                {/* 3D Decision Coordinates Badge */}
                {(() => {
                  const pVal = typeof (caseDetail.signals as any)?.p === 'number'
                    ? (caseDetail.signals as any).p
                    : (typeof caseDetail.signals?.p_risk === 'number' ? caseDetail.signals.p_risk : 0.0);
                  const uVal = typeof (caseDetail.signals as any)?.u === 'number'
                    ? (caseDetail.signals as any).u
                    : (typeof caseDetail.signals?.u_disagreement === 'number' ? caseDetail.signals.u_disagreement : 0.0);
                  const isAdmitted = Boolean(
                    caseDetail.decision?.governor_quota_admitted ||
                    (caseDetail.decision as any)?.governor_status === 'admitted'
                  );
                  const act = caseDetail.decision?.action || 'UNKNOWN';
                  const actColor = act === 'FRAUD_ALERT' ? 'var(--color-fraud-alert)' :
                    act === 'MANUAL_REVIEW' ? 'var(--color-manual-review)' :
                    act === 'ROUTINE' ? 'var(--color-routine)' : 'var(--color-epistemic-defer-bright)';

                  return (
                    <>
                      <div
                        style={{
                          background: 'var(--bg-surface-raised)',
                          border: '1px solid var(--border-default)',
                          padding: '12px 16px',
                          borderRadius: 'var(--radius-xs)',
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'space-between',
                        }}
                      >
                        <span style={{ fontSize: '12px', fontFamily: 'var(--font-mono)', color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '0.05em', fontWeight: 700 }}>
                          3D DECISION VECTOR
                        </span>
                        <span style={{ fontFamily: 'var(--font-mono)', fontSize: '14.5px', fontWeight: 800, color: 'var(--accent-primary-bright)' }}>
                          [p: {pVal.toFixed(4)}, u₂: {uVal.toFixed(4)}]
                        </span>
                      </div>

                      {/* Decision Summary */}
                      <div style={{ background: 'var(--bg-surface-subdued)', padding: '14px 16px', borderRadius: 'var(--radius-xs)', border: '1px solid var(--border-subtle)' }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                          <span style={{ fontSize: '12px', color: 'var(--text-tertiary)', textTransform: 'uppercase', fontWeight: 700 }}>ROUTER ACTION</span>
                          <span
                            style={{
                              padding: '3px 10px',
                              borderRadius: 'var(--radius-xs)',
                              fontFamily: 'var(--font-mono)',
                              fontSize: '12px',
                              fontWeight: 800,
                              color: actColor,
                              border: `1px solid ${actColor}44`,
                              background: `${actColor}15`,
                            }}
                          >
                            {act}
                          </span>
                        </div>
                        <div style={{ fontSize: '13.5px', color: 'var(--text-secondary)', lineHeight: 1.6 }}>
                          Reason Code: <strong style={{ color: 'var(--text-primary)', fontFamily: 'var(--font-mono)' }}>{caseDetail.decision?.reason_code || 'R0'}</strong><br />
                          Analyst Quota Status: <strong style={{ color: 'var(--text-primary)' }}>{isAdmitted ? 'YES (Admitted to Review Queue)' : 'NO (Shed to DEFERRED via R6)'}</strong>
                        </div>
                      </div>

                      {/* Signals Meters */}
                      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
                        <div style={{ background: 'var(--bg-surface-raised)', padding: '12px 14px', borderRadius: 'var(--radius-xs)', border: '1px solid var(--border-subtle)' }}>
                          <div style={{ fontSize: '12px', color: 'var(--text-tertiary)', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.04em' }}>CALIBRATED RISK (p)</div>
                          <div style={{ fontFamily: 'var(--font-mono)', fontSize: '20px', fontWeight: 800, color: 'var(--accent-primary)', marginTop: '4px' }}>
                            {pVal.toFixed(4)}
                          </div>
                        </div>
                        <div style={{ background: 'var(--bg-surface-raised)', padding: '12px 14px', borderRadius: 'var(--radius-xs)', border: '1px solid var(--border-subtle)' }}>
                          <div style={{ fontSize: '12px', color: 'var(--text-tertiary)', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.04em' }}>DISAGREEMENT (u₂)</div>
                          <div style={{ fontFamily: 'var(--font-mono)', fontSize: '20px', fontWeight: 800, color: 'var(--color-epistemic-defer-bright)', marginTop: '4px' }}>
                            {uVal.toFixed(4)}
                          </div>
                        </div>
                      </div>
                    </>
                  );
                })()}

                {/* Features Inspection Table */}
                <div>
                  <div style={{ fontSize: '13.5px', fontWeight: 700, color: 'var(--text-primary)', marginBottom: '8px' }}>
                    Normalized Feature Vector
                  </div>
                  <div style={{ maxHeight: '240px', overflowY: 'auto', background: 'var(--bg-surface-subdued)', borderRadius: 'var(--radius-xs)', border: '1px solid var(--border-subtle)' }}>
                    <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '13px' }}>
                      <tbody>
                        {Object.entries(caseDetail.features || {}).map(([k, v]) => (
                          <tr key={k} style={{ borderBottom: '1px solid var(--border-subtle)' }}>
                            <td style={{ padding: '6px 12px', color: 'var(--text-tertiary)', fontFamily: 'var(--font-mono)', width: '45%' }}>{k}</td>
                            <td style={{ padding: '6px 12px', fontFamily: 'var(--font-mono)', color: 'var(--text-primary)', fontWeight: 600 }}>{String(v)}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>

                {/* Explanation Attribution Status (Honest Disclosure) */}
                <div style={{ background: 'var(--bg-surface-subdued)', padding: '10px 14px', borderRadius: 'var(--radius-xs)', border: '1px solid var(--border-subtle)', display: 'flex', alignItems: 'center', gap: '10px' }}>
                  <Info size={15} style={{ color: 'var(--text-tertiary)', flexShrink: 0 }} />
                  <span style={{ fontSize: '13px', color: 'var(--text-secondary)' }}>
                    SHAP feature attributions are explicitly disabled in synthetic smoke protocol.
                  </span>
                </div>
              </div>
            ) : null}
          </div>
        </div>
      )}
    </div>
  );
};
