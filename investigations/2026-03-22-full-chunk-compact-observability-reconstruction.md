# Investigation: full-chunk compact extraction observability reconstruction

Date: 2026-03-22
Scope: reconstruct the exact full-chunk chunk-003 extraction calls from shared
llm_client observability and compare `compact_v2@1`, `compact_v2@2`, and
`compact_v3@1` on the real operational surface.

## Question

Did the live `compact3` chunk-003 extraction run differ from the earlier
`compact2` runs in any meaningful way besides the system prompt, and what did
the raw model output look like before review?

## Evidence Target

Evidence for a useful answer must include:

1. the raw llm_client call records for the three chunk-003 live runs;
2. prompt/model/task/provenance comparison across those records;
3. the raw structured response payloads before review-store projection; and
4. a synthesis about whether the remaining transfer gap is prompt wording,
   render shape, or full-chunk behavior.

## Atoms

### A1

- Question: Can the exact chunk-003 live calls be found in llm_client
  observability?
- Dependencies: none
- Status: answered
- Evidence:
  - The shared observability DB is
    `/home/brian/projects/data/llm_observability.db`.
  - `llm_calls` contains `project`, `messages`, `response`, `task`, `trace_id`,
    and `prompt_ref`.
  - Querying by `messages like '%chunk_003%'` and March 21 timestamps returned
    exactly three live extraction rows:
    - `onto-canon6-compact2-real-chunk-003`
    - `onto-canon6-compact2-real-chunk-003-rerun`
    - `onto-canon6-compact3-real-chunk-003`
- Answer:
  Yes. The exact full-chunk operational calls are preserved in raw
  observability.

### A2

- Question: What changed across the three live calls at the prompt/render
  level?
- Dependencies: A1
- Status: answered
- Evidence:
  - All three calls use the same model:
    `openrouter/deepseek/deepseek-chat`.
  - All three calls use the same task: `budget_extraction`.
  - All three calls share the same `trace_id`:
    `onto_canon6.extract.158723600359dde1`.
  - The user-message hash is identical across all three runs
    (`user_sha=05a5b228f30931db`), so the chunk render and user-side payload
    were the same.
  - The system-message hash changes across runs:
    - `compact_v2@1`: `fa0a442417c299f1`
    - `compact_v2@2`: `b4be2cc1ad8332d4`
    - `compact_v3@1`: `dc4234a4aa25c129`
  - Only `compact_v3@1` contains the new anti-analytical-prose markers:
    - "Prefer explicit actor-action-object facts over analytical summaries"
    - "the sentence is only analytical narration or evaluative summary"
    - "conclusion sections, opinion sections, and summary prose usually"
    - "do not inherit the document's main organization"
- Answer:
  The live operational surface stayed constant on model, task, and user-side
  chunk render. The meaningful change from the rerun to `compact3` was the
  system prompt only.

### A3

- Question: What raw candidate payloads did each live run return before review?
- Dependencies: A1
- Status: answered
- Evidence:
  - `compact_v2@1` raw response contained `5` candidates:
    `4 x oc:express_concern`, `1 x oc:limit_capability`.
  - `compact_v2@2` raw response contained `6` candidates:
    `5 x oc:express_concern`, `1 x oc:limit_capability`, including the
    conclusion/opinion span.
  - `compact_v3@1` raw response contained `4` candidates:
    `3 x oc:express_concern`, `1 x oc:limit_capability`.
  - The `compact3` raw response removed:
    - the digital-media concern sentence
    - the conclusion/opinion concern sentence
  - But the `compact3` raw response still returned these analytical-prose
    candidates:
    - concern over "cultural misunderstandings..." with speaker `USSOCOM`
    - concern over "hearts and minds ... hampered ..." with speaker `USSOCOM`
    - capability limitation from the bureaucratic-friction sentence with
      subject `PSYOP programs`
    - concern over ethical/legal questions with speaker
      `Congressional oversight and public scrutiny`
- Answer:
  `compact3` improved the raw full-chunk output but did not eliminate the core
  false-positive class. The surviving raw candidates are still analytical-prose
  concern/limitation extractions.

### A4

- Question: What does that imply about the remaining transfer gap?
- Dependencies: A2, A3
- Status: answered
- Evidence:
  - Because the user-side chunk render stayed identical, the `compact3`
    improvement cannot be explained by different chunk text or user context.
  - Because the system prompt changed and the candidate set shrank from `6` to
    `4`, the stronger prompt wording did affect the full-chunk output.
  - Because the remaining four raw candidates are still the exact
    analytical-prose class targeted by the new rules, the stronger system
    prompt alone is not sufficient on the full chunk.
- Answer:
  The remaining transfer gap is now best described as a full-chunk operational
  behavior problem under the same chunk render, not a simple provenance or
  fixture-mismatch problem. The prompt got better, but the full chunk still
  induces four false positives.

## Assumptions Register

| # | Assumption | Confidence | How to verify | Round | Status |
|---|-----------|------------|---------------|-------|--------|
| 1 | The March 21 chunk-003 live runs were logged to the shared llm_client DB. | High | Query raw `llm_calls` by date and chunk/path markers. | 1 | Confirmed |
| 2 | Matching `user_sha` across the three rows means the user-side chunk render was identical. | High | Compare the rendered user-message hashes and lengths. | 1 | Confirmed |
| 3 | The raw `response` column stores the pre-review structured output directly for these calls. | High | Parse the JSON payload and compare counts against the review DB. | 1 | Confirmed |

## Contractions

The search space contracted materially:

1. the missing compact3 operational provenance is no longer missing;
2. there is no evidence that chunk text, model, task, or user-side render
   changed between the rerun and `compact3`;
3. the operative difference is the stronger `compact3` system prompt; and
4. that prompt clearly helped, but not enough to make the full chunk transfer.

## Synthesis

### Root Cause

The repo is no longer dealing with an ambiguous "maybe the wrong asset ran"
problem. The raw observability history proves that `compact3` really did run on
the same full chunk with the intended stronger system prompt.

The unresolved problem is that the full multi-paragraph chunk still elicits
analytical-prose concern/limitation candidates even after the prompt tells the
model not to do that.

### Impact

1. The repo should stop spending time on proving that `compact3` was or was not
   the prompt used in the live run. That is now settled.
2. The remaining extraction-quality question is narrower: what about the full
   chunk context keeps reintroducing these four candidates?
3. Local prompt-eval and local-context fixtures are still valuable, but they no
   longer look like the primary blocker.

### Recommendation

1. Use the reconstructed full-chunk raw outputs as the operational baseline for
   the next experiment.
2. Compare full-chunk chunking/render strategies against the same prompt rather
   than doing another broad prompt rewrite first.
3. If another prompt change is attempted, evaluate it directly against this
   reconstructed full-chunk baseline, not just sentence-level or short-context
   cases.

### Confidence

High.

The conclusion is grounded in preserved raw call records, not only downstream
review artifacts or run notes.
