"""SignalGate Evaluation Package

Provides metrics, paired bootstrap confidence intervals, shift & drift monitoring,
segment analysis, scenario value modeling, and latency benchmarking.
"""

from eval.metrics import (
    calculate_binary_metrics,
    calculate_policy_metrics,
    recall_at_touched,
    value_missed,
    value_caught,
    ece,
    calculate_pr_auc,
)
from eval.bootstrap import (
    paired_bootstrap,
    paired_bootstrap_tuple,
)
from eval.drift import (
    calculate_psi,
    calculate_feature_drift,
    monitor_dataset_drift,
)
from eval.segments import (
    analyze_segment_escalation,
    analyze_all_segments,
)
from eval.value_model import (
    ScenarioValueModel,
)
from eval.latency import (
    time_calls,
    benchmark_pipeline_latency,
)

__all__ = [
    "calculate_binary_metrics",
    "calculate_policy_metrics",
    "recall_at_touched",
    "value_missed",
    "value_caught",
    "ece",
    "calculate_pr_auc",
    "paired_bootstrap",
    "paired_bootstrap_tuple",
    "calculate_psi",
    "calculate_feature_drift",
    "monitor_dataset_drift",
    "analyze_segment_escalation",
    "analyze_all_segments",
    "ScenarioValueModel",
    "time_calls",
    "benchmark_pipeline_latency",
]
