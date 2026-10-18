import React, { useState } from 'react';
import { NavLink } from 'react-router-dom';
import {
  ChevronDown,
  ChevronLeft,
  ChevronRight,
  Compass,
  Eye,
  EyeOff,
  FileCheck2,
  FileText,
  FlaskConical,
  Gauge,
  LineChart,
  Search,
  Shield,
  Zap,
} from 'lucide-react';

interface SidebarProps {
  collapsed: boolean;
  onToggleCollapse: () => void;
  mobileOpen: boolean;
  onCloseMobile: () => void;
}

interface NavItemDef {
  label: string;
  path: string;
  icon: React.ReactNode;
}

interface NavGroupDef {
  title: string;
  items: NavItemDef[];
}

const NAV_GROUPS: NavGroupDef[] = [
  {
    title: 'Operations',
    items: [
      { label: 'Overview', path: '/overview', icon: <Gauge size={15} /> },
      { label: 'Shift Storm Replay', path: '/shift-storm', icon: <Zap size={15} /> },
      { label: 'Case Explorer', path: '/case-explorer', icon: <Search size={15} /> },
      { label: 'Policy Comparison', path: '/policy-comparison', icon: <Compass size={15} /> },
    ],
  },
  {
    title: 'Intelligence',
    items: [
      { label: 'Drift & Shift', path: '/drift-shift', icon: <LineChart size={15} /> },
      { label: 'Audit Trail', path: '/audit-trail', icon: <FileText size={15} /> },
    ],
  },
  {
    title: 'Governance',
    items: [
      { label: 'Model & Policy Card', path: '/model-card', icon: <FileCheck2 size={15} /> },
      { label: 'Scoring Sandbox', path: '/sandbox', icon: <FlaskConical size={15} /> },
    ],
  },
];

