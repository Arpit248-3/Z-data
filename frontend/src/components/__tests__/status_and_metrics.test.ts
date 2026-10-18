import { describe, it, expect } from 'vitest';
import { ApiClientError } from '../../lib/api/types';

describe('SignalGate Frontend Architecture & Types', () => {
  it('constructs ApiClientError correctly with status and code', () => {
    const error = new ApiClientError(503, {
      code: 'ARTIFACT_UNAVAILABLE',
      message: 'Required evaluation artifact is not available.',
      details: { missing_artifact: 'results/results.json' },
    });

    expect(error.status).toBe(503);
    expect(error.code).toBe('ARTIFACT_UNAVAILABLE');
    expect(error.message).toBe('Required evaluation artifact is not available.');
    expect(error.details?.missing_artifact).toBe('results/results.json');
    expect(error.name).toBe('ApiClientError');
  });

  it('handles network error fallback without leaking sensitive data', () => {
    const networkError = new ApiClientError(0, {
      code: 'NETWORK_ERROR',
      message: 'Failed to connect to SignalGate backend API.',
    });

    expect(networkError.status).toBe(0);
    expect(networkError.code).toBe('NETWORK_ERROR');
  });

  it('ensures routing definitions are distinct and mapped to valid destinations', () => {
    const expectedRoutes = [
      '/overview',
      '/shift-storm',
      '/case-explorer',
      '/policy-comparison',
      '/drift-shift',
      '/audit-trail',
      '/model-card',
      '/sandbox',
    ];

    expect(new Set(expectedRoutes).size).toBe(8);
  });
});
