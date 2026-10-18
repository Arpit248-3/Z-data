# SIGNALGATE — IBM ARCHITECTURE INTEGRATION MASTER SPECIFICATION

## GSD Milestone: Real-Data ML, Governed Agents, Dynamic Fraud-Triage Services, and Full-Stack Integration

**Primary coding environment:** Google Antigravity IDE on Windows 11  
**Execution model:** Gemini 3.8 Flash High  
**Existing project root:** `C:\Users\arpit\Desktop\project`  
**Read-only reference architecture:** `C:\Users\arpit\Desktop\project\reference\architecture\IBM-main`  
**Reference repository:** `https://github.com/anshumanarchit-crypto/IBM`

Invoke and use the installed GSD workflow to manage this entire milestone. Work within the existing project and preserve the working application.

This is a substantial brownfield integration. It must not be treated as a one-shot code-generation exercise. Create a GSD roadmap with ordered, dependent phases; create implementation plans, execute them, run verification, maintain durable reports, and preserve resumable state.

The goal is to integrate the useful architecture from the reference ZIP with the existing React + TypeScript + Vite + Three.js/React Three Fiber frontend and FastAPI backend. The final application should be a coherent product with genuinely data-backed scoring and governance behavior where prerequisites permit—not a static dashboard filled with synthetic counters or cached reports.

---

# A. OPERATING MODE AND GSD ORCHESTRATION

1. Use GSD codebase mapping before designing the integration. The user may already have run `/gsd-map-codebase`; inspect the current `.planning/` state and reuse it rather than repeating completed work.
2. Create one GSD milestone named `SignalGate IBM Architecture Integration`.
3. Use fine-grained, sequential phases with explicit dependencies and verification gates.
4. Use automatic advancement and noninteractive decision handling where supported by the installed GSD version.
5. Do not ask the user for repeated approval of routine implementation choices already specified here.
6. Do not wait for the user after every phase merely to report progress. Continue to the next unblocked phase automatically when the GSD workflow allows it.
7. Pause only for genuine blockers requiring a human-only action, such as unavailable raw dataset files, missing provider credentials when a real provider is required, unresolved legal permission, a destructive decision, or insufficient hardware resources.
8. If a phase is blocked, finish independent work, record the blocker, and do not falsely mark dependent phases complete.
9. Keep verification enabled. Never disable tests, plan checking, or integrity checks to accelerate execution.
10. Maintain GSD planning state, phase plans, summaries, and verification reports. Produce integration reports under `docs/ibm_architecture_integration/`.
11. If the current GSD runtime cannot execute the entire milestone in one run, preserve its state and identify the exact GSD continuation command instead of repeating the entire specification.
12. Do not begin an unrelated milestone, redesign the entire frontend again, or change the project's existing phase history merely to make integration easier.
13. Before implementation, inspect the current GSD command syntax and project initialization state. Do not assume flags or commands unsupported by the installed version. If needed, use the interactive GSD workflow and this file as its requirements source.

## Required GSD and integration deliverables

Maintain the installed GSD planning structure, including project requirements, roadmap/state artifacts, phase plans, phase summaries, and verification reports.

Also maintain these deliverables (adapt paths only if the repository has established documentation conventions, preserving the equivalent content):

- `docs/ibm_architecture_integration/00_inventory.md`
- `docs/ibm_architecture_integration/01_boundaries.md`
- `docs/ibm_architecture_integration/02_data.md`
- `docs/ibm_architecture_integration/03_model.md`
- `docs/ibm_architecture_integration/04_scoring_policy.md`
- `docs/ibm_architecture_integration/05_agents_audit.md`
- `docs/ibm_architecture_integration/06_drift_replay.md`
- `docs/ibm_architecture_integration/07_api.md`
- `docs/ibm_architecture_integration/08_frontend.md`
- `docs/ibm_architecture_integration/09_evaluation_release.md`
- `docs/ibm_architecture_integration/FINAL_INTEGRATION_REPORT.md`

---

# B. PROJECT IDENTITY AND EXISTING SYSTEM

The project is **SignalGate — Shift-Aware Fraud Triage**.

The existing project already has a React/TypeScript/Vite frontend with dark and light themes, dashboards, charts, a Scoring Sandbox, a Model & Governance page, Case Explorer, Shift Storm Replay, Policy Comparison, Drift & Shift, Audit Trail, and 3D visualizations.

The backend uses FastAPI and deterministic Python decision logic. The project has undergone substantial implementation and testing. Do not assume it is a blank application or replace it with the reference repository's Streamlit dashboard.

Before changing code, inspect the actual filesystem. Paths in older reports may differ from the current tree.

The reference ZIP contains overlapping `models/`, `data/`, `policy/`, `results/`, `agents/`, `governance/`, `schemas/`, `monitoring/`, `scripts/`, and `tests/` directories. These overlap the current project's folders. Never copy these directories over the current project's versions wholesale.

