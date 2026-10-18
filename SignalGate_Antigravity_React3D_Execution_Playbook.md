# SignalGate — Antigravity React + 3D Hackathon Execution Playbook

**Grounded in:** `SignalGate_v2.1_Integrated_Blueprint(1).md`  
**Target:** IBM Z Datathon 2026 — Real-Time AI for Critical Decisions  
**Goal:** deliver an actual, reproducible fraud-triage decision-support prototype—not a UI mockup or hardcoded concept.

> **Integrity rule:** this is a simulation. It must never approve, reject, or block a real payment. Dataset labels are used only in offline evaluation after a prediction has been made; they must never be an input to the router. Performance, robustness, value, and latency are measured outputs, not promises.

---

## 1. Strategy: what to build first

### The winning story

SignalGate is a **reliability and routing layer** around a fraud-risk model. It tests whether calibrated risk + independently useful disagreement/novelty signals can catch more fraud at the same analyst workload, especially when data shifts. The contribution is a measured, auditable, capacity-aware decision workflow—not a claim that a new classifier was invented.

### Hard priorities

**P0 — Must work:**
1. Inspect the existing workspace and data before changing files.
2. Environment/data preflight and a documented fallback.
3. Chronological train/calibration/validation/test split: 60/10/10/20 by time.
4. Baselines B1 and especially B2 (top-B risk ranking) on identical test rows.
5. A working calibrated baseline and a real, tested router with reason codes.
6. Primary budget fixed at **1.5× training-split fraud prevalence**; budget sweep at 1.0×, 1.5×, 2.0×, 3.0×.
7. Leakage checks, audit JSONL, configuration/split hashes, and unit tests.
8. `results/results.json` is the single source of truth for the dashboard, plots, and slides.
9. FastAPI serves the saved artifacts; the React frontend works from local APIs and can replay held-out rows chronologically. The final demo must run without internet access once dependencies and data are present.
10. Honest limitations, actual measured latency, a backup recording, and two rehearsals.

**P1 — Add if P0 passes:** disagreement from a 3-model ensemble, validation-only signal keep/drop, B3a confidence deferral, B4 random control, paired bootstrap confidence intervals, PSI/KS drift monitoring, one well-defined shift scenario, segment-level escalation counts/rates, latency benchmark.

**P2 — Optional only if stable:** novelty model, rank-residual disagreement `u2`, extra S1/S2/S3 scenarios, two-tier inference, SHAP/local attribution, conformal deferral, learned deferral, V-feature pruning, IBM Snap ML benchmark.

**Cut order when late:** visual polish → learned deferral → conformal comparison → explanation polish → two-tier inference → S3 → novelty → S1. Do **not** cut leakage controls, B2, routing tests, audit logs, uncertainty reporting, the results artifact, or latency measurements.

### Recommended stack: React frontend + Python decision engine

Use a **small monorepo with two clear runtime processes**. Keep model code in Python and browser/UI code in TypeScript. Do not reimplement the fraud policy in JavaScript.

**Backend / ML**
- Python version already supported by the actual machine or IBM LinuxONE runtime; record it and avoid forcing an unverified upgrade.
- `pandas`, `numpy`, `scikit-learn`, `scipy`, `PyYAML`, `joblib` for data, modeling and evaluation.
- `FastAPI` + `Pydantic` + `uvicorn` for typed JSON REST endpoints. Use the actual compatible versions available; keep `/docs` available locally for API verification.
- `pytest` for unit/integration tests. Do not train models during API import or ordinary dashboard page load.
- Models: `HistGradientBoostingClassifier` primary candidate, `LogisticRegression` sanity baseline/fallback, a three-member ensemble for disagreement only after the baseline works.

**Frontend / visualization**
- `React` + `TypeScript` + `Vite` for a quick static build and local development server.
- `three` + `@react-three/fiber` for a small, premium 3D Signal Core / transaction-flow visualization. `@react-three/drei` is optional; add it only if it solves a specific need and its version matches the installed React/Fiber versions.
- Version compatibility is mandatory: React Three Fiber v9 pairs with React 19; v8 pairs with React 18. Inspect existing package versions before install/update and pin a compatible combination instead of blindly installing “latest”. Official docs: https://r3f.docs.pmnd.rs/getting-started/installation
- `Recharts` (or an already-working charting package) for dashboard plots. Use one chart library, not multiple competing ones.
- Plain CSS/CSS Modules with design tokens for reliable styling. Tailwind is optional only if already configured correctly; do not add a new styling system late in the hackathon.
- `lucide-react` for consistent icons. CSS transitions and keyframes are the default motion layer; add a motion library only if it is already installed and stable.
- `Vitest` + React Testing Library for key frontend component tests if setup is straightforward. Do not let test-runner configuration block the working application.

**Integration**
- REST JSON API, with Pydantic schemas on the backend and matching TypeScript types in `frontend/src/lib/api/types.ts`.
- `results/results.json`, CSV tables, model manifest and JSONL audit logs remain the canonical source of measured results. FastAPI reads these actual artifacts.
- No database, cloud deployment, external LLM call, hosted inference, live payment integration, or secrets in the browser.
- No heavy postprocessing, giant 3D model or WebGL-dependent full-screen app. The 3D scene is a carefully scoped visual component, never the only way to access important information.

**Runtime fallback principle:** if WebGL is unavailable, reduced motion is enabled, or the device is slow, the app must render an attractive SVG/CSS fallback and retain all core functionality. If backend artifacts are missing, show a truthful empty/error state rather than generated results.
---

## 2. Repository acceptance layout

Preserve existing working code. Adapt this structure after inspecting the repository; do not blindly recreate or delete folders. Existing project layout may differ, but ownership and contracts must remain clear.

```text
signalgate/
  README.md
  config.yaml
  Makefile                         # optional; do not assume GNU Make on Windows
  docs/
    implementation_checklist.md
    api_contract.md
    decisions.md
    data_card.md
    model_policy_card.md
    runbook.md
  data/                            # keep large/private datasets out of git
    load.py
    splits.py
    feature_engineering.py         # optional and leakage-safe
    scenario_builders.py
  models/
    base.py
    calibrate.py
    ensemble.py
    novelty.py                     # conditional
    explain.py                     # conditional
  policy/
    router.py
    thresholds.py
    governor.py
    baselines.py
  eval/
    metrics.py
    bootstrap.py
    value_model.py
    latency.py
    segments.py
  backend/
    app/
      main.py                      # FastAPI app + API route registration
      dependencies.py
      schemas.py                   # Pydantic request/response types
      services/
        artifacts.py
        overview.py
        cases.py
        replay.py
        audit.py
        scoring.py
    requirements.txt
  frontend/
    package.json
    package-lock.json
    vite.config.ts
    tsconfig.json
    index.html
    src/
      main.tsx
      App.tsx
      app/
        router.tsx
        AppShell.tsx
      components/
        Sidebar.tsx
        TopBar.tsx
        StatusBadge.tsx
        MetricCard.tsx
        EmptyState.tsx
        ErrorState.tsx
        SignalCoreScene.tsx
        SignalCoreFallback.tsx
      features/
        overview/
        shift-storm/
        case-explorer/
        policy-comparison/
        drift-shift/
        audit-trail/
        model-card/
        sandbox/
      lib/
        api/client.ts
        api/types.ts
        api/hooks.ts
        format.ts
      styles/
        tokens.css
        global.css
        components.css
      tests/
  scripts/
    preflight.py
    run_pipeline.py
    run_latency.py
    validate_artifacts.py
    start_demo.ps1                  # Windows convenience launcher if stable
    start_demo.sh                   # optional POSIX launcher
  tests/
    test_splits.py
    test_router.py
    test_metrics.py
    test_features.py
    test_artifacts.py
    test_api.py
  logs/
    audit.jsonl
    test_looks.log
    environment.txt
  results/
    results.json
    tables/
    figs/
    submission/
```

The model/router/evaluation layer is pure Python and testable without FastAPI. FastAPI calls services and serializes validated results; it must not duplicate modeling logic. React calls typed API wrappers and must not calculate ML predictions or synthesize performance metrics locally. The Three.js scene consumes frontend state derived from actual API/replay records but never claims to compute fraud decisions itself.
---

## 3. How to use Antigravity, GSD and browser tools

### Antigravity's role

Keep the **main Antigravity agent as the integration owner**. Ask it to inspect the repo, propose small phases, edit one bounded set of files, run commands, read the actual test output, and summarize changed files after every phase. Do not let several agents concurrently rewrite `policy/router.py`, the API schemas, `results/results.json`, or the frontend design tokens.

### If by “Get Shit Code” you mean Get Shit Done (GSD)

