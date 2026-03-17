"""Service layer for the narrow pipeline and review slices.

This service composes profile loading, assertion validation, candidate review,
proposal review, and persisted state access without importing the old
`onto-canon5` workflow runtime.
"""

from __future__ import annotations

import hashlib
import json
import logging
from pathlib import Path
from typing import Mapping, Sequence

from pydantic import JsonValue, TypeAdapter

from ..config import get_config
from ..ontology_runtime import (
    canonical_assertion_body,
    load_effective_profile,
    normalize_assertion_payload,
    validate_assertion_payload,
)
from .models import (
    CandidateAssertionRecord,
    CandidateAssertionImport,
    CandidateProvenance,
    CandidateReviewDecision,
    CandidateReviewStatus,
    CandidateSubmissionResult,
    CandidateValidationStatus,
    EvidenceSpan,
    PersistedValidationSnapshot,
    ProfileRef,
    ProposalAcceptancePolicy,
    ProposalApplicationStatus,
    ProposalRecord,
    ProposalReviewDecision,
    ProposalStatus,
    SourceArtifactRef,
)
from .store import ReviewStore, ReviewStoreConflictError

logger = logging.getLogger(__name__)
_JSON_OBJECT_ADAPTER = TypeAdapter(dict[str, JsonValue])
_EVIDENCE_SPAN_TUPLE_ADAPTER = TypeAdapter(tuple[EvidenceSpan, ...])


