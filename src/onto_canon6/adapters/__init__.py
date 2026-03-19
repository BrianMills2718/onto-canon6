"""Adapter exports for successor-local producer and consumer boundaries."""

from .research_agent_transform import (
    ResearchAgentEntityRecord,
    ResearchAgentRelationship,
    ResearchAgentWhyGameTransformResult,
    ResearchAgentWhyGameTransformService,
)
from .whygame_models import (
    WhyGameImportRequest,
    WhyGameImportResult,
    WhyGameRelationshipFact,
    WhyGameRelationshipRoles,
)
from .whygame_service import WhyGameAdapterError, WhyGameImportService

__all__ = [
    "ResearchAgentEntityRecord",
    "ResearchAgentRelationship",
    "ResearchAgentWhyGameTransformResult",
    "ResearchAgentWhyGameTransformService",
    "WhyGameAdapterError",
    "WhyGameImportRequest",
    "WhyGameImportResult",
    "WhyGameImportService",
    "WhyGameRelationshipFact",
    "WhyGameRelationshipRoles",
]
