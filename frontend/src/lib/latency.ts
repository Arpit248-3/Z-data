/**
 * SignalGate — Latency and SLA Assessment Utilities.
 *
 * Provides standardized assessment of scoring inference latency against pre-registered SLAs.
 */

export const INFERENCE_SLA_THRESHOLD_MS = 250;

export interface LatencyStatusResult {
  status: 'PASS' | 'EXCEEDED' | 'UNRATED';
  badgeText: string;
  isPass: boolean;
  isExceeded: boolean;
  thresholdMs: number;
}

/**
 * Evaluate measured model inference and routing latency against the defined SLA.
 *
 * @param latencyMs - Measured latency in milliseconds
 * @param slaThresholdMs - Maximum acceptable latency in ms (default: 250ms)
 * @returns Standardized LatencyStatusResult with human-readable badge text and boolean flags
 */
export function evaluateLatencySla(
  latencyMs: number | null | undefined,
  slaThresholdMs: number = INFERENCE_SLA_THRESHOLD_MS
): LatencyStatusResult {
  if (typeof latencyMs !== 'number' || isNaN(latencyMs) || latencyMs < 0) {
    return {
      status: 'UNRATED',
      badgeText: `TARGET \u2022 <${slaThresholdMs}ms SLA`,
      isPass: false,
      isExceeded: false,
      thresholdMs: slaThresholdMs,
    };
  }

  if (latencyMs <= slaThresholdMs) {
    return {
      status: 'PASS',
      badgeText: `PASS \u2022 <${slaThresholdMs}ms SLA`,
      isPass: true,
      isExceeded: false,
      thresholdMs: slaThresholdMs,
    };
  }

  return {
    status: 'EXCEEDED',
    badgeText: `EXCEEDED \u2022 >${slaThresholdMs}ms SLA`,
    isPass: false,
    isExceeded: true,
    thresholdMs: slaThresholdMs,
  };
}
