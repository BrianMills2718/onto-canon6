# Investigation: compact2 vs compact3 chunk003 transfer gap

Date: 2026-03-22
Scope: explain why the `compact3` prompt-eval win did not yet transfer to the
live chunk-003 extraction path, using only persisted operational evidence and
current prompt assets.

## Question

What changed operationally between the reviewed `compact2@2` chunk-003 rerun
and the reviewed `compact3` chunk-003 run, and what does that imply about the
next useful fix?

## Evidence Target

Evidence for a useful answer must include:

1. the persisted reviewed candidate sets for both runs;
2. the source chunk text they were extracted from;
3. the relevant extraction prompt asset differences; and
4. a synthesis that distinguishes candidate-volume reduction from real
   acceptance improvement.

## Atoms

### A1

- Question: What exactly was persisted and reviewed for the `compact2@2`
  chunk-003 rerun?
- Dependencies: none
- Status: answered
- Evidence:
  - The rerun note identifies the comparison target as
    `var/real_runs/2026-03-21_compact2_real_chunk_verification_chunk003_rerun/review_state_max10.sqlite3`
    and records prompt ref
    `onto_canon6.extraction.text_to_candidate_assertions_compact_v2@2`.
    See `docs/runs/2026-03-21_compact2_real_chunk_verification_chunk003_rerun.md:6`
    and `docs/runs/2026-03-21_compact2_real_chunk_verification_chunk003_rerun.md:15`.
  - The same note records `6` structurally valid candidates:
    `5 x oc:express_concern`, `1 x oc:limit_capability`, all rejected.
    See `docs/runs/2026-03-21_compact2_real_chunk_verification_chunk003_rerun.md:43`.
  - Direct DB inspection confirmed `6` rejected candidates in
    `candidate_assertions`, with rejection notes that split into two patterns:
    five "analytical narration names no speaker; do not invent USSOCOM as an
    express_concern speaker" and one "capability-limitation mapping is too
    loose ... over-anchors the subject as PSYOP".
  - Stored evidence spans show the rejected candidates came from six
    analytical-prose spans in the chunk: two limitation/credibility sentences,
    one digital-media sentence, one bureaucratic-friction sentence, one
    ethical/legal sentence, and one conclusion/opinion sentence.
- Answer:
  `compact2@2` over-extracted six analytical-prose candidates from chunk 003.
  The dominant failure mode was invented `USSOCOM` speaker attribution on
  `oc:express_concern`, plus one loosely anchored `oc:limit_capability`
  subject.

### A2

- Question: What exactly was persisted and reviewed for the `compact3`
  chunk-003 run?
- Dependencies: none
- Status: answered
- Evidence:
  - The recovered transfer artifact summarizes the reviewed store at
    `var/real_runs/2026-03-21_compact3_real_chunk_verification_chunk003/review_state_max10.sqlite3`
    as `4` total candidates, `0` accepted, `4` rejected, verdict `negative`.
    See
    `docs/runs/2026-03-22_compact3_chunk003_transfer_recovery.md:12` and
    `docs/runs/2026-03-22_compact3_chunk003_transfer_recovery.md:48`.
  - Direct DB inspection confirmed the four rejected candidates are
    `3 x oc:express_concern`, `1 x oc:limit_capability`.
  - Stored evidence spans show the surviving candidates came from four
    middle-section analytical spans: the "effectiveness ... limited" sentence,
    the "hearts and minds ... hampered" sentence, the bureaucratic-friction
    sentence, and the ethical/legal sentence.
  - Relative to `compact2@2`, the run no longer extracted the digital-media
    sentence or the conclusion/opinion sentence.
  - The candidate shapes changed as well:
    - the `limit_capability` subject tightened from `PSYOP` to `PSYOP programs`
    - the ethical/legal `express_concern` candidate no longer uses `USSOCOM`
      as the speaker; it uses `Congressional oversight and public scrutiny`
      from the source sentence
    - despite those improvements, every candidate was still rejected with the
      uniform note that analytical prose was still being over-extracted into
      concern/limitation claims
- Answer:
  `compact3` made the live output smaller and somewhat better anchored, but it
  did not produce any accepted candidates. The remaining errors are still
  analytical-prose concern/limitation extractions, not a new failure class.

