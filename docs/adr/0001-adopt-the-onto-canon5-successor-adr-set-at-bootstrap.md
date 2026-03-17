# ADR-0001: Adopt the onto-canon5 successor ADR set at bootstrap

Status: Accepted  
Date: 2026-03-16

## Context

`onto-canon6` is being created only after the lineage review concluded that the
successor should restart from a cleaner architectural center of gravity.

That architecture was already documented in `onto-canon5` through:

- the successor ADR set in `onto-canon5/docs/adr/`
- the first-slice plan in `onto-canon5/docs/plans/017_first_slice_implementation_plan.md`
- the ontology runtime PoC notebook in
  `onto-canon5/notebooks/02_ontology_runtime_poc.ipynb`

The new repo needs a durable record of why it exists and what it is trying to
avoid from the earlier lineage.

## Decision

At bootstrap, `onto-canon6` adopts the successor ADR set already recorded in
`onto-canon5`, especially:

1. restart instead of continuing `onto-canon5` as the successor
2. six explicit subsystem boundaries
3. packs separate from profiles
4. explicit `open|closed|mixed` semantics
5. domain packages outside core
6. narrow extension seams instead of a general plugin framework
7. notebook-first thin-slice proof
8. separate extraction quality from canonicalization fidelity
9. borrow by subsystem, not by version
10. realign the successor with the original refactor intent

## Consequences

### Positive

- `onto-canon6` starts with a stable architectural basis instead of a vague
  restart.
- The repo has an explicit record of why it exists on day one.
- Future local ADRs can build from an already reviewed foundation.

### Negative

- Architectural changes now require local ADR updates instead of casual drift.
- The new repo still depends on donor documentation until the local ADR set is
  expanded or copied over more fully.

### Neutral

- This bootstrap ADR adopts the prior successor architecture; it does not freeze
  every detailed implementation choice forever.
