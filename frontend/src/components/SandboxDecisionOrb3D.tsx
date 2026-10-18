import React, {
  useRef,
  useState,
  useEffect,
  useMemo,
  Suspense,
  Component,
  ReactNode,
  ErrorInfo,
} from 'react';
import { Canvas, useFrame, useThree, useLoader } from '@react-three/fiber';
import * as THREE from 'three';
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js';
import {
  Compass,
  Box,
  Eye,
  Layers,
  RotateCcw,
  ZoomIn,
  ZoomOut,
} from 'lucide-react';

// ---------------------------------------------------------------------------
// 1. Types & Documented Probability-to-Segment Mapping Rule
// ---------------------------------------------------------------------------
export interface DecisionOrbProps {
  risk: number;
  disagreement: number;
  action: string | null;
  reasonCode?: string | null;
  isEvaluating: boolean;
  hasResult: boolean;
  error?: string | null;
}

/**
 * Maps calibrated posterior probability p in [0.0, 1.0] to exactly 48 circular
 * risk segments (risk_segment_00 through risk_segment_47).
 *
 * Rule:
 * - If p <= 0: returns 0 (zero segments illuminated; track in neutral baseline state).
 * - If p > 0: returns Math.min(48, Math.max(1, Math.round(p * 48))).
 *
 * Canonical Threshold Benchmarks:
 * - p = 0.0000 -> 0 segments
 * - p = 0.0500 -> 2 segments
 * - p = 0.0710 (t_review) -> 3 segments
 * - p = 0.0847 (t_alert)  -> 4 segments
 * - p = 0.5000 -> 24 segments (180 deg / half circle)
 * - p = 1.0000 -> 48 segments (360 deg / full track)
 */
export function calculateHighlightedSegments(p: number): number {
  if (typeof p !== 'number' || isNaN(p) || p <= 0) return 0;
  return Math.min(48, Math.max(1, Math.round(p * 48)));
}

/**
 * Checks for reliable WebGL 1.0/2.0 context availability before mounting Canvas.
 */
function checkWebGLSupport(): boolean {
  if (typeof window === 'undefined') return false;
  try {
    const canvas = document.createElement('canvas');
    return Boolean(
      window.WebGLRenderingContext &&
        (canvas.getContext('webgl') || canvas.getContext('experimental-webgl'))
    );
  } catch {
    return false;
  }
}

// ---------------------------------------------------------------------------
// 2. Error Boundary for Robust 3D Fallback
// ---------------------------------------------------------------------------
interface ErrorBoundaryProps {
  fallback: ReactNode;
  children: ReactNode;
}

interface ErrorBoundaryState {
  hasError: boolean;
}

class Sandbox3DErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  constructor(props: ErrorBoundaryProps) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(): ErrorBoundaryState {
    return { hasError: true };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.warn('[SignalGate 3D Instrument] WebGL pipeline error:', error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return this.props.fallback;
    }
    return this.props.children;
  }
}

