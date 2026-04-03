# 24h End-Goal Convergence Block

Status: active

Last updated: 2026-04-02
Workstream: move from internal proof to consumer-led end-goal execution

## Mission

Use the next 24 hours to push `onto-canon6` materially closer to the actual end
goal:

1. a real investigation loop can feed it without bespoke manual glue;
2. the shared-contract path is the operational path, not just a proved side path;
3. the repo's truth surfaces match reality; and
4. the cross-project pipeline is reproducible without hidden workstation
   assumptions.

This block exists because the repo has enough internal proof already. The
highest-value remaining work is now:

1. consumer-path adoption;
2. reproducibility hardening; and
3. truthfulness about what is and is not operationally complete.

## End Goal This Block Serves

The long-term end state named in `docs/ROADMAP.md` is:

1. a real OSINT investigation uses `onto-canon6` as its governed assertion
   store;
2. cross-project data flows run end to end without manual intervention; and
3. downstream consumers depend on stable, truthful contracts.

This 24h block does **not** claim to finish the whole program. It does need to
land the next irreversible step toward that state: make the active
`research_v3` memo path feed the governed store through the shared contracts and
prove the resulting pipeline on a real memo artifact.

## Non-Goals

This block does not:

1. widen ontology/runtime capability for its own sake;
2. add another query surface;
3. revisit prompt-tuning loops unless a regression blocks the consumer path;
4. scale entity resolution beyond the current proven corpus; or
5. build a new orchestration system.

## Pre-Made Decisions

1. The next block is **consumer-path convergence**, not more query widening.
2. The active `research_v3` loop memo is the next valuable producer, not a new
   synthetic fixture.
3. The operational integration path should prefer shared `ClaimRecord`
   contracts over repo-specific adapters whenever that is feasible.
4. Hidden workstation defaults must be removed from the operational pipeline.
5. README / ROADMAP / STATUS / HANDOFF must be updated truthfully even when that
   makes the repo sound less complete than before.
6. If there is a conflict between "keep old convenience behavior" and "fail
   loud and reproducible," reproducibility wins.
7. The block closes only after a real memo-driven pipeline proof is recorded.

## Phases

### Phase 0. Authority Activation

Make this block the explicit active execution authority.

Success criteria:

1. `CLAUDE.md` names this block as the active plan;
2. `docs/plans/CLAUDE.md` lists this block as active;
3. `TODO.md` names this block as the current 24h execution block; and
4. a progress file records the mission and acceptance criteria for compaction
   safety.

### Phase 1. Truth And Reproducibility Hardening

Remove obvious truth-surface drift and hidden-environment coupling from the repo
surface that operators are supposed to trust.

Success criteria:

1. stale claims like the old test count are corrected;
2. command labels like `make test` are truthful about what they run;
3. the main cross-project pipeline script fails loud instead of silently
   skipping or defaulting to local workstation artifacts; and
4. the pipeline script no longer depends on hardcoded `Path.home()/projects/...`
   imports.

### Phase 2. Shared-Contract Memo Export

Promote the active `research_v3` memo path into the shared-contract flow.

Success criteria:

1. `research_v3/shared_export.py` can load memo findings into shared
   `ClaimRecord` objects;
2. the export maps memo confidence / corroboration / source URLs truthfully;
3. tests cover the new memo export surface; and
4. `research_v3` integration docs no longer claim the adapter is "not yet
   built" when it exists.

### Phase 3. Memo-Driven Pipeline Convergence

Make the real pipeline script accept the `research_v3` memo path through the
shared contracts and prove it end to end.

Success criteria:

1. `scripts/full_pipeline_e2e.py` supports memo-driven import explicitly;
2. the pipeline uses shared claims for graph, memo, and grounded-research
   inputs;
3. the pipeline fails loud on submission / acceptance / promotion mismatches;
4. a Make target exposes the memo path cleanly; and
5. integration tests cover the memo-driven path or its core shared helper.

### Phase 4. Real Proof And Closeout

Run the landed memo-driven pipeline on a real `research_v3` memo artifact and
record the outcome truthfully.

Success criteria:

1. one real memo artifact is imported through the landed path;
2. the run produces a governed DB plus DIGIMON export artifact;
3. a proof note under `docs/runs/` records the exact command, source artifact,
   and resulting counts; and
4. `ROADMAP.md`, `STATUS.md`, and `HANDOFF.md` reflect the landed state and the
   next unresolved gap truthfully.

## Failure Modes

1. The repo lands another special-case `research_v3` path instead of promoting
   the shared-contract seam.
2. The pipeline still "works on Brian's machine" because of implicit sibling
   repo assumptions.
3. The proof note overclaims consumer adoption when only a repo-local proof was
   achieved.
4. The memo path imports claims but loses confidence/provenance fields that the
   end goal needs.
5. The block closes on tests only, without a real memo-driven run.

## Verification

Minimum verification for closeout:

1. `python -m pytest -q` in `/home/brian/projects/onto-canon6`
2. `python -m pytest -q tests/test_shared_export.py` in `/home/brian/projects/research_v3`
3. one real memo-driven `make pipeline-rv3-memo INPUT=<memo.yaml>` run in
   `/home/brian/projects/onto-canon6`
4. `make smoke` in `/home/brian/projects/onto-canon6`

## Exit Condition

This block is complete when:

1. the active `research_v3` memo path can feed `onto-canon6` through shared
   contracts;
2. the operational pipeline no longer depends on hidden workstation imports or
   implicit fallback artifacts;
3. the proof is recorded on a real memo; and
4. the authority docs name the next unresolved gap truthfully instead of
   gesturing at general progress.
