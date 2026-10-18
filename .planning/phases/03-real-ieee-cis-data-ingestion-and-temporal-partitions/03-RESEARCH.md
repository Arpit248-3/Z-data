# Phase 3: Real IEEE-CIS Data Ingestion and Temporal Partitions — Research & Technical Specifications

**Phase:** `03-real-ieee-cis-data-ingestion-and-temporal-partitions`  
**Date:** 2026-10-18  
**Governing Specification:** `docs/ibm_architecture_integration_master_spec.md` § C, § G  
**Requirements Covered:** `DATA-01`, `DATA-02`, `DATA-03`  

---

## 1. Architectural Objectives & Invariants

The objective of Phase 3 is to establish the reproducible data ingestion, feature manifest validation, and chronological partition architecture for the real IEEE-CIS Fraud Detection dataset within the isolated integration namespace.

In strict compliance with the governing specification:
1. **Isolated Namespace (`DATA-01`):** All data loaders, splitters, manifests, and validation utilities must reside within `integrations/ibm_architecture/data/`. All output reports and manifests must be saved under the versioned real-data namespace `results/ieee_cis_v1/`, leaving the root canonical synthetic files (`results/split_report.json`, `results/results.json`, `data/synthetic_smoke_fixture.csv`) completely untouched.
2. **Ground-Truth Quarantine (`DATA-02`, Master Spec § C2):**
   - The evaluation target `isFraud` must never be present in the model feature matrix, feature manifests, calibration requests, or online scoring vectors.
   - Raw transaction identifiers (`TransactionID`) and timestamps (`TransactionDT`) must be excluded from feature transformations, remaining strictly operational metadata for chronological sorting and join keying.
3. **Chronological Splitting Protocol (`DATA-03`, Master Spec § G):**
   - Temporal partition ratios: **60% Train**, **10% Calibration**, **10% Validation**, **20% Test** (`60/10/10/20`).
   - Sorting order: Primary sort ascending on `TransactionDT`. In case of timestamp ties, deterministic secondary tie-breaking on `TransactionID` ascending.
   - Cryptographic partitioning fingerprint: Each partition's ID sequence is hashed via SHA-256 (`compute_partition_hash`).
4. **Honest Fail-Closed Handling for Missing Raw Data (Master Spec § C1, § G):**
   - As proven in Phase 1 and Phase 2, `data/raw/` does not currently exist locally (`train_transaction.csv` and `train_identity.csv` are absent).
   - Under no circumstances will synthetic rows be relabeled, copied into `data/raw/`, or substituted for real IEEE-CIS data.
   - The data loader and validation suite must fail closed with explicit diagnostic feedback when real data is requested, while providing reproducible loading logic that operates seamlessly once raw files are supplied.

---

## 2. Analysis of the IEEE-CIS Dataset Structure

The IEEE-CIS Fraud Detection benchmark comprises two primary tables linked by `TransactionID`:

### 2.1 `train_transaction.csv`
- Total rows: 590,540 transactions.
- Key columns:
  - `TransactionID`: Monotonically increasing unique integer identifier (range: 2,987,000 to 3,577,539).
  - `isFraud`: Binary fraud label (3.499% overall prevalence; 20,663 positive fraud transactions). **QUARANTINED**.
  - `TransactionDT`: Integer timedelta in seconds from a reference point (range: 86,400 to 15,811,131; span: 182 days / ~6 months).
  - Numerical features: `TransactionAmt`, `card1`–`card3`, `card5`, `addr1`–`addr2`, `dist1`–`dist2`, `C1`–`C14`, `D1`–`D15`, `V1`–`V339`.
  - Categorical features: `ProductCD`, `card4`, `card6`, `P_emaildomain`, `R_emaildomain`, `M1`–`M9`.

### 2.2 `train_identity.csv`
- Total rows: 144,233 rows (only ~24.4% of transactions have associated identity records).
- Cardinality: Exactly 1:0 or 1:1 with `train_transaction.csv`.
- Features: `id_01`–`id_38`, `DeviceType`, `DeviceInfo`.
- Join protocol: `pd.merge(df_tx, df_id, on="TransactionID", how="left")`.

### 2.3 The 391-Feature Manifest
From `reference/architecture/IBM-main/results/feature_manifest.json`:
- **Categorical columns (14):** `ProductCD`, `card4`, `card6`, `P_emaildomain`, `R_emaildomain`, `M1`, `M2`, `M3`, `M4`, `M5`, `M6`, `M7`, `M8`, `M9`.
- **Numerical columns (377):** `TransactionAmt`, `card1`, `card2`, `card3`, `card5`, `addr1`, `addr2`, `dist1`, `dist2`, `C1`–`C14`, `D1`–`D15`, `V1`–`V339`.
- **Quarantined columns (3):** `isFraud` (target), `TransactionID` (key), `TransactionDT` (time).
- Total input features to ML estimator: **391 features**.

---

## 3. Package Architecture for Data Ingestion