// ---------------------------------------------------------------------------
// 3. 2D High-Density Schematic Instrument Fallback
// ---------------------------------------------------------------------------
const SchematicInstrumentFallback: React.FC<DecisionOrbProps & { viewPreset: string }> = ({
  risk,
  disagreement,
  action,
  reasonCode,
  isEvaluating,
  hasResult,
  error,
}) => {
  const highlightedCount = hasResult ? calculateHighlightedSegments(risk) : 0;
  const segments = Array.from({ length: 48 }, (_, i) => i);

  const actionColor =
    action === 'FRAUD_ALERT' ? '#F27870' :
    action === 'MANUAL_REVIEW' ? '#E8B35E' :
    action === 'ROUTINE' ? '#68D8CB' :
    action === 'HELD' ? '#B4A0F8' : '#7DAAFF';

  return (
    <div
      style={{
        width: '100%',
        height: '100%',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '12px',
        background: 'radial-gradient(ellipse at 50% 50%, var(--bg-surface-raised) 0%, var(--bg-surface-subdued) 100%)',
        position: 'relative',
      }}
    >
      <svg viewBox="-120 -120 240 240" style={{ width: '190px', height: '190px' }}>
        {/* Outer Bezel */}
        <circle cx="0" cy="0" r="112" fill="none" stroke="#293743" strokeWidth="6" />
        <circle cx="0" cy="0" r="102" fill="none" stroke="#344654" strokeWidth="2" />
        <circle cx="0" cy="0" r="76" fill="none" stroke="#293743" strokeWidth="1.5" />

        {/* 4 Cardinal Ticks */}
        <line x1="0" y1="-106" x2="0" y2="-98" stroke="#68D8CB" strokeWidth="2.5" />
        <line x1="0" y1="106" x2="0" y2="98" stroke="#68D8CB" strokeWidth="2" />
        <line x1="-106" y1="0" x2="-98" y2="0" stroke="#68D8CB" strokeWidth="2" />
        <line x1="106" y1="0" x2="98" y2="0" stroke="#68D8CB" strokeWidth="2" />

        {/* 48 Circular Risk Segments */}
        {segments.map((idx) => {
          const angle = (Math.PI / 2) - idx * ((2 * Math.PI) / 48);
          const r1 = 80;
          const r2 = 98;
          const x1 = r1 * Math.cos(angle);
          const y1 = -r1 * Math.sin(angle);
          const x2 = r2 * Math.cos(angle);
          const y2 = -r2 * Math.sin(angle);

          const isLit = hasResult && idx < highlightedCount;
          const isZeroRef = idx === 0 && !hasResult;
          const stroke = isLit ? actionColor : isZeroRef ? '#68D8CB' : '#2D3E4E';
          const strokeWidth = isLit ? 3.5 : 2.0;

          return (
            <line
              key={idx}
              x1={x1}
              y1={y1}
              x2={x2}
              y2={y2}
              stroke={stroke}
              strokeWidth={strokeWidth}
              strokeLinecap="round"
              opacity={isLit ? 1.0 : isZeroRef ? 0.8 : 0.45}
            />
          );
        })}

        {/* Symmetrical Flank Uncertainty Calipers */}
        <path
          d="M -34 -20 A 40 40 0 0 0 -34 20"
          fill="none"
          stroke="#B4A0F8"
          strokeWidth="3.5"
          strokeLinecap="round"
          opacity={hasResult ? 0.95 : 0.45}
        />
        <path
          d="M 34 -20 A 40 40 0 0 1 34 20"
          fill="none"
          stroke="#B4A0F8"
          strokeWidth="3.5"
          strokeLinecap="round"
          opacity={hasResult ? 0.95 : 0.45}
        />

        {/* Central Core Aperture */}
        <circle cx="0" cy="0" r="28" fill="#18232D" stroke="#68D8CB" strokeWidth="2" />
        <circle cx="0" cy="0" r="10" fill={hasResult ? actionColor : '#344654'} />
        <circle cx="0" cy="0" r="5" fill="#A2B0BC" />
      </svg>

      <div
        style={{
          marginTop: '6px',
          fontFamily: 'var(--font-mono)',
          fontSize: '11px',
          color: 'var(--text-secondary)',
          display: 'flex',
          gap: '12px',
        }}
      >
        <span>
          48-Seg Risk:{' '}
          {hasResult
            ? `${highlightedCount}/48 (${(risk * 100).toFixed(1)}%)`
            : isEvaluating
            ? 'Evaluating...'
            : error
            ? 'Error'
            : 'Ready'}
        </span>
        <span>&bull;</span>
        <span>
          u₂ Disagreement:{' '}
          {hasResult
            ? disagreement.toFixed(4)
            : reasonCode
            ? `[${reasonCode}]`
            : 'Standby'}
        </span>
      </div>
    </div>
  );
};