### A3

- Question: What source text in chunk 003 could support or invalidate those
  candidate patterns?
- Dependencies: none
- Status: answered
- Evidence:
  - The chunk is dominated by analytical summary prose under sections
    "Effectiveness and Limitations", "Command and Control Challenges", and
    "Ethical and Legal Considerations".
    See
    `var/real_runs/2026-03-21_phase_b_prompt_verification/chunks/01_stage1_query2/01_stage1_query2__chunk_003.md:1`,
    `var/real_runs/2026-03-21_phase_b_prompt_verification/chunks/01_stage1_query2/01_stage1_query2__chunk_003.md:7`,
    and
    `var/real_runs/2026-03-21_phase_b_prompt_verification/chunks/01_stage1_query2/01_stage1_query2__chunk_003.md:11`.
  - The core rejected spans come from sentences that describe limitations,
    friction, or scrutiny without a clean explicit speaker/actor in the same
    evidence span. See
    `var/real_runs/2026-03-21_phase_b_prompt_verification/chunks/01_stage1_query2/01_stage1_query2__chunk_003.md:5`,
    `var/real_runs/2026-03-21_phase_b_prompt_verification/chunks/01_stage1_query2/01_stage1_query2__chunk_003.md:9`,
    and
    `var/real_runs/2026-03-21_phase_b_prompt_verification/chunks/01_stage1_query2/01_stage1_query2__chunk_003.md:13`.
  - The chunk also contains a conclusion/opinion section that explicitly says
    "it is my considered opinion", which is strong evidence that at least some
    of the prose is evaluative summary rather than a clean typed assertion
    surface. See
    `var/real_runs/2026-03-21_phase_b_prompt_verification/chunks/01_stage1_query2/01_stage1_query2__chunk_003.md:19`.
- Answer:
  The chunk text supports the reviewers' objection. Most of the rejected spans
  are evaluative or analytical sentences about effectiveness, limitations, or
  oversight, not clean actor-action-object facts with an explicit local
  speaker/subject.

### A4

- Question: What materially changed between
  `prompts/extraction/text_to_candidate_assertions_compact_v2.yaml` and
  `prompts/extraction/text_to_candidate_assertions_compact_v3.yaml`?
- Dependencies: none
- Status: answered
- Evidence:
  - `compact_v3` adds a new top-level rule to prefer explicit
    actor-action-object facts over analytical summaries, evaluative narration,
    and conclusion prose. See
    `prompts/extraction/text_to_candidate_assertions_compact_v3.yaml:33`.
  - `compact_v3` adds a new omit condition for analytical narration or
    evaluative summary that lacks an explicit speaker or limited subject in the
    same span. See
    `prompts/extraction/text_to_candidate_assertions_compact_v3.yaml:74`.
  - `compact_v3` adds two new targeted checks absent from `compact_v2`:
    - do not extract `express_concern` from conclusion/opinion/summary prose
      unless a named speaker is explicit in the same span
    - do not inherit the document's main organization or topic as the
      `express_concern` speaker or `limit_capability` subject from section
      context alone
    See `prompts/extraction/text_to_candidate_assertions_compact_v3.yaml:120`
    and `prompts/extraction/text_to_candidate_assertions_compact_v3.yaml:131`.
  - The corresponding `compact_v2` file lacks those new guards and only says
    more generally that analytical narration is not a named speaker and that
    loosely anchored `limit_capability` candidates should be omitted. See
    `prompts/extraction/text_to_candidate_assertions_compact_v2.yaml:104`.
- Answer:
  `compact_v3` is not just a rename. It adds explicit anti-analytical-prose
  guidance and tighter same-span attribution rules aimed squarely at the
  chunk-003 failure pattern.

### A5

- Question: Does the operational evidence support a prompt-quality conclusion,
  a longer-chunk-context conclusion, or both?
