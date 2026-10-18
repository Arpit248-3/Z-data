**SignalGate**

Shift-Aware Fraud Triage

**INTEGRATED BLUEPRINT v2.1**

IBM Z Datathon 2026 \| 17-18 October 2026

Theme: Real-Time AI for Critical Decisions  
Platform target: IBM LinuxONE Community Cloud  
Domain: Transaction fraud triage

*Prepared 16 October 2026*

> **Project status and integrity rule**
>
> Proposed decision-support prototype. All performance, value, latency and robustness gains remain hypotheses until measured on the chosen data and environment. Synthetic stress tests will be labelled; no real payment will be approved, rejected or blocked.

# Document Guide

This integrated v2.1 document merges the original SignalGate v2.0 blueprint with the enhancement report. Useful additions are placed in the sections where the team will implement or evaluate them; feasibility-sensitive ideas remain optional rather than becoming unsupported commitments.

| **Section** | **Contents**                                         |
|-------------|------------------------------------------------------|
| 0           | Change log and full gap analysis                     |
| 1           | Executive summary and win thesis                     |
| 2           | Problem statement and hypotheses                     |
| 3           | Solution design, architecture and routing            |
| 4           | Differentiation and judging alignment                |
| 5           | Data plan, feature engineering and shift scenarios   |
| 6           | Experimental design, metrics and acceptance criteria |
| 7           | Execution gates, timeline and role assignments       |
| 8           | Repository, module contracts, audit schema and tests |
| 9           | Shift Storm demo and five-minute pitch               |
| 10          | Technical hardening notes                            |
| 11          | Risks and responses                                  |
| 12          | Responsible AI and model/policy card                 |
| 13          | Readiness and submission checklists                  |
| 14          | References and claim status                          |

> **How to read priorities**
>
> CORE = required for a credible minimum prototype. CONDITIONAL = implement only if the environment and validation support it. STRETCH = do only after the core pipeline and fair evaluation are complete.

# 0. What v2.1 Changes: Gap Analysis

v2.0 established a sound experiment-first design. v2.1 retains its integrity core and integrates feature-level explanations, an explicit model/runtime feasibility check, safer feature engineering, stronger disagreement diagnostics, optional conformal and learned-deferral comparisons, a segment-level escalation check, and a more concrete demonstration.

## 0.1 Original v1-to-v2 gaps retained

| **\#** | **Gap in earlier plan**                        | **v2.1 treatment**                                                                                          |
|--------|------------------------------------------------|-------------------------------------------------------------------------------------------------------------|
| 1      | No time for the original pre-event plan        | Night-before readiness phase and hard execution gates                                                       |
| 2      | Review rate was undefined                      | Touched rate = FRAUD_ALERT + MANUAL_REVIEW, divided by all transactions                                     |
| 3      | Calibration could be misread as better ranking | Calibration supports probability interpretation and thresholds; monotone calibration does not reorder cases |
| 4      | Cited confidence-deferral baseline was missing | Explicit confidence baseline plus optional conformal comparison                                             |
| 5      | Reliability method was undecided               | Defined disagreement and novelty candidates with keep-or-drop rule                                          |
| 6      | Shift evidence depended on natural data drift  | Four chronological/constructed/synthetic scenarios                                                          |
| 7      | Success criteria were vague                    | Pre-registered acceptance criteria and outcome tree                                                         |
| 8      | Impact metrics lacked business context         | Assumption-labelled value model and sensitivity sweep                                                       |
| 9      | Real-time claim lacked protocol                | Warm-up, p50/p95/p99, 5,000 calls and optional two-tier inference                                           |
| 10     | No judging alignment                           | Rubric-to-evidence matrix, explicitly provisional until official rubric is obtained                         |
| 11     | Demo and pitch under-specified                 | Shift Storm, confident-miss panel, backup video and timed pitch                                             |
| 12     | Team roles too broad                           | Phase ownership, contracts, gates and single integration owner                                              |
| 13     | Possible dependency incompatibility on s390x   | scikit-learn baseline first; optional Snap ML feasibility benchmark                                         |
| 14     | Budget not tied to prevalence                  | Budgets defined at 1.0x, 1.5x, 2.0x and 3.0x training prevalence                                            |

## 0.2 v2.1 enhancement register

| **ID** | **Enhancement**                         | **Priority**          | **Integrated decision**                                                                                                             |
|--------|-----------------------------------------|-----------------------|-------------------------------------------------------------------------------------------------------------------------------------|
| E1     | Case-level feature attributions         | Conditional           | Use SHAP only if the selected model/backend is supported and latency is measured; otherwise use a clearly labelled alternative.     |
| E2     | IBM Snap ML benchmark                   | Conditional           | Attempt install/runtime check; keep scikit-learn as guaranteed fallback. No hardware-acceleration claim without verified access.    |
| E3     | Train-derived amount/card/time features | Conditional           | Fit statistics on training data only; use time-aware/lagged or cross-fitted values to prevent temporal leakage.                     |
| E4     | Rank-residual disagreement u2           | Conditional           | Compare raw u and u2; fit residualizer/scaling on calibration/validation data, freeze before test.                                  |
| E5     | Conformal deferral baseline             | Stretch               | Implement correctly from class-conditional calibration scores; coverage claims rely on exchangeability and can degrade under shift. |
| E6     | Concrete scenario-value table           | Conditional           | Use measured recall and labelled assumptions; dollar value is scenario output, not observed savings.                                |
| E7     | Segment-level escalation disparity      | Conditional           | Report segment counts/rates and caveats; a ratio is a screening signal, not a fairness certification.                               |
| E8     | Learned post-hoc deferral               | Stretch               | Requires a separate deferral-fit split or cross-fitting; never fit and assess on the same validation rows.                          |
| E9     | Prune correlated V-features             | Conditional           | Compute correlations on training only; freeze dropped columns; measure memory/time benefit instead of promising it.                 |
| E10    | Confident-miss live counter             | Core demo enhancement | Compare baseline and SignalGate ROUTINE-lane fraud counts from frozen labelled test replay.                                         |
| E11    | Version-safe calibration                | Core readiness task   | Probe installed scikit-learn API; use FrozenEstimator where supported or a tested manual sigmoid fallback.                          |

> **Non-negotiable integrity core**
>
> Preserve the chronological split; pre-register the primary 1.5x-prevalence budget; use the same test rows across policies; paired bootstrap confidence intervals; signal keep-or-drop; fail-safe routing; two logged test looks (G3 and G5); frozen configuration; and make reproduce. Do not trade these away for dashboard polish.

# 1. Executive Summary and Win Thesis

One line: SignalGate is a reliability gate for fraud models. It decides when to trust a score, when to raise an alert, and when to hand a transaction to a human, and measures performance by fraud missed at equal analyst workload.

## 1.1 Thirty-second pitch

> **Pitch**
>
> Fraud models can be confidently wrong, while analysts have limited review capacity and fraud patterns change. SignalGate combines a calibrated risk score with model disagreement and optional novelty signals, routes cases into three operational lanes, and evaluates whether those signals catch more fraud at the same workload. The pipeline is benchmarked on LinuxONE where the environment permits, with honest latency, shift, and uncertainty reporting.

## 1.2 Three claims we will test

| **Claim**                  | **Evidence required**                                                                                                                             |
|----------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------|
| Better use of analyst time | More fraud caught at the same touched rate, or equivalent recall at lower touched rate, versus the risk-only budgeted baseline.                   |
| Safer under shift          | Smaller recall degradation than baseline on pre-defined real/constructed and synthetic shift scenarios.                                           |
| Real-time and auditable    | Measured p50/p95/p99 under declared conditions, reason codes, optional feature attribution, and reproducible logs on the actual test environment. |

## 1.3 Why this approach is credible

- It evaluates a decision layer rather than claiming a fundamentally new classifier or uncertainty algorithm.

- It compares against strong risk-ranking, confidence, and random controls.

- It separates naturally observed chronology from constructed holdout and synthetic stress tests.

- It can present a negative result honestly and show which signal did or did not add value.

- It does not imply a real payment connection, production readiness, or a specific accelerator unless verified.

# 2. Problem Statement

## 2.1 Users and context