---

# C. NON-NEGOTIABLE INVARIANTS

These invariants apply throughout every phase and every new API, model, or agent.

## C1. Evidence and operation modes

Support explicit source/evidence states:

- `SYNTHETIC_SMOKE_ONLY`
- `IEEE_CIS_OFFLINE_BENCHMARK`
- `LIVE_SOURCE_NOT_CONNECTED`

Where appropriate, distinguish runtime source mode from evidence classification. The real IEEE-CIS model may become selectable only after its dataset, feature manifest, trained model, calibrator, policy, and provenance are verified.

Never silently replace the current model with the new model, or silently fall back from real-data mode to synthetic data. A historical IEEE-CIS benchmark is not a live transaction feed. Do not display fixture-generated numbers as live operational telemetry.

If a new mode is unavailable, communicate why it is unavailable and keep the existing synthetic demo functional.

## C2. Ground-truth quarantine

The target `isFraud`, and any equivalent target/label column, are evaluation-only. They must never enter:

- The model feature matrix.
- Calibration or inference request data.
- Scoring feature forms.
- Routing decisions.
- `AgentCaseView`.
- LLM prompts.
- Drift-adaptation decisions.
- Online operational behavior.

Raw `TransactionID` and `TransactionDT` must also be excluded from the ML feature matrix, inference policy parameters, and agent inputs, except for separately justified operational metadata that does not alter model input or routing.

If ground-truth labels appear in an offline evaluation detail view, mark them as post-hoc benchmark labels and keep them outside the decision path. Enforce restrictions in backend validation and tests, not merely in the frontend.

## C3. Deterministic core

Numerical model inference, probability calibration, policy ranking, routing, quota accounting, statistical tests, metric computation, drift calculations, validation replay, and claim verification must run in deterministic, testable backend code.

LLMs do not calculate authoritative numerical values. Agents may explain, propose, summarize, or verify claims under fixed schemas. Agent failure, delay, or disabled status must never alter the deterministic case action.

## C4. Frozen evidence protection

Keep all existing synthetic project artifacts, model files, configuration, frozen policy, and historical evaluation/test-look records intact.

Do not overwrite root canonical result files with the reference repository's saved outputs. Do not retune thresholds or select model hyperparameters based on test labels. Do not rerun the existing project's prior G3/G5 final-test looks.

Treat the supplied reference's `results/results.json` as versioned reference evidence until actual artifact/model/data compatibility is proven. All newly created real-data artifacts must live in a separate versioned namespace.

## C5. Honest infrastructure claims

The reference project describes an AMD64 host simulation. `security/tee_policy.py` evaluates supplied attestation evidence; it does not itself implement IBM Secure Execution attestation.

Do not claim hardware-attested IBM Secure Execution, LinuxONE/s390x execution, payment gateway connection, real transaction blocking or settlement, live bank traffic, or production deployment certification unless independently verifiable implementations and actual runtime evidence exist.

## C6. No fabricated behavior

Never fabricate risk values, case IDs, transaction events, drift statistics, latency, model outputs, audit entries, model metadata, or agent claims.

If a feature is unavailable, report its explicit status. The UI must not animate invented transaction activity or show stale results as the results of a failed request.

---

# D. SOURCE ARCHITECTURE AND EVIDENCE INSPECTION

Inspect the actual local reference tree, including:

- `README.md`
- `docs/architecture.md`
- `docs/FINAL_PLAN_COMPLIANCE_MATRIX.md`
- `docs/ML_Evidence_Audit.md`
- `docs/FINAL_RELEASE_CHECKLIST.md`
- `docs/security_governance.md`
- `config.yaml`
- `data/splits.py`
- `data/shift_scenarios.py`
- `models/features.py`
- `models/ensemble.py`
- `models/calibration.py`
- `models/signals/`
- `models/baselines.py`
- `policy/p5_candidate.py`
- `agents/supervisor.py`
- `agents/copilot.py`
- `agents/claim_verifier.py`
- `agents/drift_sentinel.py`
- `schemas/agent_view.py`
- `schemas/contracts.py`
- `governance/audit_chain.py`
- `governance/claim_ledger.py`
- `governance/replay_gate.py`
- `governance/red_teamer.py`
- `monitoring/drift.py`
- `security/tee_policy.py`
- `eval/`
- `scripts/reproduce.py`
- `scripts/validate_dataset.py`
- `scripts/run_g1_eval.py`
- `scripts/run_g2_eval.py`
- `scripts/run_g5_eval.py`
- `results/pre_eval_freeze_record.json`
- `results/results.json`
- `results/feature_manifest.json`
- `results/split_manifest.json`
- `results/dataset_validation_report.json`
- `results/shift_scenarios_manifest.json`
- `results/drift_report.json`
- `results/agent_cache.json`
- `results/sample_audit_chain.jsonl`
- `tests/`

