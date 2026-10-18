"""
SignalGate Models Package
Provides base fraud models, probability calibration, and ensemble disagreement.
"""

from .base import (
    fit_base,
    raw_score,
    save_model_artifact,
    load_model_artifact,
)
from .calibrate import (
    fit_calibrator,
    calibrated_p,
    compute_ece,
    evaluate_calibration,
    compare_calibrators,
)
from .ensemble import (
    fit_ensemble,
    predict_ensemble_proba,
    disagreement,
    fit_rank_residual,
    apply_rank_residual,
    RankResidualizer,
)

__all__ = [
    "fit_base",
    "raw_score",
    "save_model_artifact",
    "load_model_artifact",
    "fit_calibrator",
    "calibrated_p",
    "compute_ece",
    "evaluate_calibration",
    "compare_calibrators",
    "fit_ensemble",
    "predict_ensemble_proba",
    "disagreement",
    "fit_rank_residual",
    "apply_rank_residual",
    "RankResidualizer",
]
