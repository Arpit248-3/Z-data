import React, { Component, ErrorInfo, ReactNode, Suspense, useRef, useState } from 'react';
import { Canvas, useFrame } from '@react-three/fiber';
import * as THREE from 'three';
import { SignalCoreFallback } from './SignalCoreFallback';
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

// ---------------------------------------------------------------------------
// Error Boundary for WebGL/Canvas Failures
// ---------------------------------------------------------------------------
interface ErrorBoundaryProps {
  children: ReactNode;
  fallback: (error: Error) => ReactNode;
}

interface ErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
}

class WebGLErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  constructor(props: ErrorBoundaryProps) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.warn('[SignalCoreScene] WebGL error caught by boundary:', error, errorInfo);
  }

  render() {
    if (this.state.hasError && this.state.error) {
      return this.props.fallback(this.state.error);
    }
    return this.props.children;
  }
}

// ---------------------------------------------------------------------------
// Semantic Detail Definitions for Inspection Bar (Clean Title Case)
// ---------------------------------------------------------------------------
import { TOPOLOGY_DETAILS } from './topologyData';
export type { TopologyElementDetail } from './topologyData';
export { TOPOLOGY_DETAILS };

// ---------------------------------------------------------------------------
// 3D Inner Component: Real-World Dual-Rotor Optical Spectrometer Decision Core
// ---------------------------------------------------------------------------
interface DecisionCore3DProps {
  isSelected: boolean;
  isHovered: boolean;
  prefersReducedMotion: boolean;
}

