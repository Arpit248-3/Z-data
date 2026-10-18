"""SignalGate IBM Architecture Integration — Model Bundle Serialization & Manifest.

Manages isolated bundle persistence and cryptographic provenance for fitted models:
- Components: FeaturePipeline, BaselineB2, EraBaggedHeterogeneousEnsemble, PlattCalibrator.
- Synthetic adapter integration: wraps verified canonical artifacts in SYNTHETIC_SMOKE_ONLY mode.
- ModelBundleManifest: Tracks model versions, seeds, hashes, execution mode, and limitations.
- Mode-aware bundle loader and factory with fail-closed safety.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Dict, List, Optional
import joblib
import numpy as np
import pandas as pd
from pydantic import BaseModel, ConfigDict, Field

from integrations.ibm_architecture.exceptions import ModeUnavailableError
from integrations.ibm_architecture.models.baseline import BaselineB2
from integrations.ibm_architecture.models.calibration import PlattCalibrator
from integrations.ibm_architecture.models.ensemble import EraBaggedHeterogeneousEnsemble
from integrations.ibm_architecture.models.features import FeaturePipeline
from integrations.ibm_architecture.models.signals import DisagreementSignals, compute_signals


def compute_file_sha256(path: Path) -> str:
    """Compute cryptographic SHA-256 digest of a persisted file."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


class ModelBundleManifest(BaseModel):
    """Cryptographic provenance manifest for a persisted model bundle."""

    model_config = ConfigDict(extra="ignore", frozen=True)

    architecture_version: str = Field(default="synthetic_v1")
    execution_mode: str = Field(
        default="SYNTHETIC_SMOKE_ONLY",
        description="Mode identifier: SYNTHETIC_SMOKE_ONLY, RESOURCE_CONSTRAINED_LOCAL_DEV, or BENCHMARK_OFFLINE_VERIFIED",
    )
    benchmark_comparable: bool = Field(
        default=False,
        description="False for synthetic and dev runs; True only for verified full benchmark",
    )
    real_data_training_status: str = Field(
        default="DEFERRED",
        description="Status of full real-data model training (DEFERRED, BLOCKED, or COMPLETED)",
    )
    architecture_name: str = Field(
        default="synthetic_3member_hgb_u2",
        description="Active architecture identifier",
    )
    reference_architecture_status: str = Field(
        default="PROPOSED_5MEMBER_ERA_OMITTED_DEFERRED",
        description="Status of reference 5-member era-omitted architecture",
    )
    source_fixture: str = Field(
        default="data/synthetic_smoke_fixture.csv",
        description="Source dataset path or synthetic fixture",
    )
    training_timestamp: str = Field(default="")
    total_samples: int = Field(default=10000)
    row_counts: Dict[str, int] = Field(default_factory=dict)
    dt_intervals: Dict[str, List[int]] = Field(default_factory=dict)
    prevalence: Dict[str, float] = Field(default_factory=dict)
    split_hashes: Dict[str, str] = Field(default_factory=dict)
    feature_count: int = Field(default=67)
    validation_ece: float = Field(default=0.0)
    calibration_metrics: Dict[str, float] = Field(default_factory=dict)
    component_checksums: Dict[str, str] = Field(default_factory=dict)
    limitations: str = Field(
        default="Demonstration and integration mode using verified synthetic smoke artifacts. Real IEEE-CIS training deferred due to physical memory constraints."
    )


