# Phase 1: Safe Baseline and Repository Inventory

**Milestone:** SignalGate IBM Architecture Integration  
**Governing Specification:** `docs/ibm_architecture_integration_master_spec.md` § E  
**Inventory Timestamp:** 2026-10-18T15:35:00+05:30  
**Repository Root:** `C:\Users\arpit\Desktop\project`  
**Reference Architecture:** `reference/architecture/IBM-main/`  
**Audit Classification Standard:** Proven Current Facts | Source-Repository Claims | Local Validations Actually Performed | Missing Inputs | Work Not Yet Verified  

---

## Executive Summary

This inventory establishes the authoritative, verified baseline of the SignalGate repository prior to commencing integration of the reference IBM fraud-triage architecture (`reference/architecture/IBM-main`).

In accordance with Section E of the governing specification, this inventory was conducted strictly using non-destructive, read-only operations. Zero files in the working tree have been modified, staged, stashed, reset, or cleaned. The existing dual-stack application (FastAPI backend + React/TypeScript/Vite/Three.js frontend) has been confirmed fully operational with all existing test suites passing (109 Python tests, 21 Vitest frontend tests).

All core synthetic dataset fixtures, serialized models, calibration curves, frozen policy configurations, benchmark results, and replay logs have been cryptographically fingerprinted via SHA-256. The reference architecture has been inspected, license terms analyzed, and the raw dataset availability evaluated.

---

## 1. Proven Current Facts (Empirically Confirmed Local State)

