"""Service layer for the Phase 8 artifact-lineage slice.

This service composes the review store and artifact store without introducing a
new central workflow object. It exists to keep the first artifact-backed
provenance slice small, typed, and inspectable.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Mapping

from pydantic import JsonValue, TypeAdapter

from ..config import get_config
from ..pipeline import ReviewStore
from .models import (
    ArtifactLineageEdge,
    ArtifactLineageRelationship,
    ArtifactKind,
    ArtifactRecord,
    CandidateArtifactLinkRecord,
    CandidateArtifactSupportKind,
    CandidateLineageReport,
)
from .store import ArtifactStore

logger = logging.getLogger(__name__)
_JSON_OBJECT_ADAPTER = TypeAdapter(dict[str, JsonValue])


class ArtifactLineageService:
    """Register artifacts, record lineage, and build candidate-centered reports."""

    def __init__(self, *, db_path: Path | None = None) -> None:
        """Create a lineage service using the configured review DB when omitted."""

        config = get_config()
        resolved_db_path = db_path or config.review_db_path()
        self._review_store = ReviewStore(resolved_db_path)
        self._artifact_store = ArtifactStore(resolved_db_path)

    @property
    def db_path(self) -> Path:
        """Return the SQLite path shared by review and artifact state."""

        return self._artifact_store.db_path

    def register_artifact(
        self,
        *,
        artifact_kind: ArtifactKind,
        uri: str,
        label: str | None = None,
        metadata: Mapping[str, object] | None = None,
        fingerprint: str | None = None,
    ) -> ArtifactRecord:
        """Persist one first-class artifact record."""

        normalized_uri = _require_non_empty(uri, field_name="uri")
        normalized_fingerprint = fingerprint.strip() if fingerprint is not None else None
        normalized_label = label.strip() if label is not None else None
        normalized_metadata = _JSON_OBJECT_ADAPTER.validate_python(dict(metadata or {}))
        with self._artifact_store.transaction() as conn:
            artifact_id = self._artifact_store.insert_artifact(
                conn,
                artifact_kind=artifact_kind,
                uri=normalized_uri,
                label=normalized_label if normalized_label else None,
                metadata=normalized_metadata,
                fingerprint=normalized_fingerprint if normalized_fingerprint else None,
            )
            artifact = self._artifact_store.get_artifact(conn, artifact_id=artifact_id)
        logger.info(
            "artifact registered artifact_id=%s artifact_kind=%s uri=%s",
            artifact.artifact_id,
            artifact.artifact_kind,
            artifact.uri,
        )
        return artifact

    def add_lineage_edge(
        self,
        *,
        parent_artifact_id: str,
        child_artifact_id: str,
        relationship_type: ArtifactLineageRelationship = "derived_from",
    ) -> ArtifactLineageEdge:
        """Persist one explicit artifact-to-artifact lineage edge."""

        normalized_parent_id = _require_non_empty(
            parent_artifact_id,
            field_name="parent_artifact_id",
        )
        normalized_child_id = _require_non_empty(
            child_artifact_id,
            field_name="child_artifact_id",
        )
        with self._artifact_store.transaction() as conn:
            self._artifact_store.get_artifact(conn, artifact_id=normalized_parent_id)
            self._artifact_store.get_artifact(conn, artifact_id=normalized_child_id)
            edge = self._artifact_store.insert_lineage_edge(
                conn,
                parent_artifact_id=normalized_parent_id,
                child_artifact_id=normalized_child_id,
                relationship_type=relationship_type,
            )
        return edge

    def link_candidate_artifact(
        self,
        *,
        candidate_id: str,
        artifact_id: str,
        support_kind: CandidateArtifactSupportKind,
        reference_detail: str | None = None,
    ) -> CandidateArtifactLinkRecord:
        """Persist one explicit support link from a candidate to an artifact."""

        normalized_candidate_id = _require_non_empty(candidate_id, field_name="candidate_id")
        normalized_artifact_id = _require_non_empty(artifact_id, field_name="artifact_id")
        normalized_detail = reference_detail.strip() if reference_detail is not None else None
        with self._artifact_store.transaction() as conn:
            self._review_store.get_candidate_assertion(conn, candidate_id=normalized_candidate_id)
            artifact = self._artifact_store.get_artifact(conn, artifact_id=normalized_artifact_id)
            _validate_support_kind(support_kind=support_kind, artifact_kind=artifact.artifact_kind)
            link = self._artifact_store.insert_candidate_artifact_link(
                conn,
                candidate_id=normalized_candidate_id,
                artifact_id=normalized_artifact_id,
                support_kind=support_kind,
                reference_detail=normalized_detail if normalized_detail else None,
            )
        return link

    def build_candidate_lineage_report(
        self,
        *,
        candidate_id: str,
    ) -> CandidateLineageReport:
        """Return one inspectable candidate-centered artifact-lineage report."""

        normalized_candidate_id = _require_non_empty(candidate_id, field_name="candidate_id")
        with self._artifact_store.transaction() as conn:
            candidate = self._review_store.get_candidate_assertion(
                conn,
                candidate_id=normalized_candidate_id,
            )
            direct_links = self._artifact_store.list_candidate_artifact_links(
                conn,
                candidate_id=normalized_candidate_id,
            )
            direct_artifact_ids = tuple(link.artifact_id for link in direct_links)
            lineage_edges = self._artifact_store.list_ancestor_edges(
                conn,
                artifact_ids=direct_artifact_ids,
            )
            all_artifact_ids = tuple(
                dict.fromkeys(
                    [
                        *direct_artifact_ids,
                        *(edge.parent_artifact_id for edge in lineage_edges),
                        *(edge.child_artifact_id for edge in lineage_edges),
                    ]
                )
            )
            artifacts = self._artifact_store.list_artifacts(conn, artifact_ids=all_artifact_ids)
        return CandidateLineageReport(
            candidate=candidate,
            direct_artifact_links=direct_links,
            artifacts=artifacts,
            lineage_edges=lineage_edges,
        )


def _require_non_empty(value: str, *, field_name: str) -> str:
    """Normalize one required string and fail loudly when it is blank."""

    normalized = value.strip()
    if not normalized:
        raise ValueError(f"{field_name} must not be blank")
    return normalized


def _validate_support_kind(
    *,
    support_kind: CandidateArtifactSupportKind,
    artifact_kind: ArtifactKind,
) -> None:
    """Require that a candidate support link matches the linked artifact kind."""

    allowed_pairs = {
        ("quoted_from", "source"),
        ("supported_by_dataset", "derived_dataset"),
        ("supported_by_analysis", "analysis_result"),
    }
    if (support_kind, artifact_kind) not in allowed_pairs:
        raise ValueError(
            f"support_kind {support_kind!r} is not valid for artifact_kind {artifact_kind!r}"
        )
