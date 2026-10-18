import { describe, it, expect } from 'vitest';
import fs from 'fs';
import path from 'path';
import { PIPELINE_STAGES } from '../ModelCard3DVisualizer';

describe('Model Pipeline GLB Integration & Architectural Accuracy', () => {
  it('verifies the GLB asset exists locally in frontend/public/models and is non-empty', () => {
    const glbPath = path.resolve(__dirname, '../../../public/models/model-pipeline.glb');
    expect(fs.existsSync(glbPath)).toBe(true);
    const stats = fs.statSync(glbPath);
    expect(stats.size).toBeGreaterThan(400000); // 465,796 bytes
  });

  it('verifies that exactly four pipeline stages are defined with correct indices', () => {
    expect(PIPELINE_STAGES).toHaveLength(4);
    expect(PIPELINE_STAGES.map((s) => s.index)).toEqual([0, 1, 2, 3]);
    expect(PIPELINE_STAGES.map((s) => s.stageNumber)).toEqual(['01', '02', '03', '04']);
  });

  it('verifies Stage 1 schema validation and zero-leakage integrity metadata', () => {
    const stage1 = PIPELINE_STAGES[0];
    expect(stage1.name).toBe('Feature Ingestion Bus');
    expect(stage1.technicalLabel).toBe('Schema & Leakage Validator');
    expect(stage1.role).toContain('67 transaction features');
    expect(stage1.role).toContain('isFraud');
    expect(stage1.artifactFile).toBe('data/synthetic_smoke_fixture.csv');
    expect(stage1.artifactSha).toBe('da00179ebf37970ec8907d11cfb366d170ddd5b2b41370e881bf92359b7d17de');
    expect(stage1.accentColor).toBe('#68D8CB');
  });

  it('verifies Stage 2 HistGradientBoostingClassifier parameters and deterministic metrics', () => {
    const stage2 = PIPELINE_STAGES[1];
    expect(stage2.name).toBe('Primary Estimator');
    expect(stage2.technicalLabel).toBe('HistGradientBoostingClassifier');
    expect(stage2.artifactFile).toBe('models/artifacts/hgb_base.joblib');
    expect(stage2.artifactSha).toBe('b20aa6fa375303741338bca971098195f5ae72d5e1fee3882e0553172fa3b70f');

    const rocParam = stage2.metrics.find((m) => m.label.includes('ROC-AUC'));
    expect(rocParam?.value).toBe('0.5836');

    const seedParam = stage2.keyParams.find((p) => p.label.includes('Random Seed'));
    expect(seedParam?.value).toContain('11');
  });

  it('verifies Stage 3 Platt scaling calibration thresholds match canonical frozen policy', () => {
    const stage3 = PIPELINE_STAGES[2];
    expect(stage3.name).toBe('Sigmoid Calibrator');
    expect(stage3.technicalLabel).toContain('Platt Scaling');
    expect(stage3.artifactFile).toBe('models/artifacts/calibrator_sigmoid.joblib');
    expect(stage3.artifactSha).toBe('00c519243765bfd7844ed877cec0dd3caa2e45310aa47e457647680c8b787fb4');

    const alertThresh = stage3.keyParams.find((p) => p.label.includes('t_alert'));
    expect(alertThresh?.value).toContain('0.0847');

    const reviewThresh = stage3.keyParams.find((p) => p.label.includes('t_review'));
    expect(reviewThresh?.value).toContain('0.0710');

    const eceMetric = stage3.metrics.find((m) => m.label.includes('ECE'));
    expect(eceMetric?.value).toContain('0.0077');
  });

  it('verifies Stage 4 epistemic disagreement residualizer parameters and thresholds', () => {
    const stage4 = PIPELINE_STAGES[3];
    expect(stage4.name).toBe('Disagreement Engine');
    expect(stage4.technicalLabel).toContain('RankResidualizer');
    expect(stage4.artifactFile).toBe('models/artifacts/residualizer_u2.joblib');
    expect(stage4.artifactSha).toBe('10cadc14aa4f8781020079c9f23c030beb392a294066b56de18d4c972ee784a4');
    expect(stage4.accentColor).toBe('#B4A0F8');

    const epistemicThresh = stage4.keyParams.find((p) => p.label.includes('u_th'));
    expect(epistemicThresh?.value).toContain('0.526773');

    const corrMetric = stage4.metrics.find((m) => m.label.includes('Spearman'));
    expect(corrMetric?.value).toContain('0.0609');
  });
});
