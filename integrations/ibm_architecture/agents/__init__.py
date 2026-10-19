"""SignalGate IBM Architecture Integration — Governed Agents Subpackage.

Exports Case Copilot, Agent Supervisor, Brief schemas, and LLM providers.
"""

from integrations.ibm_architecture.agents.copilot import (
    CaseCopilot,
    CopilotBrief,
)
from integrations.ibm_architecture.agents.providers import (
    ConfigurableLLMProvider,
    LLMProvider,
    OfflineTemplateProvider,
)
from integrations.ibm_architecture.agents.supervisor import (
    AgentSupervisor,
)

__all__ = [
    "LLMProvider",
    "OfflineTemplateProvider",
    "ConfigurableLLMProvider",
    "CopilotBrief",
    "CaseCopilot",
    "AgentSupervisor",
]
