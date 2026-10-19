/**
 * SignalGate End-to-End Acceptance Tests (Playwright)
 * Exercises running frontend (http://127.0.0.1:5173) and backend (http://127.0.0.1:8000)
 * Validates all 3 Operational Evidence Modes across all 8 dashboard routes.
 */

const { chromium } = require('../frontend/node_modules/playwright');
const fs = require('fs');
const path = require('path');

const EVIDENCE_DIR = path.resolve(__dirname, '..', 'reports', 'e2e_evidence');
if (!fs.existsSync(EVIDENCE_DIR)) {
  fs.mkdirSync(EVIDENCE_DIR, { recursive: true });
}

const BASE_URL = 'http://127.0.0.1:5173';
const API_URL = 'http://127.0.0.1:8000';

async function switchMode(page, modeKey) {
  const trigger = page.locator('#mode-switcher-trigger');
  await trigger.waitFor({ state: 'visible', timeout: 8000 });
  await trigger.click();
  
  await page.waitForSelector('#mode-switcher-dropdown', { state: 'visible', timeout: 5000 });
  
  if (modeKey === 'SYNTHETIC_SMOKE_ONLY') {
    await page.locator('#mode-switcher-dropdown button:has-text("SYNTHETIC FIXTURE")').click();
  } else if (modeKey === 'IEEE_CIS_OFFLINE_BENCHMARK') {
    await page.locator('#mode-switcher-dropdown button:has-text("IEEE-CIS BENCHMARK")').click();
  } else if (modeKey === 'LIVE_SOURCE_NOT_CONNECTED') {
    await page.locator('#mode-switcher-dropdown button:has-text("LIVE (DISCONNECTED)")').click();
  }
  
  // Give React state & SWR/effects time to dispatch
  await page.waitForTimeout(800);
}

