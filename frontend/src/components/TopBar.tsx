import React, { useEffect, useState } from 'react';
import { NavLink } from 'react-router-dom';
import { Menu, ShieldAlert } from 'lucide-react';
import { ApiStatusIndicator } from './ApiStatusIndicator';
import { ThemeSwitcher } from './ThemeSwitcher';
import { ModeSwitcher } from './ModeSwitcher';
import { useApiStatus } from '../lib/api/hooks';

interface TopBarProps {
  onToggleMobile: () => void;
}

interface PrimaryNavTab {
  label: string;
  path: string;
}

const PRIMARY_TABS: PrimaryNavTab[] = [
  { label: 'Overview', path: '/overview' },
  { label: 'Shift Storm Replay', path: '/shift-storm' },
  { label: 'Case Explorer', path: '/case-explorer' },
  { label: 'Policy Comparison', path: '/policy-comparison' },
];

export const TopBar: React.FC<TopBarProps> = ({ onToggleMobile }) => {
  const { status, health } = useApiStatus();

  // Real local clock updated every second in 24h format
  const [localTime, setLocalTime] = useState<string>('');

  useEffect(() => {
    const updateTime = () => {
      const now = new Date();
      setLocalTime(
        now.toLocaleTimeString(undefined, {
          hour: '2-digit',
          minute: '2-digit',
          second: '2-digit',
          hour12: false,
        })
      );
    };
    updateTime();
    const timer = setInterval(updateTime, 1000);
    return () => clearInterval(timer);
  }, []);

  const version = status?.version || health?.version || '0.1.0';

  return (
    <header className="topbar" aria-label="Application Header">
      {/* Left: Brand Identity & Evidence Status */}
      <div className="topbar-left">
        <button
          type="button"
          onClick={onToggleMobile}
          className="mobile-menu-btn"
          aria-label="Open operational navigation rail"
          title="Open navigation rail"
        >
          <Menu size={18} />
        </button>

        <NavLink to="/overview" className="brand-wrapper" title="SignalGate Decision Control Room">
          <div className="brand-monogram" aria-hidden="true">
            <ShieldAlert size={18} />
          </div>
          <div className="brand-text">
            <span className="brand-title">
              SIGNAL<span>GATE</span>
            </span>
            <span className="brand-subtitle">Shift-Aware Fraud Triage</span>
          </div>
        </NavLink>

        <div className="header-divider" aria-hidden="true" />

        <ModeSwitcher />
      </div>

      {/* Center: Primary Horizontal Navigation with Scroller */}
      <div className="header-nav-wrapper" aria-label="Primary Navigation Container">
        <nav className="header-nav" aria-label="Primary Screen Navigation">
          {PRIMARY_TABS.map((tab) => (
            <NavLink
              key={tab.path}
              to={tab.path}
              className={({ isActive }) => `header-nav-link ${isActive ? 'active' : ''}`}
              title={tab.label}
            >
              <span>{tab.label}</span>
            </NavLink>
          ))}
        </nav>
      </div>

      {/* Right: Operational Telemetry & Backend Integrity */}
      <div className="topbar-right">
        {/* Primary Evaluation Budget Indicator */}
        <div
          className="budget-chip"
          title="Canonical Evaluation Review Capacity: 130 reviews (1.5x training prevalence, 6.525% touched rate on 2,000 test cases)"
        >
          <span className="budget-chip-label">CAP:</span>
          <span className="budget-chip-val">130 (6.525%)</span>
        </div>

        {/* Local Clock */}
        {localTime && (
          <div className="local-clock" title="Local system time">
            {localTime}
          </div>
        )}

        {/* Version & Status */}
        <span
          className="topbar-version"
          title={`SignalGate System Version ${version}`}
        >
          v{version}
        </span>

        {/* Global Theme Switcher */}
        <ThemeSwitcher />

        <ApiStatusIndicator showDetails={false} />
      </div>
    </header>
  );
};
