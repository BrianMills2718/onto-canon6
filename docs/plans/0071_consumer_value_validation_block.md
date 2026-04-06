# Consumer Value Validation Block

Status: completed
Phase status:
- Phase 0 completed
- Phase 1 completed
- Phase 2 completed
- Phase 3 completed

Last updated: 2026-04-05
Workstream: close the ROADMAP Tier 1 "real consumer value" gap

## Mission

The ROADMAP defines "done" as:

> A real OSINT investigation uses onto-canon6 as its governed assertion store
> (not just smoke tests — real investigation, real value)

The pipeline is proven end-to-end (research_v3 → onto-canon6 → DIGIMON, 63
entities + 62 relationships from the Iran disinformation investigation). What
has not been proven: **does the DIGIMON graph answer OSINT questions correctly?**

This block closes that gap. It also closes three documentation debts that have
accumulated since Plan 0070:

1. Plan 0067 is still marked "active" though all its exit criteria are met.
2. TODO.md points to the thin-semantics decision, which is already documented
   as deferred in `docs/assertion_semantics_evaluation.md`.
3. The entity resolution LLM gate passed (Plan 0039: precision 1.00, recall
   0.9643, 0 false merges, 10/10 questions correct) but `config.yaml` still
   has `default_strategy: exact` with no decision note explaining the gap.

## Acceptance Criteria

This block is complete when:

1. **Consumer query validation** — at least 3 real OSINT questions are run
   against the Iran DIGIMON graph; results are recorded with scores; the
   evidence supports a clear "thin semantics sufficient / insufficient" verdict.
2. **LLM resolution promotion decision** — a decision note exists saying
   whether `default_strategy: llm` is promoted or explicitly deferred, with
   reason.
3. **Plan 0067 closed** — status updated to "completed" with outcome summary.
4. **TODO.md reflects reality** — current frontier is the next genuine open
   question, not a decision that was already made.
5. **HANDOFF.md updated** — reflects session outcomes.

## Pre-Made Decisions

1. The assertion semantics evaluation doc (`docs/assertion_semantics_evaluation.md`)
   is authoritative — we do not re-derive it. We use its query-result evidence
   to confirm or revise the "defer Option A" verdict.
2. If 2 of 3 queries return informative answers, that is sufficient evidence for
   "thin semantics sufficient for current phase." If fewer, that triggers an
   explicit "consumer is blocked" note, which would gate Option A.
3. The LLM resolution decision uses Plan 0039's artifacts as the gate record.
   If the gate metrics were satisfied (precision ≥ 0.95, recall ≥ 0.60, false
   merges ≤ 2, answer rate ≥ 0.70, accuracy ≥ 0.50), the promotion is
   warranted unless a specific counter-reason exists.
4. `default_strategy: exact` is kept as the repo default for now because LLM
   resolution adds latency and cost, and the exact strategy is sufficient for
   small corpora. The decision note records this explicitly.
5. No new code changes are required for the query validation — use the existing
   `make query` + `make provenance` targets.

## Phase Order

### Phase 0: Documentation Cleanup

Close stale plan surfaces before running new experiments, so truth surfaces
are current.

Tasks:
1. Mark Plan 0067 completed with outcome summary.
2. Update TODO.md to reflect the true current frontier.
3. Write LLM resolution promotion decision note.

Success criteria:
1. Plan 0067 status is "completed."
2. TODO.md does not reference the thin-semantics decision as "current priority"
   (it is documented and deferred).
3. A decision note exists for LLM resolution promotion.

### Phase 1: Consumer Query Validation

Run 3 real OSINT questions against the Iran DIGIMON graph using
`scripts/digimon_query.py` and record results.

Candidate questions (pre-made):
- Q1: "Iran Islamic Revolutionary Guard Corps influence operations and proxies"
- Q2: "Iran disinformation campaigns targeting United States social media"
- Q3: "APT42 phishing and cyber operations attributed to Iran"

Scoring rubric (per question):
- 2: Answer contains relevant entities + relationship context from the graph
- 1: Answer contains relevant entities but no relationship structure
- 0: Answer returns irrelevant or empty results

Threshold: mean score ≥ 1.0 across 3 questions → "sufficient for current phase"

Tasks:
1. Run each query; record the full output.
2. Score each result against the rubric.
3. Write a run note at `docs/runs/2026-04-05_consumer_query_validation.md`.

Success criteria:
1. All 3 queries run without error.
2. Run note contains raw output + scores for each query.
3. A clear verdict is written: "sufficient" or "consumer is blocked."

### Phase 2: Assertion Semantics Evidence Update

Use the query results to update the assertion semantics evaluation doc's
"Is the Current State Sufficient?" section with concrete evidence.

Tasks:
1. Append a "Query Validation Evidence" section to
   `docs/assertion_semantics_evaluation.md` with the query scores and verdict.
2. If verdict is "consumer is blocked," open an Option A implementation plan.

Success criteria:
1. The evaluation doc contains query evidence, not just theoretical analysis.
2. The "Recommended action" is unchanged (defer) or escalated (Option A now),
   based on evidence.

### Phase 3: Final Documentation and Commit

Update HANDOFF.md and ROADMAP.md to reflect the landed state.

Tasks:
1. Update ROADMAP.md Tier 1 "Full pipeline E2E" row with query validation result.
2. Update HANDOFF.md for this session.
3. Commit all changes with [Plan #71] prefix.

## Failure Modes

1. `digimon_query.py` fails because the Iran graph is missing or the path is
   stale — check `var/iran_pipeline_run/` and graph path before starting Phase 1.
2. Query results are trivially empty because the graph has no relevant entities —
   inspect `make provenance` first to confirm graph content before scoring.
3. LLM resolution decision is made without reading Plan 0039 artifacts — must
   reference the actual run metrics, not memory.
4. Plan 0067 is closed without verifying its exit criteria are actually met —
   check each criterion against current repo state.

## Authority Chain

| Document | Governs |
|----------|---------|
| This file | Current execution block |
| `docs/assertion_semantics_evaluation.md` | Thin-semantics decision |
| `docs/runs/2026-04-01_entity_resolution_rerun_stability.md` | LLM resolution gate record |
| `docs/plans/0039_*` | LLM resolution gate specification |
| `docs/ROADMAP.md` | Tier 1 "done" definition |