// ---------------------------------------------------------------------------
// 4. Responsive Perspective Camera Controller
// ---------------------------------------------------------------------------
function ResponsiveInstrumentCamera() {
  const { camera, size } = useThree();

  useEffect(() => {
    const persCamera = camera as THREE.PerspectiveCamera;
    persCamera.fov = 42;
    const aspect = size.width / Math.max(size.height, 1);

    // Zoomed framing: The instrument assembly has a physical diameter of ~3.90 units.
    // To ensure it appears large, zoomed, and prominent (filling ~94% of the viewport height),
    // we calculate the camera distance precisely based on FOV = 42 deg and aspect ratio.
    const tanHalfFov = Math.tan((42 * Math.PI) / 360); // tan(21 deg) ~ 0.38386
    const desiredSpan = 4.15; // 3.90 / 0.94
    const requiredHeight = desiredSpan / Math.min(1.0, Math.max(0.65, aspect));
    const targetDistance = requiredHeight / (2 * tanHalfFov);

    persCamera.position.set(0, 0, targetDistance);
    persCamera.lookAt(0, 0, 0);
    persCamera.updateProjectionMatrix();
  }, [camera, size]);

  return null;
}

// ---------------------------------------------------------------------------
// 5. Genuine GLTF Inference Instrument Model with Cursor Direction Hover Parallax
// ---------------------------------------------------------------------------
interface InstrumentGLBProps {
  risk: number;
  disagreement: number;
  action: string | null;
  isEvaluating: boolean;
  hasResult: boolean;
  prefersReducedMotion: boolean;
  isPointerOverCanvas: boolean;
  dragRotation: { x: number; y: number };
  viewPreset: 'cursor' | 'isometric' | 'front' | 'side';
  zoomLevel: number;
}