Use GSD only as an optional planning/execution wrapper. Confirm the exact extension/repository/publisher and Antigravity compatibility before installing. The original `gsd-build/get-shit-done` repository is archived; the project page currently identifies the maintained continuation as `gsd-open/get-shit-done-redux`, with package `@opengsd/get-shit-done-redux`. Verify the installation path and runtime support yourself before proceeding; do not blindly install a similarly named extension or run an unreviewed setup script. Sources: https://github.com/gsd-open/get-shit-done-redux and https://github.com/gsd-build/get-shit-done/blob/main/docs/ARCHITECTURE.md

If you already have a trustworthy compatible GSD build installed, map the project once, plan one phase at a time, execute one phase, run verification, and review the diff. If it is not installed, use the prompts in this document; do not lose more than 10 minutes setting up another framework. Never enable broad “skip permissions” modes just to save clicks; inspect destructive changes and package installs.

### Highest-value browser tooling

- Use Antigravity's built-in browser subagent / Chrome DevTools integration to open the actual running frontend, inspect console/network errors, click every control, resize the viewport and verify keyboard/focus behavior. Chrome DevTools for agents documents Antigravity support and notes browser access can expose authenticated page content, so use a clean test browser profile and do not expose personal sessions/secrets: https://developer.chrome.com/docs/devtools/agents/get-started
- If the browser integration is missing, check Antigravity Customizations → Marketplace. The official marketplace supports plugins with skills, MCP servers, rules and subagents: https://www.antigravity.google/docs/marketplace
- Optional: use an official/verified design or frontend skill if it actually helps build accessible React layouts. Avoid installing many overlapping UI generators.
- Optional: GSD for planning only; never let it change core router/evaluation logic without inspection.

### Agent delegation

Good parallel tasks after API contracts are frozen:
- Agent A: review leakage/metric semantics; read-only at first.
- Agent B: build reusable React UI components from a written component contract.
- Agent C: perform a browser-based UX/console audit after the app is running.

Bad parallel tasks: multiple agents independently designing API JSON shapes; multiple agents editing the same files; UI agent inventing sample metrics while backend agent is changing schemas.

**Time box for new tooling: 10 minutes max.** If setup is not stable and useful quickly, skip it and continue with native Antigravity prompts.
---

# 4. Copy-paste Antigravity prompts

Run the prompts **one at a time**. After each one, inspect the changed files and run its acceptance commands before moving on. Replace only the workspace-specific paths that do not exist. The prompts deliberately tell Antigravity to inspect before assuming the repo is empty.

## Prompt 0 — Master project rules and controlled execution

Paste this first into the main Antigravity agent. Treat it as the governing system specification for this workspace.

```text
You are the technical lead, staff-level full-stack engineer, ML engineer, skeptical evaluator, and integration owner for SignalGate, based on `SignalGate_v2.1_Integrated_Blueprint(1).md` or the equivalent blueprint available in this workspace.

MISSION
Build a genuinely working, reproducible fraud-triage decision-support system. It must have a real Python/scikit-learn pipeline, a typed FastAPI backend, and a premium React + TypeScript frontend with a small React Three Fiber visualization. This is not a mockup. The browser UI must be connected to real API responses and saved experiment artifacts. Do not claim that the project has been built until the commands actually run and the key user flows have been exercised.

FIRST ACTION — INSPECT, DO NOT IMMEDIATELY REWRITE
1. Inspect the current repository/tree, git status/diff, READMEs, configs, tests, available datasets, active Python environment, Node/npm versions, installed dependency versions, OS/architecture and available memory.
2. Read the entire SignalGate v2.1 blueprint. Extract CORE, CONDITIONAL and STRETCH requirements into `docs/implementation_checklist.md`, mapping every requirement to code paths, tests and evidence artifacts.
3. Determine whether the workspace already has a model pipeline, backend, frontend, dataset, design system or package manager. Keep working code; never replace the app wholesale just because a new scaffold is easier.
4. Report actual state: what works, what fails, what is missing, highest risks, installed versions and next smallest action. Then implement in narrow phases.

TECH STACK (PREFERRED, BUT INSPECT BEFORE PINNING)
- Backend/model: Python supported by the current runtime, pandas, numpy, scikit-learn, scipy, PyYAML, joblib, FastAPI, Pydantic, uvicorn and pytest.
- Frontend: React + TypeScript + Vite.
- Charts: Recharts (or a single existing working chart package).
- 3D accent: `three` + `@react-three/fiber`; `@react-three/drei` is optional, not mandatory.
- Styling: CSS variables, CSS Modules/plain CSS. Do not introduce a fresh CSS framework unless existing setup makes it safer.
- Icons: lucide-react if available; otherwise use the existing icon set.
- Version rule: inspect package versions and pin a mutually compatible set. React Three Fiber v9 pairs with React 19; v8 pairs with React 18. Do not blindly install latest versions.
- REST JSON between browser and FastAPI. Pydantic response schemas are the backend truth; mirror them in `frontend/src/lib/api/types.ts` and `docs/api_contract.md`.
- Do not add a database, external LLM, cloud deployment, live payment connection, or secrets to the browser.

ARCHITECTURAL BOUNDARIES
- The fraud models, thresholds, router, evaluation and metrics remain Python modules that can be tested without FastAPI.
- FastAPI is a thin API layer over those services and the saved artifacts. No training on import; no hidden training during dashboard load; no duplicate router logic in TypeScript.
- React calls real API endpoints. It can format and visualize returned data but cannot invent or locally substitute performance KPIs.
- Three.js is a visual layer only. It may reflect replay state, route counts and signal status returned by the backend; it must never be represented as the actual classifier or risk computation.
- `results/results.json`, CSV evidence, model/feature manifest, configuration/split hashes and JSONL audit logs are the source of truth for measured evaluation.
- Final demo should run offline once dependencies/data/artifacts are present. A missing API/artifact must produce a clear setup/error state, not a fake “ready” screen.

NON-NEGOTIABLE SCIENTIFIC RULES
- Preserve chronological 60/10/10/20 train/calibration/validation/test split using TransactionDT for ordering only.
- Raw TransactionID and TransactionDT must not enter the model matrix. Labels, post-hoc segment values and evaluation-only fields must be excluded from inference features.
- Fit preprocessors, feature selection, model/ensemble, novelty, calibration, thresholds and keep/drop choices only on permitted partitions. No final-test tuning.
- Compare policies on identical held-out test rows and equal touched-rate budgets.
- Primary touched-rate budget = 1.5x training-split fraud prevalence. Sweep 1.0x, 1.5x, 2.0x and 3.0x where feasible.
- touched_rate = (FRAUD_ALERT + MANUAL_REVIEW) / all transactions. Report HELD/DEFERRED separately.
- Model scoring/router inputs never include true labels. True labels may be joined only after predictions are emitted for offline evaluation; the live/sandbox scoring API must not accept true_label.
- ROUTINE means “not escalated by this policy,” never approved or guaranteed legitimate. No real transaction is approved/rejected/blocked.
- Missing/invalid required signal fails closed to MANUAL_REVIEW / R0_SIGNAL_UNAVAILABLE. High novelty alone is not proof of fraud. Capacity overflow remains visible as HELD/DEFERRED / R6_CAPACITY_DEFERRED.
- Synthetic smoke fixtures and synthetic shift are explicitly labelled. Never mix them into benchmark claims.
- Calibration does not automatically improve ranking under a monotone mapping. State results correctly.
- SHAP, conformal, learned deferral, two-tier inference, V-feature pruning and Snap ML are optional. No optional feature may break the reliable scikit-learn fallback.
- No claim of savings, real-time SLA, accelerator use, supported explanations, fairness certification or production readiness without direct evidence.

API CONTRACT RULES
- Implement typed, versioned responses and stable error envelopes. At minimum: health/status, overview/results, policy comparison, scenarios, cases, case details, replay records, audit, and a manual scoring sandbox.
- Keep offline replay/evaluation data distinct from the score endpoint. The replay response can include a separately marked offline label for computing confident misses; the router is called before the label is attached. The manual scoring endpoint must reject target/label/ID/raw-time fields.
- Configure CORS only for the local frontend origins actually used. Do not use wildcard credentialed CORS.
- Bound pagination and replay batch sizes. Do not load the entire dataset into a response.
- On absent/corrupt artifact, return an accurate 503/structured error or status, not fabricated values.

IMPLEMENTATION AND PROOF RULES
- Before a phase, list files to create/change and why.
- Work in small phases and preserve a clean rollback point.
- Add tests for critical paths. Run actual commands and report exact pass/fail; never claim a test passed without running it.
- No placeholder TODO/pass modules described as done. Unsupported functionality should return an explicit status and be labelled in UI/docs.
- Save measured evidence in artifacts. Charts, dashboard, README and pitch numbers must consume the same frozen results.
- Log seeds, package/runtime metadata, file hashes, split hash, config hash and planned test-look entries.
- Review diffs; do not weaken tests simply to make them green.

VISUAL DIRECTION
Design an exceptional, editorial-grade “fraud operations intelligence” product: deep ink/navy foundation, cyan for live signal, violet for uncertainty/shift, coral for escalations, subtle grid/radial glow, polished type scale, spacious cards, custom icon-led sidebar, rich hover/focus states, clear charts, smooth but restrained motion, and small premium 3D accents.
The 3D scene should be a beautiful Signal Core / flow visualization integrated into the overview or Shift Storm page, not an overwhelming full-page game environment. It must have a static CSS/SVG fallback, reduced-motion behavior, performance limits, and no critical information trapped inside WebGL. Avoid generic over-glow, noisy gradients, fake terminal text and decorative controls that do nothing.

REQUIRED WORKFLOW
- Phase 0: audit and plan only.
- Phase 1: preflight/data integrity.
- Phase 2: leakage-safe splits and feature matrix.
- Phase 3: base model/calibration/disagreement.
- Phase 4: router/baselines/governor.
- Phase 5: evaluation, confidence intervals, shift and latency.
- Phase 6: FastAPI schema/service/API layer.
- Phase 7: React app shell, design system and 3D scene.
- Phase 8: pages, live API wiring, replay and case drilldown.
- Phase 9: integration, end-to-end test and offline demo runbook.
- Phase 10: visual polish/accessibility/performance.
- Phase 11: independent red-team audit.
- Phase 12: evidence freeze/submission pack.
Do not skip ahead to 3D polish before the measured pipeline and API contract exist.

AFTER EVERY PHASE, REPORT
1. What changed.
2. Files created/modified.
3. Exact commands actually run and pass/fail.
4. Evidence artifacts and provenance.
5. Remaining blockers/risks.
6. Next smallest task and acceptance gate.

Start with repository/data/environment inspection and the checklist only. Do not begin wholesale scaffolding yet.
```

