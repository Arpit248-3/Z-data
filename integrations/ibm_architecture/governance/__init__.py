"""SignalGate IBM Architecture Integration — Governance, Agents & Cryptographic Audit Package.

Exports:
- ClaimVerifier, VerificationResult, REGISTERED_TEMPLATES, ALLOWED_FIELD_OPERATORS
- CaseCopilot
- ClaimLedger
- AuditChain, verify_chain, get_default_audit_key
"""

from __future__ import annotations

from integrations.ibm_architecture.governance.claim_verifier import (
    ALLOWED_FIELD_OPERATORS,
    REGISTERED_TEMPLATES,
    ClaimVerifier,
    VerificationResult as ClaimVerificationResult,
)
from integrations.ibm_architecture.governance.copilot import CaseCopilot
from integrations.ibm_architecture.governance.claim_ledger import ClaimLedger
from integrations.ibm_architecture.governance.audit_chain import (
    AuditChain,
    VerificationResult as AuditVerificationResult,
    get_default_audit_key,
    verify_chain,
)

__all__ = [
    "ClaimVerifier",
    "ClaimVerificationResult",
    "REGISTERED_TEMPLATES",
    "ALLOWED_FIELD_OPERATORS",
    "CaseCopilot",
    "ClaimLedger",
    "AuditChain",
    "AuditVerificationResult",
    "get_default_audit_key",
    "verify_chain",
]
