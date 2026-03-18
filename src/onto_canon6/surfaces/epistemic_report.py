"""Typed report surface for the epistemic extension slices.

This surface stays deliberately thin. It exposes extension-local candidate and
promoted-assertion epistemic state without relocating the logic into a larger
workflow object or handler layer.
"""

from __future__ import annotations

from ..extensions.epistemic import (
    EpistemicCandidateReport,
    EpistemicService,
    PromotedAssertionEpistemicCollectionReport,
    PromotedAssertionEpistemicReport,
)


class EpistemicReportService:
    """Build inspectable candidate and promoted-assertion epistemic reports."""

    def __init__(self, *, epistemic_service: EpistemicService | None = None) -> None:
        """Use the provided epistemic service or construct a config-backed default."""

        self._epistemic_service = epistemic_service or EpistemicService()

    def build_candidate_report(self, *, candidate_id: str) -> EpistemicCandidateReport:
        """Return one accepted candidate plus its extension-local epistemic state."""

        return self._epistemic_service.build_candidate_report(candidate_id=candidate_id)

    def build_promoted_assertion_report(
        self,
        *,
        assertion_id: str,
    ) -> PromotedAssertionEpistemicReport:
        """Return one promoted assertion plus its derived epistemic state."""

        return self._epistemic_service.build_promoted_assertion_report(assertion_id=assertion_id)

    def build_promoted_assertion_collection_report(
        self,
    ) -> PromotedAssertionEpistemicCollectionReport:
        """Return all promoted assertions plus derived corroboration and tensions."""

        return self._epistemic_service.build_promoted_assertion_collection_report()