class ReviewService:
    """Validate candidate assertions and persist reviewable outcomes.

    The service stays intentionally small. It owns orchestration for the
    current proving slices only:

    - submit candidate assertions with provenance;
    - persist mixed-mode proposals;
    - record candidate review decisions;
    - record proposal review decisions;
    - expose filtered state for report surfaces.
    """

    def __init__(
        self,
        *,
        db_path: Path | None = None,
        overlay_root: Path | None = None,
        default_acceptance_policy: ProposalAcceptancePolicy | None = None,
    ) -> None:
        """Create a review service using config-backed defaults when omitted."""

        config = get_config()
        self._default_acceptance_policy = (
            default_acceptance_policy or config.pipeline.default_acceptance_policy
        )
        self._store = ReviewStore(db_path or config.review_db_path())
        self._overlay_root = (overlay_root or config.overlay_root()).resolve()

    @property
    def store(self) -> ReviewStore:
        """Expose the underlying store for notebook inspection."""

        return self._store

    @property
    def default_acceptance_policy(self) -> ProposalAcceptancePolicy:
        """Return the service's default proposal-acceptance policy."""

        return self._default_acceptance_policy

    @property
    def overlay_root(self) -> Path:
        """Return the overlay root used for overlay-aware validation loads."""

        return self._overlay_root

    def submit_candidate_assertion(
        self,
        *,
        payload: Mapping[str, object],
        profile_id: str,
        profile_version: str,
        submitted_by: str,
        source_kind: str,
        source_ref: str,
        source_label: str | None = None,
        source_metadata: Mapping[str, object] | None = None,
        source_text: str | None = None,
        claim_text: str | None = None,
        evidence_spans: Sequence[Mapping[str, object]] | None = None,
    ) -> CandidateSubmissionResult:
        """Validate and persist one convenience-form candidate assertion.

        This method remains as the notebook-friendly convenience boundary. It
        now wraps the typed Phase 4 import contract so callers can optionally
        attach source text, evidence spans, and a claim gloss without changing
        the existing review workflow API.
        """

        claim_text_value = claim_text.strip() if claim_text is not None else None
        candidate_import = CandidateAssertionImport(
            profile=ProfileRef(
                profile_id=_require_non_empty(profile_id, field_name="profile_id"),
                profile_version=_require_non_empty(
                    profile_version,
                    field_name="profile_version",
                ),
            ),
            payload=_coerce_json_object(dict(payload)),
            submitted_by=_require_non_empty(submitted_by, field_name="submitted_by"),
            source_artifact=SourceArtifactRef(
                source_kind=_require_non_empty(source_kind, field_name="source_kind"),
                source_ref=_require_non_empty(source_ref, field_name="source_ref"),
                source_label=source_label.strip() if source_label is not None else None,
                source_metadata=_coerce_json_object(dict(source_metadata or {})),
                content_text=source_text,
            ),
            evidence_spans=_EVIDENCE_SPAN_TUPLE_ADAPTER.validate_python(evidence_spans or ()),
            claim_text=claim_text_value if claim_text_value else None,
        )
        return self.submit_candidate_import(candidate_import=candidate_import)

    def submit_candidate_import(
        self,
        *,
        candidate_import: CandidateAssertionImport,
    ) -> CandidateSubmissionResult:
        """Validate and persist one typed candidate-import contract.

        This is the first explicit Phase 4 import boundary. It keeps raw source
        grounding visible by persisting:

        - the source artifact reference;
        - optional source text used for span verification;
        - one or more exact evidence spans;
        - an optional human-readable claim gloss.
        """

        normalized_profile_id = candidate_import.profile.profile_id
        normalized_profile_version = candidate_import.profile.profile_version
        provenance = CandidateProvenance(
            submitted_by=candidate_import.submitted_by,
            source_artifact=candidate_import.source_artifact,
        )
        evidence_spans = candidate_import.evidence_spans
        if evidence_spans:
            source_text = provenance.content_text
            if source_text is None:
                raise ValueError(
                    "evidence spans require source_artifact.content_text for verification"
                )
            _verify_evidence_spans(source_text=source_text, evidence_spans=evidence_spans)
        profile = load_effective_profile(
            normalized_profile_id,
            normalized_profile_version,
            overlay_root=self._overlay_root,
        )
        normalized_payload = canonical_assertion_body(candidate_import.payload)
        raw_normalized_payload = normalize_assertion_payload(candidate_import.payload)
        outcome = validate_assertion_payload(candidate_import.payload, profile=profile)
        snapshot = PersistedValidationSnapshot.from_outcome(outcome)
        validation_status = _derive_validation_status(snapshot)
        persisted_payload = _coerce_json_object(raw_normalized_payload)
        persisted_normalized_payload = _coerce_json_object(normalized_payload)
        payload_hash = _candidate_payload_hash(normalized_payload)
        profile_ref = candidate_import.profile

        with self._store.transaction() as conn:
            candidate_id = self._store.insert_candidate(
                conn,
                profile=profile_ref,
                validation_status=validation_status,
                review_status="pending_review",
                payload_hash=payload_hash,
                payload=persisted_payload,
                normalized_payload=persisted_normalized_payload,
                validation=snapshot,
                provenance=provenance,
                claim_text=candidate_import.claim_text,
                evidence_spans=evidence_spans,
            )

            proposal_ids: list[str] = []
            for request in outcome.proposal_requests:
                proposal_id = self._store.upsert_proposal(
                    conn,
                    proposal_kind=request.kind,
                    proposed_value=request.value,
                    profile=profile_ref,
                    target_pack=request.target_pack,
                    reason=request.reason,
                    details={
                        "source": "validate_assertion_payload",
                        "candidate_source_kind": provenance.source_kind,
                    },
                )
                self._store.link_candidate_to_proposal(
                    conn,
                    candidate_id=candidate_id,
                    proposal_id=proposal_id,
                )
                proposal_ids.append(proposal_id)

            candidate = self._store.get_candidate_assertion(conn, candidate_id=candidate_id)
            proposals = tuple(
                self._store.get_proposal(conn, proposal_id=proposal_id)
                for proposal_id in sorted(set(proposal_ids))
            )
        logger.info(
            "candidate submission persisted candidate_id=%s validation_status=%s review_status=%s proposal_count=%d source_kind=%s source_ref=%s",
            candidate.candidate_id,
            candidate.validation_status,
            candidate.review_status,
            len(proposals),
            candidate.provenance.source_kind,
            candidate.provenance.source_ref,
        )
        return CandidateSubmissionResult(candidate=candidate, proposals=proposals)

    def list_candidate_assertions(
        self,
        *,
        review_status_filter: CandidateReviewStatus | None = None,
        validation_status_filter: CandidateValidationStatus | None = None,
        profile_id: str | None = None,
        profile_version: str | None = None,
        proposal_status_filter: ProposalStatus | None = None,
    ) -> list[CandidateAssertionRecord]:
        """List persisted candidate assertions with optional filters."""

        normalized_profile_id = profile_id.strip() if profile_id is not None else None
        normalized_profile_version = (
            profile_version.strip() if profile_version is not None else None
        )
        _validate_profile_filter(
            profile_id=normalized_profile_id,
            profile_version=normalized_profile_version,
        )
        with self._store.transaction() as conn:
            return self._store.list_candidate_assertions(
                conn,
                review_status_filter=review_status_filter,
                validation_status_filter=validation_status_filter,
                profile_id=normalized_profile_id,
                profile_version=normalized_profile_version,
                proposal_status_filter=proposal_status_filter,
            )

    def list_proposals(
        self,
        *,
        status_filter: ProposalStatus | None = None,
        profile_id: str | None = None,
        profile_version: str | None = None,
    ) -> list[ProposalRecord]:
        """List persisted ontology proposals with optional profile filters."""

        normalized_profile_id = profile_id.strip() if profile_id is not None else None
        normalized_profile_version = (
            profile_version.strip() if profile_version is not None else None
        )
        _validate_profile_filter(
            profile_id=normalized_profile_id,
            profile_version=normalized_profile_version,
        )
        with self._store.transaction() as conn:
            return self._store.list_proposals(
                conn,
                status_filter=status_filter,
                profile_id=normalized_profile_id,
                profile_version=normalized_profile_version,
            )

    def review_candidate(
        self,
        *,
        candidate_id: str,
        decision: CandidateReviewDecision,
        actor_id: str,
        note_text: str | None = None,
    ) -> CandidateAssertionRecord:
        """Accept or reject one persisted candidate assertion.

        Candidate review is deliberately separate from proposal review so the
        system can reject a candidate without mutating ontology state and accept
        a candidate only when the review transition is valid.
        """

        normalized_candidate_id = _require_non_empty(candidate_id, field_name="candidate_id")
        normalized_actor_id = _require_non_empty(actor_id, field_name="actor_id")

        with self._store.transaction() as conn:
            candidate = self._store.get_candidate_assertion(
                conn,
                candidate_id=normalized_candidate_id,
            )
            _validate_candidate_review_transition(candidate=candidate, decision=decision)
            self._store.insert_candidate_review(
                conn,
                candidate_id=normalized_candidate_id,
                decision=decision,
                actor_id=normalized_actor_id,
                note_text=note_text,
            )
            reviewed = self._store.get_candidate_assertion(
                conn,
                candidate_id=normalized_candidate_id,
            )
        logger.info(
            "candidate review persisted candidate_id=%s decision=%s actor_id=%s",
            reviewed.candidate_id,
            decision,
            normalized_actor_id,
        )
        return reviewed

    def review_proposal(
        self,
        *,
        proposal_id: str,
        decision: ProposalReviewDecision,
        actor_id: str,
        note_text: str | None = None,
        acceptance_policy: ProposalAcceptancePolicy | None = None,
    ) -> ProposalRecord:
        """Accept or reject one persisted ontology proposal."""

        normalized_proposal_id = _require_non_empty(proposal_id, field_name="proposal_id")
        normalized_actor_id = _require_non_empty(actor_id, field_name="actor_id")

        effective_policy = acceptance_policy or self._default_acceptance_policy
        with self._store.transaction() as conn:
            proposal = self._store.get_proposal(conn, proposal_id=normalized_proposal_id)
            if proposal.review is not None:
                raise ReviewStoreConflictError(f"proposal already reviewed: {normalized_proposal_id}")
            application_status = _resolve_application_status(
                proposal=proposal,
                decision=decision,
                acceptance_policy=effective_policy,
            )
            self._store.insert_proposal_review(
                conn,
                proposal_id=normalized_proposal_id,
                decision=decision,
                actor_id=normalized_actor_id,
                note_text=note_text,
                acceptance_policy=effective_policy,
                application_status=application_status,
            )
            reviewed = self._store.get_proposal(conn, proposal_id=normalized_proposal_id)
        logger.info(
            "proposal review persisted proposal_id=%s decision=%s acceptance_policy=%s",
            reviewed.proposal_id,
            decision,
            effective_policy,
        )
        return reviewed