const SandboxInferenceInstrumentModel: React.FC<InstrumentGLBProps> = ({
  risk,
  disagreement,
  action,
  isEvaluating,
  hasResult,
  prefersReducedMotion,
  isPointerOverCanvas,
  dragRotation,
  viewPreset,
  zoomLevel,
}) => {
  const rootPivotRef = useRef<THREE.Group>(null);
  const uncertaintyArcRef = useRef<THREE.Group | null>(null);
  const centerCoreRef = useRef<THREE.Group | null>(null);
  const segmentMeshesRef = useRef<THREE.Mesh[]>([]);

  const settleProgress = useRef<number>(1.0);
  const lastAction = useRef<string | null>(action);

  // Load production GLB
  const gltf = useLoader(GLTFLoader, '/models/sandbox-inference-instrument.glb');
  const scene = useMemo(() => gltf.scene.clone(true), [gltf.scene]);

  // Documented rounding rule for segment lighting
  const highlightedSegmentsCount = useMemo(() => {
    if (!hasResult) return 0;
    return calculateHighlightedSegments(risk);
  }, [hasResult, risk]);

  // Palette definitions mapping strictly to SignalGate decision truth states
  const materials = useMemo(() => {
    return {
      neutralSegment: new THREE.MeshStandardMaterial({
        color: new THREE.Color('#2D3E4E'),
        metalness: 0.12,
        roughness: 0.40,
      }),
      zeroRefSegment: new THREE.MeshStandardMaterial({
        color: new THREE.Color('#68D8CB'),
        emissive: new THREE.Color('#005D55'),
        emissiveIntensity: 0.65,
        metalness: 0.15,
        roughness: 0.25,
      }),
      fraudAlert: new THREE.MeshStandardMaterial({
        color: new THREE.Color('#F27870'),
        emissive: new THREE.Color('#DC2626'),
        emissiveIntensity: 1.4,
        metalness: 0.20,
        roughness: 0.22,
      }),
      manualReview: new THREE.MeshStandardMaterial({
        color: new THREE.Color('#E8B35E'),
        emissive: new THREE.Color('#D97706'),
        emissiveIntensity: 1.25,
        metalness: 0.20,
        roughness: 0.25,
      }),
      routine: new THREE.MeshStandardMaterial({
        color: new THREE.Color('#68D8CB'),
        emissive: new THREE.Color('#059669'),
        emissiveIntensity: 1.15,
        metalness: 0.15,
        roughness: 0.22,
      }),
      held: new THREE.MeshStandardMaterial({
        color: new THREE.Color('#B4A0F8'),
        emissive: new THREE.Color('#7C3AED'),
        emissiveIntensity: 1.35,
        metalness: 0.15,
        roughness: 0.22,
      }),
      loadingWave: new THREE.MeshStandardMaterial({
        color: new THREE.Color('#7DAAFF'),
        emissive: new THREE.Color('#2563EB'),
        emissiveIntensity: 1.2,
        metalness: 0.2,
        roughness: 0.2,
      }),
    };
  }, []);

  // Active highlighted segment material based on verified action
  const activeSegmentMaterial = useMemo(() => {
    if (action === 'FRAUD_ALERT') return materials.fraudAlert;
    if (action === 'MANUAL_REVIEW') return materials.manualReview;
    if (action === 'HELD') return materials.held;
    return materials.routine;
  }, [action, materials]);

  // Traverse and discover all 48 segments and major functional assemblies
  useEffect(() => {
    const segMap: THREE.Mesh[] = [];

    scene.traverse((child) => {
      if ((child as THREE.Mesh).isMesh) {
        const mesh = child as THREE.Mesh;
        const name = mesh.name;

        // Discover and index all 48 risk segments
        if (name.startsWith('risk_segment_')) {
          const match = name.match(/risk_segment_(\d+)/);
          if (match) {
            const idx = parseInt(match[1], 10);
            if (idx >= 0 && idx < 48) {
              segMap[idx] = mesh;
            }
          }
        }
      } else if ((child as THREE.Group).isGroup) {
        const grp = child as THREE.Group;
        if (grp.name === 'uncertainty_arc') {
          uncertaintyArcRef.current = grp;
        } else if (grp.name === 'center_core') {
          centerCoreRef.current = grp;
        }
      }
    });

    segmentMeshesRef.current = segMap;
  }, [scene]);

  // Trigger settle transition on score arrival or action change
  useEffect(() => {
    if (action !== lastAction.current) {
      lastAction.current = action;
      settleProgress.current = 0.0;
    }
  }, [action]);

  // Animation and interaction loop
  useFrame((state, delta) => {
    const elapsed = state.clock.elapsedTime;

    // Advance settle progress
    if (settleProgress.current < 1.0) {
      settleProgress.current = Math.min(1.0, settleProgress.current + delta * 2.8);
    }

    // 1. Dynamic Orientation & Hover Parallax Tracking in all directions
    if (rootPivotRef.current) {
      let targetRotX = 0;
      let targetRotY = 0;

      if (viewPreset === 'isometric') {
        targetRotX = 0.38;
        targetRotY = 0.52;
      } else if (viewPreset === 'side') {
        targetRotX = 0.12;
        targetRotY = 1.25; // Profile angle showing thickness & cavity
      } else if (viewPreset === 'front') {
        targetRotX = 0.0;
        targetRotY = 0.0;
      } else {
        // 'cursor' mode: Smoothly tilts and pivots in the exact direction of cursor hover
        // Cursor up -> tilts forward (looks down into layers); Cursor down -> tilts back
        // Cursor right -> turns right; Cursor left -> turns left
        const mouseTiltX = isPointerOverCanvas ? -state.pointer.y * 0.52 : 0.0;
        const mouseTiltY = isPointerOverCanvas ? state.pointer.x * 0.68 : 0.0;
        targetRotX = mouseTiltX + dragRotation.x;
        targetRotY = mouseTiltY + dragRotation.y;
      }

      if (prefersReducedMotion) {
        rootPivotRef.current.rotation.x = targetRotX;
        rootPivotRef.current.rotation.y = targetRotY;
        rootPivotRef.current.scale.setScalar(zoomLevel);
      } else {
        const lerpSpeed = Math.min(delta * 9, 0.28);
        rootPivotRef.current.rotation.x = THREE.MathUtils.lerp(
          rootPivotRef.current.rotation.x,
          targetRotX,
          lerpSpeed
        );
        rootPivotRef.current.rotation.y = THREE.MathUtils.lerp(
          rootPivotRef.current.rotation.y,
          targetRotY,
          lerpSpeed
        );
        const curScale = rootPivotRef.current.scale.x;
        rootPivotRef.current.scale.setScalar(
          THREE.MathUtils.lerp(curScale, zoomLevel, lerpSpeed)
        );
      }
    }

    // 2. Segment Material State Updating
    const segments = segmentMeshesRef.current;
    if (segments.length === 48) {
      if (isEvaluating) {
        // Loading state: smooth sequential wave across the 48 segments
        const waveCenter = Math.floor((elapsed * 16) % 48);
        for (let i = 0; i < 48; i++) {
          const seg = segments[i];
          if (!seg) continue;
          const diff = (i - waveCenter + 48) % 48;
          if (diff <= 3) {
            seg.material = materials.loadingWave;
          } else {
            seg.material = (i === 0) ? materials.zeroRefSegment : materials.neutralSegment;
          }
        }
      } else if (hasResult) {
        // Success state: illuminate strictly the calculated proportion
        for (let i = 0; i < 48; i++) {
          const seg = segments[i];
          if (!seg) continue;
          if (i < highlightedSegmentsCount) {
            seg.material = activeSegmentMaterial;
          } else {
            seg.material = (i === 0) ? materials.zeroRefSegment : materials.neutralSegment;
          }
        }
      } else {
        // Idle/Standby state: zero segments illuminated; segment 00 as subtle zero reference
        for (let i = 0; i < 48; i++) {
          const seg = segments[i];
          if (!seg) continue;
          seg.material = (i === 0) ? materials.zeroRefSegment : materials.neutralSegment;
        }
      }
    }

    // 3. Violet Disagreement Caliper Arc Response (u2)
    if (uncertaintyArcRef.current) {
      if (!prefersReducedMotion) {
        // Subtle epistemic tilt responding to signed residual u2
        const targetCaliperTilt = hasResult
          ? THREE.MathUtils.clamp(disagreement * 0.35, -0.28, 0.28)
          : 0.0;
        uncertaintyArcRef.current.rotation.z = THREE.MathUtils.lerp(
          uncertaintyArcRef.current.rotation.z,
          targetCaliperTilt,
          Math.min(delta * 4, 0.2)
        );
      }
    }

    // 4. Center Core Pulse on Active Inference
    if (centerCoreRef.current && !prefersReducedMotion) {
      if (isEvaluating) {
        const pulse = 1.0 + Math.sin(elapsed * 5.0) * 0.04;
        centerCoreRef.current.scale.set(pulse, pulse, pulse);
      } else {
        centerCoreRef.current.scale.set(1.0, 1.0, 1.0);
      }
    }
  });

  return (
    <group ref={rootPivotRef} position={[0, 0.04, 0]}>
      <primitive object={scene} />
    </group>
  );
};

