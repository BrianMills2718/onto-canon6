"""Adapter exports for successor-local producer and consumer boundaries."""

from .digimon_export import (
    DigimonEntityRecord,
    DigimonExportBundle,
    DigimonRelationshipRecord,
    export_for_digimon,
    export_for_digimon_from_db,
    write_digimon_jsonl,
)
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
    "DigimonEntityRecord",
    "DigimonExportBundle",
    "DigimonRelationshipRecord",
    "export_for_digimon",
    "export_for_digimon_from_db",
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
    "write_digimon_jsonl",
]