def _derive_validation_status(
    snapshot: PersistedValidationSnapshot,
) -> CandidateValidationStatus:
    """Reduce validation findings to the persisted validation-status field."""

    if snapshot.has_hard_errors:
        return "invalid"
    if snapshot.has_soft_violations:
        return "needs_review"
    return "valid"


def _validate_candidate_review_transition(
    *,
    candidate: CandidateAssertionRecord,
    decision: CandidateReviewDecision,
) -> None:
    """Reject unsupported candidate review transitions loudly.

    The current state machine is intentionally small:

    - `pending_review -> accepted` only for validation statuses other than
      `invalid`;
    - `pending_review -> rejected` for any candidate;
    - `accepted` and `rejected` are terminal.
    """

    if candidate.review_status != "pending_review":
        raise ReviewStoreConflictError(
            f"candidate review is terminal: {candidate.candidate_id} status={candidate.review_status}"
        )
    if decision == "accepted" and candidate.validation_status == "invalid":
        raise ReviewStoreConflictError(
            "invalid candidates cannot transition to accepted review status"
        )


def _resolve_application_status(
    *,
    proposal: ProposalRecord,
    decision: ProposalReviewDecision,
    acceptance_policy: ProposalAcceptancePolicy,
) -> ProposalApplicationStatus:
    """Resolve how an accepted proposal should be treated after review."""

    if decision == "rejected":
        return "not_requested"
    if acceptance_policy == "record_only":
        return "recorded"
    if proposal.target_pack is None:
        raise ValueError(
            "acceptance_policy='apply_to_overlay' requires a proposal target_pack"
        )
    return "pending_overlay_apply"