### 1.1 Host Environment & Hardware Profile
- **Operating System:** Microsoft Windows 11 Home Single Language (Version 10.0.26100, Build 26100)
- **Host Architecture:** AMD64 (x86_64 Family 25 Model 80 Stepping 0, AuthenticAMD)
- **Physical Memory:** 8,024 MB (8.0 GB RAM) total physical memory; available ~1,850 MB
- **Disk Storage:** Drive `C:\` total 475.7 GB; Free Space: 44.1 GB (47,381,643,264 bytes)
- **Python Runtime:** Python 3.13.7 (tags/v3.13.7:bcee12e, Feb 12 2025, 14:48:38) [MSC v.1942 64 bit (AMD64)]
- **Node.js Runtime:** Node.js v20.20.0
- **Package Manager:** npm 10.8.2
- **Port Availability:**
  - Port `8000` (FastAPI backend service): Unbound and free.
  - Port `5173` (Vite frontend development server): Unbound and free.

### 1.2 Git Repository State & Working Tree Invariants
- **Git Root:** `C:\Users\arpit\Desktop\project`
- **Current Branch:** `master`
- **Commit History:** Zero commits present (`git rev-parse HEAD` returns `fatal: Needed a single revision`). The repository is initialized, but all pre-existing project work consists of untracked files in the working tree.
- **Working Tree Policy:** Strict non-destruction. Blind `git add .`, `git reset`, `git checkout -- .`, and `git clean` are strictly prohibited. All pre-existing user work (FastAPI backend, React 3D frontend, trained models, test suites, documentation, design assets) is preserved intact.
- **Working Tree Invariant Status:** Confirmed zero modified files, zero stashed changes, zero discarded assets.

### 1.3 Pre-Existing Codebase Structure & Route Map
The existing application is a fully functioning, shift-aware fraud triage platform:
- **Backend Service:** FastAPI application located in `backend/app/main.py` with 11 active API routers:
  1. `/api/v1/cases`: Case exploration, filtering, prioritization, and individual case detail retrieval.
  2. `/api/v1/inference`: Deterministic scoring inference, calibration application, and fallback execution.
  3. `/api/v1/policies`: Frozen policy retrieval, candidate threshold comparisons, and budget simulations.
  4. `/api/v1/audit`: Cryptographically chained audit ledger entries and query verification.
  5. `/api/v1/replay`: Shift storm scenario replay, partition playback, and temporal stress testing.
  6. `/api/v1/drift`: Population drift monitoring, feature distribution shifts, and divergence statistics.
  7. `/api/v1/governance`: Governance checkpoints, approval states, and model provenance verification.
  8. `/api/v1/models`: Model metadata inspection, architecture registry, and artifact status.
  9. `/api/v1/tee`: AMD64-simulated attestation policy checks and evidence payload validation.
  10. `/api/v1/agents`: Multi-agent copilot, claim verification, and supervisor triage summaries.
  11. `/api/v1/benchmarks`: Offline benchmark metrics and partition performance summaries.
- **Frontend Application:** React 18 / TypeScript / Vite application located in `frontend/`:
  - Visual Design: Tailored dark and light themes, modern typography (Inter/JetBrains Mono), glassmorphism components.
  - 3D Visualizations: React Three Fiber (`@react-three/fiber`) and Drei (`@react-three/drei`) interactive canvas pipelines.
  - Page Views: Scoring Sandbox, Model & Governance, Case Explorer, Shift Storm Replay, Policy Comparison, Drift & Shift, Audit Trail, System Architecture.
  - 3D Model Assets:
    - `frontend/public/models/model-pipeline.glb` (and alias `model_pipeline.glb`): 3D visual representation of the ML inference and calibration pipeline (465,796 bytes).
    - `frontend/public/models/sandbox-inference-instrument.glb`: Refined V2 3D interactive instrument for the Scoring Sandbox (500,056 bytes, identical to `design_assets/blender/sandbox-inference-instrument-v2.glb`).
    - `frontend/public/models/sandbox-inference-instrument.backup-20261018-120603.glb`: Timestamped pre-refinement backup asset (442,012 bytes).

### 1.4 Cryptographic Fingerprints of Canonical Synthetic Artifacts
All canonical synthetic dataset fixtures, serialized models, calibration curves, frozen policy files, evaluation outputs, and logs have been cryptographically fingerprinted using SHA-256 against actual local disk files:

| Artifact Path | SHA-256 Fingerprint (Hex) | File Size (Bytes) | Category / Purpose |
|---|---|---|---|
| `data/synthetic_smoke_fixture.csv` | `da00179ebf37970ec8907d11cfb366d170ddd5b2b41370e881bf92359b7d17de` | 6,057,352 | Canonical 10,000-row synthetic evaluation dataset |
| `policy/frozen_policy.json` | `8d3f02ca492ca94bab45f3ceac8d39432c2f29f40d54e7990b4aa78cbbff6240` | 12,634 | Frozen baseline triage thresholds and review budgets |
| `config.yaml` | `ba49e44edd6cf9b45939604b1c7de29e0fffd6f9ba8cb4a321cc40f077c0fb78` | 1,627 | Active project configuration and parameter specifications |
| `results/results.json` | `b9464630df83488c0999251460f170696465756405c39afa9fd25b694060f6fc` | 41,472 | Canonical benchmark results and baseline metrics |
| `results/split_report.json` | `3755e272e7acb3b2085e726f101757b5264ee1922330504eb6e4a669fbcb25d5` | 2,104 | Partition boundary indices and split validation metadata |
| `models/artifacts/hgb_base.joblib` | `b20aa6fa375303741338bca971098195f5ae72d5e1fee3882e0553172fa3b70f` | 131,888 | Serialized HistGradientBoosting base estimator |
| `models/artifacts/hgb_base.meta.json` | `20c464db84e00b8a0c763f4f7641596f55132a08baedb28bc06b77d7dd2cd85f` | 3,330 | Metadata and hyperparameter record for HGB base |
| `models/artifacts/logistic_base.joblib` | `14ae6440be988bb4464436f12ca727698d588e660d728dbc301ecb133fa2e4e3` | 4,572 | Serialized Logistic Regression benchmark model |
| `models/artifacts/logistic_base.meta.json` | `500c14b873a87846563d8de81217ccb3baa2907cbd18219f3a7ffeb5d0a21b3c` | 3,352 | Metadata for Logistic Regression benchmark |
| `models/artifacts/calibrator_sigmoid.joblib` | `00c519243765bfd7844ed877cec0dd3caa2e45310aa47e457647680c8b787fb4` | 132,538 | Serialized Platt / Sigmoid calibration model |
| `models/artifacts/calibrator_sigmoid.meta.json` | `6bac59ad9b738a7444efcfdfba177752bd0be14e6864d42f108b00c4b53b2df7` | 3,350 | Metadata for Sigmoid calibrator |
| `models/artifacts/calibrator_isotonic.joblib` | `8b365160004f893500b1a2381ac58d52a7d1bf243f523ad2532bf55173d54ee2` | 132,870 | Serialized Isotonic regression calibrator |
| `models/artifacts/calibrator_isotonic.meta.json` | `ad21034537f415120b57439971beba52de90e1575f67c7c1dec36afd44af950f` | 3,364 | Metadata for Isotonic calibrator |
| `models/artifacts/ensemble_members.joblib` | `6c3a00b094e1242c1436a6adc5c4509f798065454e2554c6189abb805a5964c7` | 385,066 | Serialized multi-member ensemble model weights |
| `models/artifacts/ensemble_members.meta.json` | `d582c2795c0750ca7a55bd66caa524d0df0d0247b2701860d8bbe45e1d611097` | 1,699 | Metadata for ensemble members |
| `models/artifacts/residualizer_u2.joblib` | `10cadc14aa4f8781020079c9f23c030beb392a294066b56de18d4c972ee784a4` | 16,347 | Serialized uncertainty residualizer model |
| `models/artifacts/residualizer_u2.meta.json` | `dec47f1fbe8f32a4d5b918d228e1dd7b330d366416470dfb159cfc6013510f42` | 1,069 | Metadata for uncertainty residualizer |
| `results/replay_rows.jsonl` | `30eb673bdd89587ad1bb388a9526be8a51686ab08b4e94451b4b2245090f2c3d` | 2,788,003 | Replay ledger records for temporal simulation |
| `results/cases.jsonl` | `836271c3aef5f2846bd9b6d9f05228393ed8e85b1713a0b605598b684f188b2b` | 1,718,137 | Synthetic fraud triage case database |
| `logs/audit.jsonl` | `79689ebc60c3758ccbd7423fcbfc020af65f20f5a938860986b9603bb7bd5397` | 109,925 | Cryptographic audit trail log (append-only runtime ledger) |
| `logs/test_looks.log` | `a9a7d0141dd664d6dd8848c37e06813d52cc94d105c3b7a4c1cf0bed348f9588` | 1,142 | Historical G3/G5 final evaluation gate log |
| `frontend/public/models/model-pipeline.glb` | `a8b9fe62873380677f46386de6d2c5b2cbbd301cd94a1b737b329c2122e929c9` | 465,796 | 3D visual pipeline production GLB model |
| `frontend/public/models/model_pipeline.glb` | `ceacbb4434a378eb79f91e891cd039017dd439cb745179e86da9b190181b53eb` | 465,796 | Alias production GLB model |
| `frontend/public/models/sandbox-inference-instrument.glb` | `23f09bd567bf9d88ae93abfe84da54e95de35d4fa48b1bab52173e3d89f51713` | 500,056 | Refined V2 3D sandbox inference instrument GLB model |
| `frontend/public/models/sandbox-inference-instrument.backup-20261018-120603.glb` | `932a35f3a20e68a5ce793ca8c1beb5df2e442c9baf53e70124fd2737cbe5dd78` | 442,012 | Timestamped pre-refinement backup GLB model |

### 1.5 Narrative Budget Reconciliation (Denominator Verification & Ratio Clarification)
An audit of the canonical evaluation evidence establishes the exact mathematical relationship between the review capacity parameter and the evaluation partition:
- **Canonical Split Denominator (`results/split_report.json`):** The 10,000-row synthetic fixture is partitioned chronologically into:
  - Train: 6,000 rows ($60.0\%$)
  - Calibration: 1,000 rows ($10.0\%$)
  - Validation: 1,000 rows ($10.0\%$)
  - Test: **2,000 rows** ($20.0\%$)
- **Target Budget Parameter (`policy/frozen_policy.json` & `results/results.json`):**
  - Primary budget multiplier: $1.5\times$ training fraud prevalence ($4.35\%$).
  - Target parameter: $1.5 \times 0.0435 = 0.06525$ ($6.525\%$).
- **Realized Operational Capacity Quota on Test Split:**
  - Integer capacity quota: $\text{round}(2,000 \times 0.06525) = 130$ cases ($B = 130$).
  - Exact realized test partition ratio:
    $$\frac{130}{2,000} = 0.0650 = \mathbf{6.50\%}$$
- **Reconciliation:** Previous narrative citations that wrote "$130$ reviews ($6.525\%$)" conflated the continuous target budget parameter ($6.525\%$) with the realized test partition evaluation proportion ($6.50\%$). The canonical evidence confirms that exactly 130 cases were evaluated out of 2,000 test cases, representing an exact **6.50%** touched rate. No canonical result files or frozen policies were modified.

---

## 2. Source-Repository Claims (Claims Asserted in Reference Documentation)

The reference architecture archive at `reference/architecture/IBM-main/` contains documentation and code originating from `https://github.com/anshumanarchit-crypto/IBM`. An inspection of this archive identifies the following specific assertions:

### 2.1 License and Attribution Claims
- **License Badge:** In `reference/architecture/IBM-main/README.md`, an Apache 2.0 license badge is prominently displayed:
  `[![License: Apache 2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)`
- **Archive Contents:** No standalone `LICENSE` or `COPYING` text file exists at the root of `reference/architecture/IBM-main/`.
- **Packaging Declarations:** `pyproject.toml` references an open license.
- **Attribution Policy Mandate:** In compliance with Section E.1 of the master specification:
  1. All integration code must be authored clean-room in the isolated namespace `integrations/ibm_architecture/`.
  2. Clear attribution notices acknowledging `https://github.com/anshumanarchit-crypto/IBM` will be maintained in integration documentation and headers.
  3. No bulk overwrites or indiscriminate file copying from `reference/architecture/IBM-main/` into the existing root tree will occur.

### 2.2 Machine Learning Architecture Claims
- **Feature Engineering Pipeline:** Claims a 391-feature deterministic preprocessing pipeline tailored to the IEEE-CIS Fraud Detection dataset (`train_transaction.csv` + `train_identity.csv`).
- **Base Estimator:** LightGBM / HistGradientBoostingClassifier trained on chronological train splits.
- **Ensemble Architecture:** `EraBaggedHeterogeneousEnsemble` containing 5 chronological era members designed to absorb temporal regime shifts.
- **Calibration Protocol:** Platt / Sigmoid calibrator fitted strictly on the calibration partition (`cal`), preventing data leakage into test sets.
- **Policy Formula:** Candidate P5 policy ranking formula: `Score = p_calibrated + lambda * u_signal`.
- **Lambda Parameter:** Frozen parameter `disagreement_weight_lambda = 0.0`. Under this frozen parameter, the candidate policy ranks transactions purely by calibrated probability of fraud ($p_{\text{calibrated}}$) without disagreement-based weight.
- **Workload Scenarios:** Registered review capacity sweeps at 1.0x, 1.5x (primary benchmark), 2.0x, and 3.0x.
- **Dataset Partitioning:** Chronological splits: 60% Train, 10% Calibration, 10% Validation, 20% Final Test.
- **Bootstrap Verification:** 1,000 resample bootstrap evaluations on frozen test partitions.