- Dependencies: A1, A2, A3, A4
- Status: answered
- Evidence:
  - `compact_v3` reduced the rejected candidate set from `6` to `4` and
    removed the conclusion/opinion extraction, which matches the new prompt
    guidance. See
    `docs/runs/2026-03-21_compact2_real_chunk_verification_chunk003_rerun.md:43`
    and `docs/runs/2026-03-22_compact3_chunk003_transfer_recovery.md:48`.
  - `compact_v3` also improved local anchoring in at least one case
    (`PSYOP` -> `PSYOP programs`) and stopped one `USSOCOM`-as-speaker
    substitution by using a nearer source phrase.
  - But the surviving four candidates are still exactly the class the new
    prompt was meant to suppress: analytical limitation/concern claims from
    the middle chunk sections rather than explicit actor-action-object facts.
- Answer:
  Both factors still matter, but the evidence now weighs more toward a
  full-chunk operational transfer problem than a simple prompt-asset mismatch.
  `compact_v3` clearly influenced live behavior in the intended direction, so
  prompt wording is not irrelevant. But because the remaining rejected set is
  still the same analytical-prose class, the dominant unresolved problem is
  that the full chunk context still pushes the model into extracting
  review-rejected concern/limitation claims.

## Assumptions Register

| # | Assumption | Confidence | How to verify | Round | Status |
|---|-----------|------------|---------------|-------|--------|
| 1 | The `compact2@2` comparison target is the rerun DB at `var/real_runs/2026-03-21_compact2_real_chunk_verification_chunk003_rerun/review_state_max10.sqlite3`. | High | Read the rerun run note and inspect the DB contents. | 1 | Confirmed |
| 2 | The `compact3` run used `prompts/extraction/text_to_candidate_assertions_compact_v3.yaml` with prompt ref `onto_canon6.extraction.text_to_candidate_assertions_compact_v3@1`. | Medium | Check for persisted run provenance; if absent, downgrade to chronology-based inference. | 1 | Partially confirmed: chronology-supported, DB-unproven |
| 3 | A smaller rejected candidate set can still indicate no transfer if acceptance remains zero. | High | Compare reviewed counts and rejection rationales across both runs. | 1 | Confirmed |

## Contractions

After the first parallel batch, the search space contracted substantially:

1. there is no sign of a new live failure class in `compact3`;
2. the prompt revision did have operational effect, because it removed two
   rejected candidates and improved some role anchoring;
3. the unresolved problem is therefore narrower than "prompt-eval and live
   prompt are unrelated";
4. the dominant question is now why the remaining middle-section analytical
   prose still survives the stronger same-span attribution guidance.

## Synthesis

### Root Cause

The current best explanation is a partial transfer failure:

1. `compact_v3` successfully suppresses some of the weakest chunk-003
   extractions, especially conclusion/opinion-style material; but
2. on the full chunk, the model still maps middle-section analytical prose
   about limitations, friction, and scrutiny into `oc:express_concern` and
   `oc:limit_capability` even when those sentences are not clean local
   actor-action-object facts.

This is not the same as "no live effect." The live effect is visible. It is
just not sufficient for transfer.

### Impact

1. The repo should not promote `compact3` based on the sentence-level win.
2. The transfer gap is now more specific: the remaining false positives are the
   four analytical-prose spans that survive even under the stricter prompt.
3. The next experiment should focus on those surviving spans, not on broad new
   prompt churn.

### Recommendation

1. Compare the actual extraction prompt render used on chunk 003 for
   `compact2@2` and `compact3@1` if that render can be reconstructed.
2. Add the four surviving middle-section spans as frozen prompt-eval cases,
   ideally with both sentence-only and short-local-context variants.
3. If sentence-only prompt-eval omits them but short-context prompt-eval keeps
   extracting them, treat longer context as the dominant remaining source of
   error.
4. If both sentence-only and short-context prompt-eval still extract them,
   tighten the predicate-specific omission guidance before any broader
   operational rerun.

### Confidence

Medium-high.

The candidate counts, stored payloads, rejection notes, source text, and prompt
delta all align. What remains unproven is the exact rendered operational prompt
and any provider-side dynamics during the original run.

### Open Questions

1. Can the exact operational prompt render for the `compact3` chunk-003 run be
   reconstructed from observability history?
2. Does the surviving false-positive set disappear if the same four spans are
   evaluated in shorter local windows rather than the full chunk?
3. Is `budget_extraction` itself nudging the model toward analytical-summary
   predicates on prose-heavy chunks even when the prompt says to omit them?