Inspect the current project's equivalent services, route implementations, schemas, tests, configuration, data files, model assets, and UI components. Compare actual implementations, not only documentation.

The reference freeze record identifies:

- A 391-feature preprocessing pipeline.
- A HistGradientBoosting base estimator.
- An `EraBaggedHeterogeneousEnsemble` with five chronological era members.
- A Platt/sigmoid calibrator fitted on the calibration partition.
- A P5 candidate ranking formula `p_calibrated + lambda * u_signal`.
- Frozen `disagreement_weight_lambda = 0.0`.
- Primary workload multiple 1.5.
- Registered workload sweep values 1.0x, 1.5x, 2.0x, and 3.0x.
- Chronological 60/10/10/20 train/calibration/validation/test partitions.
- Bootstrap evaluation with 1,000 resamples in its registered protocol.

Verify these details from actual files. Do not treat prose reports as a substitute for code/config/artifact inspection.

The P5 reference policy with lambda zero is effectively ranking by calibrated risk alone. Do not claim that its ranking score adds disagreement-based prioritization.

---

# E. PHASE 0 — SAFE BASELINE AND REPOSITORY INVENTORY

Perform an actual read-only inventory.

Record:
- Git root, branch, current HEAD, remotes, and working-tree status.
- Existing user changes and untracked files.
- Current React/FastAPI routes and test suites.
- Synthetic model, frozen policy, configuration, and evaluation artifact hashes.
- Status of both Blender assets and whether each is actually integrated.
- Existing run scripts and demo documentation.
- Local Python and Node versions and installed dependencies.
- Actual data files, sizes, paths, and fingerprints.
- Existing checkpoints and compatibility metadata.
- Reference archive contents and license status.

Do not reset, clean, discard, or overwrite the working tree. Do not use `git add .` blindly. Never commit pre-existing user changes as part of this integration.

Establish a safe integration branch or checkpoint while preserving all current files and user modifications. If the working tree has uncommitted changes, inspect and preserve them; do not stash or clean them automatically.

Keep the reference tree read-only.

## License

Verify the actual repository license from the live reference repository or another authoritative source before copying its source code. The ZIP README contains a license badge, but the archive itself may not contain a root `LICENSE` file.

If the license is verified as permissive and applicable, preserve attribution/license notices. If copying permission cannot be established, use the documented architecture as a specification and implement compatible behavior without copying unlicensed source verbatim. Continue unrelated work that is not blocked.

Create `docs/ibm_architecture_integration/00_inventory.md`.

The inventory must distinguish:
- Proven current facts.
- Source-repository claims.
- Local validations actually performed.
- Missing inputs.
- Work not yet verified.

---

# F. PHASE 1 — ISOLATED INTEGRATION PACKAGE AND MODE CONTRACTS

Design and implement safe integration boundaries before adding model or agent behavior.

Prefer an isolated namespace such as:

`integrations/ibm_architecture/`

Adapt to existing naming conventions after inspection. Do not overwrite existing top-level packages or canonical result files. Reuse code only where its contracts and provenance are compatible.

Create or extend typed, validated contracts for:
- Source mode and data readiness.
- Dataset and split identity.
- Model version and feature-manifest identity.
- Scoring result, reason code, and policy version.
- A sanitized `AgentCaseView`.
- Verified claims and provenance.
- Drift diagnostics.
- Adaptation proposals and human-approval state.
- Audit entries and verification status.
- Service health and component readiness.

Reuse existing schemas where compatible instead of creating duplicate types.

Define versioned namespaces for the existing synthetic model and the real-data candidate. Create a source/mode registry with explicit startup readiness checks. Selection of a real model must fail closed if its artifact bundle is missing, incompatible, or invalid.

Add tests for source-mode resolution, missing artifacts, unsupported configuration, and incompatible model manifests.

Create `docs/ibm_architecture_integration/01_boundaries.md`.

---

# G. PHASE 2 — REAL IEEE-CIS DATA INGESTION AND TEMPORAL PARTITIONS

Check the current project, not just the ZIP, for the data files required by the authoritative pipeline.

Inspect:
- `data/raw/train_transaction.csv`
- `data/raw/train_identity.csv`
- Other existing raw dataset files.
- Existing feature manifests and serialized preprocessing/model artifacts.

The reference ZIP does not itself supply the raw training dataset or a fitted model checkpoint. Do not infer availability from saved result JSON.

If valid data exists, verify its provenance, expected columns, byte sizes, target presence, ID uniqueness, timestamps, join expectations, and data fingerprint. Reuse valid local data rather than redownloading it.

If the required real dataset is missing, do not substitute the synthetic fixture, invent CSV rows, or relabel synthetic rows. Continue independent integration work, but leave real-model readiness blocked and give the exact required input path and acquisition prerequisite.