### 2.3 Multi-Agent Governance Claims
- Claims an autonomous multi-agent triage system consisting of:
  - `SupervisorAgent`: Case prioritization and workload assignment.
  - `CopilotAgent`: Case feature explanation and investigation narrative generator.
  - `ClaimVerifierAgent`: Deterministic validation of agent factual assertions against case attributes.
  - `DriftSentinel`: Real-time monitoring of feature drift and distribution divergence.
- Claims an append-only cryptographic audit chain (`governance/audit_chain.py`) with SHA-256 state hashing.

### 2.4 Infrastructure & Security Claims
- Claims AMD64 host simulation of IBM Secure Execution / Confidential Computing.
- The reference `security/tee_policy.py` validates supplied attestation evidence tokens; it does *not* execute on native IBM s390x / LinuxONE hardware.

---

## 3. Local Validations Actually Performed

The following empirical verifications were executed and validated locally:

### 3.1 Backend Test Suite Execution
- **Command:** `python -m pytest -o "pythonpath=." tests/`
- **Result:** **109 passed** in 1.48s (100% pass rate).
- **Scope Verified:**
  - `tests/test_audit_chain.py` (9 tests): Cryptographic chaining, tamper detection, and ledger invariants.
  - `tests/test_baselines.py` (8 tests): Baseline model inference and benchmark parity.
  - `tests/test_calibration.py` (9 tests): Sigmoid and Isotonic calibrator fitting, monotonically increasing output bounds $[0, 1]$.
  - `tests/test_drift.py` (10 tests): PSI, KS tests, Wasserstein distance, and distribution shift alerts.
  - `tests/test_ensemble.py` (8 tests): Multi-member ensemble weighting and variance calculations.
  - `tests/test_features.py` (11 tests): Preprocessing, missing value imputation, and feature alignment.
  - `tests/test_integration.py` (13 tests): End-to-end API route execution, case scoring, and policy comparison.
  - `tests/test_p5_policy.py` (12 tests): P5 ranking candidate, threshold cutoff, and review budget allocation.
  - `tests/test_replay.py` (9 tests): Shift storm simulation playback and timeline integrity.
  - `tests/test_signals.py` (10 tests): Signal generators and uncertainty residualizers.
  - `tests/test_tee.py` (10 tests): AMD64 simulated TEE attestation verification and policy enforcement.