## Prompt 1 — Environment and data reality check

```text
Execute Phase 1: preflight the actual environment and dataset. Do not train the full model yet.

Inspect:
- Python version, OS and architecture (`platform`, `sys.version`, `platform.machine()`; `lscpu` if available), memory if available, and versions/import status of pandas, numpy, scipy, scikit-learn, FastAPI, Pydantic, uvicorn, joblib, PyYAML, pytest, Node.js, npm and installed frontend packages (React, Vite, three, @react-three/fiber, charting library).
- Whether LinuxONE Community Cloud is available from this workspace. Do not infer hardware or accelerator access from the project name.
- Which actual dataset files are present. Prioritize the approved IEEE-CIS files if already available and authorized. If unavailable, check for the official starter sample or an existing local data artifact.
- For every found dataset: file path, byte size, SHA-256, row count, columns, missingness overview, TransactionDT range, label column, fraud count/prevalence, and whether TransactionID is unique. Do not print sensitive row-level data.

Create or update:
- `scripts/preflight.py` with repeatable checks and clear failure messages.
- `logs/environment.txt` with environment/package/platform facts.
- `docs/data_card.md` with data source, license/access note, schema, row count, prevalence, chronology, known limitations, and file hash.
- `docs/decisions.md` recording selected dataset and fallback decisions.

DATA RULES
- Never manufacture a dataset and describe it as IEEE-CIS or IBM data.
- If no benchmark dataset is available, make a tiny deterministic synthetic fixture solely to test imports, transforms, router, and UI; label it `SYNTHETIC_SMOKE_ONLY`, and disable benchmark claims on it.
- Keep the model feature list separate from target, IDs, time ordering field, and segment-report columns.
- Start with a time-ordered 10% prototype if the full dataset may exceed memory. Report exact sampling rule and sample hash.

Acceptance:
1. `python scripts/preflight.py` works and exits nonzero with a clear reason when required data is missing.
2. A smoke import and tiny model fit runs on the real environment.
3. The installed scikit-learn calibration API path is probed; test both the supported preferred path and an explicit, tested fallback when possible.
4. SHAP/explainer compatibility and Snap ML install/runtime may be probed for at most 30–45 minutes total; record status and move on if unavailable.

Report exact observed facts, not assumptions. Do not start UI styling in this phase.
```

## Prompt 2 — Data loading, chronological splits, and leakage guardrails

```text
Execute Phase 2: implement the real data path and temporal split contracts from the SignalGate blueprint.

Before coding, inspect existing dataset schema and reuse existing loaders where sound. Implement small modular functions, with type hints and tests:
- `data/load.py`: load the approved CSV(s), verify schema/label, handle optional identity data without making it a hard dependency, and produce a data provenance report.
- `data/splits.py`: `make_splits(df, time_col='TransactionDT') -> dict[str, DataFrame]`, ordered by time into train 0–60%, calibration 60–70%, validation 70–80%, test 80–100%. Save boundaries, counts, fraud counts, prevalence, min/max time per split, source file hash, and split hash.
- Keep true target labels in evaluation data structures only. Build an explicit feature-matrix function that cannot silently include the target, TransactionID, or raw TransactionDT.
- Start with a robust numeric-feature baseline. Avoid a complicated categorical encoder unless it is proven compatible with both selected models and tests pass. Record excluded columns and reasons.
- Handle NaN/Inf consistently and deterministically. Fit any imputers/encoders only on train. If the primary HGB path handles NaN directly, verify it rather than adding unnecessary transforms.

Leakage and integrity checks:
- No raw TransactionID or TransactionDT in model columns.
- No target/label/derived target column in inference features.
- Each later partition starts no earlier than the previous partition's end under the chosen rule; document tie handling.
- Train/calibration/validation/test row IDs do not overlap.
- Every split uses the same frozen feature column order.
- Any amount/card-frequency feature must use leakage-safe lagged/expanding or cross-fitted training features. Do not compute a whole-window group mean that allows earlier training rows to see future transactions.
- Segment attributes such as ProductCD/card4 may be retained for post-hoc reporting but must not enter the model by accident.

Add `tests/test_splits.py` and `tests/test_features.py` with tiny hand-built examples covering chronology, disjointness, missing values, forbidden columns, feature order, and deterministic outputs. Save the split report as JSON/CSV and write the split hash.

Acceptance: tests pass; a tiny real dataset slice can be loaded/split; no hardcoded counts; and no final-test labels are used in any fit/tuning step.
```

## Prompt 3 — Real model, calibration, ensemble disagreement

```text
Execute Phase 3: build the baseline and the SignalGate reliability signals. Do not build novelty or explanations until this phase is tested.

Implement:
- `models/base.py`: train `HistGradientBoostingClassifier` as primary candidate and `LogisticRegression` as a sanity baseline. Select robust, dependency-light parameters for actual runtime/memory. Provide fit and raw-score interfaces. Ensure class ordering and `predict_proba` behavior are handled correctly.
- `models/calibrate.py`: compare sigmoid calibration and isotonic calibration where the calibration set has enough examples. Fit on the disjoint calibration partition only, never on validation/test. Probe installed scikit-learn API. Use a supported pre-fitted-estimator path if available; otherwise implement the documented compatible path or a tested manual sigmoid/Platt fallback. Verify calibrated outputs are finite and in [0, 1].
- `models/ensemble.py`: fit a 3-member seed/subsample ensemble first (expand to 5 only if time/memory allow), compute disagreement `u = std(member probability)` and record member seeds. Keep the same base feature schema.
- On calibration/validation only, report Spearman correlation between p and u. If raw u is redundant, implement `u2` as a rank-residual disagreement variant fitted outside the test set and frozen before test. No test-distribution scaling.
- Compare calibrated and uncalibrated Brier score, ECE, and a reliability table/diagram if practical. State clearly that monotone calibration improves probability interpretation but does not reorder cases by itself.
- `models/novelty.py` only as a separate conditional task after P0 succeeds; choose either Isolation Forest or domain classifier, fit it on allowed training data, and keep it only if validation gains at matched budget.

Never place the true label inside the prediction function. Return prediction signals only: row id, p, u/u2 (if available), signal status, model/config identifier. Keep evaluation labels in an isolated offline table.

Save model/config artifacts reproducibly (e.g. joblib) with version metadata and a manifest. Do not commit very large model/data files if the repo policy forbids them.

Acceptance:
1. Tiny smoke fit succeeds.
2. Probabilities are finite/in range.
3. Train/calibration/validation/test usage is documented and tested.
4. Results include baseline-model comparison, Brier/ECE, p-u/u-u2 correlation, and actual fitted seed list.
5. If calibration API or ensemble member fails, the stable fallback still works and status is explicit.
```

## Prompt 4 — Tested routing policy, capacity handling, and reason codes

