"""Explicit overlay-application service for accepted ontology proposals.

This service owns the Phase 3 writeback step:

1. verify a proposal was accepted for overlay application;
2. write the local overlay file deterministically;
3. record one immutable overlay-application audit row;
4. expose the resulting application records for report surfaces.

It is intentionally separate from `ReviewService` so proposal review and
overlay writeback remain distinct lifecycle steps.
"""

from __future__ import annotations

from pathlib import Path

from ..config import get_config
from ..ontology_runtime import (
    OverlayPredicateAdditionRecord,
    load_profile,
    write_overlay_predicate_addition,
)
from .models import OverlayApplicationRecord
from .store import ReviewStore, ReviewStoreConflictError


class OverlayApplicationService:
    """Apply accepted ontology proposals into repo-local overlays."""

    def __init__(
        self,
        *,
        db_path: Path | None = None,
        overlay_root: Path | None = None,
    ) -> None:
        """Create an overlay service using config-backed defaults when omitted."""

        config = get_config()
        self._store = ReviewStore(db_path or config.review_db_path())
        self._overlay_root = (overlay_root or config.overlay_root()).resolve()

    @property
    def overlay_root(self) -> Path:
        """Return the local overlay root used by this service."""

        return self._overlay_root

    @property
    def store(self) -> ReviewStore:
        """Expose the shared review store for notebook inspection."""

        return self._store

    def apply_proposal_to_overlay(
        self,
        *,
        proposal_id: str,
        applied_by: str,
    ) -> OverlayApplicationRecord:
        """Apply one accepted proposal into its target overlay.

        This fails loudly unless the proposal is already accepted and marked
        `pending_overlay_apply`. Re-applying an already-applied proposal returns
        the existing immutable audit record.
        """

        normalized_proposal_id = proposal_id.strip()
        normalized_applied_by = applied_by.strip()
        if not normalized_proposal_id:
            raise ValueError("proposal_id must be a non-empty string")
        if not normalized_applied_by:
            raise ValueError("applied_by must be a non-empty string")

        with self._store.transaction() as conn:
            proposal = self._store.get_proposal(conn, proposal_id=normalized_proposal_id)
            if proposal.overlay_application is not None:
                return proposal.overlay_application
            if proposal.status != "accepted":
                raise ReviewStoreConflictError(
                    f"proposal must be accepted before overlay application: {normalized_proposal_id}"
                )
            if proposal.application_status != "pending_overlay_apply":
                raise ReviewStoreConflictError(
                    "proposal must have application_status='pending_overlay_apply' "
                    f"before overlay application: {normalized_proposal_id}"
                )
            if proposal.target_pack is None:
                raise ValueError("accepted proposal is missing target_pack for overlay application")
            if proposal.proposal_kind != "predicate":
                raise ValueError("only predicate proposals can be applied to overlays today")

            profile = load_profile(
                proposal.profile.profile_id,
                proposal.profile.profile_version,
            )
            if profile.pack_ref is None:
                raise ValueError("overlay application requires a base pack-backed profile")

            content_path = write_overlay_predicate_addition(
                OverlayPredicateAdditionRecord(
                    proposal_id=proposal.proposal_id,
                    predicate_id=proposal.proposed_value,
                    base_pack=profile.pack_ref,
                    overlay_pack=proposal.target_pack,
                    applied_by=normalized_applied_by,
                    applied_at=_now_iso(),
                ),
                overlay_root_path=self._overlay_root,
            )
            self._store.upsert_overlay_application(
                conn,
                proposal_id=proposal.proposal_id,
                profile=proposal.profile,
                overlay_pack=proposal.target_pack,
                proposal_kind=proposal.proposal_kind,
                applied_value=proposal.proposed_value,
                content_path=str(content_path),
                applied_by=normalized_applied_by,
            )
            return self._store.get_overlay_application(conn, proposal_id=proposal.proposal_id)

    def list_overlay_applications(
        self,
        *,
        profile_id: str | None = None,
        profile_version: str | None = None,
    ) -> list[OverlayApplicationRecord]:
        """List persisted overlay applications in deterministic order."""

        normalized_profile_id = profile_id.strip() if profile_id is not None else None
        normalized_profile_version = (
            profile_version.strip() if profile_version is not None else None
        )
        if normalized_profile_version is not None and not normalized_profile_id:
            raise ValueError("profile_version requires profile_id")
        with self._store.transaction() as conn:
            return self._store.list_overlay_applications(
                conn,
                profile_id=normalized_profile_id,
                profile_version=normalized_profile_version,
            )


def _now_iso() -> str:
    """Return an ISO-8601 UTC timestamp with stable formatting."""

    from datetime import datetime, timezone

    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


__all__ = ["OverlayApplicationService"]