### 3.2 Frontend Test Suite Execution
- **Command:** `npm --prefix frontend test -- --run`
- **Result:** **21 passed** in 8.35s across 7 test test files (100% pass rate).
- **Scope Verified:**
  - `frontend/src/tests/3d_fallback.test.ts` (3 tests): Graceful WebGL / Canvas fallback when 3D rendering context is unavailable.
  - `frontend/src/tests/case_explorer.test.tsx` (3 tests): Case filtering, prioritization tables, and selection state.
  - `frontend/src/tests/pipeline_glb_integration.test.ts` (3 tests): Loading and mesh verification for `model-pipeline.glb`.
  - `frontend/src/tests/sandbox.test.tsx` (3 tests): Scoring Sandbox sliders, real-time inference dispatch, and response formatting.
  - `frontend/src/tests/sandbox_instrument_glb_integration.test.ts` (3 tests): Loading and interaction hooks for `sandbox-inference-instrument.glb`.
  - `frontend/src/tests/theme.test.tsx` (3 tests): Dark/light theme state persistence and CSS class application.
  - `frontend/src/tests/ui_ux_audit_gates.test.ts` (3 tests): Visual hierarchy, accessibility attributes, and responsive breakpoints.

### 3.3 Cryptographic Integrity Check
- Cryptographic hash verification confirmed that local files in `data/`, `policy/`, and `results/` match the registered constants in `backend/app/config.py`:
  - `data/synthetic_smoke_fixture.csv`: Hash matches pre-registered constant `da00179ebf37970ec8907d11cfb366d170ddd5b2b41370e881bf92359b7d17de`.
  - `policy/frozen_policy.json`: Hash matches pre-registered constant `8d3f02ca492ca94bab45f3ceac8d39432c2f29f40d54e7990b4aa78cbbff6240`.
  - `results/split_report.json`: Hash matches pre-registered constant `3755e272e7acb3b2085e726f101757b5264ee1922330504eb6e4a669fbcb25d5`.

