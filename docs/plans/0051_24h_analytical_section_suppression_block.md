# 24h Analytical Section Suppression Block

Status: complete
Phase status:
- Phase 1 complete
- Phase 2 complete
- Phase 3 complete
- Phase 4 complete
- Phase 5 complete

Last updated: 2026-04-02
Workstream: suppress analytical-section and late-summary spillover on repaired
chunk-003 extraction

## Purpose

Plan `0050` proved the first post-parity semantic revision was not enough:

1. it changed the chunk-003 family;
2. it did not improve the score gate; and
3. it introduced a new `belongs_to_organization` spillover candidate from the
   late quantitative summary sentence.

This block exists to answer the next explicit question:

**Can the repo suppress analytical-section and late-summary spillover more
directly, so chunk `003` stops producing retrospective limitation and late
summary candidates under the repaired parity surface?**

## Scope

This block intentionally covers only:

1. the repaired compact operational-parity prompt surface;
2. the live compact prompt kept in parity with it;
3. chunk `003` as the strict-omit analytical stress case.

Out of scope:

1. new prompt-path parity work;
2. review/judge policy changes;
3. broad multi-case benchmark reruns before the one-case stress case improves.

## Pre-Made Decisions

1. Work stays in the isolated `codex/onto-canon6-integration-planning`
   worktree.
2. All Python execution in this block must use `PYTHONPATH=src`.
3. The incoming decision note is:
   `docs/runs/2026-04-02_post_parity_semantic_recovery_decision.md`.
4. Keep the prompt-side parity repairs intact.
5. The next lever is section-heading / retrospective-summary suppression, not
   another generic concern-speaker tweak.

## Gate

This block succeeds only if:

1. one bounded analytical-section suppression change lands;
2. one post-change chunk-003 artifact exists;
3. the result says whether the late-summary spillover family shrank or not.

## Phase Order

### Phase 1: Freeze The New Miss Family

#### Tasks

1. freeze the old-vs-new chunk-003 family from Plan `0050`;
2. name the exact spillover family to target next.

#### Success criteria

1. the blocker is narrower than generic semantic quality;
2. one miss family is named explicitly.

### Phase 2: Land One Bounded Suppression Change

#### Tasks

1. add one section-heading or retrospective-summary suppression rule;
2. keep parity between live compact and repaired operational-parity prompt.

#### Success criteria

1. one bounded semantic change lands;
2. parity does not regress.

### Phase 3: Re-run The Chunk-003 Diagnostic

#### Tasks

1. rerun the one-case chunk-003 prompt_eval diagnostic;
2. capture the new artifact.

#### Success criteria

1. there is one committed post-change artifact;
2. it is directly comparable to the `0050` artifact.

### Phase 4: Classify The Result

#### Tasks

1. decide whether the spillover family shrank, shifted, or stayed flat;
2. record any narrow uncertainty separately.

#### Success criteria

1. one dominant result is named explicitly;
2. it is artifact-backed.

### Phase 5: Closeout

#### Tasks

1. write the decision note;
2. refresh `CLAUDE.md`, `HANDOFF.md`, `KNOWLEDGE.md`, `TODO.md`,
   `docs/STATUS.md`, and `docs/plans/CLAUDE.md`;
3. either close this block or activate the next narrower block.

#### Success criteria

1. the next active blocker is narrower than `0051`;
2. top-level docs truthfully reflect the new semantic status.

## Exit Criteria

This block is complete only when:

1. all five phases above meet their success criteria;
2. the worktree is clean;
3. the repo contains committed analytical-section suppression artifacts and a
   decision note.

## Outcome

Plan `0051` is complete as a failed bounded suppression attempt.

The analytical-section / staffing-summary suppression wording landed and was
verified, but the compact operational-parity spillover family worsened instead
of shrinking:

1. the late `belongs_to_organization` staffing-summary spillover survived;
2. the governance-process concern family split into two speakers instead of
   shrinking; and
3. a new retrospective `limit_capability` candidate appeared.

Decision artifact:

- `docs/runs/2026-04-02_analytical_section_suppression_decision.md`

The next active bounded block is therefore predicate-local, not
section-local: `docs/plans/0052_24h_predicate_locality_gate_block.md`.