Under `integrations/ibm_architecture/data/`:
```
integrations/ibm_architecture/data/
├── __init__.py           # Public exports (load_ieee_cis, ChronologicalSplitter, FeatureManifest)
├── manifest.py           # FeatureManifest definition, column ordering, leakage validator
├── loader.py             # Memory-conscious IEEE-CIS loader, joiner, quarantine enforcement
├── splitter.py           # ChronologicalSplitter, partition metadata, SHA-256 partition hashing
└── validator.py          # validate_dataset_files, checksum audit, diagnostics
```

### 3.1 Submodule Specifications

#### `integrations/ibm_architecture/data/manifest.py`
- `FeatureManifest(BaseModel)`:
  - `target_column: str = "isFraud"`
  - `excluded_columns: List[str] = ["TransactionDT", "TransactionID", "isFraud"]`
  - `categorical_columns: List[str]` (14 columns)
  - `numerical_columns: List[str]` (377 columns)
  - Method `feature_names() -> List[str]`: Returns exact 391-column ordered list.
  - Method `validate_dataframe(df: pd.DataFrame, allow_target: bool = False) -> None`: Validates column presence and asserts no quarantined columns exist in the feature set.
  - Method `extract_features(df: pd.DataFrame) -> pd.DataFrame`: Returns `df[manifest.feature_names()]` with strict column order.

#### `integrations/ibm_architecture/data/loader.py`
- `load_ieee_cis(data_dir: Optional[Path] = None, nrows: Optional[int] = None, include_target: bool = False) -> Tuple[pd.DataFrame, Optional[pd.Series]]`:
  - Fails closed with `ArtifactNotFoundError` if raw CSVs are missing from `data/raw/`.
  - Reads `train_transaction.csv` and `train_identity.csv` with optimized dtypes (e.g., categorical as string/category, float32 where appropriate).
  - Merges left on `TransactionID`; validates row count unchanged after join.
  - If `include_target=False` (default for inference/serving), completely strips `isFraud`.
  - If `include_target=True` (permitted strictly for offline train/evaluation splitting), returns target series separately quarantined from the feature DataFrame.
  - Preserves `TransactionID` and `TransactionDT` only for sorting and indexing, never included in feature matrix.

#### `integrations/ibm_architecture/data/splitter.py`
- `ChronologicalSplitter`:
  - Default ratios:
    - Train: `(0.0, 0.60)` -> 60%
    - Calibration: `(0.60, 0.70)` -> 10%
    - Validation: `(0.70, 0.80)` -> 10%
    - Test: `(0.80, 1.00)` -> 20%
  - Method `split(df: pd.DataFrame, sort: bool = True) -> Dict[str, pd.DataFrame]`:
    - Enforces sorting on `TransactionDT` ascending, tie-breaking on `TransactionID` ascending.
    - Slices partitions cleanly without row overlap or boundary duplication.
  - Method `compute_partition_hash(ids: pd.Series | np.ndarray) -> str`:
    - Deterministic ASCII-encoded comma-separated ID hash.
  - Method `generate_split_manifest(partitions: Dict[str, pd.DataFrame]) -> Dict[str, Any]`:
    - Produces partition counts, timestamp ranges, fraud prevalence, and split hashes matching reference format.

#### `integrations/ibm_architecture/data/validator.py`
- `validate_dataset_directory(data_dir: Path, output_dir: Optional[Path] = None) -> Dict[str, Any]`:
  - Inspects file presence and hashes.
  - Writes report to `results/ieee_cis_v1/dataset_validation_report.json`.

---

## 4. Test Strategy (`tests/test_ibm_data.py`)

A comprehensive unit test suite will test:
1. **Manifest Validation:**
   - Exact 391 feature count (14 categorical, 377 numerical).
   - Rejection of quarantined columns (`isFraud`, `TransactionID`, `TransactionDT`) in feature matrix extraction.
2. **Chronological Splitting Logic:**
   - Verification of 60/10/10/20 proportions on synthetic IEEE-CIS formatted mock DataFrames.
   - Strict temporal monotonicity across partition boundaries ($dt_{\text{train}} \le dt_{\text{calib}} \le dt_{\text{val}} \le dt_{\text{test}}$).
   - Deterministic tie-breaking on `TransactionID` when timestamps are identical.
   - Complete partition disjointness (zero shared IDs across splits).
3. **Partition Hashing:**
   - Deterministic SHA-256 partition fingerprint computation.
4. **Identity Join Cardinality:**
   - Verifies 1:1 transaction-to-row relationship after left-joining identity table.
5. **Fail-Closed Loading:**
   - Loader raises `ArtifactNotFoundError` with explicit instructions when `data/raw/` CSV files are absent.
6. **Zero Regression:**
   - All 123 existing backend tests and 21 frontend tests continue to pass 100%.

---

## 5. Deliverable Requirements (`02_data.md`)

`docs/ibm_architecture_integration/02_data.md` will document:
- IEEE-CIS ingestion architecture and quarantine barriers.
- The 391-feature manifest specifications and column ordering.
- Chronological splitting parameters, partition boundaries, and cryptographic hashing.
- Raw dataset availability audit and fail-closed state report.
- Manifest artifacts published under `results/ieee_cis_v1/`.
- Test execution outputs and quality gate compliance (`DATA-01`, `DATA-02`, `DATA-03`).
