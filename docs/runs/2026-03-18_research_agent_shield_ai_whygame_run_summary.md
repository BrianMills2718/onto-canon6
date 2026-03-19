# Run Summary: 2026-03-18 research-agent Shield AI WhyGame Import

## Status

Completed.

This was the second real non-fixture `onto-canon6` workflow run and the first
one driven by another local producer project rather than by text extracted
inside the `onto-canon` lineage.

## Producer

- producer project: `../research-agent`
- investigation: `investigations/20260212_shield_ai_full/`
- input artifacts copied into the run:
  1. `entities.json`
  2. `findings.md`

## Runtime

- profile: `whygame_minimal_strict@0.1.0`
- review DB:
  `var/real_runs/2026-03-18_research_agent_shield_ai_whygame/review.sqlite3`
- outputs root:
  `var/real_runs/2026-03-18_research_agent_shield_ai_whygame/outputs`

## Acceptance Criteria Result

1. Real `research-agent` investigation output was copied and transformed into a
   local run-specific WhyGame relationship artifact. Pass.
2. At least five real relationship facts were imported through the existing
   WhyGame adapter. Pass: `14`.
3. At least five imported candidates received explicit human review decisions.
   Pass: `14`.
4. At least three accepted imported candidates were promoted into the durable
   graph slice. Pass: `14`.
5. Governed bundle and promoted graph report were exported from the real-run
   state. Pass.
6. A friction log exists and records cross-project integration pain. Pass.

## Results

- relationship facts generated from producer output: `14`
- imported candidates: `14`
- accepted candidates: `14`
- rejected candidates: `0`
- promoted assertions: `14`
- governed bundle profile counts: `whygame_minimal_strict@0.1.0 = 14`
- promoted graph entity count: `15`

Representative imported relationships:

1. `Shield AI strategic_partner Booz Allen Hamilton`
2. `Shield AI strategic_partner_investor L3Harris Technologies`
3. `Shield AI partner Palantir Technologies`
4. `Shield AI customer U.S. Coast Guard`
5. `Shield AI customer USSOCOM`

## Key Outputs

- `var/real_runs/2026-03-18_research_agent_shield_ai_whygame/outputs/import_result.json`
- `var/real_runs/2026-03-18_research_agent_shield_ai_whygame/outputs/review_and_promotion_summary.json`
- `var/real_runs/2026-03-18_research_agent_shield_ai_whygame/outputs/governed_bundle.json`
- `var/real_runs/2026-03-18_research_agent_shield_ai_whygame/outputs/promoted_graph_report.json`
- `var/real_runs/2026-03-18_research_agent_shield_ai_whygame/outputs/cli_import_result.json`

## What This Run Proved

1. `onto-canon6` can consume real local investigation output from another
   project without reopening the architecture.
2. The existing WhyGame adapter was sufficient as the core import seam.
3. Artifact-backed provenance survives the cross-project import path cleanly.
4. A thin CLI command for WhyGame relationship import was enough to turn the
   adapter into an operational surface.
5. A second thin CLI command was enough to convert `research-agent`
   `entities.json` relationship output into WhyGame facts without leaving the
   workflow dependent on ad hoc Python.

## What This Run Did Not Prove

1. It did not exercise mixed-mode ontology proposals or overlay application.
2. It did not prove text-grounded evidence spans for the imported
   relationships; the producer artifact only carried relationship summaries and
   metadata.
3. It did not prove a general `research-agent` integration layer.

## Decision

This run adds real consumer pressure evidence without justifying a new broad
phase by itself.

The main consumer-friction items exposed by the run are now already addressed
locally:

1. file-backed WhyGame import now has a CLI surface
2. `research-agent` relationship-bearing output now has a narrow transformation
   helper into WhyGame facts

Any broader integration should still be demand-driven.