```text
Execute Phase 4: implement the exact policy contract in `policy/router.py`, `policy/thresholds.py`, `policy/governor.py`, and `policy/baselines.py`.

Actions and reason codes:
- `FRAUD_ALERT` / `R1_HIGH_RISK`: calibrated p >= t_alert.
- `MANUAL_REVIEW` / `R2_INTERMEDIATE_RISK`: t_review <= p < t_alert.
- `MANUAL_REVIEW` / `R3_MODEL_DISAGREEMENT`: otherwise-low-p case exceeds a validated u/u2 threshold.
- `MANUAL_REVIEW` / `R4_UNFAMILIAR_INPUT`: otherwise-low-p case exceeds validated novelty threshold.
- `MANUAL_REVIEW` / `R0_SIGNAL_UNAVAILABLE`: a required signal is missing, invalid, or a required model stage fails.
- `ROUTINE` / `R5_LOW_RISK_RELIABLE`: all required checks pass and no escalation trigger occurs.
- `HELD` or `DEFERRED` / `R6_CAPACITY_DEFERRED`: the governor cannot admit an otherwise escalated case. It must remain visibly unresolved; never silently change it to ROUTINE.

Rules:
- Validate None/NaN/Inf, probability bounds, missing required signal, invalid config, and invalid stage-two status.
- High p may never become ROUTINE. High novelty alone may never assert fraud; it may trigger review only.
- Distinguish intentional, prevalidated stage-two skip from an unavailable/failed required signal.
- Keep policy decision separate from offline label/evaluation logic.
- Fit thresholds and signal weights using validation only. `B2` must rank top-B by risk score at exactly the declared touched-rate budget; do not use a fixed threshold that accidentally breaks matching.
- Implement B1 fixed validation threshold, B2 top-B budgeted ranking, B3a confidence-based deferral, and B4 random escalation with repeatable seeds as time permits. B2 is mandatory.
- Calculate `touched_rate` using the blueprint definition: alert + manual review divided by all rows. Report HELD/DEFERRED separately and document how they are handled so budget comparisons are not misleading.
- Normalize p/u/n only with frozen validation-derived statistics before combining signals. The governor must keep queue order/capacity explicit and auditable.

Add comprehensive tests in `tests/test_router.py` and `tests/test_metrics.py`: exact threshold boundaries, invalid values, missing signal R0, high-risk, high novelty, u/u2, no-trigger ROUTINE, permitted stage-two skip, required stage-two failure, capacity deferral, queue ordering, and matched touched-budget behavior.

Acceptance: all critical test cases pass; invalid required inputs fail closed; the policy emits action + reason + raw signals + config hash; no real payments are accessed; labels are not passed to the router.
```

## Prompt 5 — Evaluation, paired confidence intervals, shift scenarios, and latency

```text
Execute Phase 5: build the evaluation engine and freeze protocol. Follow the blueprint; do not optimize against final test labels.

Implement in `eval/`:
- `metrics.py`: recall at touched rate, missed-fraud rate, precision, FPR, PR-AUC, touched/manual-review/alert rates, deferred count, fraud count/rate in each lane, ROUTINE-lane fraud rate/confident misses, amount-weighted fraud missed/caught when actual transaction amount exists, Brier/ECE and robust segment summaries.
- `bootstrap.py`: paired bootstrap on the same test-row resamples for B2-vs-SignalGate primary difference, default 1,000 resamples; fixed seed; return point estimate and 95% interval. If interval crosses zero, mark result inconclusive.
- `scenario_builders.py`: S0 natural chronological test; S1 final tail of test with sample/fraud counts; S2 one constructed real-data segment excluded from fitting/tuning in that scenario; S3 deterministic seeded covariate perturbation on selected features. Label S3 as SYNTHETIC in every output and UI. If only one scenario is practical, prioritize a correctly built S0 plus one well-defined shift scenario.
- `segments.py`: segment counts, fraud counts, touched rates, escalation rates by a suitable available column (e.g. ProductCD/card4). Handle rare/zero groups and call ratios exploratory screening only, not fairness certification.
- `value_model.py`: sensitivity analysis only. Clearly label assumed daily volume, review cost and false-alert friction; never call transaction amount “loss prevented” or “funds recovered”.
- `latency.py`: warm-up then time actual row scoring+routing and batch-32 scoring where feasible; measure p50/p95/p99. Target 5,000 calls if feasible; otherwise record actual smaller call count and limitation. Record whether preprocessing/explanation is included.
- a reproducible drift/PSI and KS report over selected features/rolling windows. Drift is a monitor signal, not a per-transaction fraud verdict.

Freeze protocol:
1. Before opening final-test outcomes, write the primary budget, seeds, candidate signals, threshold-selection method, metrics and acceptance criteria to `config.yaml`/`docs/decisions.md`.
2. At G3 record test-look #1, frozen config hash and initial S0 result. Do not retune after seeing it.
3. At G5 run only predeclared frozen shift/latency/secondary analyses; append test-look #2. Never quietly overwrite prior test results.
4. Every chart/table must be regenerated from saved artifacts. Do not hardcode any number in code or UI.

Primary budget is 1.5x training-split fraud prevalence. Also sweep 1.0x, 2.0x and 3.0x. Check acceptance targets without changing them post hoc: +2 percentage points recall with 95% CI above zero OR equal recall with >=10% fewer touched transactions; a tested shift result; lower ROUTINE-lane fraud at comparable budget; and p95 <=50ms as an engineering target, not an assumed fact.

Create `results/results.json`, CSV tables, plots, `logs/test_looks.log`, config/split hashes, and a short factual report. Include counts and confidence intervals on small scenarios. If a result is weak or negative, report it honestly and explain what it says about the policy.

Acceptance: repeated run with the same seed/config reproduces policy-independent metrics and artifacts within expected numerical tolerance; all final metrics correspond to actual row-level predictions; no test label influenced fitting or thresholds.
```

## Prompt 6 — FastAPI layer and typed API contract

