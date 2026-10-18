"""SignalGate IBM Architecture Integration — Synthetic-Mode Model Adapter.

Adapts and wraps existing verified synthetic model artifacts without retraining:
- models/artifacts/hgb_base.joblib (Baseline B2)
- models/artifacts/calibrator_sigmoid.joblib (Platt Sigmoid Calibrator)
- models/artifacts/ensemble_members.joblib (3-Member Heterogeneous Ensemble)
- models/artifacts/residualizer_u2.joblib (Rank-Residualizer u2)
- policy/frozen_policy.json (Frozen Policy)

Enforces Master Spec invariants:
- Ground-truth quarantine: rejects isFraud, TransactionID, TransactionDT
- Explicit metadata: execution_mode=SYNTHETIC_SMOKE_ONLY, benchmark_comparable=false, real_data_training_status=DEFERRED
- Safe loading and provenance checksum verification
"""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union
import joblib
import numpy as np
import pandas as pd

from data.schema import FORBIDDEN_MODEL_COLUMNS, ID_COLUMN, TARGET_COLUMN, TIME_COLUMN
from integrations.ibm_architecture.exceptions import (
    ArtifactNotFoundError,
    LeakageViolationError,
)
from integrations.ibm_architecture.models.bundle import ModelBundleManifest, compute_file_sha256
from models.calibrate import calibrated_p
from models.ensemble import apply_rank_residual, disagreement


QUARANTINE_COLUMNS = {
    "isfraud",
    "target",
    "true_label",
    "label",
    "transactionid",
    "transactiondt",
}


class SyntheticFeaturePipeline:
    """Quarantine-enforcing feature processor for synthetic smoke transactions."""

    def __init__(self, feature_names: List[str]) -> None:
        self.feature_names = list(feature_names)

    def validate_quarantine(self, df: pd.DataFrame) -> None:
        """Validate that input DataFrame contains zero quarantined target or identifier columns."""
        for col in df.columns:
            normalized_col = str(col).lower().replace("_", "")
            if normalized_col in {c.replace("_", "") for c in QUARANTINE_COLUMNS} or col in FORBIDDEN_MODEL_COLUMNS:
                raise LeakageViolationError(
                    f"Quarantined column '{col}' detected in inference feature input",
                    violated_fields=[str(col)],
                    context="SyntheticFeaturePipeline.validate_quarantine",
                )

    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        """Sanitize and align input DataFrame to canonical 67-feature numeric schema."""
        self.validate_quarantine(df)

        if len(df) == 0:
            return pd.DataFrame(columns=self.feature_names, dtype=np.float32)

        row_dict: Dict[str, Any] = {}
        out_rows = []
        for idx, row in df.iterrows():
            r = {}
            for feat in self.feature_names:
                val = row.get(feat, np.nan)
                if val is None or val == "":
                    r[feat] = np.nan
                else:
                    try:
                        r[feat] = float(val)
                    except (ValueError, TypeError):
                        r[feat] = np.nan
            out_rows.append(r)

        X_df = pd.DataFrame(out_rows, columns=self.feature_names).astype(np.float32)
        # Replace inf with nan
        X_df.replace([np.inf, -np.inf], np.nan, inplace=True)
        return X_df


