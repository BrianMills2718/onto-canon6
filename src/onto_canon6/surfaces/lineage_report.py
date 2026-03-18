"""Typed report surface for candidate-centered artifact lineage.

This surface stays intentionally thin. It does not decide what artifacts mean
or what review transitions are valid; it exposes persisted lineage in an
inspectable shape for notebooks and later outward-facing surfaces.
"""

from __future__ import annotations

from ..artifacts import ArtifactLineageService, CandidateLineageReport


class LineageReportService:
    """Build candidate-centered lineage reports over persisted artifact state."""

    def __init__(self, *, artifact_service: ArtifactLineageService | None = None) -> None:
        """Use the provided artifact service or construct a config-backed default."""

        self._artifact_service = artifact_service or ArtifactLineageService()

    def build_candidate_report(self, *, candidate_id: str) -> CandidateLineageReport:
        """Return one inspectable candidate lineage report."""

        return self._artifact_service.build_candidate_lineage_report(candidate_id=candidate_id)
