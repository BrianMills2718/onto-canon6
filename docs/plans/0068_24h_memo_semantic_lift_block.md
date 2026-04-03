# 24h Memo Semantic Lift Block

Status: complete

Last updated: 2026-04-02
Workstream: turn memo-path transport into graph-producing consumer value

## Mission

Use the next 24 hours to close the most valuable remaining gap exposed by Plan
`0067`:

1. `research_v3` memo artifacts can already reach governed assertion storage;
2. they still do not produce canonical entities or DIGIMON rows; therefore
3. the next block must lift memo semantics, not add more transport plumbing.

This block is complete only when a real memo artifact produces `>0` canonical
entities and `>0` DIGIMON rows through the shared-contract path.

## End Goal This Block Serves

The long-term end state is not "shared claims can be imported." The long-term
end state is:

1. active investigations produce reusable governed memory;
2. that memory contains graph structure, not just free-text statements; and
3. downstream consumers like DIGIMON get usable entities and relationships
   without manual glue.

This block lands the next irreversible step toward that end state by making the
memo path carry enough structure for graph promotion.

## Non-Goals

This block does not:

1. widen query/browse surfaces;
2. redesign DIGIMON import semantics;
3. add a second memo export format;
4. reopen prompt-quality work outside the entity-resolution seam; or
5. rerun full investigations unless required for proof.

## Pre-Made Decisions

1. Reuse `research_v3`'s existing memo entity-resolution phase; do not invent a
   second extractor.
2. Final memo closeout must always persist resolved entities when entity
   resolution is enabled.
3. Existing completed memos need a backfill/enrichment path; do not require
   whole-investigation reruns just to repair memo structure.
4. `shared_export.load_memo_claims()` must derive `entity_refs` from persisted
   memo entities using `finding_indices`.
5. The real Palantir memo from Plan `0067` is the required proof artifact.
6. The block closes only when the memo path yields `>0` canonical entities and
   `>0` DIGIMON rows on a real artifact.
7. Repo truth surfaces must be updated even if the result is still only a
   partial lift.

## Phases

### Phase 0. Authority Activation

Success criteria:

1. `CLAUDE.md` names this block as active authority;
2. `docs/plans/CLAUDE.md` lists this block as active;
3. `TODO.md` names memo semantic lift as the top priority; and
4. `var/progress/0068_memo_semantic_lift.md` records mission and gates.

### Phase 1. research_v3 Final Memo Entity Persistence

Success criteria:

1. the investigation loop runs a final entity-resolution pass before writing the
   completed memo when entity resolution is enabled;
2. completed memos persist `memo.entities`;
3. a bounded backfill command can enrich an existing memo checkpoint in place;
   and
4. tests cover the new persistence/backfill path without real LLM calls.

### Phase 2. Shared-Contract Memo Entity Export

Success criteria:

1. `shared_export.load_memo_claims()` maps memo entities onto finding-level
   `entity_refs`;
2. entity ids are deterministic and stable within a memo;
3. tests cover synthetic memo -> shared claim entity mapping; and
4. real Palantir memo claims load with non-empty `entity_refs` after enrichment.

### Phase 3. onto-canon6 Graph Proof

Success criteria:

1. the enriched real memo goes through `make pipeline-rv3-memo`;
2. the resulting review DB contains `>0` promoted graph entities;
3. the DIGIMON export contains `>0` entities and `>0` relationships; and
4. the proof note records exact commands and counts.

### Phase 4. Truth Surfaces And Closeout

Success criteria:

1. `README`, `STATUS`, `ROADMAP`, and `HANDOFF` reflect the new memo-path state;
2. any remaining semantic limitations are named explicitly;
3. `KNOWLEDGE.md` captures the durable runtime lesson; and
4. verified work is committed with clean worktrees.

## Failure Modes

1. The loop still writes completed memos with empty `entities` even though
   entity resolution is enabled.
2. The backfill path mutates memo state unsafely or drops resume metadata.
3. The export path invents entity refs unrelated to memo entity resolution.
4. The real proof still lands at `0` entities because the memo entities never
   attach to findings.
5. The block closes on synthetic tests only instead of a real memo proof.

## Verification

Minimum verification for closeout:

1. `python -m pytest -q tests/test_loop.py tests/test_shared_export.py` in
   `/home/brian/projects/research_v3`
2. `python -m pytest -q tests/integration/test_cross_project_pipeline.py` in
   `/home/brian/projects/onto-canon6`
3. real memo backfill/enrichment on the Palantir memo artifact
4. `make pipeline-rv3-memo INPUT=<enriched memo>` in `/home/brian/projects/onto-canon6`
5. full `python -m pytest -q` in both repos unless an unrelated external outage
   is explicitly documented

## Exit Condition

This block is complete when:

1. final memos persist resolved entities;
2. existing memos can be enriched without rerunning the whole investigation;
3. memo-exported shared claims carry `entity_refs`;
4. the real Palantir memo produces `>0` canonical entities and `>0` DIGIMON
   rows; and
5. the docs name the next unresolved gap truthfully.

## Outcome

Closed on 2026-04-02.

Verification outcome:

1. `research_v3` targeted tests passed:
   `33 passed` (`tests/test_loop.py`, `tests/test_shared_export.py`)
2. `onto-canon6` targeted cross-project integration tests passed:
   `4 passed` (`tests/integration/test_cross_project_pipeline.py`)
3. full `research_v3` suite passed:
   `245 passed, 2 skipped`
4. full `onto-canon6` suite passed locally
5. the real Palantir memo artifact was enriched in place with `40` persisted
   memo entities
6. the real `make pipeline-rv3-memo` proof produced `40` DIGIMON entities and
   `61` DIGIMON relationships

Documented concern:

- the first live enrichment attempt on the existing memo artifact failed with
  Gemini quota exhaustion, so the bounded repair proof used
  `config_loop_entity_backfill.yaml` to switch that run to
  `claude-sonnet-4-6`