const DecisionCore3D: React.FC<DecisionCore3DProps> = ({
  isSelected,
  isHovered,
  prefersReducedMotion,
}) => {
  const outerArmatureRef = useRef<THREE.Group>(null);
  const riskRingRef = useRef<THREE.Mesh>(null);
  const disagreeRingRef = useRef<THREE.Mesh>(null);
  const centerPrismRef = useRef<THREE.Mesh>(null);
  const intakePulseRef = useRef<THREE.Mesh>(null);

  useFrame((state, delta) => {
    if (prefersReducedMotion) return;
    const elapsed = state.clock.elapsedTime;

    if (outerArmatureRef.current) {
      outerArmatureRef.current.rotation.z += delta * 0.04;
    }
    if (disagreeRingRef.current) {
      disagreeRingRef.current.rotation.y += delta * 0.07;
      disagreeRingRef.current.rotation.x += delta * 0.035;
    }
    if (riskRingRef.current) {
      riskRingRef.current.rotation.z -= delta * 0.05;
    }
    if (centerPrismRef.current) {
      centerPrismRef.current.rotation.y += delta * 0.06;
      centerPrismRef.current.rotation.z -= delta * 0.03;
      const pulse = 1.0 + Math.sin(elapsed * 3.5) * 0.05;
      centerPrismRef.current.scale.set(pulse, pulse, pulse);
    }
    if (intakePulseRef.current) {
      const p = (elapsed * 1.5) % 1.0;
      intakePulseRef.current.position.x = -1.25 + p * 1.0;
    }
  });

  const activeGlow = isSelected || isHovered;

  return (
    <group position={[0, 0, 0]}>
      {/* 1. Heavy Machined Pedestal Collar & Chassis */}
      <mesh rotation={[Math.PI / 2, 0, 0]}>
        <torusGeometry args={[1.32, 0.035, 16, 64]} />
        <meshStandardMaterial
          color="#1E293B"
          metalness={0.9}
          roughness={0.2}
        />
      </mesh>

      {/* Optical Intake Waveguide Port on Left (-X, receiving Stage 1 feed) */}
      <mesh position={[-1.3, 0, 0]} rotation={[0, 0, Math.PI / 2]}>
        <cylinderGeometry args={[0.07, 0.07, 0.16, 16]} />
        <meshStandardMaterial color="#68D8CB" emissive="#00796B" emissiveIntensity={0.8} />
      </mesh>

      {/* Photonic Ingestion Pulse traveling from Intake into Core */}
      <mesh ref={intakePulseRef} position={[-0.8, 0, 0]}>
        <sphereGeometry args={[0.035, 12, 12]} />
        <meshStandardMaterial color="#FFFFFF" emissive="#68D8CB" emissiveIntensity={2.5} />
      </mesh>

      {/* 4 Optical Output Emitters on Right (+X, aligned toward the 4 Triage Lanes) */}
      {[
        { y: 0.55, color: '#F27870', label: 'Alert' },
        { y: 0.18, color: '#E8B35E', label: 'Review' },
        { y: -0.18, color: '#68D8CB', label: 'Routine' },
        { y: -0.55, color: '#B4A0F8', label: 'Deferred' },
      ].map((lane, idx) => (
        <group key={idx} position={[1.25, lane.y, 0]}>
          <mesh rotation={[0, 0, Math.PI / 2]}>
            <cylinderGeometry args={[0.045, 0.055, 0.14, 12]} />
            <meshStandardMaterial
              color={lane.color}
              emissive={lane.color}
              emissiveIntensity={activeGlow ? 1.6 : 0.8}
              metalness={0.8}
            />
          </mesh>
          {/* Internal Refraction Light Conduit from Center to Emitter */}
          <line>
            <bufferGeometry>
              <bufferAttribute
                attach="attributes-position"
                args={[new Float32Array([0, 0, 0, -1.25, -lane.y, 0]), 3]}
              />
            </bufferGeometry>
            <lineBasicMaterial
              color={lane.color}
              transparent={true}
              opacity={activeGlow ? 0.6 : 0.25}
            />
          </line>
        </group>
      ))}

      {/* 2. Outer Datum Ticks & Caliper Brackets */}
      <group ref={outerArmatureRef}>
        {[0, Math.PI / 3, (2 * Math.PI) / 3, Math.PI, (4 * Math.PI) / 3, (5 * Math.PI) / 3].map((angle, idx) => (
          <group key={idx} rotation={[0, 0, angle]}>
            <mesh position={[1.32, 0, 0]}>
              <boxGeometry args={[0.12, 0.03, 0.04]} />
              <meshStandardMaterial
                color={idx % 2 === 0 ? '#68D8CB' : '#B4A0F8'}
                emissive={idx % 2 === 0 ? '#004740' : '#2A1854'}
                emissiveIntensity={0.7}
                metalness={0.85}
              />
            </mesh>
          </group>
        ))}
      </group>

      {/* 3. Principal Calibrated Risk Rotor Ring: p (Surgical Vibrant Teal) */}
      <mesh ref={riskRingRef}>
        <torusGeometry args={[0.96, 0.045, 16, 64]} />
        <meshStandardMaterial
          color={activeGlow ? '#94FFF0' : '#68D8CB'}
          emissive="#00796B"
          emissiveIntensity={activeGlow ? 1.5 : 0.9}
          metalness={0.75}
          roughness={0.15}
        />
      </mesh>

      {/* 4. Epistemic Disagreement Angled Gimbal Ring: u₂ (Luminous Violet) */}
      <mesh
        ref={disagreeRingRef}
        rotation={[Math.PI / 4, Math.PI / 5, 0]}
      >
        <torusGeometry args={[0.74, 0.038, 16, 64]} />
        <meshStandardMaterial
          color={activeGlow ? '#D1C4FF' : '#B4A0F8'}
          emissive="#4B2896"
          emissiveIntensity={activeGlow ? 1.4 : 0.85}
          metalness={0.8}
          roughness={0.2}
        />
      </mesh>

      {/* 5. Central Hub Precision Chassis */}
      <mesh rotation={[Math.PI / 2, 0, 0]}>
        <cylinderGeometry args={[0.34, 0.38, 0.1, 32]} />
        <meshStandardMaterial
          color="#334155"
          metalness={0.9}
          roughness={0.2}
        />
      </mesh>
      <mesh rotation={[Math.PI / 2, 0, 0]}>
        <torusGeometry args={[0.34, 0.02, 16, 32]} />
        <meshStandardMaterial
          color="#68D8CB"
          emissive="#004740"
          emissiveIntensity={0.6}
        />
      </mesh>

      {/* 6. Central Hexagonal Beam-Splitter Quartz Crystal Prism */}
      <mesh ref={centerPrismRef} position={[0, 0, 0.06]}>
        <cylinderGeometry args={[0.16, 0.16, 0.14, 6]} />
        <meshStandardMaterial
          color="#FFFFFF"
          emissive="#68D8CB"
          emissiveIntensity={activeGlow ? 1.6 : 1.1}
          metalness={0.9}
          roughness={0.1}
          transparent={true}
          opacity={0.92}
        />
      </mesh>

      {/* Core Specular Photonic Spark */}
      <mesh position={[0, 0, 0.06]}>
        <sphereGeometry args={[0.06, 16, 16]} />
        <meshStandardMaterial
          color="#FFFFFF"
          emissive="#FFFFFF"
          emissiveIntensity={3.0}
        />
      </mesh>
    </group>
  );
};

