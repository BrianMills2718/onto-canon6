"""Typed report surface for the first stable-identity slice."""

from __future__ import annotations

from collections import Counter

from pydantic import BaseModel, ConfigDict, Field

from ..core.identity_models import IdentityBundleRecord
from ..core.identity_service import IdentityService


class IdentityReportSummary(BaseModel):
    """Summarize one stable-identity report."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    total_identities: int = Field(ge=0)
    total_memberships: int = Field(ge=0)
    total_external_references: int = Field(ge=0)
    external_reference_status_counts: dict[str, int] = Field(default_factory=dict)


class IdentityReport(BaseModel):
    """Bundle identity rows plus their memberships and external refs."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    identity_bundles: tuple[IdentityBundleRecord, ...] = ()
    summary: IdentityReportSummary


class IdentityReportService:
    """Build inspectable reports over stable identity state."""

    def __init__(self, *, identity_service: IdentityService | None = None) -> None:
        """Use the provided identity service or construct a config-backed one."""

        self._identity_service = identity_service or IdentityService()

    def build_report(self) -> IdentityReport:
        """Return one report over all persisted identity bundles."""

        bundles = tuple(self._identity_service.list_identities())
        return IdentityReport(
            identity_bundles=bundles,
            summary=IdentityReportSummary(
                total_identities=len(bundles),
                total_memberships=sum(len(bundle.memberships) for bundle in bundles),
                total_external_references=sum(
                    len(bundle.external_references) for bundle in bundles
                ),
                external_reference_status_counts=dict(
                    Counter(
                        reference.reference_status
                        for bundle in bundles
                        for reference in bundle.external_references
                    )
                ),
            ),
        )


__all__ = ["IdentityReport", "IdentityReportService", "IdentityReportSummary"]