A fraud-operations team at a bank or payment processor reviews only a limited number of transactions per day. Transactions arrive continuously and may require a decision within a latency budget. A conventional model emits a risk score and applies a fixed threshold, but a low score is not a guarantee that the prediction is reliable.

## 2.2 Core failure modes

| **Failure mode**       | **Operational consequence**                                                                                 |
|------------------------|-------------------------------------------------------------------------------------------------------------|
| Silent misses          | An unfamiliar fraud pattern receives a low score and stays in the ROUTINE lane.                             |
| Alert fatigue          | Lowering a threshold catches more cases but floods analysts with false alerts.                              |
| Invisible drift        | Input characteristics change while the system provides no indication that model behavior may have degraded. |
| No explicit abstention | The classifier does not naturally say that it lacks sufficient evidence for an automatic decision.          |
| Unbounded escalation   | If every uncertain case is sent to review, the queue can exceed capacity and increase latency.              |

## 2.3 Decision to support

For each transaction, select ROUTINE, FRAUD_ALERT, or MANUAL_REVIEW so that fraud detected by count—and, as a secondary scenario measure, by transaction amount—is improved under a declared review-capacity budget and latency target. ROUTINE means the policy did not escalate a case; it is not a guarantee of legitimacy or an approval.

## 2.4 Research question

At a fixed touched-rate budget, does adding model disagreement and novelty to a calibrated fraud-risk score catch more fraud than risk-score ranking alone, and does any advantage persist or grow under distribution shift?

## 2.5 Falsifiable hypotheses

| **Hypothesis**            | **Test**                                                                                                                        |
|---------------------------|---------------------------------------------------------------------------------------------------------------------------------|
| H1 - Primary              | Risk plus a validated disagreement signal improves recall at matched touched rate versus B2 risk ranking.                       |
| H2 - Calibration          | Sigmoid or isotonic calibration improves Brier score/ECE where appropriate, but does not itself improve ranking when monotonic. |
| H3 - Shift                | On S2 and/or S3, SignalGate has a smaller recall loss from S0 than the risk-only baseline.                                      |
| H4 - Optional latency     | Two-tier inference reduces average latency while recall loss remains within a tolerance set before evaluation.                  |
| H5 - Optional explanation | Case-level feature attribution improves audit usefulness without violating latency and model-support constraints.               |

> **Scope guardrail**
>
> This is a decision-support simulation. It does not connect to live payment rails and does not authorize, approve, reject, or block actual financial transactions.

# 3. Solution Design

## 3.1 Architecture

Transaction -> Validation/preprocessing -> Train-selected features -> Base fraud model  
-> Calibration (p) -> Reliability layer (u or u2, optional novelty n) -> Router/governor  
-> Action + reason code -> JSONL audit log -> Shift Storm dashboard  
  
Separate batch monitor: rolling-window PSI/KS -> drift panel (not direct proof of per-case fraud)  
Optional explanation stage: feature attribution for escalated cases, only if supported and timed.

## 3.2 Component decisions

| **Component**       | **Core decision**                                                                                                                   | **Fallback / guardrail**                                                                                                                                |
|---------------------|-------------------------------------------------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------|
| Base model          | scikit-learn HistGradientBoostingClassifier; logistic regression sanity baseline.                                                   | Verify actual sklearn version and input types on s390x. Try Snap ML only as a parallel feasibility/latency benchmark; no primary switch until verified. |
| Calibration         | Compare sigmoid and isotonic on calibration data using Brier score and ECE on validation.                                           | Use FrozenEstimator API when supported; otherwise use a version-tested or manual sigmoid fallback. Calibration set is disjoint from model fitting.      |
| Disagreement u      | Ensemble of up to five models with different seeds/subsamples; standard deviation of predicted probabilities.                       | Start with three if time/memory is tight. Report Spearman correlation of u and p; test rank-residual u2 if useful.                                      |
| Novelty n           | Isolation Forest OR train-vs-recent domain classifier on stable features.                                                           | Choose one on validation. Fit on training only. Drop if it does not improve a matched-budget validation objective.                                      |
| Batch drift monitor | PSI and KS tests on selected features over rolling windows.                                                                         | Thresholds are monitoring heuristics, not a fraud verdict. Monitor feeds dashboard, not automatic fraud classification.                                 |
| Governor            | When queue load exceeds budget, rank escalated cases by a validation-tuned score.                                                   | Normalize p, u and n before combining. Deferred cases must be shown as deferred/held, never silently ROUTINE.                                           |
| Audit log           | One JSONL record per decision: p, signals, action, reason, latency, hashes.                                                         | Add optional feature attributions and stage status. Never imply that a rule code is a causal explanation.                                               |
| Case explanation    | Optional top-three local feature contributions for FRAUD_ALERT/MANUAL_REVIEW.                                                       | TreeExplainer compatibility with the chosen estimator must be tested. Unsupported models use a separately labelled fallback or skip local explanation.  |
| Feature engineering | Optional train-derived amount/card frequency ratios, log amount, amount fraction, cyclic time features; optional V-feature pruning. | No raw TransactionID/TransactionDT enters model matrix. Time-derived transformations and aggregates must be leakage-safe.                               |

## 3.3 Routing logic and reason codes

| **Lane**        | **Trigger**                                                | **Reason code**       |
|-----------------|------------------------------------------------------------|-----------------------|
| FRAUD_ALERT     | Calibrated p >= t_alert                                   | R1_HIGH_RISK          |
| MANUAL_REVIEW   | t_review <= p < t_alert                                  | R2_INTERMEDIATE_RISK  |
| MANUAL_REVIEW   | Low p but u/u2 >= u_max                                   | R3_MODEL_DISAGREEMENT |
| MANUAL_REVIEW   | Low p but n >= n_max                                      | R4_UNFAMILIAR_INPUT   |
| MANUAL_REVIEW   | A required signal is missing/invalid or model stage failed | R0_SIGNAL_UNAVAILABLE |
| ROUTINE         | No trigger; reliability policy permits routine lane        | R5_LOW_RISK_RELIABLE  |
| HELD / DEFERRED | Escalation governor cannot admit case immediately          | R6_CAPACITY_DEFERRED  |

```python
def route(p, u, n, cfg, stage2_status='computed'):
    # Validate p and any signals required by the active policy.
    # Missing/invalid required values -> MANUAL_REVIEW, R0.
    # A deliberately skipped second stage is allowed only if the
    # frozen, validated low-risk rule explicitly permits it.
    # p >= t_alert -> FRAUD_ALERT, R1_HIGH_RISK
    # p >= t_review -> MANUAL_REVIEW, R2_INTERMEDIATE_RISK
    # excessive u/u2 -> MANUAL_REVIEW, R3_MODEL_DISAGREEMENT
    # excessive novelty -> MANUAL_REVIEW, R4_UNFAMILIAR_INPUT
    # capacity overflow -> HELD/DEFERRED, R6_CAPACITY_DEFERRED
    # otherwise -> ROUTINE, R5_LOW_RISK_RELIABLE
```

Principles: a high score is not an approval; novelty is not proof of fraud; required signal failure is fail-closed; capacity overflow is visible; and intentionally skipped stage-two inference is not confused with a failed signal.

## 3.4 Threshold selection

Set t_review, t_alert, u_max and n_max using training/calibration/validation partitions only. Start with quantiles and a coarse grid to maximize validation recall (or an explicitly defined value objective) subject to touched rate <= budget. Freeze the configuration and hash at G3. Never tune against final-test labels.

## 3.5 Two-tier inference (stretch)

Stage 1 scores every transaction with the fast model and any cheap, validated check. Stage 2 computes the ensemble disagreement only outside the pre-defined low-risk region. Report stage-two fraction, p50/p95 latency, touched rate and recall difference versus always running stage 2. The router must explicitly distinguish an allowed stage-two skip from an unavailable required signal.

## 3.6 Feature-level explanations (conditional)

For escalated cases, show the top three feature contributions only if the selected model and installed explanation library have verified support. Treat SHAP values as model-output attributions under a specified explainer configuration—not as proof of causation, fraud, or intent. If TreeExplainer does not support HistGradientBoostingClassifier in the installed combination, do not force an unsupported private API; use a compatible explainer/model or skip the feature-attribution promise.

