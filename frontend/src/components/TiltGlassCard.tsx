import React, { useState, useRef, useCallback } from 'react';
import { X, Sparkles, Activity, Info } from 'lucide-react';

export interface TiltGlassCardDetail {
  title: string;
  subtitle: string;
  category: string;
  icon: React.ReactNode;
  accentColor: string;
  shortDesc: string;
  formula?: string;
  parameters: Array<{ label: string; value: string }>;
  telemetryNotes: string[];
  partitionInfo?: string;
}

interface TiltGlassCardProps {
  detail: TiltGlassCardDetail;
  className?: string;
  style?: React.CSSProperties;
}

export const TiltGlassCard: React.FC<TiltGlassCardProps> = ({
  detail,
  className = '',
  style = {},
}) => {
  const [isOpen, setIsOpen] = useState<boolean>(false);
  const [tilt, setTilt] = useState<{ x: number; y: number; active: boolean }>({
    x: 0,
    y: 0,
    active: false,
  });
  const [mousePos, setMousePos] = useState<{ x: number; y: number }>({ x: 0, y: 0 });
  const cardRef = useRef<HTMLDivElement>(null);

  const handleMouseMove = useCallback((e: React.MouseEvent<HTMLDivElement>) => {
    if (!cardRef.current) return;
    const rect = cardRef.current.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;

    const centerX = rect.width / 2;
    const centerY = rect.height / 2;

    // Maximum tilt angles in degrees
    const maxTilt = 10;
    const rotateY = ((x - centerX) / centerX) * maxTilt;
    const rotateX = -((y - centerY) / centerY) * maxTilt;

    setTilt({ x: rotateX, y: rotateY, active: true });
    setMousePos({ x, y });
  }, []);

  const handleMouseLeave = useCallback(() => {
    setTilt({ x: 0, y: 0, active: false });
  }, []);

  return (
    <>
      {/* 3D Tiltable Card Component */}
      <div
        ref={cardRef}
        onMouseMove={handleMouseMove}
        onMouseLeave={handleMouseLeave}
        onClick={() => setIsOpen(true)}
        className={`tilt-glass-card sg-card ${tilt.active ? 'is-hovered' : ''} ${className}`}
        style={{
          ...style,
          cursor: 'pointer',
          position: 'relative',
          transform: tilt.active
            ? `perspective(800px) rotateX(${tilt.x.toFixed(2)}deg) rotateY(${tilt.y.toFixed(2)}deg) translateZ(8px)`
            : 'perspective(800px) rotateX(0deg) rotateY(0deg) translateZ(0px)',
          transition: tilt.active ? 'transform 0.08s ease-out' : 'transform 0.4s cubic-bezier(0.2, 0.8, 0.2, 1), box-shadow 0.3s ease',
          transformStyle: 'preserve-3d',
          overflow: 'hidden',
        }}
        role="button"
        tabIndex={0}
        onKeyDown={(e) => {
          if (e.key === 'Enter' || e.key === ' ') {
            e.preventDefault();
            setIsOpen(true);
          }
        }}
        aria-label={`${detail.title}: Click to view full transparent blurred architectural description`}
      >
        {/* Dynamic Cursor Spotlight Effect */}
        {tilt.active && (
          <div
            className="card-spotlight"
            style={{
              position: 'absolute',
              top: 0,
              left: 0,
              right: 0,
              bottom: 0,
              pointerEvents: 'none',
              background: `radial-gradient(circle 180px at ${mousePos.x}px ${mousePos.y}px, ${detail.accentColor}22, transparent 80%)`,
              zIndex: 1,
            }}
          />
        )}

        <div style={{ position: 'relative', zIndex: 2, display: 'flex', flexDirection: 'column', gap: '10px', height: '100%', padding: '4px 2px' }}>
          {/* Card Header with Icon & Category */}
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <span style={{ color: detail.accentColor, display: 'flex', alignItems: 'center' }}>
                {detail.icon}
              </span>
              <span style={{ fontWeight: 700, fontSize: '16.5px', color: 'var(--text-primary)' }}>
                {detail.title}
              </span>
            </div>
            <span
              style={{
                fontSize: '11.5px',
                fontFamily: 'var(--font-mono)',
                textTransform: 'uppercase',
                padding: '3px 8px',
                borderRadius: 'var(--radius-xs)',
                backgroundColor: `${detail.accentColor}18`,
                color: detail.accentColor,
                border: `1px solid ${detail.accentColor}33`,
                display: 'inline-flex',
                alignItems: 'center',
                gap: '4px',
                fontWeight: 700,
              }}
            >
              <Sparkles size={11} />
              <span>Details</span>
            </span>
          </div>

          {/* Subtitle / Key Identifier */}
          <div
            style={{
              fontFamily: 'var(--font-mono)',
              fontSize: '14px',
              color: detail.accentColor,
              fontWeight: 700,
              letterSpacing: '-0.01em',
            }}
          >
            {detail.subtitle}
          </div>

          {/* Short Description */}
          <p style={{ fontSize: '14px', color: 'var(--text-secondary)', margin: 0, lineHeight: 1.6, flex: 1 }}>
            {detail.shortDesc}
          </p>

          {/* Click Hint Bar */}
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              fontSize: '12.5px',
              color: 'var(--text-secondary)',
              borderTop: '1px solid var(--border-subtle)',
              paddingTop: '8px',
              marginTop: '4px',
            }}
          >
            <span style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
              <Info size={13} style={{ color: detail.accentColor }} />
              <span>Click to inspect</span>
            </span>
            <span style={{ fontFamily: 'var(--font-mono)', color: detail.accentColor, fontWeight: 700 }}>
              3D Tilt Active &rarr;
            </span>
          </div>
        </div>
      </div>

      {/* Transparent Blurred Glassmorphism Box Modal */}
      {isOpen && (
        <div
          className="glass-modal-backdrop"
          onClick={() => setIsOpen(false)}
          style={{
            position: 'fixed',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            zIndex: 9999,
            backgroundColor: 'rgba(0, 0, 0, 0.55)',
            backdropFilter: 'blur(16px)',
            WebkitBackdropFilter: 'blur(16px)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            padding: '20px',
            animation: 'fadeIn 0.2s ease-out',
          }}
          role="dialog"
          aria-modal="true"
          aria-labelledby={`dialog-title-${detail.title}`}
        >
          <div
            className="glass-modal-container"
            onClick={(e) => e.stopPropagation()}
            style={{
              width: '100%',
              maxWidth: '700px',
              maxHeight: '88vh',
              overflowY: 'auto',
              backgroundColor: 'var(--bg-glass-modal, rgba(17, 25, 34, 0.92))',
              backdropFilter: 'blur(24px) saturate(180%)',
              WebkitBackdropFilter: 'blur(24px) saturate(180%)',
              border: `1px solid ${detail.accentColor}55`,
              borderRadius: 'var(--radius-md, 8px)',
              boxShadow: `0 24px 60px rgba(0, 0, 0, 0.5), 0 0 40px ${detail.accentColor}25`,
              padding: '28px 32px',
              position: 'relative',
              animation: 'scaleIn 0.25s cubic-bezier(0.16, 1, 0.3, 1)',
              display: 'flex',
              flexDirection: 'column',
              gap: '18px',
              color: 'var(--text-primary)',
            }}
          >
            {/* Header */}
            <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: '14px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                <div
                  style={{
                    width: '44px',
                    height: '44px',
                    borderRadius: 'var(--radius-sm, 6px)',
                    backgroundColor: `${detail.accentColor}22`,
                    border: `1px solid ${detail.accentColor}55`,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    color: detail.accentColor,
                    flexShrink: 0,
                  }}
                >
                  {detail.icon}
                </div>
                <div>
                  <div style={{ fontSize: '11px', color: detail.accentColor, textTransform: 'uppercase', fontFamily: 'var(--font-mono)', fontWeight: 700, letterSpacing: '0.06em' }}>
                    {detail.category}
                  </div>
                  <h2
                    id={`dialog-title-${detail.title}`}
                    style={{ fontSize: '20px', fontWeight: 700, margin: '2px 0 0 0', color: 'var(--text-primary)', letterSpacing: '-0.01em' }}
                  >
                    {detail.title}
                  </h2>
                </div>
              </div>

              <button
                type="button"
                onClick={() => setIsOpen(false)}
                className="sg-btn"
                style={{
                  background: 'transparent',
                  border: '1px solid var(--border-default)',
                  borderRadius: 'var(--radius-xs)',
                  color: 'var(--text-secondary)',
                  padding: '6px',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  cursor: 'pointer',
                }}
                aria-label="Close details"
              >
                <X size={18} />
              </button>
            </div>

            {/* Identifier Banner */}
            <div
              style={{
                padding: '10px 14px',
                borderRadius: 'var(--radius-xs)',
                backgroundColor: 'var(--bg-surface-raised)',
                border: '1px solid var(--border-default)',
                fontFamily: 'var(--font-mono)',
                fontSize: '14px',
                fontWeight: 600,
                color: detail.accentColor,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
              }}
            >
              <span>{detail.subtitle}</span>
              <Activity size={16} style={{ color: detail.accentColor }} />
            </div>

            {/* Full Architectural Description */}
            <p style={{ fontSize: '14px', lineHeight: 1.65, color: 'var(--text-secondary)', margin: 0 }}>
              {detail.shortDesc}
            </p>

            {/* Formula Block (if available) */}
            {detail.formula && (
              <div
                style={{
                  padding: '12px 16px',
                  borderRadius: 'var(--radius-xs)',
                  backgroundColor: 'var(--bg-surface-subdued)',
                  border: `1px solid ${detail.accentColor}33`,
                  fontFamily: 'var(--font-mono)',
                  fontSize: '13px',
                  color: 'var(--text-primary)',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '6px',
                }}
              >
                <span style={{ fontSize: '11px', color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '0.04em', fontWeight: 600 }}>
                  Mathematical Formulation
                </span>
                <div style={{ color: detail.accentColor, fontWeight: 700 }}>{detail.formula}</div>
              </div>
            )}

            {/* Parameters Grid */}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '10px' }}>
              {detail.parameters.map((p, idx) => (
                <div
                  key={idx}
                  style={{
                    padding: '10px 14px',
                    borderRadius: 'var(--radius-xs)',
                    backgroundColor: 'var(--bg-surface-raised)',
                    border: '1px solid var(--border-subtle)',
                    display: 'flex',
                    flexDirection: 'column',
                    gap: '4px',
                  }}
                >
                  <span style={{ fontSize: '12px', color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '0.04em', fontWeight: 600 }}>
                    {p.label}
                  </span>
                  <span style={{ fontFamily: 'var(--font-mono)', fontSize: '14px', fontWeight: 700, color: 'var(--text-primary)' }}>
                    {p.value}
                  </span>
                </div>
              ))}
            </div>

            {/* Telemetry Step Cards */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
              <span style={{ fontSize: '12.5px', color: 'var(--text-tertiary)', textTransform: 'uppercase', fontWeight: 700, letterSpacing: '0.05em' }}>
                Operational Guardrails & Architecture Verification
              </span>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                {detail.telemetryNotes.map((note, idx) => (
                  <div
                    key={idx}
                    style={{
                      display: 'flex',
                      alignItems: 'flex-start',
                      gap: '12px',
                      padding: '12px 16px',
                      borderRadius: 'var(--radius-xs)',
                      backgroundColor: 'var(--bg-surface-raised)',
                      border: '1px solid var(--border-subtle)',
                    }}
                  >
                    <span
                      style={{
                        fontFamily: 'var(--font-mono)',
                        fontSize: '12px',
                        fontWeight: 800,
                        color: detail.accentColor,
                        backgroundColor: `${detail.accentColor}18`,
                        padding: '3px 8px',
                        borderRadius: 'var(--radius-xs)',
                        flexShrink: 0,
                        marginTop: '2px',
                      }}
                    >
                      0{idx + 1}
                    </span>
                    <span style={{ fontSize: '14px', lineHeight: 1.6, color: 'var(--text-secondary)' }}>
                      {note}
                    </span>
                  </div>
                ))}
              </div>
            </div>

            {/* Footer / Partition Lineage */}
            {detail.partitionInfo && (
              <div
                style={{
                  borderTop: '1px solid var(--border-subtle)',
                  paddingTop: '12px',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  fontSize: '12.5px',
                  color: 'var(--text-secondary)',
                  fontFamily: 'var(--font-mono)',
                }}
              >
                <span>{detail.partitionInfo}</span>
                <span style={{ color: 'var(--color-routine)', fontWeight: 700 }}>VERIFIED IMMUTABLE</span>
              </div>
            )}

          </div>
        </div>
      )}
    </>
  );
};
