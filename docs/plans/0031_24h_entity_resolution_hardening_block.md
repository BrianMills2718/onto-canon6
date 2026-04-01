# 24h Entity Resolution Hardening Block

Status: active
Phase status:
- Phase 1 completed
- Phase 2 completed
- Phase 3 completed
- Phase 4 pending
- Phase 5 pending

Last updated: 2026-04-01
Workstream: bounded 24-hour hardening block after Plan 0030

## Purpose

Convert the first decision-grade value proof into a tighter, less caveated
resolution system.

This block is complete only when the repo has:

1. a fixed auto-review judge path that honors explicit bounded model overrides;
2. a general same-surname person disambiguation guard that blocks the current
   Smith-family false merges without undoing title/initial-based true merges;
3. a broader type-compatibility gate for resolution so subtype-equivalent
   entities such as `oc:military_organization` and `oc:organization` can
   compete for merge;
4. refreshed exact and LLM value-proof artifacts produced after those changes;
5. a written result stating whether the LLM strategy is now promotable.

## Scope

This block is intentionally narrow. It covers exactly:

1. the extraction review seam in `text_extraction.py`;
2. resolution-time type compatibility and person-name hardening in
   `auto_resolution.py`;
3. the same official synthetic corpus used in Plan 0030;
4. exact and LLM reruns on that corpus;
5. documentation and closeout updates.

Out of scope:

1. scale-out beyond the synthetic corpus;
2. new retrieval or DIGIMON work;
3. broader extraction-prompt redesign unrelated to the identified failure
   families;
4. a new identity architecture.

## Pre-Made Decisions

1. Work stays in the isolated `codex/onto-canon6-integration-planning`
   worktree.
2. The comparison baseline from Plan 0030 remains authoritative; this block
   reruns the governed exact and governed LLM strategies after hardening.
3. The bare baseline does not need a fresh rerun unless the rerun machinery
   itself changes materially.
4. The stale `_judge_candidate()` path must stop bypassing the explicit
   bounded-model selection. Reusing the existing llm_client-backed structured
   judging path is preferred over keeping a second bespoke litellm branch.
5. Same-surname person disambiguation should be implemented as a general guard,
   not a hardcoded `Smith` patch.
6. Type compatibility should become hierarchy-aware or override-aware; it
   should not remain exact-string equality for all resolution strategies.
7. If the LLM strategy still fails the hardening gate after this block, the
   correct outcome is to document that explicitly and keep exact as the default
   floor.
8. Every verified phase gets its own commit.

## Hardening Gate

This block succeeds only if all of the following are true on the refreshed LLM
run:

1. `_judge_candidate()` no longer uses stale `gemini-2.5-flash` implicitly when
   an explicit judge-model override was provided;
2. the prior same-surname false-merge family (`General John Smith` vs
   `James Smith`) is eliminated or materially reduced;
3. no new broad false-merge family replaces it;
4. pairwise recall does not regress below the exact floor established in Plan
   0030;
5. the run note can state clearly whether LLM resolution is now promotable.

Target metrics for a successful LLM hardening run:

1. precision at or above `0.93`;
2. recall at or above `0.50`;
3. false merges at or below `2`.

If those thresholds are missed, the run still counts as complete if the failure
mode is explicit and localized.

## Phase Order

### Phase 1: Freeze The Hardening Contract

#### Tasks

1. make this block the active execution surface in `CLAUDE.md`, the plans index,
   and `TODO.md`;
2. record the exact failure families to target:
   - stale auto-review judge model selection
   - same-surname person overmerge
   - subtype/alias blocking for orgs and installations
3. mark the success thresholds above as the gate for the rerun.

#### Success criteria

1. the active docs point to this block, not Plan 0030;
2. the stop conditions and success thresholds are explicit enough to implement
   without asking new questions.

### Phase 2: Fix Auto-Review Judge Parity

#### Tasks

1. remove the stale direct-litellm path in `_judge_candidate()` or bring it to
   parity with the llm_client-backed judge path;
2. ensure explicit `judge_model_override` flows all the way through auto-review;
3. add or update tests proving the override is honored and failures do not
   silently claim success.

#### Success criteria

1. `_judge_candidate()` no longer hardcodes or implicitly falls back to stale
   `gemini-2.5-flash` when an explicit override exists;
2. the relevant tests pass;
3. the known Plan 0030 caveat is removed or narrowed truthfully.

### Phase 3: Harden Resolution Decisions

#### Tasks

1. add a general person-name compatibility guard that blocks merges when two
   person mentions have conflicting full given names, while still allowing:
   - title variants
   - initials vs full names
   - abbreviated first names when compatible
2. make type compatibility for resolution hierarchy-aware or override-aware so
   subtype-equivalent entities can be considered together;
3. strengthen the clustering prompt or post-LLM validation rules to reflect the
   above behavior;
4. add focused regression tests for:
   - `General John Smith` vs `James Smith` should not merge
   - `USSOCOM` vs `U.S. Special Operations Command` remain eligible to merge
   - `Fort Bragg` vs `Fort Liberty` remain eligible to merge if the model can
     justify it

#### Success criteria

1. the targeted regression tests pass;
2. the same-surname false-merge family is blocked by deterministic code, not
   just prompt hope;
3. subtype-equivalent org aliases are no longer ruled out before the LLM sees
   them.

#### Outcome

Completed on 2026-04-01.

Landed changes:

1. deterministic post-LLM person-cluster splitting for conflicting full given
   names;
2. conservative resolution-family compatibility so subtype-equivalent
   organization and place mentions are not pre-rejected;
3. prompt updates that expose both resolution family and concrete entity type to
   the clustering model;
4. focused regression coverage for the Smith-family false-merge case and
   subtype-compatible organization clustering eligibility.

### Phase 4: Refresh The Value Proof

#### Tasks

1. rerun exact strategy on a fresh DB with the current bounded judge settings;
2. rerun LLM strategy on a fresh DB with the same bounded judge and resolution
   model settings;
3. compare the rerun against the Plan 0030 artifacts;
4. write a new run note summarizing:
   - new metrics
   - what improved
   - what still fails
   - whether LLM is now promotable

#### Success criteria

1. fresh exact and LLM JSON artifacts exist under `docs/runs/`;
2. the run note is decision-grade and references the new artifacts directly;
3. if the LLM path is still not promotable, the blocking failure family is
   concrete.

### Phase 5: Closeout

#### Tasks

1. update `0025`, `0024`, `CLAUDE.md`, `docs/STATUS.md`, `HANDOFF.md`, and
   `KNOWLEDGE.md`;
2. mark this block completed when all phases land;
3. refresh `TODO.md` so the next unresolved frontier is explicit.

#### Success criteria

1. top-level docs describe the current hardening result truthfully;
2. the active plan stack names the next real work, not generic “improve
   entity resolution” language;
3. the worktree is left clean with committed checkpoints only.

## Failure Modes

1. the stale judge seam remains and keeps contaminating the reruns;
2. a prompt-only tweak appears to help but the deterministic failure family is
   not actually blocked;
3. hierarchy-aware compatibility is implemented so loosely that cross-type false
   merges become easier;
4. the rerun note reports totals without naming concrete surviving failures.

## Exit Criteria

This block is complete only when:

1. all five phases above meet their success criteria;
2. the worktree is clean;
3. the repo contains committed code, tests, rerun artifacts, and docs for the
   hardening decision.
