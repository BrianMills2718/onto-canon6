# Phase 16 Candidate: First Real Run Over Local PSYOP Research Outputs

## Purpose

Put `onto-canon6` through one small non-fixture investigation workflow using
real prior research text from the `onto-canon` lineage, then let observed
friction decide whether a roadmap extension is justified.

This is not a new broad implementation phase. It is an adoption-first proof
that the current bounded core can handle a real investigation slice.

## Question

Can `onto-canon6` take a small real PSYOP/MISO corpus from raw text through:

1. live extraction,
2. candidate review,
3. proposal review / overlay application when needed,
4. graph promotion,
5. governed export,

without requiring ad hoc code changes to keep the workflow moving?

## Corpus

The run uses three real local research reports from `../onto-canon/`:

1. `research_outputs/stage1/stage1_query2_20251118_122424.md`
2. `research_outputs/stage1/stage1_query3_20251118_122613.md`
3. `research_outputs/stage1/stage1_query4_20251118_122813.md`

These are prior research artifacts, not synthetic fixtures. The first run will
copy them into the local run directory so the workflow artifacts are stable and
self-contained.

## Runtime Boundary

- profile: `psyop_seed@0.1.0`
- source kind: `text_file`
- review database: `var/real_runs/2026-03-18_psyop_stage1/review_state.sqlite3`
- overlay root: `var/real_runs/2026-03-18_psyop_stage1/ontology_overlays`
- outputs root: `var/real_runs/2026-03-18_psyop_stage1/outputs`

## Acceptance Criteria

The run passes only if all of the following happen:

1. At least three non-fixture source documents are copied into the local run
   directory and processed through the live `extract-text` CLI path.
2. Live extraction persists candidate assertions into the isolated review
   database for at least one document without using notebook fixtures or test
   doubles.
3. At least five candidate assertions receive explicit human review decisions
   (`accepted` or `rejected`), with reasoning recorded in the friction log when
   the correct decision is unclear.
4. If ontology proposals are generated, at least one proposal is reviewed and,
   when accepted, exercised through the overlay-application path.
5. At least one accepted candidate is promoted into the durable graph slice.
6. At least one governed bundle is exported from the real-run state.
7. A friction log exists and records concrete blockers, surprises, or
   usability pain from the run.

## Failure Conditions

The run fails if any of the following occur:

1. The extractor cannot run live because of repo defects, broken prompt wiring,
   or missing runtime integration inside `onto-canon6`.
2. The workflow requires direct database editing or custom code patches to move
   a normal document through the intended CLI path.
3. The run produces only fixture-backed artifacts.
4. The review or promotion steps fail silently or require undocumented
   workarounds.

External dependency failures such as unavailable model credentials do not count
as architecture success. They should still be logged as real adoption
friction.

## Known Risks

1. The donor `psyop_seed` ontology may be too narrow for the generated reports,
   producing many mixed-mode proposals.
2. Live extraction may emit more candidates than are practical to fully review
   in one pass.
3. The reports are already synthesized research outputs rather than raw source
   documents, so extraction quality here tests the workflow on analyst text,
   not on raw PDFs or transcripts.
4. Model variability may make the exact candidate set unstable across runs.

## Build Order

1. Copy the selected corpus into the local run directory.
2. Run live extraction over each document.
3. Inspect candidate/proposal counts and select a bounded review subset.
4. Record candidate review decisions.
5. Review and optionally apply proposals.
6. Promote at least one accepted candidate.
7. Export the governed bundle and capture the resulting artifacts.
8. Update the friction log and decide whether any next step is actually
   justified.

## Non-Goals

1. Do not reopen broad parity work.
2. Do not create a new generalized ingestion framework.
3. Do not treat this one run as a benchmark of extraction quality.
4. Do not add MCP or UI work just to support this run.
