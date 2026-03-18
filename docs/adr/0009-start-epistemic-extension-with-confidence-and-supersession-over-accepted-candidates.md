# ADR-0009: Start epistemic extension with confidence and supersession over accepted candidates

Status: accepted

## Context

Phase 9 recovers one of the useful ideas from the `onto-canon` lineage:
epistemic reasoning over governed assertions. The successor needs that
capability, but it should not start with a full contradiction engine or a
truth-maintenance runtime.

The main design questions were:

1. which epistemic operators belong in the first slice;
2. whether epistemic state should attach to accepted candidates only or also to
   candidates still under review;
3. whether confidence should be user-entered, model-derived, or both.

## Decision

The first epistemic slice starts with:

1. confidence assessments;
2. explicit supersession from one accepted candidate to another;
3. attachment only to accepted candidate assertions;
4. an explicit `source_kind` on confidence assessments, while the proved
   workflow uses user-entered confidence first.

## Why

This is the smallest useful operator set that still proves extension-local
epistemic behavior:

1. confidence makes reviewed assertions inspectably stronger or weaker without
   changing base review semantics;
2. supersession handles the common case where a newer accepted assertion should
   replace an older one;
3. attaching only to accepted candidates avoids mixing epistemic judgment with
   pre-review workflow state.

Starting broader with tension, contradiction, or full belief-state management
would reintroduce too much policy and coordination too early.

## Expansion Path

This narrow slice is not the final epistemic model. The intended path to a
broader version is:

1. Phase 9:
   - confidence assessments
   - supersession records
   - accepted-candidate target only
2. Later broadening when real workflows justify it:
   - add tension or contradiction records
   - add richer confidence history or model-derived confidence workflows
   - add attachment points beyond accepted candidates only if real review flows
     need them

The same architectural rule remains in force: epistemic state stays in an
extension-local package and does not become a hidden requirement for the base
workflow.

## Consequences

Positive:

1. Phase 9 remains small and independently verifiable.
2. The successor regains meaningful epistemic capability without centralizing
   the runtime.
3. The path to a broader extension remains explicit.

Negative:

1. The first slice does not support contradiction or tension reasoning.
2. Pending-review candidates do not receive epistemic state in this phase.
3. Model-derived confidence is not yet proved as a real workflow, even though
   the record shape names its source kind.

## Related

1. `docs/plans/0001_successor_roadmap.md`
2. `docs/plans/0003_phase9_epistemic_shape.md`
