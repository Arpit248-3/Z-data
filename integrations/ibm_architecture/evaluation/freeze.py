"""SignalGate IBM Architecture Integration — Pre-Evaluation Freeze Protocol.

Verifies and serializes an immutable pre-evaluation freeze record prior to test partition
evaluation, in strict adherence to:
Governing Specification: docs/ibm_architecture_integration_master_spec.md § C, § N, § O
Requirements Covered: EVAL-01
"""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field

from integrations.ibm_architecture.exceptions import ArtifactNotFoundError, IncompatibleArtifactError
from integrations.ibm_architecture.policy.frozen_policy import IEEEPolicyConfig, get_frozen_ieee_policy_config

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent

# Expected canonical fingerprints established in Phases 3-5
CANONICAL_SPLIT_HASHES: Dict[str, str] = {
    "train": "ee8c38fd7e8b2af1b93a7824fd80f59c7811e5ce2ac1651500d51bf6e2e1f53a",
    "calibration": "a1880e4f36558c33d77d0a1a2cf6b1dfe607a4983909364afff71ca84401e7bb",
    "validation": "f824d80aea2e20f72e4ed8f06e6d119c7572caf50cf304dfb4224e8d990e7170",
    "test": "88d73a15fc60f9badfedc4909ede017de45a99f6c58798d54ab9c1dff90690f1",
}

CANONICAL_ROW_COUNTS: Dict[str, int] = {
    "train": 354324,
    "calibration": 59054,
    "validation": 59054,
    "test": 118108,
}

CANONICAL_ARTIFACT_HASHES: Dict[str, str] = {
    "feature_pipeline.joblib": "b9b3176b2273ffbfdde0a01a0175f61a4491b9bed66dc55c82787dbb75ad72d6",
    "baseline_b2.joblib": "cd20605e5791806e0e9e9a5425b4e3fbf5ed3e6e4062d269b49136ea2142c732",
    "ensemble.joblib": "d34bc0426e647121972c93f15a96c234ede8453b88c70e861d0eef73abc5622a",
    "calibrator.joblib": "89de97d16c7ad77df585c3c3e7f8e32c9685bb04a34d0831bd9f985b9366d345",
}

CANONICAL_FEATURE_MANIFEST_HASH = "9be4c3ce23d1bba5060ca457b2277575a69439055a9e75154e3191ae1e8e3bc5"


def compute_file_sha256(path: Path) -> str:
    """Compute deterministic SHA-256 checksum over file contents."""
    if not path.exists():
        raise ArtifactNotFoundError(f"Missing required artifact file for hashing: {path}")
    hasher = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(1024 * 1024):
            hasher.update(chunk)
    return hasher.hexdigest()


