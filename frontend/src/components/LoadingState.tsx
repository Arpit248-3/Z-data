import React from 'react';
import { Loader2 } from 'lucide-react';

interface LoadingStateProps {
  message?: string;
  subtext?: string;
}

export const LoadingState: React.FC<LoadingStateProps> = ({
  message = 'Loading system signals...',
  subtext = 'Connecting to backend decision pipeline',
}) => {
  return (
    <div className="state-container animate-fade-in" role="status" aria-live="polite">
      <div className="state-icon loading">
        <Loader2 className="animate-spin" size={24} />
      </div>
      <h3 className="state-title">{message}</h3>
      {subtext && <p className="state-description">{subtext}</p>}
    </div>
  );
};
