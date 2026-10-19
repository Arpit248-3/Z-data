"""SignalGate IBM Architecture Integration — Models, Ensembles & Calibration Package.

Provides reproducible model training, 5-member era-bagged heterogeneous ensemble,
Platt scaling calibration, epistemic disagreement signals, and artifact bundles.

Governing Specification: docs/ibm_architecture_integration_master_spec.md § C, § H
"""

from integrations.ibm_architecture.models.baseline import BaselineB2
from integrations.ibm_architecture.models.bundle import (
    DEFAULT_ARTIFACT_DIR,
    ModelBundle,
    ModelBundleManifest,
    compute_file_sha256,
    load_bundle,
    save_bundle,
)
from integrations.ibm_architecture.models.calibration import (
    IsotonicCalibrator,
    PlattCalibrator,
    calibration_ece,
    validate_calibration_partition,
)
from integrations.ibm_architecture.models.ensemble import (
    EraBaggedHeterogeneousEnsemble,
    MemberPredictions,
    compute_training_eras,
    get_era_omitted_indices,
)
from integrations.ibm_architecture.models.features import FeaturePipeline
from integrations.ibm_architecture.models.signals import (
    DisagreementSignalExtractor,
    DisagreementSignals,
    RobustDisagreementSignalExtractor,
    compute_signals,
    compute_single_signals,
)
from integrations.ibm_architecture.models.trainer import (
    check_available_ram,
    get_available_ram_gb,
    train_mock_pipeline_for_testing,
    train_pipeline,
)

__all__ = [
    # Feature pipeline
    "FeaturePipeline",
    # Baseline
    "BaselineB2",
    # Ensemble
    "EraBaggedHeterogeneousEnsemble",
    "MemberPredictions",
    "compute_training_eras",
    "get_era_omitted_indices",
    # Calibration
    "PlattCalibrator",
    "IsotonicCalibrator",
    "calibration_ece",
    "validate_calibration_partition",
    # Signals
    "DisagreementSignals",
    "DisagreementSignalExtractor",
    "RobustDisagreementSignalExtractor",
    "compute_signals",
    "compute_single_signals",
    # Bundle serialization
    "ModelBundle",
    "ModelBundleManifest",
    "save_bundle",
    "load_bundle",
    "compute_file_sha256",
    "DEFAULT_ARTIFACT_DIR",
    # Training orchestration
    "train_pipeline",
    "train_mock_pipeline_for_testing",
    "check_available_ram",
    "get_available_ram_gb",
]