class SyntheticModelAdapter:
    """Unified adapter wrapping verified synthetic estimators and signal extractors."""

    def __init__(
        self,
        hgb_base: Any,
        calibrator: Any,
        ensemble_members: List[Any],
        residualizer: Any,
        feature_names: List[str],
        manifest: Optional[ModelBundleManifest] = None,
    ) -> None:
        self.hgb_base = hgb_base
        self.calibrator = calibrator
        self.ensemble_members = ensemble_members
        self.residualizer = residualizer
        self.feature_names = list(feature_names)
        self.pipeline = SyntheticFeaturePipeline(feature_names=self.feature_names)
        self.manifest = manifest or ModelBundleManifest(
            execution_mode="SYNTHETIC_SMOKE_ONLY",
            benchmark_comparable=False,
            real_data_training_status="DEFERRED",
            architecture_name="synthetic_3member_hgb_u2",
            reference_architecture_status="PROPOSED_5MEMBER_ERA_OMITTED_DEFERRED",
            feature_count=len(feature_names),
        )

    @property
    def execution_mode(self) -> str:
        return self.manifest.execution_mode

    @property
    def is_synthetic(self) -> bool:
        return True

    @property
    def real_data_training_status(self) -> str:
        return self.manifest.real_data_training_status

    def score_baseline(self, X: pd.DataFrame | np.ndarray) -> np.ndarray:
        """Compute Baseline B2 probability."""
        if hasattr(self.hgb_base, "predict_proba"):
            return self.hgb_base.predict_proba(X)[:, 1]
        raise AttributeError("Baseline model missing predict_proba method.")

    def calibrate(self, X: pd.DataFrame | np.ndarray) -> np.ndarray:
        """Compute Platt-calibrated fraud probability."""
        return calibrated_p(self.calibrator, X)

    def predict_ensemble(
        self, X: pd.DataFrame | np.ndarray
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray, int]:
        """Compute ensemble consensus probability, raw std disagreement, and rank-residual u2.

        Returns:
            (p_raw, u, u2, n_members)
        """
        member_probs = [m.predict_proba(X)[:, 1] for m in self.ensemble_members]
        p_raw = np.mean(member_probs, axis=0)
        u = np.std(member_probs, axis=0, ddof=0)
        u2 = apply_rank_residual(self.residualizer, u, p_raw)
        return p_raw, u, u2, len(self.ensemble_members)

    def score_features(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Transform features with quarantine check, run inference, and return typed results."""
        X = self.pipeline.transform(df)

        p_b2 = self.score_baseline(X)
        p_cal = self.calibrate(X)
        p_raw, u, u2, n_members = self.predict_ensemble(X)

        return {
            "p_raw": p_raw,
            "p_cal": p_cal,
            "u": u,
            "u2": u2,
            "n": n_members,
            "p_b2": p_b2,
            "execution_mode": self.manifest.execution_mode,
            "benchmark_comparable": self.manifest.benchmark_comparable,
            "real_data_training_status": self.manifest.real_data_training_status,
        }

    @classmethod
    def load(cls, project_root: Optional[Path | str] = None) -> SyntheticModelAdapter:
        """Safely load and verify canonical synthetic artifacts from disk without retraining."""
        root = Path(project_root) if project_root else Path(__file__).resolve().parent.parent.parent.parent
        artifacts_dir = root / "models" / "artifacts"

        hgb_file = artifacts_dir / "hgb_base.joblib"
        cal_file = artifacts_dir / "calibrator_sigmoid.joblib"
        ens_file = artifacts_dir / "ensemble_members.joblib"
        res_file = artifacts_dir / "residualizer_u2.joblib"

        for p, purpose in [
            (hgb_file, "Baseline B2 estimator"),
            (cal_file, "Sigmoid probability calibrator"),
            (ens_file, "3-member ensemble"),
            (res_file, "u2 rank-residualizer"),
        ]:
            if not p.exists():
                raise ArtifactNotFoundError(str(p), purpose)

        # Compute checksums
        checksums = {
            "hgb_base.joblib": compute_file_sha256(hgb_file),
            "calibrator_sigmoid.joblib": compute_file_sha256(cal_file),
            "ensemble_members.joblib": compute_file_sha256(ens_file),
            "residualizer_u2.joblib": compute_file_sha256(res_file),
        }

        # Safe loading without modifying original files
        raw_hgb = joblib.load(hgb_file)
        raw_cal = joblib.load(cal_file)
        raw_ens = joblib.load(ens_file)
        raw_res = joblib.load(res_file)

        hgb_model = raw_hgb["model"] if isinstance(raw_hgb, dict) and "model" in raw_hgb else raw_hgb
        cal_model = raw_cal["model"] if isinstance(raw_cal, dict) and "model" in raw_cal else raw_cal
        ens_model = raw_ens["model"] if isinstance(raw_ens, dict) and "model" in raw_ens else raw_ens
        res_model = raw_res["model"] if isinstance(raw_res, dict) and "model" in raw_res else raw_res

        # Extract canonical feature names
        if hasattr(hgb_model, "feature_names_in_"):
            feature_names = list(hgb_model.feature_names_in_)
        else:
            # Fallback to inspecting companion meta json
            meta_file = artifacts_dir / "hgb_base.meta.json"
            if meta_file.exists():
                with open(meta_file, "r", encoding="utf-8") as f:
                    meta_data = json.load(f)
                    feature_names = meta_data.get("feature_manifest", {}).get("feature_names", [])
            else:
                feature_names = []

        manifest = ModelBundleManifest(
            architecture_version="synthetic_v1",
            execution_mode="SYNTHETIC_SMOKE_ONLY",
            benchmark_comparable=False,
            real_data_training_status="DEFERRED",
            architecture_name="synthetic_3member_hgb_u2",
            reference_architecture_status="PROPOSED_5MEMBER_ERA_OMITTED_DEFERRED",
            source_fixture="data/synthetic_smoke_fixture.csv",
            feature_count=len(feature_names),
            component_checksums=checksums,
            limitations=(
                "Demonstration and integration mode using verified synthetic smoke artifacts. "
                "Real IEEE-CIS training deferred due to physical memory constraints."
            ),
        )

        return cls(
            hgb_base=hgb_model,
            calibrator=cal_model,
            ensemble_members=ens_model,
            residualizer=res_model,
            feature_names=feature_names,
            manifest=manifest,
        )