### 3.4 3D Asset Reconciliation (V2 Production Promotion Audit)
A direct byte-for-byte and cryptographic comparison of the 3D assets was conducted:
- **Sandbox Inference Instrument:**
  - `frontend/public/models/sandbox-inference-instrument.glb` has size `500,056` bytes and SHA-256 `23f09bd567bf9d88ae93abfe84da54e95de35d4fa48b1bab52173e3d89f51713`.
  - `design_assets/blender/sandbox-inference-instrument-v2.glb` has identical size (`500,056` bytes) and identical SHA-256 (`23f09bd567bf9d88ae93abfe84da54e95de35d4fa48b1bab52173e3d89f51713`).
  - **Audit Confirmation:** The file currently serving in the production frontend is the refined V2 asset engineered during Phase 10 (with 48 named risk segments, open annular chassis, and disagreement calipers). The legacy V1 placeholder values (`129,564` bytes, `eb66866be...`) recorded in early design drafts were reconciled.
  - A pre-refinement backup file is preserved at `frontend/public/models/sandbox-inference-instrument.backup-20261018-120603.glb` (`442,012` bytes, SHA-256 `932a35f3a...`).
- **Model Pipeline GLB:**
  - `frontend/public/models/model-pipeline.glb` (and alias `model_pipeline.glb`) is the full production Blender asset (`465,796` bytes).
  - All 3D assets are preserved without overwriting or replacement.

---

## 4. Missing Inputs (External Prerequisites and Uncommitted Dependencies)

The following inputs are currently missing or unavailable in the local environment:

### 4.1 Raw IEEE-CIS Fraud Detection Dataset
- **Directory Status:** `data/raw/` does not exist in the project root.
- **Missing Files:**
  - `train_transaction.csv` (~683 MB)
  - `train_identity.csv` (~68 MB)
  - `test_transaction.csv` (~583 MB)
  - `test_identity.csv` (~25 MB)
- **Impact & Operational Constraint:** In strict compliance with Section C1 and Section G of `docs/ibm_architecture_integration_master_spec.md`:
  - The application will **NOT** fabricate fake transactions or masquerade synthetic rows as IEEE-CIS data.
  - The runtime source mode will explicitly advertise `SYNTHETIC_SMOKE_ONLY` as available and functional.
  - The real-data mode `IEEE_CIS_OFFLINE_BENCHMARK` will fail closed with explicit diagnostic feedback ("Raw IEEE-CIS files not found in data/raw/").
  - The system will provide clear download instructions and a data validation script (`scripts/validate_dataset.py`) for when raw data is supplied by an operator.

### 4.2 Standalone Reference License File
- **Missing File:** `reference/architecture/IBM-main/LICENSE`
- **Mitigation:** The Apache 2.0 license declaration in `reference/architecture/IBM-main/README.md` is treated as a permissive license declaration. Clean-room integration in `integrations/ibm_architecture/` will maintain explicit header attribution while avoiding direct binary or verbatim unverified copying.

### 4.3 Hardware Security Module / Live s390x Platform
- **Missing Hardware:** No physical IBM s390x / LinuxONE hardware or native Secure Execution environment is available on this AMD64 Windows host.
- **Mitigation:** All TEE features will be clearly labeled as **AMD64 Simulated Attestation** in compliance with Section C5.

### 4.4 Live Banking / Payment Gateway Credentials
- **Missing Endpoints:** No live transaction settlement network or core banking connection exists.
- **Mitigation:** Live mode will remain explicitly set to `LIVE_SOURCE_NOT_CONNECTED`.

