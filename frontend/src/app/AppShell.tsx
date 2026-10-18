import React, { useEffect, useState } from 'react';
import { Outlet } from 'react-router-dom';
import { Sidebar } from '../components/Sidebar';
import { TopBar } from '../components/TopBar';
import { useApiStatus } from '../lib/api/hooks';
import { ThemeProvider } from '../context/ThemeContext';

export const AppShell: React.FC = () => {
  const [collapsed, setCollapsed] = useState<boolean>(false);
  const [mobileOpen, setMobileOpen] = useState<boolean>(false);
  const { status, isBackendConnected } = useApiStatus();

  // Close mobile drawer on Escape key
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && mobileOpen) {
        setMobileOpen(false);
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [mobileOpen]);

  const evidenceStatus = status?.evidence_status || 'SYNTHETIC_SMOKE_ONLY';

  return (
    <ThemeProvider>
      <div className="app-shell">
        {/* Accessible Keyboard Navigation Skip Link */}
        <a href="#main-content" className="skip-to-content">
          Skip to main cockpit content
        </a>

        {/* 1. Top Header (64px Fixed Height) */}
        <TopBar onToggleMobile={() => setMobileOpen((prev) => !prev)} />

      {/* 2. Body Region: Operational Rail + Main Content Viewport */}
      <div className="app-body">
        {/* Mobile Backdrop Veil */}
        {mobileOpen && (
          <div
            className="mobile-overlay"
            onClick={() => setMobileOpen(false)}
            aria-hidden="true"
          />
        )}

        {/* Operational Context Rail (256px Wide) */}
        <Sidebar
          collapsed={collapsed}
          onToggleCollapse={() => setCollapsed((prev) => !prev)}
          mobileOpen={mobileOpen}
          onCloseMobile={() => setMobileOpen(false)}
        />

        {/* Main Cockpit Viewport */}
        <div className="app-main">
          <main className="app-content" id="main-content">
            <Outlet />
          </main>
        </div>
      </div>

      {/* 3. Provenance Footer (28px Fixed Height) */}
      <footer className="provenance-footer" aria-label="System Provenance & Evidence Verification">
        <div className="footer-left">
          <span className="footer-label">DATASET EVIDENCE:</span>
          <span className="badge badge-synthetic" title="Development environment operates strictly on synthetic smoke fixtures">
            {evidenceStatus}
          </span>
        </div>

        <div className="footer-center">
          <span className="footer-item" title="Frozen Routing Policy Configuration Hash">
            <span className="footer-label">CONFIG:</span> 8d3f02ca...
          </span>
          <span className="footer-divider" aria-hidden="true">|</span>
          <span className="footer-item" title="Deterministic Split Hash (2,000 Test Rows)">
            <span className="footer-label">SPLIT:</span> 07b55a4e...
          </span>
        </div>

        <div className="footer-right">
          <span
            className="footer-item"
            title="Recorded offline single-transaction benchmark from results.json (not live runtime latency)"
          >
            <span className="footer-label">RECORDED BENCHMARK p95:</span> 0.17ms
          </span>
          <span className="footer-divider" aria-hidden="true">|</span>
          <span
            className="footer-status"
            style={{
              color: isBackendConnected ? 'var(--color-routine)' : 'var(--color-fraud-alert)',
            }}
          >
            {isBackendConnected ? 'BACKEND READY' : 'BACKEND OFFLINE'}
          </span>
        </div>
      </footer>
    </div>
    </ThemeProvider>
  );
};