| **Field**               | **Meaning**                                                                                         |
|-------------------------|-----------------------------------------------------------------------------------------------------|
| reason                  | Routing rule (R0-R6) that caused the lane/queue action.                                             |
| feature_attributions    | Optional top-k signed local contributions, including method and output scale; null if not computed. |
| explanation_status      | computed / not_applicable / unsupported / timeout / error.                                          |
| latency_ms              | End-to-end scoring/routing latency with explanation time stated separately if asynchronous.         |
| cfg_hash and split_hash | Identify the frozen policy and data split used to reproduce the result.                             |

# 4. Why SignalGate Stands Out

## 4.1 Positioning

SignalGate is not proposing a new fraud classifier or a new general-purpose uncertainty algorithm. It is an applied reliability and routing layer, anchored in prior work on confidence-based cascade deferral (Jitkrittum et al., NeurIPS 2023). Its contribution is a measured, capacity-aware and shift-tested implementation.

## 4.2 Technical insights

1.  In rare-event classification, confidence-based deferral may rank cases much like risk scores. B3 tests rather than assumes whether this is sufficient; u/u2 and novelty remain only if they add independent value.

2.  Monotone probability calibration does not reorder cases. Its value is probability interpretation, threshold meaning and cost-sensitive decisions, not automatic ranking improvement.

3.  Uncertainty and novelty are not synonymous with fraud. They are reasons to review whether an automatic decision is justified.

4.  Explanations and accelerator benchmarks increase credibility only when compatible, measured and appropriately qualified.

## 4.3 Differentiators

- Pre-registered chronological evaluation with paired confidence intervals.

- Risk-only, confidence, random, optional conformal and optional learned-deferral comparisons.

- Four shift scenarios with S3 clearly labelled synthetic.

- Value sensitivity analysis rather than unsupported savings claims.

- Fail-closed routing, explicit deferred lane and auditable reason codes.

- Optional case-level attributions with compatibility and latency checks.

- LinuxONE inference measurements, with Snap ML activated only if the environment supports it.

- Reproducibility through frozen configuration, hashes and one-command regeneration.

## 4.4 Rubric alignment (provisional)

Replace this mapping with the event organizers’ official rubric as soon as it is available. The criteria below are internal planning assumptions, not official judging weights.

| **Likely criterion** | **What we demonstrate**                                         | **Evidence artifact**                             |
|----------------------|-----------------------------------------------------------------|---------------------------------------------------|
| Theme fit            | Real-time triage under review and latency constraints           | Latency table; stream replay                      |
| Innovation           | Reliability gate, disagreement, novelty, explicit governor      | Architecture; ablation                            |
| Technical depth      | Leakage-safe splits, calibration, shift, statistics             | Experiment report and CIs                         |
| IBM Z / LinuxONE     | End-to-end execution on actual supplied environment             | VM evidence; benchmark log; CPU/software metadata |
| Impact               | Fraud caught at fixed workload; scenario value sensitivity      | Measured recall chart; assumptions table          |
| Feasibility          | Working pipeline, tests and reproducibility                     | README; make targets; test outputs                |
| Responsible AI       | Human-in-the-loop, fail-closed handling, limits, segment checks | Model/policy card; audit log                      |
| Presentation         | Shift Storm, backup video and consistent results                | Pitch, slides, frozen results.json                |

# 5. Data Plan and Feature Engineering

## 5.1 Dataset decision

| **Priority**            | **Dataset**                            | **Use and constraint**                                                                                                                                                         |
|-------------------------|----------------------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| 1 - Primary candidate   | IEEE-CIS Fraud Detection (Kaggle)      | Labeled transactions and TransactionDT for chronological evaluation. Accept rules and verify access, row count, prevalence, time span and feature schema before relying on it. |
| 2 - Conditional bonus   | IBM Synthetic Data Sets                | Adopt only if appropriate labelled transaction data is confirmed available in time; do not block the core system on it.                                                        |
| 3 - Smoke-test fallback | IBM LinuxONE starter repository sample | Useful for verifying the container, imports, and basic pipeline; not automatically sufficient for shift research or final claims.                                              |

## 5.2 Baseline data handling

- Start with train_transaction.csv; merge identity data only if time and memory allow and the experiment benefits from it.

- Down-cast numeric features to appropriate compact types and use categorical representations only where the model supports them.

- Use a time-ordered 10% prototype subset before full training; prototype statistics do not support the final claim by themselves.

- Use TransactionDT for temporal ordering and allowed derived time features only; never feed its raw value into the model.

- Exclude raw TransactionID from model features. Audit the final feature matrix and its column manifest.

- Fit imputers, encoders, feature selection, novelty models, ensemble members and calibration components only on their designated training/calibration partitions.

- Report class prevalence and fraud counts by split. A too-small test fraud count means wider uncertainty, not permission to overstate results.

## 5.3 Chronological split

| **Partition** | **Time percent** | **Purpose**                                                                                        |
|---------------|------------------|----------------------------------------------------------------------------------------------------|
| Train         | 0-60%            | Fit base model, preprocessing and train-only statistics.                                           |
| Calibration   | 60-70%           | Fit probability calibration and any pre-defined calibration-stage transforms.                      |
| Validation    | 70-80%           | Select signal variants, thresholds, novelty settings, queue weights and optional feature settings. |
| Test          | 80-100%          | Evaluate the frozen configuration at declared test looks only.                                     |

Save split boundaries, row counts, fraud counts, prevalence and split hash. If there are too few fraud cases, adjust the evaluation plan before opening the test results and disclose the change. Do not silently change splits after inspecting outcomes.

## 5.4 Optional feature engineering module

Add data/feature_engineering.py only after a baseline runs. Candidate features are hypotheses, not guaranteed performance wins:

| **Feature**       | **Definition / intent**                                                                                                 | **Leakage control**                                                                                                                      |
|-------------------|-------------------------------------------------------------------------------------------------------------------------|------------------------------------------------------------------------------------------------------------------------------------------|
| amt_ratio_card1   | TransactionAmt divided by historical/train-derived mean for card1; unseen cards use a documented neutral/missing value. | For training rows, use chronological lagged/expanding aggregates or cross-fitting. Frozen train stats may be mapped to later partitions. |
| amt_decimal       | Fractional portion of TransactionAmt.                                                                                   | Compute from row-level amount only; retain only if validation helps.                                                                     |
| amt_log           | log1p(TransactionAmt).                                                                                                  | Row-level deterministic transform; test numeric range and missingness.                                                                   |
| card1_freq        | Frequency of card1 in allowed historical/training data.                                                                 | Counts must not use calibration/validation/test rows to derive statistics.                                                               |
| hour_sin/hour_cos | Cyclic representation derived from TransactionDT modulo a day.                                                          | Validate that modulo time semantics are meaningful; drop raw TransactionDT afterwards.                                                   |
| Missingness flags | Indicator for selected columns with meaningful missingness.                                                             | Choose columns from train/validation analysis, freeze schema.                                                                            |
| V-feature pruning | Remove one of highly correlated V1-V339 feature pairs, with correlation estimated on training only.                     | Freeze dropped-column list; apply identically to all splits; record count and benchmark actual memory/time.                              |

**Interface sketch (`data/feature_engineering.py`):**

```python
def compute_train_stats(train_df) -> dict
def add_velocity_features(df, frozen_train_stats) -> DataFrame
def fit_v_feature_pruner(X_train, threshold=0.90) -> list[str]
def apply_v_feature_pruner(X, dropped_columns) -> DataFrame
def add_missingness_indicators(df, selected_columns) -> DataFrame
```

> **Leakage warning**
>
> Do not use whole-training-window group means to create a historical row feature if that lets an earlier training row see later transactions. Use time-aware lagged features or cross-fitting for train rows; compute frozen statistics on permitted historical data for later splits.

## 5.5 Shift scenarios

| **ID** | **Scenario**             | **Construction**                                                                                                                                                                     | **Nature**                                       |
|--------|--------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|--------------------------------------------------|
| S0     | Natural chronology       | Standard untouched chronological test split.                                                                                                                                         | Real chronology                                  |
| S1     | Far-tail time            | Restrict evaluation to the last part of the test period.                                                                                                                             | Real chronology; likely smaller sample, show CIs |
| S2     | Novel segment            | Select a segment with adequate sample and fraud count; remove it from train/calibration/validation and retain it for test. Rebuild and tune that scenario using permitted data only. | Real data, constructed shift                     |
| S3     | Injected covariate shift | Perturb selected feature distributions using a saved seed.                                                                                                                           | Synthetic; label on charts, logs and slides      |