Implement a reproducible loader in the isolated integration package.

Requirements:
- The exact registered feature manifest governs the model matrix.
- Exclude `isFraud`, raw `TransactionID`, and raw `TransactionDT` from model inputs.
- Join identity data only as prescribed by the verified feature pipeline; verify merge cardinality.
- Fit imputers, encoders, and learned preprocessing on training data only.
- Handle missing values and unseen categories according to the training pipeline.
- Avoid dumping raw transaction rows into logs.
- Protect data files from accidental Git staging.
- Keep target labels separate from feature transformation and inference.
- Do not use labelled Kaggle submission/test files as labelled ground truth.

Implement chronological partitions according to actual reference split semantics. The intended ratios are 60% training, 10% calibration, 10% validation, and 20% test unless the authoritative split implementation defines additional rules.

Persist separate reports/manifests under a real-data namespace, for example:

`results/ieee_cis_v1/`

Include dataset-validation report, split counts and temporal boundaries, feature manifest and exact feature order, dataset and partition hashes, target-exclusion checks, and evidence classification.

Do not overwrite the existing synthetic split manifest.

Test chronology, determinism, leakage, unique IDs, join cardinality, and malformed/missing-data cases.

Create `docs/ibm_architecture_integration/02_data.md`.

---

# H. PHASE 3 — REPRODUCIBLE MODEL TRAINING, CALIBRATION AND ARTIFACTS

Execute only when the real-data loader and splits are verified.

Inspect the authoritative freeze record and actual code to determine whether the model should use the five-era-member heterogeneous ensemble or another explicitly registered implementation. Do not merge different architectures into an undocumented hybrid.

Implement or adapt the verified pipeline:
1. Training-only feature preprocessing.
2. Correct frozen base estimator and ensemble design.
3. Registered seed strategy.
4. Per-member probability predictions where supported.
5. Platt/sigmoid calibration fitted only on the calibration partition.
6. Validated disagreement signals, including `u` and `u2` as applicable.
7. Model and pipeline metadata serialization.
8. Feature-order and bundle compatibility validation.

Do not feed target labels, raw transaction identifiers, or raw timestamps into model features.

Validation data may be used only for permitted diagnostics and documented selection. Do not fit the calibrator on validation or test data.

Before training, inspect the actual Windows hardware, Python environment, available memory, disk space, and expected matrix size. Use memory-aware loading and reasonable worker counts without changing the registered mathematical procedure.

Do not silently downsample. If full training exceeds resources, stop the run cleanly, preserve logs, document the actual failure, and recommend a specific resource remedy. Do not report a partial fit as full-data training.

Write all new artifacts under:

`models/artifacts/ieee_cis_v1/`

Include the fitted feature pipeline, model bundle, calibrator, signals, manifest, training metadata, and hashes.

Do not overwrite the synthetic model or existing active model registry.

Test repeated inference, feature order, model/calibrator compatibility, finite outputs, probability range, and forbidden-feature exclusion.

Create `docs/ibm_architecture_integration/03_model.md`.

---

# I. PHASE 4 — DYNAMIC SCORING, BASELINES, FROZEN POLICY AND CAPACITY GOVERNANCE

Integrate the new real-data scorer without replacing the existing deterministic synthetic scorer.

Every model version must be bound to a compatible feature manifest, calibrator, signal artifact, and explicit policy.

Implement separate policy adapters for:
- The existing project's deterministic action router.
- Reference B2 top-budget baseline.
- Reference P5 candidate policy.

Inspect actual schemas and the frozen policy before mapping actions/reason codes.

P5 is a cohort-relative budget-ranking policy, not automatically a valid standalone one-row decision policy. Do not apply P5 to individual rows as if batch context were irrelevant.

Preserve the reference formula and lambda value for exact reference reproduction. Do not represent a lambda-zero P5 ranking as disagreement-weighted ranking.

Any new disagreement-aware candidate must receive a separate identity, frozen configuration, and validation process. Select it on permitted validation evidence, not test-label tuning.

Implement a deterministic scoring service that:
- Accepts validated inputs.
- Applies the exact fitted feature pipeline.
- Produces calibrated `p`, validated `u/u2`, model identity, and policy identity.
- Returns the deterministic action/reason.
- Fails closed on bad inputs, missing artifacts, or incompatible versions.
- Does not expose the ground-truth label to inference.

Implement cohort-level top-K selection only when the complete cohort and registered budget are present. For a single-row sandbox request, use an explicitly supported deterministic per-case policy or state that batch ranking requires a cohort.

Capacity states must clearly distinguish:
- `FRAUD_ALERT`.
- `MANUAL_REVIEW` admitted against quota.
- `ROUTINE`.
- `HELD`/`DEFERRED` due to governance capacity.

