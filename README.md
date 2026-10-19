# SignalGate — Shift-Aware Fraud Triage Platform

> **Status:** `SYNTHETIC_SMOKE_ONLY`
> **Notice:** All metrics, models, datasets, and replay logs in this repository represent synthetic development fixtures. They are designed exclusively for offline architectural verification and research demonstration. They must never be cited or interpreted as real-world financial fraud benchmarks or commercial production clearance guarantees.

---

## Executive Overview

SignalGate is an open, verifiable, shift-aware fraud triage platform designed to address the critical gap in machine learning fraud operations: **operational capacity bottlenecks under covariate shift and model disagreement**.

Standard fraud detection systems often assume unlimited human review capacity or rely on arbitrary, uncalibrated score thresholds. In contrast, SignalGate couples calibrated gradient-boosted risk estimation with epistemic disagreement measurement and hard capacity governance.

### Core Architecture Pillars

1. **Primary Estimator:** Histogram-based Gradient Boosting (`HistGradientBoostingClassifier`, scikit-learn), fitted on 6,000 synthetic transaction records with native non-linear interaction modeling.
2. **Probability Calibrator:** Platt Scaling (Sigmoid Logistic Regression) fitted on a held-out calibration split (1,000 records) to convert uncalibrated decision margins into well-calibrated posterior probabilities $p \in [0, 1]$.
3. **Epistemic Disagreement ($u_2$):** Inter-model prediction variance residualized against risk rank, isolating true novel covariate shift from mere elevated baseline risk.
4. **Analyst Review Capacity Governor:** Enforces a strict operational quota ($B = 130$ reviews, matching $1.5\times$ training prevalence, or $6.525\%$ capacity). When reviewer capacity is exhausted, escalations are shunted into an explicit **HELD / DEFERRED (R6)** lane rather than silently defaulting to unmonitored clearance.
5. **Deterministic Policy Routing:**
   - **R1_HIGH_RISK:** $p \ge 0.084705$ ($t_{\text{alert}}$) $\rightarrow$ `FRAUD_ALERT` (Exempt from review quota; never routed to routine).
   - **R2_INTERMEDIATE_RISK:** $p \ge 0.071002$ ($t_{\text{review}}$) $\rightarrow$ `MANUAL_REVIEW` (Consumes review quota $B$).
   - **R3_MODEL_DISAGREEMENT:** $u_2 \ge 0.526773$ ($u_{\text{threshold}}$) $\rightarrow$ `MANUAL_REVIEW` (Consumes review quota $B$).
   - **R5_LOW_RISK_RELIABLE:** $p < 0.071002 \text{ AND } u_2 < 0.526773$ $\rightarrow$ `ROUTINE` (Zero-touch automated pass).
   - **R6_CAPACITY_DEFERRED:** Escalations $> B$ ($130$ cases) $\rightarrow$ `HELD / DEFERRED` (Stored for deferred audit; zero silent leakage).

---

## Installation & Environment Setup

### 1. Prerequisites
- **Python:** 3.10+ (Python 3.11 recommended)
- **Node.js:** v18+ with `npm`

### 2. Backend Dependencies
```powershell
# Create and activate Python virtual environment
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# Install exact pinned dependencies from lockfile
pip install -r backend/requirements.lock
```

### 3. Frontend Dependencies
```powershell
cd frontend
npm install
cd ..
```

### 4. Environment Variables Configuration
Copy the template `.env.example` to `.env`:
```powershell
# Windows PowerShell
Copy-Item .env.example .env

# Linux / macOS
cp .env.example .env
```
The `.env.example` file contains safe placeholders:
- `SIGNALGATE_AUDIT_KEY`: Optional secret key for HMAC-SHA256 signing of the cryptographic audit ledger. If left unset or blank, the audit chain operates in standard hash-chained mode.
- `VITE_API_BASE_URL`: Base URL for the FastAPI backend (defaults to `http://127.0.0.1:8000`).

---

## Operating Modes & Evidence Scope

SignalGate operates with strict boundaries across three mutually isolated operational modes:

| Operating Mode | Primary Purpose | Data & Artifact Requirements |
| :--- | :--- | :--- |
| `SYNTHETIC_SMOKE_ONLY` | **Default clone mode.** 100% offline development, interactive UI demo, and unit testing. | Uses repository-included `data/synthetic_smoke_fixture.csv` (10,000 synthetic transactions) and pre-fitted synthetic model fixtures. No external downloads required. |
| `IEEE_CIS_OFFLINE_BENCHMARK` | Offline research benchmark against the IEEE-CIS Fraud Detection dataset. | Requires local raw competition CSV files in `data/raw/` and locally fitted model artifacts in `models/artifacts/ieee_cis_v1/`. |
| `LIVE_SOURCE_NOT_CONNECTED` | Transparent boundary disclosure. | Signals that live banking feeds, payment settlement gateways, and TEE enclaves are not connected. |

### IEEE-CIS Benchmark Dataset & Model Reproduction

> **Note on Fresh Clones:** A fresh GitHub clone runs out-of-the-box in `SYNTHETIC_SMOKE_ONLY` mode. Real-data inference requires independently providing the competition dataset and generating the local model bundle as described below.