## 5.6 Data integrity rules

- Test set is evaluated at planned G3 and G5 points; log every access and configuration hash.

- No thresholds, feature choices or hyperparameters are selected using final test labels.

- Use consistent feature transforms and feature order across all splits.

- If card/device entities repeat across chronological partitions, disclose this as a limitation unless an additional entity-level evaluation is feasible.

- For S2, refit the variant without the held-out segment; choose its thresholds on that variant’s validation split, never test labels.

# 6. Experiment Design

## 6.1 Policies to compare

| **ID**         | **Policy**                                                          | **Purpose**                                                                                                                                                      |
|----------------|---------------------------------------------------------------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| B1             | Fixed threshold selected on validation                              | Conventional reference.                                                                                                                                          |
| B2             | Top-B% by risk score                                                | Strong matched-budget baseline: asks whether added signals help beyond risk ranking.                                                                             |
| B3a            | Confidence-based deferral                                           | Baseline motivated by cascade-deferral literature.                                                                                                               |
| B3b            | Class-conditional split conformal deferral (optional)               | A distinct uncertainty-set baseline; implement only with proper finite-sample quantiles and separate calibration. Its coverage assumptions can fail under shift. |
| B4             | Random escalation at the same touched rate                          | Sanity control, repeated over seeds.                                                                                                                             |
| P5             | SignalGate-U: risk plus raw or validated rank-residual disagreement | Core system candidate.                                                                                                                                           |
| P6             | SignalGate-UN: risk, disagreement and novelty                       | Stretch candidate; keep novelty only if it improves validation at matched budget.                                                                                |
| P7             | Learned post-hoc deferral (stretch)                                 | Optional learned policy using a dedicated deferral-fit split or cross-fitting; never evaluate it on the same data used to train/tune the deferral rule.          |
| Oracle ceiling | Reference bound under the declared budget                           | Context only; not an achievable deployable policy.                                                                                                               |

All policies use the same underlying primary test rows and equivalent review budgets. If a policy requires a separate fitted component, its training/calibration data and tuning budget must be documented. The optional learned-deferral policy is not a required 24-hour deliverable.

## 6.2 Touched-rate budget

touched_rate = (count(FRAUD_ALERT) + count(MANUAL_REVIEW)) / total_transactions

Both alert and manual-review lanes consume analyst time and therefore count as touched. Use budgets of 1.0x, 1.5x, 2.0x and 3.0x training-split fraud prevalence. Pre-register B-primary = 1.5x prevalence before test access. At an extremely low touched-rate budget, maximum possible recall is constrained by how many cases can be escalated; show the oracle ceiling for context.

## 6.3 Metrics

| **Group**       | **Metrics**                                                                                                               |
|-----------------|---------------------------------------------------------------------------------------------------------------------------|
| Primary         | Recall at fixed touched rate; missed-fraud rate = 1 - recall; paired difference versus B2.                                |
| Workload        | Touched rate; manual-review rate; alert rate; queue overflow/deferred count; touched rate needed for a target recall.     |
| Error profile   | Precision, false-positive rate, fraud count in each lane, fraud rate among ROUTINE cases (confident-miss rate), PR-AUC.   |
| Calibration     | Brier score, ECE and reliability diagram before/after calibration.                                                        |
| Latency         | Single-row and batch-32 p50, p95 and p99; stage-two fraction if used; explanation latency separately.                     |
| Value proxy     | Transaction-amount-weighted fraud missed/caught; scenario net-benefit sensitivity with assumptions labelled.              |
| Segment check   | Escalation rate and sample/fraud counts by ProductCD or card4 if suitable; disparity ratio only as a screening statistic. |
| Reproducibility | Seeds, config/split hashes, environment versions, test-look log and regenerated outputs.                                  |

## 6.4 Statistical protocol

- Use paired bootstrap resampling on identical test rows for each policy difference. Default blueprint: 1,000 resamples; increase if resources allow and record the count.

- Run 3-5 ensemble seeds when feasible and report mean and variation.

- If a confidence interval for a policy difference spans zero, state that the comparison is inconclusive at that resolution; do not claim statistical superiority.

- Report class prevalence and fraud counts in every tested scenario, especially S1 and any small prototype.

- Freeze thresholds/signals at G3 and record the test look. Later shift/latency evaluation at G5 uses the frozen configuration.

## 6.5 Acceptance criteria (pre-registered targets)

| **ID**         | **Proposed acceptance criterion**                                                                                        | **Interpretation**                                                    |
|----------------|--------------------------------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------|
| AC1            | At B-primary, P5 recall beats B2 by >= 2 percentage points, with 95% CI for difference above zero.                      | Primary performance claim.                                            |
| AC2            | Alternative: P5 matches B2 recall while touching at least 10% fewer transactions.                                        | Workload-efficiency claim.                                            |
| AC3            | In S2 or S3, SignalGate recall loss versus S0 is smaller than baseline loss.                                             | Shift robustness claim; S3 remains synthetic.                         |
| AC4            | ROUTINE-lane fraud rate is lower than the corresponding below-threshold fraud rate under B1/B2 at comparable budget.     | Confident-miss reduction claim.                                       |
| AC5            | Single-row p95 latency <= 50 ms under declared measurement conditions.                                                  | Engineering target, not a pre-existing result.                        |
| AC6 (optional) | Case explanation overhead stays inside a separately stated budget, e.g. <=20 ms p95, without changing action semantics. | Optional attribution feasibility target; tune only before final test. |

These are proposed engineering acceptance criteria for the project, not official Datathon judging criteria. Freeze the exact values and metric definitions after inspecting data and before the first test look. The result headline follows the outcome tree; criteria must not be moved after results are seen.

## 6.6 Scenario value model

Scenario net benefit = estimated fraud value caught  
- analyst review cost x reviewed/touched cases  
- false-alert friction cost x false alerts

| **Input**                        | **Illustrative value / source**                                       | **Required label**                                |
|----------------------------------|-----------------------------------------------------------------------|---------------------------------------------------|
| Daily volume                     | 50,000 transactions/day                                               | Scenario assumption; not measured pipeline volume |
| Fraud prevalence                 | 3.5% example from candidate benchmark only; re-check downloaded data  | Benchmark-like scenario, not real bank prevalence |
| Primary touched budget           | 1.5x prevalence = 5.25% in this illustrative scenario                 | Arithmetic derived from assumed prevalence        |
| Average fraud transaction amount | \$350 only if computed from actual selected data; otherwise leave TBD | Data-derived only after measured                  |
| Review cost                      | \$8 per review (example)                                              | Assumption; sensitivity sweep                     |
| False-alert friction             | \$2 per false alert (example)                                         | Assumption; sensitivity sweep                     |

Illustrative arithmetic only: with 50,000 transactions/day, 3.5% prevalence implies 1,750 fraud-labelled transactions/day. A +2 percentage-point recall difference would correspond to 35 additional fraud-labelled cases detected in that scenario if measured recall gain generalizes. This is not observed performance, avoided loss or guaranteed recovery. Do not put a dollar or annual uplift headline in the pitch until all inputs and the measured recall difference are available and explicitly labelled.

## 6.7 Segment-level escalation check

For a suitable categorical variable (e.g., ProductCD or card4) report group size, fraud count, touched/escalation rate, and uncertainty where feasible. A max/min escalation-rate ratio can identify a pattern for further investigation, but a ratio over 2 is not a universal fairness threshold and a zero/very small minimum rate makes the ratio unstable. Describe this as a limited benchmark-segment check, not demographic fairness certification.

## 6.8 Latency protocol

- Time scoring and routing in-process; document separately whether preprocessing and optional explanation are included.

- Warm up first, then run at least 5,000 timed calls where feasible; report single-transaction and batch-of-32 p50/p95/p99.

- Record CPU model, core count (lscpu where available), operating environment and library versions.

- Run the same code on a laptop for reference, but do not compare dissimilar workloads or imply platform advantage without measured comparability.

- If p95 exceeds 50 ms, try two-tier inference or smaller ensemble; measure recall cost and stage-two percentage.

