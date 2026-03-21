"""Adapter exports for successor-local producer and consumer boundaries."""

from .progressive_adapter import (
    convert_to_candidate_imports,
    submit_progressive_report,
)
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
    "convert_to_candidate_imports",
    "ResearchAgentEntityRecord",
    "ResearchAgentRelationship",
    "ResearchAgentWhyGameTransformResult",
    "ResearchAgentWhyGameTransformService",
    "submit_progressive_report",
    "WhyGameAdapterError",
    "WhyGameImportRequest",
    "WhyGameImportResult",
    "WhyGameImportService",
    "WhyGameRelationshipFact",
    "WhyGameRelationshipRoles",
]
