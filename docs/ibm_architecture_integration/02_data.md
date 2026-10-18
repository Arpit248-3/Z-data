# SignalGate IBM Architecture Integration — Phase 3: Data Ingestion & Temporal Partitions

**Governing Specification:** `docs/ibm_architecture_integration_master_spec.md` § C, § G  
**Status:** RAW_DATA_VERIFIED_VALIDATION_PASSED  
**Architecture Version:** `ieee_cis_v1`  
**Last Updated:** 2026-10-18 (Post-Ingestion Empirical Validation)  

---

## 1. Executive Summary & Raw Dataset Verification

The authentic IEEE-CIS Fraud Detection dataset files have been downloaded to `data/raw/` and audited. All 5 files were verified against the authoritative reference repository checksums with 100% cryptographic agreement using chunked streaming SHA-256 computation.

### 1.1 Raw Dataset Inventory & Cryptographic Hashes

| File | Actual Size (Bytes) | Expected Size (Bytes) | SHA-256 Checksum | Match Status | Role in Pipeline |
|---|:---:|:---:|---|:---:|---|
| `train_transaction.csv` | 683,351,067 | 683,351,067 | `3a5c83ab6b3cc13dcabe5ffa9f522307fd5f7f7b6e6f6a60c32284ca6283d642` | **MATCH** | Labeled training source (391 features, target, metadata) |
| `train_identity.csv` | 26,529,680 | 26,529,680 | `b63c725d8377be90a995268d97f347c17d456b95db45807adcf9f59cd603c37c` | **MATCH** | Auxiliary identity metadata |
| `test_transaction.csv` | 613,194,934 | 613,194,934 | `2a8e51f1d335a86025d2b7f45beb9b78d0ab1edd726ef531d8b71a8a0065c011` | **MATCH** | Unlabeled competition test transactions |
| `test_identity.csv` | 25,797,161 | 25,797,161 | `3e5978cb13ca5e72f52babc4349ae0125e14b87ca8bfabe952ab67bb4ff1e10b` | **MATCH** | Unlabeled competition identity metadata |
| `sample_submission.csv` | 6,080,314 | 6,080,314 | `50d7e0d6fcfc6e498efc297001f252101512ccdcb34aefbde6db98f8242a3626` | **MATCH** | Competition submission template |

### 1.2 Dataset Properties & Join Cardinality

- **Total Transactions (`train_transaction.csv`):** Exactly **590,540 rows**, 394 columns.
- **Identifier Uniqueness:** `TransactionID` is 100% unique (range: `2,987,000` to `3,577,539`).
- **Timestamp Coverage:** `TransactionDT` spans **182.0 days** (min: `86,400`, max: `15,811,131`). Strictly monotonically sorted.
- **Target Distribution (`isFraud`):**
  - Legitimate (`0`): 569,877 (96.501%)
  - Fraud (`1`): 20,663 (3.499%)
  - Overall Fraud Prevalence: **3.4990%**
- **Identity Join Cardinality (`train_identity.csv`):**
  - Identity rows: 144,233 (41 columns, 100% unique `TransactionID`).
  - Left join: `train_transaction LEFT JOIN train_identity ON TransactionID` produces exactly **590,540 rows** (1:1 cardinality preservation, zero row loss, zero row duplication).
  - Identity coverage: 144,233 transactions (24.42%) have identity records; 446,307 (75.58%) are anonymous.

---

## 2. 391-Feature Schema Conformance & Discrepancy Analysis

The joined raw dataset schema was compared against `CANONICAL_FEATURE_MANIFEST`:

| Check | Expected | Actual Raw | Discrepancy |
|---|:---:|:---:|:---:|
| Total Raw Columns | 394 | 394 | None |
| Quarantined Target | 1 (`isFraud`) | 1 (`isFraud`) | None |
| Quarantined Metadata | 2 (`TransactionID`, `TransactionDT`) | 2 (`TransactionID`, `TransactionDT`) | None |
| Available Features | 391 | 391 | None |
| Categorical Features | 14 | 14 (`ProductCD`, `card4`, `card6`, `P_emaildomain`, `R_emaildomain`, `M1`–`M9`) | 0 missing, 0 extra |
| Numerical Features | 377 | 377 (`TransactionAmt`, `card1`–`card3`, `card5`, `addr1`–`addr2`, `dist1`–`dist2`, `C1`–`C14`, `D1`–`D15`, `V1`–`V339`) | 0 missing, 0 extra |
| Identity Features in Manifest | 0 | 0 | 0 (identity columns are metadata only) |
| Feature Column Ordering | Numerical then Categorical | Matches `np.hstack([num_part, cat_part])` | Canonical order aligned |

**Discrepancy Report:** **ZERO DISCREPANCIES**. The empirical columns match the registered 391-feature specification 100%. No feature names were invented or omitted.

---

## 3. Chronological Splits & Cryptographic Verification

Transactions were chronologically partitioned by `TransactionDT` ascending (with secondary tie-breaking on `TransactionID` ascending) into 4 disjoint intervals using `ChronologicalSplitter`. All 4 split hashes match the reference pre-evaluation freeze record with 100% cryptographic agreement:

