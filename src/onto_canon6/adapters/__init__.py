"""Adapter exports for successor-local producer and consumer boundaries."""

from .whygame_models import (
    WhyGameImportRequest,
    WhyGameImportResult,
    WhyGameRelationshipFact,
    WhyGameRelationshipRoles,
)
from .whygame_service import WhyGameAdapterError, WhyGameImportService

__all__ = [
    "WhyGameAdapterError",
    "WhyGameImportRequest",
    "WhyGameImportResult",
    "WhyGameImportService",
    "WhyGameRelationshipFact",
    "WhyGameRelationshipRoles",
]