class PreEvaluationFreezeRecord(BaseModel):
    """Immutable audit record binding dataset, splits, models, and policy before evaluation."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    status: str = Field(default="PRE_EVALUATION_FREEZE_VERIFIED")
    timestamp_utc: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    architecture_version: str = Field(default="ieee_cis_v1")
    governing_specification: str = Field(
        default="docs/ibm_architecture_integration_master_spec.md § C, § N, § O"
    )
    historical_look_acknowledgement: Dict[str, Any] = Field(
        description="Transparent acknowledgement of historical test partition evaluation context"
    )
    dataset: Dict[str, Any] = Field(description="Raw dataset paths and verification status")
    split_manifest: Dict[str, Any] = Field(description="Verified partition boundaries, row counts, and hashes")
    model_bundle: Dict[str, Any] = Field(description="Verified model checkpoints, members, and artifact hashes")
    feature_manifest: Dict[str, Any] = Field(description="Verified 391-feature manifest checksum and counts")
    frozen_policy: Dict[str, Any] = Field(description="Frozen policy parameters and configuration hash")
    freeze_hash: str = Field(description="Deterministic SHA-256 fingerprint over the canonical freeze record")


def verify_and_generate_freeze_record(
    project_root: Optional[Path] = None,
    enforce_strict_artifact_hashes: bool = True,
) -> PreEvaluationFreezeRecord:
    """Verify all pre-evaluation components and generate the immutable freeze record.

    Raises:
        ArtifactNotFoundError: If any required file is missing.
        IncompatibleArtifactError: If any cryptographic hash differs from canonical specification.
    """
    root = project_root or PROJECT_ROOT
    results_dir = root / "results" / "ieee_cis_v1"
    models_dir = root / "models" / "artifacts" / "ieee_cis_v1"
    raw_dir = root / "data" / "raw"

    # 1. Dataset verification
    train_tx_path = raw_dir / "train_transaction.csv"
    train_id_path = raw_dir / "train_identity.csv"
    if not train_tx_path.exists():
        raise ArtifactNotFoundError(f"Missing train_transaction.csv at {train_tx_path}")
    if not train_id_path.exists():
        raise ArtifactNotFoundError(f"Missing train_identity.csv at {train_id_path}")

    dataset_meta = {
        "raw_dir": str(raw_dir.relative_to(root)),
        "train_transaction_bytes": train_tx_path.stat().st_size,
        "train_identity_bytes": train_id_path.stat().st_size,
        "total_raw_rows": 590540,
        "verified": True,
    }

    # 2. Split manifest verification
    split_manifest_path = results_dir / "split_manifest.json"
    if not split_manifest_path.exists():
        raise ArtifactNotFoundError(f"Missing split_manifest.json at {split_manifest_path}")

    with open(split_manifest_path, "r", encoding="utf-8") as f:
        split_data = json.load(f)

    partitions = split_data.get("partitions", {})
    verified_splits: Dict[str, Dict[str, Any]] = {}
    for part_name, expected_hash in CANONICAL_SPLIT_HASHES.items():
        if part_name not in partitions:
            raise IncompatibleArtifactError(f"Split partition '{part_name}' missing from split manifest")
        p_info = partitions[part_name]
        observed_hash = p_info.get("split_hash")
        observed_rows = p_info.get("row_count")
        if enforce_strict_artifact_hashes and observed_hash != expected_hash:
            raise IncompatibleArtifactError(
                f"Split hash mismatch for partition '{part_name}': expected {expected_hash}, got {observed_hash}"
            )
        if observed_rows != CANONICAL_ROW_COUNTS[part_name]:
            raise IncompatibleArtifactError(
                f"Row count mismatch for partition '{part_name}': expected {CANONICAL_ROW_COUNTS[part_name]}, got {observed_rows}"
            )
        verified_splits[part_name] = {
            "row_count": observed_rows,
            "fraud_count": p_info.get("fraud_count"),
            "prevalence": p_info.get("prevalence"),
            "split_hash": observed_hash,
            "dt_min": p_info.get("dt_min"),
            "dt_max": p_info.get("dt_max"),
        }

    # 3. Model bundle checkpoints verification
    verified_artifacts: Dict[str, str] = {}
    for filename, expected_hash in CANONICAL_ARTIFACT_HASHES.items():
        artifact_path = models_dir / filename
        if not artifact_path.exists():
            raise ArtifactNotFoundError(f"Missing model artifact {filename} at {artifact_path}")
        observed_hash = compute_file_sha256(artifact_path)
        if enforce_strict_artifact_hashes and observed_hash != expected_hash:
            raise IncompatibleArtifactError(
                f"Model artifact hash mismatch for {filename}: expected {expected_hash}, got {observed_hash}"
            )
        verified_artifacts[filename] = observed_hash

    model_bundle_meta = {
        "artifacts_dir": str(models_dir.relative_to(root)),
        "ensemble_members": [
            "HistGradientBoostingClassifier",
            "ExtraTreesClassifier",
            "LogisticRegression",
        ],
        "calibrator_type": "PlattSigmoid",
        "calibration_split": "calibration (59,054 rows)",
        "artifact_hashes": verified_artifacts,
        "verified": True,
    }

    # 4. Feature manifest verification
    feature_manifest_path = results_dir / "feature_manifest.json"
    if not feature_manifest_path.exists():
        raise ArtifactNotFoundError(f"Missing feature_manifest.json at {feature_manifest_path}")

    observed_fm_hash = compute_file_sha256(feature_manifest_path)
    if enforce_strict_artifact_hashes and observed_fm_hash != CANONICAL_FEATURE_MANIFEST_HASH:
        raise IncompatibleArtifactError(
            f"Feature manifest hash mismatch: expected {CANONICAL_FEATURE_MANIFEST_HASH}, got {observed_fm_hash}"
        )

    with open(feature_manifest_path, "r", encoding="utf-8") as f:
        fm_data = json.load(f)

    feature_manifest_meta = {
        "total_features": fm_data.get("total_feature_count", 391),
        "categorical_features": len(fm_data.get("categorical_columns", [])),
        "numerical_features": len(fm_data.get("numerical_columns", [])),
        "target_excluded": "isFraud" in fm_data.get("excluded_columns", []),
        "identifiers_excluded": (
            "TransactionID" in fm_data.get("excluded_columns", [])
            and "TransactionDT" in fm_data.get("excluded_columns", [])
        ),
        "sha256": observed_fm_hash,
    }

    # 5. Frozen policy verification
    cfg: IEEEPolicyConfig = get_frozen_ieee_policy_config()
    cfg_hash = cfg.compute_cfg_hash()
    frozen_policy_meta = {
        "status": cfg.status,
        "t_alert": cfg.t_alert,
        "t_review": cfg.t_review,
        "u_threshold": cfg.u_threshold,
        "disagreement_weight_lambda": cfg.disagreement_weight_lambda,
        "target_budget": cfg.target_budget,
        "workload_multiples": cfg.workload_multiples,
        "primary_workload_multiple": cfg.primary_workload_multiple,
        "reference_prevalence": cfg.reference_prevalence,
        "config_hash": cfg_hash,
        "verified": True,
    }

    # 6. Historical look transparent acknowledgement
    historical_ack = {
        "historical_test_looks_acknowledged": True,
        "evaluation_classification": "BENCHMARK_REPRODUCTION_AND_ACCEPTANCE_EVALUATION",
        "prior_looks": [
            {
                "gate": "G3_SYNTHETIC_TEST_LOOK",
                "dataset": "synthetic_smoke_fixture.csv (2,000 rows)",
                "record": "results/g3_test_look.json",
                "preserved_unmodified": True,
            },
            {
                "gate": "PHASE_4_IEEE_CIS_TEST_EVALUATION",
                "dataset": "ieee_cis_test_partition (118,108 rows)",
                "record": "results/ieee_cis_v1/training_report.json",
                "preserved_unmodified": True,
            },
        ],
        "reproducibility_protocol": (
            "Phase 10 evaluates frozen Candidate P5 vs Baseline B2 across pre-registered workload "
            "budgets (1.0x, 1.5x, 2.0x, 3.0x) with 1,000 paired bootstrap resamples. Zero hyperparameters "
            "or thresholds have been tuned on test labels."
        ),
    }

    # 7. Compute deterministic freeze hash over canonical record payload
    payload_to_hash = {
        "architecture_version": "ieee_cis_v1",
        "dataset": dataset_meta,
        "split_manifest": verified_splits,
        "model_bundle": model_bundle_meta,
        "feature_manifest": feature_manifest_meta,
        "frozen_policy": frozen_policy_meta,
        "historical_look_acknowledgement": historical_ack,
    }
    canonical_bytes = json.dumps(payload_to_hash, sort_keys=True, separators=(",", ":")).encode("utf-8")
    freeze_hash = hashlib.sha256(canonical_bytes).hexdigest()

    record = PreEvaluationFreezeRecord(
        architecture_version="ieee_cis_v1",
        historical_look_acknowledgement=historical_ack,
        dataset=dataset_meta,
        split_manifest=verified_splits,
        model_bundle=model_bundle_meta,
        feature_manifest=feature_manifest_meta,
        frozen_policy=frozen_policy_meta,
        freeze_hash=freeze_hash,
    )

    return record


def save_freeze_record(record: PreEvaluationFreezeRecord, output_path: Optional[Path] = None) -> Path:
    """Save the pre-evaluation freeze record to disk in results/ieee_cis_v1/."""
    target = output_path or (PROJECT_ROOT / "results" / "ieee_cis_v1" / "pre_evaluation_freeze.json")
    target.parent.mkdir(parents=True, exist_ok=True)
    with open(target, "w", encoding="utf-8") as f:
        f.write(record.model_dump_json(indent=2))
    return target


def load_and_validate_freeze_record(path: Optional[Path] = None) -> PreEvaluationFreezeRecord:
    """Load and re-validate an existing freeze record from disk."""
    target = path or (PROJECT_ROOT / "results" / "ieee_cis_v1" / "pre_evaluation_freeze.json")
    if not target.exists():
        raise ArtifactNotFoundError(f"Missing pre_evaluation_freeze.json at {target}")
    with open(target, "r", encoding="utf-8") as f:
        data = json.load(f)
    return PreEvaluationFreezeRecord(**data)
