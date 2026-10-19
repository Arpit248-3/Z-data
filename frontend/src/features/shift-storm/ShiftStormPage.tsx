import React, { useState, useEffect, useRef, useCallback } from 'react';
import {
  Play,
  Pause,
  RotateCcw,
  SkipForward,
  SkipBack,
  Sliders,
  Activity,
  Layers,
  ShieldAlert,
  ShieldCheck,
  UserCheck,
  Sparkles,
  CreditCard,
  Clock,
  Cpu,
  CheckCircle2,
  Lock,
} from 'lucide-react';
import { api } from '../../lib/api/client';
import { ReplayRowItem, ScenarioItem } from '../../lib/api/types';
import { useMode } from '../../context/ModeContext';
import { LoadingState } from '../../components/LoadingState';
import { ErrorState } from '../../components/ErrorState';

const getReasonDescription = (reason: string) => {
  switch (reason) {
    case 'R1_HIGH_RISK':
    case 'R1_HIGH_RISK_FRAUD':
      return 'Risk p ≥ 0.0847 exceeds direct alert cutoff; escalated to critical fraud alert.';
    case 'R2_INTERMEDIATE_RISK':
    case 'R2_HIGH_RISK_REVIEW':
      return 'Risk p ≥ 0.0710 in elevated zone; routed to human investigator review queue.';
    case 'R3_MODEL_DISAGREEMENT':
    case 'R3_DISAGREEMENT':
      return 'Epistemic disagreement u₂ ≥ 0.5268 triggers uncertainty escalation to review.';
    case 'R4_UNFAMILIAR_INPUT':
      return 'Unfamiliar input space detected; routed to human investigator review queue.';
    case 'R0_SIGNAL_UNAVAILABLE':
      return 'Signal unavailable or out of bounds; fails closed to investigator review queue.';
    case 'R5_LOW_RISK_RELIABLE':
      return 'Risk p < 0.0710 & u₂ < 0.5268; zero-touch frictionless routine clearance.';
    case 'R6_CAPACITY_DEFERRED':
      return 'Analyst capacity ceiling (130 slots) saturated; shunted to safe held deferral.';
    default:
      return 'Inference evaluated against frozen triage policy thresholds.';
  }
};

const getActionMeta = (action: string) => {
  switch (action) {
    case 'FRAUD_ALERT':
      return {
        label: 'CRITICAL FRAUD ALERT',
        shortLabel: 'ALERT',
        color: 'var(--color-fraud-alert)',
        colorBright: 'var(--color-fraud-alert-bright)',
        bg: 'var(--color-fraud-alert-tint)',
        border: 'var(--color-fraud-alert-dim)',
        icon: <ShieldAlert size={14} />,
      };
    case 'MANUAL_REVIEW':
      return {
        label: 'HUMAN REVIEW REQUIRED',
        shortLabel: 'REVIEW',
        color: 'var(--color-manual-review)',
        colorBright: 'var(--color-manual-review-bright)',
        bg: 'var(--color-manual-review-tint)',
        border: 'var(--color-manual-review-dim)',
        icon: <UserCheck size={14} />,
      };
    case 'ROUTINE':
      return {
        label: 'ROUTINE CLEARANCE',
        shortLabel: 'ROUTINE',
        color: 'var(--color-routine)',
        colorBright: 'var(--color-routine-bright)',
        bg: 'var(--color-routine-tint)',
        border: 'var(--color-routine-dim)',
        icon: <CheckCircle2 size={14} />,
      };
    default: // DEFERRED
      return {
        label: 'EPISTEMIC DEFERRED',
        shortLabel: 'DEFERRED',
        color: 'var(--color-epistemic-defer)',
        colorBright: 'var(--color-epistemic-defer-bright)',
        bg: 'var(--color-epistemic-defer-tint)',
        border: 'var(--color-epistemic-defer-dim)',
        icon: <Cpu size={14} />,
      };
  }
};

