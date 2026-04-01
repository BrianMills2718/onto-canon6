"""WhyGame relationship adapter for the Phase 14 recovery slice.

This service deliberately avoids reconstructing the v1 import runtime. It
recovers only one explicit path:

1. validate a typed WhyGame relationship batch;
2. convert it into candidate assertions under a local WhyGame profile;
3. optionally register the WhyGame graph or batch as an analysis artifact;
4. keep the imported results visible through the existing review and governed
   bundle surfaces.
"""

from __future__ import annotations

import logging
import re
from typing import Mapping, Sequence

try:
    from data_contracts import boundary
except ImportError:
    def boundary(**kwargs):
        def decorator(fn):
            return fn
        return decorator
from pydantic import JsonValue, TypeAdapter

from ..artifacts import ArtifactLineageService
from ..config import get_config
from ..pipeline import CandidateSubmissionResult, ProfileRef, ReviewService
from .whygame_models import WhyGameImportRequest, WhyGameImportResult, WhyGameRelationshipFact

logger = logging.getLogger(__name__)
_JSON_OBJECT_ADAPTER = TypeAdapter(dict[str, JsonValue])


class WhyGameAdapterError(RuntimeError):
    """Raised when the successor-local WhyGame adapter cannot import a request."""


class WhyGameImportService:
    """Import WhyGame relationship facts into the successor review flow."""

    def __init__(
        self,
        *,
        review_service: ReviewService | None = None,
        artifact_service: ArtifactLineageService | None = None,
    ) -> None:
        """Construct the adapter with config-backed review and artifact services."""

        self._review_service = review_service or ReviewService()
        self._artifact_service = artifact_service or ArtifactLineageService(
            db_path=self._review_service.store.db_path,
        )
        self._config = get_config()

    @property
    def review_service(self) -> ReviewService:
        """Expose the underlying review service for notebook inspection."""

        return self._review_service

    @property
    def artifact_service(self) -> ArtifactLineageService:
        """Expose the underlying artifact service for notebook inspection."""

        return self._artifact_service

    def build_default_request(
        self,
        *,
        facts: Sequence[Mapping[str, object]],
        submitted_by: str,
        source_ref: str,
        source_label: str | None = None,
        source_metadata: Mapping[str, object] | None = None,
        register_artifact: bool | None = None,
        artifact_uri: str | None = None,
        artifact_label: str | None = None,
    ) -> WhyGameImportRequest:
        """Build one typed request using repo-configured WhyGame defaults."""

        whygame_config = self._config.adapters.whygame
        return WhyGameImportRequest(
            profile=ProfileRef(
                profile_id=whygame_config.default_profile_id,
                profile_version=whygame_config.default_profile_version,
            ),
            submitted_by=_require_non_empty(submitted_by, field_name="submitted_by"),
            source_ref=_require_non_empty(source_ref, field_name="source_ref"),
            source_label=source_label.strip() if source_label is not None else None,
            source_metadata=_JSON_OBJECT_ADAPTER.validate_python(dict(source_metadata or {})),
            facts=tuple(WhyGameRelationshipFact.model_validate(fact) for fact in facts),
            register_artifact=(
                whygame_config.register_artifact_by_default
                if register_artifact is None
                else register_artifact
            ),
            artifact_uri=artifact_uri.strip() if artifact_uri is not None else None,
            artifact_label=artifact_label.strip() if artifact_label is not None else None,
        )

    @boundary(
        name="onto-canon6.whygame_import",
        version="0.1.0",
        producer="whygame",
        consumers=["onto-canon6"],
    )
    def import_request(
        self,
        *,
        request: WhyGameImportRequest,
    ) -> WhyGameImportResult:
        """Import one typed WhyGame request into the review pipeline."""

        artifact = (
            self._artifact_service.register_artifact(
                artifact_kind="analysis_result",
                uri=request.artifact_uri or request.source_ref,
                label=request.artifact_label or request.source_label,
                metadata={
                    "adapter": "whygame_relationship_import",
                    "profile_id": request.profile.profile_id,
                    "profile_version": request.profile.profile_version,
                    "source_ref": request.source_ref,
                    "fact_count": len(request.facts),
                },
            )
            if request.register_artifact
            else None
        )
        submissions: list[CandidateSubmissionResult] = []
        artifact_links = []
        whygame_config = self._config.adapters.whygame
        for fact in request.facts:
            candidate_submission = self._review_service.submit_candidate_assertion(
                payload=_build_candidate_payload(fact),
                profile_id=request.profile.profile_id,
                profile_version=request.profile.profile_version,
                submitted_by=request.submitted_by,
                source_kind=whygame_config.source_kind,
                source_ref=request.source_ref,
                source_label=request.source_label,
                source_metadata=_build_source_metadata(
                    request_metadata=request.source_metadata,
                    fact=fact,
                ),
                claim_text=_build_claim_text(fact),
            )
            submissions.append(candidate_submission)
            if artifact is not None:
                artifact_links.append(
                    self._artifact_service.link_candidate_artifact(
                        candidate_id=candidate_submission.candidate.candidate_id,
                        artifact_id=artifact.artifact_id,
                        support_kind="supported_by_analysis",
                        reference_detail=fact.id,
                    )
                )
        logger.info(
            "whygame import completed submitted_by=%s source_ref=%s fact_count=%d artifact_registered=%s",
            request.submitted_by,
            request.source_ref,
            len(request.facts),
            artifact is not None,
        )
        return WhyGameImportResult(
            profile=request.profile,
            artifact=artifact,
            submissions=tuple(submissions),
            artifact_links=tuple(artifact_links),
        )