Keep requested escalations, admitted cases, and deferred cases correctly reconciled. Invalid required signals must fail closed according to the verified safe action. Never let capacity saturation silently move an ambiguous or high-risk case to `ROUTINE`.

Create `docs/ibm_architecture_integration/04_scoring_policy.md`.

Test threshold boundaries, missing/invalid signals, capacity saturation, batch ties, quota arithmetic, reason codes, and routing invariance when agents are disabled.

---

# J. PHASE 5 — GOVERNED AGENTS, CLAIM VERIFICATION AND AUDIT PROVENANCE

Integrate the reference agent concepts using strict backend boundaries.

Inspect the agent supervisor/dispatch rules, `AgentCaseView`, Case Copilot, Claim Verifier and Claim Ledger, Drift Sentinel, HMAC audit-chain implementation, current audit contracts, and persisted storage.

### J1. AgentCaseView

Agents may receive only a typed sanitized projection of approved fields, such as model/calibration IDs, `p`, validated `u/u2`, deterministic action/reason, relevant config/policy hash, and a permitted pseudonymous record reference.

Agents must never receive raw feature vectors, `isFraud`, target labels, prohibited identifiers/timestamps, environment variables, private local paths, or full sensitive transaction payloads.

Enforce the boundary with strict schemas and adversarial tests.

### J2. Provider modes

Support explicit modes:
- Deterministic offline-template mode.
- Optional configured real LLM provider, only if usable credentials/configuration and an appropriate provider endpoint exist.

A locally reachable Ollama or configured OpenAI-compatible endpoint may be supported via an injectable provider interface.

Do not make agent functionality a dependency of basic scoring. If no provider is configured, label output clearly as offline templates or deterministic advisory output; do not call it live LLM-generated.

Use environment variables for provider/API credentials. Never hardcode or log secrets. Add placeholder entries only to `.env.example`. Apply timeouts, size limits, and clear failure behavior.

### J3. Claim verification

LLM agents may propose typed claims, but verified dashboard claims must be generated or checked deterministically against source artifacts and registered templates populated with verified facts.

Reject unsupported claims. Verify seeded false-claim rejection and correct-claim acceptance. Never render arbitrary agent prose as established fact. Agent failure/disablement must not change a case action/reason.

### J4. Cryptographic audit chain

Adapt the reference HMAC-SHA256 chain only after reviewing the current implementation and key handling.

Use a strong local secret supplied via environment or a suitable secret mechanism; do not commit the key. If required key/verification configuration is absent, report audit-authentication readiness as unavailable rather than using a predictable hardcoded key.

Distinguish the reference sample audit chain from newly persisted runtime entries. Do not copy cached records and call them live events.

Record model/policy ID, source mode, action/reason, provenance hashes, timestamp and chain linkage as appropriate without raw features/labels or credentials.

Test tamper detection on disposable copies, chain verification, false-claim blocking, provider failures, and routing invariance.

Create `docs/ibm_architecture_integration/05_agents_audit.md`.

---

# K. PHASE 6 — DATA-DRIVEN DRIFT MONITORING AND HUMAN-APPROVED REPLAY GATE

Integrate the reference drift monitor, Drift Sentinel, and Replay Gate.

Drift monitoring must calculate PSI/KS on actual available feature windows or scored batches, with reference-window identity, comparison-window identity, sample counts, feature-level results, thresholds/severity, evidence/source status, timestamp, and provenance.

A saved frozen drift report must be labelled as historical/recorded. Do not present static diagnostics as current monitoring.

Use actual IEEE-CIS windows when validated. Synthetic stress perturbations remain labelled synthetic. Do not use ground-truth labels to determine drift or fraud actions.

Drift is not proof of fraud and must not automatically trigger fraud decisions.

The Drift Sentinel may produce advisory proposals for allowlisted configuration keys. It must not directly mutate or activate the current model/policy.

Require the Replay Gate to validate schema, base config hash, allowlisted keys, budget bounds, and deterministic replay on permitted development/validation data.

Successful replay must still leave the proposal in `AWAITING_HUMAN_APPROVAL`. Record actual approver, timestamp, prior/new config hashes, replay metrics, decision and audit provenance.

Never use held-out test labels for adaptation approval. No automatic threshold tuning or implicit activation is allowed.

Failed validation, timeout, malformed proposal or missing data must leave the active policy intact.

Create `docs/ibm_architecture_integration/06_drift_replay.md`.

Test no-drift, available real drift, synthetic stress, empty/missing batches, failed replay, hash mismatch, forbidden config keys, and approval/rejection paths.

---

# L. PHASE 7 — FASTAPI INTEGRATION

Integrate the new services into the current FastAPI application. Do not create a second service the existing React frontend never calls. Do not replace FastAPI with Streamlit.

Inspect actual route registrations and Pydantic contracts before modifying endpoints.

