"""Typed report surface for the first epistemic extension slice.

This surface stays deliberately thin. It exposes extension-local confidence and
supersession state over accepted candidates without relocating the logic into a
larger workflow object or handler layer.
"""

from __future__ import annotations

from ..extensions.epistemic import EpistemicCandidateReport, EpistemicService


class EpistemicReportService:
    """Build inspectable epistemic reports over accepted candidate assertions."""

    def __init__(self, *, epistemic_service: EpistemicService | None = None) -> None:
        """Use the provided epistemic service or construct a config-backed default."""

        self._epistemic_service = epistemic_service or EpistemicService()

    def build_candidate_report(self, *, candidate_id: str) -> EpistemicCandidateReport:
        """Return one accepted candidate plus its extension-local epistemic state."""

        return self._epistemic_service.build_candidate_report(candidate_id=candidate_id)