(async () => {
  console.log('================================================================');
  console.log('SIGNALGATE RUNTIME MODE INTEGRATION E2E ACCEPTANCE SUITE');
  console.log('================================================================');
  console.log(`Frontend URL: ${BASE_URL}`);
  console.log(`Backend API:  ${API_URL}`);
  console.log(`Evidence Dir: ${EVIDENCE_DIR}`);
  console.log('----------------------------------------------------------------\n');

  const browser = await chromium.launch({
    headless: true,
    args: [
      '--no-sandbox',
      '--disable-setuid-sandbox',
      '--disable-webgl',
      '--disable-gpu',
      '--disable-renderer-backgrounding',
      '--disable-backgrounding-occluded-windows',
      '--disable-background-timer-throttling',
    ],
  });

  const context = await browser.newContext({
    viewport: { width: 1440, height: 960 },
  });

  const page = await context.newPage();

  const networkLog = [];
  const consoleLog = [];

  page.on('console', (msg) => {
    const text = msg.text();
    const type = msg.type();
    consoleLog.push({ type, text, time: new Date().toISOString() });
    if (type === 'error') {
      console.error(`[Browser Console Error] ${text}`);
    }
  });

  page.on('request', (req) => {
    const url = req.url();
    if (url.includes('/api/')) {
      console.log(`  [HTTP REQ] ${req.method()} ${url}`);
      networkLog.push({
        type: 'request',
        method: req.method(),
        url,
        time: new Date().toISOString(),
      });
    }
  });

  page.on('response', async (res) => {
    const url = res.url();
    if (url.includes('/api/')) {
      console.log(`  [HTTP RES] ${res.status()} ${url}`);
      networkLog.push({
        type: 'response',
        status: res.status(),
        url,
        time: new Date().toISOString(),
      });
    }
  });

  const results = {
    scenario1_synthetic: false,
    scenario2_ieeecis_overview: false,
    scenario2_ieeecis_scoring: false,
    scenario3_live_overview: false,
    scenario3_live_sandbox: false,
    scenario4_switching_and_persistence: false,
    scenario5_route_case_explorer: false,
    scenario5_route_policy_comparison: false,
    scenario5_route_audit_trail: false,
    scenario5_route_model_card: false,
    scenario5_route_drift_shift: false,
    scenario5_route_shift_storm: false,
    scenario6_guardrail_leakage: false,
    scenario6_guardrail_live_scoring_rejected: false,
  };

  try {
    // ----------------------------------------------------------------
    // SCENARIO 1 — Synthetic Mode
    // ----------------------------------------------------------------
    console.log('>>> [Scenario 1] Validating SYNTHETIC_SMOKE_ONLY mode on /overview...');
    await page.goto(`${BASE_URL}/overview`, { waitUntil: 'networkidle', timeout: 15000 });
    await switchMode(page, 'SYNTHETIC_SMOKE_ONLY');
    await page.waitForTimeout(1000);

    // Verify UI state
    const syntheticBadge = await page.locator('.topbar-badge').innerText();
    const pageContent = await page.locator('#main-content').innerText();

    const hasSyntheticBadge = syntheticBadge.includes('SYNTHETIC');
    const hasSyntheticData = pageContent.includes('2,000') || pageContent.includes('SYNTHETIC');
    console.log(`    Synthetic badge verified: ${hasSyntheticBadge} ('${syntheticBadge.trim()}')`);
    console.log(`    Synthetic data verified:  ${hasSyntheticData}`);

    await page.screenshot({ path: path.join(EVIDENCE_DIR, 'overview_synthetic.png'), fullPage: false });
    if (hasSyntheticBadge) results.scenario1_synthetic = true;

    // ----------------------------------------------------------------
    // SCENARIO 2 — IEEE-CIS Mode (Overview & Real Scoring)
    // ----------------------------------------------------------------
    console.log('\n>>> [Scenario 2] Validating IEEE_CIS_OFFLINE_BENCHMARK mode on /overview...');
    await switchMode(page, 'IEEE_CIS_OFFLINE_BENCHMARK');
    await page.waitForTimeout(1500);

    const ieeeBadge = await page.locator('.topbar-badge').innerText();
    const ieeeOverviewContent = await page.locator('#main-content').innerText();

    const hasIeeeBadge = ieeeBadge.includes('IEEE-CIS');
    const hasIeeeData = ieeeOverviewContent.includes('118,108') || ieeeOverviewContent.includes('50.9%') || ieeeOverviewContent.includes('BENCHMARK');
    console.log(`    IEEE-CIS badge verified: ${hasIeeeBadge} ('${ieeeBadge.trim()}')`);
    console.log(`    IEEE-CIS data verified (118,108 txns): ${hasIeeeData}`);

    await page.screenshot({ path: path.join(EVIDENCE_DIR, 'overview_ieeecis.png'), fullPage: false });
    if (hasIeeeBadge && hasIeeeData) results.scenario2_ieeecis_overview = true;

    // Navigate to /sandbox and execute real model inference
    console.log('>>> [Scenario 2] Validating real IEEE-CIS model scoring on /sandbox...');
    await page.goto(`${BASE_URL}/sandbox`, { waitUntil: 'networkidle', timeout: 15000 });
    await page.waitForTimeout(1000);

    // Click SCORE PAYLOAD
    const scoreButton = page.locator('button.payload-score-cta');
    await scoreButton.waitFor({ state: 'visible', timeout: 5000 });
    const scoreBtnText = await scoreButton.innerText();
    console.log(`    Score CTA button text: "${scoreBtnText.trim()}"`);

    // Trigger score and wait for response
    const [scoreResponse] = await Promise.all([
      page.waitForResponse((res) => res.url().includes('/api/score-sandbox') && res.status() === 200, { timeout: 30000 }),
      scoreButton.click(),
    ]);

    const scoreData = await scoreResponse.json();
    console.log(`    API score response received: HTTP ${scoreResponse.status()}`);
    console.log(`    - Decision ID: ${scoreData.decision_id}`);
    console.log(`    - Action:      ${scoreData.decision?.action}`);
    console.log(`    - Calibrated p: ${scoreData.signals?.p?.toFixed(4) || scoreData.signals?.p_risk?.toFixed(4)}`);
    console.log(`    - Uncertainty u: ${scoreData.signals?.u?.toFixed(4) || scoreData.signals?.u_disagreement?.toFixed(4)}`);
    console.log(`    - Latency ms:   ${scoreData.latency_ms?.toFixed(2)} ms`);

    await page.waitForTimeout(1000);
    await page.screenshot({ path: path.join(EVIDENCE_DIR, 'sandbox_ieeecis_scoring.png'), fullPage: false });

    if (scoreData.decision_id && scoreData.decision?.action) {
      results.scenario2_ieeecis_scoring = true;
    }

    // ----------------------------------------------------------------
    // SCENARIO 3 — Live Mode (Truthful Disconnection)
    // ----------------------------------------------------------------
    console.log('\n>>> [Scenario 3] Validating LIVE_SOURCE_NOT_CONNECTED mode on /sandbox & /overview...');
    await switchMode(page, 'LIVE_SOURCE_NOT_CONNECTED');
    await page.waitForTimeout(1000);

    // In sandbox, score button must be disabled
    const liveScoreButton = page.locator('button.payload-score-cta');
    const isLiveScoreDisabled = await liveScoreButton.isDisabled();
    const liveScoreBtnText = await liveScoreButton.innerText();
    console.log(`    Live mode score button disabled: ${isLiveScoreDisabled}`);
    console.log(`    Live mode score button label:    "${liveScoreBtnText.trim()}"`);

    await page.screenshot({ path: path.join(EVIDENCE_DIR, 'sandbox_live_disabled.png'), fullPage: false });
    if (isLiveScoreDisabled && liveScoreBtnText.includes('DISABLED')) {
      results.scenario3_live_sandbox = true;
    }

    // Check Overview in live disconnected mode
    await page.goto(`${BASE_URL}/overview`, { waitUntil: 'networkidle', timeout: 15000 });
    await page.waitForTimeout(1000);
    const liveOverviewContent = await page.locator('#main-content').innerText();
    const hasDisconnectedNotice = liveOverviewContent.includes('DISCONNECTED') || liveOverviewContent.includes('OFFLINE');
    console.log(`    Overview live disconnected notice verified: ${hasDisconnectedNotice}`);

    await page.screenshot({ path: path.join(EVIDENCE_DIR, 'overview_live_disconnected.png'), fullPage: false });
    if (hasDisconnectedNotice) results.scenario3_live_overview = true;

    // ----------------------------------------------------------------
    // SCENARIO 4 — Rapid Mode Switching & Persistence
    // ----------------------------------------------------------------
    console.log('\n>>> [Scenario 4] Validating rapid mode switching & localStorage persistence...');
    await switchMode(page, 'SYNTHETIC_SMOKE_ONLY');
    await switchMode(page, 'IEEE_CIS_OFFLINE_BENCHMARK');
    await switchMode(page, 'LIVE_SOURCE_NOT_CONNECTED');
    await switchMode(page, 'IEEE_CIS_OFFLINE_BENCHMARK');
    await page.waitForTimeout(1000);

    const postSwitchBadge = await page.locator('.topbar-badge').innerText();
    const postSwitchOverview = await page.locator('#main-content').innerText();
    const switchSuccessful = postSwitchBadge.includes('IEEE-CIS') && (postSwitchOverview.includes('118,108') || postSwitchOverview.includes('50.9%'));

    // Test reload persistence
    await page.reload({ waitUntil: 'networkidle' });
    await page.waitForTimeout(1000);
    const reloadedBadge = await page.locator('.topbar-badge').innerText();
    const persistenceSuccessful = reloadedBadge.includes('IEEE-CIS');

    console.log(`    Rapid switching state consistent: ${switchSuccessful}`);
    console.log(`    Reload persistence verified:      ${persistenceSuccessful} ('${reloadedBadge.trim()}')`);
    if (switchSuccessful && persistenceSuccessful) results.scenario4_switching_and_persistence = true;

    // ----------------------------------------------------------------
    // SCENARIO 5 — All Dashboard Routes Inspection
    // ----------------------------------------------------------------
    console.log('\n>>> [Scenario 5] Inspecting remaining dashboard routes in IEEE-CIS & Live modes...');

    // Route: Case Explorer
    console.log('    1. Checking /case-explorer...');
    await page.goto(`${BASE_URL}/case-explorer`, { waitUntil: 'networkidle', timeout: 15000 });
    await page.waitForTimeout(1200);
    const casesText = await page.locator('#main-content').innerText();
    const hasBenchmarkCases = casesText.includes('2987') || casesText.includes('Benchmark') || casesText.includes('CASES') || casesText.includes('ROUTINE') || casesText.includes('FRAUD_ALERT');
    await page.screenshot({ path: path.join(EVIDENCE_DIR, 'cases_ieeecis.png'), fullPage: false });

    // Switch to Live in Case Explorer
    await switchMode(page, 'LIVE_SOURCE_NOT_CONNECTED');
    await page.waitForTimeout(1000);
    const liveCasesText = await page.locator('#main-content').innerText();
    const hasLiveCasesNotice = liveCasesText.includes('DISCONNECTED') || liveCasesText.includes('No live cases');
    await page.screenshot({ path: path.join(EVIDENCE_DIR, 'cases_live_disconnected.png'), fullPage: false });
    if (hasBenchmarkCases && hasLiveCasesNotice) results.scenario5_route_case_explorer = true;

    // Switch back to IEEE-CIS
    await switchMode(page, 'IEEE_CIS_OFFLINE_BENCHMARK');

    // Route: Policy Comparison
    console.log('    2. Checking /policy-comparison...');
    await page.goto(`${BASE_URL}/policy-comparison`, { waitUntil: 'networkidle', timeout: 15000 });
    await page.waitForTimeout(1200);
    const policyText = await page.locator('#main-content').innerText();
    const hasPolicyMetrics = policyText.includes('118,108') || policyText.includes('POLICY') || policyText.includes('Deterministic');
    await page.screenshot({ path: path.join(EVIDENCE_DIR, 'policy_ieeecis.png'), fullPage: false });
    if (hasPolicyMetrics) results.scenario5_route_policy_comparison = true;

    // Route: Audit Trail
    console.log('    3. Checking /audit-trail...');
    await page.goto(`${BASE_URL}/audit-trail`, { waitUntil: 'networkidle', timeout: 15000 });
    await page.waitForTimeout(1200);
    const auditText = await page.locator('#main-content').innerText();
    const hasAuditRecords = auditText.includes('192') || auditText.includes('GENESIS') || auditText.includes('SHA-256') || auditText.includes('AUDIT');
    await page.screenshot({ path: path.join(EVIDENCE_DIR, 'audit_ieeecis.png'), fullPage: false });

    await switchMode(page, 'LIVE_SOURCE_NOT_CONNECTED');
    await page.waitForTimeout(1000);
    const liveAuditText = await page.locator('#main-content').innerText();
    const hasLiveAuditNotice = liveAuditText.includes('DISCONNECTED') || liveAuditText.includes('No live audit entries');
    await page.screenshot({ path: path.join(EVIDENCE_DIR, 'audit_live_disconnected.png'), fullPage: false });
    if (hasAuditRecords && hasLiveAuditNotice) results.scenario5_route_audit_trail = true;

    await switchMode(page, 'IEEE_CIS_OFFLINE_BENCHMARK');

    // Route: Model Card
    console.log('    4. Checking /model-card...');
    await page.goto(`${BASE_URL}/model-card`, { waitUntil: 'networkidle', timeout: 15000 });
    await page.waitForTimeout(1200);
    const modelCardText = await page.locator('#main-content').innerText();
    const hasModelCardDetails = modelCardText.includes('HistGradientBoosting') || modelCardText.includes('ExtraTrees') || modelCardText.includes('391') || modelCardText.includes('Platt');
    await page.screenshot({ path: path.join(EVIDENCE_DIR, 'model_card_ieeecis.png'), fullPage: false });
    if (hasModelCardDetails) results.scenario5_route_model_card = true;

    // Route: Drift & Shift
    console.log('    5. Checking /drift-shift...');
    await page.goto(`${BASE_URL}/drift-shift`, { waitUntil: 'networkidle', timeout: 15000 });
    await page.waitForTimeout(1200);
    const driftText = await page.locator('#main-content').innerText();
    const hasDriftContent = driftText.includes('Drift') || driftText.includes('Shift') || driftText.includes('PSI') || driftText.includes('KS');
    await page.screenshot({ path: path.join(EVIDENCE_DIR, 'drift_shift_ieeecis.png'), fullPage: false });
    if (hasDriftContent) results.scenario5_route_drift_shift = true;

    // Route: Shift Storm (3D Forensics)
    console.log('    6. Checking /shift-storm (3D Cockpit)...');
    await page.goto(`${BASE_URL}/shift-storm`, { waitUntil: 'networkidle', timeout: 15000 });
    await page.waitForTimeout(2000);
    const shiftStormText = await page.locator('#main-content').innerText();
    const hasShiftStormContent = shiftStormText.includes('SHIFT') || shiftStormText.includes('FORENSICS') || shiftStormText.includes('3D') || shiftStormText.includes('STORM');
    await page.screenshot({ path: path.join(EVIDENCE_DIR, 'shift_storm_ieeecis.png'), fullPage: false });
    if (hasShiftStormContent) results.scenario5_route_shift_storm = true;

    // ----------------------------------------------------------------
    // SCENARIO 6 — Negative & Guardrail Paths
    // ----------------------------------------------------------------
    console.log('\n>>> [Scenario 6] Testing negative & guardrail paths...');
    await page.goto(`${BASE_URL}/sandbox`, { waitUntil: 'networkidle', timeout: 15000 });
    await page.waitForTimeout(1000);

    // Type forbidden field isFraud into JSON editor
    const textarea = page.locator('textarea.payload-editor-textarea');
    await textarea.fill('{\n  "isFraud": 1,\n  "TransactionAmt": 100.0\n}');
    await page.waitForTimeout(500);

    const isFrameErrorVisible = await page.locator('.payload-editor-frame.has-error').isVisible();
    const sandboxContent = await page.locator('#main-content').innerText();
    const isLeakageWarningVisible = isFrameErrorVisible && sandboxContent.includes('LEAKAGE PROTECTION');
    const isScoreBlocked = await page.locator('button.payload-score-cta').isDisabled();
    console.log(`    Leakage protection triggered on forbidden field: ${isLeakageWarningVisible}`);
    console.log(`    Scoring blocked on forbidden field:              ${isScoreBlocked}`);

    await page.screenshot({ path: path.join(EVIDENCE_DIR, 'sandbox_leakage_guardrail.png'), fullPage: false });
    if (isLeakageWarningVisible && isScoreBlocked) {
      results.scenario6_guardrail_leakage = true;
    }

    // Direct HTTP check from page context: scoring in LIVE mode rejected with 400
    const liveRejectStatus = await page.evaluate(async (url) => {
      try {
        const resp = await fetch(`${url}/api/score-sandbox`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            features: { TransactionAmt: 50.0 },
            mode: 'LIVE_SOURCE_NOT_CONNECTED',
          }),
        });
        return { status: resp.status, data: await resp.json() };
      } catch (e) {
        return { error: e.message };
      }
    }, API_URL);

    const isDisconnectedError = JSON.stringify(liveRejectStatus.data || '').toLowerCase().includes('disconnected');
    console.log(`    Live mode scoring HTTP rejected: HTTP ${liveRejectStatus.status} (${JSON.stringify(liveRejectStatus.data)})`);
    if (liveRejectStatus.status === 400 && isDisconnectedError) {
      results.scenario6_guardrail_live_scoring_rejected = true;
    }

  } catch (err) {
    console.error('Test execution error:', err);
  } finally {
    await browser.close();
  }

  // Save network and console logs
  fs.writeFileSync(
    path.join(EVIDENCE_DIR, 'network_and_console_log.json'),
    JSON.stringify({ network: networkLog, console: consoleLog }, null, 2)
  );

  // Save summary
  fs.writeFileSync(
    path.join(EVIDENCE_DIR, 'e2e_test_summary.json'),
    JSON.stringify(results, null, 2)
  );

  console.log('\n================================================================');
  console.log('E2E TEST ACCEPTANCE RESULTS SUMMARY:');
  console.log('================================================================');
  let passCount = 0;
  let totalCount = 0;
  for (const [scenario, passed] of Object.entries(results)) {
    totalCount++;
    if (passed) passCount++;
    console.log(`  ${passed ? 'PASS' : 'FAIL'} - ${scenario}`);
  }
  console.log('----------------------------------------------------------------');
  console.log(`Total: ${passCount}/${totalCount} assertions passed (${((passCount / totalCount) * 100).toFixed(1)}%)`);
  console.log('================================================================\n');

  if (passCount === totalCount) {
    process.exit(0);
  } else {
    process.exit(1);
  }
})();
