"""
SignalGate Synthetic Development Fixture Generator
Generates a deterministic 10,000-row synthetic fixture adhering to the IEEE-CIS schema.
Used strictly for code, integration, routing, and UI development.
Status: SYNTHETIC_SMOKE_ONLY
"""

import hashlib
import json
import os
import sys
from pathlib import Path
import numpy as np
import pandas as pd

# Add parent directory to path to allow importing data.schema
current_dir = Path(__file__).resolve().parent
parent_dir = current_dir.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

from data.schema import (
    TARGET_COLUMN,
    ID_COLUMN,
    TIME_COLUMN,
    ALL_SMOKE_COLUMNS,
    validate_schema,
)

FIXTURE_STATUS = "SYNTHETIC_SMOKE_ONLY"


def generate_synthetic_fixture(
    n_rows: int = 10000,
    seed: int = 42,
    output_path: str = None,
) -> pd.DataFrame:
    """
    Generate a deterministic synthetic dataset of n_rows with IEEE-CIS transaction schema.
    """
    rng = np.random.RandomState(seed)

    # 1. TransactionID & strictly non-decreasing TransactionDT
    start_id = 2987000
    transaction_ids = np.arange(start_id, start_id + n_rows, dtype=np.int64)

    # Monotonically increasing time in seconds (average ~30 seconds between transactions)
    time_deltas = rng.exponential(scale=30.0, size=n_rows).astype(np.int64) + 1
    transaction_dt = 86400 + np.cumsum(time_deltas)

    # 2. Base Transaction Attributes
    # TransactionAmt: lognormal distribution with typical card spend ($5 - $1000)
    transaction_amt = np.round(rng.lognormal(mean=4.2, sigma=1.1, size=n_rows), 2)
    transaction_amt = np.clip(transaction_amt, 1.0, 5000.0)

    # ProductCD: categorical distribution
    product_codes = ["W", "C", "R", "H", "S"]
    product_probs = [0.74, 0.12, 0.07, 0.05, 0.02]
    product_cd = rng.choice(product_codes, size=n_rows, p=product_probs)

    # Card attributes
    card1 = rng.randint(1000, 20000, size=n_rows)
    card2 = rng.choice(
        [np.nan, 111.0, 174.0, 264.0, 321.0, 360.0, 404.0, 490.0, 555.0, 583.0],
        size=n_rows,
        p=[0.15, 0.05, 0.08, 0.12, 0.15, 0.10, 0.12, 0.08, 0.08, 0.07],
    )
    card3 = rng.choice([150.0, 185.0, np.nan], size=n_rows, p=[0.88, 0.09, 0.03])
    card4_choices = ["visa", "mastercard", "discover", "american express", "missing"]
    card4 = rng.choice(card4_choices, size=n_rows, p=[0.65, 0.28, 0.04, 0.02, 0.01])
    card5 = rng.choice([226.0, 166.0, 117.0, 102.0, np.nan], size=n_rows, p=[0.55, 0.25, 0.10, 0.07, 0.03])
    card6_choices = ["debit", "credit", "charge card", "missing"]
    card6 = rng.choice(card6_choices, size=n_rows, p=[0.75, 0.23, 0.01, 0.01])

    # Address & distance
    addr1 = rng.choice([299.0, 325.0, 494.0, 204.0, 315.0, np.nan], size=n_rows, p=[0.25, 0.20, 0.18, 0.15, 0.12, 0.10])
    addr2 = rng.choice([87.0, 60.0, np.nan], size=n_rows, p=[0.90, 0.02, 0.08])
    dist1 = rng.choice([np.nan, 0.0, 1.0, 5.0, 12.0, 35.0, 120.0], size=n_rows, p=[0.60, 0.10, 0.08, 0.08, 0.06, 0.05, 0.03])

    # Email domains
    email_choices = ["gmail.com", "yahoo.com", "hotmail.com", "anonymous.com", "aol.com", "missing"]
    p_email = rng.choice(email_choices, size=n_rows, p=[0.40, 0.20, 0.12, 0.10, 0.05, 0.13])
    r_email = rng.choice(email_choices, size=n_rows, p=[0.15, 0.10, 0.08, 0.05, 0.02, 0.60])

    # C features (counts: 1 to 14)
    c_features = {}
    for i in range(1, 15):
        c_features[f"C{i}"] = rng.poisson(lam=1.5, size=n_rows).astype(float)

    # D features (timedeltas: 1 to 15 with missingness)
    d_features = {}
    for i in range(1, 16):
        vals = rng.exponential(scale=50.0, size=n_rows)
        # introduce realistic ~20-40% missingness
        mask_nan = rng.rand(n_rows) < 0.25
        vals[mask_nan] = np.nan
        d_features[f"D{i}"] = vals

    # M features (matches: M1 to M9)
    m_features = {}
    for i in range(1, 10):
        m_features[f"M{i}"] = rng.choice(["T", "F", "missing"], size=n_rows, p=[0.55, 0.35, 0.10])

    # V features (V1 to V30 standard normalized signals)
    v_features = {}
    for i in range(1, 31):
        v_features[f"V{i}"] = np.round(rng.normal(loc=0.0, scale=1.0, size=n_rows), 4)

    # 3. Deterministic Fraud Target Generation
    # Fraud log-odds model matching ~3.5% prevalence with realistic domain correlations
    # (High amount, Product C/R, specific counts, high V signals)
    log_odds = -3.85  # baseline gives ~2.1% base
    log_odds += 0.28 * np.log1p(transaction_amt) / 4.0
    log_odds += np.where(product_cd == "C", 0.95, 0.0)
    log_odds += np.where(product_cd == "R", 0.45, 0.0)
    log_odds += np.where(card4 == "discover", 0.35, 0.0)
    log_odds += np.where(p_email == "anonymous.com", 0.60, 0.0)
    log_odds += 0.12 * np.clip(c_features["C1"], 0, 10)
    log_odds += 0.15 * v_features["V1"]
    log_odds += 0.18 * v_features["V5"]
    log_odds -= 0.10 * v_features["V12"]

    # Probability via sigmoid
    prob_fraud = 1.0 / (1.0 + np.exp(-log_odds))
    # Sample binary labels deterministically
    is_fraud = (rng.rand(n_rows) < prob_fraud).astype(int)

    # Build DataFrame
    data_dict = {
        ID_COLUMN: transaction_ids,
        TARGET_COLUMN: is_fraud,
        TIME_COLUMN: transaction_dt,
        "TransactionAmt": transaction_amt,
        "ProductCD": product_cd,
        "card1": card1,
        "card2": card2,
        "card3": card3,
        "card4": card4,
        "card5": card5,
        "card6": card6,
        "addr1": addr1,
        "addr2": addr2,
        "dist1": dist1,
        "P_emaildomain": p_email,
        "R_emaildomain": r_email,
    }
    data_dict.update(c_features)
    data_dict.update(d_features)
    data_dict.update(m_features)
    data_dict.update(v_features)

    df = pd.DataFrame(data_dict)

    # Ensure all columns in ALL_SMOKE_COLUMNS are present in clean order
    ordered_cols = [c for c in ALL_SMOKE_COLUMNS if c in df.columns]
    df = df[ordered_cols]

    if output_path:
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        df.to_csv(output_path, index=False)

    return df


