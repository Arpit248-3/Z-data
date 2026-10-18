# Codebase Concerns

**Analysis Date:** 2026-10-18

## Tech Debt

**Pytest Configuration & Reference Path Collision:**
- Issue: Running bare `pytest` from the command line without `-o "pythonpath=."` fails during collection because Pytest's default import path traverses into `reference/architecture/IBM-main` and attempts to import legacy packages (`data.splits`, `eval.bootstrap`, `models.base`).
- Files: `tests/`, `reference/architecture/IBM-main/`
- Impact: Developers running standard `pytest` encounter 15 collection errors.
- Fix approach: Add a root `pytest.ini` or `pyproject.toml` containing:
  ```ini
  [pytest]
  pythonpath = .
  testpaths = tests
  ```

**In-Memory JSONL Iteration for Replay and Cases:**
- Issue: `backend/app/services/replay.py` and `backend/app/services/cases.py` read `results/replay_rows.jsonl` (2.8 MB) and `results/cases.jsonl` (1.7 MB) by streaming and iterating lines on every paginated request without persistent indexed storage.
- Files: `backend/app/services/replay.py`, `backend/app/services/cases.py`, `results/replay_rows.jsonl`
- Impact: Fast and sufficient for the 2,000-row synthetic fixture (~5ms), but will degrade if row counts scale into hundreds of thousands.
- Fix approach: If scaling beyond demonstration scale, convert JSONL fixtures to SQLite or indexed memory-mapped tables.

## Known Limitations

**Synthetic Smoke Fixture Scope:**
- Symptoms: Metrics indicate a baseline fraud recall of $9.01\%$ (10 of 111 frauds detected at $6.525\%$ capacity).
- Files: `results/results.json`, `data/synthetic_smoke_fixture.csv`, `README.md`
- Trigger: Natural consequence of the small synthetic fixture ($N=2,000$ test rows).
- Clarification: The system is certified `SYNTHETIC_SMOKE_ONLY`. It is designed exclusively for offline architectural verification of capacity governance under covariate shift, not as a commercial production clearance benchmark.

**Scaffolded UI Interactions:**
- Symptoms: Certain buttons in the UI (e.g. Export CSV, Analyst Override Write, SHAP Explanations) are static or disabled.
- Files: `frontend/src/features/case-explorer/CaseExplorerPage.tsx`, `frontend/src/features/sandbox/SandboxPage.tsx`
- Trigger: Backend intentionally implements read-only offline contracts and has explanations disabled (`explanations.enabled: false`).
- Workaround: UI accurately displays disabled states and informational notices per `DESIGN.md:Section 2`.

## Security Considerations

**Joblib Deserialization Security:**
- Risk: Loading untrusted `.joblib` files can lead to arbitrary code execution if weights are replaced by an attacker.
- Files: `models/artifacts/*.joblib`, `backend/app/services/artifacts.py`, `models/base.py`
- Current mitigation: Companion metadata files (`*.meta.json`) verify provenance, and `scripts/validate_artifacts.py` performs SHA-256 preflight checks before running the demo.
- Recommendations: Maintain strict filesystem permissions on `models/artifacts/` and avoid accepting binary model uploads over the network.

**Target & Identifier Leakage Prevention:**
- Risk: Analysts or clients submitting test payloads containing ground truth (`isFraud`) or tracking IDs (`TransactionID`) could artificially bias model scores or leak labels.
- Files: `backend/app/schemas.py:SandboxScoreRequest`, `tests/test_api_security.py`
- Current mitigation: Recursive schema validator rejecting `isFraud`, `true_label`, `target`, `label`, `y_true`, `TransactionID`, and non-finite numbers with HTTP 422.

## Performance Bottlenecks

**3D Canvas Initial Load & WebGL Contexts:**
- Problem: Overview page mounts a Three.js canvas for the Signal Core Planar Radar (`SignalCoreScene.tsx`), and Sandbox mounts a 3D Decision Orb (`SandboxDecisionOrb3D.tsx`). On low-end GPUs or headless environments, WebGL context creation may drop frames.
- Files: `frontend/src/components/SignalCoreScene.tsx`, `frontend/src/components/SignalCoreFallback.tsx`
- Cause: Complex shader materials and particle systems.
- Improvement path: Built-in 2D SVG vector fallback (`SignalCoreFallback.tsx`) is already implemented and can be toggled by the user or triggered on WebGL failure.

**Single-Threaded Model Inference:**
- Problem: Scikit-learn's `HistGradientBoostingClassifier` and Platt scaling are CPU-bound.
- Files: `backend/app/services/scoring.py`
- Cause: Synchronous execution within the FastAPI async event loop.
- Improvement path: Current single-sample latency is exceptionally fast (<5ms, well within AC5 < 50ms requirement). For high-concurrency production load, wrap scoring calls in `fastapi.concurrency.run_in_threadpool`.

## Fragile Areas

**Frozen Policy Tuning Coupling:**
- Files: `policy/frozen_policy.json`, `config.yaml`, `results/results.json`, `frontend/src/`
- Why fragile: Canonical thresholds ($t_{\text{alert}} = 0.084705, t_{\text{review}} = 0.071002, u_{\text{threshold}} = 0.526773$) and review budget ($B = 130$) are tightly coupled across backend verification, test assertions, and frontend UI displays.
- Safe modification: Any retuning of thresholds must re-run `scripts/run_phase5_evaluation.py`, update `policy/frozen_policy.json` and `results/results.json`, and pass all 109 Python tests.

**Test Set Access Governance:**
- Files: `logs/test_looks.log`, `scripts/run_phase5_evaluation.py`
- Why fragile: SignalGate enforces strict test look governance (`G3_LOOK_1`, `G5_LOOK_2_FINAL`). Arbitrary test set evaluations without logging violate project audit integrity.
- Safe modification: Always consult the protocol before running evaluation pipelines against test splits.

## Scaling Limits

**Current Capacity:**
- Synthetic fixture size: 10,000 total transactions (2,000 test transactions).
- Review queue capacity: $B = 130$ manual reviews ($6.525\%$ of test set).
- Live scoring throughput: ~250 requests/sec on local CPU.
- Limit: File-based JSONL streaming degrades beyond ~100,000 transactions.

## Dependencies at Risk

- None currently at risk. All core dependencies (`fastapi 0.115`, `scikit-learn 1.6`, `react 18.3`, `three 0.160`, `vite 5.4`) are modern, actively maintained, and fully compatible with Python 3.13 and Node 20.

## Missing Critical Features

- Live Streaming WebSockets: Currently, shift replay operates via paginated polling (`GET /api/replay/rows`). A WebSocket channel could provide server-pushed telemetry if required in future phases.
- Real-world Payment Connector: As documented in `README.md`, SignalGate is intentionally offline and synthetic-smoke-only.

## Test Coverage Gaps

- Current automated test coverage is extensive:
  - 109 automated tests passing in Pytest across API, models, router, governor, security, and calibration.
  - 21 automated tests passing in Vitest for React components and 3D fallbacks.
- Recommended additional test coverage:
  - Add end-to-end browser automation tests (Playwright) covering interactive walkthroughs across all 7 routes.

---

*Concerns analysis: 2026-10-18*
