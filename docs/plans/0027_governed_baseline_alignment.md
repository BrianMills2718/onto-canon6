# Plan 0027 — Governed Baseline Alignment

**Status:** Complete
**Type:** bounded-governance-alignment
**Priority:** High

## Gap

**Current:** `onto-canon6` already declares capability ownership and matches the
shared registry row for `onto_canon6.governed_semantic_build_and_canonical_identity`,
but the current governed audit still reports `FAIL` / `partial` because:

1. `AGENTS.md` is out of sync
2. `scripts/relationships.yaml` remains bootstrap-only

**Target:** restore truthful governed status without changing the active
successor scope or replacing the current capability source unless review proves
it is stale.

## Goal

Bring `onto-canon6` back to truthful governed status without changing the
active successor scope or starting a new capability track.

## References Reviewed

1. `CLAUDE.md`
2. `AGENTS.md`
3. `meta-process.yaml`
4. `scripts/relationships.yaml`
5. `docs/plans/CLAUDE.md`
6. `docs/plans/0005_v1_capability_parity_matrix.md`
7. `/home/brian/projects/project-meta_worktrees/plan-57-onto-canon6-governed-alignment/docs/plans/57_onto-canon6-governed-baseline-alignment.md`

## Current Audit Truth

The current governed audit from `project-meta` reports `FAIL` / `partial`
because:

1. `AGENTS.md` is out of sync
2. `scripts/relationships.yaml` still carries only bootstrap-default linkage

The repo already declares capability ownership:

- `meta_process.capability_ownership.enabled: true`
- `meta_process.capability_ownership.source_of_record: docs/plans/0005_v1_capability_parity_matrix.md`
- shared registry match:
  - `onto_canon6.governed_semantic_build_and_canonical_identity`

## Boundaries

This plan is only about:

1. reviewing whether the current local capability source of record is still
   truthful
2. resyncing `AGENTS.md`
3. deepening `scripts/relationships.yaml` beyond bootstrap defaults enough for a
   truthful governed audit

This plan is not:

1. a new successor architecture plan
2. a new extraction/evaluation plan
3. a broad documentation rewrite

## Acceptance Criteria

1. `project-meta` governed audit reports `PASS` / `governed`
2. the local capability source of record is either confirmed or explicitly
   replaced
3. the wave remains bounded to AGENTS sync plus actionable linkage deepening

## Phase Stack

### Phase A — Freeze and review

Pass when:

1. this plan is indexed
2. the current capability source-of-record choice is reviewed explicitly
3. the exact partial-audit causes are recorded

### Phase B — Local governed repair

Pass when:

1. `AGENTS.md` is regenerated and in sync
2. `scripts/relationships.yaml` is no longer bootstrap-only
3. local truth surfaces stay aligned

### Phase C — Verification and closeout

Pass when:

1. governed audit is `PASS`
2. plan status is updated with verification evidence
3. the next repo-local follow-on is explicit

## Failure Modes

1. If `0005_v1_capability_parity_matrix.md` is no longer a truthful local
   capability source, stop and choose the replacement explicitly before editing
   config.
2. If linkage deepening starts to sprawl into a giant relationship graph, stop
   and only add the rules needed for truthful governed ownership navigation.

## Verification

1. `python /home/brian/projects/project-meta_worktrees/plan-57-onto-canon6-governed-alignment/scripts/meta/audit_governed_repo.py --repo-root /home/brian/projects/onto-canon6_worktrees/plan-0027-governed-alignment --json`
2. `python scripts/meta/check_doc_coupling.py`
3. `python scripts/meta/validate_plan.py --plan-file docs/plans/0027_governed_baseline_alignment.md`
4. `python scripts/check_markdown_links.py docs/plans/0027_governed_baseline_alignment.md docs/ops/GOVERNED_ALIGNMENT_TODO.md CLAUDE.md AGENTS.md`
5. `git diff --check`
