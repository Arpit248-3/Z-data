"""SignalGate Scenario Value Model Module

Implements transparent sensitivity analysis for fraud triage operations,
strictly complying with Blueprint Section 6.6 and 8.2:
- Net benefit formula:
    Scenario Net Benefit = (Caught Fraud Value * Recovery Rate)
                           - (Review Cost per Case * Touched Cases)
                           - (False-Alert Friction Cost * False Alerts)
- Transparent separation of measured observed amounts from operational cost assumptions.
- Explicit disclaimers: transaction amounts do not equal guaranteed recovered funds.
- Rejects missing inputs with visible unavailable statuses.
- Supports configurable assumption sweeps.
"""

from typing import Any, Dict, List, Optional, Sequence, Union
import numpy as np
import pandas as pd


class ScenarioValueModel:
    """Configurable economic value model for fraud triage sensitivity analysis."""

    def __init__(
        self,
        cost_per_review: float = 20.0,
        friction_per_false_alert: float = 30.0,
        recovery_rate: float = 0.90,
    ):
        """Initialize value model with explicit operational cost assumptions.

        Args:
            cost_per_review: Assumed operational labor cost ($) per reviewed/touched transaction.
            friction_per_false_alert: Assumed customer friction or churn cost ($) per false alert.
            recovery_rate: Assumed fraction of caught transaction value effectively recovered/prevented.
        """
        self.cost_per_review = float(cost_per_review)
        self.friction_per_false_alert = float(friction_per_false_alert)
        self.recovery_rate = float(recovery_rate)

    def evaluate(
        self,
        y_true: Union[Sequence[int], np.ndarray, pd.Series],
        actions: Union[Sequence[str], np.ndarray, pd.Series],
        amounts: Optional[Union[Sequence[float], np.ndarray, pd.Series]],
        status: str = "SYNTHETIC_SMOKE_ONLY",
    ) -> Dict[str, Any]:
        """Evaluate net economic benefit on a given evaluation cohort."""
        if amounts is None:
            return {
                "status": "UNAVAILABLE",
                "reason": "Transaction amounts not provided. Cannot compute financial value model.",
            }

        y = np.asarray(y_true, dtype=int)
        act = np.asarray(actions, dtype=str)
        amt = np.asarray(amounts, dtype=float)

        if not (len(y) == len(act) == len(amt)):
            raise ValueError("Length mismatch between y_true, actions, and amounts")

        # Masks
        alert_mask = act == "FRAUD_ALERT"
        review_mask = act == "MANUAL_REVIEW"
        touched_mask = alert_mask | review_mask

        # Measured dataset values
        total_fraud_amt = float(np.sum(amt[y == 1]))
        caught_fraud_amt = float(np.sum(amt[(y == 1) & touched_mask]))
        missed_fraud_amt = float(np.sum(amt[(y == 1) & (~touched_mask)]))
        false_alert_count = int(np.sum((y == 0) & alert_mask))
        touched_count = int(np.sum(touched_mask))

        # Model calculations
        estimated_gross_benefit = caught_fraud_amt * self.recovery_rate
        total_review_cost = touched_count * self.cost_per_review
        total_friction_cost = false_alert_count * self.friction_per_false_alert
        total_operational_cost = total_review_cost + total_friction_cost
        net_benefit = estimated_gross_benefit - total_operational_cost

        return {
            "status": status,
            "assumptions": {
                "cost_per_review_usd": self.cost_per_review,
                "friction_per_false_alert_usd": self.friction_per_false_alert,
                "assumed_recovery_rate": self.recovery_rate,
            },
            "observed_measurements": {
                "total_fraud_volume_usd": round(total_fraud_amt, 2),
                "caught_fraud_volume_usd": round(caught_fraud_amt, 2),
                "missed_fraud_volume_usd": round(missed_fraud_amt, 2),
                "touched_transactions": touched_count,
                "false_alerts_count": false_alert_count,
            },
            "financial_outcomes_usd": {
                "gross_prevented_fraud_usd": round(estimated_gross_benefit, 2),
                "analyst_review_costs_usd": round(total_review_cost, 2),
                "customer_friction_costs_usd": round(total_friction_cost, 2),
                "total_triage_costs_usd": round(total_operational_cost, 2),
                "scenario_net_benefit_usd": round(net_benefit, 2),
                "roi_multiple": round(float(net_benefit / total_operational_cost), 2)
                if total_operational_cost > 0
                else None,
            },
            "disclaimer": (
                "Hypothetical economic sensitivity analysis: observed transaction amounts "
                "do not represent guaranteed cash savings or chargeback recovery. Operational costs "
                "are explicit assumptions for policy comparison only."
            ),
        }

    def sensitivity_grid(
        self,
        y_true: Sequence[int],
        actions: Sequence[str],
        amounts: Sequence[float],
        review_costs: Sequence[float] = (10.0, 20.0, 30.0),
        friction_costs: Sequence[float] = (15.0, 30.0, 50.0),
        recovery_rates: Sequence[float] = (0.80, 0.90, 1.00),
    ) -> List[Dict[str, Any]]:
        """Compute sensitivity grid across combinations of operational assumptions."""
        grid = []
        for rc in review_costs:
            for fc in friction_costs:
                for rr in recovery_rates:
                    model = ScenarioValueModel(
                        cost_per_review=rc,
                        friction_per_false_alert=fc,
                        recovery_rate=rr,
                    )
                    res = model.evaluate(y_true, actions, amounts)
                    if res.get("status") == "UNAVAILABLE":
                        return []
                    grid.append({
                        "review_cost": rc,
                        "friction_cost": fc,
                        "recovery_rate": rr,
                        "gross_prevented_usd": res["financial_outcomes_usd"]["gross_prevented_fraud_usd"],
                        "total_costs_usd": res["financial_outcomes_usd"]["total_triage_costs_usd"],
                        "net_benefit_usd": res["financial_outcomes_usd"]["scenario_net_benefit_usd"],
                    })
        return grid
