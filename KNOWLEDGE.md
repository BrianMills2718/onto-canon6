### 2026-03-28 — codex — integration-issue
`onto-canon6/data/sumo_plus.db` already existed locally before the ownership
cutover and matched the donor `onto-canon/data/sumo_plus.db` byte-for-byte
(SHA-256 `9a6da4825eb9e4f4d81d1263e5c2ee6847bb85a1b899727e6be929658e1da0f6`).
That made the SUMO migration a contract cutover, not a rebuild project.

### 2026-03-28 — codex — best-practice
Archive-readiness should be verified from an isolated temp copy of the repo,
not inferred from the main workspace. `make verify-setup`, `make smoke`, and
`make check` all passed from `/tmp/onto-canon6-isolation.*` with no sibling
`onto-canon5` or `onto-canon` repos present.

### 2026-03-31 — codex — integration-issue
The supported DIGIMON export entrypoint is the installed `onto-canon6` console
script, not `python -m onto_canon6.cli`. `src/onto_canon6/cli.py` exposes
`main()` but does not execute it as a module entrypoint, so `python -m
onto_canon6.cli export-digimon ...` exits without writing JSONL. Use the
console script in docs and verification commands until the module entrypoint is
made explicit.

### 2026-03-31 — claude-code — bug-pattern
Judge filter (`_apply_judge_filter` in `text_extraction.py`) was calling
`call_llm_structured` with a stale API: missing `model` positional arg and
passing raw JSON Schema dict instead of Pydantic `response_model`. Fixed by
adding `_JudgeResult` Pydantic model and passing model as first arg. The bug
was hidden by a silent `except Exception` fallback that passed all candidates
through — violating the fail-loud rule. Silent fallback removed.

### 2026-03-31 — claude-code — bug-pattern
LLM entity clustering (`_group_by_llm` in `auto_resolution.py`) had three
silent fallback paths (prompt render failure, LLM call failure, parse failure)
that all fell back to fuzzy matching without raising. On first scale test run,
ALL entity types fell back to fuzzy because the prompt YAML format was wrong
(bare `system`/`user` keys instead of llm_client's `messages` list format).
The system appeared to work but was doing the wrong thing. Fixed: all fallbacks
removed, errors raise.

### 2026-03-31 — claude-code — schema-gotcha
LLM extraction produces noise entities from descriptive phrases: "several
initiatives to modernize its force structure", "met", "a ceremony",
"a joint conference". These survive structural validation because they have
valid entity types. The judge filter (now fixed) should catch these as
unsupported, but the extraction prompt may also need a discriminating
instruction to avoid extracting noun phrases as entities.

### 2026-03-31 — claude-code — schema-gotcha
Entity type inconsistency across documents: the same USSOCOM entity gets typed
as `oc:military_organization` in one extraction and `oc:organization` in
another. The ontology pack should normalize these (military_organization is a
subtype of organization) but the type guard in entity resolution treats them as
different types, preventing merge. The type guard should use type hierarchy
(is-a relationship) not exact match.

### 2026-03-31 — claude-code — best-practice
DIGIMON export adapter models (`DigimonEntityRecord`, `DigimonRelationshipRecord`)
lack `extra="forbid"` per the root CLAUDE.md Data Contracts rule ("Producer
models: `extra='forbid'`"). Fix when next touching the adapter.

### 2026-03-31 — claude-code — best-practice
Decisions D1 (`require_llm_review`) and D6 (DIGIMON as first consumer) are
documented as design decisions in Plan 0025 but do not have standalone ADRs
in `docs/adr/`. Create ADRs 0024-0025 after the scale test (Plan 0025 Phase 4)
validates these decisions with measured results.
