import React, { Suspense } from 'react';
import { Navigate, createBrowserRouter } from 'react-router-dom';
import { AppShell } from './AppShell';
import { LoadingState } from '../components/LoadingState';

const OverviewPage = React.lazy(() =>
  import('../features/overview/OverviewPage').then((m) => ({ default: m.OverviewPage }))
);
const ShiftStormPage = React.lazy(() =>
  import('../features/shift-storm/ShiftStormPage').then((m) => ({ default: m.ShiftStormPage }))
);
const CaseExplorerPage = React.lazy(() =>
  import('../features/case-explorer/CaseExplorerPage').then((m) => ({ default: m.CaseExplorerPage }))
);
const PolicyComparisonPage = React.lazy(() =>
  import('../features/policy-comparison/PolicyComparisonPage').then((m) => ({ default: m.PolicyComparisonPage }))
);
const DriftShiftPage = React.lazy(() =>
  import('../features/drift-shift/DriftShiftPage').then((m) => ({ default: m.DriftShiftPage }))
);
const AuditTrailPage = React.lazy(() =>
  import('../features/audit-trail/AuditTrailPage').then((m) => ({ default: m.AuditTrailPage }))
);
const ModelCardPage = React.lazy(() =>
  import('../features/model-card/ModelCardPage').then((m) => ({ default: m.ModelCardPage }))
);
const SandboxPage = React.lazy(() =>
  import('../features/sandbox/SandboxPage').then((m) => ({ default: m.SandboxPage }))
);

const renderLazy = (Component: React.ComponentType, moduleName: string) => (
  <Suspense
    fallback={
      <div style={{ padding: '32px 24px', display: 'flex', justifyContent: 'center' }}>
        <LoadingState message={`Loading ${moduleName}...`} />
      </div>
    }
  >
    <Component />
  </Suspense>
);

export const router = createBrowserRouter([
  {
    path: '/',
    element: <AppShell />,
    children: [
      {
        index: true,
        element: <Navigate to="/overview" replace />,
      },
      {
        path: 'overview',
        element: renderLazy(OverviewPage, 'Operational Overview'),
      },
      {
        path: 'shift-storm',
        element: renderLazy(ShiftStormPage, 'Shift Storm Forensics'),
      },
      {
        path: 'case-explorer',
        element: renderLazy(CaseExplorerPage, 'Case Ledger Explorer'),
      },
      {
        path: 'policy-comparison',
        element: renderLazy(PolicyComparisonPage, 'Policy Comparison Suite'),
      },
      {
        path: 'drift-shift',
        element: renderLazy(DriftShiftPage, 'Drift & Shift Diagnostics'),
      },
      {
        path: 'audit-trail',
        element: renderLazy(AuditTrailPage, 'Immutable Audit Ledger'),
      },
      {
        path: 'model-card',
        element: renderLazy(ModelCardPage, 'Model Governance Card'),
      },
      {
        path: 'sandbox',
        element: renderLazy(SandboxPage, 'Scoring Sandbox'),
      },
      {
        path: '*',
        element: <Navigate to="/overview" replace />,
      },
    ],
  },
]);
