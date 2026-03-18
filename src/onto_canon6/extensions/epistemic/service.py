"""Service layer for the epistemic extension slices.

This service composes the review store, promoted-graph store, and
extension-local epistemic state. It keeps the base workflow optional by
referencing accepted candidates and promoted assertions through explicit seams
rather than mutating the base review or graph schemas.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import logging
from pathlib import Path
import sqlite3

from ...config import get_config
from ...core import PromotedGraphAssertionRecord
from ...core.graph_store import (
    CanonicalGraphStore,
    CanonicalGraphStoreNotFoundError,
)
from ...pipeline import CandidateAssertionRecord, ReviewStore
from .models import (
    AssertionCorroborationGroup,
    AssertionDispositionRecord,
    AssertionDispositionTargetStatus,
    AssertionTensionRecord,
    ConfidenceAssessmentRecord,
    ConfidenceSourceKind,
    EpistemicCandidateReport,
    EpistemicCandidateStatus,
    PromotedAssertionEpistemicCollectionReport,
    PromotedAssertionEpistemicReport,
    PromotedAssertionEpistemicReportSummary,
    PromotedAssertionEpistemicStatus,
    SupersessionRecord,
)
from .store import EpistemicStore, EpistemicStoreConflictError, EpistemicStoreError

logger = logging.getLogger(__name__)

_ALLOWED_ASSERTION_TRANSITIONS: dict[
    PromotedAssertionEpistemicStatus,
    frozenset[AssertionDispositionTargetStatus],
] = {
    "active": frozenset({"weakened", "retracted"}),
    "weakened": frozenset({"active", "retracted"}),
    "superseded": frozenset(),
    "retracted": frozenset(),
}


@dataclass(frozen=True)
class _AssertionEpistemicSnapshot:
    """Capture the derived epistemic state for one promoted assertion."""

    assertion: PromotedGraphAssertionRecord
    epistemic_status: PromotedAssertionEpistemicStatus
    confidence: ConfidenceAssessmentRecord | None
    current_disposition: AssertionDispositionRecord | None
    disposition_history: tuple[AssertionDispositionRecord, ...]
    superseded_by: SupersessionRecord | None
    superseded_by_assertion_id: str | None


class EpistemicService:
    """Assign confidence, record supersession/dispositions, and build reports."""

    def __init__(self, *, db_path: Path | None = None) -> None:
        """Create an epistemic service over the configured review database."""

        config = get_config()
        resolved_db_path = db_path or config.review_db_path()
        self._review_store = ReviewStore(resolved_db_path)
        self._graph_store = CanonicalGraphStore(resolved_db_path)
        self._store = EpistemicStore(resolved_db_path)

    @property
    def db_path(self) -> Path:
        """Return the SQLite path shared across review, graph, and epistemics."""

        return self._store.db_path

    def record_confidence(
        self,
        *,
        candidate_id: str,
        confidence_score: float,
        source_kind: ConfidenceSourceKind,
        actor_id: str,
        rationale: str | None = None,
    ) -> ConfidenceAssessmentRecord:
        """Persist one confidence assessment against an accepted candidate."""

        normalized_candidate_id = _require_non_empty(candidate_id, field_name="candidate_id")
        normalized_actor_id = _require_non_empty(actor_id, field_name="actor_id")
        normalized_rationale = rationale.strip() if rationale is not None else None
        with self._store.transaction() as conn:
            candidate = self._review_store.get_candidate_assertion(
                conn,
                candidate_id=normalized_candidate_id,
            )
            _require_accepted_candidate(candidate)
            record = self._store.insert_confidence_assessment(
                conn,
                candidate_id=normalized_candidate_id,
                confidence_score=confidence_score,
                source_kind=source_kind,
                actor_id=normalized_actor_id,
                rationale=normalized_rationale if normalized_rationale else None,
            )
        logger.info(
            "epistemic confidence recorded candidate_id=%s confidence_score=%s source_kind=%s actor_id=%s",
            normalized_candidate_id,
            confidence_score,
            source_kind,
            normalized_actor_id,
        )
        return record

    def record_supersession(
        self,
        *,
        prior_candidate_id: str,
        replacement_candidate_id: str,
        actor_id: str,
        rationale: str | None = None,
    ) -> SupersessionRecord:
        """Persist one supersession from an older accepted candidate to a newer one."""

        normalized_prior_id = _require_non_empty(
            prior_candidate_id,
            field_name="prior_candidate_id",
        )
        normalized_replacement_id = _require_non_empty(
            replacement_candidate_id,
            field_name="replacement_candidate_id",
        )
        normalized_actor_id = _require_non_empty(actor_id, field_name="actor_id")
        normalized_rationale = rationale.strip() if rationale is not None else None
        if normalized_prior_id == normalized_replacement_id:
            raise ValueError("supersession requires different candidate identifiers")

        with self._store.transaction() as conn:
            prior_candidate = self._review_store.get_candidate_assertion(
                conn,
                candidate_id=normalized_prior_id,
            )
            replacement_candidate = self._review_store.get_candidate_assertion(
                conn,
                candidate_id=normalized_replacement_id,
            )
            _require_accepted_candidate(prior_candidate)
            _require_accepted_candidate(replacement_candidate)
            if self._store.get_superseded_by(conn, candidate_id=normalized_replacement_id) is not None:
                raise EpistemicStoreConflictError(
                    "replacement candidate is already superseded and cannot become the replacement"
                )
            record = self._store.insert_supersession(
                conn,
                prior_candidate_id=normalized_prior_id,
                replacement_candidate_id=normalized_replacement_id,
                actor_id=normalized_actor_id,
                rationale=normalized_rationale if normalized_rationale else None,
            )
        logger.info(
            "epistemic supersession recorded prior_candidate_id=%s replacement_candidate_id=%s actor_id=%s",
            normalized_prior_id,
            normalized_replacement_id,
            normalized_actor_id,
        )
        return record

    def record_assertion_disposition(
        self,
        *,
        assertion_id: str,
        target_status: AssertionDispositionTargetStatus,
        actor_id: str,
        rationale: str | None = None,
    ) -> AssertionDispositionRecord:
        """Persist one explicit disposition over a promoted assertion."""

        normalized_assertion_id = _require_non_empty(assertion_id, field_name="assertion_id")
        normalized_actor_id = _require_non_empty(actor_id, field_name="actor_id")
        normalized_rationale = rationale.strip() if rationale is not None else None
        with self._store.transaction() as conn:
            try:
                assertion = self._graph_store.get_promoted_assertion(
                    conn,
                    assertion_id=normalized_assertion_id,
                )
            except CanonicalGraphStoreNotFoundError as exc:
                raise EpistemicStoreError(str(exc)) from exc
            snapshot = self._build_assertion_snapshot(conn, assertion=assertion)
            _require_assertion_transition(
                current_status=snapshot.epistemic_status,
                target_status=target_status,
            )
            record = self._store.insert_assertion_disposition(
                conn,
                assertion_id=normalized_assertion_id,
                prior_status=snapshot.epistemic_status,
                target_status=target_status,
                actor_id=normalized_actor_id,
                rationale=normalized_rationale if normalized_rationale else None,
            )
        logger.info(
            "epistemic assertion disposition recorded assertion_id=%s prior_status=%s target_status=%s actor_id=%s",
            normalized_assertion_id,
            record.prior_status,
            target_status,
            normalized_actor_id,
        )
        return record

    def build_candidate_report(self, *, candidate_id: str) -> EpistemicCandidateReport:
        """Return one accepted candidate plus its extension-local epistemic state."""

        normalized_candidate_id = _require_non_empty(candidate_id, field_name="candidate_id")
        with self._store.transaction() as conn:
            candidate = self._review_store.get_candidate_assertion(
                conn,
                candidate_id=normalized_candidate_id,
            )
            _require_accepted_candidate(candidate)
            confidence = self._store.get_confidence_assessment(conn, candidate_id=normalized_candidate_id)
            superseded_by = self._store.get_superseded_by(conn, candidate_id=normalized_candidate_id)
            supersedes = self._store.list_supersedes(
                conn,
                replacement_candidate_id=normalized_candidate_id,
            )
        epistemic_status: EpistemicCandidateStatus = "superseded" if superseded_by else "active"
        return EpistemicCandidateReport(
            candidate=candidate,
            epistemic_status=epistemic_status,
            confidence=confidence,
            superseded_by=superseded_by,
            supersedes=supersedes,
        )

    def build_promoted_assertion_report(
        self,
        *,
        assertion_id: str,
    ) -> PromotedAssertionEpistemicReport:
        """Return one promoted assertion plus its derived epistemic state."""

        normalized_assertion_id = _require_non_empty(assertion_id, field_name="assertion_id")
        collection = self.build_promoted_assertion_collection_report()
        for report in collection.assertion_reports:
            if report.assertion.assertion_id == normalized_assertion_id:
                return report
        raise EpistemicStoreError(f"promoted assertion not found: {normalized_assertion_id}")

    def build_promoted_assertion_collection_report(
        self,
    ) -> PromotedAssertionEpistemicCollectionReport:
        """Return all promoted assertions with derived corroboration and tensions."""

        with self._store.transaction() as conn:
            assertions = tuple(self._graph_store.list_promoted_assertions(conn))
            snapshots = tuple(
                self._build_assertion_snapshot(conn, assertion=assertion)
                for assertion in assertions
            )
        corroboration_groups = _derive_corroboration_groups(snapshots)
        corroboration_lookup = _build_corroboration_lookup(corroboration_groups)
        tensions = _derive_tensions(snapshots)
        tension_lookup = _build_tension_lookup(tensions)
        reports = tuple(
            PromotedAssertionEpistemicReport(
                assertion=snapshot.assertion,
                epistemic_status=snapshot.epistemic_status,
                confidence=snapshot.confidence,
                current_disposition=snapshot.current_disposition,
                disposition_history=snapshot.disposition_history,
                superseded_by=snapshot.superseded_by,
                superseded_by_assertion_id=snapshot.superseded_by_assertion_id,
                corroborating_assertion_ids=corroboration_lookup.get(
                    snapshot.assertion.assertion_id,
                    (),
                ),
                tensions=tension_lookup.get(snapshot.assertion.assertion_id, ()),
            )
            for snapshot in snapshots
        )
        return PromotedAssertionEpistemicCollectionReport(
            assertion_reports=reports,
            corroboration_groups=corroboration_groups,
            tensions=tensions,
            summary=_build_promoted_summary(reports, corroboration_groups, tensions),
        )

    def _build_assertion_snapshot(
        self,
        conn: sqlite3.Connection,
        *,
        assertion: PromotedGraphAssertionRecord,
    ) -> _AssertionEpistemicSnapshot:
        """Derive the current epistemic state for one promoted assertion."""

        confidence = self._store.get_confidence_assessment(
            conn,
            candidate_id=assertion.source_candidate_id,
        )
        disposition_history = self._store.list_assertion_dispositions(
            conn,
            assertion_id=assertion.assertion_id,
        )
        current_disposition = disposition_history[-1] if disposition_history else None
        superseded_by = self._store.get_superseded_by(
            conn,
            candidate_id=assertion.source_candidate_id,
        )
        superseded_by_assertion_id = None
        if superseded_by is not None:
            replacement_assertion = self._graph_store.get_promoted_assertion_by_candidate(
                conn,
                source_candidate_id=superseded_by.replacement_candidate_id,
            )
            if replacement_assertion is not None:
                superseded_by_assertion_id = replacement_assertion.assertion_id
        if current_disposition is not None and current_disposition.target_status == "retracted":
            epistemic_status: PromotedAssertionEpistemicStatus = "retracted"
        elif superseded_by_assertion_id is not None:
            epistemic_status = "superseded"
        elif current_disposition is not None:
            epistemic_status = current_disposition.target_status
        else:
            epistemic_status = "active"
        return _AssertionEpistemicSnapshot(
            assertion=assertion,
            epistemic_status=epistemic_status,
            confidence=confidence,
            current_disposition=current_disposition,
            disposition_history=disposition_history,
            superseded_by=superseded_by,
            superseded_by_assertion_id=superseded_by_assertion_id,
        )


def _require_non_empty(value: str, *, field_name: str) -> str:
    """Reject blank string inputs at the extension service boundary."""

    normalized = value.strip()
    if not normalized:
        raise ValueError(f"{field_name} must be a non-empty string")
    return normalized


def _require_accepted_candidate(candidate: CandidateAssertionRecord) -> None:
    """Require that candidate-local epistemic state attaches only to accepted candidates."""

    if candidate.review_status != "accepted":
        raise EpistemicStoreConflictError(
            f"epistemic extension requires accepted candidate: {candidate.candidate_id}"
        )


def _require_assertion_transition(
    *,
    current_status: PromotedAssertionEpistemicStatus,
    target_status: AssertionDispositionTargetStatus,
) -> None:
    """Validate one explicit promoted-assertion disposition transition."""

    if current_status == target_status:
        raise EpistemicStoreConflictError(
            f"assertion is already in status {current_status!r}; no transition required"
        )
    allowed_targets = _ALLOWED_ASSERTION_TRANSITIONS[current_status]
    if target_status not in allowed_targets:
        raise EpistemicStoreConflictError(
            f"invalid assertion transition from {current_status!r} to {target_status!r}"
        )


def _derive_corroboration_groups(
    snapshots: tuple[_AssertionEpistemicSnapshot, ...],
) -> tuple[AssertionCorroborationGroup, ...]:
    """Group non-terminal promoted assertions that share the same canonical body."""

    groups: dict[tuple[str, str], list[str]] = {}
    for snapshot in snapshots:
        if snapshot.epistemic_status not in {"active", "weakened"}:
            continue
        fingerprint = _canonical_json(snapshot.assertion.normalized_body)
        key = (snapshot.assertion.predicate, fingerprint)
        groups.setdefault(key, []).append(snapshot.assertion.assertion_id)

    corroboration_groups: list[AssertionCorroborationGroup] = []
    for (predicate, fingerprint), assertion_ids in groups.items():
        if len(assertion_ids) < 2:
            continue
        corroboration_groups.append(
            AssertionCorroborationGroup(
                group_id=f"ecor_{_short_digest(predicate + '|' + fingerprint)}",
                predicate=predicate,
                normalized_body_fingerprint=fingerprint,
                assertion_ids=tuple(assertion_ids),
            )
        )
    return tuple(corroboration_groups)


def _build_corroboration_lookup(
    groups: tuple[AssertionCorroborationGroup, ...],
) -> dict[str, tuple[str, ...]]:
    """Map each assertion id to the corroborating assertion ids from its groups."""

    lookup: dict[str, list[str]] = {}
    for group in groups:
        for assertion_id in group.assertion_ids:
            others = [value for value in group.assertion_ids if value != assertion_id]
            if not others:
                continue
            lookup.setdefault(assertion_id, []).extend(others)
    return {
        assertion_id: tuple(_dedupe_preserving_order(values))
        for assertion_id, values in lookup.items()
    }


def _derive_tensions(
    snapshots: tuple[_AssertionEpistemicSnapshot, ...],
) -> tuple[AssertionTensionRecord, ...]:
    """Derive deterministic tension pairs over non-terminal promoted assertions."""

    eligible = [
        snapshot for snapshot in snapshots if snapshot.epistemic_status in {"active", "weakened"}
    ]
    tensions: list[AssertionTensionRecord] = []
    for index, left in enumerate(eligible):
        for right in eligible[index + 1 :]:
            tension = _build_tension_record(left=left, right=right)
            if tension is not None:
                tensions.append(tension)
    return tuple(tensions)


def _build_tension_lookup(
    tensions: tuple[AssertionTensionRecord, ...],
) -> dict[str, tuple[AssertionTensionRecord, ...]]:
    """Map each assertion id to the tension records that mention it."""

    lookup: dict[str, list[AssertionTensionRecord]] = {}
    for tension in tensions:
        lookup.setdefault(tension.assertion_a_id, []).append(tension)
        lookup.setdefault(tension.assertion_b_id, []).append(tension)
    return {
        assertion_id: tuple(records)
        for assertion_id, records in lookup.items()
    }


def _build_tension_record(
    *,
    left: _AssertionEpistemicSnapshot,
    right: _AssertionEpistemicSnapshot,
) -> AssertionTensionRecord | None:
    """Return one deterministic tension pair when the heuristics match."""

    if left.assertion.predicate != right.assertion.predicate:
        return None
    if _canonical_json(left.assertion.normalized_body) == _canonical_json(right.assertion.normalized_body):
        return None

    left_roles = _role_signature_map(left.assertion)
    right_roles = _role_signature_map(right.assertion)
    all_role_ids = sorted(set(left_roles) | set(right_roles))
    anchor_roles = tuple(
        role_id
        for role_id in sorted(set(left_roles) & set(right_roles))
        if left_roles[role_id] == right_roles[role_id]
        and _role_has_entity_anchor(left.assertion, role_id)
        and _role_has_entity_anchor(right.assertion, role_id)
    )
    differing_roles = tuple(
        role_id for role_id in all_role_ids if left_roles.get(role_id) != right_roles.get(role_id)
    )
    if not anchor_roles or not differing_roles:
        return None

    tension_key = "|".join(
        (
            left.assertion.assertion_id,
            right.assertion.assertion_id,
            left.assertion.predicate,
            ",".join(anchor_roles),
            ",".join(differing_roles),
        )
    )
    return AssertionTensionRecord(
        tension_id=f"eten_{_short_digest(tension_key)}",
        assertion_a_id=left.assertion.assertion_id,
        assertion_b_id=right.assertion.assertion_id,
        predicate=left.assertion.predicate,
        tension_kind="role_filler_conflict",
        anchor_roles=anchor_roles,
        differing_roles=differing_roles,
        description=(
            "Promoted assertions share anchor roles "
            f"{', '.join(anchor_roles)} but disagree on role fillers "
            f"{', '.join(differing_roles)}."
        ),
    )


def _role_signature_map(assertion: PromotedGraphAssertionRecord) -> dict[str, str]:
    """Return deterministic filler signatures for every normalized role."""

    roles = assertion.normalized_body.get("roles")
    if not isinstance(roles, dict):
        raise EpistemicStoreError(
            f"promoted assertion has invalid normalized roles: {assertion.assertion_id}"
        )
    signatures: dict[str, str] = {}
    for role_id, fillers in roles.items():
        if not isinstance(role_id, str) or not isinstance(fillers, list):
            raise EpistemicStoreError(
                f"promoted assertion has invalid role structure: {assertion.assertion_id}"
            )
        signatures[role_id] = _canonical_json(fillers)
    return signatures


def _role_has_entity_anchor(assertion: PromotedGraphAssertionRecord, role_id: str) -> bool:
    """Return whether one normalized role contains at least one entity filler."""

    roles = assertion.normalized_body.get("roles")
    if not isinstance(roles, dict):
        raise EpistemicStoreError(
            f"promoted assertion has invalid normalized roles: {assertion.assertion_id}"
        )
    fillers = roles.get(role_id)
    if not isinstance(fillers, list):
        raise EpistemicStoreError(
            f"promoted assertion has invalid role filler list: {assertion.assertion_id}:{role_id}"
        )
    return any(
        isinstance(filler, dict) and filler.get("kind") == "entity"
        for filler in fillers
    )


def _build_promoted_summary(
    reports: tuple[PromotedAssertionEpistemicReport, ...],
    corroboration_groups: tuple[AssertionCorroborationGroup, ...],
    tensions: tuple[AssertionTensionRecord, ...],
) -> PromotedAssertionEpistemicReportSummary:
    """Compute stable summary counts for the promoted-assertion epistemic report."""

    return PromotedAssertionEpistemicReportSummary(
        total_assertions=len(reports),
        total_active=sum(1 for report in reports if report.epistemic_status == "active"),
        total_weakened=sum(1 for report in reports if report.epistemic_status == "weakened"),
        total_superseded=sum(1 for report in reports if report.epistemic_status == "superseded"),
        total_retracted=sum(1 for report in reports if report.epistemic_status == "retracted"),
        total_assertions_with_confidence=sum(1 for report in reports if report.confidence is not None),
        total_corroboration_groups=len(corroboration_groups),
        total_tension_pairs=len(tensions),
    )


def _canonical_json(payload: object) -> str:
    """Return deterministic JSON text for one derived comparison payload."""

    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _short_digest(text: str) -> str:
    """Return a short deterministic digest for derived report identifiers."""

    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:12]


def _dedupe_preserving_order(values: list[str]) -> list[str]:
    """Deduplicate strings while preserving their first-seen order."""

    seen: set[str] = set()
    deduped: list[str] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        deduped.append(value)
    return deduped


__all__ = [
    "EpistemicService",
]