| Partition | Share | Row Count | Fraud Count | Prevalence | `TransactionDT` Interval | Split Hash (SHA-256) | Freeze Record Match |
|---|:---:|:---:|:---:|:---:|:---:|---|:---:|
| **Train** | 60% | 354,324 | 11,988 | 3.3833% | `[86,400, 8,745,772]` | `ee8c38fd7e8b2af1b93a7824fd80f59c7811e5ce2ac1651500d51bf6e2e1f53a` | **MATCH** |
| **Calibration** | 10% | 59,054 | 2,550 | 4.3181% | `[8,745,798, 10,437,996]` | `a1880e4f36558c33d77d0a1a2cf6b1dfe607a4983909364afff71ca84401e7bb` | **MATCH** |
| **Validation** | 10% | 59,054 | 2,061 | 3.4900% | `[10,438,003, 12,192,842]` | `f824d80aea2e20f72e4ed8f06e6d119c7572caf50cf304dfb4224e8d990e7170` | **MATCH** |
| **Test** | 20% | 118,108 | 4,064 | 3.4409% | `[12,192,900, 15,811,131]` | `88d73a15fc60f9badfedc4909ede017de45a99f6c58798d54ab9c1dff90690f1` | **MATCH** |
| **Total** | 100% | **590,540** | **20,663** | **3.4990%** | `[86,400, 15,811,131]` | — | — |

### Verification of Temporal Disjointness:
- $\max(\text{Train DT}) = 8,745,772 < 8,745,798 = \min(\text{Calibration DT})$
- $\max(\text{Calibration DT}) = 10,437,996 < 10,438,003 = \min(\text{Validation DT})$
- $\max(\text{Validation DT}) = 12,192,842 < 12,192,900 = \min(\text{Test DT})$
- **Partition Disjointness:** $\text{IDs}_{\text{train}} \cap \text{IDs}_{\text{cal}} \cap \text{IDs}_{\text{val}} \cap \text{IDs}_{\text{test}} = \emptyset$. Zero row or ID overlap.

---

## 4. Memory Governance & Resource Budgeting (8 GB RAM Host)

A bounded-memory approach was used for validation (loading only metadata columns, streaming 1 MB chunks for file hashing), keeping validation peak RAM under **50 MB**.

### Estimated Memory Footprint for Model Training:

| Component | Dimensions / Structure | Memory (`float32`) | Safety Assessment |
|---|---|:---:|---|
| **Train Feature Matrix ($X_{\text{train}}$)** | $354,324 \text{ rows} \times 391 \text{ features} \times 4 \text{ bytes}$ | **528.49 MB** | Safe (fits easily in RAM) |
| **Calibration Matrix ($X_{\text{cal}}$)** | $59,054 \text{ rows} \times 391 \text{ features} \times 4 \text{ bytes}$ | **88.08 MB** | Safe |
| **Validation Matrix ($X_{\text{val}}$)** | $59,054 \text{ rows} \times 391 \text{ features} \times 4 \text{ bytes}$ | **88.08 MB** | Safe |
| **Test Matrix ($X_{\text{test}}$)** | $118,108 \text{ rows} \times 391 \text{ features} \times 4 \text{ bytes}$ | **176.16 MB** | Safe |
| **Single-Model Fit (Baseline B2)** | $X_{\text{train}}$ + internal gradient boosting histogram bins | **~1.72 GB peak** | Safe (>6.0 GB headroom) |
| **Ensemble Fit (5 Era Members)** | Sequential training with explicit `gc.collect()` per member | **~2.65 GB peak** | Safe (>5.0 GB headroom) |

**Conclusion:** Training is computationally and memory-safe for this Windows machine with 8 GB RAM when using `float32` arrays, sequential member training, and aggressive garbage collection between era fits.

---

## 5. Artifact Index & Provenance

All real-data artifacts are maintained strictly in the isolated `results/ieee_cis_v1/` namespace:

| Artifact Path | Description | Status |
|---|---|:---:|
| [`results/ieee_cis_v1/dataset_validation_report.json`](file:///c:/Users/arpit/Desktop/project/results/ieee_cis_v1/dataset_validation_report.json) | Comprehensive raw dataset validation report | **VERIFIED (PASS)** |
| [`results/ieee_cis_v1/split_manifest.json`](file:///c:/Users/arpit/Desktop/project/results/ieee_cis_v1/split_manifest.json) | Chronological 60/10/10/20 partition manifest & hashes | **VERIFIED (PASS)** |
| [`results/ieee_cis_v1/feature_manifest.json`](file:///c:/Users/arpit/Desktop/project/results/ieee_cis_v1/feature_manifest.json) | Validated 391-feature schema specification | **VALIDATED** |
| `integrations/ibm_architecture/data/` | Data loader, splitter, manifest, and validator package | **OPERATIONAL** |
| `data/synthetic_transactions.csv` | Root canonical synthetic dataset | **UNMODIFIED** |
| `results/results.json` | Root canonical synthetic benchmark | **UNMODIFIED** |
| `policy/frozen_policy.json` | Frozen production policy | **UNMODIFIED** |
| `models/` | Active synthetic models | **UNMODIFIED** |

---

## 6. Readiness Decision

- **Empirical Raw Data Validation:** **PASSED** (100% hash, schema, join, and partition match).
- **Ground-Truth Quarantine:** **ENFORCED** (`isFraud`, `TransactionID`, `TransactionDT` quarantined).
- **Backend Test Suite:** **136/136 tests passing** (zero regressions).
- **Frontend Test Suite:** **21/21 tests passing**.
- **Real-Data Training Status:** **UNBLOCKED**. Model training pipeline may proceed under Phase 4.
