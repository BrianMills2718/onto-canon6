# Phase 9 Epistemic Shape

Status: Complete (bootstrap phase)


This note makes the Phase 9 slice explicit before or alongside implementation.

## Goal

Recover a narrow epistemic extension without pulling epistemic policy into the
base review workflow.

## Chosen First Slice

Operators:

1. confidence assessment
2. supersession

Attachment point:

1. accepted candidate assertions only

Confidence input:

1. explicit source-kind field on the record
2. user-entered confidence in the proved workflow

## Concrete Example

One small end-to-end epistemic chain should look like:

1. accepted candidate assertion A:
   - older reviewed claim
2. accepted candidate assertion B:
   - newer reviewed claim
3. confidence assessment on A:
   - `score = 0.72`
   - `source_kind = user`
4. supersession:
   - `A -> B`
5. epistemic report on A:
   - `status = superseded`
   - shows the confidence assessment
   - shows B as the replacement candidate

## Why This Slice

This is the smallest shape that proves real extension-local epistemic behavior:

1. reviewed assertions can be judged with explicit confidence;
2. reviewed assertions can be explicitly replaced by newer accepted claims;
3. the base review pipeline remains usable without the extension enabled.

## What We Are Not Building Yet

Not part of the first slice:

1. contradiction or tension operators;
2. full truth-maintenance;
3. epistemic state on pending-review candidates;
4. model-derived confidence as a proved production workflow.

## Path To The Fuller Version

The fuller version can grow in stages without changing the subsystem boundary:

1. add tension or contradiction records when real workflows need them;
2. add richer confidence history or recalibration when repeated updates become
   common;
3. add broader attachment points only if candidate-under-review epistemics
   become a real operational need.

The important constraint is unchanged: epistemic state stays extension-local.

## Acceptance Shape

Phase 9 should count as successful if:

1. accepted candidates can carry explicit confidence assessments;
2. accepted candidates can be superseded by newer accepted candidates;
3. the report surface can show epistemic status without changing base review
   records;
4. the notebook proof demonstrates both operators live.
