"""Ancestor-aware evaluator for SUMO type accuracy scoring.

Scores type picks against the SUMO hierarchy using ancestor-or-equal matching
with specificity ranking. Designed as a custom evaluator compatible with
``prompt_eval``'s evaluator protocol.

Implements ADR-0019: ancestor-aware evaluation with growing acceptable sets.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from onto_canon6.evaluation.sumo_hierarchy import SUMOHierarchy


@dataclass(frozen=True)
class AncestorEvalScore:
    """Evaluation score for a single type pick against the SUMO hierarchy.

    Attributes
    ----------
    score:
        Overall score in [0, 1]. 1.0 for exact match, 0.0–1.0 for
        ancestor match (proportional to specificity), 0.0 for wrong branch.
    exact:
        1.0 if pick == reference, else 0.0.
    ancestor_match:
        1.0 if pick is ancestor-or-equal of reference, else 0.0.
    specificity:
        ``depth(pick) / depth(reference)`` when ancestor match, else 0.0.
        Measures how much of the hierarchy's depth the pick uses.
    pick:
        The type the runtime LLM chose.
    reference:
        The golden reference type.
    pick_exists:
        Whether the pick is a known SUMO type.
    reference_exists:
        Whether the reference is a known SUMO type.
    """

    score: float
    exact: float
    ancestor_match: float
    specificity: float
    pick: str
    reference: str
    pick_exists: bool
    reference_exists: bool


def make_ancestor_evaluator(
    sumo_db_path: Path,
    *,
    ancestor_base_score: float = 0.8,
) -> "AncestorEvaluatorCallable":
    """Build an evaluator that checks ancestor-or-equal in the SUMO hierarchy.

    The returned callable follows ``prompt_eval``'s evaluator protocol:
    ``(output, expected) -> score``. It returns an ``AncestorEvalScore``
    which is richer than a bare float.

    Parameters
    ----------
    sumo_db_path:
        Path to v1's ``sumo_plus.db``.
    ancestor_base_score:
        Base score for an ancestor match before specificity scaling.
        Default 0.8 means a correct-but-coarser pick scores up to 0.8.

    Returns
    -------
    A callable ``(output: str, expected: str) -> AncestorEvalScore``.
    """
    hierarchy = SUMOHierarchy(sumo_db_path)

    def _evaluate(output: str, expected: str | None = None) -> AncestorEvalScore:
        """Score *output* type against *expected* reference type."""
        if expected is None:
            return AncestorEvalScore(
                score=0.0,
                exact=0.0,
                ancestor_match=0.0,
                specificity=0.0,
                pick=output,
                reference="",
                pick_exists=hierarchy.type_exists(output),
                reference_exists=False,
            )

        pick_exists = hierarchy.type_exists(output)
        ref_exists = hierarchy.type_exists(expected)

        # Exact match.
        if output == expected:
            return AncestorEvalScore(
                score=1.0,
                exact=1.0,
                ancestor_match=1.0,
                specificity=1.0,
                pick=output,
                reference=expected,
                pick_exists=pick_exists,
                reference_exists=ref_exists,
            )

        # Ancestor-or-equal match (pick is coarser than reference).
        if pick_exists and ref_exists and hierarchy.is_ancestor_or_equal(output, expected):
            ref_depth = hierarchy.depth(expected)
            pick_depth = hierarchy.depth(output)
            # Specificity: how much of the hierarchy depth the pick uses.
            # Add 1 to both to avoid zero-division for root types and to
            # give root types a small nonzero specificity.
            specificity = (pick_depth + 1) / (ref_depth + 1) if ref_depth >= 0 else 1.0
            score = ancestor_base_score * max(specificity, 0.05)  # Floor at 5%.
            return AncestorEvalScore(
                score=score,
                exact=0.0,
                ancestor_match=1.0,
                specificity=specificity,
                pick=output,
                reference=expected,
                pick_exists=pick_exists,
                reference_exists=ref_exists,
            )

        # Descendant match (pick is more specific than reference — also valid).
        if pick_exists and ref_exists and hierarchy.is_descendant_or_equal(output, expected):
            ref_depth = hierarchy.depth(expected)
            pick_depth = hierarchy.depth(output)
            # More specific is good — score higher than ancestor match.
            specificity = ref_depth / pick_depth if pick_depth > 0 else 1.0
            score = min(1.0, ancestor_base_score + (1.0 - ancestor_base_score) * (1.0 - specificity))
            return AncestorEvalScore(
                score=score,
                exact=0.0,
                ancestor_match=1.0,  # Still in the right branch.
                specificity=1.0 + (pick_depth - ref_depth),  # >1.0 signals more-specific.
                pick=output,
                reference=expected,
                pick_exists=pick_exists,
                reference_exists=ref_exists,
            )

        # Wrong branch — not ancestor, not descendant.
        return AncestorEvalScore(
            score=0.0,
            exact=0.0,
            ancestor_match=0.0,
            specificity=0.0,
            pick=output,
            reference=expected,
            pick_exists=pick_exists,
            reference_exists=ref_exists,
        )

    return _evaluate


# Type alias for the evaluator callable.
AncestorEvaluatorCallable = Callable[[str, str | None], AncestorEvalScore]
