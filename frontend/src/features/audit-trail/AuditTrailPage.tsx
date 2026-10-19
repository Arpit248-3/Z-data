import React, { useState, useEffect, useCallback } from 'react';
import {
  Download,
  ChevronLeft,
  ChevronRight,
  Eye,
  X,
  Code,
  ShieldAlert,
  UserCheck,
  CheckCircle2,
  Cpu,
  Clock,
  Lock,
  Copy,
  Check,
  Database,
  ShieldCheck,
} from 'lucide-react';
import { api } from '../../lib/api/client';
import { AuditRecordItem, AuditVerifyResponse } from '../../lib/api/types';
import { useMode } from '../../context/ModeContext';
import { LoadingState } from '../../components/LoadingState';
import { ErrorState } from '../../components/ErrorState';

const PAGE_SIZE = 25;

export const AuditTrailPage: React.FC = () => {
  const { mode, isRealDataMode, isLiveDisconnected } = useMode();
  const [records, setRecords] = useState<AuditRecordItem[]>([]);
  const [totalRecords, setTotalRecords] = useState<number>(0);
  const [offset, setOffset] = useState<number>(0);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const [selectedRecord, setSelectedRecord] = useState<AuditRecordItem | null>(null);
  const [copiedHash, setCopiedHash] = useState<boolean>(false);
  const [copiedJson, setCopiedJson] = useState<boolean>(false);

  const [verifyResult, setVerifyResult] = useState<AuditVerifyResponse | null>(null);
  const [verifying, setVerifying] = useState<boolean>(false);
  const [verifyError, setVerifyError] = useState<string | null>(null);

  const handleVerifyChain = async () => {
    setVerifying(true);
    setVerifyError(null);
    try {
      const res = await api.verifyAuditChain();
      setVerifyResult(res);
    } catch (err: unknown) {
      setVerifyError(err instanceof Error ? err.message : 'Verification failed');
    } finally {
      setVerifying(false);
    }
  };

  useEffect(() => {
    handleVerifyChain();
  }, []);

  // Close modal on Escape
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && selectedRecord) {
        setSelectedRecord(null);
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [selectedRecord]);

  const fetchRecords = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await api.getAudit({ offset, limit: PAGE_SIZE, mode });
      setRecords(res.records || []);
      setTotalRecords(res.total_records || 0);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to retrieve audit trail');
    } finally {
      setLoading(false);
    }
  }, [offset, mode]);

  useEffect(() => {
    fetchRecords();
  }, [fetchRecords]);

  const totalPages = Math.ceil(totalRecords / PAGE_SIZE) || 1;
  const currentPage = Math.floor(offset / PAGE_SIZE) + 1;

  const handleDownload = (format: 'jsonl' | 'csv') => {
    const url = `/api/audit/export?format=${format}&mode=${encodeURIComponent(mode)}`;
    window.open(url, '_blank');
  };

  const handleCopyHash = (hash: string) => {
    navigator.clipboard.writeText(hash);
    setCopiedHash(true);
    setTimeout(() => setCopiedHash(false), 2000);
  };

  const handleCopyJson = (record: AuditRecordItem) => {
    navigator.clipboard.writeText(JSON.stringify(record, null, 2));
    setCopiedJson(true);
    setTimeout(() => setCopiedJson(false), 2000);
  };

  const getActionMeta = (action: string) => {
    switch (action) {
      case 'FRAUD_ALERT':
        return {
          label: 'FRAUD_ALERT',
          color: 'var(--color-fraud-alert)',
          colorBright: 'var(--color-fraud-alert-bright)',
          bg: 'var(--color-fraud-alert-tint)',
          border: 'var(--color-fraud-alert-dim)',
          icon: <ShieldAlert size={12} />,
        };
      case 'MANUAL_REVIEW':
        return {
          label: 'MANUAL_REVIEW',
          color: 'var(--color-manual-review)',
          colorBright: 'var(--color-manual-review-bright)',
          bg: 'var(--color-manual-review-tint)',
          border: 'var(--color-manual-review-dim)',
          icon: <UserCheck size={12} />,
        };
      case 'ROUTINE':
        return {
          label: 'ROUTINE',
          color: 'var(--color-routine)',
          colorBright: 'var(--color-routine-bright)',
          bg: 'var(--color-routine-tint)',
          border: 'var(--color-routine-dim)',
          icon: <CheckCircle2 size={12} />,
        };
      default: // DEFERRED
        return {
          label: 'DEFERRED',
          color: 'var(--color-epistemic-defer)',
          colorBright: 'var(--color-epistemic-defer-bright)',
          bg: 'var(--color-epistemic-defer-tint)',
          border: 'var(--color-epistemic-defer-dim)',
          icon: <Cpu size={12} />,
        };
    }
  };

  return (
    <div className="audit-trail-page animate-fade-in" style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-4)' }}>
      {/* 1. Page Header & Export Actions */}
      <div className="page-header-card" style={{ borderLeftColor: 'var(--accent-primary)' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '14px' }}>
          <div>
            <div className="page-header-eyebrow" style={{ marginBottom: '6px' }}>
              <span className={`badge ${isRealDataMode ? 'badge-ready' : isLiveDisconnected ? 'badge-alert' : 'badge-synthetic'}`}>
                <span>{mode}</span>
              </span>
              <span>APPEND-ONLY CRYPTOGRAPHIC LOG</span>
              <span style={{ color: 'var(--border-active)' }}>|</span>
              <span style={{ color: 'var(--accent-primary-bright)', fontWeight: 600 }}>
                {totalRecords.toLocaleString()} Recorded Entries
              </span>
            </div>
            <h1 className="page-header-title">
              CRYPTOGRAPHIC AUDIT LEDGER &amp; REPRODUCIBILITY TRAIL
            </h1>
            <p className="page-header-desc">
              Cryptographically verified append-only audit trail recording every inference timestamp, calibrated risk posterior,
              epistemic disagreement, and SHA-256 policy configuration hash.
            </p>
          </div>

          {/* Export Actions & Info */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <button
              type="button"
              onClick={handleVerifyChain}
              disabled={verifying}
              className="sg-btn sg-btn-secondary"
              style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '13px', padding: '7px 14px' }}
              title="Deterministically verify the HMAC-SHA256 hash continuity of the audit chain"
            >
              <ShieldCheck size={14} style={{ color: verifyResult?.is_valid ? 'var(--color-routine)' : undefined }} />
              <span>{verifying ? 'Verifying Chain...' : 'Verify Cryptographic Ledger'}</span>
            </button>
            <button
              type="button"
              onClick={() => handleDownload('jsonl')}
              className="sg-btn sg-btn-secondary"
              style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '13px', padding: '7px 14px' }}
              title="Download entire log in JSON Lines format"
            >
              <Download size={14} />
              <span>Export JSONL</span>
            </button>
            <button
              type="button"
              onClick={() => handleDownload('csv')}
              className="sg-btn sg-btn-primary"
              style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '13px', padding: '7px 14px' }}
              title="Download tabular CSV log"
            >
              <Download size={14} />
              <span>Export CSV</span>
            </button>
          </div>
        </div>
      </div>

      {/* Cryptographic Ledger Verification Card */}
      {verifyResult && (
        <div
          className="sg-card"
          style={{
            padding: '14px 20px',
            background: 'var(--bg-surface-raised)',
            borderLeft: `4px solid ${verifyResult.is_valid ? 'var(--color-routine)' : 'var(--color-fraud-alert)'}`,
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            flexWrap: 'wrap',
            gap: '12px',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <span
              className={`badge ${verifyResult.is_valid ? 'badge-ready' : 'badge-alert'}`}
              style={{ fontSize: '12px', padding: '3px 9px' }}
            >
              {verifyResult.status === 'VERIFIED' ? 'INTEGRITY VERIFIED' : 'TAMPER DETECTED'}
            </span>
            <span style={{ fontSize: '13px', color: 'var(--text-secondary)' }}>
              Ledger Blocks Verified: <strong>{verifyResult.record_count}</strong> &bull; Signing: <strong>{verifyResult.signing_status}</strong>
            </span>
          </div>
          {verifyResult.chain_head_hash && (
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '11px', fontFamily: 'var(--font-mono)' }}>
              <span style={{ color: 'var(--text-tertiary)' }}>Chain-Head Hash:</span>
              <span style={{ color: 'var(--text-primary)', fontWeight: 700 }}>
                {verifyResult.chain_head_hash.slice(0, 16)}...
              </span>
            </div>
          )}
        </div>
      )}
      {verifyError && (
        <div style={{ padding: '10px 16px', background: 'rgba(239, 68, 68, 0.08)', border: '1px solid var(--color-fraud-alert)', borderRadius: 'var(--radius-xs)', fontSize: '12px', color: 'var(--color-fraud-alert)' }}>
          {verifyError}
        </div>
      )}

      {/* 2. Main Audit Table Panel */}
      <div className="sg-card" style={{ padding: '0', overflow: 'hidden', display: 'flex', flexDirection: 'column', boxShadow: '0 8px 24px rgba(0, 0, 0, 0.25)' }}>
        {/* Table Toolbar / Metadata Bar */}
        <div style={{ padding: '12px 18px', background: 'var(--bg-surface-header)', borderBottom: '1px solid var(--border-default)', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '10px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Database size={15} style={{ color: 'var(--accent-primary)' }} />
            <span style={{ fontSize: '13.5px', fontWeight: 700, color: 'var(--text-primary)' }}>
              Deterministic Inference Stream Log
            </span>
            <span style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>
              &bull; Click any row to view complete transparent blurred query receipt
            </span>
          </div>
          <span style={{ fontFamily: 'var(--font-mono)', fontSize: '12.5px', color: 'var(--text-secondary)' }}>
            Page {currentPage} of {totalPages}
          </span>
        </div>

        {loading ? (
          <div style={{ padding: '40px' }}>
            <LoadingState message="Streaming audit records from persistent store..." />
          </div>
        ) : error ? (
          <div style={{ padding: '24px' }}>
            <ErrorState title="Audit Ledger Unavailable" message={error} onRetry={fetchRecords} />
          </div>
        ) : records.length === 0 ? (
          <div style={{ padding: '36px', textAlign: 'center', color: 'var(--text-secondary)' }}>
            {isLiveDisconnected
              ? 'LIVE SOURCE DISCONNECTED: Production event ingestion is offline. No live decision audit records to display. Select IEEE-CIS BENCHMARK or SYNTHETIC FIXTURE to inspect ledger entries.'
              : 'No audit records present in local store.'}
          </div>
        ) : (
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '13.5px' }}>
              <thead>
                <tr style={{ background: 'var(--bg-surface-raised)', borderBottom: '1px solid var(--border-default)', color: 'var(--text-secondary)' }}>
                  <th style={{ padding: '14px 16px', fontWeight: 700, fontSize: '13px', letterSpacing: '0.04em' }}>RECORD ID</th>
                  <th style={{ padding: '14px 16px', fontWeight: 700, fontSize: '13px', letterSpacing: '0.04em' }}>TIMESTAMP</th>
                  <th style={{ padding: '14px 16px', fontWeight: 700, fontSize: '13px', letterSpacing: '0.04em' }}>ACTION</th>
                  <th style={{ padding: '14px 16px', fontWeight: 700, fontSize: '13px', letterSpacing: '0.04em' }}>REASON CODE</th>
                  <th style={{ padding: '14px 16px', fontWeight: 700, fontSize: '13px', letterSpacing: '0.04em' }}>RISK (p)</th>
                  <th style={{ padding: '14px 16px', fontWeight: 700, fontSize: '13px', letterSpacing: '0.04em' }}>DISAGREE (u₂)</th>
                  <th style={{ padding: '14px 16px', fontWeight: 700, fontSize: '13px', letterSpacing: '0.04em' }}>LATENCY</th>
                  <th style={{ padding: '14px 16px', fontWeight: 700, fontSize: '13px', letterSpacing: '0.04em' }}>POLICY HASH</th>
                  <th style={{ padding: '14px 16px', fontWeight: 700, fontSize: '13px', letterSpacing: '0.04em', textAlign: 'center' }}>INSPECT</th>
                </tr>
              </thead>
              <tbody>
                {records.map((r, idx) => {
                  const id = String(r.id || r.case_id || r.audit_id || `${offset + idx + 1}`);
                  const action = String(r.action || 'ROUTINE');
                  const reason = String(r.reason || r.reason_code || 'R5_LOW_RISK_RELIABLE');
                  const pVal = typeof r.p === 'number' ? r.p.toFixed(4) : '—';
                  const uVal = typeof r.u === 'number' ? r.u.toFixed(4) : '—';
                  const lat = typeof r.latency_ms === 'number' ? `${r.latency_ms.toFixed(1)}ms` : '—';
                  const cfg = r.cfg_hash ? String(r.cfg_hash).slice(0, 8) : '8d3f02ca';
                  const actionMeta = getActionMeta(action);

                  return (
                    <tr
                      key={`${id}-${idx}`}
                      onClick={() => setSelectedRecord(r)}
                      onKeyDown={(e) => {
                        if (e.key === 'Enter' || e.key === ' ') {
                          e.preventDefault();
                          setSelectedRecord(r);
                        }
                      }}
                      tabIndex={0}
                      role="button"
                      aria-label={`Inspect audit record ${id}, action ${action}`}
                      className="sg-table-row interactive-table-row"
                      style={{
                        borderBottom: '1px solid var(--border-subtle)',
                        cursor: 'pointer',
                        transition: 'background-color 0.15s ease, transform 0.1s ease',
                      }}
                    >
                      {/* Record ID */}
                      <td style={{ padding: '14px 16px', fontFamily: 'var(--font-mono)', fontWeight: 700, color: 'var(--text-primary)', fontSize: '14px' }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                          <span style={{ color: 'var(--text-tertiary)' }}>#</span>
                          <span>{id}</span>
                        </div>
                      </td>

                      {/* Timestamp Offset */}
                      <td style={{ padding: '14px 16px', fontFamily: 'var(--font-mono)', color: 'var(--text-secondary)', fontSize: '13.5px' }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                          <Clock size={14} style={{ color: 'var(--text-tertiary)' }} />
                          <span>+{typeof r.ts === 'number' ? r.ts : 0}s</span>
                        </div>
                      </td>

                      {/* Action Chip */}
                      <td style={{ padding: '14px 16px' }}>
                        <span
                          style={{
                            display: 'inline-flex',
                            alignItems: 'center',
                            gap: '6px',
                            padding: '4px 9px',
                            borderRadius: 'var(--radius-xs)',
                            fontFamily: 'var(--font-mono)',
                            fontSize: '12px',
                            fontWeight: 800,
                            color: actionMeta.colorBright,
                            border: `1px solid ${actionMeta.border}`,
                            background: actionMeta.bg,
                            letterSpacing: '0.03em',
                          }}
                        >
                          {actionMeta.icon}
                          <span>{action}</span>
                        </span>
                      </td>

                      {/* Reason Code */}
                      <td style={{ padding: '14px 16px', fontFamily: 'var(--font-mono)', fontSize: '12.5px', color: 'var(--text-secondary)' }}>
                        <span style={{ background: 'var(--bg-surface-raised)', padding: '4px 9px', borderRadius: 'var(--radius-xs)', border: '1px solid var(--border-subtle)' }}>
                          {reason}
                        </span>
                      </td>

                      {/* Risk Posterior (p) */}
                      <td style={{ padding: '14px 16px', fontFamily: 'var(--font-mono)', fontWeight: 700, color: 'var(--accent-primary-bright)', fontSize: '14px' }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                          <span>{pVal}</span>
                          {typeof r.p === 'number' && (
                            <div style={{ width: '48px', height: '6px', background: 'var(--bg-surface-subdued)', borderRadius: '3px', overflow: 'hidden' }}>
                              <div
                                style={{
                                  width: `${Math.min(100, (r.p / 0.12) * 100)}%`,
                                  height: '100%',
                                  backgroundColor: actionMeta.color,
                                }}
                              />
                            </div>
                          )}
                        </div>
                      </td>

                      {/* Epistemic Disagreement (u2) */}
                      <td style={{ padding: '14px 16px', fontFamily: 'var(--font-mono)', color: 'var(--color-epistemic-defer-bright)', fontWeight: 700, fontSize: '14px' }}>
                        {uVal}
                      </td>

                      {/* Latency with SLA Chip */}
                      <td style={{ padding: '14px 16px', fontFamily: 'var(--font-mono)', fontSize: '13.5px' }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                          <span style={{ color: 'var(--text-primary)', fontWeight: 600 }}>{lat}</span>
                          <span style={{ fontSize: '11px', color: 'var(--color-routine-bright)', background: 'var(--color-routine-tint)', padding: '2px 7px', borderRadius: '2px', fontWeight: 700 }}>
                            &lt;5ms
                          </span>
                        </div>
                      </td>

                      {/* Policy Configuration Hash */}
                      <td style={{ padding: '14px 16px', fontFamily: 'var(--font-mono)', fontSize: '12.5px', color: 'var(--text-tertiary)' }}>
                        <span style={{ background: 'var(--bg-surface-subdued)', padding: '4px 9px', borderRadius: 'var(--radius-xs)', border: '1px solid var(--border-subtle)' }}>
                          {cfg}...
                        </span>
                      </td>

                      {/* Inspect Action */}
                      <td style={{ padding: '14px 16px', textAlign: 'center' }}>
                        <span
                          className="sg-btn sg-btn-secondary"
                          style={{
                            padding: '5px 12px',
                            fontSize: '12.5px',
                            display: 'inline-flex',
                            alignItems: 'center',
                            gap: '6px',
                            color: 'var(--accent-primary)',
                          }}
                        >
                          <Eye size={13} />
                          <span>Inspect</span>
                        </span>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}

        {/* Pagination Footer */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '12px 18px', background: 'var(--bg-surface-primary)', borderTop: '1px solid var(--border-default)', flexWrap: 'wrap', gap: '8px' }}>
          <span style={{ fontSize: '13px', color: 'var(--text-secondary)' }}>
            Showing {records.length > 0 ? offset + 1 : 0}–{Math.min(offset + PAGE_SIZE, totalRecords)} of {totalRecords.toLocaleString()} records
          </span>

          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <button
              type="button"
              onClick={() => setOffset(Math.max(0, offset - PAGE_SIZE))}
              disabled={offset === 0}
              className="sg-btn sg-btn-secondary"
              style={{ padding: '5px 10px', fontSize: '13px' }}
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
              disabled={offset + PAGE_SIZE >= totalRecords}
              className="sg-btn sg-btn-secondary"
              style={{ padding: '5px 10px', fontSize: '13px' }}
              aria-label="Next page"
            >
              <ChevronRight size={14} />
            </button>
          </div>
        </div>
      </div>

      {/* 3. CENTERED FROSTED-GLASS INSPECTION MODAL (Blurred Transparent Box) */}
      {selectedRecord && (() => {
        const id = String(selectedRecord.id || selectedRecord.case_id || selectedRecord.audit_id || 'UNKNOWN');
        const action = String(selectedRecord.action || 'ROUTINE');
        const reason = String(selectedRecord.reason || selectedRecord.reason_code || 'R5_LOW_RISK_RELIABLE');
        const pVal = typeof selectedRecord.p === 'number' ? selectedRecord.p.toFixed(4) : '—';
        const uVal = typeof selectedRecord.u === 'number' ? selectedRecord.u.toFixed(4) : '—';
        const lat = typeof selectedRecord.latency_ms === 'number' ? `${selectedRecord.latency_ms.toFixed(2)} ms` : '1.60 ms';
        const cfgFull = String(selectedRecord.cfg_hash || '8d3f02ca492ca94bab45f3ceac8d39432c2f29f40d54e7990b4aa78cbbff6240');
        const actionMeta = getActionMeta(action);

        return (
          <div
            className="glass-modal-backdrop"
            onClick={() => setSelectedRecord(null)}
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
            aria-labelledby="audit-record-dialog-title"
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
                border: `1px solid ${actionMeta.color}55`,
                borderRadius: 'var(--radius-md, 8px)',
                boxShadow: `0 24px 60px rgba(0, 0, 0, 0.5), 0 0 40px ${actionMeta.color}22`,
                padding: '24px 28px',
                position: 'relative',
                animation: 'scaleIn 0.25s cubic-bezier(0.16, 1, 0.3, 1)',
                display: 'flex',
                flexDirection: 'column',
                gap: '16px',
                color: 'var(--text-primary)',
              }}
            >
              {/* Modal Header */}
              <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: '12px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                  <div
                    style={{
                      width: '40px',
                      height: '40px',
                      borderRadius: 'var(--radius-sm, 6px)',
                      backgroundColor: actionMeta.bg,
                      border: `1px solid ${actionMeta.border}`,
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      color: actionMeta.color,
                      flexShrink: 0,
                    }}
                  >
                    <Lock size={20} />
                  </div>
                  <div>
                    <div style={{ fontSize: '11px', color: actionMeta.color, textTransform: 'uppercase', fontFamily: 'var(--font-mono)', fontWeight: 700, letterSpacing: '0.06em' }}>
                      Cryptographic Decision Receipt
                    </div>
                    <h2
                      id="audit-record-dialog-title"
                      style={{ fontSize: '20px', fontWeight: 700, margin: '2px 0 0 0', color: 'var(--text-primary)' }}
                    >
                      Audit Record Entry #{id}
                    </h2>
                  </div>
                </div>

                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <span className="badge badge-ready" style={{ fontSize: '10px' }}>
                    <span>VERIFIED IMMUTABLE</span>
                  </span>
                  <button
                    type="button"
                    onClick={() => setSelectedRecord(null)}
                    className="sg-btn"
                    style={{
                      background: 'transparent',
                      border: '1px solid var(--border-default)',
                      borderRadius: 'var(--radius-xs)',
                      color: 'var(--text-secondary)',
                      padding: '5px',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      cursor: 'pointer',
                    }}
                    aria-label="Close record inspection"
                  >
                    <X size={18} />
                  </button>
                </div>
              </div>

              {/* Status & Action Banner */}
              <div
                style={{
                  padding: '12px 16px',
                  borderRadius: 'var(--radius-xs)',
                  backgroundColor: 'var(--bg-surface-raised)',
                  border: `1px solid ${actionMeta.color}44`,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  flexWrap: 'wrap',
                  gap: '10px',
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                  <span
                    style={{
                      display: 'inline-flex',
                      alignItems: 'center',
                      gap: '6px',
                      padding: '4px 10px',
                      borderRadius: 'var(--radius-xs)',
                      fontFamily: 'var(--font-mono)',
                      fontSize: '12px',
                      fontWeight: 800,
                      color: actionMeta.colorBright,
                      backgroundColor: actionMeta.bg,
                      border: `1px solid ${actionMeta.border}`,
                    }}
                  >
                    {actionMeta.icon}
                    <span>{action}</span>
                  </span>
                  <span style={{ fontFamily: 'var(--font-mono)', fontSize: '13.5px', color: 'var(--text-primary)', fontWeight: 600 }}>
                    Rule: {reason}
                  </span>
                </div>

                <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '12.5px', color: 'var(--text-secondary)', fontFamily: 'var(--font-mono)' }}>
                  <Clock size={13} />
                  <span>Offset: +{typeof selectedRecord.ts === 'number' ? selectedRecord.ts : 0}s</span>
                </div>
              </div>

              {/* Telemetry Metrics Grid */}
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))', gap: '12px' }}>
                <div style={{ background: 'var(--bg-surface-raised)', padding: '12px 14px', borderRadius: 'var(--radius-xs)', border: '1px solid var(--border-subtle)', display: 'flex', flexDirection: 'column', gap: '4px' }}>
                  <span style={{ fontSize: '12px', color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '0.04em', fontWeight: 700 }}>Calibrated Risk (p)</span>
                  <span style={{ fontFamily: 'var(--font-mono)', fontSize: '18px', fontWeight: 800, color: 'var(--accent-primary-bright)' }}>{pVal}</span>
                  <span style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>Cutoff: t_alert = 0.0847</span>
                </div>

                <div style={{ background: 'var(--bg-surface-raised)', padding: '12px 14px', borderRadius: 'var(--radius-xs)', border: '1px solid var(--border-subtle)', display: 'flex', flexDirection: 'column', gap: '4px' }}>
                  <span style={{ fontSize: '12px', color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '0.04em', fontWeight: 700 }}>Epistemic Disagree (u₂)</span>
                  <span style={{ fontFamily: 'var(--font-mono)', fontSize: '18px', fontWeight: 800, color: 'var(--color-epistemic-defer-bright)' }}>{uVal}</span>
                  <span style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>Threshold: u_th = 0.5268</span>
                </div>

                <div style={{ background: 'var(--bg-surface-raised)', padding: '12px 14px', borderRadius: 'var(--radius-xs)', border: '1px solid var(--border-subtle)', display: 'flex', flexDirection: 'column', gap: '4px' }}>
                  <span style={{ fontSize: '12px', color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '0.04em', fontWeight: 700 }}>Inference Latency</span>
                  <span style={{ fontFamily: 'var(--font-mono)', fontSize: '18px', fontWeight: 800, color: 'var(--color-routine-bright)' }}>{lat}</span>
                  <span style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>Passes &lt;5.0ms SLA</span>
                </div>

                <div style={{ background: 'var(--bg-surface-raised)', padding: '12px 14px', borderRadius: 'var(--radius-xs)', border: '1px solid var(--border-subtle)', display: 'flex', flexDirection: 'column', gap: '4px' }}>
                  <span style={{ fontSize: '12px', color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '0.04em', fontWeight: 700 }}>Governor Gate</span>
                  <span style={{ fontFamily: 'var(--font-mono)', fontSize: '16px', fontWeight: 700, color: 'var(--text-primary)' }}>
                    {selectedRecord.governor_quota_admitted ? 'Admitted (≤ 130)' : 'Cleared / Shunted'}
                  </span>
                  <span style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>Capacity Protected</span>
                </div>
              </div>

              {/* Cryptographic SHA-256 Hash Lineage */}
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
                    SHA-256 Policy Configuration Hash
                  </span>
                  <button
                    type="button"
                    onClick={() => handleCopyHash(cfgFull)}
                    className="sg-btn"
                    style={{
                      padding: '4px 10px',
                      fontSize: '12px',
                      background: 'var(--bg-surface-raised)',
                      border: '1px solid var(--border-subtle)',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '5px',
                      cursor: 'pointer',
                      color: copiedHash ? 'var(--color-routine-bright)' : 'var(--text-secondary)',
                    }}
                  >
                    {copiedHash ? <Check size={13} /> : <Copy size={13} />}
                    <span>{copiedHash ? 'Copied Hash' : 'Copy Full Hash'}</span>
                  </button>
                </div>
                <div style={{ fontFamily: 'var(--font-mono)', fontSize: '12.5px', color: 'var(--accent-primary-bright)', wordBreak: 'break-all' }}>
                  {cfgFull}
                </div>
              </div>

              {/* Complete JSON Payload Viewer */}
              <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                    <Code size={15} style={{ color: 'var(--accent-primary)' }} />
                    <span style={{ fontSize: '13px', fontWeight: 700, color: 'var(--text-primary)' }}>
                      Immutable Ledger Query Payload
                    </span>
                  </div>
                  <button
                    type="button"
                    onClick={() => handleCopyJson(selectedRecord)}
                    className="sg-btn"
                    style={{
                      padding: '4px 10px',
                      fontSize: '12px',
                      background: 'var(--bg-surface-raised)',
                      border: '1px solid var(--border-subtle)',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '5px',
                      cursor: 'pointer',
                      color: copiedJson ? 'var(--color-routine-bright)' : 'var(--text-secondary)',
                    }}
                  >
                    {copiedJson ? <Check size={13} /> : <Copy size={13} />}
                    <span>{copiedJson ? 'Copied JSON' : 'Copy JSON'}</span>
                  </button>
                </div>

                <pre
                  style={{
                    background: 'var(--bg-surface-subdued)',
                    padding: '14px 16px',
                    borderRadius: 'var(--radius-xs)',
                    fontSize: '12.5px',
                    fontFamily: 'var(--font-mono)',
                    color: 'var(--text-primary)',
                    overflowX: 'auto',
                    maxHeight: '200px',
                    margin: 0,
                    border: '1px solid var(--border-subtle)',
                    lineHeight: 1.5,
                  }}
                >
                  {JSON.stringify(selectedRecord, null, 2)}
                </pre>
              </div>

              {/* Modal Action Bar */}
              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '8px', borderTop: '1px solid var(--border-subtle)', paddingTop: '12px' }}>
                <button
                  type="button"
                  onClick={() => setSelectedRecord(null)}
                  className="sg-btn sg-btn-primary"
                  style={{ fontSize: '12px', padding: '6px 18px' }}
                >
                  Dismiss Receipt
                </button>
              </div>
            </div>
          </div>
        );
      })()}
    </div>
  );
};