1. **Obtaining the Raw Dataset:**
   - Download the raw IEEE-CIS Fraud Detection competition files independently from Kaggle:
     ```bash
     kaggle competitions download -c ieee-fraud-detection
     ```
   - Extract the CSV files directly into `data/raw/`:
     - `data/raw/train_transaction.csv`
     - `data/raw/train_identity.csv`
     - `data/raw/test_transaction.csv`
     - `data/raw/test_identity.csv`
     - `data/raw/sample_submission.csv`
   - *Security Note:* The `data/raw/` directory is excluded from version control via `.gitignore` to adhere to dataset licensing and size limits.

2. **Generating Model Artifacts Locally:**
   - Fit the 391-feature pipeline, 3-member heterogeneous ensemble, and Platt calibrator locally:
     ```powershell
     python -m integrations.ibm_architecture.models.trainer
     ```
   - This writes serialized `.joblib` model artifacts to `models/artifacts/ieee_cis_v1/` and evaluates resource constraints.
   - *Distribution Note:* The trained model bundle contains large binary weights (~115 MB `ensemble.joblib`) and is excluded from git version control.

3. **Executing the Offline Benchmark:**
   - Run the pre-registered benchmark runner and paired bootstrap evaluation:
     ```powershell
     python scripts/run_ieee_benchmark.py
     ```
   - All results, metrics, and audit chains are written to `results/ieee_cis_v1/`.

---

## Offline Demo Quickstart (Windows)

The SignalGate demonstration runs **100% locally and offline**. In `SYNTHETIC_SMOKE_ONLY` mode, it requires no external database, no API keys, no cloud credentials, and no external dataset downloads.

### Option A: One-Click Windows Launcher

Double-click or run from PowerShell:
```cmd
scripts\start_demo.bat
```
This launcher checks prerequisites, executes the deterministic artifact validator, detects whether services are already running, and spawns the backend and frontend dev servers.

### Option B: Two-Terminal Manual Startup

#### Terminal 1 — FastAPI Backend API
```powershell
# In project root
python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000
```
- Health Check: `http://127.0.0.1:8000/api/health`
- Readiness Status: `http://127.0.0.1:8000/api/status`
- OpenAPI Swagger: `http://127.0.0.1:8000/docs`

#### Terminal 2 — Vite React Frontend
```powershell
# In frontend directory
cd frontend
npm run dev -- --host 127.0.0.1 --port 5173
```
- Frontend Dashboard: `http://127.0.0.1:5173/overview`

### Graceful Shutdown
- Simply close the two command windows spawned by the demo script (`SignalGate Backend API` and `SignalGate Frontend`), or press `Ctrl+C` in each window.
- Alternatively, run the safe shutdown script to terminate only the processes listening on demo ports 8000 and 5173 without affecting unrelated Python or Node processes:
```cmd
scripts\stop_demo.bat
```


---

## 3-to-5 Minute Demonstration Walkthrough

Follow this curated walkthrough path to inspect the complete platform:

### 1. Operational Overview (`/overview`)
- **Key Metrics:** View total tested transactions ($N = 2,000$), total synthetic fraud ($111$), analyst workload budget ($130$ reviews, $6.525\%$), and baseline comparison ($9.01\%$ recall).
- **Outcome Distribution Bar:** Examine the mutually consistent canonical split:
  - `FRAUD_ALERT`: 11 cases ($0.55\%$)
  - `MANUAL_REVIEW`: 119 cases ($5.95\%$) (100% capacity consumed)
  - `ROUTINE`: 896 cases ($44.80\%$)
  - `HELD / DEFERRED`: 974 cases ($48.70\%$)
- **Signal Core Radar:** Interactive 2.5D planar radar disk mapping transactions across risk rings and uncertainty axes. Click nodes to inspect stage contracts, or toggle to the 2D SVG vector fallback.
- **Theme Toggle:** Click the Sun/Moon toggle in the top bar to switch between Dark Obsidian (`#0B0E14`) and Light Slate (`#F4F6F9`) with soft purple navigation boxing.

### 2. Policy Comparison (`/policy-comparison`)
- **Matched-Capacity Benchmark:** Compare SignalGate against B1 (Fixed Threshold), B2 (Top-B Risk), B3a (Confidence Deferral), and B4 (Random Control).
- **Budget Selector:** Switch between pre-registered budget points (`1.0x`, `1.5x`, `2.0x`, `3.0x`).
- **Paired Bootstrap CI:** Inspect the empirical finding: 95% CI is `[-2.75 pp, +2.75 pp]` with `is_conclusive = false`, demonstrating that SignalGate achieves matched recall without claiming superiority while safely sequestering 974 unreviewed transactions.

### 3. Shift Storm Replay (`/shift-storm`)
- **Offline Telemetry Stream:** Step through the 2,000 evaluation rows.
- **Transport Controls:** Use Play, Pause, Step Forward/Back, Scrub Slider, and Speed Multipliers (`0.5x`, `1x`, `2x`, `5x`).
- **Transaction Dossier:** Select any row in the streaming table to populate its full feature payload, risk score $p$, disagreement $u_2$, and governance decision.

