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

### 2026-04-01 — codex — best-practice
The Plan 0031 hardening reruns proved that pairwise precision alone is not a
sufficient promotion gate for entity resolution. The hardened LLM strategy
reached `1.00` precision and `0` false merges, but benchmark answerability
still collapsed because many mentions no longer resolved to a unique predicted
cluster. Keep the fixed question set as a co-equal gate with pairwise metrics
for future promotion decisions.

### 2026-04-01 — codex — bug-pattern
If a scale-test rerun suddenly loses one document, check
`candidate_assertions.source_ref` distribution before debugging resolution.
The hardened LLM rerun under Plan 0031 had only `24` source refs instead of
`25`; `doc_06` was missing because extraction emitted unsupported filler kind
`event` and failed validation before promotion or resolution even ran.

### 2026-04-01 — codex — workaround
Response-level salvage in `TextExtractionResponse` is sufficient to keep the
scale-test corpus intact even when Gemini emits malformed sibling candidates.
After the Plan 0032 fix, the refreshed LLM rerun preserved all `25`
`candidate_assertions.source_ref` values despite continuing to log malformed
`event` / malformed-unknown candidate payloads.

### 2026-04-01 — codex — bug-pattern
The remaining fixed-question misses after the successful Plan 0032 rerun are
not dominated by false merges. They cluster into two narrower families:
type-divergent mention surfaces (`Gen. Smith` as `person` vs `military_rank`,
`Ft. Bragg` as `location` vs `Fort Liberty` as `military_organization`) and
alias-surface absence (`the Agency`, `GWU`, `George Washington University`
never surviving as promoted matched observations). Treat the next block as
answerability hardening, not generic clustering churn.

### 2026-04-01 — codex — bug-pattern
`_candidate_ground_truth_entity_ids()` in
`src/onto_canon6/evaluation/entity_resolution_value_proof.py` must not fall
back to source-doc overlap when an observation already has explicit named
surfaces that do not match any ground-truth variant. The old fallback created
bogus "unique normalized name + type match" assignments and contaminated
intermediate value-proof artifacts until fixed.

### 2026-04-01 — codex — best-practice
Do not treat repeated `--skip-extraction` reruns on an already-resolved DB as
decision-grade entity-resolution evidence. Identity memberships and prior
resolution state can change answerability in misleading ways. Use a fresh DB
for closeout reruns, and treat repeated-resolution artifacts as diagnostics
only.

### 2026-04-01 — codex — workaround
Long-running scale-test reruns can hang indefinitely unless
`LLM_CLIENT_TIMEOUT_POLICY=allow` is set for the process. The first fresh rerun
attempt for Plan 0036 stalled until manually killed; the canonical decision
artifact `docs/runs/scale_test_llm_2026-04-01_113959.json` came from the same
command with timeout policy explicitly enabled.

### 2026-04-01 — codex — best-practice
Plan 0036 proved that pairwise false splits can remain even after the benchmark
question set is fully green. After `113959`, answer rate and accuracy were both
`1.00`, but pairwise recall still trailed because the Rodriguez title family
and Washington place family were split across separate identity clusters. Use
question accuracy and pairwise recall together when deciding whether
entity-resolution work is actually complete.

### 2026-04-01 — codex — best-practice
Plan 0039 closed only after two consecutive fresh reruns on new DBs
(`145141`, `152927`) both preserved `10/10` fixed-question accuracy and `0`
false merges. One good rerun is not enough for rerun-stability claims.

### 2026-04-01 — codex — bug-pattern
Even after Plan 0039 closed, pairwise false splits can still drift across fresh
reruns without reopening the fixed question set. The dominant residual families
were descriptor-only `the Agency` and the `Washington D.C.` / `Washington` /
`D.C.` place family. Treat those as follow-on quality work, not proof that the
question-level rerun gate failed.

### 2026-04-01 — codex — integration-issue
When executing `onto-canon6` from the isolated worktree, `python -m onto_canon6`
without `PYTHONPATH=src` can import the editable install from the main checkout
instead of the worktree source tree. Plan 0040 produced invalid intermediate
certification artifacts until the commands were rerun with `PYTHONPATH=src`.
Treat this as a hard execution rule for future worktree-based runtime checks.

### 2026-04-01 — codex — schema-gotcha
Prompt-eval report `execution_id` is not the same key as
`experiment_items.run_id` in the observability DB. For transfer-comparison
work, recover the real per-variant `run_id` from `experiment_runs`
(`config.variant_kwargs.prompt_ref`) before querying `experiment_items`.

### 2026-04-01 — codex — best-practice
For full-chunk prompt-surface diagnosis, treat prompt-eval as a two-step
surface: template messages still contain literal `{input}`, and the effective
runtime surface appears only after `prompt_eval.runner._substitute_input()`
applies the case payload. Plan 0041 proved that the live vs prompt-eval system
messages are identical and the remaining user-surface delta is a stable wrapper
family (`Case input:` plus wording drift), not an unknown prompt-asset mixup.

### 2026-04-01 — codex — bug-pattern
Plan 0042 proved that a narrow compact prompt revision can still stay perfect
in prompt-eval and yet diverge completely on the live extraction path under the
same selected model (`gemini/gemini-2.5-flash`). For chunk `003`,
`compact_operational_parity@3` still returned `candidates: []` in prompt-eval,
while the live `compact_v5` rerun produced four accepted candidates and zero
body-level overlap. After this point, treat the blocker as same-model
live-path divergence, not just "needs another prompt tweak."

### 2026-04-01 — codex — integration-issue
Plan 0043 localized the same-model chunk-003 divergence further: the raw live
`budget_extraction` call already emitted four candidates before review, and the
review path then amplified the problem by labeling all four `supported`
(`judge_filter` plus four per-candidate `judging` calls). Treat review/judge
permissiveness as secondary amplification; the primary next experiment is
wrapper alignment on the live extraction surface.

### 2026-04-01 — codex — integration-issue
Plan 0044 falsified the wrapper-alignment rescue hypothesis. Aligning the live
user wrapper closer to prompt-eval reduced the prompt-surface diff, but the
live chunk-003 rerun still had zero shared bodies with prompt-eval and widened
from four to six accepted candidates. The next blocker is deeper extraction-path
behavior, not wrapper wording alone.

### 2026-04-02 — codex — integration-issue
Plan 0045 localized the extraction-path residual further. The live extractor
had been omitting `temperature=0.0`, but aligning both `temperature=0.0` and
the relative `source_ref` still left zero body overlap with prompt-eval on
chunk `003` and produced five accepted candidates. The remaining residual is
now bounded to sync vs async structured-call behavior and the prompt_eval-only
`Case id` metadata line.

### 2026-04-02 — codex — bug-pattern
Plan 0046 proved the prompt_eval-only `Case id:` line was materially changing
chunk-003 extraction behavior. Replaying the captured prompt_eval async call
without only that line flipped the parsed result from `0` candidates to `5`.
Benchmark control metadata can meaningfully distort extraction behavior even
when the rest of the prompt surface is unchanged.

### 2026-04-02 — codex — best-practice
Plan 0048 proved prompt-surface parity work should not stop at the most obvious
metadata line. After removing `Case id:`, the prompt_eval-only `Case input:`
wrapper still changed the chunk-003 replay family. Only after both were
removed did the rendered user prompt collapse to content-line parity with live.

### 2026-04-02 — codex — integration-issue
The fully aligned manual replay that also replaced the last opening wording
line (`source material` -> `source text`) hung for minutes and had to be
aborted. That instability did not block the decision because the repaired
prompt surface and the post-repair prompt_eval rerun already proved the active
blocker had moved back to semantics.
