import React from 'react';
import { Database } from 'lucide-react';

interface EmptyStateProps {
  title?: string;
  message?: string;
  actionText?: string;
  onAction?: () => void;
}

export const EmptyState: React.FC<EmptyStateProps> = ({
  title = 'No Data Available',
  message = 'Evaluation artifacts have not been generated for this partition or scenario.',
  actionText,
  onAction,
}) => {
  return (
    <div className="state-container animate-fade-in">
      <div className="state-icon empty">
        <Database size={24} />
      </div>
      <h3 className="state-title">{title}</h3>
      <p className="state-description">{message}</p>
      {actionText && onAction && (
        <button
          type="button"
          onClick={onAction}
          className="sg-btn sg-btn-secondary"
          style={{ marginTop: '12px' }}
        >
          {actionText}
        </button>
      )}
    </div>
  );
};