// ---------------------------------------------------------------------------
// Main SignalCoreScene Component (Hybrid 2.5D Topology)
// ---------------------------------------------------------------------------
export const SignalCoreScene: React.FC = () => {
  const { isRealDataMode, isLiveDisconnected } = useMode();
  const [selectedKey, setSelectedKey] = useState<string | null>(null);
  const [hoveredKey, setHoveredKey] = useState<string | null>(null);
  const [forceFallback, setForceFallback] = useState<boolean>(false);

  // Check prefers-reduced-motion
  const prefersReducedMotion =
    typeof window !== 'undefined' &&
    window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  const activeDetailKey = selectedKey || hoveredKey;
  const activeDetail = activeDetailKey ? TOPOLOGY_DETAILS[activeDetailKey] : null;

  if (forceFallback || prefersReducedMotion) {
    return (
      <SignalCoreFallback
        reason={prefersReducedMotion ? 'Reduced motion preference active' : '2D Vector Mode selected'}
        onSelectNode={(key) => setSelectedKey(key)}
        onSwitchTo3D={() => setForceFallback(false)}
      />
    );
  }

  // Active connector state calculation
  const isInputActive = selectedKey === 'stage_input' || hoveredKey === 'stage_input' || selectedKey === 'stage_core' || hoveredKey === 'stage_core';
  const isAlertActive = selectedKey === 'lane_alert' || hoveredKey === 'lane_alert';
  const isReviewActive = selectedKey === 'lane_review' || hoveredKey === 'lane_review';
  const isRoutineActive = selectedKey === 'lane_routine' || hoveredKey === 'lane_routine';
  const isDeferredActive = selectedKey === 'lane_deferred' || hoveredKey === 'lane_deferred';

  return (
    <div className="signal-core-container" aria-label="Signal Core Decision Topology Visualizer">
      {/* 1. Header Toolbar Strip (Clean Title Case, Zero Faux-Terminal //) */}
      <div className="signal-core-header-bar">
        <div className="signal-core-header-left">
          <Sliders size={14} className="signal-core-header-icon" />
          <span className="signal-core-title">Decision Topology: Shift-Aware Triage Pipeline</span>
          {isRealDataMode ? (
            <span className="badge badge-ready">
              <span>IEEE-CIS Offline Benchmark</span>
            </span>
          ) : isLiveDisconnected ? (
            <span className="badge badge-alert">
              <span>Live Ingestion Disconnected</span>
            </span>
          ) : (
            <span className="badge badge-synthetic">
              <span>Synthetic Fixture</span>
            </span>
          )}
          <span className="badge badge-ready">
            <span className="badge-dot" />
            <span>v2.1 Topology</span>
          </span>
        </div>

        <button
          type="button"
          onClick={() => setForceFallback(true)}
          className="sg-btn sg-btn-secondary signal-core-mode-btn"
          title="Switch to 2D SVG vector diagram"
          aria-label="Switch to 2D SVG vector mode"
        >
          <Layers size={12} />
          <span>2D Vector Mode</span>
        </button>
      </div>

      {/* 2. Main Hybrid 2.5D Decision Stage Area (236px container height budget) */}
      <div className="signal-core-stage-area">
        {/* Layer 2: High-Contrast Directional SVG Connectors with Arrowheads */}
        <div className="topology-svg-connectors-layer">
          <svg
            viewBox="0 0 1000 240"
            preserveAspectRatio="none"
            className="topology-connectors-svg"
            aria-hidden="true"
          >
            <defs>
              {/* Neutral Arrowhead Marker */}
              <marker
                id="arrow-neutral"
                viewBox="0 0 10 10"
                refX="7"
                refY="5"
                markerWidth="6"
                markerHeight="6"
                orient="auto-start-reverse"
              >
                <path d="M 0 1 L 9 5 L 0 9 z" fill="var(--border-active)" />
              </marker>

              {/* Active Teal Arrowhead */}
              <marker
                id="arrow-teal"
                viewBox="0 0 10 10"
                refX="7"
                refY="5"
                markerWidth="7"
                markerHeight="7"
                orient="auto-start-reverse"
              >
                <path d="M 0 1 L 9 5 L 0 9 z" fill="var(--accent-primary)" />
              </marker>

              {/* Active Coral Arrowhead */}
              <marker
                id="arrow-coral"
                viewBox="0 0 10 10"
                refX="7"
                refY="5"
                markerWidth="7"
                markerHeight="7"
                orient="auto-start-reverse"
              >
                <path d="M 0 1 L 9 5 L 0 9 z" fill="var(--color-fraud-alert)" />
              </marker>

              {/* Active Amber Arrowhead */}
              <marker
                id="arrow-amber"
                viewBox="0 0 10 10"
                refX="7"
                refY="5"
                markerWidth="7"
                markerHeight="7"
                orient="auto-start-reverse"
              >
                <path d="M 0 1 L 9 5 L 0 9 z" fill="var(--color-manual-review)" />
              </marker>

              {/* Active Green Arrowhead */}
              <marker
                id="arrow-green"
                viewBox="0 0 10 10"
                refX="7"
                refY="5"
                markerWidth="7"
                markerHeight="7"
                orient="auto-start-reverse"
              >
                <path d="M 0 1 L 9 5 L 0 9 z" fill="var(--color-routine)" />
              </marker>

              {/* Active Violet Arrowhead */}
              <marker
                id="arrow-violet"
                viewBox="0 0 10 10"
                refX="7"
                refY="5"
                markerWidth="7"
                markerHeight="7"
                orient="auto-start-reverse"
              >
                <path d="M 0 1 L 9 5 L 0 9 z" fill="var(--color-epistemic-defer)" />
              </marker>
            </defs>

            {/* Path 1: Input to Decision Core */}
            <path
              d="M 245 120 L 365 120"
              stroke={isInputActive ? 'var(--accent-primary)' : 'var(--border-active)'}
              strokeWidth={isInputActive ? '2.5' : '1.75'}
              strokeDasharray={isInputActive ? 'none' : '4 3'}
              fill="none"
              markerEnd={isInputActive ? 'url(#arrow-teal)' : 'url(#arrow-neutral)'}
            />

            {/* Path 2: Decision Core to Lane 1 (FRAUD_ALERT, y = 46) */}
            <path
              d="M 605 120 C 665 120, 675 46, 700 46"
              stroke={isAlertActive ? 'var(--color-fraud-alert)' : 'var(--border-active)'}
              strokeWidth={isAlertActive ? '2.5' : '1.75'}
              strokeDasharray={isAlertActive ? 'none' : '4 3'}
              fill="none"
              markerEnd={isAlertActive ? 'url(#arrow-coral)' : 'url(#arrow-neutral)'}
            />

            {/* Path 3: Decision Core to Lane 2 (MANUAL_REVIEW, y = 94) */}
            <path
              d="M 605 120 C 665 120, 675 94, 700 94"
              stroke={isReviewActive ? 'var(--color-manual-review)' : 'var(--border-active)'}
              strokeWidth={isReviewActive ? '2.5' : '1.75'}
              strokeDasharray={isReviewActive ? 'none' : '4 3'}
              fill="none"
              markerEnd={isReviewActive ? 'url(#arrow-amber)' : 'url(#arrow-neutral)'}
            />

            {/* Path 4: Decision Core to Lane 3 (ROUTINE, y = 144) */}
            <path
              d="M 605 120 C 665 120, 675 144, 700 144"
              stroke={isRoutineActive ? 'var(--color-routine)' : 'var(--border-active)'}
              strokeWidth={isRoutineActive ? '2.5' : '1.75'}
              strokeDasharray={isRoutineActive ? 'none' : '4 3'}
              fill="none"
              markerEnd={isRoutineActive ? 'url(#arrow-green)' : 'url(#arrow-neutral)'}
            />

            {/* Path 5: Decision Core to Lane 4 (HELD/DEFERRED, y = 194) */}
            <path
              d="M 605 120 C 665 120, 675 194, 700 194"
              stroke={isDeferredActive ? 'var(--color-epistemic-defer)' : 'var(--border-active)'}
              strokeWidth={isDeferredActive ? '2.5' : '1.75'}
              strokeDasharray={isDeferredActive ? 'none' : '4 3'}
              fill="none"
              markerEnd={isDeferredActive ? 'url(#arrow-violet)' : 'url(#arrow-neutral)'}
            />
          </svg>
        </div>

        {/* Layer 3: Central 3D Canvas (Dedicated Unobscured Center Viewport) */}
        <div className="topology-core-canvas-container">
          <WebGLErrorBoundary
            fallback={(error) => (
              <SignalCoreFallback reason={`WebGL initialization failed: ${error.message}`} />
            )}
          >
            <Suspense fallback={<div className="core-canvas-loading">Loading 3D Core...</div>}>
              <Canvas
                camera={{ position: [0, 0, 6.2], fov: 34 }}
                dpr={[1, 1.5]}
                gl={{ antialias: true, alpha: true, powerPreference: 'high-performance' }}
                style={{ pointerEvents: 'none' }}
              >
                <ambientLight intensity={1.0} />
                <directionalLight position={[5, 6, 8]} intensity={1.8} color="#EDF2F6" />
                <pointLight position={[-5, -3, 4]} intensity={1.4} color="#86F5E7" />
                <pointLight position={[5, -3, 4]} intensity={1.2} color="#D1C4FF" />
                <pointLight position={[0, 0, 6]} intensity={0.8} color="#EDF2F6" />

                <DecisionCore3D
                  isSelected={selectedKey === 'stage_core'}
                  isHovered={hoveredKey === 'stage_core'}
                  prefersReducedMotion={prefersReducedMotion}
                />
              </Canvas>
            </Suspense>
          </WebGLErrorBoundary>
        </div>

        {/* Layer 4: HTML Stage Grid (Left Ingestion, Center Labels, Right Lanes) */}
        <div className="topology-interactive-grid">
          {/* STAGE 1: INGESTION MODULE (Left, ~210px) */}
          <div className="topology-stage-col col-input">
            <button
              type="button"
              className={`stage-input-card ${selectedKey === 'stage_input' ? 'is-selected' : ''}`}
              onClick={() => setSelectedKey(selectedKey === 'stage_input' ? null : 'stage_input')}
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
          {/* Note: Labels are placed OUTSIDE the 3D geometry footprint; central area is transparent! */}
          <div className="topology-stage-col col-core">
            <button
              type="button"
              className={`stage-core-card ${selectedKey === 'stage_core' ? 'is-selected' : ''}`}
              onClick={() => setSelectedKey(selectedKey === 'stage_core' ? null : 'stage_core')}
              onMouseEnter={() => setHoveredKey('stage_core')}
              onMouseLeave={() => setHoveredKey(null)}
              aria-label="Stage 2: Decision Core. Dual-model evaluation of calibrated risk score p and epistemic disagreement u₂."
              aria-pressed={selectedKey === 'stage_core'}
            >
              <div className="core-top-label">
                <span className="stage-num-badge">STAGE 2</span>
                <span className="core-stage-name">Decision Core</span>
              </div>

              {/* Middle is transparent to let 3D assembly shine through */}
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
                onClick={() => setSelectedKey(selectedKey === 'lane_alert' ? null : 'lane_alert')}
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
                onClick={() => setSelectedKey(selectedKey === 'lane_review' ? null : 'lane_review')}
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
                onClick={() => setSelectedKey(selectedKey === 'lane_routine' ? null : 'lane_routine')}
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
                onClick={() => setSelectedKey(selectedKey === 'lane_deferred' ? null : 'lane_deferred')}
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

      {/* 3. Anchored Inspection & Detail Bar (~36px height) */}
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
                onClick={() => setSelectedKey(null)}
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
              <strong>Operational Decision Flow:</strong> Input &rarr; Risk/Disagreement Core &rarr; Capacity-Aware Routing. Select any stage or lane to inspect decision logic.
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