export const ShiftStormPage: React.FC = () => {
  const { mode, isRealDataMode, isLiveDisconnected } = useMode();
  const [scenarios, setScenarios] = useState<ScenarioItem[]>([]);
  const [selectedScenario, setSelectedScenario] = useState<string>('S0');
  const [rows, setRows] = useState<ReplayRowItem[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Playback state
  const [currentIndex, setCurrentIndex] = useState<number>(0);
  const [isPlaying, setIsPlaying] = useState<boolean>(false);
  const [playbackSpeed, setPlaybackSpeed] = useState<number>(1); // 0.5x, 1x, 2x, 5x

  const timerRef = useRef<NodeJS.Timeout | null>(null);

  // Load scenarios on mount
  useEffect(() => {
    let isMounted = true;
    api.getScenarios()
      .then((res) => {
        if (isMounted && res.scenarios) {
          setScenarios(res.scenarios);
        }
      })
      .catch((err) => {
        console.warn('Could not load scenarios list:', err);
      });
    return () => { isMounted = false; };
  }, []);

  // Fetch replay rows for the selected scenario
  const fetchRows = useCallback(async (scenarioId: string) => {
    setLoading(true);
    setError(null);
    setIsPlaying(false);
    setCurrentIndex(0);
    try {
      const res = await api.getReplayRows({ scenario: scenarioId, offset: 0, limit: 200 });
      if (res && res.rows) {
        setRows(res.rows);
      } else {
        setRows([]);
      }
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to load replay rows');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchRows(selectedScenario);
  }, [selectedScenario, fetchRows]);

  // Playback timer loop
  useEffect(() => {
    if (isPlaying && rows.length > 0) {
      const intervalMs = Math.max(100, Math.floor(1000 / playbackSpeed));
      timerRef.current = setInterval(() => {
        setCurrentIndex((prev) => {
          if (prev >= rows.length - 1) {
            setIsPlaying(false);
            return prev;
          }
          return prev + 1;
        });
      }, intervalMs);
    } else {
      if (timerRef.current) clearInterval(timerRef.current);
    }

    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
    };
  }, [isPlaying, playbackSpeed, rows.length]);

  const currentRow = rows[currentIndex] || null;

  const handlePlayPause = () => {
    if (currentIndex >= rows.length - 1 && !isPlaying) {
      setCurrentIndex(0);
    }
    setIsPlaying(!isPlaying);
  };

  const handleStepForward = () => {
    setIsPlaying(false);
    setCurrentIndex((prev) => Math.min(rows.length - 1, prev + 1));
  };

  const handleStepBack = () => {
    setIsPlaying(false);
    setCurrentIndex((prev) => Math.max(0, prev - 1));
  };

  const handleReset = () => {
    setIsPlaying(false);
    setCurrentIndex(0);
  };

  // Recent 6 transactions window
  const recentSlice = rows.slice(Math.max(0, currentIndex - 5), currentIndex + 1);

  return (
    <div className="shift-storm-page animate-fade-in" style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-4)' }}>
      {/* 1. Page Header & Provenance Banner */}
      <div className="page-header-card" style={{ borderLeftColor: 'var(--accent-violet)' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '14px' }}>
          <div>
            <div className="page-header-eyebrow" style={{ marginBottom: '6px' }}>
              <span className={`badge ${isRealDataMode ? 'badge-ready' : isLiveDisconnected ? 'badge-alert' : 'badge-synthetic'}`}>
                <span>{mode}</span>
              </span>
              <span>{isRealDataMode ? 'IEEE-CIS OFFLINE BENCHMARK HARNESS' : isLiveDisconnected ? 'LIVE INGESTION DISCONNECTED' : 'OFFLINE REPLAY PROTOCOL'}</span>
              <span style={{ color: 'var(--border-active)' }}>|</span>
              <span style={{ color: 'var(--text-secondary)' }}>
                {rows.length > 0 ? `${rows.length} loaded cases` : 'Awaiting stream'}
              </span>
            </div>
            <h1 className="page-header-title">
              SHIFT STORM REPLAY &amp; TEMPORAL TELEMETRY
            </h1>
            <p className="page-header-desc">
              High-resolution chronological replay of distribution shifts across calibrated risk (<span style={{ color: 'var(--accent-primary)', fontWeight: 600 }}>p</span>)
              and epistemic disagreement (<span style={{ color: 'var(--color-epistemic-defer-bright)', fontWeight: 600 }}>u₂</span>).
            </p>
          </div>

          {/* Scenario Selector Dropdown */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span style={{ fontSize: '12px', color: 'var(--text-secondary)', fontWeight: 600 }}>Scenario:</span>
            <select
              value={selectedScenario}
              onChange={(e) => setSelectedScenario(e.target.value)}
              className="sg-select"
              style={{
                background: 'var(--bg-surface-raised)',
                color: 'var(--text-primary)',
                border: '1px solid var(--border-default)',
                borderRadius: 'var(--radius-xs)',
                padding: '5px 10px',
                fontSize: '12px',
                fontFamily: 'var(--font-mono)',
              }}
            >
              <option value="S0">S0: Untouched Reference (2,000 txns)</option>
              <option value="S1">S1: Temporal Prevalence Burst (1,200 txns)</option>
              <option value="S3">S3: Covariate Shift Storm (2,000 txns)</option>
              {scenarios.filter((s) => s.scenario_id !== 'S0' && s.scenario_id !== 'S1' && s.scenario_id !== 'S3').map((s) => (
                <option key={s.scenario_id} value={s.scenario_id}>
                  {s.scenario_id}: {s.name} ({s.sample_count || 2000} txns)
                </option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {isLiveDisconnected && (
        <div
          className="card"
          style={{
            borderLeft: '4px solid var(--color-fraud-alert, #ef4444)',
            backgroundColor: 'rgba(239, 68, 68, 0.08)',
            padding: '14px 18px',
            display: 'flex',
            flexDirection: 'column',
            gap: '6px',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span className="badge badge-alert">DISCONNECTED</span>
            <span style={{ fontWeight: 700, fontSize: '13px', color: 'var(--color-fraud-alert-bright)' }}>
              LIVE EDGE BANKING BROKERS OFFLINE
            </span>
          </div>
          <p style={{ margin: 0, fontSize: '12px', color: 'var(--text-secondary)', lineHeight: 1.4 }}>
            Live production transaction event streaming is disconnected. Real-time shift replay is running against frozen offline validation partitions.
          </p>
        </div>
      )}

      {loading ? (
        <LoadingState message="Streaming chronological evaluation replay rows..." />
      ) : error ? (
        <ErrorState
          title="Replay Feed Unavailable"
          message={error}
          onRetry={() => fetchRows(selectedScenario)}
        />
      ) : rows.length === 0 ? (
        <div className="sg-card" style={{ padding: '32px', textAlign: 'center' }}>
          <p style={{ color: 'var(--text-secondary)' }}>No replay rows persisted for scenario {selectedScenario}.</p>
        </div>
      ) : (
        <>
          {/* 2. Interactive Playback Transport Console */}
          <div className="sg-card" style={{ padding: '12px 16px', display: 'flex', flexDirection: 'column', gap: '10px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '12px' }}>
              {/* Transport Controls */}
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <button
                  type="button"
                  onClick={handleReset}
                  className="sg-btn sg-btn-secondary"
                  title="Reset to beginning"
                  aria-label="Reset playback to beginning"
                >
                  <RotateCcw size={13} />
                </button>
                <button
                  type="button"
                  onClick={handleStepBack}
                  disabled={currentIndex === 0}
                  className="sg-btn sg-btn-secondary"
                  title="Step backward"
                  aria-label="Step backward 1 case"
                >
                  <SkipBack size={13} />
                </button>
                <button
                  type="button"
                  onClick={handlePlayPause}
                  className="sg-btn sg-btn-primary"
                  style={{ minWidth: '85px', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '6px' }}
                  aria-label={isPlaying ? 'Pause replay' : 'Play replay'}
                >
                  {isPlaying ? <Pause size={14} /> : <Play size={14} />}
                  <span>{isPlaying ? 'PAUSE' : 'PLAY'}</span>
                </button>
                <button
                  type="button"
                  onClick={handleStepForward}
                  disabled={currentIndex === rows.length - 1}
                  className="sg-btn sg-btn-secondary"
                  title="Step forward"
                  aria-label="Step forward 1 case"
                >
                  <SkipForward size={13} />
                </button>
              </div>

              {/* Position Readout */}
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                <span style={{ fontSize: '12.5px', color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
                  Position:
                </span>
                <span style={{ fontFamily: 'var(--font-mono)', fontSize: '15px', fontWeight: 700, color: 'var(--text-primary)' }}>
                  Case {currentIndex + 1} <span style={{ color: 'var(--text-tertiary)', fontWeight: 400 }}>/ {rows.length}</span>
                </span>
                <span className="badge badge-ready" style={{ fontSize: '11px', padding: '3px 8px' }}>
                  <span>{isPlaying ? 'PLAYING' : 'PAUSED'}</span>
                </span>
              </div>

              {/* Speed Multiplier Controls */}
              <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                <span style={{ fontSize: '12.5px', color: 'var(--text-tertiary)', marginRight: '4px' }}>SPEED:</span>
                {[0.5, 1, 2, 5].map((spd) => (
                  <button
                    key={spd}
                    type="button"
                    onClick={() => setPlaybackSpeed(spd)}
                    className="sg-btn"
                    style={{
                      padding: '4px 9px',
                      fontSize: '12px',
                      fontFamily: 'var(--font-mono)',
                      background: playbackSpeed === spd ? 'var(--accent-primary)' : 'var(--bg-surface-raised)',
                      color: playbackSpeed === spd ? '#000' : 'var(--text-secondary)',
                      fontWeight: playbackSpeed === spd ? 700 : 400,
                      borderColor: playbackSpeed === spd ? 'var(--accent-primary)' : 'var(--border-subtle)',
                    }}
                  >
                    {spd}x
                  </button>
                ))}
              </div>
            </div>

            {/* Scrubbing Range Slider */}
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <input
                type="range"
                min={0}
                max={rows.length - 1}
                value={currentIndex}
                onChange={(e) => {
                  setIsPlaying(false);
                  setCurrentIndex(Number(e.target.value));
                }}
                style={{
                  width: '100%',
                  accentColor: 'var(--accent-primary)',
                  cursor: 'pointer',
                  height: '8px',
                }}
                aria-label="Timeline position scrubber"
              />
            </div>
          </div>

          {/* 3. Real-Time Case Inspection & Triage Flow */}
          {currentRow && (
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(400px, 1fr))', gap: 'var(--space-4)' }}>
              {/* Dossier Card: Current Transaction Details */}
              <div
                className="sg-card"
                style={{
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '14px',
                  padding: '20px',
                  borderTop: '3px solid var(--accent-primary)',
                  boxShadow: '0 8px 24px rgba(0, 0, 0, 0.25)',
                }}
              >
                <div className="sg-card-header" style={{ paddingBottom: '12px', borderBottom: '1px solid var(--border-subtle)' }}>
                  <div className="sg-card-title" style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                    <div
                      style={{
                        width: '32px',
                        height: '32px',
                        borderRadius: 'var(--radius-xs)',
                        background: 'var(--accent-primary-tint)',
                        border: '1px solid var(--accent-primary-dim)',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        color: 'var(--accent-primary)',
                      }}
                    >
                      <Activity size={17} />
                    </div>
                    <div>
                      <div style={{ fontSize: '15px', fontWeight: 700, color: 'var(--text-primary)' }}>
                        Transaction Dossier & Entity Profile
                      </div>
                      <div style={{ fontSize: '12px', color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
                        Inference Payload Telemetry
                      </div>
                    </div>
                  </div>
                  <span
                    style={{
                      fontFamily: 'var(--font-mono)',
                      fontSize: '12.5px',
                      color: 'var(--accent-primary-bright)',
                      background: 'var(--bg-surface-raised)',
                      padding: '4px 10px',
                      borderRadius: 'var(--radius-xs)',
                      border: '1px solid var(--border-default)',
                      fontWeight: 700,
                    }}
                  >
                    TXN #{currentRow.transaction_id || currentRow.case_id || currentIndex + 1}
                  </span>
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
                  {/* Amount Tile */}
                  <div
                    style={{
                      background: 'var(--bg-surface-raised)',
                      padding: '14px 16px',
                      borderRadius: 'var(--radius-xs)',
                      border: '1px solid var(--border-subtle)',
                      display: 'flex',
                      flexDirection: 'column',
                      gap: '4px',
                    }}
                  >
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <span style={{ fontSize: '12px', color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '0.04em', fontWeight: 700 }}>
                        Evaluated Amount
                      </span>
                      <Sparkles size={14} style={{ color: 'var(--accent-primary)' }} />
                    </div>
                    <div style={{ fontFamily: 'var(--font-mono)', fontSize: '24px', fontWeight: 800, color: 'var(--text-primary)' }}>
                      ${currentRow.amount.toFixed(2)}
                    </div>
                    <span style={{ fontSize: '13px', color: 'var(--text-secondary)' }}>
                      Inbound Transaction Value
                    </span>
                  </div>

                  {/* Card & Product Tile */}
                  <div
                    style={{
                      background: 'var(--bg-surface-raised)',
                      padding: '14px 16px',
                      borderRadius: 'var(--radius-xs)',
                      border: '1px solid var(--border-subtle)',
                      display: 'flex',
                      flexDirection: 'column',
                      gap: '4px',
                    }}
                  >
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <span style={{ fontSize: '12px', color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '0.04em', fontWeight: 700 }}>
                        Card & Product Rail
                      </span>
                      <CreditCard size={14} style={{ color: 'var(--text-secondary)' }} />
                    </div>
                    <div style={{ fontFamily: 'var(--font-mono)', fontSize: '16px', fontWeight: 700, color: 'var(--accent-primary-bright)' }}>
                      {currentRow.card4.toUpperCase()} • {currentRow.product_cd}
                    </div>
                    <span style={{ fontSize: '13px', color: 'var(--text-secondary)' }}>
                      Interbank Clearing Channel
                    </span>
                  </div>

                  {/* Timestamp Offset Tile */}
                  <div
                    style={{
                      background: 'var(--bg-surface-raised)',
                      padding: '14px 16px',
                      borderRadius: 'var(--radius-xs)',
                      border: '1px solid var(--border-subtle)',
                      display: 'flex',
                      flexDirection: 'column',
                      gap: '4px',
                    }}
                  >
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <span style={{ fontSize: '12px', color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '0.04em', fontWeight: 700 }}>
                        Timestamp Offset
                      </span>
                      <Clock size={14} style={{ color: 'var(--text-secondary)' }} />
                    </div>
                    <div style={{ fontFamily: 'var(--font-mono)', fontSize: '16px', fontWeight: 700, color: 'var(--text-primary)' }}>
                      +{currentRow.timestamp.toLocaleString()}s
                    </div>
                    <span style={{ fontSize: '13px', color: 'var(--text-secondary)' }}>
                      T + {(currentRow.timestamp / 3600).toFixed(1)}h Ingestion Delta
                    </span>
                  </div>

                  {/* Offline Ground Truth Tile */}
                  <div
                    style={{
                      background: 'var(--bg-surface-raised)',
                      padding: '14px 16px',
                      borderRadius: 'var(--radius-xs)',
                      border: `1px solid ${currentRow.offline_ground_truth?.is_fraud === 1 ? 'var(--color-fraud-alert)44' : 'var(--color-routine)44'}`,
                      display: 'flex',
                      flexDirection: 'column',
                      gap: '4px',
                    }}
                  >
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <span style={{ fontSize: '12px', color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '0.04em', fontWeight: 700 }}>
                        Offline Ground Truth
                      </span>
                      {currentRow.offline_ground_truth?.is_fraud === 1 ? (
                        <ShieldAlert size={14} style={{ color: 'var(--color-fraud-alert)' }} />
                      ) : (
                        <ShieldCheck size={14} style={{ color: 'var(--color-routine)' }} />
                      )}
                    </div>
                    <div
                      style={{
                        fontFamily: 'var(--font-mono)',
                        fontSize: '16px',
                        fontWeight: 800,
                        color: currentRow.offline_ground_truth?.is_fraud === 1 ? 'var(--color-fraud-alert-bright)' : 'var(--color-routine-bright)',
                      }}
                    >
                      {currentRow.offline_ground_truth?.is_fraud === 1 ? 'FRAUD (1)' : 'LEGIT (0)'}
                    </div>
                    <span style={{ fontSize: '13px', color: 'var(--text-secondary)' }}>
                      Evaluation Partition Benchmark
                    </span>
                  </div>
                </div>

                <div
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '10px',
                    fontSize: '12.5px',
                    color: 'var(--text-secondary)',
                    background: 'var(--bg-surface-subdued)',
                    padding: '10px 14px',
                    borderRadius: 'var(--radius-xs)',
                    border: '1px solid var(--border-subtle)',
                  }}
                >
                  <Lock size={14} style={{ flexShrink: 0, color: 'var(--accent-primary)' }} />
                  <span>Ground truth label is an offline verification benchmark; never leaked into live router execution.</span>
                </div>
              </div>

              {/* Signals & Router Decision Card */}
              {(() => {
                const actionMeta = getActionMeta(currentRow.action);
                return (
                  <div
                    className="sg-card"
                    style={{
                      display: 'flex',
                      flexDirection: 'column',
                      gap: '14px',
                      padding: '20px',
                      borderTop: `3px solid ${actionMeta.color}`,
                      boxShadow: '0 8px 24px rgba(0, 0, 0, 0.25)',
                    }}
                  >
                    <div className="sg-card-header" style={{ paddingBottom: '12px', borderBottom: '1px solid var(--border-subtle)' }}>
                      <div className="sg-card-title" style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                        <div
                          style={{
                            width: '32px',
                            height: '32px',
                            borderRadius: 'var(--radius-xs)',
                            background: actionMeta.bg,
                            border: `1px solid ${actionMeta.border}`,
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            color: actionMeta.color,
                          }}
                        >
                          <Sliders size={17} />
                        </div>
                        <div>
                          <div style={{ fontSize: '15px', fontWeight: 700, color: 'var(--text-primary)' }}>
                            Decision & Signal Telemetry
                          </div>
                          <div style={{ fontSize: '12px', color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
                            Policy Execution Engine
                          </div>
                        </div>
                      </div>

                      {/* Large Glowing Action Badge */}
                      <span
                        style={{
                          display: 'inline-flex',
                          alignItems: 'center',
                          gap: '6px',
                          padding: '6px 12px',
                          borderRadius: 'var(--radius-xs)',
                          fontFamily: 'var(--font-mono)',
                          fontSize: '12px',
                          fontWeight: 800,
                          color: actionMeta.colorBright,
                          background: actionMeta.bg,
                          border: `1px solid ${actionMeta.color}`,
                          boxShadow: `0 0 10px ${actionMeta.color}33`,
                          letterSpacing: '0.04em',
                        }}
                      >
                        {actionMeta.icon}
                        <span>{actionMeta.label}</span>
                      </span>
                    </div>

                    {/* Risk & Disagreement Progress Meters */}
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                      {/* Calibrated Risk Meter */}
                      <div>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', fontSize: '12.5px', marginBottom: '5px' }}>
                          <span style={{ color: 'var(--text-secondary)', fontWeight: 600 }}>
                            Calibrated Risk (p):
                          </span>
                          <div style={{ display: 'flex', alignItems: 'baseline', gap: '8px' }}>
                            <span style={{ fontFamily: 'var(--font-mono)', color: 'var(--text-tertiary)', fontSize: '11px' }}>
                              [t_review: 0.0710 | t_alert: 0.0847]
                            </span>
                            <span style={{ fontFamily: 'var(--font-mono)', color: 'var(--accent-primary-bright)', fontWeight: 800, fontSize: '15px' }}>
                              {currentRow.p.toFixed(4)}
                            </span>
                          </div>
                        </div>
                        <div style={{ width: '100%', height: '10px', background: 'var(--bg-surface-subdued)', borderRadius: '5px', overflow: 'hidden', border: '1px solid var(--border-subtle)', position: 'relative' }}>
                          <div
                            style={{
                              width: `${Math.min(100, (currentRow.p / 0.12) * 100)}%`,
                              height: '100%',
                              backgroundColor: currentRow.p >= 0.0847 ? 'var(--color-fraud-alert)' : currentRow.p >= 0.0710 ? 'var(--color-manual-review)' : 'var(--color-routine)',
                              transition: 'width 0.3s cubic-bezier(0.16, 1, 0.3, 1), background-color 0.3s ease',
                              boxShadow: `0 0 8px ${currentRow.p >= 0.0847 ? 'var(--color-fraud-alert)' : currentRow.p >= 0.0710 ? 'var(--color-manual-review)' : 'var(--color-routine)'}88`,
                            }}
                          />
                        </div>
                      </div>

                      {/* Epistemic Disagreement Meter */}
                      <div>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', fontSize: '12.5px', marginBottom: '5px' }}>
                          <span style={{ color: 'var(--text-secondary)', fontWeight: 600 }}>
                            Disagreement Residual (u₂):
                          </span>
                          <div style={{ display: 'flex', alignItems: 'baseline', gap: '8px' }}>
                            <span style={{ fontFamily: 'var(--font-mono)', color: 'var(--text-tertiary)', fontSize: '11px' }}>
                              [u_threshold: 0.5268]
                            </span>
                            <span style={{ fontFamily: 'var(--font-mono)', color: 'var(--color-epistemic-defer-bright)', fontWeight: 800, fontSize: '15px' }}>
                              {currentRow.u.toFixed(4)}
                            </span>
                          </div>
                        </div>
                        <div style={{ width: '100%', height: '10px', background: 'var(--bg-surface-subdued)', borderRadius: '5px', overflow: 'hidden', border: '1px solid var(--border-subtle)' }}>
                          <div
                            style={{
                              width: `${Math.min(100, Math.max(0, ((currentRow.u + 0.5) / 1.5) * 100))}%`,
                              height: '100%',
                              backgroundColor: 'var(--color-epistemic-defer)',
                              transition: 'width 0.3s cubic-bezier(0.16, 1, 0.3, 1)',
                              boxShadow: '0 0 8px rgba(180, 160, 248, 0.4)',
                            }}
                          />
                        </div>
                      </div>
                    </div>

                    {/* Reason Code & Governor Status */}
                    <div style={{ display: 'grid', gridTemplateColumns: '1.2fr 1fr', gap: '14px', marginTop: '4px' }}>
                      <div
                        style={{
                          background: 'var(--bg-surface-raised)',
                          padding: '12px 14px',
                          borderRadius: 'var(--radius-xs)',
                          border: '1px solid var(--border-subtle)',
                          display: 'flex',
                          flexDirection: 'column',
                          gap: '4px',
                        }}
                      >
                        <div style={{ fontSize: '12px', color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '0.04em', fontWeight: 700 }}>
                          Triggered Routing Rule
                        </div>
                        <div style={{ fontFamily: 'var(--font-mono)', fontSize: '14.5px', fontWeight: 800, color: actionMeta.color }}>
                          {currentRow.reason_code}
                        </div>
                        <div style={{ fontSize: '13px', color: 'var(--text-secondary)', lineHeight: 1.45, marginTop: '2px' }}>
                          {getReasonDescription(currentRow.reason_code)}
                        </div>
                      </div>

                      <div
                        style={{
                          background: 'var(--bg-surface-raised)',
                          padding: '12px 14px',
                          borderRadius: 'var(--radius-xs)',
                          border: '1px solid var(--border-subtle)',
                          display: 'flex',
                          flexDirection: 'column',
                          gap: '4px',
                        }}
                      >
                        <div style={{ fontSize: '12px', color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '0.04em', fontWeight: 700 }}>
                          Human Quota Governor
                        </div>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                          <span
                            style={{
                              width: '10px',
                              height: '10px',
                              borderRadius: '50%',
                              backgroundColor: currentRow.governor_status === 'admitted' ? 'var(--color-routine)' : 'var(--color-manual-review)',
                              boxShadow: `0 0 8px ${currentRow.governor_status === 'admitted' ? 'var(--color-routine)' : 'var(--color-manual-review)'}`,
                            }}
                          />
                          <span style={{ fontFamily: 'var(--font-mono)', fontSize: '14.5px', fontWeight: 800, color: currentRow.governor_status === 'admitted' ? 'var(--color-routine-bright)' : 'var(--color-manual-review-bright)' }}>
                            {currentRow.governor_status.toUpperCase()}
                          </span>
                        </div>
                        <div style={{ fontSize: '13px', color: 'var(--text-secondary)', lineHeight: 1.45, marginTop: '2px' }}>
                          {currentRow.governor_status === 'admitted'
                            ? 'Analyst slot quota reserved (≤ 130)'
                            : 'Capacity saturated; shunted to held queue (R6)'}
                        </div>
                      </div>
                    </div>
                  </div>
                );
              })()}
            </div>
          )}

          {/* 4. Recent Evaluated Transactions Timeline Strip (Elevated Glass Stream Rail) */}
          <div
            className="sg-card"
            style={{
              padding: '16px',
              display: 'flex',
              flexDirection: 'column',
              gap: '12px',
              borderLeft: '3px solid var(--accent-primary)',
              background: 'var(--bg-surface-primary)',
              boxShadow: '0 8px 24px rgba(0, 0, 0, 0.25)',
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '10px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                <div
                  style={{
                    width: '32px',
                    height: '32px',
                    borderRadius: 'var(--radius-xs)',
                    background: 'var(--accent-primary-tint)',
                    border: '1px solid var(--accent-primary-dim)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    color: 'var(--accent-primary)',
                    flexShrink: 0,
                  }}
                >
                  <Layers size={17} />
                </div>
                <div>
                  <div style={{ fontSize: '15.5px', fontWeight: 800, color: 'var(--text-primary)', letterSpacing: '-0.01em', textTransform: 'uppercase' }}>
                    Evaluated Stream Window (Cases {Math.max(1, currentIndex - 4)} – {currentIndex + 1})
                  </div>
                  <div style={{ fontSize: '13.5px', color: 'var(--text-secondary)', fontWeight: 500, marginTop: '2px' }}>
                    Chronological rolling buffer &bull; Click any chip to jump timeline
                  </div>
                </div>
              </div>

              <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                <span className="badge badge-synthetic" style={{ fontSize: '12px', padding: '4px 10px', fontWeight: 700 }}>
                  <span>BUFFER: {rows.length} TXNS</span>
                </span>
                <span style={{ fontFamily: 'var(--font-mono)', fontSize: '13.5px', color: 'var(--accent-primary-bright)', fontWeight: 700, padding: '4px 10px', background: 'var(--bg-surface-raised)', borderRadius: 'var(--radius-xs)', border: '1px solid var(--border-subtle)' }}>
                  ACTIVE CASE #{currentRow?.row_id || currentIndex + 1}
                </span>
              </div>
            </div>

            {/* Stream Scroll Rail */}
            <div
              style={{
                display: 'flex',
                gap: '12px',
                overflowX: 'auto',
                padding: '8px 4px 12px 4px',
                scrollbarWidth: 'thin',
              }}
            >
              {recentSlice.map((r, idx) => {
                const globalIndex = Math.max(0, currentIndex - 5) + idx;
                const isSelected = globalIndex === currentIndex;
                const actionMeta = getActionMeta(r.action);

                return (
                  <button
                    key={r.case_id || idx}
                    type="button"
                    onClick={() => {
                      setIsPlaying(false);
                      setCurrentIndex(globalIndex);
                    }}
                    className={`stream-case-card ${isSelected ? 'is-active' : ''}`}
                    style={{
                      border: isSelected ? `2px solid ${actionMeta.color}` : `1px solid var(--border-default)`,
                      boxShadow: isSelected ? `0 0 20px ${actionMeta.color}44, 0 8px 24px rgba(0, 0, 0, 0.4)` : 'none',
                      padding: '12px 14px',
                      minWidth: '155px',
                    }}
                    aria-label={`Jump to replay case ${r.row_id || globalIndex + 1}`}
                  >
                    {/* Top Row: Case ID & Radar Pulse Beacon */}
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <span style={{ fontFamily: 'var(--font-mono)', fontSize: '14px', fontWeight: 800, color: 'var(--text-primary)' }}>
                        #{r.row_id || globalIndex + 1}
                      </span>
                      {isSelected ? (
                        <div style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
                          <span className="stream-beacon-pulse" style={{ backgroundColor: actionMeta.color, color: actionMeta.color }} />
                          <span style={{ fontSize: '11px', fontWeight: 800, color: actionMeta.colorBright, letterSpacing: '0.04em' }}>
                            ACTIVE
                          </span>
                        </div>
                      ) : (
                        <span style={{ width: '8px', height: '8px', borderRadius: '50%', backgroundColor: actionMeta.color, opacity: 0.8 }} />
                      )}
                    </div>

                    {/* Amount & Product */}
                    <div style={{ display: 'flex', alignItems: 'baseline', justifyContent: 'space-between', marginTop: '4px' }}>
                      <span style={{ fontFamily: 'var(--font-mono)', fontSize: '18px', fontWeight: 800, color: 'var(--text-primary)' }}>
                        ${r.amount.toFixed(2)}
                      </span>
                      <span style={{ fontSize: '12.5px', color: 'var(--text-secondary)', fontFamily: 'var(--font-mono)', fontWeight: 700 }}>
                        {r.card4.toUpperCase()}
                      </span>
                    </div>

                    {/* Telemetry Micro-Bars */}
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '5px', marginTop: '4px' }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '12px', fontFamily: 'var(--font-mono)' }}>
                        <span style={{ color: 'var(--text-secondary)', fontWeight: 600 }}>p: {r.p.toFixed(3)}</span>
                        <span style={{ color: 'var(--color-epistemic-defer-bright)', fontWeight: 700 }}>u₂: {r.u.toFixed(2)}</span>
                      </div>
                      <div style={{ width: '100%', height: '5px', background: 'var(--bg-surface-subdued)', borderRadius: '3px', overflow: 'hidden' }}>
                        <div
                          style={{
                            width: `${Math.min(100, (r.p / 0.12) * 100)}%`,
                            height: '100%',
                            backgroundColor: actionMeta.color,
                          }}
                        />
                      </div>
                    </div>

                    {/* Bottom Action Badge */}
                    <div style={{ marginTop: '5px' }}>
                      <span
                        style={{
                          display: 'inline-flex',
                          alignItems: 'center',
                          gap: '6px',
                          padding: '4px 10px',
                          borderRadius: 'var(--radius-xs)',
                          fontFamily: 'var(--font-mono)',
                          fontSize: '11.5px',
                          fontWeight: 800,
                          color: actionMeta.colorBright,
                          backgroundColor: actionMeta.bg,
                          border: `1px solid ${actionMeta.border}`,
                          width: '100%',
                          justifyContent: 'center',
                          textTransform: 'uppercase',
                        }}
                      >
                        {actionMeta.icon}
                        <span>{actionMeta.shortLabel}</span>
                      </span>
                    </div>
                  </button>
                );
              })}
            </div>
          </div>

        </>
      )}
    </div>
  );
};
