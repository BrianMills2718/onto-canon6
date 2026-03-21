# ADR-0023: Require a chunk-level transfer evaluation slice before live prompt promotion

Date: 2026-03-21
Status: Accepted

## Context

The post-bootstrap extraction R&D workstream now has evidence for a specific
evaluation gap:

1. sentence-level prompt-eval cases can recover a failure mode cleanly;
2. the same prompt-family improvement can still fail on the full
   multi-paragraph operational chunk; and
3. the resulting disagreement is large enough that prompt-eval wins alone are
   no longer a trustworthy promotion gate for live extraction defaults.

The chunk-003 work made this concrete:

1. the `v4` prompt-eval fixture recovered the narrator-analysis strict-omit
   cases under `compact`;
2. the same family of guidance still failed on the full chunk through the live
   `extract-text` path; and
3. rendered-prompt comparison showed that the bigger gap is the user payload
   and chunk context, not only residual system-prompt wording differences.

If the repo continues to treat sentence-level prompt-eval as the only
promotion gate, it will keep promoting changes that do not actually transfer to
the real extraction workflow.

## Decision

`onto-canon6` will add an explicit chunk-level transfer evaluation slice before
promoting new extraction prompts into the repo-default live extraction path.

That slice must:

1. operate on real or fixture-backed multi-paragraph chunks, not only isolated
   sentence cases;
2. preserve reviewability and directly grounded extraction semantics;
3. report transfer explicitly, not infer it from sentence-level benchmark
   improvement; and
4. sit alongside the current sentence-level prompt-eval lane rather than
   replacing it.

Sentence-level prompt-eval remains useful for fast failure isolation and prompt
comparison. It is no longer sufficient evidence by itself for live prompt
promotion.

## Consequences

### Positive

1. live extraction promotion decisions will be based on evidence that matches
   the real chunked workflow more closely;
2. the repo can keep using sentence-level prompt-eval for fast iteration
   without overclaiming its transfer value; and
3. chunk-level narrator/speaker/context failures become first-class measured
   behavior instead of post hoc surprises in analyst review.

### Negative

1. the evaluation stack becomes more complex because there is now an explicit
   transfer layer to maintain;
2. prompt changes will take longer to promote because they need one more proof
   step; and
3. some previously “good enough” sentence-level wins will be blocked from
   promotion until chunk-level evidence exists.

## Alternatives Considered

### Keep using sentence-level prompt-eval as the only promotion gate

Rejected. The chunk-003 evidence already shows that this is no longer
trustworthy.

### Skip prompt-eval and judge only through real chunk reviews

Rejected. That would throw away the fastest discriminative lane and make prompt
iteration much slower and noisier.

### Immediately rewrite the extraction architecture again

Rejected. The current evidence points first to an evaluation-transfer gap, not
yet to a necessary architecture replacement.
