"""Epistemic extension exports.

The successor keeps epistemic behavior extension-local. The current exported
slice includes:

1. confidence assessment for accepted candidate assertions;
2. explicit supersession from one accepted candidate to another;
3. explicit `active` / `weakened` / `retracted` dispositions over promoted
   assertions;
4. typed reports for candidate-local and promoted-assertion-local epistemics.
"""

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
from .service import EpistemicService
from .store import EpistemicStore, EpistemicStoreConflictError, EpistemicStoreError

__all__ = [
    "AssertionCorroborationGroup",
    "AssertionDispositionRecord",
    "AssertionDispositionTargetStatus",
    "AssertionTensionRecord",
    "ConfidenceAssessmentRecord",
    "ConfidenceSourceKind",
    "EpistemicCandidateReport",
    "EpistemicCandidateStatus",
    "EpistemicService",
    "EpistemicStore",
    "EpistemicStoreConflictError",
    "EpistemicStoreError",
    "PromotedAssertionEpistemicCollectionReport",
    "PromotedAssertionEpistemicReport",
    "PromotedAssertionEpistemicReportSummary",
    "PromotedAssertionEpistemicStatus",
    "SupersessionRecord",
]
