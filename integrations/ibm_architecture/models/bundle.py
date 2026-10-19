"""SignalGate IBM Architecture Integration — Model Bundle Serialization.

Manages versioned, cryptographic model artifact bundles under models/artifacts/ieee_cis_v1/:
- Encapsulates FeaturePipeline, BaselineB2, EraBaggedHeterogeneousEnsemble, and PlattCalibrator.
- ModelBundleManifest captures seeds, partition hashes, metrics, and execution concurrency.
- Validates artifact checksums on save and load to guarantee provenance.
"""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
import joblib
from pydantic import BaseModel, ConfigDict, Field

from integrations.ibm_architecture.models.features import FeaturePipeline
from integrations.ibm_architecture.models.baseline import BaselineB2
from integrations.ibm_architecture.models.ensemble import EraBaggedHeterogeneousEnsemble
from integrations.ibm_architecture.models.calibration import PlattCalibrator
from integrations.ibm_architecture.exceptions import ArtifactNotFoundError, IncompatibleArtifactError

DEFAULT_ARTIFACT_DIR = Path(__file__).resolve().parent.parent.parent.parent / "models" / "artifacts" / "ieee_cis_v1"


def compute_file_sha256(path: Path) -> str:
    """Compute deterministic SHA-256 checksum over file contents."""
    hasher = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(1024 * 1024):
            hasher.update(chunk)
    return hasher.hexdigest()


class ModelBundleManifest(BaseModel):
    """Pydantic model recording model bundle provenance and configuration."""

    model_config = ConfigDict(extra="forbid")

    architecture_version: str = Field(default="ieee_cis_v1")
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    execution_concurrency: str = Field(default="sequential", description="Execution mode (sequential vs parallel)")
    member_concurrency: Dict[str, Any] = Field(default_factory=lambda: {"extra_trees_n_jobs": 1})
    feature_count: int = Field(default=391)
    feature_manifest_sha256: str = Field(default="")
    split_hashes: Dict[str, str] = Field(default_factory=dict)
    row_counts: Dict[str, int] = Field(default_factory=dict)
    training_duration_seconds: float = Field(default=0.0)
    memory_peak_mb: Optional[float] = Field(default=None)
    metrics: Dict[str, Any] = Field(default_factory=dict)
    artifact_hashes: Dict[str, str] = Field(default_factory=dict)


class ModelBundle:
    """Container holding all fitted pipeline components and bundle manifest."""

    def __init__(
        self,
        feature_pipeline: FeaturePipeline,
        baseline_b2: BaselineB2,
        ensemble: EraBaggedHeterogeneousEnsemble,
        calibrator: PlattCalibrator,
        manifest: Optional[ModelBundleManifest] = None,
    ) -> None:
        self.feature_pipeline = feature_pipeline
        self.baseline_b2 = baseline_b2
        self.ensemble = ensemble
        self.calibrator = calibrator
        self.manifest = manifest or ModelBundleManifest()


def save_bundle(bundle: ModelBundle, output_dir: Optional[Union[str, Path]] = None) -> Dict[str, str]:
    """Persist model bundle components and manifest to output directory with SHA-256 verification."""
    out_path = Path(output_dir) if output_dir else DEFAULT_ARTIFACT_DIR
    out_path.mkdir(parents=True, exist_ok=True)

    # 1. Serialize estimators
    pipeline_file = out_path / "feature_pipeline.joblib"
    baseline_file = out_path / "baseline_b2.joblib"
    ensemble_file = out_path / "ensemble.joblib"
    calibrator_file = out_path / "calibrator.joblib"

    joblib.dump(bundle.feature_pipeline, pipeline_file, compress=3)
    joblib.dump(bundle.baseline_b2, baseline_file, compress=3)
    joblib.dump(bundle.ensemble, ensemble_file, compress=3)
    joblib.dump(bundle.calibrator, calibrator_file, compress=3)

    # 2. Record artifact hashes
    hashes = {
        "feature_pipeline.joblib": compute_file_sha256(pipeline_file),
        "baseline_b2.joblib": compute_file_sha256(baseline_file),
        "ensemble.joblib": compute_file_sha256(ensemble_file),
        "calibrator.joblib": compute_file_sha256(calibrator_file),
    }
    bundle.manifest.artifact_hashes = hashes

    # 3. Write manifest
    manifest_file = out_path / "model_bundle_manifest.json"
    with open(manifest_file, "w", encoding="utf-8") as f:
        json.dump(bundle.manifest.model_dump(), f, indent=2)

    return hashes


def load_bundle(bundle_dir: Optional[Union[str, Path]] = None) -> ModelBundle:
    """Load model bundle components and verify cryptographic SHA-256 checksums."""
    in_path = Path(bundle_dir) if bundle_dir else DEFAULT_ARTIFACT_DIR
    manifest_file = in_path / "model_bundle_manifest.json"

    if not manifest_file.exists():
        raise ArtifactNotFoundError(
            artifact_path=str(manifest_file),
            expected_purpose="Model bundle provenance manifest",
        )

    with open(manifest_file, "r", encoding="utf-8") as f:
        manifest_data = json.load(f)
    manifest = ModelBundleManifest(**manifest_data)

    # Verify hashes
    expected_files = {
        "feature_pipeline.joblib": in_path / "feature_pipeline.joblib",
        "baseline_b2.joblib": in_path / "baseline_b2.joblib",
        "ensemble.joblib": in_path / "ensemble.joblib",
        "calibrator.joblib": in_path / "calibrator.joblib",
    }

    for fname, fpath in expected_files.items():
        if not fpath.exists():
            raise ArtifactNotFoundError(
                artifact_path=str(fpath),
                expected_purpose=f"Model bundle component {fname}",
            )
        actual_hash = compute_file_sha256(fpath)
        expected_hash = manifest.artifact_hashes.get(fname)
        if expected_hash and actual_hash != expected_hash:
            raise IncompatibleArtifactError(
                artifact_path=str(fpath),
                expected_hash=expected_hash,
                actual_hash=actual_hash,
                details={"recommendation": "Re-run training pipeline to regenerate artifact bundle."},
            )

    feature_pipeline = joblib.load(expected_files["feature_pipeline.joblib"])
    baseline_b2 = joblib.load(expected_files["baseline_b2.joblib"])
    ensemble = joblib.load(expected_files["ensemble.joblib"])
    calibrator = joblib.load(expected_files["calibrator.joblib"])

    return ModelBundle(
        feature_pipeline=feature_pipeline,
        baseline_b2=baseline_b2,
        ensemble=ensemble,
        calibrator=calibrator,
        manifest=manifest,
    )