Extend existing endpoints when a compatible route exists. Add routes only for genuinely new capabilities.

Provide verified access to:
- Source-mode/data readiness.
- Real-data model and feature-manifest identity.
- Dataset-backed cases and bounded pagination.
- Actual loaded/scored replay rows.
- Policy comparison records.
- Calculated drift reports and advisory proposals.
- Replay Gate/approval status.
- Sanitized Copilot briefs.
- Persisted audit records and supported chain verification/export.
- Actual scoring-sandbox results.

Reuse compatible current routes such as `/api/overview`, `/api/status`, `/api/cases`, `/api/replay/rows`, `/api/policies/compare`, `/api/results`, `/api/audit`, and `/api/score-sandbox`, but use the actual registered paths and current response schemas.

Use typed Pydantic request/response schemas. Keep old response contracts backwards-compatible where practical and introduce versioned metadata rather than silently changing semantic meanings.

Ensure requests cannot inject labels/prohibited identifiers into inference, submit unbounded batches, trigger training through GET routes, trigger policy activation without explicit approval, read arbitrary local paths, expose raw feature vectors/secrets/model internals unnecessarily, reorder data, or conflate model versions.

Each score/analysis response must identify model, policy, evidence mode and relevant artifact identity.

IEEE-CIS mode may return ready only when its dependency bundle is verified. Do not silently fall back to the synthetic scorer.

Keep error handling structured and honest: unavailable, invalid input, incompatible artifact, provider unavailable, audit not authenticated, and actual success are distinct states.

Run backend integration tests and add tests for schemas/routes, source readiness, scoring payload rejection, pagination, agent failures, audit verification, and approval gates.

Create `docs/ibm_architecture_integration/07_api.md`.

---

# M. PHASE 8 — CONNECT THE EXISTING REACT DASHBOARDS

Use the current React + TypeScript + Vite frontend and established API client. Read the current UI, page components, themes, modal system, charts, 3D assets, responsive styling, and tests.

Do not port the Streamlit dashboard or rebuild the visual identity.

## Required application modes

Display an explicit status:
- `SYNTHETIC_SMOKE_ONLY`
- `IEEE_CIS_OFFLINE_BENCHMARK`
- `LIVE_SOURCE_NOT_CONNECTED`

Show real-data mode as available only when its verified model/policy bundle is ready. Keep live mode unavailable until a genuinely authorized source has been connected.

## Overview

Use genuine API values for dataset status, outcome distribution, review capacity, model readiness, thresholds, and provenance. Preserve spacious KPI layout and correct dialog behavior.

## Shift Storm Replay

Use actual loaded rows or explicitly identified offline replay records. Play/pause/step/reset/scrub controls must manipulate coherent current-row state. Do not fake a live stream.

## Case Explorer

Use real paginated case records, supported filters, correct selected-case details, actual scoring fields and reason codes. Preserve the centered, blurred, internally scrollable modal without splitting the table.

## Policy Comparison

Use actual canonical/reference or newly evaluated metrics from the appropriate version. Display matched workload, denominator, confidence intervals and inconclusive findings. Never merge metrics from different model/policy versions, datasets or source modes in one series.

## Drift & Shift

Use genuine calculated diagnostics when available. Label historical reports clearly and keep synthetic stress separate from real-data scenarios. State that drift is not a fraud verdict.

## Audit Trail

Show actual persisted records and real integrity status. Never label cached demonstration records as newly recorded or claim verification merely because a hash is displayed.

## Model & Governance

Show actual model architecture, feature count, calibrator, thresholds, artifact identity and policy version. Do not invent architecture names. If a GLB asset exists, inspect whether it is actually integrated; preserve working local models and use responsive, readable layouts.

## Scoring Sandbox

Call the actual scoring API using the verified source mode. Display returned `p`, `u/u2`, action, reason and available latency/provenance. Do not use client-side hardcoded scores or display stale success values after a failure.

The Blender inference instrument may visually react to actual API responses if its integration is already present and verified. Keep model assets local; do not require remote Spline services.

## Agent interfaces

Case Copilot must distinguish deterministic template mode from a configured real LLM provider. Show only verified claims. Agent failures never change routing.

Any proposed policy adaptation must be labelled advisory and awaiting approval until the backend confirms authorized activation.

## UX, performance and accessibility

Preserve existing typography, dark/light themes, readable KPI cards, scrolling dialogs, reduced-motion behavior, keyboard accessibility and responsive layout.

Use data-bound charts with denominators and provenance. Do not build fake sparklines or arbitrary historical curves.

Every significant interaction must change UI state or execute a valid API operation. An unavailable feature must be visibly unavailable, not presented as an active button.

Create `docs/ibm_architecture_integration/08_frontend.md`.

Test all eight routes in both themes. Use genuine browser screenshots when possible and disclose any automation failure.

