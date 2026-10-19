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
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  return (
    <div
      className="mode-switcher-container"
      ref={containerRef}
      style={{ position: 'relative', display: 'inline-flex', alignItems: 'center' }}
    >
      <button
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        className={`badge ${currentOption.badgeClass} topbar-badge mode-switcher-trigger`}
        style={{
          cursor: 'pointer',
          padding: '4px 10px',
          gap: '8px',
          border: '1px solid var(--border-subtle)',
          background: 'var(--surface-secondary)',
          display: 'flex',
          alignItems: 'center',
          transition: 'all 0.15s ease',
        }}
        aria-haspopup="listbox"
        aria-expanded={isOpen}
        aria-label={`Operating Mode: ${currentOption.label}. Click to switch mode.`}
        title={`Operating Evidence Mode: ${currentOption.label} (Click to switch)`}
      >
        <span className="badge-dot" />
        <span style={{ display: 'inline-flex', alignItems: 'center', gap: '4px' }}>
          {currentOption.icon}
          <span className="badge-text-full" style={{ fontWeight: 600 }}>{currentOption.label}</span>
          <span className="badge-text-short" style={{ fontWeight: 600 }}>{currentOption.shortLabel}</span>
        </span>
        <ChevronDown
          size={12}
          style={{
            opacity: 0.7,
            transform: isOpen ? 'rotate(180deg)' : 'none',
            transition: 'transform 0.15s ease',
          }}
        />
      </button>

      {isOpen && (
        <div
          role="listbox"
          aria-label="Select Operating Mode"
          style={{
            position: 'absolute',
            top: 'calc(100% + 6px)',
            left: 0,
            zIndex: 1000,
            minWidth: '320px',
            backgroundColor: 'var(--surface-primary, #11151a)',
            border: '1px solid var(--border-subtle, #2d3748)',
            borderRadius: 'var(--radius-sm, 4px)',
            boxShadow: '0 8px 24px rgba(0, 0, 0, 0.4)',
            padding: '6px',
            display: 'flex',
            flexDirection: 'column',
            gap: '4px',
          }}
        >
          <div
            style={{
              padding: '6px 8px 4px',
              fontSize: '10px',
              textTransform: 'uppercase',
              letterSpacing: '0.08em',
              color: 'var(--text-tertiary)',
              borderBottom: '1px solid var(--border-subtle)',
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
            }}
          >
            <span>Operational Evidence Mode</span>
            {modeReadiness && (
              <span style={{ fontSize: '9px', color: 'var(--color-routine-bright)' }}>API READY</span>
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
                style={{
                  textAlign: 'left',
                  padding: '8px 10px',
                  borderRadius: 'var(--radius-xs, 2px)',
                  border: isSelected ? '1px solid var(--accent-primary, #6366f1)' : '1px solid transparent',
                  backgroundColor: isSelected ? 'rgba(99, 102, 241, 0.12)' : 'transparent',
                  color: 'var(--text-primary)',
                  cursor: 'pointer',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '4px',
                  transition: 'background-color 0.1s ease',
                }}
                onMouseEnter={(e) => {
                  if (!isSelected) {
                    e.currentTarget.style.backgroundColor = 'var(--surface-hover, rgba(255,255,255,0.04))';
                  }
                }}
                onMouseLeave={(e) => {
                  if (!isSelected) {
                    e.currentTarget.style.backgroundColor = 'transparent';
                  }
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                    <span className={`badge ${option.badgeClass}`} style={{ padding: '1px 5px', fontSize: '10px' }}>
                      <span className="badge-dot" />
                      {option.label}
                    </span>
                  </div>
                  {isSelected && (
                    <span style={{ fontSize: '10px', fontWeight: 600, color: 'var(--accent-primary, #6366f1)' }}>
                      ACTIVE
                    </span>
                  )}
                </div>
                <div
                  style={{
                    fontSize: '11px',
                    color: 'var(--text-secondary, #94a3b8)',
                    lineHeight: 1.35,
                    paddingLeft: '2px',
                  }}
                >
                  {option.description}
                </div>
              </button>
            );
          })}

          <div
            style={{
              marginTop: '4px',
              padding: '6px 8px',
              fontSize: '10px',
              color: 'var(--text-tertiary)',
              borderTop: '1px solid var(--border-subtle)',
              display: 'flex',
              alignItems: 'center',
              gap: '4px',
            }}
          >
            <Info size={11} />
            <span>Mode propagates across all 8 cockpit views & backend scoring</span>
          </div>
        </div>
      )}
    </div>
  );
};
