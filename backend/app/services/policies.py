"""SignalGate Policy Comparison Service

Extracts policy evaluations from results.json, supporting optional budget filtering.
"""

from typing import Any, Dict, List, Optional
from backend.app.schemas import PolicyComparisonItem, PolicyCompareResponse
from backend.app.services.artifacts import ArtifactService


class PolicyService:
    def __init__(self, artifact_service: ArtifactService):
        self.artifacts = artifact_service

    def compare_policies(self, budget_multiple: Optional[str] = None) -> Optional[PolicyCompareResponse]:
        results = self.artifacts.get_results_json()
        if results is None:
            return None

        status = results.get("status", "SYNTHETIC_SMOKE_ONLY")
        is_synthetic = results.get("is_synthetic", True)
        disclaimer = (
            "Evidence derived from synthetic development fixture under pre-registered budgets. "
            "Never cite as real-world benchmark performance."
        )

        # Default to primary 1.5x budget if not specified
        if budget_multiple is None or budget_multiple == "1.5x":
            primary_comp = results.get("primary_policy_comparison", {})
            items: List[PolicyComparisonItem] = []
            for pol_name, m in primary_comp.items():
                items.append(
                    PolicyComparisonItem(
                        policy=m.get("policy", pol_name),
                        target_budget=m.get("target_budget", 0.06525),
                        total_transactions=m.get("total_transactions", 2000),
                        escalated_count=m.get("touched_count", 130),
                        touched_rate=m.get("touched_rate", 0.065),
                        total_fraud=m.get("total_fraud", 111),
                        caught_fraud=m.get("tp", 0),
                        missed_fraud=m.get("fn", 0),
                        recall_at_touched=m.get("recall_at_touched", 0.0),
                        precision=m.get("precision", 0.0),
                        fpr=m.get("fpr"),
                        deferred_count=m.get("deferred_count"),
                        deferred_rate=m.get("deferred_rate"),
                        confident_miss_count=m.get("confident_miss_count"),
                        routine_fraud_rate=m.get("routine_fraud_rate"),
                        threshold=m.get("threshold"),
                    )
                )
            return PolicyCompareResponse(
                status=status,
                is_synthetic=is_synthetic,
                budget_multiple="1.5x",
                target_budget=0.06525,
                policies=items,
                disclaimer=disclaimer,
            )

        # Handle specific budget sweep multiples
        budget_sweep = results.get("budget_sweep", {})
        if budget_multiple not in budget_sweep:
            return None

        sw = budget_sweep[budget_multiple]
        sg_m = sw.get("signalgate_metrics", {})
        target_b = sw.get("target_budget", 0.06525)

        items = [
            PolicyComparisonItem(
                policy="B2_top_b_risk",
                target_budget=target_b,
                total_transactions=sg_m.get("total_transactions", 2000),
                escalated_count=sw.get("capacity", 130),
                touched_rate=round(float(sw.get("capacity", 130) / sg_m.get("total_transactions", 2000)), 4),
                total_fraud=sg_m.get("total_fraud", 111),
                caught_fraud=int(round(sw.get("b2_recall", 0.0) * sg_m.get("total_fraud", 111))),
                missed_fraud=sg_m.get("total_fraud", 111) - int(round(sw.get("b2_recall", 0.0) * sg_m.get("total_fraud", 111))),
                recall_at_touched=sw.get("b2_recall", 0.0),
                precision=round(float(round(sw.get("b2_recall", 0.0) * sg_m.get("total_fraud", 111)) / max(1, sw.get("capacity", 130))), 4),
            ),
            PolicyComparisonItem(
                policy="SignalGate_frozen",
                target_budget=target_b,
                total_transactions=sg_m.get("total_transactions", 2000),
                escalated_count=sg_m.get("touched_count", 130),
                touched_rate=sg_m.get("touched_rate", target_b),
                total_fraud=sg_m.get("total_fraud", 111),
                caught_fraud=sg_m.get("tp", 0),
                missed_fraud=sg_m.get("fn", 0),
                recall_at_touched=sg_m.get("recall_at_touched", 0.0),
                precision=sg_m.get("precision", 0.0),
                fpr=sg_m.get("fpr"),
                deferred_count=sg_m.get("deferred_count"),
                deferred_rate=sg_m.get("deferred_rate"),
                confident_miss_count=sg_m.get("confident_miss_count"),
                routine_fraud_rate=sg_m.get("routine_fraud_rate"),
            ),
        ]

        return PolicyCompareResponse(
            status=status,
            is_synthetic=is_synthetic,
            budget_multiple=budget_multiple,
            target_budget=target_b,
            policies=items,
            disclaimer=disclaimer,
        )