def _build_candidate_payload(fact: WhyGameRelationshipFact) -> dict[str, JsonValue]:
    """Map one WhyGame relationship fact into the local successor assertion shape."""

    source_name = fact.roles.from_.strip()
    target_name = fact.roles.to.strip()
    relationship_text = fact.roles.relationship.strip()
    return {
        "predicate": "whygame:relationship",
        "roles": {
            "source_concept": [
                {
                    "kind": "entity",
                    "entity_id": _entity_id_for_name(source_name),
                    "entity_type": "whygame:Concept",
                    "name": source_name,
                }
            ],
            "target_concept": [
                {
                    "kind": "entity",
                    "entity_id": _entity_id_for_name(target_name),
                    "entity_type": "whygame:Concept",
                    "name": target_name,
                }
            ],
            "relationship_label": [
                {
                    "kind": "value",
                    "value_kind": "string",
                    "value": relationship_text,
                }
            ],
        },
    }


def _build_claim_text(fact: WhyGameRelationshipFact) -> str:
    """Render one readable claim gloss from the WhyGame relationship triple."""

    return f"{fact.roles.from_.strip()} {fact.roles.relationship.strip()} {fact.roles.to.strip()}."


def _build_source_metadata(
    *,
    request_metadata: Mapping[str, JsonValue],
    fact: WhyGameRelationshipFact,
) -> dict[str, JsonValue]:
    """Merge request-level and fact-level metadata without hiding source context."""

    merged = dict(request_metadata)
    merged.update(
        {
            "adapter": "whygame_relationship_import",
            "fact_id": fact.id,
            "fact_type": fact.fact_type,
            "confidence": fact.confidence,
            "context": fact.context,
            "metadata": fact.metadata,
        }
    )
    if fact.created_at is not None:
        merged["created_at"] = fact.created_at
    return merged


def _entity_id_for_name(name: str) -> str:
    """Create a stable local entity id for one WhyGame concept name."""

    slug = re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")
    if not slug:
        raise WhyGameAdapterError(f"cannot derive entity id from concept name: {name!r}")
    return f"ent:whygame:{slug}"


def _require_non_empty(value: str, *, field_name: str) -> str:
    """Reject blank string inputs at the adapter boundary."""

    normalized = value.strip()
    if not normalized:
        raise ValueError(f"{field_name} must not be blank")
    return normalized


__all__ = [
    "WhyGameAdapterError",
    "WhyGameImportService",
]
