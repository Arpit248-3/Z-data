import React from 'react';
import { Activity, AlertTriangle, CheckCircle2, RefreshCw, XCircle } from 'lucide-react';
import { useApiStatus } from '../lib/api/hooks';

interface ApiStatusIndicatorProps {
  showDetails?: boolean;
  showEvidenceBadge?: boolean;
}

export const ApiStatusIndicator: React.FC<ApiStatusIndicatorProps> = ({
  showDetails = false,
  showEvidenceBadge = false,
}) => {
  const { health, status, loading, error, isBackendConnected, refetch } = useApiStatus();

  if (loading && !health) {
    return (
      <div className="badge badge-disabled" title="Checking API connection...">
        <Activity size={11} className="animate-spin" />
        <span>Connecting...</span>
      </div>
    );
  }

  if (!isBackendConnected || error) {
    return (
      <div style={{ display: 'inline-flex', alignItems: 'center', gap: '6px' }}>
        <div className="badge badge-alert" title={error?.message || 'API Unreachable'}>
          <XCircle size={11} />
          <span>API Disconnected</span>
        </div>
        <button
          type="button"
          onClick={() => refetch()}
          title="Retry backend connection"
          aria-label="Retry backend connection"
          className="collapse-btn"
          style={{ padding: '2px 4px' }}
        >
          <RefreshCw size={11} />
        </button>
      </div>
    );
  }

  const overall = status?.overall_status || 'READY';
  const evidence = status?.evidence_status || 'SYNTHETIC_SMOKE_ONLY';
  const isOperational = overall === 'READY' || overall === 'OPERATIONAL_SYNTHETIC';

  return (
    <div style={{ display: 'inline-flex', alignItems: 'center', gap: '6px' }}>
      {isOperational ? (
        <div className="badge badge-ready" title="FastAPI backend operational & models ready">
          <CheckCircle2 size={11} />
          <span>Backend Ready</span>
        </div>
      ) : (
        <div className="badge badge-caution" title="FastAPI operational with missing/degraded dependencies">
          <AlertTriangle size={11} />
          <span>Backend Degraded</span>
        </div>
      )}

      {showEvidenceBadge && (
        <div
          className={evidence === 'SYNTHETIC_SMOKE_ONLY' ? 'badge badge-synthetic' : 'badge badge-ready'}
          title={`Dataset Evidence: ${evidence}`}
        >
          <span className="badge-dot" />
          <span>{evidence}</span>
        </div>
      )}

      {showDetails && status && (
        <span style={{ fontSize: '11px', color: 'var(--text-tertiary)', fontFamily: 'var(--font-mono)' }}>
          v{status.version}
        </span>
      )}
    </div>
  );
};