### 4. Case Explorer (`/case-explorer`)
- **Search & Filtering:** Search by Case ID (e.g. `2995000`), filter by triage action (`FRAUD_ALERT`, `MANUAL_REVIEW`, `ROUTINE`, `DEFER`), and paginate.
- **Drawer Inspection:** Click "Inspect Dossier" to slide out the detailed transaction ledger.

### 5. Real-Time Scoring Sandbox (`/sandbox`)
- **Preset Scenarios:** Click "Clean Routine", "High-Risk Alert", or "Disagreement Edge Case" to populate the feature JSON editor.
- **Target Leakage Guardrail:** Try typing `"isFraud": 1` or `"TransactionID": "123"` into the JSON. Notice the immediate client-side error and backend HTTP 422 rejection.
- **Live Scoring:** Click "Score Payload" to evaluate through the in-memory HGB + Calibrator pipeline in $< 15\text{ms}$.

### 6. Audit Trail & Ledger (`/audit-trail`)
- **Immutable Log:** View decisions logged to `logs/audit.jsonl`.
- **Exporting:** Click "Export JSONL" or "Export CSV" to trigger clean file downloads via `/api/audit/export`.

### 7. Model Governance Card (`/model-card`)
- Review frozen thresholds, model parameters, reliability calibration curve, and SHA-256 artifact hashes.

---

## Verification & Test Commands

### 1. Deterministic Artifact Integrity
```powershell
python scripts/validate_artifacts.py
# Exit Code: 0 (All hashes, splits, thresholds, and result counts verified)
```

### 2. Backend Unit & API Tests
```powershell
python -m pytest tests/
# 108 passed in ~11s (Exit Code: 0)
```

### 3. Frontend Type Checking
```powershell
cd frontend
npx tsc --noEmit
# Exit Code: 0 (Zero type errors)
```

### 4. Frontend Component Tests
```powershell
cd frontend
npm test -- --run
# 3 passed (Exit Code: 0)
```

### 5. Production Bundle Compilation
```powershell
cd frontend
npm run build
# 2,432 modules transformed cleanly (Exit Code: 0)
```

---

## Repository Structure

```
├── backend/
│   └── app/
│       ├── main.py              # FastAPI app factory, CORS, exception handlers
│       ├── routers/             # API route controllers (overview, policies, cases, replay, audit, scoring)
│       ├── schemas.py           # Pydantic v2 request/response contracts
│       └── services/            # Artifact reading, caching, and inference services
├── config.yaml                  # Frozen project configuration & threshold parameters
├── data/
│   └── synthetic_smoke_fixture.csv # 10,000 synthetic transaction rows (SHA-256 verified)
├── docs/
│   ├── runbook.md               # Operational runbook & offline demo guide
│   ├── phase9_e2e_report.md     # Phase 9 integration report
│   ├── final_frontend_consistency_report.md # Source-of-truth reconciliation
│   └── api_contract.md          # OpenAPI contract specification
├── frontend/
│   ├── src/
│   │   ├── app/AppShell.tsx     # Shell navigation, header, sidebar, theme context
│   │   ├── components/          # SignalCoreScene (3D radar), Fallback (2D SVG), MetricCard
│   │   ├── features/            # 8 routed dashboard feature pages
│   │   ├── lib/api/             # Strongly typed API client & error handling
│   │   └── styles/              # Design tokens (tokens.css), layout, components
│   └── package.json             # Vite 5, React 18, Three.js, Recharts
├── models/
│   └── artifacts/               # Fitted HGB, sigmoid calibrator, ensemble & residualizer
├── policy/
│   ├── router.py                # Core decision router (R0-R6)
│   ├── governor.py              # Capacity governor (quota enforcement)
│   └── frozen_policy.json       # Immutable frozen policy definition
├── results/
│   ├── results.json             # Canonical consolidated evaluation artifact
│   ├── g3_test_look.json        # Planned test-look #1 canonical evaluation
│   ├── split_report.json        # Train/calib/val/test split indices and hash
│   └── cases.jsonl              # 2,000 sequential offline test replay records
└── scripts/
    ├── start_demo.bat           # Windows offline demo launcher
    └── validate_artifacts.py    # Deterministic read-only artifact validator
```

---

## Technical Disclosures & Limitations

1. **Synthetic Data Only:** All transactions are generated from statistical distributions mimicking credit card payment patterns. No real customer PII or cardholder data is contained in this repository.
2. **Inconclusive Superiority:** At the primary evaluation budget ($B = 130$ reviews), SignalGate and the baseline B2 policy achieve an identical point recall of $9.01\%$ ($10/111$ fraud cases caught). The paired percentile bootstrap 95% confidence interval is $[-2.75\text{ pp}, +2.75\text{ pp}]$, spanning zero. Superiority is explicitly not claimed on this smoke fixture.
3. **SHAP Disabled:** Tree SHAP local feature attributions are intentionally disabled in the static smoke protocol to prevent slow Python execution times.
4. **Offline Scope:** The scoring sandbox operates entirely in memory and logs records to a local JSONL file; it does not initiate payment settlement transactions.