---

## 5. Work Not Yet Verified (Integration Roadmap Phases 2–10)

The following subsequent integration phases are planned in `.planning/ROADMAP.md` and will be executed sequentially:

- **Phase 2: Isolated Integration Package and Mode Contracts** (`INVN-03`, `INVN-04`)
  - Target Deliverable: `docs/ibm_architecture_integration/01_boundaries.md`
  - Implementation of `integrations/ibm_architecture/` namespace, strict mode enums (`SYNTHETIC_SMOKE_ONLY`, `IEEE_CIS_OFFLINE_BENCHMARK`, `LIVE_SOURCE_NOT_CONNECTED`), and ground-truth quarantine barriers.
- **Phase 3: Dataset Ingestion, Temporal Partitions, and Provenance** (`DATA-01`, `DATA-02`)
  - Target Deliverable: `docs/ibm_architecture_integration/02_data.md`
  - IEEE-CIS ingestion parser, 60/10/10/20 chronological partition validation, and manifest generation.
- **Phase 4: ML Pipeline, Calibrator, and Ensemble Engine** (`MODL-01`, `MODL-02`)
  - Target Deliverable: `docs/ibm_architecture_integration/03_model.md`
  - 391-feature preprocessor, HistGradientBoosting base, EraBaggedHeterogeneousEnsemble, and Platt calibrator.
- **Phase 5: Dynamic Scoring Policy and Workload Simulation** (`PLCY-01`, `PLCY-02`)
  - Target Deliverable: `docs/ibm_architecture_integration/04_scoring_policy.md`
  - Candidate P5 formula evaluation (`lambda = 0.0`), threshold optimization across 1.0x–3.0x workload sweeps.
- **Phase 6: Multi-Agent Governance and Immutable Audit Ledger** (`AGNT-01`, `AGNT-02`, `AGNT-03`)
  - Target Deliverable: `docs/ibm_architecture_integration/05_agents_audit.md`
  - Deterministic Supervisor, Copilot, Claim Verifier, and append-only SHA-256 audit ledger.
- **Phase 7: Drift Sentinel, Scenario Replay, and Stress Gates** (`DRFT-01`, `DRFT-02`)
  - Target Deliverable: `docs/ibm_architecture_integration/06_drift_replay.md`
  - Real-data drift metrics (PSI, Wasserstein) and Shift Storm scenario replay engine.
- **Phase 8: Unified FastAPI Integration and Mode Switching** (`API-01`, `API-02`)
  - Target Deliverable: `docs/ibm_architecture_integration/07_api.md`
  - Dynamic API mode switching, status endpoints, and comprehensive integration tests.
- **Phase 9: React 3D Frontend Integration and Operational Views** (`UI-01`, `UI-02`)
  - Target Deliverable: `docs/ibm_architecture_integration/08_frontend.md`
  - UI mode selector banner, real-data dashboard metrics, 3D asset integration, and dark/light polish.
- **Phase 10: Validation, Benchmark Evaluation, and Release Report** (`EVAL-01`, `EVAL-02`)
  - Target Deliverables: `docs/ibm_architecture_integration/09_evaluation_release.md` & `docs/ibm_architecture_integration/FINAL_INTEGRATION_REPORT.md`
  - Full end-to-end regression validation, bootstrap benchmark verification, and master integration report.

---

## Conclusion & Verification Sign-Off

The baseline inventory has been successfully completed. The repository is in an intact, highly stable state:
- All 109 Python tests and 21 Vitest frontend tests are passing.
- Working tree files remain untouched.
- Synthetic artifact hashes have been captured and verified.
- The reference archive and missing raw dataset conditions have been fully documented with fail-closed safeguards.

Phase 1 requirements `INVN-01` and `INVN-02` are fully satisfied. The codebase is ready to proceed to Phase 2.
