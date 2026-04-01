# 2026-04-01 Entity Resolution Value Proof

## Scope

Decision-grade comparison for the official synthetic military/OSINT corpus under
`tests/fixtures/synthetic_corpus`, executed as Plan 0030 for Plan 0025 Phase 4.

Compared surfaces:

1. governed exact resolution
2. bare extraction baseline with no identity resolution
3. governed LLM resolution

## Artifacts

1. `docs/runs/scale_test_exact_2026-03-31_221450.json`
2. `docs/runs/scale_test_bare_2026-04-01_051535.json`
3. `docs/runs/scale_test_llm_2026-03-31_222414.json`

## Headline Result

The value-proof block is now decision-grade enough to answer the main question:
LLM resolution is materially better than exact matching and the bare baseline on
pairwise recall, but it is **not** ready to become the default resolution
strategy yet because it introduces real false merges and does not beat exact on
the fixed question set.

## Metric Comparison

| Strategy | Precision | Recall | False merges | False splits | Unmatched | Ambiguous | Answer rate | Accuracy (all) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| exact | 1.00 | 0.204 | 0 | 43 | 68 | 5 | 0.80 | 0.40 |
| bare_baseline | 1.00 | 0.000 | 0 | 128 | 1 | 4 | 0.40 | 0.30 |
| llm | 0.85 | 0.500 | 6 | 34 | 56 | 2 | 0.50 | 0.30 |

## Interpretation

### What exact proves

Exact matching is a strong high-precision floor:

1. zero false merges;
2. better fixed-question accuracy than the current LLM clustering run;
3. but recall is too low to support the full cross-document value proposition.

Exact fails mainly by leaving true aliases split apart.

### What the bare baseline proves

The bare baseline is not a viable substitute:

1. it leaves every observation isolated;
2. recall is effectively zero;
3. it answers fewer questions than the governed paths.

This is the evidence that raw extraction without governed identity work is not
enough for the intended value proposition.

### What LLM clustering proves

LLM clustering is the first strategy that clearly improves the core value-proof
metric:

1. recall improves from `0.204` to `0.500`;
2. false splits fall from `43` to `34`;
3. unmatched and ambiguous observations also drop.

But the same run introduces six false merges, all concentrated in one failure
family: same-surname military/person mentions that should remain distinct.

## Failure Families

### LLM false-merge family: Smith-person overmerge

Representative false merges:

1. `John Smith` ↔ `James Smith`
2. `General John Smith` ↔ `James Smith`
3. `Gen. Smith` ↔ `James Smith`
4. `General Smith` ↔ `James Smith`
5. `James Smith` ↔ `Gen. J. Smith`

This is the main reason the LLM strategy is not promotable yet. The prompt or
validator is over-weighting shared surname and military context.

### Persistent split family: organization and installation aliases

Representative false splits still present under the LLM strategy:

1. `Special Operations Command` ↔ `USSOCOM`
2. `Special Operations Command` ↔ `U.S. Special Operations Command`
3. `Special Operations Command` ↔ `USSOCOM headquarters`
4. `Fort Bragg` ↔ `Fort Liberty`

So the LLM strategy improves recall, but the remaining misses are exactly the
alias-heavy canonicalization cases the system is supposed to solve.

### Exact-match split family

Exact matching still splits:

1. `Sarah Chen` ↔ `Dr. Chen`
2. `Fort Bragg` ↔ `Fort Liberty`
3. installation paraphrases such as `the installation`

This confirms exact matching alone is too weak as the long-term answer.

## Fixed-Question Outcome

The fixed question set does not yet support promoting the LLM strategy:

1. exact: answer rate `0.80`, accuracy over all questions `0.40`
2. llm: answer rate `0.50`, accuracy over all questions `0.30`

The LLM run answered fewer questions cleanly because some mentions still did not
resolve to unique matched ground-truth entities, while the Smith-family false
merges actively hurt correctness.

## Environment Caveats

The value-proof artifacts are usable, but one caveat is real and must stay
attached to them:

1. `_apply_judge_filter` honored the explicit `gemini/gemini-2.5-flash-lite`
   override during these runs;
2. the later auto-review path `_judge_candidate()` still used the stale
   `gemini-2.5-flash` config default during these runs;
3. that model was quota-exhausted, so the path fail-opened to `supported`.

This caveat does **not** invalidate the exact/LLM resolution comparison, but it
does mean the extraction-review stage was more permissive than intended.

## Decision

1. keep Plan 0025 active;
2. do **not** promote LLM clustering as the default resolution strategy yet;
3. keep exact matching as the safer floor while hardening the LLM path;
4. keep the governed path over the bare baseline, because the bare baseline
   proved it cannot do the job.

## Next Work

1. fix the stale `_judge_candidate()` model-selection seam so the auto-review
   path respects the bounded judge-model override;
2. harden person disambiguation around same-surname military names before any
   LLM default promotion;
3. improve alias recovery for `USSOCOM` / `U.S. Special Operations Command` and
   `Fort Bragg` / `Fort Liberty`;
4. revisit the type guard so near-equivalent ontology types can merge when the
   pack hierarchy supports it.
