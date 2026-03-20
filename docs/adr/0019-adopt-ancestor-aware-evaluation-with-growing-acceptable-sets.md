# ADR-0019: Adopt Ancestor-Aware Evaluation with Growing Acceptable Sets

Status: Accepted

Date: 2026-03-19

## Context

Extraction evaluation has hit a measurement problem: exact-match scoring
penalizes valid alternative labels. When a golden answer says `MilitaryCommand`
and the runtime LLM picks `MilitaryOrganization` (a valid ancestor in the SUMO
hierarchy), exact-match marks it wrong. When two reasonable LLMs disagree on
which of several valid types to assign, the one that happens to differ from the
golden answer is penalized.

This was observed empirically: the LLM setting the golden answer would pick one
reasonable choice, and the runtime LLM a different reasonable choice, and the
runtime LLM was marked wrong despite both being defensible.

The SUMO type hierarchy provides a natural solution: any ancestor of the
reference label is a correct-but-coarser answer. The hierarchy defines the
acceptable set structurally, without hand-authoring.

However, not all reasonable alternatives are ancestors. A runtime LLM might
pick `DefenseContractor` where the golden says `CommercialOrganization` — both
reasonable, neither an ancestor of the other. These cases need LLM judge review,
and the set of validated alternatives should grow over time so the judge cost
amortizes to near-zero.

## Decision

1. **Ancestor-or-equal scoring** is the primary type-accuracy metric. If the
   runtime pick is an ancestor-or-equal of the reference label in the SUMO
   hierarchy, it passes. This is a deterministic O(1) check against the
   materialized ancestor closure table.

2. **Specificity scoring** is a secondary dimension. Among correct picks, more
   specific labels score higher: `depth(pick) / depth(reference)`. This
   measures whether the LLM is using the ontology's full depth.

3. **Growing acceptable set**: when a pick fails ancestor-match AND is not in
   the known-acceptable set, it routes to an LLM judge for reasonableness
   review. If the judge says reasonable, the alternative is added to a
   persistent acceptable-alternatives table. Future runs check this table
   before invoking the judge.

4. The acceptable set grows over time. First runs have high judge cost; by
   run N, most reasonable alternatives have been seen and validated. The
   review cost amortizes to near-zero.

5. **Evaluation lanes remain separate** (per ADR-0005):
   - Reasonableness/support: judged against source text.
   - Type accuracy: ancestor-aware scoring (this ADR).
   - Structural validity: deterministic local validation.
   - Canonicalization fidelity: exact-match against reference (reported but
     not treated as the primary metric).

6. The acceptable-set pattern is general-purpose and will be implemented in
   `prompt_eval` (see prompt_eval ADR-0004). The ancestor-aware evaluator is
   onto-canon-specific and lives in this repo.

7. **Fidelity-level evaluation** measures accuracy at each configurable depth
   (coarse, moderate, precise). Metrics per fidelity level tell us the
   optimal progressive disclosure strategy.

## Consequences

Positive:

1. Evaluation stops penalizing valid alternatives, giving honest accuracy
   numbers.
2. The type hierarchy provides the acceptable set structurally for ancestor
   matches — no manual curation needed.
3. LLM judge cost amortizes over time as the acceptable set grows.
4. Specificity scoring gives signal about whether finer-grained types add
   value or just add noise.
5. Fidelity-level metrics directly inform the progressive disclosure pass
   design (ADR-0018).

Tradeoffs:

1. Initial evaluation runs have higher cost (LLM judge invoked on every
   non-ancestor miss).
2. The acceptable set must be stored and maintained.
3. A bad judge ruling adds a wrong alternative permanently (mitigated by
   human review of judge decisions and periodic auditing).

## Dependencies

- v1's `sumo_plus.db` provides the ancestor closure table.
- `prompt_eval` ADR-0004 provides the growing acceptable set infrastructure.
- Plan 0017 defines the empirical experiment to baseline ancestor-match rates.

## Implementation Notes

See Plan 0017 for the ancestor-aware evaluator implementation and the fidelity
experiment design.

Key components:
- Ancestor closure query against `sumo_plus.db` `type_ancestors` table
- Custom `prompt_eval` evaluator wrapping the hierarchy check
- `GoldenSetManager` from `prompt_eval` for the growing acceptable set
- Fidelity experiment: three conditions (top-level, mid-level, full subtree)