def _coerce_json_object(payload: dict[str, object]) -> dict[str, JsonValue]:
    """Keep the JSON-object boundary explicit for open payload surfaces."""

    return _JSON_OBJECT_ADAPTER.validate_python(payload)


def _candidate_payload_hash(payload: dict[str, object]) -> str:
    """Return a stable hash for one normalized candidate payload."""

    digest = hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode(
            "utf-8"
        )
    ).hexdigest()
    return f"sha256:{digest}"


def _verify_evidence_spans(
    *,
    source_text: str,
    evidence_spans: tuple[EvidenceSpan, ...],
) -> None:
    """Fail loudly when a proposed evidence span does not match the source text."""

    source_length = len(source_text)
    for index, span in enumerate(evidence_spans):
        if span.end_char > source_length:
            raise ValueError(
                f"evidence span {index} ends beyond source text length: "
                f"{span.end_char} > {source_length}"
            )
        actual_text = source_text[span.start_char : span.end_char]
        if actual_text != span.text:
            raise ValueError(
                f"evidence span {index} text does not match source text at "
                f"{span.start_char}:{span.end_char}"
            )


def _require_non_empty(value: str, *, field_name: str) -> str:
    """Reject blank string inputs at service boundaries."""

    normalized = value.strip()
    if not normalized:
        raise ValueError(f"{field_name} must be a non-empty string")
    return normalized


def _validate_profile_filter(*, profile_id: str | None, profile_version: str | None) -> None:
    """Reject ambiguous profile filtering at the service boundary."""

    if profile_version is not None and not profile_id:
        raise ValueError("profile_version requires profile_id")


__all__ = ["ReviewService"]
