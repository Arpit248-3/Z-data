import React, { useRef, useState, useCallback, useEffect } from 'react';
import { X, Activity } from 'lucide-react';
import { TiltGlassCardDetail } from './TiltGlassCard';

export interface MetricCardProps {
  label: string;
  value: number | string | null;
  unit?: string;
  subtext?: string;
  isAvailable?: boolean;
  unavailableText?: string;
  icon?: React.ReactNode;
  variant?: 'cyan' | 'coral' | 'amber' | 'violet' | 'green' | 'default';
  progressPercent?: number;
  onClick?: () => void;
  clickable?: boolean;
  badgeText?: string;
  detail?: TiltGlassCardDetail;
}

export const MetricCard: React.FC<MetricCardProps> = ({
  label,
  value,
  unit,
  subtext,
  isAvailable = true,
  unavailableText = 'Unavailable',
  icon,
  variant = 'default',
  progressPercent,
  onClick,
  clickable = false,
  badgeText,
  detail,
}) => {
  const cardRef = useRef<HTMLDivElement>(null);
  const [isModalOpen, setIsModalOpen] = useState<boolean>(false);
  const [tilt, setTilt] = useState<{ x: number; y: number; active: boolean }>({
    x: 0,
    y: 0,
    active: false,
  });
  const [mousePos, setMousePos] = useState<{ x: number; y: number }>({ x: 0, y: 0 });

  const isNullOrUnavailable = !isAvailable || value === null || value === undefined;
  const hasInteractiveDetail = Boolean(detail);
  const isInteractive = (clickable || hasInteractiveDetail) && (Boolean(onClick) || hasInteractiveDetail);

  // Close modal on Escape
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isModalOpen) {
        setIsModalOpen(false);
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isModalOpen]);

  // Enhanced 3D Tilt with cursor tracking
  const handleMouseMove = useCallback((e: React.MouseEvent<HTMLDivElement>) => {
    if (!cardRef.current) return;
    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;

    const rect = cardRef.current.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;
    const centerX = rect.width / 2;
    const centerY = rect.height / 2;

    // Smooth 3D tilt
    const maxTilt = 7.5;
    const rotateY = ((x - centerX) / centerX) * maxTilt;
    const rotateX = -((y - centerY) / centerY) * maxTilt;

    setTilt({ x: rotateX, y: rotateY, active: true });
    setMousePos({ x, y });
  }, []);

  const handleMouseLeave = useCallback(() => {
    setTilt({ x: 0, y: 0, active: false });
  }, []);

  const handleClick = () => {
    if (detail) {
      setIsModalOpen(true);
    } else if (onClick) {
      onClick();
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLDivElement>) => {
    if (!isInteractive) return;
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault();
      handleClick();
    }
  };

  let accentColor = 'var(--text-primary)';
  let iconBg = 'var(--bg-surface-raised)';
  let iconBorder = 'var(--border-subtle)';
  let iconColor = 'var(--text-tertiary)';

  if (!isNullOrUnavailable) {
    if (variant === 'cyan') {
      accentColor = 'var(--accent-primary-bright)';
      iconBg = 'var(--accent-primary-tint)';
      iconBorder = 'var(--accent-primary-dim)';
      iconColor = 'var(--accent-primary)';
    } else if (variant === 'coral') {
      accentColor = 'var(--color-fraud-alert-bright)';
      iconBg = 'var(--color-fraud-alert-tint)';
      iconBorder = 'var(--color-fraud-alert-dim)';
      iconColor = 'var(--color-fraud-alert)';
    } else if (variant === 'amber') {
      accentColor = 'var(--color-manual-review-bright)';
      iconBg = 'var(--color-manual-review-tint)';
      iconBorder = 'var(--color-manual-review-dim)';
      iconColor = 'var(--color-manual-review)';
    } else if (variant === 'violet') {
      accentColor = 'var(--color-epistemic-defer-bright)';
      iconBg = 'var(--color-epistemic-defer-tint)';
      iconBorder = 'var(--color-epistemic-defer-dim)';
      iconColor = 'var(--color-epistemic-defer)';
    } else if (variant === 'green') {
      accentColor = 'var(--color-routine-bright)';
      iconBg = 'var(--color-routine-tint)';
      iconBorder = 'var(--color-routine-dim)';
      iconColor = 'var(--color-routine)';
    }
  }

  const variantClass = variant !== 'default' ? `metric-card-variant-${variant}` : '';

  return (
    <>
      <div
        ref={cardRef}
        className={`metric-card ${variantClass} ${isInteractive ? 'metric-card-interactive is-tiltable' : ''} ${isNullOrUnavailable ? 'metric-card-offline' : ''}`}
        onClick={isInteractive ? handleClick : undefined}
        onMouseMove={handleMouseMove}
        onMouseLeave={handleMouseLeave}
        onKeyDown={handleKeyDown}
        role={isInteractive ? 'button' : undefined}
        tabIndex={isInteractive ? 0 : undefined}
        aria-label={`${label}: ${isNullOrUnavailable ? unavailableText : `${value} ${unit || ''}`}${subtext ? ` (${subtext})` : ''}${detail ? ' — Click to inspect detailed 3D telemetry' : ''}`}
        style={{
          position: 'relative',
          transform: tilt.active
            ? `perspective(800px) rotateX(${tilt.x.toFixed(2)}deg) rotateY(${tilt.y.toFixed(2)}deg) translateZ(6px)`
            : 'perspective(800px) rotateX(0deg) rotateY(0deg) translateZ(0px)',
          transition: tilt.active ? 'transform 0.08s ease-out' : 'transform 0.4s cubic-bezier(0.2, 0.8, 0.2, 1), box-shadow 0.3s ease, border-color 0.2s ease',
          transformStyle: 'preserve-3d',
          overflow: 'hidden',
          cursor: isInteractive ? 'pointer' : 'default',
        }}
      >
        {/* Dynamic Cursor Spotlight Effect */}
        {tilt.active && (
          <div
            style={{
              position: 'absolute',
              top: 0,
              left: 0,
              right: 0,
              bottom: 0,
              pointerEvents: 'none',
              background: `radial-gradient(circle 140px at ${mousePos.x}px ${mousePos.y}px, ${accentColor}18, transparent 75%)`,
              zIndex: 1,
            }}
          />
        )}

        <div className="metric-label-row" style={{ position: 'relative', zIndex: 2 }}>
          <div className="metric-label-group">
            <span className="metric-label">{label}</span>
            {badgeText && <span className="metric-badge">{badgeText}</span>}
          </div>
          {icon && (
            <div
              className="metric-icon-wrap"
              style={{ backgroundColor: iconBg, borderColor: iconBorder, color: iconColor }}
            >
              {icon}
            </div>
          )}
        </div>

        <div className="metric-value-row" style={{ position: 'relative', zIndex: 2 }}>
          {isNullOrUnavailable ? (
            <span className="metric-value unavailable">{unavailableText}</span>
          ) : (
            <>
              <span className="metric-value" style={{ color: accentColor }}>
                {typeof value === 'number' ? value.toLocaleString() : value}
              </span>
              {unit && <span className="metric-unit">{unit}</span>}
            </>
          )}
        </div>

        {progressPercent !== undefined && !isNullOrUnavailable && (
          <div className="metric-progress-track" style={{ position: 'relative', zIndex: 2 }}>
            <div
              className="metric-progress-bar"
              style={{
                width: `${Math.min(100, Math.max(0, progressPercent))}%`,
                backgroundColor: accentColor,
              }}
            />
          </div>
        )}

        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '6px', position: 'relative', zIndex: 2 }}>
          {subtext && <div className="metric-subtext">{subtext}</div>}
          {detail && (
            <span
              style={{
                fontSize: '11px',
                fontFamily: 'var(--font-mono)',
                color: accentColor,
                fontWeight: 700,
                letterSpacing: '0.04em',
                textTransform: 'uppercase',
                padding: '2px 7px',
                borderRadius: 'var(--radius-xs)',
                backgroundColor: `${accentColor}15`,
                border: `1px solid ${accentColor}33`,
                display: 'inline-flex',
                alignItems: 'center',
                gap: '4px',
                flexShrink: 0,
              }}
            >
              Inspect &rarr;
            </span>
          )}
        </div>
      </div>

      {/* Transparent Background Blurred Modal Box */}
      {isModalOpen && detail && (
        <div
          className="glass-modal-backdrop"
          onClick={() => setIsModalOpen(false)}
          style={{
            position: 'fixed',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            zIndex: 1000,
            backgroundColor: 'rgba(10, 15, 20, 0.65)',
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
          aria-labelledby={`kpi-dialog-title-${detail.title}`}
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
            {/* Modal Header */}
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
                    id={`kpi-dialog-title-${detail.title}`}
                    style={{ fontSize: '20px', fontWeight: 700, margin: '2px 0 0 0', color: 'var(--text-primary)', letterSpacing: '-0.01em' }}
                  >
                    {detail.title}
                  </h2>
                </div>
              </div>

              <button
                type="button"
                onClick={() => setIsModalOpen(false)}
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

            {/* Subtitle / Operational Value Banner */}
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

            {/* Architectural Explanation */}
            <p style={{ fontSize: '14px', lineHeight: 1.65, color: 'var(--text-secondary)', margin: 0 }}>
              {detail.shortDesc}
            </p>

            {/* Mathematical Formula Pill */}
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
                  Mathematical Specification
                </span>
                <div style={{ color: detail.accentColor, fontWeight: 700 }}>{detail.formula}</div>
              </div>
            )}

            {/* Parameter Metrics Grid */}
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

            {/* Operational Telemetry Notes (Uncongested Step Cards) */}
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

            {/* Action Bar */}
            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px', borderTop: '1px solid var(--border-subtle)', paddingTop: '14px' }}>
              <button
                type="button"
                onClick={() => setIsModalOpen(false)}
                className="sg-btn sg-btn-secondary"
                style={{ fontSize: '12px', padding: '7px 16px' }}
              >
                Dismiss
              </button>

              {onClick && (
                <button
                  type="button"
                  onClick={() => {
                    setIsModalOpen(false);
                    onClick();
                  }}
                  className="sg-btn sg-btn-primary"
                  style={{ fontSize: '12px', padding: '6px 14px', display: 'flex', alignItems: 'center', gap: '6px' }}
                >
                  <span>Jump to Cockpit Section</span>
                </button>
              )}
            </div>
          </div>
        </div>
      )}
    </>
  );
};