- Optional Snap ML benchmark: attempt only if installation and supported estimator are confirmed. Keep scikit-learn as fallback. Snap ML availability in an IBM software stack does not prove that this student VM exposes a Telum/AI accelerator.

## 6.9 Outcome tree

| **Observed result**                      | **Permitted headline**                                                                                          |
|------------------------------------------|-----------------------------------------------------------------------------------------------------------------|
| AC1 or AC2 met with suitable uncertainty | More fraud caught for the same analyst time / equivalent recall at lower workload.                              |
| Only AC3 or AC4 met                      | A safety net under the tested shift or a reduction in confident misses.                                         |
| None met                                 | A reliability audit: where score-based triage was hard to beat and where signals did or did not help.           |
| AC5 missed                               | Report actual latency and, if feasible, use and measure two-tier inference. Do not claim real-time SLA success. |
| Snap ML unavailable/not supported        | Report the scikit-learn LinuxONE benchmark only; do not imply accelerator use.                                  |
| Local explanation unsupported/too slow   | Show the rule code and available evidence; label attribution as unavailable rather than fabricate SHAP output.  |

# 7. Phase-wise Execution Plan

The event plan begins with a night-before readiness phase, then phases through the 24-hour window. At each gate, pass/fail is explicit. If a gate fails, use the fallback and protect the core experiment.

## 7.1 Gate schedule

| **Gate** | **When**        | **Pass condition**                                                                                                                    | **Fallback**                                                                       |
|----------|-----------------|---------------------------------------------------------------------------------------------------------------------------------------|------------------------------------------------------------------------------------|
| G0       | Night before H0 | Container/imports work on s390x; dataset file verified; smoke fit and calibration API probe pass; repository and tests start cleanly. | Use starter sample if full data/access fails; keep primary model dependency-light. |
| G1       | H4              | Chronological split report; row/fraud counts; B1/B2 run; no identifier/time leakage.                                                  | Use time-ordered prototype subset; adjust evaluation plan before test look.        |
| G2       | H8              | Calibration chosen on validation; disagreement computed; correlation of u and p reported; keep/drop run complete.                     | Try u2 if raw u adds no value; otherwise keep simpler baseline.                    |
| G3       | H12             | Thresholds and config frozen/hashed; S0 result recorded at test look 1; AC verdicts logged.                                           | Do not retune after test look; follow outcome tree.                                |
| G4       | H15             | Novelty decision frozen; chosen shift scenarios built; optional governance/two-tier draft tested.                                     | Drop n or two-tier if fragile; keep P5 core.                                       |
| G5       | H18             | Shift results, paired CIs and latency recorded in test look 2; results freeze.                                                        | Report results as measured; stop feature development.                              |
| G6       | H21             | Demo frozen; case explanation status clear; confident-miss panel matches results; backup recording saved.                             | Offline saved-artifact dashboard or notebook fallback.                             |
| G7       | H22-H24         | Submission, repository tag, one-command reproduction and two rehearsals completed.                                                    | Cut slides/polish, not rehearsal or required submission.                           |

## 7.2 Night-before readiness

- Confirm Community Cloud access and event rules; check whether pre-event dataset download and repository work are allowed.

- Download the primary candidate if allowed; verify file hash, row count, prevalence and TransactionDT span.

- Run starter notebook; record pip freeze, sklearn version and lscpu. Check HistGradientBoostingClassifier, IsolationForest, calibration API and feature matrix path on 10k rows.

- Attempt shap import/explainer compatibility and Snap ML install as probes only; do not let either block G0 or alter the fallback.

- Create repository skeleton and pre-register the primary budget; add feature_engineering.py stubs and tests.

- Confirm official rubric, presentation time, data rules, VM memory/CPU, pip install permissions, allowed submissions and team sleep rotation.

## 7.3 Phase plan

| **Phase**                   | **Time**         | **Deliverables**                                                                                   | **Gate** |
|-----------------------------|------------------|----------------------------------------------------------------------------------------------------|----------|
| P1 Data and baseline        | H0-H4            | Environment, 10% time-ordered prototype, split report, data-quality notes, B1/B2.                  | G1       |
| P2 Model and reliability    | H4-H8            | Base model and logistic floor, calibration comparison, 3-5 member ensemble, u/u2 comparison.       | G2       |
| P3 Routing and freeze       | H8-H12           | Tested route, confidence baseline, random control, threshold selection, config hash, S0 test look. | G3       |
| P4 Shift and optional speed | H12-H15          | Chosen novelty method, PSI/KS, S1/S2/S3 if feasible, queue governor and two-tier tests.            | G4       |
| P5 Full evaluation          | H15-H18          | Paired CIs, seeds, value sensitivity, segment table, latency protocol, test look 2.                | G5       |
| P6 Demo/integration         | H15-H21 parallel | Streaming replay, confident-miss counter, case drilldown, reason-coded logs and backup video.      | G6       |
| P7 Story/submission         | H18-H24          | Model/policy card, README, deck, Q&A cards, two timed rehearsals and submission.                   | G7       |

## 7.4 Deliverable acceptance details

- P1: split counts/prevalence and hash saved; ID and raw time excluded; no leakage checks omitted.

- P2: calibration reliability diagram, Brier/ECE table, Spearman correlations of raw u and p and residualized u2 and p.

- P3: router boundary and invalid-value tests pass; config is frozen and hash stored.

- P4: shift builders reproducible from seed; synthetic scenario carries an explicit synthetic flag.

- P5: every final figure/table regenerated from results artifacts; measured and assumed results are distinguishable.

- P6: dashboard works offline from frozen results; attribution stage has measured latency and supported/unsupported status.

- P7: clean-checkout reproduction, slide numbers linked to results.json, and explicit limitations slide.

## 7.5 Team division

| **Role**                  | **Owns**         | **Primary work**                                                                                                      |
|---------------------------|------------------|-----------------------------------------------------------------------------------------------------------------------|
| R1 - Data/evaluation      | data/, eval/     | Dataset/hash, leakage-safe splits, baseline metrics, shift builders, paired bootstrap, value model and segment check. |
| R2 - Modelling            | models/          | Base model, calibration API, ensemble, disagreement, optional explanation compatibility.                              |
| R3 - Routing/research     | policy/          | Router, threshold search, baselines, queue governor, ablations and outcome tree.                                      |
| R4 - LinuxONE/integration | infra/, Makefile | Environment/version probe, end-to-end integration, latency and optional Snap ML benchmark, reproducibility.           |
| R5 - Interface/visuals    | app/, figs/      | Static plots, Shift Storm, confident-miss counter, case drilldown, backup video.                                      |
| R6 - Story/QA (optional)  | docs/, tests/    | Rubric/rules, code review, model card, QA, slides and Q&A cards.                                                      |

For a four-person team, combine R1/R2 and R4/R5. Use one integration owner; short-lived branches; \`make smoke\` as the daily minimum; merge at gates; log major decisions. A practical cut order is dashboard polish, learned deferral, optional conformal comparison, optional explanation polish, two-tier, S3, novelty, then S1. Never cut leakage controls, B2 and a defensible deferral baseline, audit logs, paired uncertainty reporting or latency measurement.

## 7.6 Time-box guide

| **Task**                             | **Time-box**                          | **Fallback**                                                                                       |
|--------------------------------------|---------------------------------------|----------------------------------------------------------------------------------------------------|
| Dataset load and split               | 2 h                                   | 10% time-ordered subset; document scope                                                            |
| Base model + calibration             | 3 h                                   | Logistic regression + sigmoid calibration                                                          |
| Ensemble disagreement                | 2 h                                   | 3 smaller members                                                                                  |
| Optional feature engineering/pruning | 1 h                                   | Skip if baseline or leakage tests blocked                                                          |
| Novelty                              | 2 h                                   | Drop n; report shift monitoring only                                                               |
| Feature explanation compatibility    | 45 min probe; time-box implementation | Skip local attribution if unsupported/slow                                                         |
| Snap ML benchmark probe              | 30 min                                | Record outcome and use scikit-learn                                                                |
| Dashboard                            | 5 h maximum                           | Notebook with same saved plots                                                                     |
| Latency protocol                     | 1.5 h                                 | At minimum compare single row and batch-32 with a disclosed smaller call count if resource-limited |

# 8. Code Contracts and Repository

Contracts allow team members to code in parallel. Implementations may remain simple, but inputs, outputs and ownership must be stable.

## 8.1 Repository layout

signalgate/  
```text
signalgate/
  Makefile # smoke | test | reproduce | demo | latency  
