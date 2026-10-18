"""SignalGate Dependency Injection Providers

Provides reusable service instances with test substitution support.
"""

from functools import lru_cache
from fastapi import Depends
from backend.app.services.artifacts import ArtifactService
from backend.app.services.overview import OverviewService
from backend.app.services.policies import PolicyService
from backend.app.services.cases import CaseService
from backend.app.services.replay import ReplayService
from backend.app.services.audit import AuditService
from backend.app.services.scoring import ScoringService


@lru_cache()
def get_artifact_service() -> ArtifactService:
    return ArtifactService()


def get_overview_service(
    artifacts: ArtifactService = Depends(get_artifact_service),
) -> OverviewService:
    return OverviewService(artifacts)


def get_policy_service(
    artifacts: ArtifactService = Depends(get_artifact_service),
) -> PolicyService:
    return PolicyService(artifacts)


def get_case_service(
    artifacts: ArtifactService = Depends(get_artifact_service),
) -> CaseService:
    return CaseService(artifacts)


def get_replay_service(
    artifacts: ArtifactService = Depends(get_artifact_service),
) -> ReplayService:
    return ReplayService(artifacts)


def get_audit_service(
    artifacts: ArtifactService = Depends(get_artifact_service),
) -> AuditService:
    return AuditService(artifacts)


def get_scoring_service(
    artifacts: ArtifactService = Depends(get_artifact_service),
) -> ScoringService:
    return ScoringService(artifacts)
