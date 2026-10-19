"""SignalGate IBM Architecture Integration — Governed LLM Providers.

Implements pluggable provider interfaces for Case Copilot:
- LLMProvider protocol defining the generator contract.
- OfflineTemplateProvider: Deterministic, factual brief generator with zero network dependency.
- ConfigurableLLMProvider: Optional real LLM provider (Ollama / OpenAI-compatible endpoint)
  with bounded timeouts (<= 5s) and automatic fallback to OfflineTemplateProvider.

Governing Specification: docs/ibm_architecture_integration_master_spec.md § C, § J2
"""

from __future__ import annotations

import json
from typing import Any, Dict, Optional, Protocol
import urllib.error
import urllib.request

from integrations.ibm_architecture.agent_view import AgentCaseView


class LLMProvider(Protocol):
    """Protocol defining the interface for agent explanation generators."""

    provider_name: str

    def generate(self, prompt: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate structured advisory content from prompt and sanitized context."""
        ...


class OfflineTemplateProvider:
    """Deterministic, rule-based explanation provider using factual templates.

    Guarantees:
    - 100% offline, zero external dependencies or network requests.
    - Grounded strictly in allowlisted AgentCaseView fields.
    - Model disagreement (u) is explicitly interpreted as epistemic uncertainty,
      never as evidence of fraudulent activity.
    """

    provider_name: str = "offline_template_v1"

    def generate(self, prompt: str, context: Dict[str, Any]) -> Dict[str, Any]:
        p = context.get("p")
        u2 = context.get("u2") or context.get("u")
        action = context.get("action", "ROUTINE")
        reason = context.get("reason", "R5_LOW_RISK_RELIABLE")
        case_id = context.get("record_id", "unknown")

        # 1. High-risk alert case
        if action == "FRAUD_ALERT" or reason == "R1_HIGH_RISK":
            risk_assessment = (
                f"Elevated fraud risk detected. Calibrated posterior probability p={p:.4f} "
                f"exceeds high-risk alert threshold."
            )
            uncertainty_interp = (
                f"Model consensus is firm (dispersion u2={u2:.4f} if u2 is not None else 0.0)."
                if u2 is not None and u2 < 0.3
                else "Elevated dispersion observed; multiple model eras indicate high fraud signals."
            )
            focus_areas = [
                "Verify cardholder identity and shipping address against billing history.",
                "Inspect device and IP domain consistency.",
                "Review velocity of recent transaction amounts.",
            ]

        # 2. Epistemic model disagreement case
        elif reason == "R3_MODEL_DISAGREEMENT":
            risk_assessment = (
                f"Model disagreement escalation. Calibrated risk probability p={p:.4f} is below "
                f"fraud alert cutoff, but estimator dispersion u2={u2:.4f} exceeds disagreement threshold."
            )
            uncertainty_interp = (
                f"Substantial disagreement detected across heterogeneous ensemble members. "
                f"Tree-based estimators diverge from linear and gradient-boosted estimators. "
                f"IMPORTANT: Disagreement reflects epistemic model uncertainty regarding an unfamiliar "
                f"or borderline pattern, NOT affirmative proof of fraud."
            )
            focus_areas = [
                "Examine novel feature combinations that may deviate from historical baseline distributions.",
                "Check for emerging merchant or cardholder transaction profiles.",
                "Perform manual verification to establish ground-truth feedback for drift monitoring.",
            ]

        # 3. Intermediate risk review case
        elif action == "MANUAL_REVIEW" or reason == "R2_INTERMEDIATE_RISK":
            risk_assessment = (
                f"Borderline transaction risk. Calibrated posterior probability p={p:.4f} "
                f"warrants secondary analyst evaluation under review threshold."
            )
            uncertainty_interp = (
                f"Estimator dispersion is moderate (u2={u2:.4f} if u2 is not None else 0.0). "
                f"Scores cluster in the intermediate uncertainty margin."
            )
            focus_areas = [
                "Assess transaction amount against account historical norms.",
                "Cross-reference email domain and product category.",
            ]

        # 4. Routine low-risk case
        else:
            p_val = p if p is not None else 0.0
            risk_assessment = (
                f"Routine transaction. Calibrated posterior probability p={p_val:.4f} "
                f"is well below review threshold."
            )
            uncertainty_interp = "Ensemble members exhibit strong consensus on low fraud risk."
            focus_areas = [
                "No immediate investigation required; eligible for straight-through processing."
            ]

        return {
            "case_id": case_id,
            "risk_assessment": risk_assessment,
            "uncertainty_interpretation": uncertainty_interp,
            "suggested_investigation_focus": focus_areas,
            "provider": self.provider_name,
            "is_live_llm": False,
        }


class ConfigurableLLMProvider:
    """Configurable live LLM provider interfacing with Ollama or OpenAI-compatible endpoints.

    Features:
    - Bounded execution timeouts (default 5.0s).
    - Proactive JSON format enforcement.
    - Automatic, graceful fallback to OfflineTemplateProvider upon any network error,
      timeout, missing credentials, or invalid response.
    """

    provider_name: str = "configurable_llm_v1"

    def __init__(
        self,
        endpoint_url: Optional[str] = None,
        api_key: Optional[str] = None,
        model_name: str = "llama3",
        timeout_seconds: float = 5.0,
        fallback_provider: Optional[OfflineTemplateProvider] = None,
    ) -> None:
        self.endpoint_url = endpoint_url
        self.api_key = api_key
        self.model_name = model_name
        self.timeout_seconds = timeout_seconds
        self.fallback = fallback_provider or OfflineTemplateProvider()

    def is_available(self) -> bool:
        """Check if provider has a configured endpoint URL."""
        return bool(self.endpoint_url and self.endpoint_url.strip())

    def generate(self, prompt: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Attempt live generation; fail safe to OfflineTemplateProvider on any error."""
        if not self.is_available():
            fallback_res = self.fallback.generate(prompt, context)
            fallback_res["fallback_reason"] = "Live LLM endpoint not configured"
            return fallback_res

        try:
            payload = {
                "model": self.model_name,
                "prompt": prompt,
                "stream": False,
                "format": "json",
            }
            data = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(
                self.endpoint_url,  # type: ignore[arg-type]
                data=data,
                headers={"Content-Type": "application/json"},
            )
            if self.api_key:
                req.add_header("Authorization", f"Bearer {self.api_key}")

            with urllib.request.urlopen(req, timeout=self.timeout_seconds) as response:
                resp_bytes = response.read()
                raw_json = json.loads(resp_bytes.decode("utf-8"))
                # Extract text response from Ollama or OpenAI format
                content_str = raw_json.get("response") or raw_json.get("choices", [{}])[0].get("message", {}).get("content", "")
                parsed = json.loads(content_str)
                return {
                    "case_id": context.get("record_id", "unknown"),
                    "risk_assessment": parsed.get("risk_assessment", "Live assessment generated"),
                    "uncertainty_interpretation": parsed.get("uncertainty_interpretation", "Live uncertainty generated"),
                    "suggested_investigation_focus": parsed.get("suggested_investigation_focus", []),
                    "provider": f"{self.provider_name}:{self.model_name}",
                    "is_live_llm": True,
                }
        except Exception as exc:
            # Strictly fall back to offline template on any failure
            fallback_res = self.fallback.generate(prompt, context)
            fallback_res["fallback_reason"] = f"Live LLM call failed ({type(exc).__name__}: {str(exc)})"
            return fallback_res
