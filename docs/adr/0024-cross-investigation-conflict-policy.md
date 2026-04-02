# ADR 0024: Cross-Investigation Conflict Policy

Date: 2026-04-02
Status: adopted

## Context

onto-canon6 detects tensions (role_filler_conflict) between promoted assertions.
On a combined Booz Allen + EU sanctions corpus, 871 tensions and 6 corroboration
groups were detected. However, there is no policy for when tensions should
trigger action vs. be informational.

Tensions arise naturally and correctly when:
- Multiple assertions about the same predicate have different fillers
  (e.g., different lobbying expenditure amounts for the same company in
  different years — each is correct for its timeframe)
- Assertions from different investigations overlap on entity references

## Decision

**v1: Flag-only, no auto-resolution.**

1. **Tensions are informational, not blocking.** The tension engine reports
   all role_filler_conflicts. No tension prevents promotion or export.

2. **Cross-investigation metadata.** When the epistemic report includes
   tensions, it should include the source_kind of both assertions so
   consumers can distinguish same-investigation tensions from
   cross-investigation tensions.

3. **Corroboration groups are informational.** Multiple assertions from
   different sources supporting the same predicate+entity pattern are
   reported as corroboration groups. This increases confidence but does not
   auto-update confidence scores in v1.

4. **No auto-resolution.** Resolving which assertion is "correct" when two
   investigations disagree requires domain judgment. onto-canon6 flags the
   conflict; consumers or humans decide.

5. **Escalation path.** When a consumer needs auto-resolution, the
   architecture supports it via the grounded-research adjudication pipeline
   (emit dispute requests, receive arbitration results). Not implemented in v1.

## Consequences

- Agents browsing the knowledge base see tension reports in epistemic output
- No data is silently discarded due to conflict
- Consumers who need conflict resolution must implement it downstream
  (or wire the grounded-research adjudication pipeline)
- The existing tension detection infrastructure is sufficient for v1

## Alternatives Considered

1. **Auto-merge on corroboration.** Rejected: corroboration should increase
   confidence, but auto-updating confidence requires a well-defined policy for
   combining scores from different confidence sources.

2. **Auto-block on conflict.** Rejected: most tensions are legitimate
   (different time periods, different sources reporting the same fact slightly
   differently). Blocking would prevent most real data from being usable.

3. **Require manual review of all tensions.** Rejected: 871 tensions on a
   small corpus makes manual review impractical. The flag-only approach lets
   consumers focus on the tensions that matter to their use case.
