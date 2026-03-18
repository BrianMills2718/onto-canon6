"""Epistemic extension exports.

The first epistemic slice stays intentionally small:

1. confidence assessment for accepted candidate assertions;
2. explicit supersession from one accepted candidate to another;
3. typed report views over that extension-local state.
"""

from .models import (
    ConfidenceAssessmentRecord,
    ConfidenceSourceKind,
    EpistemicCandidateReport,
    EpistemicCandidateStatus,
    SupersessionRecord,
)
from .service import EpistemicService
from .store import EpistemicStore, EpistemicStoreConflictError, EpistemicStoreError

__all__ = [
    "ConfidenceAssessmentRecord",
    "ConfidenceSourceKind",
    "EpistemicCandidateReport",
    "EpistemicCandidateStatus",
    "EpistemicService",
    "EpistemicStore",
    "EpistemicStoreConflictError",
    "EpistemicStoreError",
    "SupersessionRecord",
]
