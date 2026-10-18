import React from 'react';
import { AlertCircle, RefreshCw } from 'lucide-react';

interface ErrorStateProps {
  title?: string;
  message?: string;
  onRetry?: () => void;
  code?: string;
}

export const ErrorState: React.FC<ErrorStateProps> = ({
  title = 'Connection Degraded',
  message = 'Unable to communicate with the SignalGate backend API.',
  onRetry,
  code,
}) => {
  return (
    <div className="state-container animate-fade-in" role="alert">
      <div className="state-icon error">
        <AlertCircle size={24} />
      </div>
      <h3 className="state-title">{title}</h3>
      <p className="state-description">{message}</p>
      {code && (
        <span className="badge badge-error" style={{ marginTop: '4px' }}>
          Code: {code}
        </span>
      )}
      {onRetry && (
        <button
          type="button"
          onClick={onRetry}
          className="sg-btn sg-btn-secondary"
          style={{ marginTop: '12px' }}
        >
          <RefreshCw size={14} />
          Retry Connection
        </button>
      )}
    </div>
  );
};
