# Coding Conventions

**Analysis Date:** 2026-10-18

## Naming Patterns

**Files & Directories:**
- Python modules: `snake_case.py` (e.g. `backend/app/routers/scoring.py`, `policy/router.py`, `models/calibrate.py`).
- React components: `PascalCase.tsx` (e.g. `frontend/src/features/overview/OverviewPage.tsx`, `frontend/src/components/MetricCard.tsx`).
- React hooks: `camelCase.ts` prefixed with `use` (e.g. `useOverviewMetrics`, `useScoreSandbox` in `frontend/src/lib/api/hooks.ts`).
- Style sheets: `kebab-case.css` (e.g. `tokens.css`, `layout.css`, `components.css`).
- Test files:
  - Python: `test_<module>.py` in `tests/` directory (e.g. `test_router.py`, `test_api_security.py`).
  - Frontend: `<name>.test.ts` in `src/components/__tests__/` (e.g. `phase10_quality.test.ts`).

**Functions & Methods:**
- Python: `snake_case()` (e.g. `score_sandbox_transaction()`, `get_readiness_status()`, `validate_router_config()`).
- TypeScript: `camelCase()` (e.g. `fetchOverviewMetrics()`, `handlePresetSelect()`).

**Variables & Attributes:**
- Python: `snake_case` (e.g. `target_budget`, `admitted_reviews`, `frozen_config_hash`).
- TypeScript: `camelCase` (e.g. `selectedBudget`, `isStreaming`, `activeScenario`).
- Constants & Enums: `UPPER_SNAKE_CASE` (e.g. `FORBIDDEN_SCORING_FIELDS`, `Action.FRAUD_ALERT`, `ReasonCode.R6_CAPACITY_DEFERRED`).

**Types, Classes & Interfaces:**
- Python: `PascalCase` (e.g. `ArtifactService`, `CapacityGovernor`, `SandboxScoreRequest`, `OverviewResponse`).
- TypeScript: `PascalCase` (e.g. `OverviewMetrics`, `PolicyComparisonItem`, `SandboxScorePayload`).

## Code Style

**Python Formatting & Typing:**
- Adheres to PEP 8 with 4-space indentation.
- Strict type annotations on all public functions, methods, and FastAPI routes (`Optional[T]`, `Dict[str, Any]`, `Tuple[...]`).
- Type safety enforced via Pydantic v2 `BaseModel` and `@field_validator`.

**TypeScript & Frontend Styling:**
- Strict TypeScript compilation (`"strict": true` in `tsconfig.json`).
- Zero Tailwind / CSS-in-JS: Exclusively styled with Vanilla CSS using CSS Custom Properties defined in `frontend/src/styles/tokens.css`.
- Design System tokens govern all surfaces, text colors, and borders:
  ```css
  var(--bg-canvas)            /* #0A0F14 */
  var(--bg-surface-primary)   /* #111922 */
  var(--bg-surface-raised)    /* #18232D */
  var(--border-default)       /* #293743 */
  var(--text-primary)         /* #E0E6ED */
  var(--text-muted)           /* #7A8C9E */
  ```
- Geometry: Maximum 4px corner radius (`0.25rem`) for cards and panels; zero ambient drop shadows or blurred button glows.

## Import Organization

**Python Module Imports:**
Strict 3-block structure separated by single blank lines:
1. Standard Library (`os`, `json`, `math`, `datetime`, `pathlib`, `typing`).
2. Third-Party Packages (`fastapi`, `pydantic`, `numpy`, `pandas`, `sklearn`, `joblib`).
3. Internal Project Packages (`backend.app.*`, `models.*`, `policy.*`, `eval.*`, `data.*`).

```python
# Example from backend/app/routers/scoring.py
from fastapi import APIRouter, Depends, HTTPException, status

from backend.app.dependencies import get_scoring_service
from backend.app.schemas import ErrorResponse, SandboxScoreRequest, SandboxScoreResponse
from backend.app.services.scoring import ScoringService
```

**TypeScript Module Imports:**
1. React & Core Libraries (`react`, `react-router-dom`).
2. Third-Party Libraries (`lucide-react`, `recharts`, `three`, `@react-three/fiber`).
3. Internal Components, Contexts & Hooks (`../../components/*`, `../../context/*`, `../../lib/api/*`).
4. Stylesheets (`../../styles/*.css`).

## Error Handling

**FastAPI Error Envelope:**
All HTTP exceptions and validation errors return an immutable, structured JSON schema:
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Human-readable explanation",
    "details": {}
  }
}
```

**Fail-Closed Policy Pattern:**
In `policy/router.py`, any invalid configuration or missing/non-finite feature input automatically triggers `MANUAL_REVIEW` / `R0_SIGNAL_UNAVAILABLE`:
```python
if p is None or not isinstance(p, (int, float)) or not np.isfinite(p):
    return Action.MANUAL_REVIEW, ReasonCode.R0_SIGNAL_UNAVAILABLE
```

**Target Leakage Guardrail:**
Input payloads to the Scoring Sandbox are inspected recursively; any key matching forbidden target columns or database IDs immediately aborts execution:
```python
# backend/app/schemas.py
FORBIDDEN_SCORING_FIELDS = {
    "true_label", "isfraud", "target", "label", "y_true",
    "ground_truth", "transactionid", "transactiondt", "id"
}
```

## Logging

**Audit Logging:**
- Production decisions in the Sandbox are appended synchronously to `logs/audit.jsonl` using JSON Lines format.
- Every log entry includes: `decision_id`, `timestamp` (UTC ISO), `latency_ms`, `signals` ($p, u_2$), `decision` (action, reason), `governor` state, and `inputs_sanitized`.

**Operational Logs:**
- Standard Python `logging` module configured for warning/error level outputs.

## Comments & Documentation

**Docstrings:**
- Python modules and classes carry multi-line docstrings detailing responsibilities, invariants, and mathematical guarantees.
- Functions specify purpose, arguments, and return types.

**Design Integrity Annotations:**
- Frontend components cite authoritative design rules from `DESIGN.md` (e.g. matched review budget $B=130$, review threshold $t_{\text{review}} = 0.0710$, zero live streaming claims).

## Function & Module Design

- Pure Functions: Core mathematical calculations (`eval/bootstrap.py`, `eval/metrics.py`, `policy/router.py`) are pure functions with no side effects.
- Stateless Service Handlers: FastAPI route controllers delegate business logic to injectable service classes (`ArtifactService`, `ScoringService`) instantiated via FastAPI's `Depends` system.
- Zero Hardcoded Secrets: Code is strictly public-safe with zero API keys or live credentials.

---

*Convention analysis: 2026-10-18*
