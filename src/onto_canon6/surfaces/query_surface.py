"""Shared read-only query service over promoted knowledge.

This service intentionally answers a small set of deterministic browse/search
questions over promoted state without turning `onto-canon6` into a general
retrieval runtime.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from ..artifacts import ArtifactLineageService, CandidateLineageReport
from ..config import get_config
from ..core import (
    CanonicalGraphPromotionNotFoundError,
    CanonicalGraphService,
    IdentityBundleRecord,
    IdentityNotFoundError,
    IdentityService,
    PromotedGraphAssertionRecord,
    PromotedGraphEntityRecord,
)
from ..extensions.epistemic import EpistemicService
from ..pipeline import CandidateAssertionRecord, ReviewService
from .epistemic_report import EpistemicReportService
from .query_models import (
    AssertionSearchRequest,
    AssertionSearchResult,
    EntityDetail,
    EntityMatchReason,
    EntitySearchRequest,
    EntitySearchResult,
    EvidenceBundle,
    GetEntityRequest,
    GetEvidenceRequest,
    GetPromotedAssertionRequest,
    PromotedAssertionDetail,
)


class QuerySurfaceError(RuntimeError):
    """Base error for query-surface failures."""


class QuerySurfaceNotFoundError(QuerySurfaceError):
    """Raised when a requested entity or assertion does not exist."""


class QuerySurfaceConflictError(QuerySurfaceError):
    """Raised when stored provenance/query state is internally inconsistent."""


@dataclass(frozen=True)
class _EntityContext:
    """Internal entity context used to build search/detail responses."""

    entity: PromotedGraphEntityRecord
    names: tuple[str, ...]
    identity_member_names: dict[str, tuple[str, ...]]
    identity_bundle: IdentityBundleRecord | None
    linked_assertion_ids: tuple[str, ...]
    identity_linked_assertion_ids: tuple[str, ...]


class QuerySurfaceService:
    """Provide deterministic read-only query operations over promoted state."""

    def __init__(
        self,
        *,
        graph_service: CanonicalGraphService | None = None,
        identity_service: IdentityService | None = None,
        review_service: ReviewService | None = None,
        artifact_service: ArtifactLineageService | None = None,
        epistemic_report_service: EpistemicReportService | None = None,
    ) -> None:
        """Use provided services or construct matching config-backed defaults."""

        config = get_config()
        resolved_db_path = config.review_db_path()
        self._graph_service = graph_service or CanonicalGraphService(db_path=resolved_db_path)
        active_db_path = self._graph_service.db_path
        self._identity_service = identity_service or IdentityService(db_path=active_db_path)
        self._review_service = review_service or ReviewService(db_path=active_db_path)
        self._artifact_service = artifact_service or ArtifactLineageService(db_path=active_db_path)
        self._epistemic_report_service = epistemic_report_service or EpistemicReportService(
            epistemic_service=EpistemicService(db_path=active_db_path)
        )

    @property
    def db_path(self) -> Path:
        """Return the shared SQLite path used by the query surface."""

        return self._graph_service.db_path

    def search_entities(
        self,
        request: EntitySearchRequest,
    ) -> tuple[EntitySearchResult, ...]:
        """Return entity matches in deterministic ranking order."""

        query = request.query.strip()
        if not query:
            raise ValueError("query must be a non-empty string")
        needle = query.casefold()
        contexts = self._build_entity_contexts()
        matches: list[tuple[int, str, str, EntitySearchResult]] = []
        for context in contexts.values():
            if request.entity_type and context.entity.entity_type != request.entity_type:
                continue
            match_reason = _match_entity_query(
                needle=needle,
                context=context,
            )
            if match_reason is None:
                continue
            result = EntitySearchResult(
                identity_id=(
                    context.identity_bundle.identity.identity_id
                    if context.identity_bundle is not None
                    else None
                ),
                entity_id=context.entity.entity_id,
                display_label=_choose_display_label(context),
                entity_type=context.entity.entity_type,
                match_reason=match_reason,
            )
            matches.append(
                (
                    _MATCH_RANK[match_reason],
                    0 if _any_exact_match(needle, context.names) else 1,
                    0 if _is_canonical_context(context) else 1,
                    result.display_label.casefold(),
                    result.entity_id,
                    result,
                )
            )
        matches.sort()
        return tuple(result for *_ignored, result in matches[: request.limit])

    def get_entity(self, request: GetEntityRequest) -> EntityDetail:
        """Return one detailed entity view by entity or identity id."""

        contexts = self._build_entity_contexts()
        if request.identity_id is not None:
            try:
                identity_bundle = self._identity_service.get_identity_bundle(
                    identity_id=request.identity_id
                )
            except IdentityNotFoundError as exc:
                raise QuerySurfaceNotFoundError(str(exc)) from exc
            canonical_entity_id = _choose_canonical_entity_id(identity_bundle)
            if canonical_entity_id not in contexts:
                raise QuerySurfaceConflictError(
                    f"identity {request.identity_id} points at missing entity {canonical_entity_id}"
                )
            context = contexts[canonical_entity_id]
            if context.identity_bundle is None:
                context = _EntityContext(
                    entity=context.entity,
                    names=context.names,
                    identity_member_names=context.identity_member_names,
                    identity_bundle=identity_bundle,
                    linked_assertion_ids=context.linked_assertion_ids,
                    identity_linked_assertion_ids=_collect_identity_linked_assertion_ids(
                        identity_bundle=identity_bundle,
                        entity_assertion_map={context.entity.entity_id: context.linked_assertion_ids},
                    ),
                )
        else:
            entity_id = request.entity_id or ""
            try:
                context = contexts[entity_id]
            except KeyError as exc:
                raise QuerySurfaceNotFoundError(
                    f"promoted entity not found: {entity_id}"
                ) from exc
        return EntityDetail(
            entity=context.entity,
            display_label=_choose_display_label(context),
            names=context.names,
            identity_bundle=context.identity_bundle,
            linked_assertions=tuple(
                self._build_assertion_summary(assertion_id=assertion_id)
                for assertion_id in _collect_linked_assertion_ids(context)
            ),
        )

    def search_promoted_assertions(
        self,
        request: AssertionSearchRequest,
    ) -> tuple[AssertionSearchResult, ...]:
        """Return promoted-assertion matches in deterministic order."""

        predicate = request.predicate.strip() if request.predicate is not None else None
        entity_id = request.entity_id.strip() if request.entity_id is not None else None
        text_query = request.text_query.strip().casefold() if request.text_query is not None else None
        results: list[AssertionSearchResult] = []
        for assertion in self._graph_service.list_promoted_assertions():
            entity_ids = _assertion_entity_ids(assertion)
            if predicate is not None and assertion.predicate != predicate:
                continue
            if entity_id is not None and entity_id not in entity_ids:
                continue
            if text_query is not None:
                claim_text = (assertion.claim_text or "").casefold()
                if text_query not in claim_text:
                    continue
            results.append(self._build_assertion_summary(assertion_id=assertion.assertion_id))
        return tuple(results[: request.limit])

    def get_promoted_assertion(
        self,
        request: GetPromotedAssertionRequest,
    ) -> PromotedAssertionDetail:
        """Return one promoted assertion with candidate, epistemic, and evidence context."""

        try:
            promotion = self._graph_service.get_promotion_result(assertion_id=request.assertion_id)
        except CanonicalGraphPromotionNotFoundError as exc:
            raise QuerySurfaceNotFoundError(str(exc)) from exc
        candidate = self._review_service.get_candidate_assertion(
            candidate_id=promotion.assertion.source_candidate_id
        )
        evidence = self._build_evidence_bundle(assertion_id=request.assertion_id, candidate=candidate)
        epistemic_report = self._epistemic_report_service.build_promoted_assertion_report(
            assertion_id=request.assertion_id
        )
        return PromotedAssertionDetail(
            promotion=promotion,
            source_candidate=candidate,
            epistemic_report=epistemic_report,
            evidence=evidence,
        )

    def get_evidence(self, request: GetEvidenceRequest) -> EvidenceBundle:
        """Return one evidence/provenance bundle for a promoted assertion."""

        try:
            promotion = self._graph_service.get_promotion_result(assertion_id=request.assertion_id)
        except CanonicalGraphPromotionNotFoundError as exc:
            raise QuerySurfaceNotFoundError(str(exc)) from exc
        candidate = self._review_service.get_candidate_assertion(
            candidate_id=promotion.assertion.source_candidate_id
        )
        return self._build_evidence_bundle(assertion_id=request.assertion_id, candidate=candidate)

    def _build_assertion_summary(self, *, assertion_id: str) -> AssertionSearchResult:
        """Build one summary result for a promoted assertion identifier."""

        assertion = self._graph_service.get_promoted_assertion(assertion_id=assertion_id)
        epistemic_report = self._epistemic_report_service.build_promoted_assertion_report(
            assertion_id=assertion_id
        )
        confidence_score = (
            epistemic_report.confidence.confidence_score
            if epistemic_report.confidence is not None
            else None
        )
        return AssertionSearchResult(
            assertion_id=assertion.assertion_id,
            predicate=assertion.predicate,
            claim_text=assertion.claim_text,
            entity_ids=_assertion_entity_ids(assertion),
            confidence_score=confidence_score,
            epistemic_status=epistemic_report.epistemic_status,
        )

    def _build_evidence_bundle(
        self,
        *,
        assertion_id: str,
        candidate: CandidateAssertionRecord,
    ) -> EvidenceBundle:
        """Build one evidence/provenance bundle for a promoted assertion."""

        lineage_report: CandidateLineageReport = self._artifact_service.build_candidate_lineage_report(
            candidate_id=candidate.candidate_id
        )
        if lineage_report.candidate.candidate_id != candidate.candidate_id:
            raise QuerySurfaceConflictError(
                f"lineage report candidate mismatch for assertion {assertion_id}"
            )
        source_artifact = candidate.provenance.source_artifact
        return EvidenceBundle(
            assertion_id=assertion_id,
            candidate=candidate,
            source_artifact=source_artifact,
            claim_text=candidate.claim_text,
            source_text=source_artifact.content_text,
            evidence_spans=candidate.evidence_spans,
            artifact_links=lineage_report.direct_artifact_links,
            artifacts=lineage_report.artifacts,
            lineage_edges=lineage_report.lineage_edges,
        )

    def _build_entity_contexts(self) -> dict[str, _EntityContext]:
        """Build entity contexts from promoted assertions and identity state."""

        assertions = tuple(self._graph_service.list_promoted_assertions())
        entity_name_map = _build_entity_name_map(assertions)
        entity_assertion_map = _build_entity_assertion_map(assertions)
        identity_bundles = tuple(self._identity_service.list_identities())
        identity_by_entity_id = {
            membership.entity_id: bundle
            for bundle in identity_bundles
            for membership in bundle.memberships
        }
        all_entities = _list_all_entities(self._graph_service)
        return {
            entity.entity_id: _EntityContext(
                entity=entity,
                names=tuple(
                    sorted(
                        set(entity_name_map.get(entity.entity_id, ())) or {entity.entity_id}
                    )
                ),
                identity_member_names={
                    membership.entity_id: tuple(
                        sorted(
                            set(entity_name_map.get(membership.entity_id, ()))
                            or {membership.entity_id}
                        )
                    )
                    for membership in identity_by_entity_id.get(entity.entity_id, ()).memberships
                }
                if identity_by_entity_id.get(entity.entity_id) is not None
                else {},
                identity_bundle=identity_by_entity_id.get(entity.entity_id),
                linked_assertion_ids=entity_assertion_map.get(entity.entity_id, ()),
                identity_linked_assertion_ids=_collect_identity_linked_assertion_ids(
                    identity_bundle=identity_by_entity_id.get(entity.entity_id),
                    entity_assertion_map=entity_assertion_map,
                ),
            )
            for entity in all_entities
        }


_MATCH_RANK: dict[EntityMatchReason, int] = {
    "canonical_exact": 0,
    "alias_exact": 1,
    "prefix": 2,
    "substring": 3,
}


def _list_all_entities(
    graph_service: CanonicalGraphService,
) -> tuple[PromotedGraphEntityRecord, ...]:
    """Return all promoted entities in deterministic order."""

    rows = graph_service._store.transaction()
    with rows as conn:
        fetched = conn.execute(
            """
            SELECT entity_id, entity_type, first_candidate_id, created_at
            FROM promoted_graph_entities
            ORDER BY created_at, entity_id
            """
        ).fetchall()
    return tuple(
        PromotedGraphEntityRecord(
            entity_id=str(row["entity_id"]),
            entity_type=str(row["entity_type"]) if row["entity_type"] is not None else None,
            first_candidate_id=str(row["first_candidate_id"]),
            created_at=str(row["created_at"]),
        )
        for row in fetched
    )


def _build_entity_name_map(
    assertions: Iterable[PromotedGraphAssertionRecord],
) -> dict[str, tuple[str, ...]]:
    """Map each entity id to the human-readable names seen in assertion roles."""

    names: dict[str, set[str]] = defaultdict(set)
    for assertion in assertions:
        roles = assertion.normalized_body.get("roles")
        if not isinstance(roles, dict):
            continue
        for fillers in roles.values():
            if not isinstance(fillers, list):
                continue
            for filler in fillers:
                if not isinstance(filler, dict):
                    continue
                entity_id = filler.get("entity_id")
                name = filler.get("name")
                if isinstance(entity_id, str) and entity_id.strip():
                    if isinstance(name, str) and name.strip():
                        names[entity_id].add(name.strip())
    return {
        entity_id: tuple(sorted(entity_names))
        for entity_id, entity_names in names.items()
    }


def _build_entity_assertion_map(
    assertions: Iterable[PromotedGraphAssertionRecord],
) -> dict[str, tuple[str, ...]]:
    """Map each entity id to linked promoted assertion ids."""

    linked_ids: dict[str, list[str]] = defaultdict(list)
    for assertion in assertions:
        for entity_id in _assertion_entity_ids(assertion):
            linked_ids[entity_id].append(assertion.assertion_id)
    return {
        entity_id: tuple(ids)
        for entity_id, ids in linked_ids.items()
    }


def _assertion_entity_ids(assertion: PromotedGraphAssertionRecord) -> tuple[str, ...]:
    """Extract linked entity ids from one promoted assertion body."""

    entity_ids: list[str] = []
    roles = assertion.normalized_body.get("roles")
    if not isinstance(roles, dict):
        return ()
    for fillers in roles.values():
        if not isinstance(fillers, list):
            continue
        for filler in fillers:
            if not isinstance(filler, dict):
                continue
            entity_id = filler.get("entity_id")
            if isinstance(entity_id, str) and entity_id.strip():
                entity_ids.append(entity_id)
    return tuple(dict.fromkeys(entity_ids))


def _choose_canonical_entity_id(identity_bundle: IdentityBundleRecord) -> str:
    """Return the canonical entity id for one identity bundle."""

    for membership in identity_bundle.memberships:
        if membership.membership_kind == "canonical":
            return membership.entity_id
    if identity_bundle.memberships:
        return identity_bundle.memberships[0].entity_id
    raise QuerySurfaceConflictError(
        f"identity {identity_bundle.identity.identity_id} has no memberships"
    )


def _choose_display_label(context: _EntityContext) -> str:
    """Choose the best display label for one entity context."""

    if context.identity_bundle is not None and context.identity_bundle.identity.display_label:
        return context.identity_bundle.identity.display_label
    if context.names:
        return context.names[0]
    return context.entity.entity_id


def _is_canonical_context(context: _EntityContext) -> bool:
    """Return whether this context is the canonical member of its identity."""

    if context.identity_bundle is None:
        return True
    return context.entity.entity_id == _choose_canonical_entity_id(context.identity_bundle)


def _collect_linked_assertion_ids(context: _EntityContext) -> tuple[str, ...]:
    """Return direct or identity-cluster assertion ids in stable order."""

    if context.identity_bundle is None or not context.identity_linked_assertion_ids:
        return context.linked_assertion_ids
    return context.identity_linked_assertion_ids


def _collect_identity_linked_assertion_ids(
    *,
    identity_bundle: IdentityBundleRecord | None,
    entity_assertion_map: dict[str, tuple[str, ...]],
) -> tuple[str, ...]:
    """Return all assertion ids linked across one identity cluster."""

    if identity_bundle is None:
        return ()
    ordered_ids: list[str] = []
    seen: set[str] = set()
    for membership in identity_bundle.memberships:
        for linked_id in entity_assertion_map.get(membership.entity_id, ()):
            if linked_id not in seen:
                seen.add(linked_id)
                ordered_ids.append(linked_id)
    return tuple(ordered_ids)


def _match_entity_query(
    *,
    needle: str,
    context: _EntityContext,
) -> EntityMatchReason | None:
    """Return the best deterministic match reason for one entity context."""

    identity_bundle = context.identity_bundle
    canonical_names: set[str] = set()
    alias_names: set[str] = set()

    if identity_bundle is not None:
        canonical_entity_id = _choose_canonical_entity_id(identity_bundle)
        if identity_bundle.identity.display_label:
            canonical_names.add(identity_bundle.identity.display_label)
        if context.entity.entity_id == canonical_entity_id:
            canonical_names.update(context.names)
        else:
            alias_names.update(context.names)
        for membership in identity_bundle.memberships:
            if membership.entity_id == context.entity.entity_id:
                continue
            member_names = context.identity_member_names.get(membership.entity_id, ())
            if membership.membership_kind == "canonical":
                canonical_names.update(member_names)
            else:
                alias_names.update(member_names)
    else:
        canonical_names.update(context.names)

    if _any_exact_match(needle, canonical_names):
        return "canonical_exact"
    if _any_exact_match(needle, alias_names):
        return "alias_exact"
    if _any_startswith_match(needle, canonical_names | alias_names):
        return "prefix"
    if _any_contains_match(needle, canonical_names | alias_names):
        return "substring"
    return None


def _any_exact_match(needle: str, haystack: Iterable[str]) -> bool:
    """Return true when any candidate matches exactly."""

    return any(candidate.casefold() == needle for candidate in haystack if candidate)


def _any_startswith_match(needle: str, haystack: Iterable[str]) -> bool:
    """Return true when any candidate starts with the query."""

    return any(candidate.casefold().startswith(needle) for candidate in haystack if candidate)


def _any_contains_match(needle: str, haystack: Iterable[str]) -> bool:
    """Return true when any candidate contains the query."""

    return any(needle in candidate.casefold() for candidate in haystack if candidate)


__all__ = [
    "QuerySurfaceConflictError",
    "QuerySurfaceError",
    "QuerySurfaceNotFoundError",
    "QuerySurfaceService",
]