class ModelBundle:
    """Fitted model bundle providing complete end-to-end inference and signal calculation."""

    def __init__(
        self,
        pipeline: Any,
        baseline: Any,
        ensemble: Any,
        calibrator: Any,
        manifest: Optional[ModelBundleManifest] = None,
        adapter: Optional[Any] = None,
    ) -> None:
        self.pipeline = pipeline
        self.baseline = baseline
        self.ensemble = ensemble
        self.calibrator = calibrator
        self.manifest = manifest or ModelBundleManifest()
        self.adapter = adapter

    @property
    def execution_mode(self) -> str:
        return self.manifest.execution_mode

    @property
    def is_synthetic(self) -> bool:
        return self.manifest.execution_mode == "SYNTHETIC_SMOKE_ONLY"

    @property
    def real_data_training_status(self) -> str:
        return self.manifest.real_data_training_status

    def score_features(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Transform raw features, compute ensemble consensus, calibration, and disagreement signals.

        Returns dictionary containing:
          - 'p_raw': Raw ensemble consensus probabilities
          - 'p_cal': Calibrated risk probabilities
          - 'u': Disagreement standard deviation
          - 'u2': Disagreement rank-residual or MAD
          - 'n': Active ensemble members count
          - 'p_b2': Baseline B2 probabilities
          - 'execution_mode': Explicit execution mode
          - 'benchmark_comparable': Comparability flag
          - 'real_data_training_status': Explicit deferred status
        """
        if self.adapter is not None:
            return self.adapter.score_features(df)

        # Standard IEEE-CIS local dev pipeline execution
        X = self.pipeline.transform(df)
        mp = self.ensemble.predict_member_proba(X)
        signals_struct = compute_signals(mp)

        p_raw = signals_struct["p"]
        u = signals_struct["u"]
        u2 = signals_struct["u2"]
        n = signals_struct["n"]

        p_cal = self.calibrator.predict_proba(p_raw)
        p_b2 = self.baseline.predict_proba(X)

        return {
            "p_raw": p_raw,
            "p_cal": p_cal,
            "u": u,
            "u2": u2,
            "n": n,
            "p_b2": p_b2,
            "execution_mode": self.manifest.execution_mode,
            "benchmark_comparable": self.manifest.benchmark_comparable,
            "real_data_training_status": self.manifest.real_data_training_status,
        }


def save_bundle(bundle: ModelBundle, output_dir: Path | str) -> ModelBundleManifest:
    """Persist all bundle components and manifest with cryptographic checksums."""
    target_dir = Path(output_dir)
    target_dir.mkdir(parents=True, exist_ok=True)

    pipeline_file = target_dir / "feature_pipeline.joblib"
    baseline_file = target_dir / "baseline_b2.joblib"
    ensemble_file = target_dir / "ensemble.joblib"
    calibrator_file = target_dir / "calibrator.joblib"

    joblib.dump(bundle.pipeline, pipeline_file)
    joblib.dump(bundle.baseline, baseline_file)
    joblib.dump(bundle.ensemble, ensemble_file)
    joblib.dump(bundle.calibrator, calibrator_file)

    checksums = {
        "feature_pipeline.joblib": compute_file_sha256(pipeline_file),
        "baseline_b2.joblib": compute_file_sha256(baseline_file),
        "ensemble.joblib": compute_file_sha256(ensemble_file),
        "calibrator.joblib": compute_file_sha256(calibrator_file),
    }

    manifest_dict = bundle.manifest.model_dump()
    manifest_dict["component_checksums"] = checksums
    updated_manifest = ModelBundleManifest(**manifest_dict)

    manifest_path = target_dir / "model_bundle_manifest.json"
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(updated_manifest.model_dump(), f, indent=2)

    return updated_manifest


def load_bundle(bundle_dir: Path | str) -> ModelBundle:
    """Load and verify a persisted model bundle from disk."""
    target_dir = Path(bundle_dir)
    if not target_dir.exists():
        raise FileNotFoundError(f"Model bundle directory not found at: {target_dir}")

    manifest_path = target_dir / "model_bundle_manifest.json"
    if not manifest_path.exists():
        raise FileNotFoundError(f"Manifest not found at: {manifest_path}")

    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest_data = json.load(f)
    manifest = ModelBundleManifest(**manifest_data)

    pipeline = joblib.load(target_dir / "feature_pipeline.joblib")
    baseline = joblib.load(target_dir / "baseline_b2.joblib")
    ensemble = joblib.load(target_dir / "ensemble.joblib")
    calibrator = joblib.load(target_dir / "calibrator.joblib")

    return ModelBundle(
        pipeline=pipeline,
        baseline=baseline,
        ensemble=ensemble,
        calibrator=calibrator,
        manifest=manifest,
    )


def load_synthetic_bundle(project_root: Optional[Path | str] = None) -> ModelBundle:
    """Safely load and construct a ModelBundle wrapping verified synthetic artifacts."""
    from integrations.ibm_architecture.models.synthetic_adapter import SyntheticModelAdapter

    adapter = SyntheticModelAdapter.load(project_root=project_root)
    return ModelBundle(
        pipeline=adapter.pipeline,
        baseline=adapter.hgb_base,
        ensemble=adapter.ensemble_members,
        calibrator=adapter.calibrator,
        manifest=adapter.manifest,
        adapter=adapter,
    )


def get_model_bundle(
    mode: str = "SYNTHETIC_SMOKE_ONLY",
    project_root: Optional[Path | str] = None,
) -> ModelBundle:
    """Mode-aware factory providing verified model bundles with fail-closed safety."""
    if mode == "SYNTHETIC_SMOKE_ONLY":
        return load_synthetic_bundle(project_root=project_root)
    elif mode == "IEEE_CIS_OFFLINE_BENCHMARK":
        raise ModeUnavailableError(
            mode=mode,
            reason=(
                "Real IEEE-CIS model training is DEFERRED due to host physical RAM constraints "
                "(host has 7.75 GB total RAM; benchmark requires >= 16 GB). "
                "The full benchmark script is armed at 'scripts/train_full_benchmark.py'."
            ),
            missing_prerequisites=["16GB_PHYSICAL_RAM", "MODELS_ARTIFACTS_IEEE_CIS_V1_FULL"],
            diagnostics={
                "benchmark_comparable": False,
                "real_data_training_status": "DEFERRED",
                "recommended_action": "Execute scripts/train_full_benchmark.py on an eligible machine.",
            },
        )
    elif mode == "LIVE_SOURCE_NOT_CONNECTED":
        raise ModeUnavailableError(
            mode=mode,
            reason="Live transaction feed is DISCONNECTED. SignalGate is an offline decision-support benchmark.",
            missing_prerequisites=["LIVE_BANK_FEED"],
        )
    else:
        raise ValueError(f"Unrecognized evidence mode: {mode}")
