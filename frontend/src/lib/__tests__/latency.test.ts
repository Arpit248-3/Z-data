import { describe, it, expect } from 'vitest';
import { evaluateLatencySla, INFERENCE_SLA_THRESHOLD_MS } from '../latency';

describe('evaluateLatencySla', () => {
  it('exports default threshold of 250ms', () => {
    expect(INFERENCE_SLA_THRESHOLD_MS).toBe(250);
  });

  it('returns UNRATED for undefined or null latency', () => {
    const resUndefined = evaluateLatencySla(undefined);
    expect(resUndefined.status).toBe('UNRATED');
    expect(resUndefined.isPass).toBe(false);
    expect(resUndefined.isExceeded).toBe(false);
    expect(resUndefined.badgeText).toContain('TARGET');
    expect(resUndefined.badgeText).toContain('<250ms SLA');

    const resNull = evaluateLatencySla(null);
    expect(resNull.status).toBe('UNRATED');
    expect(resNull.isPass).toBe(false);
  });

  it('returns UNRATED for invalid or negative numbers', () => {
    expect(evaluateLatencySla(NaN).status).toBe('UNRATED');
    expect(evaluateLatencySla(-5).status).toBe('UNRATED');
  });

  it('returns PASS for zero or fast inference latency', () => {
    const resZero = evaluateLatencySla(0);
    expect(resZero.status).toBe('PASS');
    expect(resZero.isPass).toBe(true);
    expect(resZero.badgeText).toBe('PASS • <250ms SLA');

    const resFast = evaluateLatencySla(18.5);
    expect(resFast.status).toBe('PASS');
    expect(resFast.isPass).toBe(true);
    expect(resFast.badgeText).toBe('PASS • <250ms SLA');
  });

  it('returns PASS at exact boundary of 250.0ms', () => {
    const resBoundary = evaluateLatencySla(250.0);
    expect(resBoundary.status).toBe('PASS');
    expect(resBoundary.isPass).toBe(true);
    expect(resBoundary.isExceeded).toBe(false);
    expect(resBoundary.badgeText).toBe('PASS • <250ms SLA');
  });

  it('returns EXCEEDED immediately above 250.0ms boundary', () => {
    const resAbove = evaluateLatencySla(250.01);
    expect(resAbove.status).toBe('EXCEEDED');
    expect(resAbove.isPass).toBe(false);
    expect(resAbove.isExceeded).toBe(true);
    expect(resAbove.badgeText).toBe('EXCEEDED • >250ms SLA');
  });

  it('returns EXCEEDED for cold-start 2120.6ms latency and never displays PASS', () => {
    const resCold = evaluateLatencySla(2120.6);
    expect(resCold.status).toBe('EXCEEDED');
    expect(resCold.isPass).toBe(false);
    expect(resCold.isExceeded).toBe(true);
    expect(resCold.badgeText).toBe('EXCEEDED • >250ms SLA');
    expect(resCold.badgeText).not.toContain('PASS');
  });

  it('respects custom SLA thresholds if provided', () => {
    const resCustomPass = evaluateLatencySla(45, 50);
    expect(resCustomPass.status).toBe('PASS');
    expect(resCustomPass.badgeText).toBe('PASS • <50ms SLA');

    const resCustomExceed = evaluateLatencySla(55, 50);
    expect(resCustomExceed.status).toBe('EXCEEDED');
    expect(resCustomExceed.badgeText).toBe('EXCEEDED • >50ms SLA');
  });
});
