import React, { useRef, useState, useEffect, useMemo, Suspense, Component, ReactNode, ErrorInfo } from 'react';
import { Canvas, useFrame, useThree, useLoader, ThreeEvent } from '@react-three/fiber';
import * as THREE from 'three';
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js';
import {
  Database,
  Cpu,
  Scale,
  Layers,
  ShieldCheck,
  RotateCcw,
  Sliders,
  BarChart3,
  Eye,
  Compass,
} from 'lucide-react';

// ---------------------------------------------------------------------------
// 1. Verified Model Metadata Architecture
// ---------------------------------------------------------------------------
export interface StageMeta {
  index: number;
  stageNumber: string;
  name: string;
  technicalLabel: string;
  role: string;
  accentColor: string;
  accentDim: string;
  accentTint: string;
  artifactFile: string;
  artifactSha: string;
  algorithm: string;
  keyParams: { label: string; value: string }[];
  metrics: { label: string; value: string }[];
  governanceNote: string;
}

export const PIPELINE_STAGES: StageMeta[] = [
  {
    index: 0,
    stageNumber: '01',
    name: 'Feature Ingestion Bus',
    technicalLabel: 'Schema & Leakage Validator',
    role: 'Deterministic zero-leakage ingestion of 67 transaction features. Enforces strict exclusion of target (isFraud) and temporal tracking identifiers.',
    accentColor: '#68D8CB',
    accentDim: '#005D55',
    accentTint: 'rgba(104, 216, 203, 0.12)',
    artifactFile: 'data/synthetic_smoke_fixture.csv',
    artifactSha: 'da00179ebf37970ec8907d11cfb366d170ddd5b2b41370e881bf92359b7d17de',
    algorithm: 'Deterministic Schema Manifest (67 Features)',
    keyParams: [
      { label: 'Train Partition', value: '6,000 cases (zero lookahead)' },
      { label: 'Calib Partition', value: '1,000 cases' },
      { label: 'Val Partition', value: '1,000 cases' },
      { label: 'Forbidden Target', value: 'isFraud (strictly excluded)' },
      { label: 'Excluded IDs', value: 'TransactionID, TransactionDT' },
    ],
    metrics: [
      { label: 'Feature Columns', value: '67 dimensions' },
      { label: 'Missing Value Mode', value: 'Native NaN propagation' },
      { label: 'Integrity Seal', value: 'SHA-256 Validated' },
    ],
    governanceNote: 'Guarantees zero-lookahead integrity and prevents target leakage into model scoring representations.',
  },
  {
    index: 1,
    stageNumber: '02',
    name: 'Primary Estimator',
    technicalLabel: 'HistGradientBoostingClassifier',
    role: 'Histogram-based gradient boosted decision ensemble mapping non-linear tabular interactions into continuous decision margins.',
    accentColor: '#7DAAFF',
    accentDim: '#1D3B7A',
    accentTint: 'rgba(125, 170, 255, 0.12)',
    artifactFile: 'models/artifacts/hgb_base.joblib',
    artifactSha: 'b20aa6fa375303741338bca971098195f5ae72d5e1fee3882e0553172fa3b70f',
    algorithm: 'sklearn.ensemble.HistGradientBoostingClassifier',
    keyParams: [
      { label: 'Boosting Iterations', value: '50 boosting trees' },
      { label: 'Min Samples Leaf', value: '20' },
      { label: 'Histogram Bins', value: '255 native bins' },
      { label: 'Loss Function', value: 'Log-loss (cross-entropy)' },
      { label: 'Random Seed', value: 'Seed 11 (deterministic)' },
    ],
    metrics: [
      { label: 'Validation ROC-AUC', value: '0.5836' },
      { label: 'Raw Brier Score', value: '0.0465' },
      { label: 'Training Latency', value: '3,401.4 ms' },
    ],
    governanceNote: 'Primary decision margin producer. Model weights and structure are frozen and cryptographically hashed.',
  },
  {
    index: 2,
    stageNumber: '03',
    name: 'Sigmoid Calibrator',
    technicalLabel: 'Platt Scaling (Logistic CV)',
    role: 'Univariate Platt logistic calibration mapping boosting logits into strictly monotonic, posterior empirical probabilities p in [0.0, 1.0].',
    accentColor: '#68D8CB',
    accentDim: '#005D55',
    accentTint: 'rgba(104, 216, 203, 0.12)',
    artifactFile: 'models/artifacts/calibrator_sigmoid.joblib',
    artifactSha: '00c519243765bfd7844ed877cec0dd3caa2e45310aa47e457647680c8b787fb4',
    algorithm: 'CalibratedClassifierCV(method="sigmoid")',
    keyParams: [
      { label: 'Calibration Split', value: '1,000 held-out rows' },
      { label: 'Scaling Method', value: 'Platt logistic sigmoid' },
      { label: 'Monotonicity', value: 'Strictly order-preserving' },
      { label: 'Alert Threshold (t_alert)', value: '0.084705 (8.47%)' },
      { label: 'Review Threshold (t_review)', value: '0.071002 (7.10%)' },
    ],
    metrics: [
      { label: 'Expected Calib Error (ECE)', value: '0.0077 (reduced from 0.0272)' },
      { label: 'Calibrated Brier Score', value: '0.0456' },
      { label: 'Validation ROC-AUC', value: '0.5836 (preserved)' },
    ],
    governanceNote: 'Aligns raw margins with empirical fraud prevalence so alert thresholds correspond to auditable risk levels.',
  },
  {
    index: 3,
    stageNumber: '04',
    name: 'Disagreement Engine',
    technicalLabel: 'RankResidualizer (u₂)',
    role: '3-member shadow ensemble (seeds 11, 22, 33) with rank-conditioned variance residualization to isolate epistemic shift from risk rank.',
    accentColor: '#B4A0F8',
    accentDim: '#442C82',
    accentTint: 'rgba(180, 160, 248, 0.12)',
    artifactFile: 'models/artifacts/residualizer_u2.joblib',
    artifactSha: '10cadc14aa4f8781020079c9f23c030beb392a294066b56de18d4c972ee784a4',
    algorithm: '3-Member Ensemble + RankResidualizer',
    keyParams: [
      { label: 'Ensemble Seeds', value: 'Seeds 11, 22, 33 (3 models)' },
      { label: 'Raw Disagreement', value: 'u = std(member_probabilities)' },
      { label: 'Residual Formula', value: 'u2 = rank(u) - hat{rank}(u)' },
      { label: 'Epistemic Threshold (u_th)', value: '0.526773' },
      { label: 'Decorrelation vs Risk', value: '0.3901 decorrelation' },
    ],
    metrics: [
      { label: 'Spearman corr(p, u2)', value: '0.0609 (uncoupled)' },
      { label: 'Epistemic Range', value: 'u2 in [-0.68, +0.60]' },
      { label: 'Shift Scenarios', value: 'S1, S2, S3 robust' },
    ],
    governanceNote: 'Detects covariate perturbation and distribution shifts where models diverge, escalating cases to review.',
  },
];

