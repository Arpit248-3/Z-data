import React, { useState, useRef, useEffect } from 'react';
import { ChevronDown, Database, Cpu, WifiOff, Info } from 'lucide-react';
import { useMode } from '../context/ModeContext';
import { OperatingMode } from '../lib/api/types';

interface ModeOption {
  key: OperatingMode;
  label: string;
  shortLabel: string;
  badgeClass: string;
  icon: React.ReactNode;
  description: string;
}

const MODE_OPTIONS: ModeOption[] = [
  {
    key: 'SYNTHETIC_SMOKE_ONLY',
    label: 'SYNTHETIC FIXTURE',
    shortLabel: 'SYNTHETIC',
    badgeClass: 'badge-synthetic',
    icon: <Cpu size={13} />,
    description: 'Deterministic synthetic baseline fixtures for local smoke testing & UI verification.',
  },
  {
    key: 'IEEE_CIS_OFFLINE_BENCHMARK',
    label: 'IEEE-CIS BENCHMARK',
    shortLabel: 'IEEE-CIS',
    badgeClass: 'badge-ready',
    icon: <Database size={13} />,
    description: '391-feature tabular ensemble (HistGradientBoosting + ExtraTrees + LogisticRegression) with Platt calibration & cryptographic audit logging.',
  },
  {
    key: 'LIVE_SOURCE_NOT_CONNECTED',
    label: 'LIVE (DISCONNECTED)',
    shortLabel: 'OFFLINE',
    badgeClass: 'badge-alert',
    icon: <WifiOff size={13} />,
    description: 'Production real-time banking pipelines are offline. Fails closed; no synthetic data masquerading as live.',
  },
];

export const ModeSwitcher: React.FC = () => {
  const { mode, setMode, modeReadiness } = useMode();
  const [isOpen, setIsOpen] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);

  const currentOption = MODE_OPTIONS.find((opt) => opt.key === mode) || MODE_OPTIONS[0];

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape' && isOpen) {
        setIsOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    document.addEventListener('keydown', handleKeyDown);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
      document.removeEventListener('keydown', handleKeyDown);
    };
  }, [isOpen]);

  return (
    <div className="mode-switcher-container" ref={containerRef}>
      <button
        type="button"
        id="mode-switcher-trigger"
        onClick={() => setIsOpen(!isOpen)}
        className={`badge ${currentOption.badgeClass} topbar-badge mode-switcher-trigger ${isOpen ? 'is-open' : ''}`}
        aria-haspopup="listbox"
        aria-expanded={isOpen}
        aria-controls="mode-switcher-dropdown"
        aria-label={`Operating Mode: ${currentOption.label}. Click to switch mode.`}
        title={`Operating Evidence Mode: ${currentOption.label} (Click to switch)`}
      >
        <span className="badge-dot" />
        <span className="mode-switcher-trigger-content">
          {currentOption.icon}
          <span className="badge-text-full">{currentOption.label}</span>
          <span className="badge-text-short">{currentOption.shortLabel}</span>
        </span>
        <ChevronDown
          size={12}
          className={`mode-switcher-chevron ${isOpen ? 'is-open' : ''}`}
        />
      </button>

      {isOpen && (
        <div
          id="mode-switcher-dropdown"
          className="mode-switcher-dropdown"
          role="listbox"
          aria-label="Select Operational Evidence Mode"
        >
          <div className="mode-switcher-dropdown-header">
            <span>Operational Evidence Mode</span>
            {modeReadiness && (
              <span className="mode-switcher-api-ready">API READY</span>
            )}
          </div>

          {MODE_OPTIONS.map((option) => {
            const isSelected = option.key === mode;
            return (
              <button
                key={option.key}
                type="button"
                role="option"
                aria-selected={isSelected}
                onClick={() => {
                  setMode(option.key);
                  setIsOpen(false);
                }}
                className={`mode-switcher-option ${isSelected ? 'is-selected' : ''}`}
              >
                <div className="mode-switcher-option-header">
                  <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                    <span className={`badge ${option.badgeClass}`} style={{ padding: '2px 6px', fontSize: '10px' }}>
                      <span className="badge-dot" />
                      {option.label}
                    </span>
                  </div>
                  {isSelected && (
                    <span className="mode-switcher-active-tag">
                      ACTIVE
                    </span>
                  )}
                </div>
                <div className="mode-switcher-option-desc">
                  {option.description}
                </div>
              </button>
            );
          })}

          <div className="mode-switcher-dropdown-footer">
            <Info size={11} style={{ flexShrink: 0 }} />
            <span>Mode propagates across all 8 cockpit views &amp; backend scoring</span>
          </div>
        </div>
      )}
    </div>
  );
};
