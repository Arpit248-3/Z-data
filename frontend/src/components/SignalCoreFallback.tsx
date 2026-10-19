import React, { useState } from 'react';
import {
  Layers,
  RotateCcw,
  ShieldAlert,
  UserCheck,
  CheckCircle,
  Filter,
  Database,
  Sliders,
} from 'lucide-react';
import { useMode } from '../context/ModeContext';
import { TOPOLOGY_DETAILS } from './topologyData';

interface SignalCoreFallbackProps {
  onSelectNode?: (nodeKey: string) => void;
  onSwitchTo3D?: () => void;
  reason?: string;
}

export const SignalCoreFallback: React.FC<SignalCoreFallbackProps> = ({
  onSelectNode,
  onSwitchTo3D,
  reason = '2D Vector Fallback Mode (SVG Topology Pipeline)',
}) => {
  const { isRealDataMode, isLiveDisconnected } = useMode();
  const [selectedKey, setSelectedKey] = useState<string | null>(null);
  const [hoveredKey, setHoveredKey] = useState<string | null>(null);

  const handleSelect = (key: string) => {
    const nextKey = selectedKey === key ? null : key;
    setSelectedKey(nextKey);
    onSelectNode?.(nextKey || '');
  };

  const activeDetailKey = selectedKey || hoveredKey;
  const activeDetail = activeDetailKey ? TOPOLOGY_DETAILS[activeDetailKey] : null;

  // Active connector state calculation
  const isInputActive = selectedKey === 'stage_input' || hoveredKey === 'stage_input' || selectedKey === 'stage_core' || hoveredKey === 'stage_core';
  const isAlertActive = selectedKey === 'lane_alert' || hoveredKey === 'lane_alert';
  const isReviewActive = selectedKey === 'lane_review' || hoveredKey === 'lane_review';
  const isRoutineActive = selectedKey === 'lane_routine' || hoveredKey === 'lane_routine';
  const isDeferredActive = selectedKey === 'lane_deferred' || hoveredKey === 'lane_deferred';

  return (
    <div className="signal-core-container signal-core-fallback-container" aria-label="Signal Core 2D Vector Topology Fallback">
      {/* 1. Header Toolbar Strip (Clean Title Case) */}
      <div className="signal-core-header-bar">
        <div className="signal-core-header-left">
          <Sliders size={14} className="signal-core-header-icon" />
          <span className="signal-core-title">Decision Topology: Shift-Aware Triage Pipeline</span>
          <span className="badge badge-caution">
            <Layers size={11} />
            <span>{reason}</span>
          </span>
          <span className="badge badge-ready">
            <span className="badge-dot" />
            <span>v2.1 Topology</span>
          </span>
        </div>

        {onSwitchTo3D && (
          <button
            type="button"
            onClick={onSwitchTo3D}
            className="sg-btn sg-btn-secondary signal-core-mode-btn"
            title="Switch back to 3D Canvas view"
            aria-label="Switch back to 3D Canvas"
          >
            <RotateCcw size={12} />
            <span>Switch to 3D Canvas</span>
          </button>
        )}
      </div>

      {/* 2. Main 2D SVG Topology Area */}
      <div className="signal-core-stage-area">
        {/* Layer 2: Directional SVG Connectors and Central 2D Decision Core Assembly */}
        <div className="topology-svg-connectors-layer">
          <svg
            viewBox="0 0 1000 240"
            preserveAspectRatio="none"
            className="topology-connectors-svg"
            aria-hidden="true"
          >
            <defs>
              {/* Arrowhead Markers */}
              <marker id="fallback-arrow-neutral" viewBox="0 0 10 10" refX="7" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
                <path d="M 0 1 L 9 5 L 0 9 z" fill="#3E5060" />
              </marker>
              <marker id="fallback-arrow-teal" viewBox="0 0 10 10" refX="7" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
                <path d="M 0 1 L 9 5 L 0 9 z" fill="#68D8CB" />
              </marker>
              <marker id="fallback-arrow-coral" viewBox="0 0 10 10" refX="7" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
                <path d="M 0 1 L 9 5 L 0 9 z" fill="#F27870" />
              </marker>
              <marker id="fallback-arrow-amber" viewBox="0 0 10 10" refX="7" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
                <path d="M 0 1 L 9 5 L 0 9 z" fill="#E8B35E" />
              </marker>
              <marker id="fallback-arrow-green" viewBox="0 0 10 10" refX="7" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
                <path d="M 0 1 L 9 5 L 0 9 z" fill="#68C99A" />
              </marker>
              <marker id="fallback-arrow-violet" viewBox="0 0 10 10" refX="7" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
                <path d="M 0 1 L 9 5 L 0 9 z" fill="#B4A0F8" />
              </marker>
            </defs>

            {/* Path 1: Input to Decision Core */}
            <path
              d="M 245 120 L 365 120"
              stroke={isInputActive ? '#68D8CB' : '#3E5060'}
              strokeWidth={isInputActive ? '2.5' : '1.75'}
              strokeDasharray={isInputActive ? 'none' : '4 3'}
              fill="none"
              markerEnd={isInputActive ? 'url(#fallback-arrow-teal)' : 'url(#fallback-arrow-neutral)'}
            />

            {/* Central 2D Decision Core Assembly (Centered at x = 485, y = 120) */}
            <g transform="translate(485, 120)">
              {/* Outer Mounting Chassis */}
              <circle r="48" fill="var(--bg-surface-raised)" stroke="var(--border-default)" strokeWidth="2" />
              {/* Mechanical Cardinal Brackets */}
              <rect x="-54" y="-3" width="7" height="6" fill="var(--border-active)" rx="1" />
              <rect x="47" y="-3" width="7" height="6" fill="var(--border-active)" rx="1" />
              <rect x="-3" y="-54" width="6" height="7" fill="var(--border-active)" rx="1" />
              <rect x="-3" y="47" width="6" height="7" fill="var(--border-active)" rx="1" />
              {/* Calibrated Risk Outer Ring: p */}
              <circle
                r="36"
                fill="none"
                stroke={selectedKey === 'stage_core' || hoveredKey === 'stage_core' ? 'var(--accent-primary-bright)' : 'var(--accent-primary)'}
                strokeWidth="4"
              />
              {/* Epistemic Disagreement Angled Ring: u₂ */}
              <ellipse
                rx="26"
                ry="16"
                transform="rotate(30)"
                fill="none"
                stroke="var(--color-epistemic-defer)"
                strokeWidth="2.5"
                strokeDasharray="5 2"
              />
              {/* Central Core Hub */}
              <circle r="14" fill="var(--bg-surface-header)" stroke="var(--border-default)" strokeWidth="1.5" />
              {/* Optical Jewel Core */}
              <circle r="6" fill="var(--text-primary)" stroke="var(--accent-primary)" strokeWidth="1.5" />
            </g>

            {/* Path 2: Decision Core to Lane 1 (FRAUD_ALERT, y = 46) */}
            <path
              d="M 605 120 C 665 120, 675 46, 700 46"
              stroke={isAlertActive ? '#F27870' : '#3E5060'}
              strokeWidth={isAlertActive ? '2.5' : '1.75'}
              strokeDasharray={isAlertActive ? 'none' : '4 3'}
              fill="none"
              markerEnd={isAlertActive ? 'url(#fallback-arrow-coral)' : 'url(#fallback-arrow-neutral)'}
            />

            {/* Path 3: Decision Core to Lane 2 (MANUAL_REVIEW, y = 94) */}
            <path
              d="M 605 120 C 665 120, 675 94, 700 94"
              stroke={isReviewActive ? '#E8B35E' : '#3E5060'}
              strokeWidth={isReviewActive ? '2.5' : '1.75'}
              strokeDasharray={isReviewActive ? 'none' : '4 3'}
              fill="none"
              markerEnd={isReviewActive ? 'url(#fallback-arrow-amber)' : 'url(#fallback-arrow-neutral)'}
            />

            {/* Path 4: Decision Core to Lane 3 (ROUTINE, y = 144) */}
            <path
              d="M 605 120 C 665 120, 675 144, 700 144"
              stroke={isRoutineActive ? '#68C99A' : '#3E5060'}
              strokeWidth={isRoutineActive ? '2.5' : '1.75'}
              strokeDasharray={isRoutineActive ? 'none' : '4 3'}
              fill="none"
              markerEnd={isRoutineActive ? 'url(#fallback-arrow-green)' : 'url(#fallback-arrow-neutral)'}
            />

            {/* Path 5: Decision Core to Lane 4 (HELD/DEFERRED, y = 194) */}
            <path
              d="M 605 120 C 665 120, 675 194, 700 194"
              stroke={isDeferredActive ? '#B4A0F8' : '#3E5060'}
              strokeWidth={isDeferredActive ? '2.5' : '1.75'}
              strokeDasharray={isDeferredActive ? 'none' : '4 3'}
              fill="none"
              markerEnd={isDeferredActive ? 'url(#fallback-arrow-violet)' : 'url(#fallback-arrow-neutral)'}
            />
          </svg>
        </div>

        {/* Layer 4: HTML Stage Grid (Same interactive buttons and non-occluding layout) */}
        <div className="topology-interactive-grid">
          {/* STAGE 1: INGESTION MODULE (Left, ~210px) */}
          <div className="topology-stage-col col-input">
            <button
              type="button"
              className={`stage-input-card ${selectedKey === 'stage_input' ? 'is-selected' : ''}`}
              onClick={() => handleSelect('stage_input')}
              onMouseEnter={() => setHoveredKey('stage_input')}
              onMouseLeave={() => setHoveredKey(null)}
              aria-label={`Stage 1: Input Ingestion. ${isRealDataMode ? '118,108 benchmark' : isLiveDisconnected ? '0 live' : '2,000 offline'} test cases with zero-trust validation.`}
              aria-pressed={selectedKey === 'stage_input'}
            >
              <div className="input-card-header">
                <span className="stage-num-badge">STAGE 1</span>
                <span className="input-cases-pill">
                  {isRealDataMode ? '118,108 cases' : isLiveDisconnected ? '0 cases' : '2,000 cases'}
                </span>
              </div>
              <div className="input-card-title-row">
                <Database size={15} style={{ color: 'var(--accent-primary)', flexShrink: 0 }} />
                <span className="input-card-title">Input Ingestion</span>
              </div>
              <p className="input-card-desc">
                Offline test partition. Schema-verified with zero-trust payload guardrails.
              </p>
              <div className="input-card-status">
                <span className="input-status-dot" />
                <span>Zero-Trust Validation</span>
              </div>
            </button>
          </div>

          {/* STAGE 2: DECISION CORE ZONE (Center, ~280px) */}
          <div className="topology-stage-col col-core">
            <button
              type="button"
              className={`stage-core-card ${selectedKey === 'stage_core' ? 'is-selected' : ''}`}
              onClick={() => handleSelect('stage_core')}
              onMouseEnter={() => setHoveredKey('stage_core')}
              onMouseLeave={() => setHoveredKey(null)}
              aria-label="Stage 2: Decision Core. Dual-model evaluation of calibrated risk score p and epistemic disagreement u₂."
              aria-pressed={selectedKey === 'stage_core'}
            >
              <div className="core-top-label">
                <span className="stage-num-badge">STAGE 2</span>
                <span className="core-stage-name">Decision Core</span>
              </div>

              {/* Middle is transparent to let 2D SVG assembly shine through */}
              <div className="core-center-spacer" aria-hidden="true" />

              <div className="core-bottom-signals">
                <span className="signal-pill signal-risk">
                  <span className="signal-dot dot-risk" />
                  <span>p Calibrated Risk</span>
                </span>
                <span className="signal-pill signal-disagree">
                  <span className="signal-dot dot-disagree" />
                  <span>u₂ Disagreement</span>
                </span>
              </div>
            </button>
          </div>

          {/* STAGE 3: ROUTING OUTCOMES (Right, ~270px) */}
          <div className="topology-stage-col col-lanes">
            <div className="lanes-header-row">
              <span className="stage-num-badge">STAGE 3</span>
              <span className="lanes-header-title">Routing Outcomes</span>
            </div>

            <div className="lanes-vertical-stack">
              {/* Lane 1: FRAUD_ALERT */}
              <button
                type="button"
                className={`outcome-lane-btn lane-alert ${selectedKey === 'lane_alert' ? 'is-selected' : ''}`}
                onClick={() => handleSelect('lane_alert')}
                onMouseEnter={() => setHoveredKey('lane_alert')}
                onMouseLeave={() => setHoveredKey(null)}
                aria-label="Outcome Lane 1: Fraud Alert. 11 cases, p >= 0.0847."
                aria-pressed={selectedKey === 'lane_alert'}
              >
                <div className="lane-accent-bar" style={{ backgroundColor: 'var(--color-fraud-alert)' }} />
                <div className="lane-text-content">
                  <div className="lane-main-line">
                    <ShieldAlert size={13} style={{ color: 'var(--color-fraud-alert)', flexShrink: 0 }} />
                    <span className="lane-action-name">Fraud Alert</span>
                    <span className="lane-count-tag count-alert">11 cases</span>
                  </div>
                  <div className="lane-sub-line">p &ge; 0.0847 &bull; Direct Alert</div>
                </div>
              </button>

              {/* Lane 2: MANUAL_REVIEW */}
              <button
                type="button"
                className={`outcome-lane-btn lane-review ${selectedKey === 'lane_review' ? 'is-selected' : ''}`}
                onClick={() => handleSelect('lane_review')}
                onMouseEnter={() => setHoveredKey('lane_review')}
                onMouseLeave={() => setHoveredKey(null)}
                aria-label="Outcome Lane 2: Manual Review. 119 cases, quota cap saturated."
                aria-pressed={selectedKey === 'lane_review'}
              >
                <div className="lane-accent-bar" style={{ backgroundColor: 'var(--color-manual-review)' }} />
                <div className="lane-text-content">
                  <div className="lane-main-line">
                    <UserCheck size={13} style={{ color: 'var(--color-manual-review)', flexShrink: 0 }} />
                    <span className="lane-action-name">Manual Review</span>
                    <span className="lane-count-tag count-review">119 cases</span>
                  </div>
                  <div className="lane-sub-line">Cap Saturated &bull; Analyst Queue</div>
                </div>
              </button>

              {/* Lane 3: ROUTINE */}
              <button
                type="button"
                className={`outcome-lane-btn lane-routine ${selectedKey === 'lane_routine' ? 'is-selected' : ''}`}
                onClick={() => handleSelect('lane_routine')}
                onMouseEnter={() => setHoveredKey('lane_routine')}
                onMouseLeave={() => setHoveredKey(null)}
                aria-label="Outcome Lane 3: Routine Clearance. 896 cases, automated pass."
                aria-pressed={selectedKey === 'lane_routine'}
              >
                <div className="lane-accent-bar" style={{ backgroundColor: 'var(--color-routine)' }} />
                <div className="lane-text-content">
                  <div className="lane-main-line">
                    <CheckCircle size={13} style={{ color: 'var(--color-routine)', flexShrink: 0 }} />
                    <span className="lane-action-name">Routine</span>
                    <span className="lane-count-tag count-routine">896 cases</span>
                  </div>
                  <div className="lane-sub-line">Low Risk Clearance &bull; Auto Pass</div>
                </div>
              </button>

              {/* Lane 4: HELD / DEFERRED */}
              <button
                type="button"
                className={`outcome-lane-btn lane-deferred ${selectedKey === 'lane_deferred' ? 'is-selected' : ''}`}
                onClick={() => handleSelect('lane_deferred')}
                onMouseEnter={() => setHoveredKey('lane_deferred')}
                onMouseLeave={() => setHoveredKey(null)}
                aria-label="Outcome Lane 4: Held / Deferred. 974 cases, capacity buffer."
                aria-pressed={selectedKey === 'lane_deferred'}
              >
                <div className="lane-accent-bar" style={{ backgroundColor: 'var(--color-epistemic-defer)' }} />
                <div className="lane-text-content">
                  <div className="lane-main-line">
                    <Filter size={13} style={{ color: 'var(--color-epistemic-defer)', flexShrink: 0 }} />
                    <span className="lane-action-name">Held / Deferred</span>
                    <span className="lane-count-tag count-deferred">974 cases</span>
                  </div>
                  <div className="lane-sub-line">Capacity Saturated &bull; 48.7% Staged</div>
                </div>
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* 3. Anchored Inspection & Detail Bar */}
      <div className="signal-core-detail-bar" role="region" aria-live="polite">
        {activeDetail ? (
          <div className="detail-active-row">
            <div className="detail-title-group">
              <span className={`detail-tag detail-tag-${activeDetail.badgeVariant}`}>
                {activeDetail.stageName}
              </span>
              <span className="detail-title">{activeDetail.title}</span>
            </div>
            <div className="detail-role-desc">
              {activeDetail.role}
            </div>
            {activeDetail.formula && (
              <div className="detail-formula">
                <code>{activeDetail.formula}</code>
              </div>
            )}
            {selectedKey && (
              <button
                type="button"
                onClick={() => handleSelect(selectedKey)}
                className="detail-reset-btn"
                title="Reset selection to default topology view"
                aria-label="Reset selection"
              >
                <RotateCcw size={11} />
                <span>Reset View</span>
              </button>
            )}
          </div>
        ) : (
          <div className="detail-default-row">
            <span className="detail-default-hint">
              <strong>Operational Decision Flow (2D Vector):</strong> Input &rarr; Risk/Disagreement Core &rarr; Capacity-Aware Routing. Select any stage or lane to inspect decision logic.
            </span>
            <span className="detail-default-meta">
              {isRealDataMode
                ? 'IEEE-CIS Offline Partition: 118,108 Cases • Primary Review Budget: 5,993 Slots (5.075%)'
                : isLiveDisconnected
                ? 'Live Ingestion Bus: Disconnected • Primary Review Budget: 0 Slots (Fail-Closed)'
                : 'Offline Test Partition: 2,000 Cases • Primary Review Budget: 130 Slots (6.525%)'}
            </span>
          </div>
        )}
      </div>
    </div>
  );
};
