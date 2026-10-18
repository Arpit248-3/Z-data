import { describe, it, expect } from 'vitest';
import fs from 'fs';
import path from 'path';
import crypto from 'crypto';
import { calculateHighlightedSegments } from '../SandboxDecisionOrb3D';

describe('Sandbox Inference Instrument GLB Integration & Mapping Tests', () => {
  const glbPath = path.resolve(__dirname, '../../../public/models/sandbox-inference-instrument.glb');
  const v2SourcePath = path.resolve(__dirname, '../../../../design_assets/blender/sandbox-inference-instrument-v2.glb');

  it('verifies production GLB exists in frontend/public/models and has expected size', () => {
    expect(fs.existsSync(glbPath)).toBe(true);
    const stats = fs.statSync(glbPath);
    expect(stats.size).toBeGreaterThan(450000); // 500,056 bytes
  });

  it('verifies production GLB matches V2 Blender export SHA-256 hash', () => {
    expect(fs.existsSync(v2SourcePath)).toBe(true);
    const prodHash = crypto.createHash('sha256').update(fs.readFileSync(glbPath)).digest('hex');
    const v2Hash = crypto.createHash('sha256').update(fs.readFileSync(v2SourcePath)).digest('hex');
    expect(prodHash).toBe(v2Hash);
  });

  it('verifies that all seven required component groups exist in the GLB node hierarchy', () => {
    const data = fs.readFileSync(glbPath);
    const chunkLen = data.readUInt32LE(12);
    const jsonStr = data.toString('utf-8', 20, 20 + chunkLen);
    const gltf = JSON.parse(jsonStr);

    const nodeNames = (gltf.nodes || []).map((n: { name?: string }) => n.name);

    const requiredGroups = [
      'sandbox_inference_instrument',
      'instrument_housing',
      'risk_track',
      'uncertainty_arc',
      'center_core',
      'mounting_base',
      'instrument_edge_details',
    ];

    for (const group of requiredGroups) {
      expect(nodeNames).toContain(group);
    }
  });

  it('verifies that all 48 individual risk segments (risk_segment_00..47) exist in the GLB', () => {
    const data = fs.readFileSync(glbPath);
    const chunkLen = data.readUInt32LE(12);
    const jsonStr = data.toString('utf-8', 20, 20 + chunkLen);
    const gltf = JSON.parse(jsonStr);

    const nodeNames = (gltf.nodes || []).map((n: { name?: string }) => n.name);

    for (let i = 0; i < 48; i++) {
      const segName = `risk_segment_${i.toString().padStart(2, '0')}`;
      expect(nodeNames).toContain(segName);
    }
  });

  it('verifies zero leaked cameras or punctual lights in the production GLB', () => {
    const data = fs.readFileSync(glbPath);
    const chunkLen = data.readUInt32LE(12);
    const jsonStr = data.toString('utf-8', 20, 20 + chunkLen);
    const gltf = JSON.parse(jsonStr);

    expect(gltf.cameras || []).toHaveLength(0);
    const ext = gltf.extensions || {};
    expect('KHR_lights_punctual' in ext).toBe(false);
  });

  it('verifies calculateHighlightedSegments adheres to the canonical rounding contract', () => {
    // Baseline / zero / invalid
    expect(calculateHighlightedSegments(0)).toBe(0);
    expect(calculateHighlightedSegments(-0.1)).toBe(0);
    expect(calculateHighlightedSegments(NaN)).toBe(0);

    // Canonical thresholds
    expect(calculateHighlightedSegments(0.05)).toBe(2); // 0.05 * 48 = 2.4 -> 2
    expect(calculateHighlightedSegments(0.071002)).toBe(3); // t_review: 0.071002 * 48 = 3.408 -> 3
    expect(calculateHighlightedSegments(0.084705)).toBe(4); // t_alert: 0.084705 * 48 = 4.065 -> 4

    // Midpoint & maximum
    expect(calculateHighlightedSegments(0.5)).toBe(24); // 24 segments (half dial)
    expect(calculateHighlightedSegments(1.0)).toBe(48); // 48 segments (full dial)
    expect(calculateHighlightedSegments(1.5)).toBe(48); // clamped to 48
  });
});
