# Phase 1: Safe Baseline and Repository Inventory — Research & Protocol

**Phase:** 01-safe-baseline-and-repository-inventory  
**Date:** 2026-10-18  
**Governing Specification:** `docs/ibm_architecture_integration_master_spec.md` § E

## Research Objective

Determine the exact verification mechanisms, hash algorithms, directory inspection commands, and license attribution protocols needed to produce the authoritative `docs/ibm_architecture_integration/00_inventory.md` without modifying any working files or disturbing the uncommitted working tree.

## Technical Findings

### 1. Git State & Working Tree Invariants
- The workspace at `C:\Users\arpit\Desktop\project` is an initialized Git repository on branch `master`.
- There are no prior commits (`git rev-parse HEAD` returns `fatal: Needed a single revision`), which means all project files are currently untracked working-tree files.
- **Safety Directive:** Blind `git add .` or `git checkout -- .` or `git clean -fd` is strictly prohibited. The working tree contains extensive pre-existing user work (FastAPI backend, React 3D frontend, trained models, test suites, documentation, and design assets) that must be preserved completely.

### 2. Hash Verification Protocols
The following core artifacts must be fingerprinted using SHA-256:
- Synthetic dataset: `data/synthetic_smoke_fixture.csv`
- Frozen policy: `policy/frozen_policy.json`
- Configuration: `config.yaml`
- Benchmark evaluation: `results/results.json`
- Partition splits: `results/split_report.json`
- Model artifacts: `models/artifacts/*.joblib` and `models/artifacts/*.meta.json`
- Replay telemetry: `results/replay_rows.jsonl` and `results/cases.jsonl`

### 3. Reference Architecture Inspection
- The reference code is located at `reference/architecture/IBM-main/`.
- It contains legacy models, policies, agents, and results from `https://github.com/anshumanarchit-crypto/IBM`.
- The README in `reference/architecture/IBM-main/README.md` contains an MIT License badge, but there is no separate root `LICENSE` file in the archive.
- **Attribution Strategy:** We will inspect the README badge and repository headers, document the permissive MIT license claim, preserve attribution notices, and adopt an architectural specification approach (clean-room compatible implementation) in the isolated namespace `integrations/ibm_architecture/`.

### 4. 3D Blender Assets Inventory
- Two 3D GLTF/GLB models exist in `frontend/public/models/`:
  - `model-pipeline.glb` (and `model_pipeline.glb` alias)
  - `sandbox-inference-instrument.glb` (and backup)
- Frontend unit tests (`pipeline_glb_integration.test.ts` and `sandbox_instrument_glb_integration.test.ts`) already verify fallback handling and asset integration.

### 5. Deliverable Contract
The deliverable `docs/ibm_architecture_integration/00_inventory.md` must categorize findings into five distinct audit columns:
1. Proven Current Facts (empirically validated locally).
2. Source-Repository Claims (from reference documentation).
3. Local Validations Actually Performed (tests and hashes executed).
4. Missing Inputs (e.g., raw IEEE-CIS dataset files).
5. Work Not Yet Verified (downstream integration targets).

---
*Research compiled: 2026-10-18*
