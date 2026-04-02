# 24h Predicate-Locality Gate Block

Status: complete
Phase status:
- Phase 1 complete
- Phase 2 complete
- Phase 3 complete
- Phase 4 complete
- Phase 5 complete

Last updated: 2026-04-02
Workstream: tighten predicate-local gating for chunk-003 semantic spillover
after Plan `0051`

## Purpose

Plan `0051` proved that another generic analytical-section suppression rule is
not enough. The spillover family got worse under the repaired parity surface.

This block exists to answer the next narrower question:

**Can the repo suppress chunk-003 spillover by tightening predicate-local
eligibility for `express_concern` and `limit_capability`, instead of adding
more section-level omission language?**

## Scope

This block intentionally covers only:

1. the repaired compact operational-parity prompt surface;
2. the live compact prompt kept in parity with it;
3. chunk `003` as the strict-omit stress case;
4. predicate-local gating for:
   - `express_concern`
   - `limit_capability`
   - preservation of the existing staffing-summary omission rule

Out of scope:

1. new prompt-path parity work;
2. review/judge policy changes;
3. broad multi-case benchmark reruns before the one-case stress case improves;
4. schema/runtime post-processing outside the prompt surface

## Pre-Made Decisions

1. Work stays in the isolated `codex/onto-canon6-integration-planning`
   worktree.
2. All Python execution in this block must use `PYTHONPATH=src`.
3. The incoming decision note is:
   `docs/runs/2026-04-02_analytical_section_suppression_decision.md`.
4. Keep the case-id and wrapper parity repairs intact.
5. Do not spend this block on more section-heading language.
6. The next lever is predicate-local gating:
   - `express_concern` requires an explicit concern/criticism/warning act or a
     clearly stated concern statement by the named speaker; governance reactions
     like oversight increasing, scrutiny increasing, periodic review, or
     doctrine adjustment are not enough by themselves.
   - `limit_capability` requires a concrete operational capability or named
     activity that the text explicitly says was limited; abstract result nouns
     such as `effectiveness`, `impact`, and `credibility` are not enough by
     themselves.

## Gate

This block succeeds only if:

1. one bounded predicate-local prompt revision lands;
2. one post-change chunk-003 artifact exists;
3. the compact operational-parity spillover family is smaller than the
   `0051` result.

## Phase Order

### Phase 1: Freeze The Predicate-Local Residual

#### Tasks

1. freeze the before/after `0051` compact operational-parity outputs;
2. name the exact predicate-local spillover family to target next.

#### Success criteria

1. the blocker is narrower than analytical-section suppression;
2. the active miss family is written in terms of specific predicates and role
   eligibility, not generic prose style.

### Phase 2: Land One Bounded Predicate-Local Revision

#### Tasks

1. add one prompt revision that tightens `express_concern` to explicit
   concern/speech-act evidence;
2. add one prompt revision that tightens `limit_capability` to concrete
   operational capabilities or named activities;
3. keep parity between the live compact prompt and the repaired operational
   parity prompt.

#### Success criteria

1. one bounded predicate-local change lands;
2. parity does not regress.

### Phase 3: Re-run The Chunk-003 Diagnostic

#### Tasks

1. rerun the one-case chunk-003 prompt_eval diagnostic;
2. capture the new artifact;
3. recover the compact-operational-parity response from observability.

#### Success criteria

1. there is one committed post-change artifact;
2. the compact-operational-parity response can be compared directly to the
   `0051` call.

### Phase 4: Classify The Result

#### Tasks

1. decide whether the predicate-local spillover family shrank, shifted, or
   stayed flat;
2. record any narrow uncertainty separately.

#### Success criteria

1. one dominant result is named explicitly;
2. it is artifact-backed at the compact-operational-parity surface, not just
   the report baseline.

### Phase 5: Closeout

#### Tasks

1. write the decision note;
2. refresh `CLAUDE.md`, `HANDOFF.md`, `KNOWLEDGE.md`, `TODO.md`,
   `docs/STATUS.md`, and `docs/plans/CLAUDE.md`;
3. either close this block or activate the next narrower block.

#### Success criteria

1. the next active blocker is narrower than `0052`;
2. top-level docs truthfully reflect the predicate-local semantic status.

## Exit Criteria

This block is complete only when:

1. all five phases above meet their success criteria;
2. the worktree is clean;
3. the repo contains committed predicate-local gating artifacts and a decision
   note.

## Outcome

Plan `0052` is complete and useful, but not sufficient.

It narrowed the compact-operational-parity family from `6` candidates to `5`
and collapsed the split concern-speaker family, but it did not remove the core
semantic residual:

1. abstract-result `limit_capability` candidates survived;
2. governance-reaction `express_concern` survived in combined form; and
3. the old staffing-summary `belongs_to_organization` spillover shifted into a
   citation/report-style `send_report` spillover.

Decision artifact:

- `docs/runs/2026-04-02_predicate_locality_gate_decision.md`

The next active bounded block is therefore even narrower:
`docs/plans/0053_24h_abstract_result_and_citation_block.md`.
