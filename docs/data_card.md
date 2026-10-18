# SignalGate Data Card

## 1. Overview & Dataset Identity

| Attribute | Specification | Current Active State |
|:---|:---|:---|
| **Intended Primary Dataset** | IEEE-CIS Fraud Detection (`train_transaction.csv`) | **UNAVAILABLE** (not present on local workstation) |
| **Active Development Dataset** | Deterministic Synthetic Smoke Fixture (`data/synthetic_smoke_fixture.csv`) | **ACTIVE** |
| **Dataset Status Tag** | `SYNTHETIC_SMOKE_ONLY` | Preflight verified |
| **Benchmark Validity** | **STRICTLY PROHIBITED** | Must never be cited as real-world benchmark performance |
| **Declared Random Seed** | `42` | Fully deterministic regeneration |
| **Row Count** | `10,000` | Matched to Phase 1 smoke-fit requirement |
| **Column Count** | `84` | IEEE-CIS schema compatible |
| **SHA-256 Checksum** | `da00179ebf37970ec8907d11cfb366d170ddd5b2b41370e881bf92359b7d17de` | Verified reproducible |
| **Fraud Cases / Prevalence** | `476` / `4.7600%` | Approximating real-world fraud class imbalance |
| **Temporal Span (TransactionDT)** | `86,432` to `388,515` (strictly monotonic) | Non-decreasing timestamps |

---

## 2. Integrity and Usage Rules

> [!CAUTION]
> **SYNTHETIC SMOKE FIXTURE INTEGRITY NOTICE**
> The current active dataset is a deterministic synthetic development fixture. It is generated solely to support code implementation, schema validation, scikit-learn pipeline integration, policy routing logic, and UI development.
>
> 1. All results, tables, and dashboard statuses derived from this fixture must be stamped `SYNTHETIC_SMOKE_ONLY`.
> 2. Synthetic evaluation metrics must never be represented or claimed as real benchmark performance.
> 3. True labels (`isFraud`, `true_label`) must never be supplied to the feature matrix, inference router, or live scoring endpoints.
> 4. `TransactionID` and raw `TransactionDT` are strictly forbidden from entering the model feature matrix.

---

## 3. Schema Specification

The active fixture adheres strictly to the column naming, types, and semantics of IEEE-CIS `train_transaction.csv`:

### Identifiers & Target (Forbidden from Model Features)
- `TransactionID` (int64): Unique sequential transaction identifier (`2987000` to `2996999`).
- `isFraud` (int64): Binary fraud ground-truth label in `{0, 1}`. Excluded from inference feature matrix.
- `TransactionDT` (int64): Monotonically non-decreasing integer seconds from reference start. Used strictly for chronological partitioning; excluded from model features.

### Transaction Attributes
- `TransactionAmt` (float64): Transaction amount in USD ($1.00 to $5,000.00, lognormal distribution).
- `ProductCD` (categorical object): Product code (`W`, `C`, `R`, `H`, `S`).
- `card1` (int64): Payment card identifier.
- `card2` (float64): Card issuing bank identifier (with realistic missingness).
- `card3` (float64): Card country / network code.
- `card4` (categorical object): Card issuer (`visa`, `mastercard`, `discover`, `american express`).
- `card5` (float64): Card category code.
- `card6` (categorical object): Card type (`debit`, `credit`).
- `addr1` (float64): Billing region code.
- `addr2` (float64): Billing country code.
- `dist1` (float64): Distance proxy metric (with ~60% missingness).
- `P_emaildomain` (categorical object): Purchaser email domain (`gmail.com`, `yahoo.com`, `hotmail.com`, `anonymous.com`, `aol.com`).
- `R_emaildomain` (categorical object): Recipient email domain (with ~60% missingness).

### Engineered & Masked Features
- `C1` - `C14` (float64): Transaction counting features.
- `D1` - `D15` (float64): Timedelta features representing recency with realistic NaN rates.
- `M1` - `M9` (categorical object): Verification matches (`T`, `F`, or `missing`).
- `V1` - `V30` (float64): Vesta engineered behavioral signals (normalized numeric float values).

---

## 4. Chronological Split Strategy (Planned for Phase 2)

Per SignalGate Blueprint Section 5.3:

| Partition | Time Allocation | Purpose |
|:---|:---|:---|
| **Train** | `0% - 60%` | Fit base estimator, preprocessors, and train-derived statistics |
| **Calibration** | `60% - 70%` | Fit probability calibration (`FrozenEstimator` + `CalibratedClassifierCV`) |
| **Validation** | `70% - 80%` | Threshold tuning, budget matching, keep/drop decisions |
| **Test** | `80% - 100%` | Frozen final evaluation at declared test looks only |

---

## 5. Transition to Real IEEE-CIS Dataset

When authorized and supplied:
1. Place the genuine `train_transaction.csv` into `data/train_transaction.csv`.
2. Re-run `python scripts/preflight.py`.
3. The preflight script automatically detects the genuine IEEE-CIS dataset, verifies its SHA-256 and schema, updates `logs/environment.txt`, and lifts the `SYNTHETIC_SMOKE_ONLY` constraint for benchmark claims.
4. No API keys or Kaggle credentials are hardcoded into source control.
