"""SignalGate IBM Architecture Integration — Models Package.

Exports:
- FeaturePipeline, SyntheticFeaturePipeline
- BaselineB2, SyntheticModelAdapter
- EraBaggedHeterogeneousEnsemble, MemberPredictions, compute_training_eras, get_era_omitted_indices
- PlattCalibrator, IsotonicCalibrator, calibration_ece, validate_calibration_partition
- DisagreementSignals, DisagreementSignalExtractor, RobustDisagreementSignalExtractor, compute_signals
- ModelBundle, ModelBundleManifest, save_bundle, load_bundle, load_synthetic_bundle, get_model_bundle
- check_memory_preflight, load_bounded_dev_cohort, split_dev_cohort, train_local_dev_pipeline
"""

from __future__ import annotations

from integrations.ibm_architecture.models.baseline import BaselineB2
from integrations.ibm_architecture.models.bundle import (
    ModelBundle,
    ModelBundleManifest,
    get_model_bundle,
    load_bundle,
    load_synthetic_bundle,
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
)
from integrations.ibm_architecture.models.synthetic_adapter import (
    SyntheticFeaturePipeline,
    SyntheticModelAdapter,
)
from integrations.ibm_architecture.models.trainer import (
    check_memory_preflight,
    load_bounded_dev_cohort,
    split_dev_cohort,
    train_local_dev_pipeline,
    train_mock_pipeline_for_testing,
)

__all__ = [
    "FeaturePipeline",
    "SyntheticFeaturePipeline",
    "BaselineB2",
    "SyntheticModelAdapter",
    "EraBaggedHeterogeneousEnsemble",
    "MemberPredictions",
    "compute_training_eras",
    "get_era_omitted_indices",
    "PlattCalibrator",
    "IsotonicCalibrator",
    "calibration_ece",
    "validate_calibration_partition",
    "DisagreementSignals",
    "DisagreementSignalExtractor",
    "RobustDisagreementSignalExtractor",
    "compute_signals",
    "ModelBundle",
    "ModelBundleManifest",
    "save_bundle",
    "load_bundle",
    "load_synthetic_bundle",
    "get_model_bundle",
    "check_memory_preflight",
    "load_bounded_dev_cohort",
    "split_dev_cohort",
    "train_local_dev_pipeline",
    "train_mock_pipeline_for_testing",
]
