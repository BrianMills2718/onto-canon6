"""Thin FastMCP surface for the Phase 14 successor recovery slice.

This server intentionally stays service-backed. It does not recreate the v1
monolithic runtime. Each tool:

1. validates explicit inputs;
2. builds the proved successor services over the configured SQLite state;
3. delegates to those services directly;
4. returns JSON-serializable typed records.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from fastmcp import FastMCP

from .adapters import WhyGameImportService
from .config import get_config
from .core import CanonicalGraphService
from .pipeline import OverlayApplicationService, ReviewService
from .surfaces import (
    AssertionBrowseRequest,
    AssertionSearchRequest,
    EntityBrowseRequest,
    EntitySearchRequest,
    GetEntityRequest,
    GetEvidenceRequest,
    GetPromotedAssertionRequest,
    GovernedWorkflowBundleService,
    QuerySurfaceService,
)

_CONFIG = get_config()
mcp = FastMCP(_CONFIG.project.name)


def _review_service(*, review_db_path: str | None = None, overlay_root: str | None = None) -> ReviewService:
    """Build one review service for the current tool call."""

    return ReviewService(
        db_path=Path(review_db_path).expanduser() if review_db_path is not None else None,
        overlay_root=Path(overlay_root).expanduser() if overlay_root is not None else None,
    )


def _overlay_service(
    *,
    review_db_path: str | None = None,
    overlay_root: str | None = None,
) -> OverlayApplicationService:
    """Build one overlay service for the current tool call."""

    return OverlayApplicationService(
        db_path=Path(review_db_path).expanduser() if review_db_path is not None else None,
        overlay_root=Path(overlay_root).expanduser() if overlay_root is not None else None,
    )


def _graph_service(*, review_db_path: str | None = None) -> CanonicalGraphService:
    """Build one graph service for the current tool call."""

    return CanonicalGraphService(
        db_path=Path(review_db_path).expanduser() if review_db_path is not None else None,
    )


def _bundle_service(*, review_db_path: str | None = None) -> GovernedWorkflowBundleService:
    """Build one governed-bundle export service for the current tool call."""

    return GovernedWorkflowBundleService(
        review_service=_review_service(review_db_path=review_db_path),
    )


def _query_service(*, review_db_path: str | None = None) -> QuerySurfaceService:
    """Build one read-only query surface for the current tool call."""

    return QuerySurfaceService(
        graph_service=_graph_service(review_db_path=review_db_path),
        review_service=_review_service(review_db_path=review_db_path),
    )


def _whygame_service(
    *,
    review_db_path: str | None = None,
    overlay_root: str | None = None,
) -> WhyGameImportService:
    """Build one WhyGame import service for the current tool call."""

    review_service = _review_service(
        review_db_path=review_db_path,
        overlay_root=overlay_root,
    )
    return WhyGameImportService(review_service=review_service)


def canon6_import_whygame_relationships(
    facts: list[dict[str, object]],
    submitted_by: str,
    source_ref: str,
    source_label: str | None = None,
    source_metadata: dict[str, object] | None = None,
    register_artifact: bool | None = None,
    artifact_uri: str | None = None,
    artifact_label: str | None = None,
    review_db_path: str | None = None,
    overlay_root: str | None = None,
) -> dict[str, Any]:
    """Import typed WhyGame relationship facts into reviewable candidate assertions."""

    service = _whygame_service(
        review_db_path=review_db_path,
        overlay_root=overlay_root,
    )
    request = service.build_default_request(
        facts=facts,
        submitted_by=submitted_by,
        source_ref=source_ref,
        source_label=source_label,
        source_metadata=source_metadata,
        register_artifact=register_artifact,
        artifact_uri=artifact_uri,
        artifact_label=artifact_label,
    )
    return service.import_request(request=request).model_dump(mode="json")


def canon6_list_candidates(
    review_status: str | None = None,
    validation_status: str | None = None,
    proposal_status: str | None = None,
    profile_id: str | None = None,
    profile_version: str | None = None,
    review_db_path: str | None = None,
) -> list[dict[str, Any]]:
    """List persisted candidate assertions with explicit review filters."""

    service = _review_service(review_db_path=review_db_path)
    return [
        candidate.model_dump(mode="json")
        for candidate in service.list_candidate_assertions(
            review_status_filter=review_status,  # type: ignore[arg-type]
            validation_status_filter=validation_status,  # type: ignore[arg-type]
            proposal_status_filter=proposal_status,  # type: ignore[arg-type]
            profile_id=profile_id,
            profile_version=profile_version,
        )
    ]


def canon6_list_proposals(
    status: str | None = None,
    profile_id: str | None = None,
    profile_version: str | None = None,
    review_db_path: str | None = None,
) -> list[dict[str, Any]]:
    """List persisted ontology proposals with explicit filters."""

    service = _review_service(review_db_path=review_db_path)
    return [
        proposal.model_dump(mode="json")
        for proposal in service.list_proposals(
            status_filter=status,  # type: ignore[arg-type]
            profile_id=profile_id,
            profile_version=profile_version,
        )
    ]


def canon6_review_candidate(
    candidate_id: str,
    decision: str,
    actor_id: str,
    note_text: str | None = None,
    review_db_path: str | None = None,
) -> dict[str, Any]:
    """Record one explicit candidate review decision."""

    service = _review_service(review_db_path=review_db_path)
    reviewed = service.review_candidate(
        candidate_id=candidate_id,
        decision=decision,  # type: ignore[arg-type]
        actor_id=actor_id,
        note_text=note_text,
    )
    return reviewed.model_dump(mode="json")


def canon6_review_proposal(
    proposal_id: str,
    decision: str,
    actor_id: str,
    note_text: str | None = None,
    acceptance_policy: str | None = None,
    review_db_path: str | None = None,
) -> dict[str, Any]:
    """Record one explicit ontology proposal review decision."""

    service = _review_service(review_db_path=review_db_path)
    reviewed = service.review_proposal(
        proposal_id=proposal_id,
        decision=decision,  # type: ignore[arg-type]
        actor_id=actor_id,
        note_text=note_text,
        acceptance_policy=acceptance_policy,  # type: ignore[arg-type]
    )
    return reviewed.model_dump(mode="json")


def canon6_apply_overlay(
    proposal_id: str,
    actor_id: str,
    review_db_path: str | None = None,
    overlay_root: str | None = None,
) -> dict[str, Any]:
    """Apply one accepted proposal into its target overlay."""

    service = _overlay_service(
        review_db_path=review_db_path,
        overlay_root=overlay_root,
    )
    return service.apply_proposal_to_overlay(
        proposal_id=proposal_id,
        applied_by=actor_id,
    ).model_dump(mode="json")


def canon6_promote_candidate(
    candidate_id: str,
    actor_id: str,
    review_db_path: str | None = None,
) -> dict[str, Any]:
    """Promote one accepted candidate into the durable graph slice."""

    service = _graph_service(review_db_path=review_db_path)
    return service.promote_candidate(
        candidate_id=candidate_id,
        promoted_by=actor_id,
    ).model_dump(mode="json")


def canon6_export_governed_bundle(
    profile_id: str | None = None,
    profile_version: str | None = None,
    candidate_ids: list[str] | None = None,
    review_db_path: str | None = None,
) -> dict[str, Any]:
    """Export the governed workflow bundle for agents and downstream consumers."""

    service = _bundle_service(review_db_path=review_db_path)
    return service.build_bundle(
        profile_id=profile_id,
        profile_version=profile_version,
        candidate_ids=tuple(candidate_ids or ()),
    ).model_dump(mode="json")


def canon6_list_entities(
    entity_type: str | None = None,
    limit: int = 50,
    review_db_path: str | None = None,
) -> list[dict[str, Any]]:
    """Browse promoted entities over the read-only query surface."""

    service = _query_service(review_db_path=review_db_path)
    return [
        result.model_dump(mode="json")
        for result in service.list_entities(
            EntityBrowseRequest(entity_type=entity_type, limit=limit)
        )
    ]



def canon6_search_entities(
    query: str,
    entity_type: str | None = None,
    limit: int = 20,
    review_db_path: str | None = None,
) -> list[dict[str, Any]]:
    """Search promoted entities and identity aliases over the read-only query surface."""

    service = _query_service(review_db_path=review_db_path)
    return [
        result.model_dump(mode="json")
        for result in service.search_entities(
            EntitySearchRequest(query=query, entity_type=entity_type, limit=limit)
        )
    ]


def canon6_get_entity(
    entity_id: str | None = None,
    identity_id: str | None = None,
    review_db_path: str | None = None,
) -> dict[str, Any]:
    """Return one promoted entity or identity detail view."""

    service = _query_service(review_db_path=review_db_path)
    return service.get_entity(
        GetEntityRequest(entity_id=entity_id, identity_id=identity_id)
    ).model_dump(mode="json")


def canon6_list_promoted_assertions(
    predicate: str | None = None,
    entity_id: str | None = None,
    source_ref: str | None = None,
    source_kind: str | None = None,
    limit: int = 50,
    review_db_path: str | None = None,
) -> list[dict[str, Any]]:
    """Browse promoted assertions over the read-only query surface."""

    service = _query_service(review_db_path=review_db_path)
    return [
        result.model_dump(mode="json")
        for result in service.list_promoted_assertions(
            AssertionBrowseRequest(
                predicate=predicate,
                entity_id=entity_id,
                source_ref=source_ref,
                source_kind=source_kind,
                limit=limit,
            )
        )
    ]



def canon6_search_promoted_assertions(
    predicate: str | None = None,
    entity_id: str | None = None,
    text_query: str | None = None,
    source_ref: str | None = None,
    source_kind: str | None = None,
    limit: int = 20,
    review_db_path: str | None = None,
) -> list[dict[str, Any]]:
    """Search promoted assertions by predicate, linked entity, claim text, or source."""

    service = _query_service(review_db_path=review_db_path)
    return [
        result.model_dump(mode="json")
        for result in service.search_promoted_assertions(
            AssertionSearchRequest(
                predicate=predicate,
                entity_id=entity_id,
                text_query=text_query,
                source_ref=source_ref,
                source_kind=source_kind,
                limit=limit,
            )
        )
    ]


def canon6_get_promoted_assertion(
    assertion_id: str,
    review_db_path: str | None = None,
) -> dict[str, Any]:
    """Return one promoted assertion with source, epistemic, and evidence context."""

    service = _query_service(review_db_path=review_db_path)
    return service.get_promoted_assertion(
        GetPromotedAssertionRequest(assertion_id=assertion_id)
    ).model_dump(mode="json")


def canon6_get_evidence(
    assertion_id: str,
    review_db_path: str | None = None,
) -> dict[str, Any]:
    """Return evidence and lineage context for one promoted assertion."""

    service = _query_service(review_db_path=review_db_path)
    return service.get_evidence(
        GetEvidenceRequest(assertion_id=assertion_id)
    ).model_dump(mode="json")


def main() -> None:
    """Run the thin MCP server using the configured transport."""

    mcp.run(transport=_CONFIG.mcp.transport)


mcp.tool()(canon6_import_whygame_relationships)
mcp.tool()(canon6_list_candidates)
mcp.tool()(canon6_list_proposals)
mcp.tool()(canon6_review_candidate)
mcp.tool()(canon6_review_proposal)
mcp.tool()(canon6_apply_overlay)
mcp.tool()(canon6_promote_candidate)
mcp.tool()(canon6_export_governed_bundle)
mcp.tool()(canon6_list_entities)
mcp.tool()(canon6_search_entities)
mcp.tool()(canon6_get_entity)
mcp.tool()(canon6_list_promoted_assertions)
mcp.tool()(canon6_search_promoted_assertions)
mcp.tool()(canon6_get_promoted_assertion)
mcp.tool()(canon6_get_evidence)


if __name__ == "__main__":
    main()