config.yaml # frozen budget, thresholds, seeds, feature flags  
data/  
splits.py # time-safe train/calib/val/test splits  
feature_engineering.py # optional train-fit feature transforms  
scenario_builders.py # S0-S3 scenarios  
models/  
base.py # sklearn baseline, optional Snap ML benchmark  
calibrate.py # version-safe probability calibration  
ensemble.py # u and optional rank-residual u2  
novelty.py # optional n  
explain.py # optional compatibility-tested local attribution  
policy/  
router.py | thresholds.py | governor.py | baselines.py  
eval/  
metrics.py | bootstrap.py | value_model.py | latency.py | segments.py  
app/streamlit_app.py or notebooks/demo.ipynb  
logs/audit.jsonl | test_looks.log | environment.txt  
results/results.json | tables/ | figs/  
docs/model_policy_card.md | decisions.md | pitch/  
tests/test_router.py | test_splits.py | test_metrics.py | test_features.py
```

## 8.2 Module interfaces

```python
data/splits.py  
def make_splits(df, time_col="TransactionDT") -> dict[str, DataFrame]  
def make_scenario(name, splits, seed) -> dict[str, DataFrame] # S0-S3  
  
data/feature_engineering.py  
def compute_train_stats(train_df) -> dict  
def add_velocity_features(df, frozen_stats) -> DataFrame  
def fit_v_feature_pruner(X_train, threshold=0.90) -> list[str]  
def apply_v_feature_pruner(X, dropped_columns) -> DataFrame  
  
models/base.py  
def fit_base(X_train, y_train, seed, backend="sklearn") -> Model  
def raw_score(model, X) -> ndarray  
def fit_calibrator(fitted_model, X_calib, y_calib, method) -> Calibrator  
def calibrated_p(calibrator, X) -> ndarray  
  
models/ensemble.py  
def fit_ensemble(X_train, y_train, k=5, seeds=...) -> list[Model]  
def disagreement(ensemble, X) -> ndarray  
def fit_rank_residual(raw_u_calib, p_calib) -> Residualizer  
def apply_rank_residual(residualizer, raw_u, p) -> ndarray  
  
policy/router.py  
def route(p, u, n, cfg, stage2_status) -> (action, reason)  
def route_batch(P, U, N, cfg, stage2_status) -> DataFrame  
  
eval/metrics.py  
def recall_at_touched(y, touched_mask) -> float  
def value_missed(y, amount, touched_mask) -> float  
def paired_bootstrap(y, maskA, maskB, metric, n=1000, seed=0) -> (diff, lo, hi)  
def ece(y, p, bins=10) -> float  
def escalation_rate_by_segment(actions, segment) -> DataFrame  
  
