# 24h Graph-Value Stop Gate

Status: active

Last updated: 2026-04-03
Workstream: contract-investigation stop policy and runtime-promotion decision

## Mission

Use the next 24 hours to close the operational gap left after Plan `0069`:

1. a fresh live Claude-backed memo can already produce downstream graph value;
2. the loop can still continue because reflect confidence remains below the
   generic deep-research stop threshold; therefore
3. the next block must add and prove a contract-style stop gate based on
   downstream graph readiness, not confidence alone.

This block is complete only when a fresh live contract investigation stops on
an explicit graph-value gate, still produces non-empty downstream graph
structure, and the runtime-promotion decision is documented as closed rather
than left implicit.

## End Goal This Block Serves

The end state is not merely "the loop can stop sooner." The end state is:

1. contract-style investigations stop when the memo already satisfies
   downstream graph-use acceptance;
2. that stop behavior is explicit, configurable, and off by default for
   non-contract investigations;
3. a fresh live run proves the gate on the real Palantir contract question;
   and
4. the Claude runtime profile is either promoted for contract investigations
   or explicitly rejected with evidence.

## Pre-Made Decisions

1. Keep the repo-default loop behavior depth-biased; the new stop gate must be
   config-driven and disabled by default.
2. Use export-aligned metrics rather than ad hoc heuristics. The stop gate must
   reason from memo structure that maps directly to the shared-contract export.
3. Reuse the Palantir federal-contracts question so the new proof stays
   comparable with Plans `0068` and `0069`.
4. Promote the existing Claude runtime profile for contract-style
   investigations only if the fresh live proof stops naturally under the new
   gate and still produces a non-empty downstream graph.
5. If the live proof still requires a checkpoint copy or manual judgment to
   claim success, the runtime-promotion decision remains "not promoted."

## Phases

### Phase 0. Authority Activation

Success criteria:

1. `CLAUDE.md` names this block as the active authority;
2. `docs/plans/CLAUDE.md` lists this block as active;
3. `TODO.md` names the stop-gate proof as the top priority; and
4. `var/progress/0070_graph_value_stop_gate.md` records mission and gates.

### Phase 1. Graph-Value Contract Definition

Success criteria:

1. the stop gate is defined in terms of export-aligned memo metrics;
2. all thresholds are config-driven and documented;
3. default loop behavior remains unchanged when the gate is disabled; and
4. failure modes are recorded before code changes begin.

### Phase 2. research_v3 Implementation And Tests

Success criteria:

1. `research_v3` can compute graph-readiness metrics from a live memo without
   writing a new artifact first;
2. `_apply_reflect_decision()` or its equivalent can stop on graph readiness
   even when reflect says `continue`;
3. deterministic tests cover both enabled and disabled gate behavior; and
4. the Claude contract runtime profile enables the gate explicitly.

### Phase 3. Verification

Success criteria:

1. targeted `research_v3` tests for the new gate pass;
2. full `research_v3` suite passes unless a documented upstream outage forces a
   truthful skip;
3. relevant `onto-canon6` integration coverage still passes; and
4. no existing proof path regresses.

### Phase 4. Fresh Live Proof

Success criteria:

1. a fresh Palantir contract investigation runs under the promoted Claude
   contract profile;
2. the run stops without requiring a manual checkpoint freeze;
3. the final memo/report artifacts come from the run itself; and
4. the resulting memo still yields `>0` entities and `>0` DIGIMON
   relationships downstream.

### Phase 5. Runtime Decision And Truth Surfaces

Success criteria:

1. the runtime-promotion decision is closed explicitly in docs;
2. `CLAUDE.md`, `STATUS`, `ROADMAP`, `HANDOFF`, and proof notes match the
   actual result;
3. any residual concern is documented precisely; and
4. verified work is committed with clean worktrees.

## Failure Modes

1. The stop gate uses memo metrics that do not actually correspond to the
   downstream export path.
2. The gate accidentally changes default deep-research behavior when no
   contract profile is selected.
3. The live proof still depends on copying a checkpoint snapshot rather than
   stopping naturally.
4. The gate stops too early and produces an empty or trivial downstream graph.
5. The block claims runtime promotion without a fresh live proof.

## Verification

Minimum verification for closeout:

1. deterministic tests for graph-readiness metrics and stop behavior
2. full `research_v3` suite unless an external outage is explicitly documented
3. relevant `onto-canon6` integration tests
4. one fresh live Palantir run under the contract Claude profile
5. `make pipeline-rv3-memo INPUT=<fresh final memo>` in `/home/brian/projects/onto-canon6`
6. doc and handoff updates that close or preserve the runtime decision
   truthfully

## Exit Condition

This block is complete when:

1. graph-value stop gating exists behind config;
2. default loop behavior is unchanged when the gate is off;
3. the contract Claude profile enables the gate explicitly;
4. a fresh live Palantir run stops naturally and produces final artifacts;
5. the final memo still produces a non-empty downstream graph; and
6. the runtime-promotion decision is documented as closed with evidence.
