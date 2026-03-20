# ADR-0018: Adopt Multi-Pass Progressive Disclosure Extraction

Status: Accepted

Date: 2026-03-19

## Context

The Predicate Canon (the PropBank/FrameNet/SUMO/VerbNet synthesis) contains
~4,663 predicates, ~7,894 SUMO types, and ~11,858 role slots. This cannot fit
in a single extraction prompt's context window, and attempting to do so would
be prohibitively expensive per extraction.

The current approach asks the LLM to produce a complete, schema-valid assertion
in one shot with a small ontology slice in context. This creates three problems:

1. The LLM must simultaneously detect relationships, map to ontology predicates,
   fill role slots, and assign entity types — each task has decreasing
   reliability when combined.
2. When the text does not contain enough information for all roles, the model
   emits `roles: {}` rather than a partial extraction.
3. The prompt can only show a tiny fraction of the ontology, so the model
   cannot make informed predicate/type choices.

However, LLMs have decent baseline knowledge of common PropBank senses,
FrameNet frames, and SUMO upper types from their training data. This knowledge
can be leveraged as a coarse filter before precision mapping with ontology data.

## Decision

1. Extraction adopts a **multi-pass progressive disclosure** architecture:

   **Pass 1 — Open extraction with top-level ontology seeding.**
   Seed ~50 top-level SUMO types into the prompt. The LLM uses its training
   knowledge to extract relationships and make coarse type/predicate
   assignments. No strict schema required. Output: triples with approximate
   labels and evidence spans.

   **Pass 2 — Predicate mapping with narrowed candidates.**
   For each extracted triple, look up candidate predicates by lemma in the
   Predicate Canon index. Show only the 3–10 matching predicates with their
   role schemas. The LLM picks the best match and maps roles.

   **Pass 3 — Entity typing with narrowed subtree.**
   For each role filler, use the predicate's role constraint to determine the
   relevant SUMO subtree. Show only the constrained subtypes. The LLM picks
   the most specific applicable type.

   **Pass 4+ — Optional enrichment.**
   FrameNet frame enrichment, Wikidata entity linking, cross-source
   corroboration. These run on stored candidates, not at extraction time.

2. **Early exit** is supported: if Pass 1 produces an unambiguous predicate
   match (78% of PropBank senses are single-sense), Pass 2 can validate
   deterministically without an LLM call.

3. **Configurable fidelity** controls how deep the passes go:
   - `coarse`: Accept top-level types (e.g., CognitiveAgent). Cheapest.
   - `moderate`: Show mid-level subtypes (~30 per branch). Default.
   - `precise`: Show full subtree to leaves. Most expensive.

   The optimal fidelity level is an empirical question (see Plan 0017 for
   the experiment design). Cost vs. accuracy tradeoffs may vary by SUMO
   branch depth and LLM training knowledge coverage.

4. Each pass only asks the LLM to make **one kind of decision** with exactly
   the context needed for that decision. This is the core principle.

5. Partial results from any pass are valid candidates under ADR-0017
   (permissive extraction). A triple with a detected relationship but no
   predicate mapping is still stored.

## Consequences

Positive:

1. Context window per call is small (hundreds of tokens, not tens of
   thousands), enabling cheaper models for bulk passes.
2. Each pass has a narrow, testable contract.
3. The LLM's existing training knowledge is leveraged rather than fought.
4. Partial extractions (relationship detected, predicate unknown) are
   first-class under permissive extraction.
5. The Predicate Canon's full depth is accessible without fitting it all in
   one prompt.

Tradeoffs:

1. More API calls per extraction (2–4 vs. 1), though each is cheaper.
2. Pass orchestration adds pipeline complexity.
3. Error propagation: a wrong coarse pick in Pass 1 sends subsequent passes
   down the wrong SUMO subtree. Validation catches this, and re-routing is
   possible, but adds latency.
4. The optimal pass structure and fidelity levels depend on empirical data
   that does not yet exist (see Plan 0017).

## Dependencies

- ADR-0017 (permissive extraction) must be adopted first — partial pass
  results must be storable.
- ADR-0019 (ancestor-aware evaluation) is needed to measure pass accuracy
  fairly.
- Plan 0017 (fidelity experiments) must produce empirical data before the
  pass structure is finalized.

## Implementation Notes

See Plan 0018 for the detailed design. Implementation is blocked on
empirical results from Plan 0017.

The name **Predicate Canon** refers to the PropBank/FrameNet/SUMO/VerbNet
synthesis — the unified linguistic ontology that onto-canon manages. This name
distinguishes the ontology asset from the pipeline code.