def compute_file_sha256(filepath: str) -> str:
    """Compute SHA-256 hash of a file."""
    hasher = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()


def generate_and_save_fixture(
    n_rows: int = 10000,
    seed: int = 42,
    output_dir: str = "data",
) -> dict:
    """
    Generate fixture, save CSV, validate schema, and save metadata JSON.
    """
    os.makedirs(output_dir, exist_ok=True)
    csv_path = os.path.join(output_dir, "synthetic_smoke_fixture.csv")
    meta_path = os.path.join(output_dir, "synthetic_smoke_fixture_meta.json")

    df = generate_synthetic_fixture(n_rows=n_rows, seed=seed, output_path=csv_path)
    is_valid, errors = validate_schema(df, is_synthetic=True)
    if not is_valid:
        raise ValueError(f"Generated fixture failed schema validation: {errors}")

    file_hash = compute_file_sha256(csv_path)
    fraud_count = int(df[TARGET_COLUMN].sum())
    prevalence = float(fraud_count / len(df))

    metadata = {
        "status": FIXTURE_STATUS,
        "is_synthetic": True,
        "generator_script": "data/generate_fixture.py",
        "rows": len(df),
        "columns": len(df.columns),
        "target_column": TARGET_COLUMN,
        "id_column": ID_COLUMN,
        "time_column": TIME_COLUMN,
        "fraud_count": fraud_count,
        "fraud_prevalence": round(prevalence, 6),
        "time_min": int(df[TIME_COLUMN].min()),
        "time_max": int(df[TIME_COLUMN].max()),
        "seed": seed,
        "sha256": file_hash,
        "notice": (
            "This dataset is a deterministic synthetic smoke fixture for development, "
            "routing, API, and UI integration only. Metrics evaluated on this fixture "
            "must never be presented as benchmark performance."
        ),
    }

    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)

    return metadata


if __name__ == "__main__":
    meta = generate_and_save_fixture()
    print(f"Generated synthetic fixture: {meta['rows']} rows, {meta['columns']} cols, SHA-256: {meta['sha256']}")
    print(f"Fraud count: {meta['fraud_count']} ({meta['fraud_prevalence']*100:.2f}%)")
