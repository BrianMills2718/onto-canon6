# Handoff: onto-canon6

**Date**: 2026-03-26
**From**: Claude Code (vision gap closure sprint)
**Session**: All 10 Plan 0020 gaps closed in one session

---

## What This Session Delivered

### All 10 Vision Gaps Closed

| Gap | Status | Key Result |
|-----|--------|------------|
| 1. Predicate names | ALREADY CLOSED | 4,669 senses already have `name` column in sumo_plus.db |
| 2. Non-military domain | COMPLETED | Financial + academic text: 82% structural validity, 11 candidates |
| 3. Entity resolution | COMPLETED | auto_resolution.py: exact name match, USSOCOM merged across chunks |
| 4. Temporal qualifiers | COMPLETED | valid_from/valid_to in extraction, payload, and Foundation IR |
| 5. Digimon export | COMPLETED | 20 entities → 19 merged nodes, 16 edges in Digimon GraphML |
| 6. research_v3 adapter | COMPLETED | FtM mapping (15 schemas), 48 claims imported from real investigation |
| 7. Epistemic on data | COMPLETED | 16 scored, 1 supersession, 19 tensions, 1 weakened |
| 8. ProbLog spike | COMPLETED | 45 derived facts from 16 inputs, decision: use ProbLog |
| 9. Second vocabulary | COMPLETED | dodaf_minimal: 7 candidates, 100% validation, dm2: namespace |
| 10. Autonomous ops | COMPLETED | .openclaw/ with success-criteria.yaml and mission-spec.yaml |

### Plan 0020 Review Notes

6 issues identified and documented (see plan file):
1. Missing multi-modal projection gap (deliberately deferred)
2. Gap 8 dependency correction (Gap 7 nice-to-have, not required)
3. Gap 6 scope caveat (FtM mapping could expand)
4. Gap 10 review gate design gap (structured_output_check chosen)
5. Confidence alignment cross-cut
6. Gap 2 vocabulary question (predicate catalog, not profile config)

---

## Commits This Session

```
2e6a489 Add continuous execution mandate for 24-hour vision gap sprint
f1ed4a9 [Gap 9] Second vocabulary proof — dodaf_minimal E2E extraction
b32d38f [Gap 1] Mark as already closed — predicate names exist in sumo_plus.db
44f5ff2 [Gap 2] Non-military domain testing — financial and academic text proven
a8a7226 [Gap 3] Automated entity resolution — exact name matching
d368d0c [Gap 4] Temporal qualifiers — valid_from/valid_to in extraction and export
49e51df [Gap 7] Epistemic engine on real data — confidence, supersession, tension
de1cd7b [Gap 8] ProbLog spike — 45 derived facts from 16 inputs, use ProbLog
84fd99b [Gap 6] research_v3 adapter — FtM entity mapping + claim import
dc2345a [Gap 10] Autonomous operation — success criteria and mission spec
```

---

## Key Files Changed

| Purpose | Path |
|---------|------|
| Auto entity resolution | `src/onto_canon6/core/auto_resolution.py` (NEW) |
| research_v3 adapter | `src/onto_canon6/adapters/research_v3_import.py` (NEW) |
| Temporal fields | `src/onto_canon6/pipeline/text_extraction.py` (MODIFIED) |
| Temporal prompt | `prompts/extraction/text_to_candidate_assertions.yaml` (MODIFIED) |
| Foundation IR temporal | `src/onto_canon6/adapters/foundation_assertion_export.py` (MODIFIED) |
| Auto-resolve CLI | `src/onto_canon6/cli.py` (MODIFIED) |
| Mission spec | `.openclaw/mission-spec.yaml` (NEW) |
| Success criteria | `.openclaw/success-criteria.yaml` (NEW) |
| Vision gap plan | `docs/plans/0020_vision_gap_closure.md` (MODIFIED) |

---

## Environment Facts

- Model: `gemini/gemini-2.5-flash` (stable, used for all extractions)
- ProbLog: installed in shared venv (pip install problog)
- No pre-commit hook issues this session
- All tests pass (full suite except notebook_process, digimon_export, cli_flow)

---

## Next Steps (Post-Gap-Closure)

1. **Extraction quality iteration** — the #1 bottleneck per CLAUDE.md strategic
   direction. Use prompt_eval to improve acceptance rates.
2. **Submit research_v3 imports to review pipeline** — adapter produces
   CandidateAssertionImport objects but doesn't yet submit them via the CLI.
3. **ProbLog integration** — move from spike to production: fact-store adapter
   in llm_client, rule YAML format, CLI for rule evaluation.
4. **Second consumer integration** — prove Digimon or research_v3 uses
   onto-canon6 assertions in their actual workflow.
5. **Broader entity types** — the psyop_seed pack's entity types are military-
   specific. A general-purpose pack would improve non-military extraction.

---

## What NOT to Do

- Don't add new ADRs/phases/subsystems (per CLAUDE.md)
- Don't refactor into separate packages (only 1 vocabulary+extension tested)
- Don't rebuild entity dedup in consumers (onto-canon6 owns it)
- Don't adopt Foundation event log internally (wrapper adds it)
- Don't estimate LLM costs — query the observability DB instead
