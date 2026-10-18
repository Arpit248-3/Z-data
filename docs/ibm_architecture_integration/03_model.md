# SignalGate IBM Architecture Integration — Phase 4: Model Integration Interfaces & Safe Bundle Adapters

**Governing Specification:** `docs/ibm_architecture_integration_master_spec.md` § C, § H  
**Active Execution Mode:** `SYNTHETIC_SMOKE_ONLY`  
**Real-Data Training Status:** `DEFERRED` (Hardware Gated: >= 16 GB RAM required)  
**Benchmark Comparable:** `false`  
**Active Model Architecture:** `synthetic_3member_hgb_u2`  
**Reference Model Architecture:** `PROPOSED_5MEMBER_ERA_OMITTED_DEFERRED`  
**Last Updated:** 2026-10-18  

---

## 1. Executive Summary & Strategic Scope

In compliance with project directives and host resource safety rules, full-scale IEEE-CIS model training (590,540 transactions × 391 features) and unconstrained ensemble fitting are temporarily **DEFERRED** due to local development workstation physical memory limits (7.75 GB total physical RAM) and project submission timelines.

Phase 4 implements and validates the model integration interfaces within `integrations/ibm_architecture/models/` in **`SYNTHETIC_SMOKE_ONLY`** mode, adapting and reusing existing, verified synthetic model artifacts and frozen policy configurations without expensive retraining.

### 1.1 Operating Modes & Readiness Status

| Operating Mode | Operational State | Execution Contract |
|---|:---:|---|
| **`SYNTHETIC_SMOKE_ONLY`** | **ACTIVE** | Functional demonstration and integration using canonical 67-feature fixture, verified 3-member ensemble, $u_2$ rank-residualizer, and Platt calibrator. |
| **`IEEE_CIS_OFFLINE_BENCHMARK`** | **DEFERRED** | Hardware preflight gate unmet on 7.75 GB host (requires $\ge 16$ GB total RAM). Armed standalone script in `scripts/train_full_benchmark.py`. Fails closed if invoked. |
| **`LIVE_SOURCE_NOT_CONNECTED`** | **DISCONNECTED** | Offline decision-support platform; live payment networks disconnected. |

---

## 2. Reused Canonical Synthetic Artifacts

Phase 4 safely binds to existing verified synthetic artifacts with zero modification or retraining:

| Component | Disk Path | SHA-256 Digest | Role in Integration |
|---|---|---|---|
| **Baseline B2** | `models/artifacts/hgb_base.joblib` | `1016892e6d63...` | HistGradientBoosting base estimator (seed 11) |
| **Sigmoid Calibrator** | `models/artifacts/calibrator_sigmoid.joblib` | `33b432a5146c...` | Platt Sigmoid probability calibrator |
| **Ensemble Members** | `models/artifacts/ensemble_members.joblib` | `6c3a00b094e1...` | 3-member HistGradientBoosting ensemble (seeds 11, 22, 33) |
| **Residualizer $u_2$** | `models/artifacts/residualizer_u2.joblib` | `10cadc14aa4f...` | Polynomial rank-residualizer for epistemic disagreement |
| **Frozen Policy** | `policy/frozen_policy.json` | `8d3f02ca492c...` | Frozen threshold policy ($B=0.06525$, $t_{\text{alert}}$, $t_{\text{review}}$, $u_{\text{threshold}}$) |
| **Synthetic Fixture** | `data/synthetic_smoke_fixture.csv` | `da00179ebf37...` | 10,000-row deterministic smoke dataset (67 numeric features) |

---

## 3. Architecture Distinction: Synthetic vs. Reference Architecture

To maintain complete scientific and operational integrity, the active synthetic architecture and the proposed reference architecture remain strictly distinguishable:

| Dimension | Active Synthetic Architecture | Reference Architecture (Deferred) |
|---|---|---|
| **Execution Mode** | `SYNTHETIC_SMOKE_ONLY` | `IEEE_CIS_OFFLINE_BENCHMARK` |
| **Ensemble Composition** | 3-member HistGradientBoosting (varying regularization & leaf nodes) | 5-member heterogeneous era-omitted (3x HGB, 1x ExtraTrees, 1x LogisticRegression) |
| **Disagreement Formulation** | Raw std dev $u$ + Rank-residual $u_2 = r_u - \hat{r}_u(r_p)$ | Raw std dev $u$ + Median absolute deviation $u_2 = \frac{1}{M}\sum \|p_m - \tilde{p}\|$ |
| **Feature Manifest** | 67 canonical numeric features (`data/schema.py`) | 391 canonical features (14 categorical, 377 numerical) |
| **Training Dataset** | Deterministic synthetic smoke fixture (10,000 rows) | IEEE-CIS Fraud Detection (590,540 rows) |
| **Benchmark Comparable** | `false` | `true` (when fully trained on $\ge 16$ GB host) |
| **Training Status** | **VERIFIED (REUSED)** | **DEFERRED (Hardware Gated)** |

---

## 4. Software Deliverables Implemented

All deliverables reside inside `integrations/ibm_architecture/models/`:

1. **`SyntheticFeaturePipeline` (`synthetic_adapter.py`):**
   - Enforces ground-truth quarantine: detects and immediately raises `LeakageViolationError` if `isFraud`, `target`, `true_label`, `TransactionID`, or `TransactionDT` are passed.
   - Sanitizes infinite values and downcasts floats to `float32`.
   - Aligns feature matrices to canonical 67-feature numeric schema.

2. **`SyntheticModelAdapter` (`synthetic_adapter.py`):**
   - Safely loads canonical artifacts without modifying files.
   - Computes baseline $p_{\text{b2}}$, calibrated probability $p_{\text{cal}}$, consensus probability $\bar{p}$, raw disagreement $u$, and rank-residual $u_2$.
   - Stamps output dictionary with explicit execution mode metadata:
     `execution_mode: "SYNTHETIC_SMOKE_ONLY"`, `benchmark_comparable: False`, `real_data_training_status: "DEFERRED"`.

3. **`ModelBundle` & `ModelBundleManifest` (`bundle.py`):**
   - Manifest schema explicitly tracking `execution_mode`, `benchmark_comparable`, `real_data_training_status`, `architecture_name`, `reference_architecture_status`, and component SHA-256 checksums.
   - Backward-compatible deserialization of both synthetic and local dev bundles.

4. **`load_synthetic_bundle()` & `get_model_bundle()` (`bundle.py`):**
   - Safe bundle loader providing unified interface for downstream scoring and policy governance.
   - Mode-aware factory that fails closed with `ModeUnavailableError` when `IEEE_CIS_OFFLINE_BENCHMARK` or `LIVE_SOURCE_NOT_CONNECTED` are requested.

---

## 5. Verification Summary

- **Unit Tests (`tests/test_ibm_models.py`):** **23 / 23 PASS (100%)**
- **Boundary Tests (`tests/test_ibm_boundaries.py`):** **15 / 15 PASS (100%)**
- **Data Tests (`tests/test_ibm_data.py`):** **12 / 12 PASS (100%)**
- **Regression Suite:** All prior tests passing with zero regressions.
- **Quarantine Barriers:** Verified rejecting `isFraud`, `TransactionID`, `TransactionDT` across all model inputs.