// ---------------------------------------------------------------------------
// 6. Loading Indicator inside Three.js
// ---------------------------------------------------------------------------
const InstrumentLoadingIndicator: React.FC = () => (
  <div
    style={{
      width: '100%',
      height: '100%',
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      gap: '8px',
      color: 'var(--text-secondary)',
      fontSize: '11.5px',
      fontFamily: 'var(--font-mono)',
      background: 'radial-gradient(ellipse at 50% 50%, var(--bg-surface-raised) 0%, var(--bg-surface-subdued) 100%)',
    }}
  >
    <div
      style={{
        width: '28px',
        height: '28px',
        borderRadius: '50%',
        border: '2px solid var(--border-default)',
        borderTopColor: 'var(--accent-primary)',
        animation: 'spin 0.9s linear infinite',
      }}
    />
    <span>Loading 3D Inference Instrument Asset...</span>
  </div>
);

// ---------------------------------------------------------------------------
// 7. Exported Component: Clean, Bounded 3D Instrument with Cursor Orbit
// ---------------------------------------------------------------------------
export const SandboxDecisionOrb3D: React.FC<DecisionOrbProps> = (props) => {
  const [webGLSupported] = useState<boolean>(() => checkWebGLSupport());
  const [isPointerOverCanvas, setIsPointerOverCanvas] = useState<boolean>(false);
  const [dragRotation, setDragRotation] = useState<{ x: number; y: number }>({ x: 0, y: 0 });
  const [viewPreset, setViewPreset] = useState<'cursor' | 'isometric' | 'front' | 'side'>('cursor');
  const [zoomLevel, setZoomLevel] = useState<number>(1.0);

  const isDragging = useRef<boolean>(false);
  const dragStart = useRef<{ x: number; y: number }>({ x: 0, y: 0 });
  const dragBase = useRef<{ x: number; y: number }>({ x: 0, y: 0 });

  const prefersReducedMotion =
    typeof window !== 'undefined' &&
    window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  // Drag-to-rotate interaction handlers
  const handlePointerDown = (e: React.PointerEvent) => {
    if (e.button !== 0) return;
    isDragging.current = true;
    dragStart.current = { x: e.clientX, y: e.clientY };
    dragBase.current = { ...dragRotation };
    try {
      (e.currentTarget as HTMLElement).setPointerCapture(e.pointerId);
    } catch {}
  };

  const handlePointerMove = (e: React.PointerEvent) => {
    if (!isDragging.current) return;
    const dx = e.clientX - dragStart.current.x;
    const dy = e.clientY - dragStart.current.y;
    setDragRotation({
      y: dragBase.current.y + dx * 0.009,
      x: Math.max(-0.75, Math.min(0.75, dragBase.current.x + dy * 0.009)),
    });
    if (viewPreset !== 'cursor') {
      setViewPreset('cursor');
    }
  };

  const handlePointerUp = (e: React.PointerEvent) => {
    if (isDragging.current) {
      isDragging.current = false;
      try {
        (e.currentTarget as HTMLElement).releasePointerCapture(e.pointerId);
      } catch {}
    }
  };

  const handleWheel = (e: React.WheelEvent) => {
    const delta = -e.deltaY * 0.001;
    setZoomLevel((prev) => Math.max(0.75, Math.min(2.2, prev + delta)));
  };

  const handleDoubleClick = () => {
    setDragRotation({ x: 0, y: 0 });
    setViewPreset('cursor');
    setZoomLevel(1.0);
  };

  const highlightedCount = props.hasResult ? calculateHighlightedSegments(props.risk) : 0;

  // Preset button styling helper
  const getPresetButtonStyle = (preset: typeof viewPreset) => ({
    background:
      viewPreset === preset && dragRotation.x === 0 && dragRotation.y === 0
        ? 'var(--bg-surface-raised)'
        : 'transparent',
    border: `1px solid ${
      viewPreset === preset && dragRotation.x === 0 && dragRotation.y === 0
        ? 'var(--accent-primary)'
        : 'var(--border-subtle)'
    }`,
    color:
      viewPreset === preset && dragRotation.x === 0 && dragRotation.y === 0
        ? 'var(--accent-primary)'
        : 'var(--text-secondary)',
    borderRadius: 'var(--radius-xs)',
    padding: '2px 7px',
    fontSize: '10px',
    fontFamily: 'var(--font-mono)',
    cursor: 'pointer',
    display: 'flex',
    alignItems: 'center',
    gap: '4px',
    transition: 'all var(--transition-fast)',
  });

  const zoomBtnStyle: React.CSSProperties = {
    background: 'transparent',
    border: '1px solid var(--border-subtle)',
    color: 'var(--text-secondary)',
    borderRadius: 'var(--radius-xs)',
    padding: '2px 6px',
    fontSize: '10px',
    fontFamily: 'var(--font-mono)',
    cursor: 'pointer',
    display: 'flex',
    alignItems: 'center',
    transition: 'all var(--transition-fast)',
  };

  return (
    <div
      className="sandbox-3d-instrument-container"
      style={{
        display: 'flex',
        flexDirection: 'column',
        width: '100%',
        background: 'var(--bg-surface-primary)',
        borderRadius: 'var(--radius-xs)',
        border: '1px solid var(--border-default)',
        overflow: 'hidden',
        boxShadow: '0 8px 24px rgba(0, 0, 0, 0.28)',
      }}
      aria-label="3D Scoring Sandbox Inference Instrument with interactive cursor orbit"
    >
      {/* Top HUD Toolbar: Title + Perspective & Zoom Controls */}
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          padding: '8px 12px',
          background: 'var(--bg-surface-header)',
          borderBottom: '1px solid var(--border-subtle)',
          flexWrap: 'wrap',
          gap: '6px',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <span
            style={{
              width: '7px',
              height: '7px',
              borderRadius: '50%',
              backgroundColor: props.isEvaluating
                ? 'var(--color-manual-review)'
                : props.error
                ? 'var(--color-fraud-alert)'
                : props.hasResult
                ? 'var(--color-routine)'
                : 'var(--text-tertiary)',
              boxShadow: props.hasResult ? '0 0 8px var(--color-routine)' : 'none',
            }}
          />
          <span
            style={{
              fontSize: '11px',
              fontWeight: 800,
              fontFamily: 'var(--font-mono)',
              color: 'var(--text-primary)',
              letterSpacing: '0.04em',
              textTransform: 'uppercase',
            }}
          >
            INFERENCE INSTRUMENT V2
          </span>
          <span style={{ fontSize: '10.5px', color: 'var(--text-tertiary)', fontFamily: 'var(--font-mono)' }}>
            [48-SEG RISK TRACK]
          </span>
        </div>

        {/* Perspective Preset & Zoom Buttons */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '4px', flexWrap: 'wrap' }}>
          <button
            type="button"
            onClick={() => {
              setViewPreset('cursor');
              setDragRotation({ x: 0, y: 0 });
            }}
            style={getPresetButtonStyle('cursor')}
            title="Cursor Track: Instrument tilts smoothly in the direction of your mouse"
          >
            <Compass size={11} />
            <span>Cursor</span>
          </button>

          <button
            type="button"
            onClick={() => {
              setViewPreset('isometric');
              setDragRotation({ x: 0, y: 0 });
            }}
            style={getPresetButtonStyle('isometric')}
            title="Isometric 3/4: View all layers, struts, and aperture depth"
          >
            <Box size={11} />
            <span>Iso</span>
          </button>

          <button
            type="button"
            onClick={() => {
              setViewPreset('front');
              setDragRotation({ x: 0, y: 0 });
            }}
            style={getPresetButtonStyle('front')}
            title="Front Alignment: Orthogonal face alignment"
          >
            <Eye size={11} />
            <span>Front</span>
          </button>

          <button
            type="button"
            onClick={() => {
              setViewPreset('side');
              setDragRotation({ x: 0, y: 0 });
            }}
            style={getPresetButtonStyle('side')}
            title="Side Profile: View thickness, plinth, and cavity depth"
          >
            <Layers size={11} />
            <span>Side</span>
          </button>

          {/* Zoom In & Out */}
          <button
            type="button"
            onClick={() => setZoomLevel((prev) => Math.min(2.2, prev + 0.15))}
            style={zoomBtnStyle}
            title="Zoom In (+) to inspect 48 segments & core hub"
          >
            <ZoomIn size={11} />
          </button>

          <button
            type="button"
            onClick={() => setZoomLevel((prev) => Math.max(0.75, prev - 0.15))}
            style={zoomBtnStyle}
            title="Zoom Out (-)"
          >
            <ZoomOut size={11} />
          </button>

          <button
            type="button"
            onClick={handleDoubleClick}
            style={zoomBtnStyle}
            title="Reset to default orientation and zoom (or double-click canvas)"
          >
            <RotateCcw size={11} />
          </button>
        </div>
      </div>

      {/* Main 3D Canvas / WebGL Fallback Viewport */}
      <div
        style={{
          width: '100%',
          height: '365px',
          position: 'relative',
          background: 'radial-gradient(ellipse at 50% 50%, var(--bg-surface-raised) 0%, var(--bg-surface-subdued) 100%)',
          cursor: isDragging.current ? 'grabbing' : 'grab',
          touchAction: 'none',
        }}
        onPointerEnter={() => setIsPointerOverCanvas(true)}
        onPointerLeave={() => {
          setIsPointerOverCanvas(false);
          if (isDragging.current) isDragging.current = false;
        }}
        onPointerDown={handlePointerDown}
        onPointerMove={handlePointerMove}
        onPointerUp={handlePointerUp}
        onWheel={handleWheel}
        onDoubleClick={handleDoubleClick}
      >
        {/* Floating Interactive Tracking Badge (High Contrast in both Dark and Light Themes) */}
        <div
          style={{
            position: 'absolute',
            top: '10px',
            right: '12px',
            padding: '4px 10px',
            background: 'var(--bg-surface-elevated)',
            border: '1px solid var(--border-default)',
            borderRadius: 'var(--radius-xs)',
            fontSize: '11px',
            fontWeight: 700,
            fontFamily: 'var(--font-mono)',
            color: 'var(--text-primary)',
            boxShadow: '0 2px 8px rgba(0, 0, 0, 0.18)',
            display: 'flex',
            alignItems: 'center',
            gap: '6px',
            pointerEvents: 'none',
            zIndex: 5,
          }}
        >
          <span
            style={{
              width: '6px',
              height: '6px',
              borderRadius: '50%',
              backgroundColor: isPointerOverCanvas ? 'var(--accent-primary)' : 'var(--text-tertiary)',
              boxShadow: isPointerOverCanvas ? '0 0 6px var(--accent-primary)' : 'none',
              transition: 'all var(--transition-fast)',
            }}
          />
          <span
            style={{
              color: 'var(--text-primary)',
              fontWeight: 700,
              letterSpacing: '0.02em',
            }}
          >
            {isPointerOverCanvas
              ? 'Cursor 3D Parallax Active'
              : 'Hover to Tilt • Drag to Orbit'}
          </span>
        </div>

        {!webGLSupported ? (
          <SchematicInstrumentFallback {...props} viewPreset={viewPreset} />
        ) : (
          <Sandbox3DErrorBoundary
            fallback={<SchematicInstrumentFallback {...props} viewPreset={viewPreset} />}
          >
            <Suspense fallback={<InstrumentLoadingIndicator />}>
              <Canvas
                camera={{ fov: 42, position: [0, 0, 5.4] }}
                gl={{
                  antialias: true,
                  alpha: true,
                  powerPreference: 'high-performance',
                }}
                dpr={[1, 1.5]}
                style={{ width: '100%', height: '100%' }}
              >
                <ResponsiveInstrumentCamera />

                {/* Studio 4-Point Lighting */}
                <ambientLight intensity={1.4} color="#FFFFFF" />
                <directionalLight position={[3.5, 5.0, 4.0]} intensity={2.2} color="#FFFFFF" />
                <directionalLight position={[-3.5, -2.0, 3.0]} intensity={1.4} color="#E0F2FE" />
                <directionalLight position={[0.0, 3.5, -3.0]} intensity={1.6} color="#FFFFFF" />
                <directionalLight position={[0.0, -3.5, 2.5]} intensity={1.2} color="#BAE6FD" />

                <SandboxInferenceInstrumentModel
                  {...props}
                  prefersReducedMotion={prefersReducedMotion}
                  isPointerOverCanvas={isPointerOverCanvas}
                  dragRotation={dragRotation}
                  viewPreset={viewPreset}
                  zoomLevel={zoomLevel}
                />
              </Canvas>
            </Suspense>
          </Sandbox3DErrorBoundary>
        )}
      </div>

      {/* Bottom Telemetry Strip */}
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          fontSize: '11px',
          fontFamily: 'var(--font-mono)',
          padding: '7px 14px',
          background: 'var(--bg-surface-elevated)',
          borderTop: '1px solid var(--border-subtle)',
          color: 'var(--text-primary)',
          flexWrap: 'wrap',
          gap: '6px',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          <Compass size={13} style={{ color: 'var(--accent-primary)' }} />
          <span style={{ fontWeight: 600, color: 'var(--text-primary)' }}>
            Hover cursor tilts model &bull; Drag rotates &bull; Wheel zooms
          </span>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <span style={{ color: props.hasResult ? 'var(--text-primary)' : 'var(--text-secondary)', fontWeight: 700 }}>
            {props.hasResult
              ? `${highlightedCount}/48 Segments Lit`
              : props.isEvaluating
              ? 'Evaluating...'
              : 'Standby / Idle'}
          </span>
        </div>
      </div>
    </div>
  );
};
