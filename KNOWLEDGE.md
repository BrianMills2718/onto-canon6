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

### 2026-03-31 — codex — schema-gotcha
Compatibility fixtures for governed exports cannot snapshot raw serialized
objects directly because generated ids, timestamps, and temp-path-like values
drift even when the contract shape is stable. Lane 3 now normalizes those
volatile fields in `tests/compatibility_helpers.py` before comparing snapshots;
future compatibility fixtures should reuse that helper instead of embedding raw
volatile values.

### 2026-03-31 — codex — integration-issue
Lightweight worktrees for `onto-canon6` do not automatically carry the heavy
proof DB under `var/e2e_test_2026_03_25/`. Read-only real-proof verification
from a worktree should therefore target the canonical DB in the main checkout
explicitly, e.g. `/home/brian/projects/onto-canon6/var/e2e_test_2026_03_25/review_combined.sqlite3`.

### 2026-03-31 — codex — schema-gotcha
Exact entity search over an identity cluster with identical observed labels on
both canonical and alias members can legitimately return both members. For the
real proof DB, searching `USSOCOM` returns two promoted organization entities
in the same identity cluster. Use `get-entity` to inspect canonical/alias
membership truthfully; do not treat search-result ordering alone as proof of
alias disambiguation.

### 2026-04-01 — codex — best-practice
The first decision-grade entity-resolution value proof on
`tests/fixtures/synthetic_corpus` showed a clear three-way split:
exact matching is the high-precision floor, the bare baseline is not
competitive, and LLM clustering improves recall materially but is not yet safe
to promote because of same-surname person false merges and unresolved
organization / installation alias splits. Use
`docs/runs/2026-04-01_entity_resolution_value_proof.md` as the summary artifact
before revisiting strategy promotion.

### 2026-04-01 — codex — bug-pattern
During the 2026-04-01 value-proof runs, `_apply_judge_filter()` correctly
honored explicit `gemini/gemini-2.5-flash-lite` overrides, but the later
single-candidate auto-review path `_judge_candidate()` still used the stale
`gemini-2.5-flash` default and fail-opened to `supported` on quota exhaustion.
Treat the resulting run artifacts as decision-grade but caveated until that
override seam is fixed and rerun.