```text
Execute Phase 6 only after the Python pipeline, routing tests, and evaluation artifacts exist. Build a thin FastAPI boundary around the tested Python services. Do not move or duplicate core model/policy logic into API handlers.

FIRST inspect:
- Existing service interfaces and saved artifact schema.
- Actual Python/FastAPI/Pydantic/uvicorn versions and runtime limitations.
- Whether results/results.json, prediction rows, model artifacts, audit.jsonl and scenario outputs exist. Do not create benchmark facts when artifacts are missing.

FILES / DESIGN
Create/adapt `backend/app/main.py`, `backend/app/schemas.py`, `backend/app/dependencies.py`, and small `backend/app/services/*.py` modules for artifacts, overview/results, cases, replay, audit and scoring. If an existing backend layout already exists, preserve it and document the mapping. Keep the backend easy to start from the repo root.

Required endpoints (adapt names only if an existing contract already exists; document any differences in `docs/api_contract.md`):
- `GET /api/health`: process health, API version, no implied model/data readiness.
- `GET /api/status`: dataset/artifact/model/policy readiness, benchmark-vs-synthetic status, versions, active config/split hashes when available.
- `GET /api/overview`: actual provenance metadata and summary metrics from saved results.
- `GET /api/results`: frozen result summary, artifact status, primary comparison and available evidence sections.
- `GET /api/policies/compare?budget_multiple=1.5`: only policies/budgets actually evaluated. Validate supported range and report unavailable rows explicitly.
- `GET /api/scenarios`: S0/S1/S2/S3 status, scenario type, available row/fraud counts, seed/hash/provenance. Do not invent scenarios that were not built.
- `GET /api/cases?scenario=S0&policy=signalgate&action=&q=&limit=50&offset=0`: bounded pagination and deterministic ordering. Return prediction/audit fields, not a giant raw dataset.
- `GET /api/cases/{case_id}`: case detail with risk p, disagreement u/u2 if computed, novelty/status if computed, action, reason, stage status, latency, hashes and allowed feature-value detail.
- `GET /api/replay/rows?scenario=S0&policy=signalgate&limit=100&cursor=`: ordered, bounded rows for the Shift Storm player. If the UI compares both policies, expose paired per-row outcomes and source provenance. True labels may appear only under an explicitly named `offline_evaluation` object so the frontend can calculate *offline benchmark replay* metrics. Policy predictions must be generated without the label first.
- `GET /api/audit?limit=100&offset=0&action=&reason=`: actual JSONL records; bounded and filtered.
- `GET /api/audit/export?...`: safe JSONL/CSV download for the filtered actual records if time permits.
- `POST /api/score-sandbox`: score one sample/transaction using the already loaded fitted pipeline and router; request contains only allowed feature fields. It must reject `true_label`, target/label columns, TransactionID and raw TransactionDT. Return model signal, action, reason, latency and config hash; no payment action occurs.

CONTRACT RULES
- Use Pydantic request/response models. Keep optional/uncomputed values `null` plus a status field; never replace them with invented 0.0.
- Standardize errors, e.g. `{ "error": { "code": "ARTIFACTS_NOT_READY", "message": "...", "details": {} } }`. Return appropriate 4xx/5xx instead of HTTP 200 with fake empty KPIs.
- Add API version/schema version fields and timestamps where appropriate.
- Paginate large case/audit/replay responses, cap requested limit, and validate scenario/action enums.
- Avoid reading all large CSVs on every request. Use an explicit, bounded artifact cache with file mtime/hash invalidation where appropriate.
- Do not fit a model at API import or on a GET request. Inference loads a verified existing artifact; CLI pipeline runs training/evaluation separately.
- A failed required model signal must go through the real router's fail-closed behavior, not be hidden by the API.
- CORS: permit only the actual local frontend origins from config/environment, e.g. `http://localhost:5173` and `http://127.0.0.1:5173`. No wildcard credentialed CORS.
- Never log secrets, full high-dimensional raw transactions or labels in a production-like score request. This is a simulation; make that visible.
- If artifacts are missing or invalid, `/api/status` should reveal not-ready status and dependent endpoints should return structured, truthful errors.

TESTS
Add `tests/test_api.py` with FastAPI TestClient (compatible with installed versions) to check health, status when artifacts exist/missing, schema validation, bounded pagination, invalid scenario/action, structured errors, sandbox rejection of label/ID/time fields, no router label argument, and route response shapes. Use temp fixture artifacts labelled synthetic smoke only; tests must not treat them as benchmark evidence.

DELIVERABLES
- `docs/api_contract.md` with each endpoint, request/response example shape, error codes and provenance rules.
- `backend/requirements.txt` or the repository's existing Python dependency manifest updated conservatively.
- A reliable command to start the API and a command to run API tests.
- `/docs` OpenAPI accessible locally for manual contract inspection.

ACCEPTANCE
1. FastAPI starts on the actual machine.
2. API handlers consume the existing tested model/policy/artifact services rather than duplicating logic.
3. No import-time training and no invented metrics.
4. Core endpoints and invalid-input behavior have tests.
5. If benchmark artifacts are absent, the API reports not ready rather than fake success.
```

## Prompt 7 — React + TypeScript application shell and 3D visual identity

```text
Execute Phase 7: create the actual React + TypeScript + Vite frontend and premium design system. Do not build all data-heavy pages yet; first create a stable, responsive app shell and a working API connection. Inspect existing frontend/package files before scaffolding.

DEPENDENCY PREFLIGHT
- Record Node/npm versions and current React/Vite/TypeScript versions.
- Pin compatible dependencies. `@react-three/fiber@9` pairs with React 19; `@react-three/fiber@8` pairs with React 18. Confirm actual pair from lockfile after installation.
- Install only what is needed: React, Vite, TypeScript; React Router if route-based pages are used; a single chart package (prefer Recharts unless an existing chart library is already working); lucide-react if compatible; `three` + `@react-three/fiber`; optional `@react-three/drei` only when needed.
- Use CSS variables/CSS Modules. Do not add multiple animation, chart, state-management and styling libraries at once. Use local `fetch` wrappers; no new API client framework is required.

VISUAL GOAL
Build a premium, technical, editorial-grade decision operations product—not a generic admin template. Product brand: `SignalGate`, subtitle `SHIFT-AWARE FRAUD TRIAGE`, visible simulation status `SIMULATION · NO LIVE PAYMENTS`.
- Base: deep ink/navy (`#080D18` / `#0D1424` family), panel layers (`#121C30`), restrained thin borders.
- Signal cyan for active/verified telemetry; violet for disagreement/shift; coral/orange for escalation; muted slate for secondary labels; never use color alone to communicate status.
- Strong spacing system, consistent radius, tight but legible typography, table alignment, minimal all-caps metadata, clear active nav state, useful hover/focus rings, fast transitions and well-designed empty/loading/error states.
- Avoid the usual overdone AI aesthetic: no excessive random glows, every-card gradient, meaningless waveform, stock dashboard template or fake live feed.

APP SHELL
Create:
- fixed/collapsible left sidebar with brand mark, navigation groups, custom active indicator, icons, hover/focus states, optional compact mode on narrower screens, status footer, and no dead menu items;
- top bar with page title, environment/readiness badge, active scenario or data-source context, and connection/error status derived from `GET /api/status`;
- content container/grid and global tokens for color, spacing, radii, elevations, type scale, breakpoints and motion durations;
- responsive page layout for a normal laptop first and narrow viewports second. Do not allow chart overflow or a sidebar that hides primary actions.

3D SIGNAL CORE COMPONENT
Create a reusable `SignalCoreScene.tsx` using React Three Fiber:
- A tasteful abstract decision-gate core: central glass/metal-like sphere or polyhedron, thin orbit/ring paths and small transaction nodes flowing toward three clearly represented lanes (ROUTINE, ALERT, REVIEW). Maintain restrained geometry, lighting and motion; do not use downloaded assets or depend on external 3D URLs.
- It may react to real app state (selected case/policy, replay activity, lane counts) passed as props. Do not let the 3D scene make or imply a fraud prediction.
- Keep Canvas small and bounded, with controlled DPR, modest geometry, no heavy postprocessing, no continuous expensive animation when idle, and no unbounded particle system.
- Provide an attractive `SignalCoreFallback.tsx` using SVG/CSS for WebGL errors, unsupported hardware, mobile performance, or reduced-motion preference. If the canvas crashes, core dashboard remains usable.
- Respect `prefers-reduced-motion`; pause/reduce animations when the browser tab is hidden if practical.
- Keyboard users must still be able to operate the app; scene is decorative and is not the only way to inspect metrics.

API CLIENT AND ERROR STATES
- Create typed `frontend/src/lib/api/types.ts` mirroring Pydantic responses.
- Create `api/client.ts` with one configured base URL (`VITE_API_BASE_URL`, local default) and robust timeout/network/non-2xx handling. Parse structured error messages; do not fabricate fallback KPIs on error.
- On startup, call `/api/health` and `/api/status`; show distinct “API unavailable”, “artifacts not ready”, “synthetic smoke only”, and “benchmark artifacts loaded” states.
- Never hardcode dataset row counts, recall, precision, latency or financial results into UI source. Static text such as page names/design tokens is fine.

FIRST MILESTONE
Build app shell, sidebar, topbar, tokens, loading skeleton, API status panel, one visually polished Overview placeholder that uses real `/api/status` data only, the Signal Core 3D component and SVG/CSS fallback. Do not implement page-specific fake metrics.

TESTS / ACCEPTANCE
- `npm run dev` starts, `npm run build` succeeds and TypeScript has no errors.
- API status is genuinely fetched; shutting down backend changes the visible state to API unavailable.
- 3D canvas and fallback both render; there is no app crash on WebGL failure/reduced motion.
- All navigation destinations either have real pages or a disabled/coming-next state that is clearly labeled; no dead interactions.
- Review desktop and narrow viewport, readable contrast, focus states and console output.
```

## Prompt 8 — Wire all pages, real APIs, and Shift Storm replay

```text
Execute Phase 8: implement the complete SignalGate React interface on top of the frozen FastAPI contract. Every meaningful page and control must work against real API data. Do not use hardcoded metrics, lorem ipsum, randomly generated case rows, or fake response objects in app runtime. Synthetic fixtures may be used in isolated tests only and must say `SYNTHETIC_SMOKE_ONLY`.

REQUIRED PAGES
1. Overview
   - Dataset source/name/hash, row count, fraud count/prevalence, chronological split counts, model/policy readiness, config/split hashes, primary budget, measured recall at budget, missed-fraud rate, touched/manual/alert/deferred rates, B2 comparison with paired 95% CI, latency percentiles if measured, artifact/source status.
   - Use KPI cards and a compact trend/flow visualization only where actual series exist. Null metrics display “Not measured” with reason, not zero.
2. Shift Storm
   - Real held-out replay in chronological order and side-by-side B2 vs SignalGate lanes using the exact same rows and declared touched-rate budget.
   - Controls: scenario selector limited to scenarios the backend says exist, play/pause/step/reset, bounded replay speed, row window, selected policy view and a case selection control.
   - Show counts by ROUTINE/FRAUD_ALERT/MANUAL_REVIEW/HELD or DEFERRED. Update cards and the 3D Signal Core from the replay records/state, not timers alone. The visual may animate between actual replay records but must not invent transactions.
   - Confident-miss counter = offline_evaluation label is fraud AND action is ROUTINE; label it prominently `OFFLINE HELD-OUT REPLAY`. Keep the raw labels out of the `/api/score-sandbox` route.
   - S3 must display `SYNTHETIC SHIFT` in the selector, header, charts and export. S2 must be labelled `CONSTRUCTED REAL-DATA SEGMENT` if implemented.
   - Start/pause/reset/step and scenario switching must alter actual displayed case/counters and make API requests as needed. Prevent duplicate intervals/memory leaks and stale response races.
3. Case Explorer
   - Search/paginate/filter true saved case/prediction records. Click a row to view p, u/u2 status, novelty only if actually computed, chosen lane, reason code, latency, model/policy status, hashes, and actual feature values that are allowed to display.
   - Separate model-output/routing reason from optional model explanation. Show `unsupported`, `not computed`, `timeout` or `error` accurately; no fake SHAP bars.
   - For offline test cases, label any truth/outcome field as offline evaluation-only. A live/sandbox scoring request must not accept a true label.
4. Policy Comparison
   - Select 1.0x/1.5x/2.0x/3.0x budgets only where actual outputs exist. Compare B1, B2, B3a, B4 and SignalGate only when each has been implemented and evaluated. Show touched rate, recall, precision, confident misses, CI and sample/fraud counts. Explain B2 is the primary matched-budget baseline.
   - Calibration comparison (Brier/ECE/reliability diagram) only if actually computed. Make clear monotone calibration does not itself improve ranking.
5. Drift & Shift
   - Actual PSI/KS, distribution trends and novelty share only if computed. Show sample size, fraud count, window/scenario and provenance. PSI/KS/novelty are monitoring signals, not proof of fraud or a production drift guarantee.
6. Capacity & Governor
   - Review capacity/budget, alert/review/deferred counts, queue ordering and explicit R6 cases. The queue is computed by real governor output; it must not disappear or silently convert overflow to ROUTINE.
7. Audit Trail
   - Real JSONL records with bounded pagination and lane/reason filters, visible timestamps/latency/config/split hash, status and export of filtered actual records. Redact secrets; never expose high-dimensional feature dumps unless needed and approved.
8. Model & Policy Card
   - Intended use, human oversight, data source/license, chronological split, thresholds, calibration, signals actually used, measured findings, environment, limitations, segment check caveat, synthetic scenario explanation and explicit `NOT PRODUCTION READY — NO PAYMENT ACTION`.
9. Scoring Sandbox
   - A form based on the backend's verified feature schema. Offer a real sample replay case stripped of label/ID/raw time where available. Submit to `POST /api/score-sandbox`, show returned p/signals/action/reason/latency/config hash. Handle invalid/missing fields fail-closed. Show that this is a simulation. Never include a `true_label` field in the request.

INTEGRATION RULES
- All APIs are called through the shared typed client. Do not use ad hoc fetch calls scattered through pages.
- Use clear loading skeletons, empty states, retry actions, API errors and `Not measured` statuses.
- Use bounded pagination; avoid pulling large dataset CSVs into browser memory.
- The result numbers must trace back to `/api/results`, actual replay output or a documented client-side aggregation of received replay rows. No random data generation in production code.
- Keep filters, chart tooltips, selected rows, navigation, downloads and replay controls functional with keyboard and mouse.
- Use defensive parsing of null/missing fields and API schema versions. Show a version mismatch error instead of silently using stale field names.

ACCEPTANCE TESTS
- Changing a scenario/policy/budget/filter updates the data and charts, or shows a documented unavailable status.
- Replay play/pause/reset/step functions work and counters match a hand-calculated subset of the same rows.
- A selected case displays matching detail and audit row.
- B2 and SignalGate use identical row identifiers for comparisons.
- API offline state does not show old fabricated/green “ready” values.
- S3 labelling persists in UI and exports.
- No true label is sent to scoring/router requests.
- All downloads contain the actual current filtered artifact/rows.
```

## Prompt 9 — End-to-end integration, tests, and offline demo

```text
Execute Phase 9 as the integration owner. Do not add optional modeling features. The goal is an end-to-end application that starts reliably on the actual development machine and has no contract mismatch between Python, FastAPI and React.

RUN ORDER
1. preflight dataset/runtime/package check;
2. run split/feature generation;
3. train baseline/calibration and any selected ensemble;
4. select thresholds on validation only;
5. freeze config/hash and log planned test-look #1;
6. evaluate frozen baseline/SignalGate on planned test rows;
7. run predeclared shift/latency/secondary analysis and log test-look #2;
8. validate `results/results.json`, CSVs, audit JSONL, config/split hashes and model manifest;
9. start FastAPI and test endpoints;
10. start Vite frontend and exercise pages in browser;
11. turn off internet (after local deps/artifacts exist) and repeat the demo flow;
12. run a clean documented reproduction/smoke command.

ENVIRONMENT AND STARTUP
- Preserve the actual Python environment and frontend package lock. Provide exact Windows PowerShell steps and, if inexpensive, bash equivalents. Do not assume GNU Make is installed.
- Prefer two explicit terminals if a cross-platform single-command launcher is unreliable. Clearly document backend and frontend commands and expected URLs/ports.
- Add a launcher script only if it reliably starts both processes, surfaces logs, and shuts down children cleanly on Windows. No fragile background jobs.
- Keep API base URL configurable with `VITE_API_BASE_URL`; no hardcoded production URL.
- Ensure FastAPI CORS permits only the local Vite origin used for the demo.

TESTING
- Python: run all pytest tests including router boundaries, leakage, metrics, artifacts and API schema/error tests.
- Frontend: run TypeScript checks and production build; run configured component tests if they work.
- Browser: use Antigravity browser/Chrome DevTools to verify Overview, navigation, Shift Storm, replay controls, scenario label, Case Explorer, Policy Comparison, Drift/Shift, Audit Trail, Model Card, Sandbox, API error state, narrow viewport, keyboard/focus and console/network errors.
- Confirm `npm run build` and backend tests pass; use exact output, not assumptions.
- If frontend build or API fails, fix root cause and rerun relevant checks. Do not hide errors, remove tests, or create a fake fallback KPI.

INTEGRATION BUG CLASSES TO CHECK
- Pydantic vs TypeScript field mismatches; null vs omitted fields; enum spelling; date/time formatting/time zones; pagination cursor and limits; stale API responses after filter changes; duplicate replay timer; unhandled fetch rejection; CORS; base URL; stale cached artifacts; import-time model training; missing-file exception; class order for probability; target/ID/time leakage; label accidentally sent to sandbox; API blocking inference; unbounded request or response payload.

DELIVERABLES
- `docs/runbook.md` with tested commands from clean startup through demo.
- `docs/api_contract.md` updated to match implemented responses.
- exact test/build/browser checklist with pass/fail and remaining defects.
- list each CORE/CONDITIONAL/STRETCH requirement as complete / partial / not implemented with evidence path.

ACCEPTANCE
A clean start launches backend and frontend; the API status reflects real artifact readiness; all core pages load; the replay is driven by actual saved rows; browser controls work; tests/build pass; offline demo works; there are no invented KPIs.
```

## Prompt 10 — Premium UI polish, 3D refinement, accessibility and performance

```text
Perform a frontend-only visual quality pass after the backend/API/data wiring is stable. Do not change thresholds, model behavior, metrics, result values, API semantics or the scientific freeze. No new backend logic except a strictly necessary contract bug, documented first.

QUALITY BAR
SignalGate should feel like a premium financial-risk decision console made by a strong product design and frontend engineering team. Use one coherent design system rather than a pile of effects.

DESIGN CHECKLIST
- Typography hierarchy: strong product/page heading, one concise page subtitle, quiet uppercase metadata, readable numerical values, consistent body/label sizes.
- Layout: intentional whitespace, tight alignment, consistent card geometry, stable chart heights, proper table widths, sensible responsive breakpoints, no horizontal page scroll.
- Sidebar: custom brand treatment, grouped nav labels, icon alignment, active indicator, hover/focus states, accessible collapse on mobile, status footer and clear selected page.
- Color: dark ink, cyan signal, violet uncertainty/shift, coral/orange escalation, neutral slate. Meet contrast standards and use icon/text in addition to color.
- Microinteractions: short transitions for cards, tooltip, selection, sidebar and data refresh; no long page transitions or perpetual flashing.
- Loading: skeletons that resemble the eventual layout. Empty, error, backend offline, benchmark not ready and synthetic-smoke-only are distinct states.
- Charts: legible axes/units, matching color/legend semantics, responsive sizing, accessible data summary/table alternative, helpful tooltip, sample size and source labeling.
- Tables: sticky header only where useful; readable row density; selected row state; true empty/error states; keyboard focus.
- 3D: refine signal-core lighting/material balance, ring/node motion and connection to replay state. It must be bounded and light. Avoid a full-page background that compromises text contrast. No noisy bloom/postprocessing or external 3D models.
- Fallback: test with WebGL disabled or simulate scene failure; the fallback is intentional and beautiful, not a blank rectangle. Respect reduced-motion preferences.
- Interaction: every button, toggle, navigation element and download must do what its label promises. Remove or disable nonfunctional controls truthfully.

PERFORMANCE
- Avoid unnecessary rerenders and rerendering the 3D canvas on every metric card update.
- Use memoization only where measured/clear; keep state local to relevant features.
- Bound number of replay rows and plot points. Avoid huge DOM tables.
- Lazy-load the 3D scene and non-core pages if it is simple to do so; do not let a Three.js chunk failure prevent the rest of the app from loading.
- Check browser console and network logs. No unhandled promise rejections.

ACCESSIBILITY
- Visible keyboard focus, semantic controls, meaningful button labels, accessible sidebar, form labels and validation messages.
- Color is never the only carrier of action/status.
- Respect reduced motion and browser zoom. Critical information remains in normal DOM text/tables rather than canvas-only.

VERIFY WITH BROWSER
Capture/review Overview, Shift Storm running and paused, Case Explorer selected row, Policy Comparison, Audit Trail, error state and narrow viewport. Report every issue found and what was fixed. Run production build again and re-test core interactions.

Do not fabricate numbers, add fake “live” activity, alter results for better visual balance, or turn a missing metric into 0.0.
```

## Prompt 11 — Independent red-team / acceptance audit

Use a fresh Antigravity agent/chat if possible. Ask for review first; only allow fixes after findings are grounded in code/artifact evidence.

```text
Act as a skeptical principal engineer and ML evaluation reviewer who did not build SignalGate. Read the full v2.1 blueprint, source code, tests, `results/results.json`, saved tables, config/split hashes, test-look log, model manifest, API schemas, docs and React frontend.

Do not begin with praise. Try to falsify the system's claims and determine if the UI and backend are truly dynamic rather than hardcoded.

AUDIT A — scientific validity
1. Raw TransactionDT/TransactionID/target leakage and feature-matrix construction.
2. Chronological 60/10/10/20 ordering, disjoint splits, train-only preprocessing/statistics, calibration separation and test-look logging.
3. Threshold/signal/novelty selection is validation-only; no tuning from final test labels.
4. B2 is top-B risk ranking; same test row IDs and equal budget for each policy.
5. Touched-rate arithmetic is alerts + manual review divided by total rows; deferred handled separately and transparently.
6. Correct recall, precision, false-positive rate, PR-AUC, Brier/ECE, confident misses, lane rates, amount-weighted metrics and paired bootstrap confidence intervals.
7. If a CI spans zero, the result is marked inconclusive. Synthetic and constructed shifts are correctly labelled; PSI/KS are not overstated.

AUDIT B — router/fail-safe
1. None/NaN/Inf/out-of-range probabilities or missing required signals route to R0 MANUAL_REVIEW.
2. High p cannot route to ROUTINE; high novelty alone cannot claim fraud.
3. Queue capacity overflow remains visible as R6 HELD/DEFERRED, not ROUTINE.
4. Intentional validated stage-two skip differs from a failed required stage.
5. True label is absent from prediction/router/sandbox functions and requests.

AUDIT C — API
1. FastAPI endpoints consume the real tested services and artifacts.
2. Pydantic response models and TypeScript types match; null/error/status/version/pagination handling is correct.
3. Missing/corrupt artifacts return truthful structured error/not-ready state, not 200 plus fabricated metrics.
4. CORS is restricted; payloads are bounded; no secret leaks, unsafe paths or unbounded data responses.
5. No import-time or GET-triggered training; the score sandbox has no true-label parameter.

AUDIT D — frontend/product integrity
1. Search code for hardcoded KPI/demo numbers and random production transaction generation.
2. Verify each displayed metric source. Distinguish measured result, target, assumption, not measured and synthetic smoke.
3. Filters/scenario/policy/budget/navigation/download/selected case/replay controls all change real displayed data or show a clear unsupported state.
4. Shift Storm compares the same rows; confident-miss counter uses offline labels only after predictions; S3 label is persistent.
5. 3D visualization reflects real state but does not pretend to be the model. WebGL failure/reduced motion keeps core functionality.
6. Case detail and audit row correspond to same ID; no fake SHAP chart; ROUTINE not described as approval.
7. Responsive layout, keyboard focus, semantic buttons, API offline state, console errors and stale request races.

AUDIT E — build/reproduction/claims
1. Run pytest, frontend typecheck/build, API tests, artifact validator and the documented smoke/reproduction commands.
2. Confirm frontend can run against actual local API and dashboard uses saved artifacts offline.
3. Verify environment versions, CPU/architecture and latency call counts are actually captured.
4. No unsupported “real-time SLA”, “IBM accelerator/Snap ML speedup”, “SHAP”, “saved money”, “fairness certified” or “production ready” claims.
5. Slides/README/demo numbers trace to frozen results or are labelled assumptions/targets.

For each finding include severity, file/line, direct evidence, impact, minimal fix, and regression test. Fix only blockers and high-severity defects automatically; avoid major redesign after result freeze. Re-run tests after every fix. Final response must contain a pass/partial/fail table and a stop-ship list. Be honest about anything not run.
```

## Prompt 12 — Freeze demo, verify every claim and create submission evidence

```text
Execute the final freeze only after the red-team audit. Do not retrain, retune or change the tested policy after freezing. If a critical bug forces a change, record it, rerun the full affected evaluation, update hashes and mark the new version explicitly.

1. Run the exact documented data preflight, tests, artifact validator, frozen pipeline/reproduction command, API tests, frontend typecheck/build and browser smoke checks. Save exact output.
2. Freeze current config, model/feature manifest, config SHA-256, split SHA-256, dataset SHA-256, runtime and package metadata, model seed list, test-look log, actual results, scenario provenance, latency call count, API schema version and a representative sanitized audit sample.
3. Confirm the demo can start from a clean restart with no external network access once dependencies and permitted dataset artifacts are local. The API and frontend may run as two local processes; document exact ports/commands.
4. Write `results/submission/` with:
   - frozen `results.json` and summary CSV;
   - primary 1.5x touched-budget table with B2 vs SignalGate recall difference and paired 95% CI;
   - full budget sweep if computed;
   - scenario table with provenance, sample/fraud counts and labels;
   - measured latency table, call counts and actual environment/CPU metadata;
   - calibration/segment/value sensitivity artifacts only if computed;
   - `docs/model_policy_card.md`, `docs/data_card.md`, `docs/api_contract.md`, `docs/runbook.md`;
   - config/split/dataset hashes and test-look log;
   - screenshots of Overview, Shift Storm running/paused, Case Explorer, Policy Comparison, Drift & Shift, Audit, Model Card, Sandbox and a genuine error state.
5. Keep the 3D visual aligned with the frozen replay/overview state. Do not add new 3D effects after freeze if they risk crashes.
6. Pitch evidence structure (maximum 10 slides, adapt to official rules): title/claim; confident-wrong problem; user/decision; system architecture; matched-budget method; actual primary result + CI; shift findings; latency/platform proof; responsible AI/limits; takeaway/next steps.
7. Open with a real held-out case verified in frozen artifacts. Never pre-write a fake risk score or transaction amount. Keep the phrase `offline held-out benchmark replay` near confident-miss metrics.
8. Record a 90-second backup demo of the same frozen build. Test the recording and rehearse twice, including a scenario where optional explanation/Snap ML is unavailable and the truthful fallback is shown.
9. Every pitch claim must link to an evidence path or be visibly labelled a target/assumption. If SignalGate loses to B2, show the result and present a reliability audit—not a fabricated win.
10. Final response: list project start commands, tests/builds actually run, artifact paths, current git diff/status, complete/partial/unsupported checklist and remaining issues. Do not say “ready” if the application has not been launched and verified.
```

---

## 5. Execution schedule and hard gates

Treat these as **relative time boxes from the organizers’ actual allowed start**. Confirm the official start/end/submission times rather than relying only on “tomorrow”. Run the scientific core first and build frontend pages in parallel only after the API response shape is agreed.

| Time box | Owner / deliverable | Gate / stop condition |
|---|---|---|
| First 30–45 min | Integration owner: repo/data/runtime inventory, blueprint checklist, API and frontend version compatibility | Do not build against unverified dataset/platform assumptions. |
| H0–H4 | Data/evaluation: loader, chronological splits, leakage checks, B1/B2 | G1: class counts, prevalence, source/split hashes; IDs/raw time excluded. |
| H4–H8 | Modeling/routing: calibration, three-member disagreement, validation-only keep/drop, router tests | G2: signals work and are evaluated; drop anything not useful. |
| H8–H12 | Evaluation: B2/SignalGate matched budget, config freeze, first planned test look | G3: thresholds frozen; no test-driven tuning. |
| H12–H15 | Evaluation: one useful shift, drift panel, governor and latency | G4: optional novelty/two-tier only if robust. |
| H12–H16 parallel | Backend owner: FastAPI typed schemas/services/endpoints; frontend owner: design tokens and shell against contract | No frontend-local fake metrics. Use generated empty/error states until artifacts exist. |
| H15–H18 | Paired CI, budget sweep, shift/segment/value/latency outputs, second planned test look | G5: measured result saved; stop feature work. |
| H16–H20 parallel | React pages, 3D scene/fallback, live API wiring, replay/case/audit interactions | G6: key user flows work on actual local API and match `results.json`. |
| H20–H22 | Integration test, browser QA, offline restart, accessibility/performance pass | Freeze feature scope; fix blockers only. |
| H22–H24 | Model/policy card, screenshots, backup recording, README, slide evidence, two rehearsals | G7: no risky dependency or major refactor after final freeze. |

### Role split for a four-person team

- **Data/evaluation:** data schema/hash, splits, baseline metrics, paired bootstrap, shifts, segment/value tables and result manifest.
- **Modeling/policy:** base/calibration/ensemble, router, thresholds, capacity governor and tests.
- **Backend/integration:** FastAPI schemas/endpoints, artifact loading, runtime compatibility, API tests and reproducibility.
- **Frontend/demo/QA:** React design system, 3D scene/fallback, pages, browser tests, screenshots, backup recording and pitch.

One integration owner must coordinate API changes. Freeze request/response schemas before parallel UI work. Merge at the gates, run tests after merges and preserve a known-working commit before optional dependencies.
---

## 6. The required result schema: no magic numbers in the UI

The specific schema can be extended, but it must cover at least these fields and carry schema/version provenance.

```json
{
  "schema_version": 1,
  "project": "SignalGate",
  "api_schema_version": 1,
  "source": {
    "dataset_name": "actual source name",
    "dataset_sha256": "actual hash",
    "synthetic_smoke_only": false,
    "rows": 0,
    "fraud_count": 0,
    "fraud_prevalence": 0.0
  },
  "environment": {
    "python": "actual version",
    "sklearn": "actual version",
    "platform": "actual OS/architecture/CPU details",
    "node": "actual version if frontend built",
    "react": "actual version if frontend built",
    "vite": "actual version if frontend built",
    "three_fiber": "actual compatible version if used"
  },
  "split": {
    "train_rows": 0,
    "calibration_rows": 0,
    "validation_rows": 0,
    "test_rows": 0,
    "split_sha256": "actual hash"
  },
  "policy": {
    "primary_budget_multiple": 1.5,
    "primary_touched_budget": 0.0,
    "config_sha256": "actual hash",
    "thresholds_source": "validation_only"
  },
  "comparisons": {
    "B2": {},
    "SignalGate": {},
    "paired_recall_difference": {
      "estimate": null,
      "ci95_low": null,
      "ci95_high": null,
      "bootstrap_resamples": 1000
    }
  },
  "latency": {
    "single_row_calls": 0,
    "batch_size": 32,
    "p50_ms": null,
    "p95_ms": null,
    "p99_ms": null,
    "includes_explanation": false
  },
  "test_looks": [],
  "limitations": []
}
```

This is a **shape example**, not result data. The API and frontend version metadata shown as example fields must be populated from the actual build/environment. `0` placeholders above must be replaced only by actual measured values; if no value can be computed, use `null` and surface “not measured/unavailable” in the UI. Never present the example JSON as observed evidence.

---

## 7. Demo checklist

Before judges see the app:

- [ ] Preflight displays actual dataset name/hash/count/prevalence and source.
- [ ] `SYNTHETIC_SMOKE_ONLY` cannot accidentally be shown as benchmark evidence.
- [ ] B2 and SignalGate use the same held-out rows and same touched-rate budget.
- [ ] Primary result shows estimate plus paired 95% CI, not only a headline percentage.
- [ ] Confident misses are clearly labelled as **offline held-out replay**.
- [ ] S3 has a persistent **synthetic shift** label; S2 says **constructed from real rows** if implemented.
- [ ] The selected case, p/u/u2/novelty status, reason code, route, latency, and hashes come from real prediction/audit records.
- [ ] All reason-code branches and invalid-input behavior have tests.
- [ ] Governor/deferred cases remain visible; none disappear into ROUTINE.
- [ ] p50/p95/p99 have actual call counts and conditions; a p95 target is not described as measured unless it is.
- [ ] SHAP chart appears only if a supported explainer actually computed attributions; otherwise show status.
- [ ] Snap ML/Telum/accelerator is mentioned only with direct runtime evidence.
- [ ] Dollar or business-value scenario is visibly labelled as assumptions and sensitivity, not savings.
- [ ] Every slide statistic traces to frozen `results.json` or is labelled assumption/target.
- [ ] Demo launches with internet disabled and from a clean restart.
- [ ] Backup recording and a notebook/CLI fallback are ready.
- [ ] Two timed rehearsals completed; one includes an intentionally triggered API-offline/WebGL-fallback scenario.

---

## 8. Decision rules when something breaks

- **No benchmark data:** verify official access and policy, use the approved starter sample for smoke only, label it honestly, and prioritize running on the real dataset as soon as permitted.
- **Dataset too large/OOM:** downcast safely or use a chronological prototype subset; document the precise row selection and do not claim full-data results.
- **Calibration API breaks:** use a tested fallback supported in the installed version; record the path.
- **Disagreement adds no value:** keep/drop decision says drop it; present a reliability audit rather than forcing a positive result.
- **Novelty is not helpful:** remove the novelty score from the policy; retain PSI/KS as monitoring if useful.
- **SHAP unsupported/slow:** turn off local attribution; show rule code and `explanation_status` truthfully.
- **Snap ML unavailable:** retain scikit-learn; make no accelerator claim.
- **Latency >50ms:** report actual latency, benchmark batch-32, then test two-tier or a smaller ensemble only if time permits.
- **UI is late or unstable:** reduce pages to Overview + Shift Storm + Case Explorer + Audit/Model Card; use saved artifacts with the React UI and a CLI/notebook fallback.
- **Primary result is inconclusive or worse:** do not retune on test or hide the result. Show the CI, analysis, and what did/did not help.

---

## 9. API endpoint contract to freeze before parallel UI work

These are the minimum conceptual endpoints. Antigravity may adapt names to an existing implementation, but it must document one stable contract in `docs/api_contract.md` and keep Pydantic and TypeScript in sync.

| Endpoint | Why it exists | Important rule |
|---|---|---|
| `GET /api/health` | API process health | Does not claim model/data readiness. |
| `GET /api/status` | Model/artifact/source readiness | Distinguishes benchmark, synthetic smoke and missing artifacts. |
| `GET /api/overview` | Topline actual results | Reads saved result artifacts; no hardcoded KPI. |
| `GET /api/results` | Frozen policy metrics/CI/provenance | Unmeasured fields are `null` plus a status. |
| `GET /api/policies/compare` | Matched-budget policy comparison | Same test row IDs and budget basis. |
| `GET /api/scenarios` | S0–S3 availability/provenance | Never offers unavailable scenario as computed. |
| `GET /api/cases` | Search/paginate predictions | Bounded response and deterministic ordering. |
| `GET /api/cases/{case_id}` | Detail drilldown | Predictions, reason codes, signals and hashes. |
| `GET /api/replay/rows` | Bounded chronological Shift Storm feed | Labels explicitly separated under `offline_evaluation`; router does not receive them. |
| `GET /api/audit` | Audit rows | Actual JSONL records, bounded/filterable. |
| `GET /api/audit/export` | Download filtered audit records | Exports actual selected rows only. |
| `POST /api/score-sandbox` | One-off simulated scoring | Rejects label/target/ID/raw time; no real payment action. |

The UI can calculate simple counters from returned records for the currently displayed replay window, but final research metrics should come from the frozen backend evaluation. When an endpoint or metric is unavailable, show an error/status instead of a fabricated response.

## 10. Frontend package and startup compatibility checklist

Before installing/upgrading anything:

1. Run `node --version` and `npm --version`; inspect `frontend/package.json` and lockfile.
2. Choose a compatible React/Fiber pair from official React Three Fiber guidance. As documented by React Three Fiber, v9 pairs with React 19 and v8 pairs with React 18: https://r3f.docs.pmnd.rs/getting-started/installation
3. Install dependencies with the existing package manager and commit the lockfile. Do not switch npm/pnpm/yarn mid-project without a reason.
4. Keep the API and frontend local, with environment-controlled API URL. For example, frontend `.env.local` may set `VITE_API_BASE_URL=http://127.0.0.1:8000`, but no secret belongs in a Vite `VITE_*` variable.
5. Provide exact Windows PowerShell startup commands in README/runbook. At minimum, start backend and frontend in separate terminals if a cross-platform supervisor is unreliable. Example shape (adapt to actual venv and app path):

```powershell
# Terminal 1 — backend (activate the project's venv first)
python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000

# Terminal 2 — frontend
cd frontend
npm run dev -- --host 127.0.0.1
```

Do not copy those paths blindly if the project uses a different existing module layout; the final README must show the exact command that was run successfully.

## 11. Official tooling references

- React Three Fiber installation and React-major compatibility: https://r3f.docs.pmnd.rs/getting-started/installation
- Antigravity Marketplace: https://www.antigravity.google/docs/marketplace
- Chrome DevTools for agents / Antigravity browser tooling: https://developer.chrome.com/docs/devtools/agents/get-started
- Maintained GSD continuation and project history: https://github.com/gsd-open/get-shit-done-redux and https://github.com/gsd-build/get-shit-done/blob/main/docs/ARCHITECTURE.md

## 12. Final instruction

**A genuinely running pipeline with honest evidence beats a larger fake system.** Freeze the scientific core before UI polish, build the React dashboard from real FastAPI responses/artifacts, and use the exact same saved results everywhere. Make the 3D layer impressive but non-essential: it can enhance understanding, never hide missing evidence or break the core workflow. The prototype is successful if it answers the stated research question credibly—even if SignalGate does not beat B2.
