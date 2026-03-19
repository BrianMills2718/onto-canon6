# Real Run: research-agent Shield AI WhyGame Import

Status: complete

## Purpose

Put `onto-canon6` through one real cross-project consumer workflow using local
output from `research-agent`, rather than staying entirely inside the
`onto-canon` lineage.

This run uses the existing WhyGame relationship adapter as the thinnest path
from another project's investigation output into `onto-canon6` review,
promotion, and export surfaces.

## Source Workflow

- producer project: `../research-agent`
- investigation:
  `investigations/20260212_shield_ai_full/`
- primary input:
  `investigations/20260212_shield_ai_full/entities.json`
- supporting human-readable context:
  `investigations/20260212_shield_ai_full/findings.md`

## Question

Can `onto-canon6` import real relationship-oriented investigation output from
another local project, review it, promote it, and export it without adding a
new broad integration layer?

## Runtime Boundary

- profile: `whygame_minimal_strict@0.1.0`
- review database:
  `var/real_runs/2026-03-18_research_agent_shield_ai_whygame/review.sqlite3`
- overlay root:
  `var/real_runs/2026-03-18_research_agent_shield_ai_whygame/ontology_overlays`
- outputs root:
  `var/real_runs/2026-03-18_research_agent_shield_ai_whygame/outputs`

## Acceptance Criteria

The run passes only if all of the following happen:

1. Real `research-agent` investigation output is copied or transformed into a
   local run-specific import artifact without synthetic placeholder facts.
2. At least five real relationship facts are imported through the existing
   WhyGame adapter into an isolated `onto-canon6` review database.
3. At least five imported candidates receive explicit human review decisions.
4. At least three accepted imported candidates are promoted into the durable
   graph slice.
5. A governed bundle and promoted graph report are exported from the real-run
   state.
6. A friction log exists and records concrete cross-project integration pain,
   not just ontology-runtime issues.

## Failure Conditions

The run fails if any of the following occur:

1. The import requires direct database editing.
2. The import requires a new generalized integration framework rather than the
   existing adapter seam.
3. The source facts are replaced with synthetic filler data.
4. The workflow cannot complete extract-free import -> review -> promote ->
   export using existing or narrowly justified surfaces.

## Known Risks

1. `research-agent`'s `entities.json` is not a WhyGame-native contract, so a
   narrow transformation step may be needed.
2. The WhyGame profile is deliberately relationship-only and may lose some
   nuance from the original investigation output.
3. The main ergonomic pain may be surface-level, especially the lack of a
   thin CLI command for WhyGame import.

## Build Order

1. Read the real `research-agent` investigation output.
2. Build a local run artifact containing transformed WhyGame relationship
   facts.
3. Import those facts through the existing WhyGame adapter.
4. Review a bounded subset or all imported candidates.
5. Promote accepted candidates.
6. Export governed bundle and promoted graph report.
7. Record friction and decide whether any small follow-on change is justified.

## Non-Goals

1. Do not build a new general research-agent integration layer.
2. Do not reopen parity phases just because the producer project differs.
3. Do not add ontology features unless the consumer workflow actually forces
   them.

## Outcome

The run completed successfully.

See:

1. `docs/runs/2026-03-18_research_agent_shield_ai_whygame_run_summary.md`
2. `docs/runs/2026-03-18_research_agent_shield_ai_whygame_friction_log.md`

This run also justified one small surface improvement during execution:
`onto-canon6` now has a thin CLI command for WhyGame relationship imports, so
future cross-project imports no longer require ad hoc Python just to call the
existing adapter.
