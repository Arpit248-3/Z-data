# Phase 7: Drift Monitoring and Controlled Scenario Replay (Synthetic Mode)

## 1. Overview and Invariants

Phase 7 integrates the drift monitoring, advisory configuration proposal, and human-in-the-loop validation replay gates under the SignalGate IBM Architecture Integration specification.

### Core Architectural Invariants:
1. **Target and Key Quarantine**: Ground-truth target `isFraud` and keys `TransactionID` and `TransactionDT` are strictly barred from feature drift calculations and proposal evaluations. Any attempt to include them immediately raises `GroundTruthQuarantineError`.
2. **Indicator Discipline**: Covariate shift indicators (Population Stability Index and Kolmogorov-Smirnov statistics) quantify distributional movement in feature windows; they do **not** assert fraud or trigger automatic policy changes.
3. **Advisory Proposals Only**: Drift Sentinel generates typed `Proposal` records constrained to allowlisted configuration keys (`budget.primary_multiple`, `budget.sweep_multiples`, `thresholds`, `policy.p5.disagreement_weight_lambda`, `policy.p5.budget_multiple`). It cannot directly mutate runtime policy.
4. **Mandatory Human-in-the-Loop Replay Gate**: Replay Gate validates proposals against schema, frozen base configuration hashes, allowlists, and capacity boundaries. Passing validation leaves the proposal in `AWAITING_HUMAN_APPROVAL`. Operational activation requires explicit human sign-off (`APPROVED_ACTIVE`).
5. **Fail-Closed Provider Safety**: External provider timeouts, HTTP errors, or malformed outputs fail closed cleanly without crashing or mutating active decision policy.
6. **Explicit Operating Mode Telemetry**: In `SYNTHETIC_SMOKE_ONLY` mode, all replayed shift scenarios (S1–S4) and metrics are explicitly labeled synthetic, and real-data drift benchmarks are marked **DEFERRED**.

---

## 2. Implemented Components

### 2.1 Distribution Drift Calculator (`integrations/ibm_architecture/monitoring/drift.py`)
- **PSI Engine**: Derives reference quantile bins from the baseline sample with epsilon smoothing ($\epsilon = 10^{-4}$) to prevent zero divisions. Categorizes stability:
  - $\text{PSI} < 0.10$: `stable`
  - $0.10 \le \text{PSI} \le 0.20$: `moderate_drift`
  - $\text{PSI} > 0.20$: `significant_drift`
- **KS Test Engine**: Executes two-sample Kolmogorov-Smirnov test via `scipy.stats.ks_2samp` to yield empirical distribution divergence and asymptotic p-values.
- **Batch Evaluation**: Evaluates all requested numeric features, detects overall drift status, identifies individual shifting features, and records explicit metadata (`status: SYNTHETIC_SMOKE_ONLY`, `real_data_benchmark_status: DEFERRED`).

### 2.2 Advisory Drift Sentinel (`integrations/ibm_architecture/monitoring/sentinel.py`)
- Ingests sanitized summary dictionaries containing aggregate PSI/KS stats (never raw feature matrices or labels).
- Emits typed `Proposal` objects targeting registered configuration keys.
- Operates deterministically offline by default, proposing proportional review budget expansions (e.g. from $1.5\times$ to $2.0\times$) to accommodate shift uncertainty while keeping classification policy intact.

### 2.3 Deterministic Replay Gate (`integrations/ibm_architecture/monitoring/replay_gate.py`)
- Enforces strict validation across four stages:
  1. Pydantic schema validation.
  2. Base configuration hash matching (`base_cfg_hash == frozen_cfg_hash`).
  3. Allowlisted key verification.
  4. Workload constraint verification ($0 < \text{workload\_multiple} \le 3.0$).
- Replays proposed adjustments on simulated development/validation samples without using test partitions or evaluation labels.
- Emits `ReplayEvaluationRecord` sealed with a deterministic SHA-256 hash.
- Human review methods `approve(record, approver)` and `reject(record, reviewer, reason)` govern operational transitions.

---

## 3. Verification and Test Results

Unit and integration tests in `tests/test_ibm_drift_replay.py`:
- `test_psi_calculation_stable_and_drift`: PASSED (stable $< 0.10$, shifted $> 0.20$)
- `test_feature_drift_ks_and_psi`: PASSED (accurate KS statistic and p-value)
- `test_drift_calculator_quarantine_enforcement`: PASSED (`isFraud`, `TransactionID`, `TransactionDT` rejected)
- `test_drift_calculator_synthetic_mode_telemetry`: PASSED (`status: SYNTHETIC_SMOKE_ONLY`, `real_data_benchmark_status: DEFERRED`)
- `test_drift_sentinel_offline_proposal_generation`: PASSED (advisory `Proposal` on detected drift)
- `test_drift_sentinel_returns_none_when_no_drift`: PASSED (quiet on stable distribution)
- `test_drift_sentinel_fail_closed_on_provider_error`: PASSED (fails closed safely on exception)
- `test_replay_gate_validation_and_human_approval_lifecycle`: PASSED (`AWAITING_HUMAN_APPROVAL` $\to$ `APPROVED_ACTIVE`)
- `test_replay_gate_rejects_mismatched_base_hash`: PASSED (rejected on outdated configuration)
- `test_replay_gate_rejects_excessive_workload_multiple`: PASSED (rejected on $> 3.0\times$ multiple)
- `test_replay_gate_human_rejection`: PASSED (audit trail records human rejection reason)

All 11 Phase 7 tests passed with zero failures.
