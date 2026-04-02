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

### 2026-03-31 — codex — integration-issue (RESOLVED 2026-04-01)
`__main__.py` now exists — both `python -m onto_canon6 --help` and the
installed `onto-canon6` console script work. Use either.

### 2026-04-01 — claude-code — best-practice
First real value demonstration (Booz Allen lobbying network analysis):
9 extracted facts from 2 investigations → ProbLog inference rules derived
14 new facts including: strongest lobbying tie (DLA Piper — dual relationship),
corporate lobby reach through subsidiary structure, 6 distinct lobbying firms
identified across documents. None of these answers were in any single source
document. The neurosymbolic pipeline (extraction + resolution + inference)
produces intelligence that raw text search cannot.

### 2026-04-01 — claude-code — schema-gotcha
gemini-3-flash-preview cannot fill `additionalProperties` with nested
array-of-objects in JSON schema structured output. The extraction `roles` field
(`dict[str, list[ExtractedFiller]]` → `additionalProperties: {type: array,
items: {$ref: ...}}`) produces empty `"roles": {}` every time. Flat properties
work fine — the model correctly fills subject_name, object_name, etc.

Root cause: Gemini 3's structured output decoder can't navigate dynamic-key
objects containing complex nested items. NOT a schema complexity issue —
specifically the `additionalProperties` + nested `$ref` pattern.
Fix options: (1) flat extraction schema + post-process into roles format,
(2) use gemini-2.5-flash/2.5-flash-lite which handle `additionalProperties`.

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
LLM extraction produces noise entities from descriptive phrases ("several
initiatives to modernize its force structure", "met", "a ceremony"). These
survive structural validation because they have valid entity types. Two
mitigation paths: (1) judge filter rejects as unsupported, (2) extraction
prompt needs discriminating instruction to avoid noun-phrase entities.
Tracked as extraction quality issue in Plan 0014.

### 2026-03-31 — claude-code — integration-issue
Gemini API daily quota exhausted (10,000 requests/day for gemini-2.5-flash).
Hit during scale test runs + extraction experiments. llm_client's retry logic
reported this as "Temporary failure in name resolution" which was misleading —
actual error is HTTP 429 rate limit. Quota resets ~5pm PDT 2026-04-01. The
earlier llm_client error masking should be investigated — rate limits should
surface as RateLimitError, not DNS errors.

### 2026-03-31 — claude-code — schema-gotcha
Entity type inconsistency across documents: the same USSOCOM entity gets typed
as `oc:military_organization` in one extraction and `oc:organization` in
another. The ontology pack should normalize these (military_organization is a
subtype of organization) but the type guard in entity resolution treats them as
different types, preventing merge. The type guard should use type hierarchy
(is-a relationship) not exact match.

