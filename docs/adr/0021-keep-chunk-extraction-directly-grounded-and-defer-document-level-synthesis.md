# 0021 - Keep chunk extraction directly grounded and defer document-level synthesis

## Status

Accepted.

## Context

Phase B real-document verification surfaced an important ambiguity in how to
interpret extraction errors on chunked runs.

Example from `2026-03-21_phase_b_chunk_verification.md`:

- the chunk text said `The 4th PSYOP Group, as the principal Army PSYOP unit,
  had its own commanders...`
- the extractor produced `4th PSYOP Group -> belongs_to_organization ->
  USSOCOM`

A human reading the broader report might reasonably infer that relationship
from the surrounding document context. But the current extraction boundary in
`onto-canon6` is not a free inference layer. It is a grounded producer layer:

1. the extractor is called on one explicit input text payload
2. it must emit reviewable candidate assertions
3. every candidate must carry quoted evidence spans from that same input
4. reviewers should be able to tell whether the current input directly
   supports the asserted fact

If broader document synthesis is silently folded into chunk extraction, the
review contract becomes muddy:

- some candidates are direct extractions
- some are hidden multi-span or cross-section inferences
- reviewers cannot easily tell which kind they are approving

That is especially risky in a system whose design emphasis is evidence-grounded
review and fail-loud provenance.

At the same time, full-document synthesis is valuable. The issue is not that
cross-chunk or cross-document inference is wrong. The issue is that it should
not masquerade as chunk-grounded extraction.

## Decision

`onto-canon6` keeps the following boundary explicit:

1. **Chunk/document extraction stays directly grounded to the current call
   input.**
   - If the extractor is called on one chunk, the candidate must be directly
     supported by evidence spans from that chunk.
   - If the extractor is called on one full document, the candidate must be
     directly supported by evidence spans from that document.
2. **Broader synthesis/inference is deferred to a later explicit pass.**
   - Whole-document or cross-chunk synthesis is valuable, but it must be a
     separate operator with its own provenance and failure semantics.
   - That later pass may consume multiple extracted candidates or multiple
     source slices and emit explicitly synthesized candidates.
3. **Extraction benchmarks and review decisions follow the current boundary,
   not the deferred synthesis ambition.**
   - Cases like context-only parent-organization inference remain strict-omit
     cases in the extraction fixture.
   - Reasonable whole-document inferences are not counted as extraction wins
     unless the current input directly supports them.

## Consequences

Positive:

1. Reviewability stays honest. Reviewers know extracted candidates are backed
   by the current input, not hidden synthesis.
2. Evidence spans keep their meaning. A quoted span remains the direct support
   for the candidate being reviewed.
3. Prompt and benchmark iteration can target extraction quality without
   conflating it with later reasoning quality.

Costs:

1. Some human-reasonable whole-document inferences will be rejected at the
   extraction stage.
2. Chunked extraction can under-claim relationships that would be defensible
   after broader synthesis.
3. A later synthesis layer will need a separate design and provenance
   contract.

## Deferred Follow-Up

When whole-document or cross-chunk synthesis becomes a priority, the next
slice should not weaken extraction review rules. It should add an explicit
operator with:

1. candidate or evidence inputs from multiple chunks/documents
2. explicit synthesized-output status
3. multi-source provenance
4. distinct review semantics from direct extraction

Until that exists, extraction errors should continue to be judged against the
direct-support contract.
