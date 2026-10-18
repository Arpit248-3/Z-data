import React, { useState, useEffect, useRef } from 'react';
import { AlertCircle, Database, ChevronDown, Info, X } from 'lucide-react';
import { api } from '../lib/api/client';
import { ModeDetail, ModesOverviewResponse } from '../lib/api/types';

export const ModeSwitcher: React.FC = () => {
  const [activeMode, setActiveMode] = useState<string>('SYNTHETIC_SMOKE_ONLY');
  const [supportedModes, setSupportedModes] = useState<ModeDetail[]>([]);
  const [isOpen, setIsOpen] = useState<boolean>(false);
  const [selectedDisclosure, setSelectedDisclosure] = useState<ModeDetail | null>(null);
  const dropdownRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    let isMounted = true;
    api.getModes()
      .then((res: ModesOverviewResponse) => {
        if (isMounted) {
          setActiveMode(res.active_mode);
          setSupportedModes(res.supported_modes);
        }
      })
      .catch(() => {
        // Fallback static definition if API is booting
        if (isMounted) {
          setSupportedModes([
            {
              mode: 'SYNTHETIC_SMOKE_ONLY',
              available: true,
              status: 'READY',
              active: true,
              description: 'Canonical synthetic 10,000-row smoke evaluation fixture is active.',
              missing_prerequisites: [],
              diagnostics: { host_ram_gb: 8.0 },
            },
            {
              mode: 'IEEE_CIS_OFFLINE_BENCHMARK',
              available: false,
              status: 'DEFERRED',
              active: false,
              description: 'Real-data IEEE-CIS training is deferred due to host 8 GB RAM limit.',
              missing_prerequisites: ['models/real_artifacts/model_bundle.joblib'],
              diagnostics: { required_ram_gb: 16.0, host_ram_gb: 8.0, real_data_training_status: 'DEFERRED' },
            },
            {
              mode: 'LIVE_SOURCE_NOT_CONNECTED',
              available: false,
              status: 'DISCONNECTED',
              active: false,
              description: 'Live transaction settlement feed is explicitly disconnected.',
              missing_prerequisites: ['Payment gateway API credentials'],
              diagnostics: { connection_status: 'DISCONNECTED' },
            },
          ]);
        }
      });

    return () => {
      isMounted = false;
    };
  }, []);

  // Close dropdown on outside click
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target as Node)) {
        setIsOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleSelect = async (mode: ModeDetail) => {
    setIsOpen(false);
    if (!mode.available || mode.mode !== 'SYNTHETIC_SMOKE_ONLY') {
      setSelectedDisclosure(mode);
      return;
    }

    try {
      await api.selectMode(mode.mode);
      setActiveMode(mode.mode);
    } catch {
      setSelectedDisclosure(mode);
    }
  };

  const getBadgeStyle = (mode: string) => {
    if (mode === 'SYNTHETIC_SMOKE_ONLY') return { bg: 'rgba(34, 197, 94, 0.15)', text: '#22c55e', dot: '#22c55e' };
    if (mode === 'IEEE_CIS_OFFLINE_BENCHMARK') return { bg: 'rgba(234, 179, 8, 0.15)', text: '#eab308', dot: '#eab308' };
    return { bg: 'rgba(148, 163, 184, 0.15)', text: '#94a3b8', dot: '#94a3b8' };
  };

  const currentBadge = getBadgeStyle(activeMode);

  return (
    <div className="mode-switcher-container" ref={dropdownRef}>
      {/* Trigger Button */}
      <button
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        className="mode-switcher-trigger"
        aria-haspopup="true"
        aria-expanded={isOpen}
        title="Operating Evidence Source Mode Switcher"
      >
        <span
          style={{
            width: '8px',
            height: '8px',
            borderRadius: '50%',
            backgroundColor: currentBadge.dot,
            boxShadow: `0 0 6px ${currentBadge.dot}`,
            flexShrink: 0,
          }}
        />
        <span className="mode-switcher-trigger-label">
          {activeMode === 'SYNTHETIC_SMOKE_ONLY' ? 'SYNTHETIC_SMOKE' : activeMode}
        </span>
        <ChevronDown size={13} style={{ color: 'var(--text-secondary)', marginLeft: '2px' }} />
      </button>

      {/* Dropdown Menu */}
      {isOpen && (
        <div className="mode-switcher-dropdown" role="menu">
          <div className="mode-switcher-dropdown-header">
            Evidence Source Modes
          </div>
          <div className="mode-switcher-dropdown-list">
            {supportedModes.map((mode) => {
              const style = getBadgeStyle(mode.mode);
              const isActive = mode.mode === activeMode;

              return (
                <button
                  key={mode.mode}
                  type="button"
                  onClick={() => handleSelect(mode)}
                  className={`mode-switcher-item ${isActive ? 'is-active' : ''}`}
                  role="menuitem"
                >
                  <div className="mode-switcher-item-header">
                    <span className="mode-switcher-item-name" title={mode.mode}>
                      <span
                        style={{
                          width: '7px',
                          height: '7px',
                          borderRadius: '50%',
                          backgroundColor: style.dot,
                          flexShrink: 0,
                        }}
                      />
                      {mode.mode}
                    </span>
                    <span
                      className="mode-switcher-item-badge"
                      style={{
                        backgroundColor: style.bg,
                        color: style.text,
                        border: `1px solid ${style.text}40`,
                      }}
                    >
                      {isActive ? 'ACTIVE' : mode.status}
                    </span>
                  </div>
                  <p className="mode-switcher-item-desc">
                    {mode.description}
                  </p>
                </button>
              );
            })}
          </div>
          <div className="mode-switcher-dropdown-footer">
            <Info size={13} style={{ color: 'var(--color-manual-review, #eab308)', flexShrink: 0 }} />
            <span>Fails closed: unavailable modes never fallback silently.</span>
          </div>
        </div>
      )}

      {/* Diagnostic & Limitation Modal */}
      {selectedDisclosure && (
        <div className="mode-switcher-modal-backdrop" onClick={() => setSelectedDisclosure(null)}>
          <div
            className="mode-switcher-modal-card"
            onClick={(e) => e.stopPropagation()}
            role="dialog"
            aria-modal="true"
          >
            <div className="mode-switcher-modal-header">
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                {selectedDisclosure.mode === 'IEEE_CIS_OFFLINE_BENCHMARK' ? (
                  <Database size={18} style={{ color: 'var(--color-manual-review, #eab308)' }} />
                ) : (
                  <AlertCircle size={18} style={{ color: 'var(--text-tertiary)' }} />
                )}
                <h3 style={{ margin: 0, fontSize: '13.5px', fontWeight: 700, color: 'var(--text-primary)' }}>
                  {selectedDisclosure.mode === 'IEEE_CIS_OFFLINE_BENCHMARK'
                    ? 'IEEE-CIS Real-Data Benchmark: Deferred'
                    : 'Live Source: Disconnected'}
                </h3>
              </div>
              <button
                type="button"
                onClick={() => setSelectedDisclosure(null)}
                style={{
                  background: 'transparent',
                  border: 'none',
                  color: 'var(--text-secondary)',
                  cursor: 'pointer',
                  padding: '4px',
                  display: 'flex',
                  alignItems: 'center',
                }}
              >
                <X size={16} />
              </button>
            </div>

            <div className="mode-switcher-modal-body">
              {selectedDisclosure.mode === 'IEEE_CIS_OFFLINE_BENCHMARK' ? (
                <>
                  <div
                    style={{
                      padding: '10px 12px',
                      borderRadius: 'var(--radius-sm)',
                      background: 'rgba(234, 179, 8, 0.12)',
                      border: '1px solid rgba(234, 179, 8, 0.3)',
                      color: 'var(--color-manual-review, #eab308)',
                      fontWeight: 700,
                      fontSize: '11.5px',
                    }}
                  >
                    Hardware Memory Constraint (8 GB RAM Host)
                  </div>
                  <p style={{ margin: 0 }}>
                    Full IEEE-CIS model training and ensemble fitting across 590,540 transactions
                    require a minimum of <strong>16 GB RAM</strong>. On this host (7.75 GB RAM), full training is
                    <strong> permanently deferred</strong> to prevent out-of-memory system freeze.
                  </p>
                  <p style={{ margin: 0 }}>
                    In strict accordance with Master Specification &sect; C1, SignalGate
                    <strong> fails closed</strong> and refuses to substitute synthetic results under a real-data label.
                  </p>
                  <div
                    style={{
                      background: 'var(--bg-surface-subdued)',
                      border: '1px solid var(--border-subtle)',
                      padding: '10px',
                      borderRadius: 'var(--radius-xs)',
                      fontFamily: 'var(--font-mono)',
                      fontSize: '11px',
                      display: 'flex',
                      flexDirection: 'column',
                      gap: '4px',
                    }}
                  >
                    <div>Status: {selectedDisclosure.status}</div>
                    <div>Prerequisites: {selectedDisclosure.missing_prerequisites.join(', ') || 'Checkpoints deferred'}</div>
                  </div>
                </>
              ) : (
                <>
                  <div
                    style={{
                      padding: '10px 12px',
                      borderRadius: 'var(--radius-sm)',
                      background: 'rgba(148, 163, 184, 0.12)',
                      border: '1px solid rgba(148, 163, 184, 0.3)',
                      color: 'var(--text-secondary)',
                      fontWeight: 700,
                      fontSize: '11.5px',
                    }}
                  >
                    Offline Forensic Triage Mode Active
                  </div>
                  <p style={{ margin: 0 }}>
                    SignalGate operates strictly in offline forensic decision-support and replay modes.
                    Live core banking Kafka streaming and payment gateway settlements are disconnected.
                  </p>
                </>
              )}
            </div>

            <div className="mode-switcher-modal-footer">
              <button
                type="button"
                onClick={() => setSelectedDisclosure(null)}
                style={{
                  padding: '7px 14px',
                  borderRadius: 'var(--radius-xs)',
                  background: 'var(--accent-primary)',
                  color: '#0A0F14',
                  fontWeight: 700,
                  fontSize: '11.5px',
                  border: 'none',
                  cursor: 'pointer',
                  transition: 'opacity var(--transition-fast)',
                }}
              >
                Acknowledge &amp; Keep Synthetic Mode
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