---

# N. PHASE 9 — EVALUATION, REPRODUCIBILITY AND ACCEPTANCE GATES

Perform the required final evaluation only after the real-data pipeline, model artifacts, policy, pre-evaluation freeze, and API integrations have been verified.

The reference pre-evaluation record acknowledges a historical G1 test-set look. Any reproduced benchmark must be described as a reproduction, extension, or new frozen candidate evaluation as appropriate—not falsely presented as a pristine first-ever test.

## Evidence sources

Before running an evaluation:
- Verify exact dataset fingerprint.
- Verify train/calibration/validation/test split hashes and boundaries.
- Verify model checkpoint, feature manifest, calibration and policy identity.
- Check if the existing reference artifacts match exactly.
- Inspect reference acceptance reports and registered metrics.
- Write/verify an immutable pre-evaluation freeze record for any genuinely new candidate.

If model and policy exactly match, verify existing frozen evidence without unnecessary new test evaluation. If the integrated candidate differs, create a new versioned evaluation record and execute the documented pre-registered evaluation once. Do not repeatedly inspect test results while tuning.

Do not overwrite existing synthetic results or the reference ZIP's canonical metrics. Save new outputs separately under `results/ieee_cis_v1/`.

## Required evaluation

When required inputs and artifact provenance are verified:
- Evaluate B2 and P5 separately.
- Use identical records and registered workload budgets.
- Calculate recall, precision, touched rate, PR-AUC, calibration error, confident misses, deferrals and denominators.
- Compute the registered paired-bootstrap interval and confidence rule.
- Evaluate registered S0, S1, S2 and S3 scenario definitions.
- Keep real-data shift and synthetic perturbation evidence separate.
- Measure actual host inference latency with warm-up and documented sample counts.
- Report actual CPU/OS architecture.

Do not modify thresholds or weights based on final-test labels. Do not invent missing scenario points or performance improvements.

## Acceptance criteria

Use the exact registered criteria in the authoritative freeze record. Reference criteria include recall-gain targets, workload-reduction requirements, shift-robustness comparisons, confident-miss reduction, and p95 latency thresholds.

The reference README reports:
- S0 recall improvement below the +2.00 percentage-point target.
- Required workload reduction not established.
- Confident-miss reduction target not met.
- AC3 shift robustness and AC5 latency passing in the recorded reference benchmark.

Verify these findings against the actual artifacts. Never convert a documented unmet criterion to PASS.

If acceptance targets remain unmet, report them honestly; integration does not guarantee a winning result.

## Final integration tests

Run and record actual results for:
- Dataset validation and artifact validator.
- Existing backend suite and new integration tests.
- Agent guardrail tests.
- Claim-ledger tests.
- Audit-chain/tamper tests.
- Replay Gate tests.
- TypeScript compilation.
- Frontend tests.
- Production build.
- API readiness and scoring.
- All eight frontend routes.
- Demo start/stop.
- Local asset loading.
- Source-mode labels and no-fallback behavior.

Use actual outputs, exit codes and test counts.

Create `docs/ibm_architecture_integration/09_evaluation_release.md`.

---

# O. DATA AND ARTIFACT SAFETY

Never commit/package raw transaction CSVs, training checkpoints, secret keys, private environment files, caches, or large audit logs unless an explicitly necessary private artifact path is justified and protected.

Ensure `data/raw/` and generated large artifacts follow current ignore rules. Do not log whole transaction rows.

Store secrets outside source control. Provide placeholders only in `.env.example`.

Never overwrite:
- Current root `config.yaml` unless an explicitly compatible migration is necessary and separately verified.
- Current `policy/frozen_policy.json`.
- Current `results/results.json`.
- Existing G3/G5 test-look records.
- Existing split metadata/hashes.
- Existing models or calibrators.
- Existing Blender source/backup files.
- Existing historical audit records.

New real-data artifacts, configs, policies, reports, and evaluation outputs must have separate paths and version IDs.

Prefer an explicit active-model registry/selection config. Keep synthetic mode as a usable option, not as an implicit fallback for real-data requests.

---

# P. PROJECT SIZE AND RESOURCE MANAGEMENT

Do not install unrelated packages or replace dependency manifests wholesale. Inspect actual dependency versions and compatibility first. Preserve the existing frontend build and current application behavior.

The project may already contain IEEE-CIS CSVs under `data/raw/`. Use local files when valid. Do not redownload data simply because the reference ZIP is incomplete.

Before training, evaluate local RAM, CPU, available disk space, expected matrix sizes, package compatibility, and estimated runtime.

If model training or reproduction exceeds resources:
- Preserve current artifacts.
- Record the actual failure.
- Stop the offending operation safely.
- Recommend the minimum specific resource/environment change needed.
- Continue independent work/tests where possible.

Do not silently truncate, downsample or change the registered algorithm.

