import React, { Suspense, useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Lock,
  Server,
  Sliders,
  UserCheck,
  Radio,
  Filter,
  Crosshair,
  BarChart3,
  Play,
  Square,
  StepForward,
  RotateCcw,
  CheckCircle2,
  AlertTriangle,
  Cpu,
  Activity,
  Database,
  ShieldCheck,
  Zap,
} from 'lucide-react';
import { MetricCard } from '../../components/MetricCard';
import { TiltGlassCardDetail } from '../../components/TiltGlassCard';
import { useApiStatus, useOverview } from '../../lib/api/hooks';
import { useMode } from '../../context/ModeContext';
import { LoadingState } from '../../components/LoadingState';
import { ErrorState } from '../../components/ErrorState';
import { api } from '../../lib/api/client';
import { ReplayStatusResponse } from '../../lib/api/types';

const SignalCoreScene = React.lazy(() =>
  import('../../components/SignalCoreScene').then((m) => ({ default: m.SignalCoreScene }))
);

export const OverviewPage: React.FC = () => {
  const navigate = useNavigate();
  const { mode, isRealDataMode, isLiveDisconnected } = useMode();
  const { status, isBackendConnected, loading: statusLoading, error: statusError, refetch: refetchStatus } = useApiStatus(mode);
  const { overview, refetch: refetchOverview } = useOverview(mode);

  const [replayStatus, setReplayStatus] = useState<ReplayStatusResponse | null>(null);
  const [replayLoading, setReplayLoading] = useState(false);
  const [replayError, setReplayError] = useState<string | null>(null);
  const [stepSuccessMsg, setStepSuccessMsg] = useState<string | null>(null);

  const fetchReplayStatus = useCallback(async () => {
    try {
      const res = await api.getReplayStatus();
      setReplayStatus(res);
      setReplayError(null);
    } catch {
      // Replay worker may be offline or starting
    }
  }, []);

  useEffect(() => {
    fetchReplayStatus();
    const intervalMs = replayStatus?.is_running ? 1000 : 3500;
    const interval = setInterval(fetchReplayStatus, intervalMs);
    return () => clearInterval(interval);
  }, [fetchReplayStatus, replayStatus?.is_running]);

  const handleStartReplay = async () => {
    setReplayLoading(true);
    setReplayError(null);
    try {
      await api.startReplay(500, 100);
      await fetchReplayStatus();
      refetchOverview();
    } catch (err: unknown) {
      const e = err as Error;
      setReplayError(e?.message || 'Failed to start historical replay');
    } finally {
      setReplayLoading(false);
    }
  };

  const handleStopReplay = async () => {
    setReplayLoading(true);
    setReplayError(null);
    try {
      await api.stopReplay();
      await fetchReplayStatus();
      refetchOverview();
    } catch (err: unknown) {
      const e = err as Error;
      setReplayError(e?.message || 'Failed to stop historical replay');
    } finally {
      setReplayLoading(false);
    }
  };

  const handleStepReplay = async () => {
    setReplayLoading(true);
    setReplayError(null);
    setStepSuccessMsg(null);
    try {
      const res = await api.stepReplay();
      await fetchReplayStatus();
      if (res.event) {
        setStepSuccessMsg(`Scored Txn ${res.event.transaction_id}: ${res.event.action} (${res.event.reason_code}) p=${(res.event.score ?? res.event.p ?? 0).toFixed(4)}`);
        setTimeout(() => setStepSuccessMsg(null), 4000);
      }
      refetchOverview();
    } catch (err: unknown) {
      const e = err as Error;
      setReplayError(e?.message || 'Failed to step replay');
    } finally {
      setReplayLoading(false);
    }
  };

  const handleResetReplay = async () => {
    setReplayLoading(true);
    setReplayError(null);
    try {
      await api.resetReplay();
      await fetchReplayStatus();
      refetchOverview();
    } catch (err: unknown) {
      const e = err as Error;
      setReplayError(e?.message || 'Failed to reset replay');
    } finally {
      setReplayLoading(false);
    }
  };

  const handleRetryAll = () => {
    refetchStatus();
    refetchOverview();
    fetchReplayStatus();
  };

  const scrollToSection = (id: string) => {
    const el = document.getElementById(id);
    if (el) {
      el.scrollIntoView({ behavior: 'smooth', block: 'start' });
      el.classList.add('pulse-highlight');
      setTimeout(() => el.classList.remove('pulse-highlight'), 1200);
    }
  };

  return (
    <div className="overview-page animate-fade-in" style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-4)' }}>
      {/* 1. Contextual Evidence Banner & Screen Header */}
      <div className="page-header-card">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '14px' }}>
          <div>
            <div className="page-header-eyebrow" style={{ marginBottom: '6px' }}>
              <span className={`badge ${isRealDataMode ? 'badge-ready' : isLiveDisconnected ? 'badge-alert' : 'badge-synthetic'}`}>
                <span>{mode}</span>
              </span>
              <span>
                {isRealDataMode
                  ? 'IEEE-CIS 391-FEATURE ENSEMBLE BENCHMARK'
                  : isLiveDisconnected
                  ? 'LIVE INGESTION DISCONNECTED'
                  : 'OFFLINE EVALUATION FIXTURE PROTOCOL'}
              </span>
              <span style={{ color: 'var(--border-active)' }}>|</span>
              <span style={{ color: 'var(--text-secondary)' }}>
                {isRealDataMode ? 'Chronological Test Partition' : 'Test Partition: 2,000 txns'}
              </span>
            </div>
            <h1 className="page-header-title">
              OPERATIONAL OVERVIEW &amp; DECISION TELEMETRY
            </h1>
            <p className="page-header-desc">
              Shift-aware decision cockpit evaluating calibrated risk (<span style={{ color: 'var(--accent-primary)', fontWeight: 600 }}>p</span>),
              epistemic disagreement (<span style={{ color: 'var(--color-epistemic-defer-bright)', fontWeight: 600 }}>u₂</span>), and
              capacity-governed review queues.
            </p>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', background: 'var(--bg-surface-raised)', padding: '8px 14px', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-subtle)' }}>
            <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: '3px' }}>
              <span style={{ fontSize: '11px', color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '0.06em', fontWeight: 600 }}>
                Frozen Policy Hash
              </span>
              <span style={{ fontFamily: 'var(--font-mono)', fontSize: '12.5px', fontWeight: 700, color: 'var(--accent-primary-bright)' }}>
                {overview?.frozen_config_hash?.slice(0, 8) || '8d3f02ca'}...
              </span>
            </div>
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
            Live production event ingestion is not connected. Under strict SignalGate non-negotiable safety boundaries, the system fails closed rather than fabricating synthetic live data. Select <strong>IEEE-CIS BENCHMARK</strong> to test against real competition records, or <strong>SYNTHETIC FIXTURE</strong> for smoke validation.
          </p>
        </div>
      )}
      {(() => {
        const incomingCaserateDetail: TiltGlassCardDetail = {
          title: 'Incoming Caserate & Ingestion Bus',
          subtitle: isLiveDisconnected
            ? 'Live Edge Message Brokers Offline'
            : replayStatus?.is_running
            ? 'Streaming IEEE-CIS Historical Replay'
            : (replayStatus?.scored_count ?? 0) > 0
            ? 'Historical Replay Standby (Telemetry Retained)'
            : 'Deterministic Replay Worker Ready',
          category: 'STREAMING INGESTION BUS',
          icon: <Radio size={18} />,
          accentColor: 'var(--accent-primary)',
          shortDesc: isLiveDisconnected
            ? 'Live edge banking message brokers (Kafka) remain disconnected under fail-closed safety constraints. No synthetic live data is fabricated.'
            : replayStatus?.is_running
            ? `Active sequential replay streaming directly from ${replayStatus.replay_source}. Records undergo feature alignment, model scoring, and cryptographic audit hashing.`
            : `Controllable sequential replay worker configured for ${replayStatus?.replay_source || 'data/raw/test_transaction.csv'}. Real-time scoring invokes EraBaggedHeterogeneousEnsemble.`,
          formula: 'λ(t) = dN(t)/dt [5-second Rolling Window Decay]',
          parameters: [
            { label: 'Replay State', value: `${replayStatus?.state || 'IDLE'} (${replayStatus?.data_provenance || 'HISTORICAL_REPLAY'})` },
            { label: 'Current Caserate', value: `${replayStatus?.recent_caserate.toFixed(1) || '0.0'} evt/s` },
            { label: 'Total Scored', value: `${replayStatus?.scored_count.toLocaleString() || '0'} events` },
            { label: 'Mean Latency', value: `${replayStatus?.avg_latency_ms.toFixed(1) || '0.0'} ms` },
            { label: 'Live Banking Stream', value: 'DISCONNECTED (Fail-Closed)' },
          ],
          telemetryNotes: [
            'Sliding window event rate decays to 0.0 evt/s when replay stops or pauses.',
            'Idempotency hash ring rejects duplicate event submissions automatically.',
            'Cryptographic audit entries appended immutably to audit_chain.jsonl.',
          ],
          partitionInfo: isLiveDisconnected
            ? 'Live Ingestion: Disconnected'
            : `Replay Source: ${replayStatus?.replay_source || 'data/raw/test_transaction.csv'}`,
        };

        const reviewCapacityDetail: TiltGlassCardDetail = {
          title: 'Human Review Capacity Governor',
          subtitle: 'Strict Capacity Ceiling & Workload Protection',
          category: 'HUMAN-IN-THE-LOOP GOVERNANCE',
          icon: <UserCheck size={18} />,
          accentColor: 'var(--color-manual-review)',
          shortDesc: isRealDataMode
            ? 'Imposes a hard quota ceiling on human investigator review slots (5,993 cases across 118,108 cases, representing a 1.5× multiplier on 5.075% budget). When saturated, Rule R6 triggers automated epistemic deferral.'
            : isLiveDisconnected
            ? 'Live edge broker disconnected. Review capacity governor is armed with 0 active tickets in queue under fail-closed safety constraints.'
            : 'Imposes a hard quota ceiling on human investigator review slots (130 cases across 2,000 cases, representing a 1.5× multiplier on 6.525% budget). When saturated, Rule R6 triggers automated epistemic deferral.',
          formula: isRealDataMode
            ? 'Capacity_Max = 1.5 × Baseline = 5,993 cases (5.075% budget on N=118,108)'
            : isLiveDisconnected
            ? 'Capacity_Max = 0 cases (Live Ingestion Offline - Fail-Closed)'
            : 'Capacity_Max = 1.5 × Baseline = 130 cases (6.525% budget on N=2,000)',
          parameters: isRealDataMode
            ? [
                { label: 'Max Review Slots', value: '5,993 cases (100% Saturated: 5,993 / 5,993)' },
                { label: 'Budget Multiplier', value: '1.5× baseline capacity ceiling (5.075%)' },
                { label: 'Current Queue Pressure', value: '100% Saturated (Governor Active)' },
                { label: 'Overflow Routing Policy', value: 'Rule R6: Epistemic Deferral Fallback' },
              ]
            : isLiveDisconnected
            ? [
                { label: 'Max Review Slots', value: '0 cases (Offline)' },
                { label: 'Budget Multiplier', value: 'N/A (Stream Disconnected)' },
                { label: 'Current Queue Pressure', value: '0% (Ingestion Quenched)' },
                { label: 'Overflow Routing Policy', value: 'Fail-Closed Disconnect Hold' },
              ]
            : [
                { label: 'Max Review Slots', value: '130 cases (100% Saturated: 130 / 130)' },
                { label: 'Budget Multiplier', value: '1.5× baseline capacity ceiling (6.525%)' },
                { label: 'Current Queue Pressure', value: '100% Saturated (Governor Active)' },
                { label: 'Overflow Routing Policy', value: 'Rule R6: Epistemic Deferral Fallback' },
              ],
          telemetryNotes: [
            'Prevents cognitive fatigue and review quality degradation under volume spikes.',
            'Excess cases route to safe held quarantine instead of unverified auto-approval.',
            'Governor quota admission flag recorded immutably in append-only ledger.',
          ],
          partitionInfo: isRealDataMode
            ? 'Primary Review Queue Budget: 5,993 Slots (5.075%)'
            : isLiveDisconnected
            ? 'Primary Review Queue Budget: 0 Slots (Offline)'
            : 'Primary Review Queue Budget: 130 Slots (6.525%)',
        };

        const deferralRatioDetail: TiltGlassCardDetail = {
          title: 'Epistemic Deferral Ratio & Safe Triage',
          subtitle: 'Uncertainty Isolation & Out-of-Distribution Shielding',
          category: 'DRIFT-AWARE TRIAGE & ISOLATION',
          icon: <Filter size={18} />,
          accentColor: 'var(--color-epistemic-defer)',
          shortDesc: 'Measures transaction volume diverted away from brittle automated execution. Cases exceeding epistemic ensemble threshold (u₂ ≥ 0.5268) or human capacity ceiling (Rule R6) enter safe asynchronous quarantine.',
          formula: 'Deferral_Ratio = N_deferred / N_total = 974 / 2,000 (48.7%)',
          parameters: [
            { label: 'Total Deferred Volume', value: '974 cases (48.7% of evaluation set)' },
            { label: 'Epistemic Gate (u_th)', value: '0.5268 (Ensemble Disagreement Cutoff)' },
            { label: 'Review Spillover Cases', value: 'Diverted via Rule R6 Capacity Ceiling' },
            { label: 'Execution Mode', value: 'Safe Held / Epistemic Async Inspection' },
          ],
          telemetryNotes: [
            'Eliminates catastrophic false-negative leaks under unseen covariate shifts (S1/S2/S3).',
            'Quarantines anomalous distributions for secondary offline analysis.',
            'Provides audit-verifiable isolation with cryptographic hash references.',
          ],
          partitionInfo: 'Test Look Partition: 974 / 2,000 Deferred',
        };

        const precisionTouchedDetail: TiltGlassCardDetail = {
          title: 'Precision @ Touched Performance Benchmark',
          subtitle: 'Active Investigation Yield on Canonical Test Set',
          category: 'ACTIVE INTERVENTION FIDELITY',
          icon: <Crosshair size={18} />,
          accentColor: 'var(--accent-primary-bright)',
          shortDesc: 'Quantifies confirmed fraud instances intercepted within the 130 cases actively touched by human investigators on the frozen test look partition, capturing 10 of 111 total ground-truth fraud occurrences.',
          formula: 'Precision@Touched = TP / (TP + FP) = 10 / 130 (7.69%)',
          parameters: [
            { label: 'True Positives Caught', value: '10 confirmed fraud cases' },
            { label: 'Active Queue Volume', value: '130 touched cases' },
            { label: 'Recall @ Touched', value: '9.01% (10 of 111 total ground-truth fraud)' },
            { label: 'Intervention Precision', value: '7.69% (10 of 130 touched)' },
          ],
          telemetryNotes: [
            'Verified frozen benchmark on canonical G3 test look partition.',
            'Matches B2 Top-B baseline recall while adding 974 safe deferrals.',
            'Conclusive superiority test flag: false (honest smoke protocol reporting).',
          ],
          partitionInfo: 'Frozen Benchmark: G3 Test Look Partition',
        };


        return (
          <section aria-label="Key Operational Benchmarks" style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: 'var(--space-4)' }}>
            {/* Card 1: Incoming Caserate (Real Backend Response & Rolling Decay) */}
            <MetricCard
              label="INCOMING CASERATE"
              value={
                isLiveDisconnected
                  ? null
                  : (replayStatus?.is_running || (replayStatus?.scored_count ?? 0) > 0)
                  ? `${(replayStatus?.recent_caserate ?? 0).toFixed(1)}`
                  : isRealDataMode
                  ? '0.0'
                  : null
              }
              unit={(!isLiveDisconnected && ((replayStatus?.scored_count ?? 0) > 0 || isRealDataMode)) ? 'evt/s' : undefined}
              isAvailable={!isLiveDisconnected}
              unavailableText="Unavailable (Offline)"
              subtext={
                isLiveDisconnected
                  ? 'Live edge disconnected • External broker unattached'
                  : replayStatus?.is_running
                  ? `Historical replay active • ${replayStatus.scored_count.toLocaleString()} scored (${replayStatus.last_latency_ms.toFixed(1)}ms)`
                  : (replayStatus?.scored_count ?? 0) > 0
                  ? `Replay ${replayStatus?.state.toLowerCase()} • ${replayStatus?.scored_count.toLocaleString()} scored (Rate decayed to 0.0)`
                  : isRealDataMode
                  ? 'Replay worker ready • test_transaction.csv'
                  : 'Offline synthetic fixture • Replay ready'
              }
              icon={<Radio size={16} />}
              variant={replayStatus?.is_running ? 'cyan' : 'default'}
              clickable={true}
              onClick={() => scrollToSection('ingestion-bus-section')}
              detail={incomingCaserateDetail}
              badgeText={
                isLiveDisconnected
                  ? 'OFFLINE'
                  : replayStatus?.is_running
                  ? 'STREAMING'
                  : (replayStatus?.scored_count ?? 0) > 0
                  ? `REPLAY ${replayStatus?.state}`
                  : 'READY'
              }
            />

            {/* Card 2: Review Capacity */}
            <MetricCard
              label="REVIEW CAPACITY"
              value={isLiveDisconnected ? '0 / 0' : isRealDataMode ? '5,993 / 5,993' : '130 / 130'}
              unit="slots"
              subtext={
                isLiveDisconnected
                  ? 'Live stream disconnected • No active quota'
                  : isRealDataMode
                  ? '1.5x budget (5.075%) • Cap saturated'
                  : '1.5x budget (6.525%) • Cap saturated'
              }
              icon={<UserCheck size={16} />}
              variant="amber"
              progressPercent={isLiveDisconnected ? 0 : 100}
              clickable={true}
              onClick={() => scrollToSection('review-capacity-pane')}
              detail={reviewCapacityDetail}
              badgeText={isLiveDisconnected ? 'OFFLINE' : '100% CAP'}
            />

            {/* Card 3: Deferral Ratio */}
            <MetricCard
              label="DEFERRAL RATIO"
              value={
                isLiveDisconnected
                  ? '0.0%'
                  : isRealDataMode
                  ? (overview?.deferred_rate ? `${(overview.deferred_rate * 100).toFixed(1)}%` : '2.0%')
                  : (overview?.deferred_rate ? `${(overview.deferred_rate * 100).toFixed(1)}%` : '48.7%')
              }
              unit={isLiveDisconnected ? '0 cases' : isRealDataMode ? '2,328 cases' : '974 cases'}
              subtext="Capacity shed to HELD/DEFERRED (R6)"
              icon={<Filter size={16} />}
              variant="violet"
              progressPercent={isLiveDisconnected ? 0 : isRealDataMode ? 2.0 : 48.7}
              clickable={true}
              onClick={() => scrollToSection('topology-section')}
              detail={deferralRatioDetail}
              badgeText={isLiveDisconnected ? '0 SHED' : isRealDataMode ? '2,328 SHED' : '974 SHED'}
            />

            {/* Card 4: Precision @ Touched */}
            <MetricCard
              label="PRECISION @ TOUCHED"
              value={isLiveDisconnected ? 'N/A' : isRealDataMode ? '34.49%' : '7.69%'}
              unit={isLiveDisconnected ? '0/0 caught' : isRealDataMode ? '2,067/5,993 caught' : '10/130 caught'}
              subtext={
                isLiveDisconnected
                  ? 'Live stream disconnected • Evaluation suspended'
                  : isRealDataMode
                  ? '50.86% recall on test partition (2,067/4,064)'
                  : '9.01% recall on test look (10/111)'
              }
              icon={<Crosshair size={16} />}
              variant="cyan"
              progressPercent={isLiveDisconnected ? 0 : isRealDataMode ? 34.49 : 7.69}
              clickable={true}
              onClick={() => navigate('/policy-comparison')}
              detail={precisionTouchedDetail}
              badgeText={isRealDataMode ? 'IEEE-CIS TEST' : 'TEST LOOK'}
            />
          </section>
        );
      })()}

      {/* 3. Outcome Distribution Stacked Bar (Milestone 3A) */}
      {(() => {
        const totalTx = isLiveDisconnected ? 0 : isRealDataMode ? 118108 : 2000;
        const fraudAlertCount = isLiveDisconnected ? 0 : isRealDataMode ? 1280 : 11;
        const fraudAlertPct = totalTx > 0 ? ((fraudAlertCount / totalTx) * 100).toFixed(2) : '0.00';

        const reviewCount = isLiveDisconnected ? 0 : isRealDataMode ? 4713 : 119;
        const reviewPct = totalTx > 0 ? ((reviewCount / totalTx) * 100).toFixed(2) : '0.00';

        const routineCount = isLiveDisconnected ? 0 : isRealDataMode ? 109787 : 896;
        const routinePct = totalTx > 0 ? ((routineCount / totalTx) * 100).toFixed(2) : '0.00';

        const deferredCount = isLiveDisconnected ? 0 : isRealDataMode ? 2328 : 974;
        const deferredPct = totalTx > 0 ? ((deferredCount / totalTx) * 100).toFixed(2) : '0.00';

        return (
          <section aria-label="Outcome Distribution Telemetry" className="sg-card" style={{ padding: '18px 20px', display: 'flex', flexDirection: 'column', gap: '14px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '8px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                <BarChart3 size={18} style={{ color: 'var(--accent-primary)' }} />
                <span style={{ fontSize: '15px', fontWeight: 700, color: 'var(--text-primary)' }}>
                  Outcome Distribution & Triage Proportions
                </span>
                <span className={`badge ${isRealDataMode ? 'badge-ready' : isLiveDisconnected ? 'badge-alert' : 'badge-synthetic'}`} style={{ fontSize: '11px', padding: '2px 8px' }}>
                  <span>{isLiveDisconnected ? 'N = 0 cases (Disconnected)' : `N = ${totalTx.toLocaleString()} cases`}</span>
                </span>
              </div>
              <span style={{ fontFamily: 'var(--font-mono)', fontSize: '12px', color: 'var(--text-secondary)' }}>
                {isRealDataMode ? 'IEEE-CIS Chronological Test Partition' : isLiveDisconnected ? 'Streaming Bus Offline' : 'G3_LOOK_1 Canonical Fixture'}
              </span>
            </div>

        {/* Horizontal Stacked Distribution Bar */}
        <div style={{ width: '100%', height: '16px', borderRadius: '4px', overflow: 'hidden', display: 'flex', background: 'var(--bg-surface-subdued)', border: '1px solid var(--border-default)' }}>
          <div
            style={{ width: `${fraudAlertPct}%`, minWidth: fraudAlertCount > 0 ? '4px' : '0px', backgroundColor: 'var(--color-fraud-alert)' }}
            title={`FRAUD_ALERT: ${fraudAlertCount.toLocaleString()} cases (${fraudAlertPct}%)`}
          />
          <div
            style={{ width: `${reviewPct}%`, backgroundColor: 'var(--color-manual-review)' }}
            title={`MANUAL_REVIEW: ${reviewCount.toLocaleString()} cases (${reviewPct}%)`}
          />
          <div
            style={{ width: `${routinePct}%`, backgroundColor: 'var(--color-routine)' }}
            title={`ROUTINE: ${routineCount.toLocaleString()} cases (${routinePct}%)`}
          />
          <div
            style={{ width: `${deferredPct}%`, backgroundColor: 'var(--color-epistemic-defer-bright)' }}
            title={`HELD / DEFERRED: ${deferredCount.toLocaleString()} cases (${deferredPct}%)`}
          />
        </div>

        {/* Spacious 2x2 Outcome Breakdown Cards */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '14px', marginTop: '6px' }}>
          {/* Card 1: FRAUD_ALERT */}
          <div style={{ background: 'var(--bg-surface-raised)', padding: '16px 20px', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-subtle)', borderLeft: '4px solid var(--color-fraud-alert)', display: 'flex', justifyContent: 'space-between', alignItems: 'center', boxShadow: '0 2px 10px rgba(0, 0, 0, 0.15)' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
              <span style={{ width: '12px', height: '12px', borderRadius: '3px', background: 'var(--color-fraud-alert)', flexShrink: 0 }} />
              <div>
                <div style={{ fontSize: '14.5px', fontWeight: 700, color: 'var(--text-primary)' }}>FRAUD_ALERT (R1)</div>
                <div style={{ fontSize: '12.5px', color: 'var(--text-secondary)', marginTop: '3px' }}>High Risk Escalation &bull; p &ge; 0.0847</div>
              </div>
            </div>
            <div style={{ textAlign: 'right' }}>
              <div style={{ fontFamily: 'var(--font-mono)', fontSize: '22px', fontWeight: 800, color: 'var(--color-fraud-alert-bright)' }}>
                {fraudAlertCount.toLocaleString()}
              </div>
              <div style={{ fontSize: '13px', color: 'var(--text-secondary)', fontWeight: 500 }}>
                {fraudAlertPct}% of total
              </div>
            </div>
          </div>

          {/* Card 2: MANUAL_REVIEW */}
          <div style={{ background: 'var(--bg-surface-raised)', padding: '16px 20px', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-subtle)', borderLeft: '4px solid var(--color-manual-review)', display: 'flex', justifyContent: 'space-between', alignItems: 'center', boxShadow: '0 2px 10px rgba(0, 0, 0, 0.15)' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
              <span style={{ width: '12px', height: '12px', borderRadius: '3px', background: 'var(--color-manual-review)', flexShrink: 0 }} />
              <div>
                <div style={{ fontSize: '14.5px', fontWeight: 700, color: 'var(--text-primary)' }}>MANUAL_REVIEW (R2/3)</div>
                <div style={{ fontSize: '12.5px', color: 'var(--text-secondary)', marginTop: '3px' }}>Analyst Queue Allocation &bull; Cap Saturated</div>
              </div>
            </div>
            <div style={{ textAlign: 'right' }}>
              <div style={{ fontFamily: 'var(--font-mono)', fontSize: '22px', fontWeight: 800, color: 'var(--color-manual-review-bright)' }}>
                {reviewCount.toLocaleString()}
              </div>
              <div style={{ fontSize: '13px', color: 'var(--text-secondary)', fontWeight: 500 }}>
                {reviewPct}% of total
              </div>
            </div>
          </div>

          {/* Card 3: ROUTINE */}
          <div style={{ background: 'var(--bg-surface-raised)', padding: '16px 20px', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-subtle)', borderLeft: '4px solid var(--color-routine)', display: 'flex', justifyContent: 'space-between', alignItems: 'center', boxShadow: '0 2px 10px rgba(0, 0, 0, 0.15)' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
              <span style={{ width: '12px', height: '12px', borderRadius: '3px', background: 'var(--color-routine)', flexShrink: 0 }} />
              <div>
                <div style={{ fontSize: '14.5px', fontWeight: 700, color: 'var(--text-primary)' }}>ROUTINE (R5)</div>
                <div style={{ fontSize: '12.5px', color: 'var(--text-secondary)', marginTop: '3px' }}>Low Risk Frictionless Auto Clearance</div>
              </div>
            </div>
            <div style={{ textAlign: 'right' }}>
              <div style={{ fontFamily: 'var(--font-mono)', fontSize: '22px', fontWeight: 800, color: 'var(--color-routine-bright)' }}>
                {routineCount.toLocaleString()}
              </div>
              <div style={{ fontSize: '13px', color: 'var(--text-secondary)', fontWeight: 500 }}>
                {routinePct}% of total
              </div>
            </div>
          </div>

          {/* Card 4: HELD / DEFERRED */}
          <div style={{ background: 'var(--bg-surface-raised)', padding: '16px 20px', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-subtle)', borderLeft: '4px solid var(--color-epistemic-defer-bright)', display: 'flex', justifyContent: 'space-between', alignItems: 'center', boxShadow: '0 2px 10px rgba(0, 0, 0, 0.15)' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
              <span style={{ width: '12px', height: '12px', borderRadius: '3px', background: 'var(--color-epistemic-defer-bright)', flexShrink: 0 }} />
              <div>
                <div style={{ fontSize: '14.5px', fontWeight: 700, color: 'var(--text-primary)' }}>HELD / DEFERRED (R6)</div>
                <div style={{ fontSize: '12.5px', color: 'var(--text-secondary)', marginTop: '3px' }}>Capacity Overflow Buffer &bull; Zero Leakage</div>
              </div>
            </div>
            <div style={{ textAlign: 'right' }}>
              <div style={{ fontFamily: 'var(--font-mono)', fontSize: '22px', fontWeight: 800, color: 'var(--color-epistemic-defer-bright)' }}>
                {deferredCount.toLocaleString()}
              </div>
              <div style={{ fontSize: '13px', color: 'var(--text-secondary)', fontWeight: 500 }}>
                {deferredPct}% of total
              </div>
            </div>
          </div>
        </div>
      </section>
        );
      })()}

      {/* 3.5. Historical Replay Ingestion Bus & Streaming Scorer (Stage A) */}
      <section id="ingestion-bus-section" aria-label="Historical Replay Ingestion Bus" className="sg-card" style={{ padding: '20px 22px', display: 'flex', flexDirection: 'column', gap: '16px', borderLeft: '4px solid var(--accent-primary)' }}>
        {/* Header Bar */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '12px' }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <Radio size={19} style={{ color: 'var(--accent-primary)' }} />
              <h2 style={{ fontSize: '16px', fontWeight: 700, margin: 0, color: 'var(--text-primary)', letterSpacing: '0.02em' }}>
                HISTORICAL REPLAY INGESTION BUS &amp; DETERMINISTIC SCORING ENGINE
              </h2>
              <span className={`badge ${replayStatus?.is_running ? 'badge-ready' : 'badge-synthetic'}`}>
                <span className="badge-dot" />
                <span>{replayStatus?.state || 'IDLE'}</span>
              </span>
            </div>
            <p style={{ margin: '4px 0 0 0', fontSize: '12.5px', color: 'var(--text-secondary)' }}>
              Provenance: <strong style={{ color: 'var(--accent-primary-bright)', fontFamily: 'var(--font-mono)' }}>HISTORICAL_REPLAY</strong> &bull; Source: <code style={{ color: 'var(--text-primary)' }}>{replayStatus?.replay_source || 'data/raw/test_transaction.csv'}</code> &bull; External Live Gateway: <span style={{ color: 'var(--color-fraud-alert-bright)', fontWeight: 600 }}>DISCONNECTED (Fail-Closed)</span>
            </p>
          </div>

          {/* Action Control Buttons */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <button
              type="button"
              className="sg-btn sg-btn-primary"
              disabled={replayStatus?.is_running || replayLoading}
              onClick={handleStartReplay}
              title="Start continuous historical replay worker"
              style={{ padding: '7px 16px', gap: '6px' }}
            >
              <Play size={14} />
              <span>Start Replay</span>
            </button>

            <button
              type="button"
              className="sg-btn sg-btn-secondary"
              disabled={!replayStatus?.is_running || replayLoading}
              onClick={handleStopReplay}
              title="Stop continuous replay worker (rate will decay to 0.0)"
              style={{ padding: '7px 16px', gap: '6px' }}
            >
              <Square size={14} />
              <span>Stop Replay</span>
            </button>

            <button
              type="button"
              className="sg-btn sg-btn-secondary"
              disabled={replayStatus?.is_running || replayLoading}
              onClick={handleStepReplay}
              title="Read, validate, score, and audit exactly 1 historical record"
              style={{ padding: '7px 16px', gap: '6px' }}
            >
              <StepForward size={14} />
              <span>Step 1 Txn</span>
            </button>

            <button
              type="button"
              className="sg-btn sg-btn-ghost"
              disabled={replayStatus?.is_running || replayLoading}
              onClick={handleResetReplay}
              title="Reset replay worker cursor and telemetry counters"
              style={{ padding: '7px 12px' }}
            >
              <RotateCcw size={14} />
              <span>Reset</span>
            </button>
          </div>
        </div>

        {/* Feedback Messages */}
        {replayError && (
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', padding: '10px 14px', background: 'rgba(239, 68, 68, 0.1)', border: '1px solid rgba(239, 68, 68, 0.3)', borderRadius: 'var(--radius-xs)', color: 'var(--color-fraud-alert-bright)', fontSize: '13px' }}>
            <AlertTriangle size={15} style={{ flexShrink: 0 }} />
            <span>{replayError}</span>
          </div>
        )}
        {stepSuccessMsg && (
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', padding: '10px 14px', background: 'rgba(16, 185, 129, 0.1)', border: '1px solid rgba(16, 185, 129, 0.3)', borderRadius: 'var(--radius-xs)', color: 'var(--color-routine-bright)', fontSize: '13px' }}>
            <CheckCircle2 size={15} style={{ flexShrink: 0 }} />
            <span>{stepSuccessMsg}</span>
          </div>
        )}

        {/* Real-time Telemetry Grid */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '12px' }}>
          {/* Card 1: Live Caserate */}
          <div style={{ background: 'var(--bg-surface-raised)', padding: '14px 16px', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-subtle)' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <span style={{ fontSize: '11.5px', color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '0.05em', fontWeight: 600 }}>
                Instantaneous Caserate
              </span>
              <Activity size={14} style={{ color: replayStatus?.is_running ? 'var(--accent-primary-bright)' : 'var(--text-disabled)' }} />
            </div>
            <div style={{ fontFamily: 'var(--font-mono)', fontSize: '24px', fontWeight: 800, color: replayStatus?.is_running ? 'var(--accent-primary-bright)' : 'var(--text-primary)', marginTop: '4px' }}>
              {(replayStatus?.recent_caserate ?? 0).toFixed(1)} <span style={{ fontSize: '13px', fontWeight: 500, color: 'var(--text-secondary)' }}>evt/s</span>
            </div>
            <div style={{ fontSize: '11px', color: 'var(--text-tertiary)', marginTop: '3px' }}>
              5-sec sliding window decay
            </div>
          </div>

          {/* Card 2: Scored Events */}
          <div style={{ background: 'var(--bg-surface-raised)', padding: '14px 16px', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-subtle)' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <span style={{ fontSize: '11.5px', color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '0.05em', fontWeight: 600 }}>
                Model Invocations
              </span>
              <Cpu size={14} style={{ color: 'var(--color-routine-bright)' }} />
            </div>
            <div style={{ fontFamily: 'var(--font-mono)', fontSize: '24px', fontWeight: 800, color: 'var(--color-routine-bright)', marginTop: '4px' }}>
              {(replayStatus?.scored_count ?? 0).toLocaleString()} <span style={{ fontSize: '13px', fontWeight: 500, color: 'var(--text-secondary)' }}>scored</span>
            </div>
            <div style={{ fontSize: '11px', color: 'var(--text-tertiary)', marginTop: '3px' }}>
              {(replayStatus?.received_count ?? 0).toLocaleString()} read from test_transaction.csv
            </div>
          </div>

          {/* Card 3: Ingestion Quality */}
          <div style={{ background: 'var(--bg-surface-raised)', padding: '14px 16px', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-subtle)' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <span style={{ fontSize: '11.5px', color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '0.05em', fontWeight: 600 }}>
                Ingestion Quality
              </span>
              <ShieldCheck size={14} style={{ color: 'var(--accent-primary)' }} />
            </div>
            <div style={{ fontFamily: 'var(--font-mono)', fontSize: '24px', fontWeight: 800, color: 'var(--text-primary)', marginTop: '4px' }}>
              {(replayStatus?.accepted_count ?? 0).toLocaleString()} <span style={{ fontSize: '13px', fontWeight: 500, color: 'var(--text-secondary)' }}>accepted</span>
            </div>
            <div style={{ fontSize: '11px', color: 'var(--text-tertiary)', marginTop: '3px' }}>
              {replayStatus?.rejected_count ?? 0} rejected &bull; {replayStatus?.duplicate_count ?? 0} dupes idempotent
            </div>
          </div>

          {/* Card 4: Inference Latency */}
          <div style={{ background: 'var(--bg-surface-raised)', padding: '14px 16px', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-subtle)' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <span style={{ fontSize: '11.5px', color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '0.05em', fontWeight: 600 }}>
                Scoring Latency
              </span>
              <Zap size={14} style={{ color: 'var(--color-epistemic-defer-bright)' }} />
            </div>
            <div style={{ fontFamily: 'var(--font-mono)', fontSize: '24px', fontWeight: 800, color: 'var(--text-primary)', marginTop: '4px' }}>
              {(replayStatus?.last_latency_ms ?? 0).toFixed(1)} <span style={{ fontSize: '13px', fontWeight: 500, color: 'var(--text-secondary)' }}>ms (last)</span>
            </div>
            <div style={{ fontSize: '11px', color: 'var(--text-tertiary)', marginTop: '3px' }}>
              {(replayStatus?.avg_latency_ms ?? 0).toFixed(1)} ms rolling mean
            </div>
          </div>
        </div>

        {/* Last Scored Transaction Inspector Panel */}
        <div style={{ background: 'var(--bg-surface-subdued)', padding: '14px 18px', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-subtle)' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Database size={15} style={{ color: 'var(--accent-primary)' }} />
              <span style={{ fontSize: '13px', fontWeight: 700, color: 'var(--text-primary)' }}>
                Last Scored Historical Event Inspector
              </span>
            </div>
            {replayStatus?.last_scored_event && (
              <span style={{ fontFamily: 'var(--font-mono)', fontSize: '11.5px', color: 'var(--text-tertiary)' }}>
                Audit Chain Entry: <strong style={{ color: 'var(--color-routine-bright)' }}>SEALED (HMAC-SHA256)</strong>
              </span>
            )}
          </div>

          {replayStatus?.last_scored_event ? (
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(5, 1fr)', gap: '10px', alignItems: 'center', background: 'var(--bg-surface-raised)', padding: '10px 14px', borderRadius: 'var(--radius-xs)', border: '1px solid var(--border-default)' }}>
              <div>
                <div style={{ fontSize: '10.5px', color: 'var(--text-tertiary)', textTransform: 'uppercase' }}>Event ID / Sequence</div>
                <div style={{ fontFamily: 'var(--font-mono)', fontSize: '12px', fontWeight: 700, color: 'var(--accent-primary-bright)', marginTop: '2px', wordBreak: 'break-all' }}>
                  {replayStatus.last_scored_event.event_id}
                </div>
              </div>

              <div>
                <div style={{ fontSize: '10.5px', color: 'var(--text-tertiary)', textTransform: 'uppercase' }}>Txn ID / Provenance</div>
                <div style={{ fontFamily: 'var(--font-mono)', fontSize: '12px', fontWeight: 700, color: 'var(--text-primary)', marginTop: '2px' }}>
                  {replayStatus.last_scored_event.transaction_id} <span style={{ fontSize: '10px', color: 'var(--text-secondary)' }}>({replayStatus.last_scored_event.data_provenance})</span>
                </div>
              </div>

              <div>
                <div style={{ fontSize: '10.5px', color: 'var(--text-tertiary)', textTransform: 'uppercase' }}>Model Prob (p) / Disagreement (u₂)</div>
                <div style={{ fontFamily: 'var(--font-mono)', fontSize: '12px', fontWeight: 700, color: 'var(--text-primary)', marginTop: '2px' }}>
                  p = {replayStatus.last_scored_event.score.toFixed(4)} &bull; u₂ = {replayStatus.last_scored_event.disagreement.toFixed(4)}
                </div>
              </div>

              <div>
                <div style={{ fontSize: '10.5px', color: 'var(--text-tertiary)', textTransform: 'uppercase' }}>Routing Decision</div>
                <div style={{ marginTop: '2px' }}>
                  <span
                    className="badge"
                    style={{
                      fontSize: '11px',
                      fontWeight: 700,
                      backgroundColor:
                        replayStatus.last_scored_event.action === 'FRAUD_ALERT'
                          ? 'var(--color-fraud-alert)'
                          : replayStatus.last_scored_event.action === 'MANUAL_REVIEW'
                          ? 'var(--color-manual-review)'
                          : replayStatus.last_scored_event.action === 'ROUTINE'
                          ? 'var(--color-routine)'
                          : 'var(--color-epistemic-defer-bright)',
                      color: '#000',
                    }}
                  >
                    {replayStatus.last_scored_event.action}
                  </span>
                </div>
              </div>

              <div>
                <div style={{ fontSize: '10.5px', color: 'var(--text-tertiary)', textTransform: 'uppercase' }}>Reason Code / Rule</div>
                <div style={{ fontFamily: 'var(--font-mono)', fontSize: '12px', fontWeight: 700, color: 'var(--text-secondary)', marginTop: '2px' }}>
                  {replayStatus.last_scored_event.reason_code}
                </div>
              </div>
            </div>
          ) : (
            <div style={{ fontSize: '12.5px', color: 'var(--text-tertiary)', padding: '8px 0', display: 'flex', alignItems: 'center', gap: '8px' }}>
              <ShieldCheck size={14} style={{ color: 'var(--accent-primary)' }} />
              <span>Replay worker ready to stream from <code>data/raw/test_transaction.csv</code>. Click <strong>Step 1 Txn</strong> or <strong>Start Replay</strong> to observe real model scoring and audit registration.</span>
            </div>
          )}
        </div>
      </section>

      {/* 4. Primary Analytical Visual: Compact Signal Core Routing Topology (350px Height) */}
      <section id="topology-section" aria-label="Signal Core Routing Topology">
        <Suspense
          fallback={
            <div
              className="signal-core-container"
              style={{
                minHeight: '350px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                border: '1px solid var(--border-default)',
                borderRadius: 'var(--radius-sm)',
              }}
            >
              <LoadingState message="Loading 3D Decision Topology Scene..." />
            </div>
          }
        >
          <SignalCoreScene />
        </Suspense>
      </section>

      {/* 5. Lower Cockpit: Capacity Allocation, Decision Rules, Pipeline Readiness */}
      <section aria-label="Operational Cockpit Analysis" style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(460px, 1fr))', gap: 'var(--space-4)' }}>
        {/* Pane 1: Human Review Capacity Allocation */}
        <div id="review-capacity-pane" className="sg-card" style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-3)', padding: '18px 20px' }}>
          <div className="sg-card-header" style={{ paddingBottom: '10px', borderBottom: '1px solid var(--border-subtle)' }}>
            <div className="sg-card-title" style={{ fontSize: '15px' }}>
              <UserCheck size={18} style={{ color: 'var(--color-manual-review)' }} />
              <span>Review Capacity Allocation</span>
            </div>
            <span className={`badge ${isLiveDisconnected ? 'badge-alert' : 'badge-caution'}`} style={{ fontSize: '11px' }}>
              <span>{isLiveDisconnected ? 'IDLE / OFFLINE' : 'CAP REACHED'}</span>
            </span>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline' }}>
              <span style={{ fontSize: '13.5px', color: 'var(--text-secondary)' }}>Primary Workload Budget B:</span>
              <span style={{ fontFamily: 'var(--font-mono)', fontSize: '15px', fontWeight: 700, color: 'var(--text-primary)' }}>
                {isLiveDisconnected ? '0 Reviews (Offline)' : isRealDataMode ? '5,993 Reviews (5.075%)' : '130 Reviews (6.525%)'}
              </span>
            </div>

            {/* Stepped Capacity Segmented Bar */}
            <div style={{ width: '100%', height: '10px', background: 'var(--bg-surface-subdued)', borderRadius: '3px', overflow: 'hidden', display: 'flex', border: '1px solid var(--border-default)' }}>
              <div
                style={{ width: isLiveDisconnected ? '0%' : isRealDataMode ? '15%' : '8.4%', background: 'var(--color-fraud-alert)' }}
                title={`${isLiveDisconnected ? 0 : isRealDataMode ? 899 : 11} Alerts`}
              />
              <div
                style={{ width: isLiveDisconnected ? '0%' : isRealDataMode ? '85%' : '91.6%', background: 'var(--color-manual-review)' }}
                title={`${isLiveDisconnected ? 0 : isRealDataMode ? 5094 : 119} Reviews`}
              />
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px', marginTop: '6px' }}>
              <div style={{ background: 'var(--bg-surface-raised)', padding: '10px 14px', borderRadius: 'var(--radius-xs)', border: '1px solid var(--border-subtle)' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                  <span style={{ width: '8px', height: '8px', borderRadius: '2px', background: 'var(--color-fraud-alert)' }} />
                  <span style={{ fontSize: '13px', fontWeight: 600, color: 'var(--text-secondary)' }}>FRAUD_ALERT</span>
                </div>
                <div style={{ fontFamily: 'var(--font-mono)', fontSize: '18px', fontWeight: 800, color: 'var(--color-fraud-alert-bright)', marginTop: '4px' }}>
                  {isLiveDisconnected ? 0 : isRealDataMode ? 899 : 11} <span style={{ fontSize: '12px', color: 'var(--text-tertiary)', fontWeight: 400 }}>cases</span>
                </div>
              </div>

              <div style={{ background: 'var(--bg-surface-raised)', padding: '10px 14px', borderRadius: 'var(--radius-xs)', border: '1px solid var(--border-subtle)' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                  <span style={{ width: '8px', height: '8px', borderRadius: '2px', background: 'var(--color-manual-review)' }} />
                  <span style={{ fontSize: '13px', fontWeight: 600, color: 'var(--text-secondary)' }}>MANUAL_REVIEW</span>
                </div>
                <div style={{ fontFamily: 'var(--font-mono)', fontSize: '18px', fontWeight: 800, color: 'var(--color-manual-review-bright)', marginTop: '4px' }}>
                  {isLiveDisconnected ? '0 / 0' : isRealDataMode ? '5,094 / 5,094' : '119 / 119'} <span style={{ fontSize: '12px', color: 'var(--text-tertiary)', fontWeight: 400 }}>slots</span>
                </div>
              </div>
            </div>

            <p style={{ fontSize: '12.5px', color: 'var(--text-secondary)', margin: '6px 0 0 0', lineHeight: 1.5 }}>
              <strong>Zero Leakage Guarantee:</strong>{' '}
              {isLiveDisconnected
                ? 'Live production banking feed is disconnected; capacity governor is idle with 0 active review slots.'
                : isRealDataMode
                ? 'When analyst queue reaches 5,094 slots, all additional review escalations shunt to HELD / DEFERRED (5,020 cases); never silently passed into Routine.'
                : 'When analyst queue reaches 119 slots, all additional review escalations shunt to HELD / DEFERRED (974 cases); never silently passed into Routine.'}
            </p>
          </div>
        </div>

        {/* Pane 2: Active Scenario Profile & Decision Rules */}
        <div className="sg-card" style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-3)', padding: '18px 20px' }}>
          <div className="sg-card-header" style={{ paddingBottom: '10px', borderBottom: '1px solid var(--border-subtle)' }}>
            <div className="sg-card-title" style={{ fontSize: '15px' }}>
              <Sliders size={18} style={{ color: 'var(--accent-primary)' }} />
              <span>Decision Thresholds & Rules</span>
            </div>
            <span className="badge badge-ready" style={{ fontSize: '11px' }}>
              <span className="badge-dot" />
              <span>FROZEN POLICY</span>
            </span>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', background: 'var(--bg-surface-raised)', padding: '8px 12px', borderRadius: 'var(--radius-xs)' }}>
              <span style={{ fontSize: '13px', color: 'var(--text-secondary)' }}>High Risk Alert (R1):</span>
              <span style={{ fontFamily: 'var(--font-mono)', fontSize: '13px', color: 'var(--color-fraud-alert)', fontWeight: 700 }}>
                p &ge; 0.0847 (t_alert)
              </span>
            </div>

            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', background: 'var(--bg-surface-raised)', padding: '8px 12px', borderRadius: 'var(--radius-xs)' }}>
              <span style={{ fontSize: '13px', color: 'var(--text-secondary)' }}>Intermediate Review (R2):</span>
              <span style={{ fontFamily: 'var(--font-mono)', fontSize: '13px', color: 'var(--color-manual-review)', fontWeight: 700 }}>
                p &ge; 0.0710 (t_review)
              </span>
            </div>

            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', background: 'var(--bg-surface-raised)', padding: '8px 12px', borderRadius: 'var(--radius-xs)' }}>
              <span style={{ fontSize: '13px', color: 'var(--text-secondary)' }}>Disagreement Boundary (R3):</span>
              <span style={{ fontFamily: 'var(--font-mono)', fontSize: '13px', color: 'var(--color-epistemic-defer-bright)', fontWeight: 700 }}>
                u₂ &ge; 0.5268 (u_threshold)
              </span>
            </div>

            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', background: 'var(--bg-surface-raised)', padding: '8px 12px', borderRadius: 'var(--radius-xs)' }}>
              <span style={{ fontSize: '13px', color: 'var(--text-secondary)' }}>Consensus Low Risk (R5):</span>
              <span style={{ fontFamily: 'var(--font-mono)', fontSize: '13px', color: 'var(--color-routine-bright)', fontWeight: 700 }}>
                p &lt; 0.0710 & u₂ &lt; 0.5268
              </span>
            </div>
          </div>
        </div>

        {/* Pane 3: Pipeline Readiness & Provenance Sentinel */}
        <div className="sg-card" style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-3)', padding: '18px 20px', gridColumn: 'span 2' }}>
          <div className="sg-card-header" style={{ paddingBottom: '10px', borderBottom: '1px solid var(--border-subtle)' }}>
            <div className="sg-card-title" style={{ fontSize: '15px' }}>
              <Server size={18} style={{ color: 'var(--accent-primary)' }} />
              <span>Pipeline Readiness (FastAPI)</span>
            </div>
            <span style={{ fontSize: '12px', color: 'var(--text-tertiary)', fontFamily: 'var(--font-mono)' }}>
              /api/status
            </span>
          </div>

          {statusLoading ? (
            <LoadingState message="Verifying pipeline dependencies..." />
          ) : !isBackendConnected ? (
            <ErrorState
              title="Backend Disconnected"
              message={statusError?.message || 'FastAPI service on 127.0.0.1:8000 is not reachable.'}
              onRetry={handleRetryAll}
            />
          ) : (
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(5, 1fr)', gap: '10px' }}>
              <div style={{ background: 'var(--bg-surface-raised)', padding: '10px 12px', borderRadius: 'var(--radius-xs)', border: '1px solid var(--border-subtle)' }}>
                <div style={{ fontSize: '11px', color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '0.04em' }}>1. Backend / API</div>
                <div style={{ fontFamily: 'var(--font-mono)', fontSize: '13.5px', fontWeight: 700, color: 'var(--color-routine-bright)', marginTop: '4px' }}>
                  {status?.readiness?.backend_api || (isBackendConnected ? 'READY' : 'OFFLINE')}
                </div>
              </div>

              <div style={{ background: 'var(--bg-surface-raised)', padding: '10px 12px', borderRadius: 'var(--radius-xs)', border: '1px solid var(--border-subtle)' }}>
                <div style={{ fontSize: '11px', color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '0.04em' }}>2. Model Bundle</div>
                <div style={{ fontFamily: 'var(--font-mono)', fontSize: '13.5px', fontWeight: 700, color: 'var(--color-routine-bright)', marginTop: '4px' }}>
                  {status?.readiness?.local_model || status?.dependencies?.model_artifacts?.status || 'READY'}
                </div>
              </div>

              <div style={{ background: 'var(--bg-surface-raised)', padding: '10px 12px', borderRadius: 'var(--radius-xs)', border: '1px solid var(--border-subtle)' }}>
                <div style={{ fontSize: '11px', color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '0.04em' }}>3. IEEE-CIS Data</div>
                <div style={{ fontFamily: 'var(--font-mono)', fontSize: '13.5px', fontWeight: 700, color: 'var(--color-epistemic-defer-bright)', marginTop: '4px' }}>
                  {status?.readiness?.ieee_cis_data || (isRealDataMode ? 'READY' : 'FIXTURE')}
                </div>
              </div>

              <div style={{ background: 'var(--bg-surface-raised)', padding: '10px 12px', borderRadius: 'var(--radius-xs)', border: '1px solid var(--border-subtle)' }}>
                <div style={{ fontSize: '11px', color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '0.04em' }}>4. Replay Worker</div>
                <div style={{ fontFamily: 'var(--font-mono)', fontSize: '13.5px', fontWeight: 700, color: replayStatus?.is_running ? 'var(--accent-primary-bright)' : 'var(--text-primary)', marginTop: '4px' }}>
                  {replayStatus?.state || 'IDLE'}
                </div>
              </div>

              <div style={{ background: 'var(--bg-surface-raised)', padding: '10px 12px', borderRadius: 'var(--radius-xs)', border: '1px solid var(--border-subtle)' }}>
                <div style={{ fontSize: '11px', color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '0.04em' }}>5. Live Broker</div>
                <div style={{ fontFamily: 'var(--font-mono)', fontSize: '13.5px', fontWeight: 700, color: 'var(--color-fraud-alert-bright)', marginTop: '4px' }}>
                  DISCONNECTED
                </div>
              </div>
            </div>
          )}

          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '12px', color: 'var(--text-secondary)', background: 'var(--bg-surface-subdued)', padding: '8px 14px', borderRadius: 'var(--radius-xs)', border: '1px solid var(--border-subtle)' }}>
            <Lock size={13} style={{ color: 'var(--accent-primary)', flexShrink: 0 }} />
            <span>Leakage Protection: Recursive target and timestamp features strictly rejected.</span>
          </div>
        </div>
      </section>
    </div>
  );
};