eval/latency.py  
def time_calls(fn, rows, n_calls=5000, batch=1, warmup=200) -> dict # p50/p95/p99
```

## 8.3 Pre-registered configuration

```yaml
budget_primary_multiple: 1.5  
budget_sweep: [1.0, 1.5, 2.0, 3.0]  
seeds: [11, 22, 33, 44, 55]  
split_pct: {train: [0,60], calib: [60,70], val: [70,80], test: [80,100]}  
acceptance: {AC1_pp: 2.0, AC2_reduction: 0.10, AC5_p95_ms: 50}  
bootstrap_resamples: 1000  
features: {velocity: false, v_pruning: false}  
explanations: {enabled: false, method: null}  
backend: sklearn # switch only after optional Snap ML feasibility/benchmark succeeds  
thresholds: null # written by validation-only selection, then frozen and hashed
```

## 8.4 Audit record schema

```json
{
"id": "t_000123", "ts": "...", "p": 0.031, "u": 0.002, "u_method": "raw_std",
"n": 0.71, "stage2_status": "computed", "action": "MANUAL_REVIEW",
"reason": "R4_UNFAMILIAR_INPUT", "latency_ms": 3.4,
"explanation_status": "not_computed", "feature_attributions": null,
"cfg_hash": "...", "split_hash": "...", "lane_rank": 412,
"governor_status": "admitted", "synthetic_scenario": false
}
```

The record above is a schema example only; all numeric entries are illustrative placeholders. If local feature attribution is computed, add \`method\`, \`output_scale\`, and top-k \`{feature, contribution}\` entries. Log true labels only in offline evaluation artifacts, not as a live inference input to the router.

## 8.5 Minimum test list

| **Test**                      | **What it checks**                                                                                                      |
|-------------------------------|-------------------------------------------------------------------------------------------------------------------------|
| Router invalid values         | NaN/None/Inf for required input -> MANUAL_REVIEW, R0.                                                                  |
| Router boundaries             | Values exactly at t_alert/t_review enter the documented lane.                                                           |
| No unsupported auto-clear     | High p never yields ROUTINE; high novelty alone never asserts fraud.                                                    |
| Two-tier state                | Allowed stage-two skip is distinguishable from missing/failed required signal; queue overflow becomes R6.               |
| Chronological split           | No timestamp in a later split precedes any timestamp in the prior split.                                                |
| Feature leakage               | TransactionID/raw TransactionDT not in final feature matrix; derived features are reproducible; train stats are frozen. |
| V-pruner consistency          | Columns selected on training are the same columns removed in all other splits.                                          |
| Metric sanity                 | recall_at_touched matches hand-computed toy example; budget/oracle bound respected.                                     |
| Calibration API               | Supported installed path returns probabilities in \[0,1\]; manual fallback works in smoke test.                         |
| Disagreement residual         | u2 residualizer/scaler is fit outside test; correlation and validation impact are recorded.                             |
| Conformal baseline (optional) | Prediction sets follow documented finite-sample implementation; coverage evaluated only under stated assumptions.       |
| Explanation compatibility     | Selected estimator can be explained by configured method; failed/unsupported path logs status; p95 overhead measured.   |
| Snap ML fallback              | If Snap ML import/fit fails, sklearn pipeline completes unchanged.                                                      |
| Segment check                 | results.json contains group counts/rates and handles zero/rare groups safely.                                           |
| Reproducibility               | Same seeds/config generate same model-independent metrics/artifact hashes where deterministic.                          |

# 9. Demo and Pitch

## 9.1 Shift Storm live demo

Replay held-out transactions in chronological order, side-by-side: B2 risk-budget policy and SignalGate, both under the same touched-rate budget. Midway, activate the pre-built shift scenario. Label S2 as constructed from real rows and S3 as synthetic on screen.

- Lane counters show ROUTINE, FRAUD_ALERT, MANUAL_REVIEW and held/deferred cases for both policies.

- Confident-miss counter shows how many true fraud labels remain in ROUTINE in the offline replay; do not imply labels are available in a live production stream.

- Drift panel shows PSI/KS on selected features and novelty-share trend; color thresholds must be documented and are not universal fraud rules.

- Case drill-down shows p, u/u2, n, action, reason code, explanation status and an optional top-three attribution only when supported.

- Governor panel shows capacity pressure and explicit deferred/held cases; no case disappears or silently becomes ROUTINE.

- Value strip applies only measured recall differences and clearly stated assumptions; it is labeled scenario model, not measured savings.

- The demo loads the same frozen results.json as final slides. If SignalGate loses a comparison, the screen shows it.

## 9.2 Confident-miss panel

Offline evaluation definition:  
confident_miss = (action == ROUTINE) AND (true_label == 1)  
  
Display side-by-side counters:  
B2 confident misses \| SignalGate confident misses \| transaction amount in ROUTINE fraud labels  
  
Always label as held-out benchmark replay, not live production observations.

## 9.3 Five-minute pitch script

| **Time**  | **Beat**  | **Say / show**                                                                                                                                                         |
|-----------|-----------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| 0:00-0:30 | Hook      | Show one clearly labelled benchmark example of a confident miss, using only a row verified in the frozen test results. Never pre-write a made-up 0.02 score or amount. |
| 0:30-1:10 | Problem   | Limited analyst capacity, fixed thresholds, data drift; define three lanes.                                                                                            |
| 1:10-2:00 | Solution  | Show calibrated p, disagreement u/u2, optional novelty n, router, reason codes, audit log and optional explanation.                                                    |
| 2:00-3:20 | Demo      | Run Shift Storm, confident-miss counters, one case drilldown and deferred queue.                                                                                       |
| 3:20-4:10 | Evidence  | Show recall at 1.5x budget and paired CIs vs B2/B3; shift table; value sensitivity; p95 latency.                                                                       |
| 4:10-4:40 | IBM Z fit | Show evidence of actual LinuxONE run and measured environment. Mention Snap ML/accelerator only if verified.                                                           |
| 4:40-5:00 | Close     | Human oversight, limits, honest outcome and next step.                                                                                                                 |

## 9.4 Slide outline (10 slides maximum)

1\. Title and promise. 2. Confident-wrong problem. 3. Users and decision. 4. Architecture and lanes. 5. Evaluation design and matched budgets. 6. Main result with confidence intervals. 7. Shift results. 8. Value proxy and latency. 9. Responsible AI and limitations. 10. Roadmap and ask. Appendix: reliability diagram, ablation, threshold table, split report, hashes and model/policy card.

## 9.5 Backup plan

- Record a 90-second screen capture after demo freeze.

- Run dashboard from saved artifacts with no live training or external network.

- Keep a notebook that produces the same tables.

- If explanation or Snap ML fails, show the fallback honestly; it must not break the main demo.

## 9.6 Likely judge questions

| **Question**                          | **Prepared answer**                                                                                                                                                                                              |
|---------------------------------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| What is new?                          | Not a new classifier or generic uncertainty algorithm; the contribution is an applied, leakage-safe, budget-matched evaluation of a reliability gate, with shift tests, auditable routing and value sensitivity. |
| Did it beat the baseline?             | State the measured difference and confidence interval. If inconclusive, say so and explain where signals did or did not help.                                                                                    |
| Is calibration pointless for ranking? | It does not reorder scores when the calibration mapping is monotone; it helps probability interpretation and threshold decisions.                                                                                |
| Is the shift real?                    | S0/S1 use chronology; S2 is constructed from held-out real data; S3 is synthetic and labelled.                                                                                                                   |
| Why LinuxONE?                         | The full pipeline was run and timed there if supported by evidence. No specific accelerator is claimed unless the environment proves access.                                                                     |
| Is 3.5% fraud realistic?              | No, this is a benchmark prevalence example; real portfolios may have much lower prevalence. We use multiples of prevalence and disclose limitations.                                                             |
| Can it block payments?                | No. It is a prototype; all actions are simulated and escalation is decision support.                                                                                                                             |
| Why add SHAP?                         | Only to provide model-output feature attributions if compatible and measured. It does not prove causality or replace policy reason codes.                                                                        |

# 10. Technical Hardening Notes

## 10.1 Disagreement must add information beyond risk

The standard deviation of ensemble probabilities may correlate with p, including through the shape of p(1-p). Report Spearman corr(raw_u, p) on validation. If correlation is high, test a rank-residual variant: fit a mapping from rank(p) to rank(raw_u) using calibration/validation only, subtract predicted rank from observed rank, then scale using frozen validation-derived parameters. Apply unchanged to test. Do not normalize residuals using test distribution statistics. Keep raw u or u2 only if validation recall at matched budget improves.

## 10.2 Calibration API compatibility

Probe the installed scikit-learn version at G0. Current scikit-learn documentation supports calibrating a pre-fitted classifier by wrapping it with FrozenEstimator and fitting CalibratedClassifierCV on a disjoint calibration set. Older versions need the API path supported by that environment. Retain a tested manual sigmoid fallback where necessary; fit it only on separate calibration data and verify output probability range. Do not assume a specific API solely from laptop packages.

Preferred modern path, only where installed API supports it:  
calibrated = CalibratedClassifierCV(FrozenEstimator(fitted_model), method="sigmoid")  
calibrated.fit(X_calib, y_calib)  
  
Compatibility gate:  
1. print sklearn.\_\_version\_\_  
2. import the selected symbols  
3. smoke-fit and check predict_proba in \[0,1\]  
4. record the API path in environment.txt

## 10.3 SHAP and explanation support

- SHAP TreeExplainer supports many tree ensembles, but support is estimator/version-specific; do not assume HistGradientBoostingClassifier is supported just because it is a tree model.

- At G0, import SHAP and test the exact selected model on a small batch. Measure explanation time separately from core scoring.

- If the model is unsupported, either use a compatible base model with justified validation impact, a suitable model-agnostic explainer within latency, or disable local attribution. Do not claim exact SHAP outputs from an unsupported path.

- SHAP sign/scale depends on model output and explainer configuration. Store method/output scale and explain that attribution indicates contribution to model output under that method—not causality.

## 10.4 Snap ML feasibility and performance

IBM documents Snap ML as part of the AI Toolkit for IBM Z and LinuxONE for selected ML models and environments. This does not prove that the event VM has the required package, compatible estimator, container layer, permissions, or access to a particular Telum/Telum II accelerator. At G0, attempt the documented path only if event instructions permit; record install/runtime results. Benchmark side-by-side only when the same data, preprocessing, model objective and call protocol can be compared. If unavailable, continue with scikit-learn and make no accelerator claim.

| **Backend**                  | **Platform**   | **p50 ms** | **p95 ms** | **p99 ms** | **Evidence status**                    |
|------------------------------|----------------|------------|------------|------------|----------------------------------------|
| sklearn HistGradientBoosting | LinuxONE s390x | TBD        | TBD        | TBD        | Measure                                |
| sklearn HistGradientBoosting | x86 laptop     | TBD        | TBD        | TBD        | Reference only                         |
| Snap ML supported estimator  | LinuxONE s390x | TBD        | TBD        | TBD        | Conditional on package/runtime support |

## 10.5 Feature engineering and V-feature pruning

Compute training statistics only from permitted historical training data. For each time-split, apply the same frozen feature transform. To avoid temporal leakage in train rows, use lagged/expanding or cross-fitted aggregates rather than group means that incorporate later rows. Estimate V-feature correlations on training only, save the dropped-column list, apply it consistently and report actual memory/time changes. If no useful speed or validation gain appears, drop the optional features.

## 10.6 Conformal deferral baseline

Conformal prediction produces label sets from calibration nonconformity scores and finite-sample quantiles. For a binary transaction classifier, define ROUTINE/FRAUD_ALERT from sufficiently singleton prediction sets and MANUAL_REVIEW when the set is ambiguous, under an explicitly documented policy. The sample pseudocode in the enhancement report should not be copied literally: class-conditional quantile directions and prediction-set inclusion must be verified against a correct implementation. Coverage statements assume exchangeability and can degrade when S2/S3 shift the data. Report empirical coverage and touched rate; do not promise coverage under drift.

## 10.7 Learned post-hoc deferral (stretch)

A learned deferral model could use p, u/u2 and n to estimate where the base model is likely to be wrong. It needs a dedicated deferral-fit dataset or cross-fitting to avoid training the deferral rule and assessing its improvement on the same validation examples. Tune thresholds under the workload budget using data reserved for policy selection; final test remains untouched. Implement only after core policies and their statistics are complete.

## 10.8 Statistical power and thresholds

- At the stated candidate dataset size and prevalence, estimated fraud counts per split are approximate; verify on the actual download.

- A 10% prototype subset may be enough to smoke-test code but not to confidently resolve a two-percentage-point recall difference.

- S1 may have smaller sample size; show its confidence interval and do not over-read a noisy result.

- Report validation-to-test gap for frozen thresholds; a large gap signals threshold overfit or distribution change.

- When an acceptance criterion is not met, keep it unmet in the results table; do not modify its definition after seeing data.

## 10.9 Latency realism

Single-row calls through five models may be dominated by per-call overhead. Benchmark row and micro-batch paths separately. If p95 is over target, measure two-tier inference with stage-two fraction and recall delta. Optional explanation latency belongs in a separate column and should not be silently excluded from user-visible end-to-end latency.

# 11. Risks, Triggers and Responses

| **Risk**                                   | **Likelihood**   | **Early warning**                                                 | **Response**                                                                                                                       |
|--------------------------------------------|------------------|-------------------------------------------------------------------|------------------------------------------------------------------------------------------------------------------------------------|
| No cloud access or broken container        | Low-medium       | G0 fails                                                          | Ask organizers; use local dev only for work allowed by rules; run on LinuxONE as soon as possible; keep dependency-light fallback. |
| Dataset too large                          | Medium           | Out-of-memory                                                     | Float32/categorical down-casting, time-ordered subset; record exact subset; do not claim full-data results.                        |
| Signals add nothing                        | Medium           | Keep-or-drop fails at G2                                          | Report negative result; retain simpler model and audit/decision workflow.                                                          |
| Too few test fraud cases                   | Low-medium       | Split report at G1                                                | Revise plan before test look; widen test/merge scenario only with disclosure; report wide CIs.                                     |
| Test leakage                               | Low, high impact | Extra test looks or feature matrix includes forbidden columns     | Freeze config; stop tuning; log and disclose incident; add tests.                                                                  |
| Latency target missed                      | Medium           | p95 > 50 ms at G5                                                | Try measured two-tier path, micro-batching, fewer/shallow ensemble members; report trade-off.                                      |
| SHAP unsupported/slow                      | Medium-high      | Explainer fails or too slow on selected estimator                 | Disable local attribution or select compatible approach; keep rule codes; disclose status.                                         |
| Snap ML unavailable or hardware unverified | Medium           | Import/runtime/permissions fail                                   | Keep sklearn; report only confirmed environment and timing; no accelerator claims.                                                 |
| Feature engineering leakage                | Medium           | Stats use later splits or correlated pruning sees validation/test | Fit stats/pruner on permitted training data; time-aware/cross-fit train features; assert schema tests.                             |
| Conformal coverage misrepresented          | Medium           | Quantile implementation unclear or shift invalidates assumptions  | Check implementation; report empirical coverage and assumptions; optional only.                                                    |
| Segment disparity                          | Unknown          | Large/unstable rate ratio or small group counts                   | Report group counts and rates; investigate; do not claim fairness certification.                                                   |
| Overambitious integration/team fatigue     | Medium           | Main broken >30 min; repeated merges                             | One integration owner, sleep rotation, feature freeze at G6, follow cut order.                                                     |
| Demo fails                                 | Low-medium       | Network/UI problem in rehearsal                                   | Frozen artifacts, backup video and notebook demo.                                                                                  |

# 12. Responsible AI and Model/Policy Card

| **Item**              | **Disclosure**                                                                                                                                                          |
|-----------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Intended use          | Decision support for ordering analyst review; not automatic account closure or payment blocking.                                                                        |
| Human oversight       | Every alert/review is a simulation for human investigation; ROUTINE is never described as approval.                                                                     |
| Fail-safe behavior    | Missing/invalid required signals lead to MANUAL_REVIEW, R0. Queue-capacity overflow is marked held/deferred, not ROUTINE.                                               |
| Data                  | Benchmark transaction data; prevalence may be much higher than real portfolios. Document licenses, schema and anonymization limitations.                                |
| Fairness/segment note | Show escalation rates by available benchmark categories such as ProductCD/card4 with group counts. This is exploratory and not demographic fairness proof.              |
| Explanations          | Rule reason codes identify the routing rule. Optional feature attributions describe model output according to the configured explainer, not cause or intent.            |
| Known limits          | Results do not establish production readiness. S3 is synthetic; S2 is constructed. Calibration does not guarantee any single prediction is correct.                     |
| Platform              | List OS/architecture, packages, CPU metadata and actual Snap ML/accelerator evidence if used. Do not infer hardware capabilities from “LinuxONE” alone.                 |
| Transparency          | Publish thresholds, configuration hash, split hash, random seeds, test-look log, metric definitions and results artifacts.                                              |
| Value assumptions     | Mark every review cost, friction cost, volume and financial projection as assumed unless sourced from data; distinguish transaction amount from loss avoided/recovered. |

# 13. Checklists

## 13.1 Night before / G0

- Community Cloud login works and event rules/readiness time are confirmed.

- Dataset access and license terms are verified; local file hash, row count, prevalence and time span saved.

- Container runs; sklearn/pandas/numpy versions and CPU metadata captured.

- 10k-row smoke fit, routing test and calibration API probe pass.

- SHAP compatibility/latency probe attempted; status recorded; not a blocker.

- Snap ML install/runtime probe attempted only if supported/allowed; status recorded; sklearn fallback available.

- Repository created with pre-registered B-primary, owner assignments and feature flags off by default.

- Feature engineering stats and V-pruning are train-only; tests prevent raw identifier/time leakage.

- Official rubric and submission requirements asked/confirmed; sleep and integration plan agreed.

## 13.2 Before final submission / G7

- make reproduce regenerates every required table and figure from a clean checkout on LinuxONE where required.

- results.json, config hash, split hash, environment metadata and test-look log are committed.

- every slide number traces to results.json or is labelled as an assumption/scenario.

- confidence intervals, actual class counts, scenario labels, missing criteria and measured latency are shown honestly.

- no claim about Telum, Spyre, Snap ML speedup, SHAP latency or novel algorithm beyond what is verified.

- demo uses frozen artifacts; confident-miss counters and lane metrics match offline labels.

- backup video and notebook fallback tested; two timed rehearsals completed; limitations slide included.

# 14. References and Claim Status

References are included to ground the implementation and caveats. Current package/API support, cloud entitlements and hardware availability must be verified in the actual event environment, not inferred from these links.

**\[1\]** Jitkrittum et al., “When Does Confidence-Based Cascade Deferral Suffice?” NeurIPS 2023.  
https://arxiv.org/abs/2307.02764

**\[2\]** IEEE-CIS Fraud Detection dataset / competition data page.  
https://www.kaggle.com/competitions/ieee-fraud-detection/data

**\[3\]** IBM LinuxONE Community Cloud Jupyter Lab ML starter repository.  
https://github.com/linuxone-community-cloud/jupyter-lab-ml

**\[4\]** IBM Synthetic Data Sets repository and product information.  
https://github.com/IBM/IBM-Synthetic-Data-Sets

**\[5\]** scikit-learn probability calibration documentation.  
https://scikit-learn.org/stable/modules/calibration.html

**\[6\]** scikit-learn CalibratedClassifierCV and FrozenEstimator documentation.  
https://scikit-learn.org/stable/modules/generated/sklearn.calibration.CalibratedClassifierCV.html

**\[7\]** SHAP TreeExplainer documentation; model support varies by estimator and installed version.  
https://shap.readthedocs.io/en/latest/generated/shap.TreeExplainer.html

**\[8\]** SHAP issue documenting historical lack of direct support for HistGradientBoostingClassifier; re-check present version instead of assuming support.  
https://github.com/shap/shap/issues/1028

**\[9\]** IBM AI Toolkit for IBM Z and LinuxONE, including Snap ML.  
https://www.ibm.com/products/ai-toolkit-for-z-and-linuxone

**\[10\]** IBM Community: AI Toolkit and Snap ML updates for Telum II / IBM Z and LinuxONE.  
https://community.ibm.com/community/user/blogs/abraham-varghese/2025/06/17/accelerating-enterprise-ai-with-ai-toolkit-for-ibm

**\[11\]** IBM LinuxONE Telum processor platform overview.  
https://www.ibm.com/products/linuxone/telum

**\[12\]** IBM AI on IBM Z product overview.  
https://www.ibm.com/products/z/artificial-intelligence

## 14.1 Status of claims

| **Claim type**            | **Status rule**                                                                                          |
|---------------------------|----------------------------------------------------------------------------------------------------------|
| Measured result           | Must be derived from saved results artifacts and identify dataset/split/config.                          |
| Acceptance target         | A pre-registered criterion for future evaluation; not a result.                                          |
| Scenario estimate         | Uses explicit assumptions; not observed loss prevention, recovered funds or guaranteed business savings. |
| Synthetic shift           | Always labelled synthetic in the UI, plots, logs and presentation.                                       |
| Model explanation         | Explainer/method/output scale stated; never described as causal proof.                                   |
| Snap ML / accelerator     | Only claim package, environment or hardware use that was directly checked and documented.                |
| Official judging criteria | Any mapping in this blueprint remains provisional until the organizers’ current rubric is obtained.      |

> **Final rule**
>
> Every technical addition stays only if it works in the real environment, passes leakage and routing tests, and adds measured value at a matched workload. The project can still be successful as a rigorous reliability audit if the additional signals do not improve the baseline.
