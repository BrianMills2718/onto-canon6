# 24h Abstract-Result And Citation Block

Status: complete
Phase status:
- Phase 1 complete
- Phase 2 complete
- Phase 3 complete
- Phase 4 complete
- Phase 5 complete

Last updated: 2026-04-02
Workstream: suppress abstract-result and citation/report spillover on repaired
chunk-003 extraction after Plan `0052`

## Purpose

Plan `0052` proved that predicate-local gating can shrink the chunk-003 family,
but the remaining residual is now even narrower and more explicit.

This block exists to answer the next question:

**Can the repo suppress the remaining chunk-003 spillover by hard-blocking
abstract evaluative `limit_capability` fillers and citation/report-style
hallucinations, while preserving the `0052` concern-speaker shrink?**

## Scope

This block intentionally covers only:

1. the repaired compact operational-parity prompt surface;
2. the live compact prompt kept in parity with it;
3. chunk `003` as the strict-omit stress case;
4. the remaining spillover families:
   - abstract-result `limit_capability`
   - governance-reaction `express_concern`
   - citation/report-style `send_report`

Out of scope:

1. new prompt-path parity work;
2. review/judge policy changes;
3. broad multi-case benchmark reruns before the one-case stress case improves;
4. runtime/harness refactors beyond using the already-known timeout setting

## Pre-Made Decisions

1. Work stays in the isolated `codex/onto-canon6-integration-planning`
   worktree.
2. All Python execution in this block must use `PYTHONPATH=src`.
3. The incoming decision note is:
   `docs/runs/2026-04-02_predicate_locality_gate_decision.md`.
4. Use `LLM_CLIENT_TIMEOUT_POLICY=allow` for the one-case rerun in this block.
5. Keep the case-id and wrapper parity repairs intact.
6. Do not spend this block on more section-heading language.
7. The next lever is explicit hard-negative gating:
   - if `limit_capability` would use an abstract evaluative noun such as
     `effectiveness`, `impact`, or `credibility` as the capability filler,
     omit the candidate;
   - if the candidate depends on retrospective message/campaign labels such as
     `PSYOP messages` or `"hearts and minds" campaigns` as the limited
     subject, omit it unless a concrete operational capability is stated;
   - if the cited span only says a fact book, citation, bibliography entry,
     or `was reported`, do not emit `send_report` without an explicit sender,
     recipient, and delivery act in the source text;
   - if the cited span only says oversight/scrutiny increased or reviews
     happened, do not emit `express_concern`.

## Gate

This block succeeds only if:

1. one bounded hard-negative prompt revision lands;
2. one post-change chunk-003 artifact exists;
3. the compact operational-parity spillover family is smaller than the `0052`
   result and no citation/report spillover remains.

## Phase Order

### Phase 1: Freeze The Post-0052 Residual

#### Tasks

1. freeze the `0052` compact-operational-parity output family;
2. name the exact abstract-result and citation/report spillovers to target.

#### Success criteria

1. the blocker is narrower than generic predicate-local gating;
2. the active miss family is written as hard-negative conditions.

### Phase 2: Land One Bounded Hard-Negative Revision

#### Tasks

1. add one prompt revision that forbids abstract evaluative
   `limit_capability` fillers;
2. add one prompt revision that forbids citation/report-style `send_report`
   extraction without an explicit delivery event;
3. preserve the `0052` concern-speaker shrink and prompt parity.

#### Success criteria

1. one bounded hard-negative change lands;
2. parity does not regress.

### Phase 3: Re-run The Chunk-003 Diagnostic

#### Tasks

1. rerun the one-case chunk-003 prompt_eval diagnostic with
   `LLM_CLIENT_TIMEOUT_POLICY=allow`;
2. capture the new artifact;
3. recover the compact-operational-parity response from observability.

#### Success criteria

1. there is one committed post-change artifact;
2. the compact-operational-parity response can be compared directly to the
   `0052` call.

### Phase 4: Classify The Result

#### Tasks

1. decide whether the abstract-result/citation family shrank, shifted, or
   stayed flat;
2. record any narrow uncertainty separately.

#### Success criteria

1. one dominant result is named explicitly;
2. it is artifact-backed at the compact-operational-parity surface.

### Phase 5: Closeout

#### Tasks

1. write the decision note;
2. refresh `CLAUDE.md`, `HANDOFF.md`, `KNOWLEDGE.md`, `TODO.md`,
   `docs/STATUS.md`, and `docs/plans/CLAUDE.md`;
3. either close this block or activate the next narrower block.

#### Success criteria

1. the next active blocker is narrower than `0053`;
2. top-level docs truthfully reflect the remaining semantic status.

## Exit Criteria

This block is complete only when:

1. all five phases above meet their success criteria;
2. the worktree is clean;
3. the repo contains committed hard-negative gating artifacts and a decision
   note.

## Outcome

Plan `0053` is complete as a failed prompt-only suppression attempt.

The hard-negative revision did not shrink the compact-operational-parity
family. It widened again and introduced a new `create_organizational_unit`
candidate from the `JPOTF model` sentence while leaving the abstract-result
`limit_capability`, governance-reaction `express_concern`, and citation/report
`send_report` spillovers in place.

Decision artifact:

- `docs/runs/2026-04-02_abstract_result_and_citation_decision.md`

The next active bounded block is therefore not another prompt tweak. It is a
benchmark-contract audit:
`docs/plans/0054_24h_full_chunk_strict_omit_contract_audit.md`.
