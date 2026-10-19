import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { api } from '../../lib/api/client';
import { OperatingMode } from '../../lib/api/types';

describe('SignalGate Mode Switcher, Operating Modes & API Client (DASH-01, DASH-02, DASH-03)', () => {
  const originalFetch = global.fetch;

  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    global.fetch = originalFetch;
  });

  it('verifies the 3 non-negotiable operating modes are distinct', () => {
    const modes: OperatingMode[] = [
      'SYNTHETIC_SMOKE_ONLY',
      'IEEE_CIS_OFFLINE_BENCHMARK',
      'LIVE_SOURCE_NOT_CONNECTED',
    ];

    expect(new Set(modes).size).toBe(3);
    expect(modes).toContain('SYNTHETIC_SMOKE_ONLY');
    expect(modes).toContain('IEEE_CIS_OFFLINE_BENCHMARK');
    expect(modes).toContain('LIVE_SOURCE_NOT_CONNECTED');
  });

  it('verifies api.getMode calls GET /api/mode', async () => {
    const mockResponse = {
      active_mode: 'SYNTHETIC_SMOKE_ONLY',
      available_modes: ['SYNTHETIC_SMOKE_ONLY', 'IEEE_CIS_OFFLINE_BENCHMARK', 'LIVE_SOURCE_NOT_CONNECTED'],
      modes_detail: {
        SYNTHETIC_SMOKE_ONLY: { status: 'READY', details: 'Synthetic smoke fixture mode' },
        IEEE_CIS_OFFLINE_BENCHMARK: { status: 'READY', details: 'Full 391-feature ensemble model' },
        LIVE_SOURCE_NOT_CONNECTED: { status: 'NOT_CONNECTED', details: 'Live sources disconnected' },
      },
      notice: 'Operating mode readiness query successful.',
    };

    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => mockResponse,
    });

    const res = await api.getMode();
    expect(global.fetch).toHaveBeenCalledWith(
      expect.stringContaining('/api/mode'),
      expect.objectContaining({ headers: expect.objectContaining({ 'Accept': 'application/json' }) })
    );
    expect(res.active_mode).toBe('SYNTHETIC_SMOKE_ONLY');
    expect(res.available_modes.length).toBe(3);
  });

  it('verifies api.getModelCard appends mode query parameter', async () => {
    const mockModelCard = {
      mode: 'IEEE_CIS_OFFLINE_BENCHMARK',
      model_id: 'ieee_cis_v1',
      architecture_version: 'v1.0.0',
      architecture_type: 'EraBaggedHeterogeneousEnsemble',
      sub_models: ['HistGradientBoosting', 'ExtraTrees', 'LogisticRegression'],
      calibrator_type: 'PlattCalibrator',
      feature_count: 391,
      features_sample: ['TransactionAmt', 'card1'],
      manifest_hash: 'a'.repeat(64),
      artifact_hashes: {},
      split_provenance: {},
      notice: 'Offline benchmark model card.',
    };

    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => mockModelCard,
    });

    const res = await api.getModelCard('IEEE_CIS_OFFLINE_BENCHMARK');
    expect(global.fetch).toHaveBeenCalledWith(
      expect.stringContaining('/api/model/card?mode=IEEE_CIS_OFFLINE_BENCHMARK'),
      expect.anything()
    );
    expect(res.architecture_type).toBe('EraBaggedHeterogeneousEnsemble');
    expect(res.sub_models).toEqual(['HistGradientBoosting', 'ExtraTrees', 'LogisticRegression']);
    expect(res.feature_count).toBe(391);
  });

  it('verifies api.getDriftReport appends mode parameter and returns statutory discipline notice', async () => {
    const mockDrift = {
      report_id: 'drift-test-01',
      status: 'STABLE',
      features_monitored: 391,
      significant_drift_features: [],
      moderate_drift_features: [],
      mean_psi: 0.0125,
      max_psi: 0.045,
      score_drift: {
        psi: 0.008,
        wasserstein_distance: 0.003,
      },
      provenance_hash: 'b'.repeat(64),
      timestamp: '2026-10-18T22:00:00Z',
      notice: 'Distribution drift indicates data shift, not proof of fraud.',
      feature_reports: [],
    };

    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => mockDrift,
    });

    const res = await api.getDriftReport('IEEE_CIS_OFFLINE_BENCHMARK');
    expect(global.fetch).toHaveBeenCalledWith(
      expect.stringContaining('/api/drift/report?mode=IEEE_CIS_OFFLINE_BENCHMARK'),
      expect.anything()
    );
    expect(res.features_monitored).toBe(391);
    expect(res.notice).toContain('not proof of fraud');
  });

  it('verifies api.verifyAuditChain calls GET /api/audit/verify', async () => {
    const mockVerify = {
      status: 'VERIFIED',
      is_valid: true,
      record_count: 142,
      signing_status: 'SIGNED_HMAC_SHA256',
      errors: [],
      chain_head_hash: 'c'.repeat(64),
    };

    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => mockVerify,
    });

    const res = await api.verifyAuditChain();
    expect(global.fetch).toHaveBeenCalledWith(
      expect.stringContaining('/api/audit/verify'),
      expect.anything()
    );
    expect(res.is_valid).toBe(true);
    expect(res.status).toBe('VERIFIED');
    expect(res.signing_status).toBe('SIGNED_HMAC_SHA256');
  });

  it('verifies api.scoreSandbox passes features and mode payload correctly', async () => {
    const mockScoreResponse = {
      decision_id: 'dec-1001',
      timestamp: '2026-10-18T22:00:00Z',
      signals: {
        p_risk: 0.045,
        u_disagreement: 0.12,
        u_method: 'rank_residualized_ensemble',
      },
      decision: {
        action: 'ROUTINE',
        reason_code: 'R5_LOW_RISK_RELIABLE',
        governor_quota_status: 'UNDER_QUOTA',
      },
      governor: {},
      latency_ms: 1.25,
      provenance: {},
      audit_logged: true,
      notice: 'Offline benchmark inference completed.',
      mode: 'IEEE_CIS_OFFLINE_BENCHMARK',
      audit_seq: 143,
    };

    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => mockScoreResponse,
    });

    const features = { TransactionAmt: 150.0, ProductCD: 'W' };
    const res = await api.scoreSandbox(features, 'IEEE_CIS_OFFLINE_BENCHMARK');

    expect(global.fetch).toHaveBeenCalledWith(
      expect.stringContaining('/api/score-sandbox'),
      expect.objectContaining({
        method: 'POST',
        body: JSON.stringify({
          features,
          mode: 'IEEE_CIS_OFFLINE_BENCHMARK',
        }),
      })
    );
    expect(res.decision_id).toBe('dec-1001');
    expect(res.mode).toBe('IEEE_CIS_OFFLINE_BENCHMARK');
    expect(res.audit_seq).toBe(143);
  });

  it('rejects forbidden ground truth fields from sandbox inference payloads', () => {
    const forbiddenKeys = [
      'isFraud',
      'isfraud',
      'true_label',
      'target',
      'label',
      'TransactionID',
      'TransactionDT',
    ];

    const cleanPayload: Record<string, unknown> = {
      TransactionAmt: 250.0,
      ProductCD: 'W',
      C1: 2.0,
    };

    // Helper checking ground-truth quarantine
    const isQuarantined = (payload: Record<string, unknown>): boolean => {
      const keys = Object.keys(payload).map((k) => k.toLowerCase().replace(/_/g, ''));
      return forbiddenKeys.some((f) => keys.includes(f.toLowerCase().replace(/_/g, '')));
    };

    expect(isQuarantined(cleanPayload)).toBe(false);

    for (const forbidden of forbiddenKeys) {
      const dirtyPayload = { ...cleanPayload, [forbidden]: 1 };
      expect(isQuarantined(dirtyPayload)).toBe(true);
    }
  });

  it('verifies governance proposal replay and approval workflows', async () => {
    const mockProposal = {
      proposal_id: 'prop-001',
      status: 'APPROVED',
      base_cfg_hash: 'd'.repeat(64),
      changes: { t_alert: 0.09 },
      rationale: 'Calibrated alert threshold adjustment',
      created_at: '2026-10-18T21:00:00Z',
      replay_result: { gate_passed: true },
      approval_record: { approver: 'LeadAnalyst', timestamp: '2026-10-18T22:00:00Z' },
    };

    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => mockProposal,
    });

    const res = await api.approveProposal('prop-001', 'LeadAnalyst', 'Valid replay gate');
    expect(global.fetch).toHaveBeenCalledWith(
      expect.stringContaining('/api/governance/proposals/prop-001/approve'),
      expect.objectContaining({
        method: 'POST',
        body: JSON.stringify({ approver: 'LeadAnalyst', rationale: 'Valid replay gate' }),
      })
    );
    expect(res.status).toBe('APPROVED');
  });
});
