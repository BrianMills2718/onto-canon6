# Entity Resolution LLM Promotion Decision

Date: 2026-04-05
Closes: open gap — `config.yaml` still has `default_strategy: exact` despite
Plan 0039 gate being satisfied.

## Gate Specification (from Plan 0034)

| Criterion | Threshold | Required |
|-----------|-----------|----------|
| Source documents survive extraction | 25/25 | Yes |
| Pairwise precision | ≥ 0.95 | Yes |
| Pairwise recall | ≥ 0.60 | Yes |
| False merges | ≤ 2 | Yes |
| Fixed-question answer rate | ≥ 0.70 | Yes |
| Fixed-question accuracy | ≥ 0.50 | Yes |
| q04, q08, q09 no longer wrong/unanswered | — | Yes |

## Gate Results (Plan 0039, 2026-04-01)

Two fresh reruns on new DBs with `LLM_CLIENT_TIMEOUT_POLICY=allow`:

| Run | Precision | Recall | False merges | Answer rate | Accuracy |
|-----|-----------|--------|--------------|-------------|----------|
| `scale_test_llm_2026-04-01_145141.json` | 1.00 | 0.9643 | 0 | 1.00 | 1.00 |
| `scale_test_llm_2026-04-01_152927.json` | 1.00 | 0.9346 | 0 | 1.00 | 1.00 |

Both runs clear all gate thresholds. q04, q08, q09 are correctly answered on
both runs (confirmed in Plan 0039 closeout and Plan 0035 outcomes).

**Gate verdict: PASSED.**

## Decision: Do Not Promote to Default

The gate passed. LLM resolution is accurate enough to be default. However,
**`default_strategy: exact` is intentionally retained** for the following reasons:

1. **Latency and cost.** LLM resolution adds one batch LLM call per
   `resolve-all` invocation. For small corpora (current typical use: 20-60
   claims per investigation), the exact strategy is fast and free. The LLM
   strategy becomes cost-effective only when exact-match recall misses
   matter — i.e., when aliases like `IRGC` vs. `Islamic Revolutionary Guard
   Corps` exist in the same corpus.

2. **Corpus size.** The gate was passed on a 25-document synthetic PSYOP corpus.
   The current production use cases are single-investigation memos (20-60
   claims). At this scale, the exact strategy resolves correctly because
   entity names within a single investigation tend to be consistent.

3. **Opt-in is the right default.** LLM resolution is a quality enhancement for
   corpora with alias drift. Making it opt-in via `--strategy llm` in CLI
   or `resolution.default_strategy: llm` in config means operators choose it
   when they know they need it, rather than paying for it on every run.

## What This Decision Is Not

This is NOT a deferral for quality reasons. The LLM strategy works. It passes
the gate. The choice to keep `exact` as default is a cost/latency optimization,
not a quality concern.

## Practical Guidance for Operators

Use `--strategy llm` (CLI) or `default_strategy: llm` (config) when:
- Corpus spans multiple sources that may name the same entity differently
- Investigation scope is a full research session (50+ claims)
- Alias drift is expected (e.g., organization abbreviations, informal references)

Use `exact` (default) when:
- Single-investigation memo import (20-60 claims, consistent naming)
- Speed matters and you expect consistent entity naming from one source

## Config Change (not made — decision is to keep exact)

If LLM strategy were promoted, the change would be:

```yaml
# config/config.yaml
resolution:
  default_strategy: llm  # was: exact
```

This change is NOT being made now. It is pre-approved if a production use case
demonstrates that exact-match misses are causing downstream errors.

## References

- Plan 0033: `docs/plans/0033_24h_entity_resolution_answerability_block.md`
- Plan 0034: `docs/plans/0034_24h_entity_resolution_clean_measurement_block.md`
- Plan 0039: `docs/plans/0039_24h_entity_resolution_rerun_stability_block.md`
- Gate artifacts: `docs/runs/scale_test_llm_2026-04-01_145141.json`,
  `docs/runs/scale_test_llm_2026-04-01_152927.json`
- Stability note: `docs/runs/2026-04-01_entity_resolution_rerun_stability.md`
