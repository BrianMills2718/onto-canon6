"""Typed report surface for the Phase 13 semantic canonicalization slice.

This report stays narrow and service-backed. It does not create a second repair
runtime. Instead it bundles:

1. the current promoted assertion and role-filler state;
2. any persisted recanonicalization events for that assertion;
3. a small summary over the current repair trail.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from ..core import (
    CanonicalGraphService,
    PromotedGraphAssertionRecord,
    PromotedGraphRecanonicalizationEventRecord,
    PromotedGraphRoleFillerRecord,
    SemanticCanonicalizationService,
)


class SemanticCanonicalizationAssertionBundle(BaseModel):
    """Bundle one promoted assertion with its semantic repair history."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    assertion: PromotedGraphAssertionRecord
    role_fillers: tuple[PromotedGraphRoleFillerRecord, ...] = ()
    events: tuple[PromotedGraphRecanonicalizationEventRecord, ...] = ()
    latest_event: PromotedGraphRecanonicalizationEventRecord | None = None


class SemanticCanonicalizationReportSummary(BaseModel):
    """Summarize the persisted semantic repair state."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    total_assertions: int = Field(ge=0)
    total_recanonicalization_events: int = Field(ge=0)
    total_rewritten_assertions: int = Field(ge=0)


class SemanticCanonicalizationReport(BaseModel):
    """Bundle promoted assertions with their semantic repair history."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    assertion_bundles: tuple[SemanticCanonicalizationAssertionBundle, ...] = ()
    summary: SemanticCanonicalizationReportSummary


class SemanticCanonicalizationReportService:
    """Build inspectable reports over the Phase 13 semantic repair slice."""

    def __init__(
        self,
        *,
        graph_service: CanonicalGraphService | None = None,
        semantic_service: SemanticCanonicalizationService | None = None,
    ) -> None:
        """Use provided services or construct matching config-backed defaults."""

        resolved_graph_service = graph_service
        resolved_semantic_service = semantic_service
        if resolved_graph_service is None and resolved_semantic_service is not None:
            resolved_graph_service = CanonicalGraphService(
                db_path=resolved_semantic_service.db_path
            )
        self._graph_service = resolved_graph_service or CanonicalGraphService()
        self._semantic_service = resolved_semantic_service or SemanticCanonicalizationService(
            db_path=self._graph_service.db_path
        )

    def build_report(self) -> SemanticCanonicalizationReport:
        """Return the current promoted assertions with their repair history."""

        bundles: list[SemanticCanonicalizationAssertionBundle] = []
        total_events = 0
        total_rewritten_assertions = 0
        for assertion in self._graph_service.list_promoted_assertions():
            promotion = self._graph_service.get_promotion_result(
                assertion_id=assertion.assertion_id
            )
            events = tuple(
                self._semantic_service.list_recanonicalization_events(
                    assertion_id=assertion.assertion_id
                )
            )
            total_events += len(events)
            if events:
                total_rewritten_assertions += 1
            bundles.append(
                SemanticCanonicalizationAssertionBundle(
                    assertion=promotion.assertion,
                    role_fillers=promotion.role_fillers,
                    events=events,
                    latest_event=events[-1] if events else None,
                )
            )
        return SemanticCanonicalizationReport(
            assertion_bundles=tuple(bundles),
            summary=SemanticCanonicalizationReportSummary(
                total_assertions=len(bundles),
                total_recanonicalization_events=total_events,
                total_rewritten_assertions=total_rewritten_assertions,
            ),
        )


__all__ = [
    "SemanticCanonicalizationAssertionBundle",
    "SemanticCanonicalizationReport",
    "SemanticCanonicalizationReportService",
    "SemanticCanonicalizationReportSummary",
]