const STAGE_NODE_NAMES = [
  'stage_01_input_validation',
  'stage_02_model_inference',
  'stage_03_sigmoid_calibration',
  'stage_04_disagreement_residualizer',
];

// ---------------------------------------------------------------------------
// 2. WebGL Error Boundary & Diagnostic Detection
// ---------------------------------------------------------------------------
interface WebGLErrorBoundaryProps {
  children: ReactNode;
  fallback: (error: Error) => ReactNode;
}

interface WebGLErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
}

class WebGLErrorBoundary extends Component<WebGLErrorBoundaryProps, WebGLErrorBoundaryState> {
  constructor(props: WebGLErrorBoundaryProps) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): WebGLErrorBoundaryState {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.warn('[ModelCard3DVisualizer] WebGL execution trapped by boundary:', error, errorInfo);
  }

  render() {
    if (this.state.hasError && this.state.error) {
      return this.props.fallback(this.state.error);
    }
    return this.props.children;
  }
}

function checkWebGLSupport(): boolean {
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
// 3. Responsive Orthographic Camera Controller
// ---------------------------------------------------------------------------
function ResponsiveOrthoCamera() {
  const { camera, size } = useThree();

  useEffect(() => {
    const aspect = size.width / Math.max(size.height, 1);
    let halfWidth = 8.0;
    let halfHeight = halfWidth / aspect;

    // Ensure the 1.8-unit tall assembly is never cropped vertically
    if (halfHeight < 1.35) {
      halfHeight = 1.35;
      halfWidth = halfHeight * aspect;
    }

    const ortho = camera as THREE.OrthographicCamera;
    ortho.left = -halfWidth;
    ortho.right = halfWidth;
    ortho.top = halfHeight;
    ortho.bottom = -halfHeight;
    ortho.near = 0.1;
    ortho.far = 100;
    ortho.position.set(0, 2.2, 9.0);
    ortho.lookAt(0, 0, 0);
    ortho.updateProjectionMatrix();
  }, [camera, size]);

  return null;
}

// ---------------------------------------------------------------------------
// 4. Genuine GLTF Pipeline Model with Dynamic Cursor Direction Tilt
// ---------------------------------------------------------------------------
interface PipelineGLBModelProps {
  hoveredStage: number | null;
  selectedStage: number | null;
  onHoverStage: (idx: number | null) => void;
  onSelectStage: (idx: number) => void;
  prefersReducedMotion: boolean;
  isPointerOverCanvas: boolean;
  dragRotation: { x: number; y: number };
  viewPreset: 'cursor' | 'isometric' | 'front' | 'side';
  zoomLevel: number;
}

const PipelineGLBModel: React.FC<PipelineGLBModelProps> = ({
  hoveredStage,
  selectedStage,
  onHoverStage,
  onSelectStage,
  prefersReducedMotion,
  isPointerOverCanvas,
  dragRotation,
  viewPreset,
  zoomLevel,
}) => {
  const gltf = useLoader(GLTFLoader, '/models/model-pipeline.glb');

  // Deep-clone scene so transform mutations never leak across mounts
  const scene = useMemo(() => {
    const cloned = gltf.scene.clone(true);
    cloned.traverse((node) => {
      if ((node as THREE.Mesh).isMesh) {
        const mesh = node as THREE.Mesh;
        mesh.castShadow = false;
        mesh.receiveShadow = false;
      }
    });
    return cloned;
  }, [gltf]);

  const rootPivotRef = useRef<THREE.Group>(null);
  const stageRefs = useRef<(THREE.Object3D | null)[]>([null, null, null, null]);

  useEffect(() => {
    stageRefs.current = STAGE_NODE_NAMES.map((name) => scene.getObjectByName(name) || null);
  }, [scene]);

  // Raycasting helper to resolve which stage group was targeted
  const resolveStageIndex = (object: THREE.Object3D | null): number | null => {
    let curr: THREE.Object3D | null = object;
    while (curr) {
      const idx = STAGE_NODE_NAMES.indexOf(curr.name);
      if (idx !== -1) return idx;
      curr = curr.parent;
    }
    return null;
  };

  // Dynamic Cursor Direction & 3D Parallax Tracking in useFrame
  useFrame((state, delta) => {
    // 1. Master Assembly Rotation (Follows cursor direction in all angles)
    if (rootPivotRef.current) {
      let targetRotX = 0;
      let targetRotY = 0;

      if (viewPreset === 'isometric') {
        targetRotX = 0.38; // ~22 deg down angle
        targetRotY = -0.52; // ~-30 deg angled
      } else if (viewPreset === 'side') {
        targetRotX = 0.12;
        targetRotY = -1.22; // ~-70 deg side view
      } else if (viewPreset === 'front') {
        targetRotX = 0.0;
        targetRotY = 0.0;
      } else {
        // 'cursor' mode: Smoothly tilts and pivots in the exact direction of the user's cursor
        // Moving mouse right -> turns right; moving left -> turns left
        // Moving mouse up -> tilts forward (looks down into layers); moving down -> tilts backward
        const mouseInfluenceX = isPointerOverCanvas ? -state.pointer.y * 0.44 : 0;
        const mouseInfluenceY = isPointerOverCanvas ? state.pointer.x * 0.58 : 0;
        targetRotX = mouseInfluenceX + dragRotation.x;
        targetRotY = mouseInfluenceY + dragRotation.y;
      }

      if (prefersReducedMotion) {
        rootPivotRef.current.rotation.x = targetRotX;
        rootPivotRef.current.rotation.y = targetRotY;
        rootPivotRef.current.scale.setScalar(zoomLevel);
      } else {
        const lerpSpeed = Math.min(delta * 8, 0.25);
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

    // 2. Individual Stage Tactile Elevation & Scale
    for (let i = 0; i < 4; i++) {
      const stageObj = stageRefs.current[i];
      if (!stageObj) continue;

      const isSelected = selectedStage === i;
      const isHovered = hoveredStage === i;

      const targetY = isSelected ? 0.16 : isHovered ? 0.08 : 0.0;
      const targetScale = isSelected ? 1.04 : isHovered ? 1.02 : 1.0;

      if (prefersReducedMotion) {
        stageObj.position.y = targetY;
        stageObj.scale.setScalar(targetScale);
      } else {
        const lerpFactor = Math.min(delta * 12, 0.35);
        stageObj.position.y += (targetY - stageObj.position.y) * lerpFactor;
        const curScale = stageObj.scale.x;
        const nextScale = curScale + (targetScale - curScale) * lerpFactor;
        stageObj.scale.setScalar(nextScale);
      }
    }
  });

  return (
    <group ref={rootPivotRef}>
      <primitive
        object={scene}
        onPointerOver={(e: ThreeEvent<PointerEvent>) => {
          e.stopPropagation();
          const idx = resolveStageIndex(e.object);
          if (idx !== null) {
            onHoverStage(idx);
            document.body.style.cursor = 'pointer';
          }
        }}
        onPointerOut={(e: ThreeEvent<PointerEvent>) => {
          e.stopPropagation();
          onHoverStage(null);
          document.body.style.cursor = 'auto';
        }}
        onClick={(e: ThreeEvent<MouseEvent>) => {
          e.stopPropagation();
          const idx = resolveStageIndex(e.object);
          if (idx !== null) {
            onSelectStage(idx);
          }
        }}
      />
    </group>
  );
};

// ---------------------------------------------------------------------------
// 5. Loading Skeleton & 2D Diagnostic Fallback
// ---------------------------------------------------------------------------
const PipelineLoadingFallback: React.FC = () => (
  <div
    style={{
      width: '100%',
      height: '100%',
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      gap: '10px',
      color: 'var(--text-secondary)',
      fontSize: '12px',
      fontFamily: 'var(--font-mono)',
      background: 'radial-gradient(ellipse at 50% 50%, var(--bg-surface-elevated) 0%, var(--bg-surface-subdued) 100%)',
    }}
  >
    <div
      style={{
        width: '32px',
        height: '32px',
        borderRadius: '50%',
        border: '2px solid var(--border-default)',
        borderTopColor: 'var(--accent-primary)',
        animation: 'spin 0.9s linear infinite',
      }}
    />
    <span>Loading Precision 3D Model Pipeline Assembly...</span>
  </div>
);

interface SchematicFallbackProps {
  hoveredStage: number | null;
  selectedStage: number | null;
  onSelectStage: (idx: number) => void;
  onHoverStage: (idx: number | null) => void;
}

const SchematicFallback: React.FC<SchematicFallbackProps> = ({
  hoveredStage,
  selectedStage,
  onSelectStage,
  onHoverStage,
}) => (
  <div
    style={{
      width: '100%',
      height: '100%',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-around',
      padding: '16px 24px',
      background: 'var(--bg-surface-subdued)',
      borderRadius: 'var(--radius-xs)',
    }}
  >
    {PIPELINE_STAGES.map((s, idx) => {
      const isSelected = selectedStage === idx;
      const isHovered = hoveredStage === idx;
      return (
        <button
          key={s.stageNumber}
          type="button"
          onClick={() => onSelectStage(idx)}
          onMouseEnter={() => onHoverStage(idx)}
          onMouseLeave={() => onHoverStage(null)}
          style={{
            flex: 1,
            margin: '0 8px',
            padding: '16px 12px',
            background: isSelected ? 'var(--bg-surface-raised)' : 'var(--bg-surface-primary)',
            border: `1px solid ${isSelected ? s.accentColor : isHovered ? 'var(--border-active)' : 'var(--border-default)'}`,
            borderRadius: 'var(--radius-sm)',
            cursor: 'pointer',
            textAlign: 'center',
            color: 'var(--text-primary)',
          }}
        >
          <div style={{ fontFamily: 'var(--font-mono)', fontSize: '11px', color: s.accentColor, fontWeight: 700 }}>
            STAGE {s.stageNumber}
          </div>
          <div style={{ fontSize: '13px', fontWeight: 700, margin: '4px 0' }}>{s.name}</div>
          <div style={{ fontSize: '11px', color: 'var(--text-secondary)', fontFamily: 'var(--font-mono)' }}>
            {s.technicalLabel}
          </div>
        </button>
      );
    })}
  </div>
);

// ---------------------------------------------------------------------------
// 6. Primary Exported Component: Interactive 3D Model Card Visualizer
// ---------------------------------------------------------------------------
interface ModelCard3DVisualizerProps {
  onSelectStage?: (stageIndex: number) => void;
}

export const ModelCard3DVisualizer: React.FC<ModelCard3DVisualizerProps> = ({ onSelectStage }) => {
  const [hoveredStage, setHoveredStage] = useState<number | null>(null);
  const [selectedStage, setSelectedStage] = useState<number | null>(null);
  const [webGLSupported] = useState<boolean>(() => checkWebGLSupport());

  // Interactive 3D view control state
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

  const handleSelect = (idx: number) => {
    setSelectedStage((prev) => (prev === idx ? null : idx));
    if (onSelectStage) {
      onSelectStage(idx);
    }
  };

  const handleReset = () => {
    setSelectedStage(null);
    setHoveredStage(null);
    setDragRotation({ x: 0, y: 0 });
    setViewPreset('cursor');
    setZoomLevel(1.0);
  };

  // Drag-to-rotate interaction handlers
  const handlePointerDown = (e: React.PointerEvent) => {
    if (e.button !== 0) return; // Only primary button
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
      x: Math.max(-0.65, Math.min(0.65, dragBase.current.x + dy * 0.009)),
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
    // Zoom inspection with mouse wheel (clamped between 0.8x and 1.8x)
    const delta = -e.deltaY * 0.001;
    setZoomLevel((prev) => Math.max(0.8, Math.min(1.8, prev + delta)));
  };

  const handleDoubleClick = () => {
    // Double click resets view to canonical alignment
    setDragRotation({ x: 0, y: 0 });
    setViewPreset('cursor');
    setZoomLevel(1.0);
  };

  const activeStage = selectedStage !== null ? PIPELINE_STAGES[selectedStage] : null;

  // Preset button styling helper
  const getPresetButtonStyle = (preset: typeof viewPreset) => ({
    background: viewPreset === preset && dragRotation.x === 0 && dragRotation.y === 0
      ? 'var(--bg-surface-raised)'
      : 'transparent',
    border: `1px solid ${viewPreset === preset && dragRotation.x === 0 && dragRotation.y === 0 ? 'var(--accent-primary)' : 'var(--border-subtle)'}`,
    color: viewPreset === preset && dragRotation.x === 0 && dragRotation.y === 0 ? 'var(--accent-primary)' : 'var(--text-secondary)',
    borderRadius: 'var(--radius-xs)',
    padding: '3px 8px',
    fontSize: '10.5px',
    fontFamily: 'var(--font-mono)',
    cursor: 'pointer',
    display: 'flex',
    alignItems: 'center',
    gap: '4px',
    transition: 'all var(--transition-fast)',
  });

  return (
    <div
      className="model-card-3d-visualizer"
      style={{
        display: 'flex',
        flexDirection: 'column',
        gap: 'var(--space-3)',
        width: '100%',
      }}
    >
      {/* 1. Cockpit Card: 3D Assembly Viewport + Aligned Labels */}
      <div
        className="sg-card"
        style={{
          padding: '16px 20px',
          display: 'flex',
          flexDirection: 'column',
          gap: '12px',
          position: 'relative',
          backgroundColor: 'var(--bg-surface-primary)',
          borderRadius: 'var(--radius-sm)',
          border: '1px solid var(--border-default)',
        }}
      >
        {/* Top Header HUD with View Preset Switchers */}
        <div
          style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            fontSize: '11.5px',
            fontFamily: 'var(--font-mono)',
            paddingBottom: '10px',
            borderBottom: '1px solid var(--border-subtle)',
            flexWrap: 'wrap',
            gap: '8px',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span style={{ fontWeight: 700, color: 'var(--accent-primary)', letterSpacing: '0.04em' }}>
              MODEL INFERENCE PIPELINE
            </span>
            <span style={{ color: 'var(--text-tertiary)' }}>&bull;</span>
            <span style={{ color: 'var(--text-secondary)' }}>
              Interactive 3D Structure Viewer
            </span>
          </div>

          {/* View Perspective Controls (Cursor Track / Isometric / Front / Side) */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
              <button
                type="button"
                onClick={() => { setViewPreset('cursor'); setDragRotation({ x: 0, y: 0 }); }}
                style={getPresetButtonStyle('cursor')}
                title="Cursor Track: Assembly tilts dynamically in the direction of your mouse"
              >
                <Compass size={11} />
                <span>Cursor Track</span>
              </button>

              <button
                type="button"
                onClick={() => { setViewPreset('isometric'); setDragRotation({ x: 0, y: 0 }); }}
                style={getPresetButtonStyle('isometric')}
                title="Isometric 3D: Reveals stacked compute blades and hollow aperture depth"
              >
                <Eye size={11} />
                <span>Isometric 3D</span>
              </button>

              <button
                type="button"
                onClick={() => { setViewPreset('front'); setDragRotation({ x: 0, y: 0 }); }}
                style={getPresetButtonStyle('front')}
                title="Front Align: Aligns exactly with the 4 cards below"
              >
                <span>Front Align</span>
              </button>

              <button
                type="button"
                onClick={() => { setViewPreset('side'); setDragRotation({ x: 0, y: 0 }); }}
                style={getPresetButtonStyle('side')}
                title="Side Profile: View longitudinal rails and gimbal rings from profile"
              >
                <span>Side View</span>
              </button>
            </div>

            {/* Reset View Button */}
            {(selectedStage !== null || dragRotation.x !== 0 || dragRotation.y !== 0 || viewPreset !== 'cursor' || zoomLevel !== 1.0) && (
              <button
                type="button"
                onClick={handleReset}
                style={{
                  background: 'transparent',
                  border: '1px solid var(--border-default)',
                  color: 'var(--accent-primary)',
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '4px',
                  fontSize: '11px',
                  fontFamily: 'var(--font-mono)',
                  padding: '3px 8px',
                  borderRadius: 'var(--radius-xs)',
                  transition: 'background var(--transition-fast)',
                }}
                aria-label="Reset stage selection and 3D camera orientation"
              >
                <RotateCcw size={11} />
                <span>Reset View</span>
              </button>
            )}
          </div>
        </div>

        {/* 3D WebGL Canvas Viewport with Cursor Tracking & Orbit Control */}
        <div
          onPointerEnter={() => setIsPointerOverCanvas(true)}
          onPointerLeave={(e) => {
            setIsPointerOverCanvas(false);
            handlePointerUp(e);
          }}
          onPointerDown={handlePointerDown}
          onPointerMove={handlePointerMove}
          onPointerUp={handlePointerUp}
          onWheel={handleWheel}
          onDoubleClick={handleDoubleClick}
          style={{
            width: '100%',
            height: '240px',
            position: 'relative',
            borderRadius: 'var(--radius-xs)',
            overflow: 'hidden',
            background: 'radial-gradient(ellipse at 50% 50%, var(--bg-surface-elevated) 0%, var(--bg-surface-subdued) 100%)',
            border: '1px solid var(--border-subtle)',
            cursor: isDragging.current ? 'grabbing' : 'grab',
            touchAction: 'none',
          }}
          title="Move cursor over pipeline to tilt view in cursor direction • Drag to rotate 360° • Scroll to zoom • Double-click to reset"
        >
          {/* Active 3D Cursor Tracking Indicator Badge */}
          <div
            style={{
              position: 'absolute',
              top: '8px',
              right: '12px',
              padding: '4px 10px',
              background: 'var(--bg-surface-elevated)',
              border: '1px solid var(--border-default)',
              borderRadius: 'var(--radius-xs)',
              fontSize: '11px',
              fontWeight: 600,
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
                ? 'Cursor 3D Direction Tracking'
                : 'Hover to Tilt • Drag to Orbit'}
            </span>
          </div>

          {webGLSupported ? (
            <WebGLErrorBoundary
              fallback={(_err) => (
                <SchematicFallback
                  hoveredStage={hoveredStage}
                  selectedStage={selectedStage}
                  onSelectStage={handleSelect}
                  onHoverStage={setHoveredStage}
                />
              )}
            >
              <Suspense fallback={<PipelineLoadingFallback />}>
                <Canvas
                  orthographic
                  camera={{ position: [0, 2.2, 9.0], zoom: 1 }}
                  dpr={[1, 1.5]}
                  gl={{ antialias: true, alpha: true, powerPreference: 'high-performance' }}
                  style={{ width: '100%', height: '100%' }}
                >
                  <ResponsiveOrthoCamera />

                  {/* Balanced 3-Point Studio Lighting */}
                  <ambientLight color="#BAC8D3" intensity={1.3} />
                  <directionalLight position={[5, 8, 6]} intensity={2.2} color="#FFFFFF" />
                  <directionalLight position={[-6, 5, 4]} intensity={1.4} color="#D6E4F0" />
                  <directionalLight position={[0, 6, -5]} intensity={1.5} color="#E8F0F8" />

                  {/* 3D Assembly Model with Dynamic Cursor Rotation */}
                  <PipelineGLBModel
                    hoveredStage={hoveredStage}
                    selectedStage={selectedStage}
                    onHoverStage={setHoveredStage}
                    onSelectStage={handleSelect}
                    prefersReducedMotion={Boolean(prefersReducedMotion)}
                    isPointerOverCanvas={isPointerOverCanvas}
                    dragRotation={dragRotation}
                    viewPreset={viewPreset}
                    zoomLevel={zoomLevel}
                  />
                </Canvas>
              </Suspense>
            </WebGLErrorBoundary>
          ) : (
            <SchematicFallback
              hoveredStage={hoveredStage}
              selectedStage={selectedStage}
              onSelectStage={handleSelect}
              onHoverStage={setHoveredStage}
            />
          )}
        </div>

        {/* Interstage Flow Track (Visual Alignment Bridge between 3D Model and HTML Cards) */}
        <div className="pipeline-flow-track" aria-hidden="true">
          <svg width="100%" height="20" style={{ overflow: 'visible' }}>
            {/* Guide line linking the 4 stage centers */}
            <line
              x1="12.5%"
              y1="10"
              x2="87.5%"
              y2="10"
              stroke="var(--border-default)"
              strokeWidth="2"
              strokeDasharray="4 4"
            />

            {/* Conduit 1 -> 2 */}
            <line x1="16%" y1="10" x2="34%" y2="10" stroke="#68D8CB" strokeWidth="2.5" />
            <polygon points="34%,7 37%,10 34%,13" fill="#68D8CB" />

            {/* Conduit 2 -> 3 */}
            <line x1="41%" y1="10" x2="59%" y2="10" stroke="#7DAAFF" strokeWidth="2.5" />
            <polygon points="59%,7 62%,10 59%,13" fill="#7DAAFF" />

            {/* Conduit 3 -> 4 */}
            <line x1="66%" y1="10" x2="84%" y2="10" stroke="#B4A0F8" strokeWidth="2.5" />
            <polygon points="84%,7 87%,10 84%,13" fill="#B4A0F8" />

            {/* Stage Center Node Indicator Markers */}
            <circle cx="12.5%" cy="10" r="4.5" fill="#68D8CB" />
            <circle cx="37.5%" cy="10" r="4.5" fill="#7DAAFF" />
            <circle cx="62.5%" cy="10" r="4.5" fill="#68D8CB" />
            <circle cx="87.5%" cy="10" r="4.5" fill="#B4A0F8" />
          </svg>
        </div>

        {/* Four Responsive Aligned Stage Cards (Directly beneath matching 3D objects) */}
        <div className="pipeline-stages-grid" role="region" aria-label="Pipeline Stages Selection Grid">
          {PIPELINE_STAGES.map((stage) => {
            const isSelected = selectedStage === stage.index;
            const isHovered = hoveredStage === stage.index;
            return (
              <button
                key={stage.stageNumber}
                type="button"
                onClick={() => handleSelect(stage.index)}
                onMouseEnter={() => setHoveredStage(stage.index)}
                onMouseLeave={() => setHoveredStage(null)}
                onFocus={() => setHoveredStage(stage.index)}
                onBlur={() => setHoveredStage(null)}
                className="stage-selector-card"
                style={{
                  background: isSelected
                    ? 'var(--bg-surface-raised)'
                    : isHovered
                    ? 'var(--bg-surface-subdued)'
                    : 'var(--bg-surface-primary)',
                  border: isSelected
                    ? `2px solid ${stage.accentColor}`
                    : isHovered
                    ? '1px solid var(--border-active)'
                    : '1px solid var(--border-default)',
                  boxShadow: isSelected
                    ? `0 0 16px ${stage.accentColor}33, 0 4px 16px rgba(0, 0, 0, 0.25)`
                    : 'none',
                }}
                aria-pressed={isSelected}
                aria-label={`Inspect Stage ${stage.stageNumber}: ${stage.name}`}
              >
                {/* Top Row: Stage Indicator & Status Beacon */}
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <span
                    style={{
                      fontFamily: 'var(--font-mono)',
                      fontSize: '11px',
                      fontWeight: 800,
                      color: isSelected ? stage.accentColor : 'var(--text-secondary)',
                      letterSpacing: '0.04em',
                    }}
                  >
                    STAGE {stage.stageNumber}
                  </span>
                  <div
                    style={{
                      width: '8px',
                      height: '8px',
                      borderRadius: '50%',
                      backgroundColor: isSelected ? stage.accentColor : 'var(--border-active)',
                      boxShadow: isSelected ? `0 0 8px ${stage.accentColor}` : 'none',
                      transition: 'background var(--transition-fast), box-shadow var(--transition-fast)',
                    }}
                  />
                </div>

                {/* Main Text: Stage Title & Icon */}
                <div
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '8px',
                    fontSize: '14px',
                    fontWeight: 700,
                    color: 'var(--text-primary)',
                    letterSpacing: '-0.01em',
                    whiteSpace: 'nowrap',
                    overflow: 'hidden',
                    textOverflow: 'ellipsis',
                  }}
                >
                  {stage.index === 0 && <Database size={15} style={{ color: stage.accentColor, flexShrink: 0 }} />}
                  {stage.index === 1 && <Cpu size={15} style={{ color: stage.accentColor, flexShrink: 0 }} />}
                  {stage.index === 2 && <Scale size={15} style={{ color: stage.accentColor, flexShrink: 0 }} />}
                  {stage.index === 3 && <Layers size={15} style={{ color: stage.accentColor, flexShrink: 0 }} />}
                  <span>{stage.name}</span>
                </div>

                {/* Subtitle: Technical Architecture Label */}
                <div
                  style={{
                    fontFamily: 'var(--font-mono)',
                    fontSize: '11px',
                    color: 'var(--text-secondary)',
                    fontWeight: 500,
                    whiteSpace: 'nowrap',
                    overflow: 'hidden',
                    textOverflow: 'ellipsis',
                  }}
                >
                  {stage.technicalLabel}
                </div>

                {/* Role Snippet */}
                <div
                  style={{
                    fontSize: '11.5px',
                    color: 'var(--text-tertiary)',
                    lineHeight: 1.4,
                    display: '-webkit-box',
                    WebkitLineClamp: 2,
                    WebkitBoxOrient: 'vertical',
                    overflow: 'hidden',
                  }}
                >
                  {stage.role}
                </div>
              </button>
            );
          })}
        </div>
      </div>

      {/* 2. Structured Stage Inspection Drawer (Appears cleanly below cards) */}
      {activeStage && (
        <div
          className="sg-card animate-fade-in"
          style={{
            padding: '20px 24px',
            borderLeft: `4px solid ${activeStage.accentColor}`,
            backgroundColor: 'var(--bg-surface-raised)',
            borderRadius: 'var(--radius-sm)',
            display: 'flex',
            flexDirection: 'column',
            gap: '16px',
            border: '1px solid var(--border-default)',
            borderLeftWidth: '4px',
          }}
          role="region"
          aria-live="polite"
          aria-label={`Detailed specifications for Stage ${activeStage.stageNumber}`}
        >
          {/* Header Row */}
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '12px' }}>
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '6px' }}>
                <span
                  style={{
                    fontFamily: 'var(--font-mono)',
                    fontSize: '11px',
                    fontWeight: 700,
                    padding: '3px 8px',
                    borderRadius: 'var(--radius-xs)',
                    backgroundColor: 'var(--bg-surface-subdued)',
                    border: `1px solid ${activeStage.accentColor}55`,
                    color: activeStage.accentColor,
                    letterSpacing: '0.04em',
                  }}
                >
                  STAGE {activeStage.stageNumber} SPECIFICATION
                </span>
                <span style={{ fontFamily: 'var(--font-mono)', fontSize: '12px', color: 'var(--text-secondary)' }}>
                  {activeStage.algorithm}
                </span>
              </div>
              <h3 style={{ margin: 0, fontSize: '18px', fontWeight: 800, color: 'var(--text-primary)', letterSpacing: '-0.01em' }}>
                {activeStage.name} &bull; {activeStage.technicalLabel}
              </h3>
              <p style={{ margin: '6px 0 0 0', fontSize: '13.5px', color: 'var(--text-secondary)', maxWidth: '860px', lineHeight: 1.55 }}>
                {activeStage.role}
              </p>
            </div>

            <button
              type="button"
              onClick={() => setSelectedStage(null)}
              className="sg-btn sg-btn-secondary"
              style={{ fontSize: '12px', padding: '6px 14px', cursor: 'pointer' }}
            >
              Close Inspector
            </button>
          </div>

          {/* Parameters & Metrics Grid */}
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))',
              gap: '14px',
            }}
          >
            {/* Parameters Column */}
            <div
              style={{
                background: 'var(--bg-surface-primary)',
                padding: '14px 16px',
                borderRadius: 'var(--radius-xs)',
                border: '1px solid var(--border-subtle)',
              }}
            >
              <div
                style={{
                  fontSize: '11px',
                  fontFamily: 'var(--font-mono)',
                  color: 'var(--text-tertiary)',
                  textTransform: 'uppercase',
                  marginBottom: '10px',
                  fontWeight: 700,
                  letterSpacing: '0.05em',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '6px',
                }}
              >
                <Sliders size={13} style={{ color: activeStage.accentColor }} />
                <span>Verified Architecture Parameters</span>
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                {activeStage.keyParams.map((p) => (
                  <div key={p.label} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', fontSize: '13px', gap: '8px' }}>
                    <span style={{ color: 'var(--text-secondary)', fontWeight: 500 }}>{p.label}:</span>
                    <span style={{ fontFamily: 'var(--font-mono)', color: 'var(--text-primary)', fontWeight: 700, textAlign: 'right' }}>
                      {p.value}
                    </span>
                  </div>
                ))}
              </div>
            </div>

            {/* Metrics Column */}
            <div
              style={{
                background: 'var(--bg-surface-primary)',
                padding: '14px 16px',
                borderRadius: 'var(--radius-xs)',
                border: '1px solid var(--border-subtle)',
              }}
            >
              <div
                style={{
                  fontSize: '11px',
                  fontFamily: 'var(--font-mono)',
                  color: 'var(--text-tertiary)',
                  textTransform: 'uppercase',
                  marginBottom: '10px',
                  fontWeight: 700,
                  letterSpacing: '0.05em',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '6px',
                }}
              >
                <BarChart3 size={13} style={{ color: activeStage.accentColor }} />
                <span>Deterministic Validation Metrics</span>
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                {activeStage.metrics.map((m) => (
                  <div key={m.label} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', fontSize: '13px', gap: '8px' }}>
                    <span style={{ color: 'var(--text-secondary)', fontWeight: 500 }}>{m.label}:</span>
                    <span style={{ fontFamily: 'var(--font-mono)', color: activeStage.accentColor, fontWeight: 800, textAlign: 'right' }}>
                      {m.value}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Cryptographic Lineage & Governance Bar */}
          <div
            style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              flexWrap: 'wrap',
              gap: '12px',
              fontSize: '12px',
              fontFamily: 'var(--font-mono)',
              padding: '10px 16px',
              background: 'var(--bg-surface-subdued)',
              borderRadius: 'var(--radius-xs)',
              border: '1px solid var(--border-subtle)',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <ShieldCheck size={16} style={{ color: activeStage.accentColor }} />
              <span style={{ color: 'var(--text-secondary)', fontWeight: 500 }}>Artifact:</span>
              <span style={{ color: 'var(--text-primary)', fontWeight: 700 }}>{activeStage.artifactFile}</span>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <span style={{ color: 'var(--text-tertiary)' }}>SHA-256:</span>
              <span style={{ color: 'var(--text-secondary)', fontWeight: 600 }}>
                {activeStage.artifactSha}
              </span>
            </div>
          </div>

          {/* Governance Assurance Note */}
          <div
            style={{
              fontSize: '12px',
              color: 'var(--text-secondary)',
              lineHeight: 1.5,
              padding: '8px 12px',
              borderLeft: '2px solid var(--border-active)',
              background: 'var(--bg-surface-primary)',
              borderRadius: 'var(--radius-xs)',
            }}
          >
            <span style={{ fontWeight: 700, color: 'var(--text-primary)' }}>Governance Assurance: </span>
            {activeStage.governanceNote}
          </div>
        </div>
      )}
    </div>
  );
};
