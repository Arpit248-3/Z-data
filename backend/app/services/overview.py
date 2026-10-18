"""SignalGate Overview Service

Provides summary metrics derived strictly from validated results.json.
"""

from typing import Any, Dict, Optional
from backend.app.schemas import OverviewResponse
from backend.app.services.artifacts import ArtifactService


class OverviewService:
    def __init__(self, artifact_service: ArtifactService):
        self.artifacts = artifact_service

    def get_overview(self) -> OverviewResponse:
        results = self.artifacts.get_results_json()

        if results is None:
            return OverviewResponse(
                dataset_status="SYNTHETIC_SMOKE_ONLY",
                is_synthetic=True,
                evaluation_status="NOT_AVAILABLE",
                status_fields={"results_json": "NOT_AVAILABLE", "reason": "Evaluation results artifact not found."},
            )

        prov = results.get("provenance", {})
        primary = results.get("primary_policy_comparison", {})
        boot = results.get("paired_bootstrap_ci", {})
        sg = primary.get("SignalGate_frozen", {})
        b2 = primary.get("B2_top_b_risk", {})
        lat = results.get("latency_benchmarks", {})

        p95_lat = None
        if "single_transaction_path" in lat:
            p95_lat = lat["single_transaction_path"].get("p95_ms")

        ci_vals = None
        if "ci_lower" in boot and "ci_upper" in boot:
            ci_vals = [boot["ci_lower"], boot["ci_upper"]]

        return OverviewResponse(
            dataset_status=results.get("status", "SYNTHETIC_SMOKE_ONLY"),
            is_synthetic=results.get("is_synthetic", True),
            evaluation_status="COMPLETE",
            total_tested_transactions=prov.get("test_rows"),
            available_fraud_count=prov.get("test_fraud_count"),
            fraud_prevalence=prov.get("test_fraud_prevalence"),
            primary_budget=prov.get("primary_budget_touched_rate"),
            b2_recall=b2.get("recall_at_touched"),
            signalgate_recall=sg.get("recall_at_touched"),
            delta_recall_pp=sg.get("delta_recall_vs_b2_pp"),
            ci_95=ci_vals,
            ci_conclusive=boot.get("is_conclusive"),
            touched_rate=sg.get("touched_rate"),
            alert_rate=sg.get("alert_rate"),
            review_rate=sg.get("review_rate"),
            deferred_rate=sg.get("deferred_rate"),
            confident_miss_count=sg.get("confident_miss_count"),
            routine_fraud_rate=sg.get("routine_fraud_rate"),
            latency_p95_ms=p95_lat,
            frozen_config_hash=prov.get("frozen_config_hash"),
            split_hash=prov.get("split_hash"),
            status_fields={"results_json": "READY", "policy": "FROZEN"},
        )
