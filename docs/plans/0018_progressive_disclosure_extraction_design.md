# Progressive Disclosure Extraction Design

Status: planned (blocked on Plan 0017 empirical results)

Updated: 2026-03-19

## Purpose

Design the multi-pass progressive disclosure extraction pipeline described in
ADR-0018. This plan is deliberately blocked on empirical results from Plan 0017
(fidelity experiments) because the pass structure depends on data we don't have
yet.

## What We Know

1. The Predicate Canon (~4,663 predicates, ~7,894 SUMO types, ~11,858 role
   slots) cannot fit in a single extraction prompt.
2. LLMs have decent baseline knowledge of common PropBank, FrameNet, and
   upper SUMO types.
3. 78% of PropBank senses are unambiguous (single sense per lemma).
4. The current single-shot extraction produces `roles: {}` when the text
   lacks enough information for all role slots.
5. Partial extractions are now storable under ADR-0017 (permissive extraction).

## What We Don't Know (Plan 0017 Will Tell Us)

1. **Ancestor match rate on coarse picks**: What fraction of top-level SUMO
   type picks are ancestors of the correct fine-grained type? This determines
   whether Pass 1 coarse picks are useful starting points or noise.
2. **Wrong-branch rate**: How often does the LLM pick a type from the wrong
   SUMO subtree entirely? High wrong-branch rates mean Pass 1 needs more
   guidance.
3. **Fidelity cost-accuracy tradeoff**: Is there a meaningful accuracy
   difference between showing 30 subtypes vs. the full subtree? If not,
   always show the full subtree. If yes, the moderate fidelity level earns
   its keep.
4. **Model variation**: Do different models have significantly different
   baseline SUMO knowledge? This determines whether the pass structure
   should be model-adaptive.

## Proposed Pass Structure (Subject to Empirical Validation)

### Pass 1: Open extraction with top-level SUMO seeding

- **Input**: Raw text + ~50 top-level SUMO types + "use PropBank senses if
  you know them"
- **Output**: Triples `(entity_a, relationship_type, entity_b)` with
  coarse type assignments and evidence spans
- **Model**: Cheap/fast (gemini-2.5-flash-lite or similar)
- **Contract**: No strict schema. Partial results valid.

### Pass 2: Predicate mapping with narrowed candidates

- **Input**: Pass 1 triples
- **For each triple**: Look up candidate predicates by lemma in the
  Predicate Canon index. Show only the 3-10 matching predicates with their
  role schemas.
- **Output**: Mapped assertions with predicate IDs and role structure
- **Early exit**: If lemma maps to exactly one PropBank sense (78% of
  cases), validate deterministically. No LLM call needed.
- **Model**: Same as Pass 1, or task-appropriate

### Pass 3: Entity typing with narrowed subtree

- **Input**: Pass 2 mapped assertions
- **For each role filler**: Use the predicate's role constraint to find the
  relevant SUMO subtree. Show the subtypes at the configured fidelity level.
- **Output**: Fully typed assertions
- **Fidelity**: Configurable (coarse/moderate/precise). Plan 0017 results
  determine the default.
- **Model**: Same or task-appropriate

### Pass 4+: Optional enrichment (future)

- FrameNet frame mapping (deterministic via SemLink when available)
- Wikidata entity linking
- Cross-source corroboration
- Role-filling enrichment on stored partial candidates

## Design Decisions Deferred Until Empirical Data

1. **Default fidelity level**: coarse vs moderate vs precise — depends on
   Plan 0017 cost-accuracy results.
2. **Whether Pass 3 is always needed**: If ancestor match rate at top-level
   is >90%, Pass 3 may be optional for most extractions.
3. **Whether a third API call is needed for deep subtrees**: If moderate
   (~30 types) doesn't reach leaves, a targeted third call could narrow
   further. But this may not be worth the complexity.
4. **Model selection per pass**: Whether different models should be used for
   different passes (cheap for Pass 1, precise for Pass 2).
5. **Batch vs. sequential**: Whether Pass 2 can batch multiple triples into
   one LLM call (depends on context window constraints).

## Integration Points

- **Permissive extraction (Plan 0016)**: Partial results from any pass are
  stored as candidates.
- **Ancestor-aware evaluation (Plan 0017)**: Measures type accuracy at each
  fidelity level.
- **Predicate Canon bridge (future)**: Pass 2 needs a predicate index
  searchable by lemma. v1's `sumo_plus.db` has this in the `predicates`
  table. Bridge work is needed to make it accessible.

## Acceptance Criteria (for this plan to become active)

- [ ] Plan 0017 fidelity experiment is complete with results
- [ ] Ancestor match rate, wrong-branch rate, and cost data are documented
- [ ] Design decisions above are resolved based on empirical data
- [ ] Build order and file list are specified

## Relationship to Prior Work

- Implements: ADR-0018 (progressive disclosure)
- Blocked by: Plan 0017 (empirical data)
- Depends on: Plan 0016 (permissive extraction for partial results)
- Depends on: v1's Predicate Canon data (predicates table, role slots,
  SUMO hierarchy)
- Eventually feeds: Digimon build integration (the assertion interchange
  format should carry pass-level provenance)
