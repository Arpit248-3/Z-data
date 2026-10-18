# Testing Patterns

**Analysis Date:** 2026-10-18

## Test Framework

**Python Backend & ML Test Runner:**
- Framework: Pytest 9.1.1 (`tests/`)
- Integration Client: FastAPI `TestClient` (backed by `httpx`)
- Execution Command:
  ```powershell
  python -m pytest -o "pythonpath=." tests/
  ```
  *(Note: `-o "pythonpath=."` ensures the project root packages `backend`, `models`, `policy`, `eval`, and `data` take precedence over nested reference directories).*

**Frontend Dashboard Test Runner:**
- Framework: Vitest 2.1.8 (`frontend/`)
- Config: `frontend/vite.config.ts`
- Execution Command:
  ```powershell
  cd frontend
  npm test
  ```

## Test File Organization

**Location:**
- Python: Centrally located in root `tests/` directory.
- Frontend: Located in `frontend/src/components/__tests__/`.

**Naming:**
- Python test suites: `test_<subsystem>.py`
- Frontend test suites: `<feature_or_phase>.test.ts`

**Structure:**
```
tests/
├── test_api.py             # FastAPI REST endpoint integration tests (11 tests)
├── test_api_artifacts.py   # Artifact loading, caching, and error state tests (2 tests)
├── test_api_scoring.py     # Live scoring sandbox validation tests (3 tests)
├── test_api_security.py    # Recursive anti-leakage and payload security tests (25 tests)
├── test_bootstrap.py       # Paired bootstrap confidence interval tests (4 tests)
├── test_calibration.py     # Platt sigmoid and isotonic probability calibration tests (5 tests)
├── test_ensemble.py        # Inter-model disagreement & rank residualizer tests (5 tests)
├── test_eval_artifacts.py  # Results file schema and cryptographic hash checks (4 tests)
├── test_eval_metrics.py    # Matched-capacity metrics calculation tests (4 tests)
├── test_features.py        # Feature matrix transformation and validation (7 tests)
├── test_metrics.py         # Baseline comparison metrics (B1-B4) tests (7 tests)
├── test_models.py          # Estimator inference and decision boundary tests (4 tests)
├── test_phase1.py          # Data ingestion and schema contract verification (4 tests)
├── test_router.py          # Routing state machine and capacity governor tests (10 tests)
├── test_shift_drift.py     # Covariate shift generation and PSI drift tests (6 tests)
└── test_splits.py          # Time-ordered train/calib/val/test split partition tests (8 tests)
```

## Test Structure

**FastAPI Test Pattern:**
```python
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)

def test_get_health():
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "HEALTHY"
    assert "version" in data
```

**Security & Anti-Leakage Test Pattern:**
```python
import pytest
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)

@pytest.mark.parametrize("forbidden_key", [
    "isFraud", "true_label", "target", "label", "TransactionID", "TransactionDT"
])
def test_sandbox_rejects_leakage_fields(forbidden_key):
    payload = {"features": {forbidden_key: 1, "TransactionAmt": 100.0}}
    response = client.post("/api/score-sandbox", json=payload)
    assert response.status_code == 422
    data = response.json()
    assert data["error"]["code"] == "VALIDATION_ERROR"
    assert "LEAKAGE VIOLATION" in data["error"]["message"]
```

**Deterministic Policy Routing Test Pattern:**
```python
from policy.router import route, Action, ReasonCode

def test_high_risk_routing():
    cfg = {"t_alert": 0.084705, "t_review": 0.071002, "u_threshold": 0.526773, "disagreement_enabled": True}
    action, reason = route(p=0.095, u=0.10, cfg=cfg)
    assert action == Action.FRAUD_ALERT
    assert reason == ReasonCode.R1_HIGH_RISK

def test_fail_closed_on_nan_risk():
    cfg = {"t_alert": 0.084705, "t_review": 0.071002}
    action, reason = route(p=float("nan"), cfg=cfg)
    assert action == Action.MANUAL_REVIEW
    assert reason == ReasonCode.R0_SIGNAL_UNAVAILABLE
```

## Mocking & Fixtures

**What to Mock:**
- Time stamps where strict deterministic ISO representations are asserted.
- External network requests (none exist in standard runtime).

**What NOT to Mock:**
- Model artifact loading: Tests run against real serialized Joblib artifacts (`models/artifacts/*.joblib`) to guarantee real-world deserialization integrity.
- Decision router and capacity governor: Policy logic is executed directly against true production thresholds.
- Pydantic schema validation: Never bypass Pydantic model validation.

## Fixtures & Test Data

**Synthetic Fixture:**
- Ground truth test fixture located at `data/synthetic_smoke_fixture.csv` (10,000 rows).
- Evaluated splits loaded deterministically via `data/splits.py:make_splits()` using fixed seed `42`.

## Coverage & Test Health

**Summary of Automated Test Suites:**
- **Python Backend & ML Suites:** 109 tests passing in ~16 seconds (0 failures, 0 skipped, 0 xfailed).
- **TypeScript Frontend Suites:** 21 tests passing in ~2 seconds (0 failures, 0 skipped).
- **TypeScript Static Verification:** `npx tsc --noEmit` clean with 0 compilation errors.

**Run All Verification:**
```powershell
# 1. Run Python unit & integration tests:
python -m pytest -o "pythonpath=." tests/

# 2. Run TypeScript unit tests:
cd frontend
npm test

# 3. Verify TypeScript types:
npx tsc --noEmit
```

---

*Testing analysis: 2026-10-18*