---

# Q. DELIVERY, RUNBOOK AND HONEST CAPABILITY CLAIMS

Maintain:
- `README.md`
- `docs/runbook.md`
- `docs/known_limitations.md`
- Final integration report.

Document:
- How to start the application on Windows.
- How to verify the backend.
- How to select synthetic or real IEEE-CIS mode.
- How to score a real-data row/batch.
- How to inspect a case and audit record.
- How to configure an optional LLM provider.
- How to inspect drift reports and create a proposal.
- How to validate and approve a Replay Gate proposal.
- How to stop only processes launched by SignalGate.

Do not terminate all Python/Node processes during shutdown.

Make no live payment, bank connection, throughput, or hardware-attestation claim unless the capability exists and independent evidence supports it.

The final demo should show the actual selected source mode, real model outputs when the IEEE-CIS bundle is ready, genuine API responses, genuine case/replay data, and truthful agent/audit status.

---

# R. GSD EXECUTION POLICY

Create the roadmap and execute the milestone in dependent phases using the GSD commands/workflows supported by the installed Antigravity integration.

Execute in this logical order:

- Phase 0: Inventory and source/evidence audit.
- Phase 1: Safe integration namespace, mode contracts and baseline protection.
- Phase 2: Real-data loader, leakage checks and temporal splits.
- Phase 3: Real-data model training and calibration.
- Phase 4: Dynamic scoring, policy adapters and capacity governance.
- Phase 5: Governed agents, claim ledger and audit chain.
- Phase 6: Data-driven drift, advisory proposals and human-approved replay.
- Phase 7: FastAPI integration.
- Phase 8: React data-bound integration.
- Phase 9: Benchmark validation, end-to-end verification and documentation.

Do not start a dependent phase before its prerequisite is verified. Independent tests or documentation may continue around a blocked data-training prerequisite.

For every phase:
1. Create a concrete plan.
2. Execute its tasks.
3. Run specified checks.
4. Review actual failures and repair in-scope defects.
5. Write a phase summary and update GSD state.
6. Advance automatically when the gate passes.

Do not stop after generating the roadmap. Implement the integration.

Do not ask repetitive preference questions. Make reasonable decisions based on this specification and current source. Ask the user only when a required human decision, external credential, authorization, data acquisition, legal permission, or material-risk acceptance cannot be derived from actual files.

Never conceal a failed check. Never downgrade blocker severity. Never mark a phase complete when its mandatory outputs have not been verified.

No GSD instruction overrides scientific, data-security, or artifact-preservation rules in this specification.

---

# S. FINAL RELEASE-READINESS REPORT

Create:
`docs/ibm_architecture_integration/FINAL_INTEGRATION_REPORT.md`

The report must include:
- Architecture component mapping from reference to existing project.
- All phases completed, blocked or partially verified.
- Actual real-data and model readiness.
- Dataset, split, model, calibrator, policy and configuration identities.
- Which capabilities are dynamic and genuinely connected.
- Which remain template/offline/advisory.
- Actual provider availability.
- API contract and frontend integration results.
- Audit-chain readiness and verification.
- Drift/Replay Gate state.
- Actual evaluation outcome and unmet acceptance criteria.
- All test commands, counts, failures and exit codes.
- Browser verification status and tooling limitations.
- Resource limitations.
- Files modified and preservation of existing artifacts.
- Remaining blockers.
- Exact Windows commands to run the completed project.

Choose exactly one status:

### `INTEGRATED_REAL_DATA_READY`
Use only if the real dataset/model/policy pipeline is ready and verified, real-data API calls work with matching provenance, tests and artifact checks pass, and no critical integrity/security defect remains.

### `INTEGRATED_WITH_DOCUMENTED_LIMITATIONS`
Use only if the core integrated application is verified but some explicitly documented optional providers, data modes, hardware integrations or noncritical evaluation targets remain unavailable or unmet. Do not imply live production use.

### `BLOCKED`
Use if the real data/model path cannot be verified, essential artifacts are incompatible or missing, a critical routing/leakage/security defect remains, provenance is uncertain, or the UI materially misrepresents runtime behavior.

Do not use a favorable status to imply benchmark goals were achieved if actual reports say otherwise.

---

# T. STOP CONDITION

Finish all feasible phases and their verification without repeatedly asking the user to paste another phase prompt.

If integration is fully verified, summarize exact completed capabilities and final status.

If something cannot be completed, finish all nondependent work, provide the exact missing prerequisites and commands, and preserve GSD state for continuation.

Do not push or publish to GitHub, deploy, modify payment rails, or claim production certification.

Do not perform an additional final-test evaluation merely to obtain improved metrics.

Once `docs/ibm_architecture_integration/FINAL_INTEGRATION_REPORT.md` exists and the final status is accurately recorded, stop and return the report summary and exact run instructions.