export const Sidebar: React.FC<SidebarProps> = ({
  collapsed,
  onToggleCollapse,
  mobileOpen,
  onCloseMobile,
}) => {
  // Collapsible & Hideable Capacity state with localStorage persistence
  const [capacityCollapsed, setCapacityCollapsed] = useState<boolean>(() => {
    return localStorage.getItem('signalgate_capacity_collapsed') === 'true';
  });

  const [capacityHidden, setCapacityHidden] = useState<boolean>(() => {
    return localStorage.getItem('signalgate_capacity_hidden') === 'true';
  });

  const toggleCollapse = () => {
    setCapacityCollapsed((prev) => {
      const next = !prev;
      localStorage.setItem('signalgate_capacity_collapsed', String(next));
      return next;
    });
  };

  const toggleHide = (hidden: boolean) => {
    setCapacityHidden(hidden);
    localStorage.setItem('signalgate_capacity_hidden', String(hidden));
  };

  return (
    <aside
      className={`sidebar operational-rail ${collapsed ? 'collapsed' : ''} ${mobileOpen ? 'mobile-open' : ''}`}
      aria-label="Operational Context Rail"
    >
      {/* Rail Control Header */}
      <div className="rail-header">
        {!collapsed ? (
          <span className="rail-heading">Operational Context</span>
        ) : (
          <span style={{ fontSize: '10px', color: 'var(--text-tertiary)', fontWeight: 600 }}>CTRL</span>
        )}

        <button
          type="button"
          onClick={onToggleCollapse}
          className="collapse-btn"
          aria-label={collapsed ? 'Expand operational rail' : 'Collapse operational rail'}
          title={collapsed ? 'Expand operational rail' : 'Collapse operational rail'}
        >
          {collapsed ? <ChevronRight size={14} /> : <ChevronLeft size={14} />}
        </button>
      </div>

      {/* Section 1: Evaluation Budget & Capacity State (Collapsible & Hideable) */}
      {!collapsed && (
        <div className={`rail-section capacity-section ${capacityHidden ? 'is-hidden' : ''} ${capacityCollapsed ? 'is-collapsed' : ''}`}>
          {capacityHidden ? (
            <div className="capacity-hidden-banner">
              <button
                type="button"
                className="capacity-restore-btn"
                onClick={() => toggleHide(false)}
                title="Restore Evaluation Capacity panel"
                aria-label="Restore Evaluation Capacity panel"
              >
                <Eye size={12} />
                <span>Show Capacity</span>
                <span className="capacity-mini-badge">130</span>
              </button>
            </div>
          ) : (
            <>
              <div className="capacity-section-header">
                <button
                  type="button"
                  className="capacity-toggle-btn"
                  onClick={toggleCollapse}
                  aria-expanded={!capacityCollapsed}
                  title={capacityCollapsed ? 'Expand evaluation metrics' : 'Collapse evaluation metrics'}
                >
                  <ChevronDown
                    size={13}
                    className={`capacity-chevron ${capacityCollapsed ? 'collapsed' : ''}`}
                  />
                  <span className="rail-section-title" style={{ margin: 0 }}>
                    Evaluation Capacity
                  </span>
                  {capacityCollapsed && (
                    <span className="capacity-pill-summary" title="Review queue saturated at 130 / 130">
                      130 / 130 [Sat]
                    </span>
                  )}
                </button>

                <button
                  type="button"
                  className="capacity-action-icon-btn"
                  onClick={() => toggleHide(true)}
                  title="Hide evaluation capacity card (maximizes navigation height)"
                  aria-label="Hide evaluation capacity card"
                >
                  <EyeOff size={12} />
                </button>
              </div>

              {!capacityCollapsed && (
                <div className="capacity-telemetry-box animate-fade-in">
                  <div className="capacity-metric-row">
                    <span className="capacity-metric-label">Review Budget:</span>
                    <span className="capacity-metric-value" title="1.5x training prevalence target budget (6.525%)">
                      130 (6.525%)
                    </span>
                  </div>
                  <div className="capacity-metric-row">
                    <span className="capacity-metric-label">Queue Consumption:</span>
                    <span className="capacity-metric-value saturated" title="Governor consumed 130 of 130 review slots on test partition">
                      130 / 130 [Saturated]
                    </span>
                  </div>
                  <div className="capacity-metric-row">
                    <span className="capacity-metric-label">Admitted Alerts:</span>
                    <span className="capacity-metric-value">11</span>
                  </div>
                  <div className="capacity-metric-row">
                    <span className="capacity-metric-label">Admitted Reviews:</span>
                    <span className="capacity-metric-value">119</span>
                  </div>
                  <div className="capacity-metric-row">
                    <span className="capacity-metric-label">Capacity Deferred:</span>
                    <span className="capacity-metric-value" style={{ color: 'var(--color-epistemic-defer)' }}>
                      974
                    </span>
                  </div>
                  <div className="capacity-metric-row" style={{ marginTop: '2px', paddingTop: '4px', borderTop: '1px solid var(--border-subtle)' }}>
                    <span className="capacity-metric-label">Ingest Caserate:</span>
                    <span className="capacity-metric-value unavailable" title="Live stream ingestion is unbacked in offline synthetic mode">
                      Unavailable (Offline)
                    </span>
                  </div>
                  <div className="capacity-metric-row">
                    <span className="capacity-metric-label">Anomaly Velocity:</span>
                    <span className="capacity-metric-value unavailable" title="Real-time anomaly rate unbacked in offline test harness">
                      Unavailable (Offline)
                    </span>
                  </div>
                </div>
              )}
            </>
          )}
        </div>
      )}

      {/* Section 2: Investigation Rails Navigation */}
      <nav className="sidebar-nav" aria-label="Investigation Navigation">
        {NAV_GROUPS.map((group) => (
          <div key={group.title} className="nav-group">
            <div className="nav-group-title">{group.title}</div>
            <ul className="nav-list">
              {group.items.map((item) => (
                <li key={item.path} className="nav-item">
                  <NavLink
                    to={item.path}
                    className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}
                    onClick={onCloseMobile}
                    title={collapsed ? item.label : undefined}
                  >
                    {item.icon}
                    <span>{item.label}</span>
                  </NavLink>
                </li>
              ))}
            </ul>
          </div>
        ))}
      </nav>

      {/* Section 3: Offline Scoring Sandbox Assurance Card */}
      {!collapsed && (
        <div className="sandbox-assurance-card">
          <div className="sandbox-assurance-header">
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <Shield size={12} color="var(--accent-primary)" />
              <span className="sandbox-assurance-title">Scoring Sandbox</span>
            </div>
            <span className="badge badge-ready" style={{ fontSize: '9px', padding: '1px 5px' }}>
              OFFLINE
            </span>
          </div>
          <p className="sandbox-assurance-text">
            Local scoring with strict recursive leakage checks. Not connected to live payment networks or external ledgers.
          </p>
        </div>
      )}
    </aside>
  );
};
