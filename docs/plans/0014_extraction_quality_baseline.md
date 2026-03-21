# Extraction Quality Baseline

Status: active

Last updated: 2026-03-21

## Purpose

Get extraction quality to a reasonable baseline before moving to new
features or consumers. The Stage 1 real run showed 37.5% acceptance (6/16),
but the failures split into distinct fixable categories. This plan
addresses them without inventing new architecture.

Driven by Stage 1 friction log entries 5 and 7, not by parity pressure.

## Latest Live Findings (2026-03-21)

The extraction experiment boundary is no longer the primary blocker.
Today’s bounded live sweep proved that the current prompt-experiment path
is usable when run explicitly with:

- `--selection-task budget_extraction`
- `--comparison-method bootstrap`
- `--case-limit 1`
- `--n-runs 2`

That run completed with `2/2` successful scored trials for all four
existing variants (`baseline`, `hardened`, `compact`,
`single_response_hardened`) and no structural failures. The result was
still poor semantically:

- `mean_score = 0.275`
- `structural_usable_rate = 1.0`
- `count_alignment = 0.25`
- `exact_f1 = 0.0`

So the next work is not more experiment plumbing. The next work is to
improve semantic extraction quality on a now-usable harness.

One more conclusion from the same day: changing the repo-default prompt
experiment task to `budget_extraction` is premature. The explicit override
works and is the right iteration lane for now, but the default path is not
yet stable enough to flip globally.

Later on 2026-03-21, the expanded 5-case fixture (`psyop_eval_slice_v2`)
also ran end to end on the same explicit lane. Two useful things are now
clear:

1. The structural contract is stable enough to iterate on. After adding the
   fixture-expansion cases and then tightening the prompt contract around
   `kind`, all variants completed the expanded sweep with `10/10`
   successful trials and no trial-level structural failure counts.
2. Prompt-only guardrail changes did not produce a clear semantic winner.
   The pre-guardrail expanded sweep had:
   - `compact = 0.27`
   - `single_response_hardened = 0.26`
   - `baseline = 0.235`
   - `hardened = 0.22`

   After propagating the semantic guardrails and explicit `kind`
   requirement, the expanded sweep had:
   - `baseline = 0.2475`
   - `single_response_hardened = 0.24`
   - `compact = 0.20`
   - `hardened = 0.17`

   None of the bootstrap comparisons was significant, and every variant
   still had `exact_f1 = 0.0`.

That means the next blocker is no longer missing infrastructure or an
obvious prompt-schema omission. The next blocker is a benchmark-contract
question plus remaining semantic extraction quality work:

- the exact-match lane is still partly confounded by extraction-boundary
  normalization (`ent:auto:*`, raw-string normalization) versus
  reviewer-style fixture payloads
- the designation-change case still rewards variants that can emit more
  than one candidate cleanly
- prompt guardrails alone are not enough to separate the variants on the
  expanded fixture

That benchmark-contract question is now resolved. A third expanded sweep on
2026-03-21 aligned the Phase A exact lane to extraction-boundary semantics
instead of reviewer-style canonical payloads. That rerun used the same
explicit live lane and produced:

- `baseline = 0.34`, `exact_f1 = 0.20`, `structural_usable_rate = 0.70`
- `compact = 0.3639`, `exact_f1 = 0.2222`, `structural_usable_rate = 0.5556`,
  `n_errors = 1`
- `hardened = 0.335`, `exact_f1 = 0.20`, `structural_usable_rate = 0.60`
- `single_response_hardened = 0.345`, `exact_f1 = 0.20`,
  `structural_usable_rate = 0.60`

None of the bootstrap comparisons was significant, but the important change
is that `exact_f1` moved off zero for every successful variant. Phase A is
now measuring extractor behavior instead of reviewer-only IDs and downstream
value-normalization shape. The remaining blockers are honest semantic and
structural ones:

- under-extraction of multi-fact cases like designation change
- concern/capability structure still collapsing in the truth-shift case
- one surviving compact-variant structural failure from an unnamed entity
  filler on `psyop_001_designation_change`

## Motivation

The Stage 1 run revealed three failure modes:

1. **Alias self-references (2/10 rejections)**: The model extracted
   abbreviation expansions like `USSOCOM → U.S. Special Operations Command`
   as organizational relationships. These are the same entity with two
   names, not a relationship.

2. **Wrong predicate choice (4/10 rejections)**: The model chose
   `hold_command_role` when text said "subordinate unit"
   (`belongs_to_organization` is correct). Also forced
   `use_organizational_form` and `belongs_to_organization` on non-entity
   metadata like MOS codes.

3. **Unattributed opinion/sentiment claims (4/10 rejections)**: Predicates
   like `express_concern` and `describe_dissatisfaction` require a named
   speaker, but narrative text often has the opinion without clear
   attribution. The model either invented a vague speaker or left the role
   weakly grounded.

In addition to the semantic failures above, the Stage 1 run and subsequent
live experiments exposed **structural reliability** failures that prevent
extraction from producing valid output at all:

4. **Length-limit truncation**: Long-thinking model paths hit output limits
   on real documents. Worked around via deterministic chunking and the
   `budget_extraction` task, but not formally tracked.
5. **Multiple tool-call envelopes**: Some providers return multiple
   tool-call blocks instead of a single structured response, breaking the
   extractor's response parser.
6. **Provider rate limiting**: OpenRouter key exhaustion during live runs.
   Managed by llm_client retry/rotation, but visible as friction.

As of 2026-03-21, those structural issues are sufficiently bounded for
iteration on the explicit `budget_extraction` experiment lane. They remain
important guardrails, but they are no longer the main immediate blocker.

Category 3 is the most interesting semantic failure because the current
prompt hardcodes a policy: "omit any candidate whose roles would require
unnamed entities." This closes off a legitimate use case (sentiment/
thematic analysis where *what* is said matters more than *who* said it).
Sometimes the content of a claim matters more than who made it.

## Design Decisions

### D0: Phase A prompt-eval exact scoring uses extraction-boundary semantics

Prompt experiments are supposed to evaluate what the extractor is
responsible for now: predicate choice, role structure, entity surface form,
entity type, and value-kind/text. They should not fail exact-match scoring
because later stages might assign different stable IDs or richer value
normalization objects.

So the Phase A prompt-eval exact lane is intentionally narrower than the
later reviewer-style canonicalization lane:

1. `ExtractionPromptExperimentService` uses a prompt-eval-specific exact
   matcher that:
   - keeps exact predicate and role-name structure
   - compares entity fillers by `kind`, `entity_type`, and `name`
   - compares value fillers by `kind`, `value_kind`, and primary value text
   - ignores reviewer-only `entity_id` / `alias_ids`
   - ignores richer downstream normalization shape when the extraction
     boundary already matches on surface text
2. `LiveExtractionEvaluationService` keeps the stricter reviewer-style exact
   canonicalization lane for later evaluation and review-quality checks.
3. Phase A exact scores and Phase B canonicalization-fidelity scores are
   therefore related but not identical. The separation is deliberate and
   follows ADR-0005's lane-separation principle.

This decision is now captured in ADR-0020 and should not be reopened unless
the extractor boundary itself changes.

### D1: Allow typed-but-unidentified entity fillers

The extraction contract currently has three filler kinds:

- `entity`: requires `name` or `entity_id`
- `value`: requires `value_kind` + `normalized` or `raw`
- `unknown`: catch-all, requires `raw`

The gap: when a role constraint says "this should be a person" but the
text doesn't name the person, the model must either invent a name, use
`unknown` (losing the known type), or drop the candidate entirely.

These are different situations:

- **Unknown type**: "I found something but don't know what kind of thing
  it is." That's what `unknown` filler is for.
- **Known type, unknown identity**: "The `speaker` role requires a person —
  I know that from the ontology — but I can't tell *which* person from the
  text." This is common with opinion predicates in narrative text.

The fix touches three layers:

1. **Extraction boundary** (`text_extraction.py`): Relax
   `ExtractedFiller._validate_shape` to allow entity fillers with
   `entity_type` but no `name` and no `entity_id`. The model already has
   `name: str | None = None` and `entity_id: str | None = None` — the
   current validator just rejects that combination. No new fields needed.

2. **Filler normalization** (`text_extraction.py`):
   `_pipeline_filler_from_extracted` currently calls
   `_derive_local_entity_id` when `entity_id` is absent, which requires a
   non-blank `name` and raises `ValueError` otherwise. Unidentified
   fillers must bypass local ID derivation entirely — persist with no
   `entity_id` in the payload. Downstream promotion already requires typed
   entities with IDs, so unidentified fillers naturally stop at the review
   boundary until identity is resolved.

3. **Validation pipeline** (`validation.py`):
   `_check_entity_ids` currently emits `oc:hard_missing_entity_id` for any
   entity filler without a non-empty `entity_id`. This must become
   conditional on the profile's `unidentified_entity_fillers` setting:
   when `reject`, emit the finding as before; when `allow`, skip the
   finding for fillers that have `entity_type` but no `entity_id`.

An entity filler is **unidentified** when `kind == "entity"` and both
`name` and `entity_id` are None or empty. The `entity_type` is still
present, so role type constraints still validate.

Whether unidentified fillers are acceptable is a **profile-level policy
question**, not a prompt-level rule:

- Strict profiles reject candidates with unidentified entity fillers at
  validation time.
- Permissive profiles allow them through to review.
- The prompt renders the active policy so the model knows whether to
  produce or omit unattributed candidates.

### D2: Prompt negative guidance for common extraction errors

The `hardened` prompt variant
(`prompts/extraction/prompt_eval_text_to_candidate_assertions_hardened.yaml`)
already implements these rules as error-check bullets. The implementing
agent should apply the same rules to the **main** extraction prompt
(`prompts/extraction/text_to_candidate_assertions.yaml`) — the variant
was the experiment, the main prompt is what the CLI and MCP surface use.

The rules (already proven in the hardened variant):

1. Abbreviation expansions and parenthetical name variants of the same
   entity are not relationships — do not extract them as assertions.
2. Text describing a unit as "subordinate" or "under" another unit maps to
   `belongs_to_organization`, not `hold_command_role`.
   `hold_command_role` is for named people holding positions over
   organizations.
3. Classification codes, MOS designators, and acronym definitions are
   metadata, not entities that belong to organizations.
4. If the text only implies sentiment, concern, or dissatisfaction without
   a named speaker, omit the candidate rather than inventing a person or
   a vague source. (This rule becomes conditional on D3's
   `unidentified_entity_fillers` policy once implemented.)

These are rules, not worked examples — they do not violate the CLAUDE.md
"no examples in prompts without approval" policy. If the implementing
agent needs to add few-shot input/output examples beyond these rules,
that requires approval.

### D3: Profile-level control over unidentified-filler acceptance

Add a profile-level setting to the profile manifest:

```yaml
unidentified_entity_fillers: reject   # or "allow"
```

Use `Literal["allow", "reject"]` to match the existing `UnknownItemAction`
naming convention in `contracts.py`. Default: `reject` (strict).

- `reject` (default): candidates with unidentified entity fillers fail
  validation. Existing profiles are unaffected.
- `allow`: candidates with unidentified entity fillers pass validation and
  enter review normally.

Implementation touches:

- `LoadedProfile` dataclass (`loaders.py:129`): add
  `unidentified_entity_fillers: str` field (default `"reject"`).
- Profile manifest parser (`loaders.py`, around line 475): extract the
  setting from the `validation` block of the profile manifest YAML.
- `_check_entity_ids` (`validation.py:276`): read
  `profile.unidentified_entity_fillers` and skip the
  `oc:hard_missing_entity_id` finding when `"allow"` and the filler has
  `entity_type`.

The `psyop_seed@0.1.0` profile stays `reject` for the verification run.
To test the permissive path, either create a `psyop_seed_permissive`
profile variant or bump to `psyop_seed@0.2.0` with `allow`.

The verification run should test both paths:

1. strict (`reject`): confirm alias and predicate fixes improve the
   structural acceptance rate;
2. permissive (`allow`): confirm opinion candidates with typed-but-
   unidentified fillers now pass validation and reach review.

### D4: Failure taxonomy — extend existing infrastructure

`ExtractionPromptExperimentService` in `evaluation/prompt_eval_service.py`
already classifies trial-level structural failures into 8 categories:

| Existing label | Description |
|---|---|
| `rate_limited` | Provider rate limit or key exhaustion |
| `length_truncated` | Output hit token/length limit |
| `multiple_tool_calls` | Provider returned multiple tool-call blocks |
| `unnamed_entity_filler` | Entity filler without name or ID |
| `empty_roles` | Candidate with no role fillers |
| `bad_evidence_span` | Evidence text doesn't match source |
| `schema_validation_error` | Response didn't parse into expected model |
| `other_failure` | Catch-all |

These cover trial-level structural failures. Extend with **semantic
rejection labels** for candidate-level review classification:

| New label | Description |
|---|---|
| `alias_self_reference` | Abbreviation expansion extracted as a relationship |
| `wrong_predicate` | Predicate doesn't match the evidence |
| `unattributed_opinion` | Opinion predicate with no identifiable speaker |
| `weak_grounding` | Structurally valid but not supported by the text |
| `entity_type_mismatch` | Filler entity type doesn't match what the text describes |

The structural labels are already wired into
`ExtractionPromptExperimentService`. The semantic labels are applied
during human/agent review after extraction, not during the experiment
run itself. Both sets appear in the verification report.

### D5: Use existing evaluation infrastructure

`onto-canon6` already has the evaluation infrastructure for this work:

1. **`ExtractionPromptExperimentService`** (`evaluation/prompt_eval_service.py`)
   runs prompt variants over the benchmark fixture with configurable N
   runs, computes a 3-dimensional score (exact_f1 * 0.65 +
   structural_usable_rate * 0.25 + count_alignment * 0.10), classifies
   failures, and compares variants with statistical significance tests.

2. **Four prompt variants already exist** in `config/config.yaml`:
   `baseline`, `hardened`, `compact`, `single_response_hardened` — with
   corresponding prompt assets in `prompts/extraction/`. Do not recreate
   these. A bounded live sweep on 2026-03-21 successfully executed all
   four variants when explicitly run with `--selection-task
   budget_extraction --comparison-method bootstrap --n-runs 2
   --case-limit 1`. Keep using that explicit override as the prompt-
   iteration harness until the default experiment lane is demonstrably
   stable.

3. **`LiveExtractionEvaluationService`** (`evaluation/service.py`)
   provides the 3-lane evaluation (reasonableness, structural validation,
   canonicalization fidelity) for individual extraction runs.

4. **llm_client experiment lifecycle** (`start_run`, `log_item`,
   `finish_run`) is already integrated. Results go to SQLite + JSONL.
   Use `python -m llm_client experiments compare` to compare runs.

5. **llm_client deterministic checks** (`run_deterministic_checks_for_items`)
   can validate structural integrity guards (`prediction_present`,
   `no_item_error`, `trace_id_present`) automatically.

6. **llm_client gate policies** can formalize acceptance criteria as
   machine-readable pass/fail:

   ```json
   {
     "fail_if": {"deterministic_pass_rate_lt": 1.0},
     "pass_if": {"avg_review_score_gte": 0.5}
   }
   ```

   Consider defining a gate policy for the verification run so pass/fail
   is automated, not prose. This is optional — the manual verification
   tables are still the primary acceptance criteria.

The current implication of D5 is simple: use the existing infrastructure
for all prompt-quality work until a real semantic blocker proves that more
infrastructure is required.

### D6: Expand benchmark fixture to cover targeted failure modes

The current benchmark fixture (`tests/fixtures/psyop_eval_slice.json`)
has only 2 cases with 6 expected candidates. It was built before the
Stage 1 failure modes were identified and does not test any of them:

| Failure mode | Covered? |
|---|---|
| Abbreviation expansion as relationship | No |
| Subordinate-unit → wrong predicate | No |
| MOS codes as entities | No |
| Unattributed opinion (no named speaker) | No |

Without cases that exercise these patterns, Phase A cannot measure
whether the prompt hardening actually helps — it can only check for
regression on the existing 2 cases.

Add 2-3 benchmark cases before Phase A:

1. A text containing an abbreviation expansion like "USAFRICOM (U.S.
   Africa Command)" where the correct behavior is to extract zero
   relationship candidates from the expansion itself. Expected:
   no `belongs_to_organization` between USAFRICOM and U.S. Africa
   Command.

2. A text containing subordinate-unit language like "the 4th POG(A) is
   a subordinate unit of the 1st Special Forces Command" where the
   correct predicate is `belongs_to_organization`, not
   `hold_command_role`. Expected: one `belongs_to_organization` candidate.

3. A text containing passive/unattributed opinion like "concerns have
   been raised about the effectiveness of MISO" where no specific speaker
   is named. For the fixture (Phase A), write expected output for the
   strict profile: zero opinion candidates from this text. The
   `ExtractionPromptExperimentService` requires a single shared profile
   and the fixture format has a fixed `expected_candidates` list — no
   conditional expectations. The permissive path (unidentified speaker
   fillers reaching review) is tested in Phase B, not Phase A.

These cases can use real text from the Stage 1 corpus or synthetic text
that exercises the same patterns. Synthetic is fine — the point is to
have expected-candidate reference data for the scoring lanes.

### D7: Note on prompt variant coverage

The `single_response_hardened` variant addresses structural reliability
(single response, no empty roles) but does NOT include the D2 error-check
rules from the `hardened` variant. After this plan is implemented, the
implementing agent should consider whether a combined variant (hardened
error-checks + single-response structural rules) is worth creating. This
is not blocking — Phase A will measure all 4 existing variants and the
data will show whether the combination is needed.

The config has `n_runs: 2`; this plan recommends `n_runs: 3` for more
statistical power on the expanded fixture. For bounded live viability
checks, keep `n_runs: 2` as the minimum honest bootstrap shape. Only bump
to `n_runs: 3` after the expanded fixture is structurally stable.

### D8: Use the bounded budget lane as the semantic-iteration harness

Until the default experiment lane is stable, prompt iteration should use a
small explicit live command:

```bash
env LLM_CLIENT_PROJECT=onto-canon6-extraction-sweep-budget5 \
  LLM_CLIENT_TIMEOUT_POLICY=ban \
  ./.venv/bin/python -m onto_canon6 run-extraction-prompt-experiment \
  --case-limit 1 \
  --n-runs 2 \
  --comparison-method bootstrap \
  --selection-task budget_extraction \
  --output json
```

That harness is now the regression guard for prompt changes. The rule is:

- if a prompt change cannot keep this harness structurally green, do not
  broaden the experiment;
- if the harness stays green but scores stay flat, work on semantic
  benchmark coverage and prompt semantics, not on runtime plumbing;
- do not change the repo-default selection task to `budget_extraction`
  until the non-override path is stable.

## Acceptance Criteria

1. The extraction prompts preserve the now-proven structural contract
   (one structured response, one `candidates` array, no empty-role
   candidates) while adding semantic guidance for the targeted failure
   modes.
2. The benchmark fixture includes cases that exercise all three targeted
   failure modes (alias expansion, subordinate-unit predicate,
   unattributed opinion).
3. The bounded live viability sweep in D8 completes with scored trials for
   all four variants and 0 structural failures. This is the regression
   guard for future prompt changes.
4. The expanded Phase A benchmark uses the D0 extraction-boundary exact
   contract and therefore produces non-zero `exact_f1` when predicate/role
   semantics are genuinely correct even if reviewer IDs differ.
5. The expanded Phase A benchmark shows semantic improvement over the
   2026-03-21 bounded live baseline and over the baseline variant on at
   least one of `mean_score` or `exact_f1`, without structural
   regression.
6. Phase B (review-quality verification) shows measurable improvement on
   the strict profile (see Verification section).
7. If the unidentified-filler mechanism is implemented, then
   `ExtractedFiller._validate_shape`, validation, and prompt rendering all
   follow D1 and D3 consistently.
8. All existing tests continue to pass.
9. New tests cover: benchmark cases for the targeted semantic failures,
   prompt negative guidance rendering, and any unidentified-filler policy
   path that is actually implemented.
10. Each rejected candidate in Phase B is labeled with a D4 semantic
    failure taxonomy label.

## Verification

### Experiment design

Run verification in two phases:

**Phase A0 — Bounded live viability check:**

Run the D8 command exactly. This is not the semantic proof. It is the
"can we iterate honestly on a real live lane?" check.

This phase is already green as of 2026-03-21:

- all four variants produced scored trials
- all four variants had `structural_usable_rate = 1.0`
- all four variants tied semantically (`mean_score = 0.275`,
  `exact_f1 = 0.0`)

Future prompt edits must preserve that structural viability before moving
to the expanded benchmark.

**Phase A — Prompt experiment (automated, uses existing infrastructure):**

Use `ExtractionPromptExperimentService` with the benchmark fixture. After
expanding the fixture with the D6 semantic cases, run all 4 existing
variants (`baseline`, `hardened`, `compact`, `single_response_hardened`).
Use `n_runs: 2` for the first expanded-fixture sweep if needed to keep the
lane stable; bump to `n_runs: 3` once that expanded sweep is structurally
green. The service handles:

- multi-run execution with failure classification
- 3-dimensional scoring (exact_f1, structural_usable_rate, count_alignment)
- statistical comparison across variants (Welch or bootstrap per config)
- experiment logging to llm_client observability (SQLite + JSONL)

Compare results with `python -m llm_client experiments compare`.

As of 2026-03-21, three expanded-fixture runs now exist:

1. initial expanded baseline
2. guardrail + `kind` rerun
3. contract-aligned rerun using D0 exact scoring

The third run is the current honest baseline for Phase A interpretation:

- `baseline`: `mean_score = 0.34`, `exact_f1 = 0.20`
- `compact`: `mean_score = 0.3639`, `exact_f1 = 0.2222`, but with
  `n_errors = 1`
- `hardened`: `mean_score = 0.335`, `exact_f1 = 0.20`
- `single_response_hardened`: `mean_score = 0.345`, `exact_f1 = 0.20`

Bootstrap comparisons remain non-significant. So the contract alignment is
done, but the semantic selection problem is still open.

**Phase B — Review-quality verification (manual or agent-assisted):**

Run live extraction over 4-6 real documents (the 3 Stage 1 docs plus 1-3
additional) using the best-performing variant from Phase A. Review
extracted candidates and label each rejection with D4 semantic taxonomy
labels. This tests real-world quality, not just benchmark fidelity.

The additional documents should cover different text structures to test
generalization: e.g. one narrative-heavy, one with tables/lists, one with
attributed quotes. Synthetic documents are acceptable if they exercise the
targeted failure modes. The implementing agent selects or creates these.

### Structural reliability guards (must pass, both phases)

| Guard | Target |
|---|---|
| bounded D8 viability sweep | pass |
| `schema_validation_error` trials | 0 |
| `multiple_tool_calls` trials | 0 |
| `length_truncated` trials | 0 |

These are already tracked by `ExtractionPromptExperimentService`. If any
guard fails, fix the structural issue before measuring semantic quality.

### Phase A targets (benchmark)

| Metric | Target |
|---|---|
| structural_usable_rate (all variants) | >=0.95 |
| at least one variant exact_f1 | >0.0 |
| D0 extraction-boundary exact lane in place | yes |
| at least one non-baseline variant beats baseline on `mean_score` or `exact_f1` | yes |
| 0 structural failure trials across all variants | yes |

### Phase B targets (strict profile — primary success metric)

| Metric | Stage 1 baseline | Target |
|---|---|---|
| Alias self-references produced | 2 | 0-1 |
| Wrong predicate choices | 4 | 1-2 |
| Structural claim acceptance rate | 75% (6/8) | >80% |
| Overall acceptance rate (strict) | 37.5% (6/16) | >50% |

The >50% target applies to the strict profile run. Improvement comes from
prompt fixes reducing alias and predicate errors, not from the permissive
policy letting more candidates through.

### Phase B targets (permissive profile — unidentified-filler mechanism, optional)

| Metric | Stage 1 baseline | Target |
|---|---|---|
| Opinion candidates reaching review | 0 (all omitted or rejected) | >2 |
| Opinion candidates with typed unidentified fillers | 0 | >0 |

The permissive run is a separate signal about whether the
unidentified-filler mechanism works, not about overall acceptance rate. It
is only in scope if Steps 6-8 in Build Order are justified by the
expanded benchmark and dry review.

### Measurement notes

The target is a reasonable baseline, not perfection. The review workflow
handles residual errors.

Before Phase B (which costs money), do a dry review: compare the new
prompt outputs against the 10 rejected Stage 1 candidate payloads and the
new D6 fixture cases to confirm the changes would have prevented the
observed alias and predicate errors.

### If the targets are not met

The existing prompt variants (`hardened`, `compact`,
`single_response_hardened`) are already configured and ready to test. If
the surgical baseline fixes (D2) do not reach the >50% strict acceptance
target, Phase A will show which variant performs best and the D4 failure
taxonomy will show which failure modes remain. Use that data to decide
whether to adopt a different variant as the new default or to make further
targeted prompt changes. Do not add new variants until the existing four
have been measured.

## Build Order

1. **Hold the infrastructure constant**: The current experiment boundary is
   good enough. Do not add new prompt-eval or llm_client infrastructure
   unless a real semantic blocker proves it is needed.
2. **Benchmark fixture expansion first** (D6): Add 2-3 cases to
   `tests/fixtures/psyop_eval_slice.json` that exercise the targeted
   semantic failure modes. Do this before broader code changes so prompt
   iteration has an honest measuring surface.
3. **Dry review and taxonomy pass**: Compare current live outputs against
   the 10 rejected Stage 1 candidates and label failures with the D4
   semantic taxonomy. Confirm which categories remain dominant now that
   the bounded live lane is structurally green.
4. **Prompt iteration on the bounded D8 harness**: After each prompt
   change, rerun the bounded live sweep. Do not broaden the experiment
   until it stays structurally green.
5. **Expanded Phase A benchmark**: Run all four variants over the
   expanded fixture and compare them. This is the first real semantic
   selection gate.
6. **Contract-align Phase A exact scoring** (D0): Keep prompt-eval exact
   matching local to the extraction boundary so Phase A is not confounded
   by reviewer IDs or downstream normalization shape. This is now done.
7. **Filler contract** (conditional, only if the expanded fixture or dry
   review still shows unattributed-opinion loss as a material blocker):
   a. Relax `ExtractedFiller._validate_shape` to allow entity fillers with
      `entity_type` but no `name`/`entity_id`.
   b. Update `_pipeline_filler_from_extracted` so unidentified fillers
      bypass `_derive_local_entity_id` and persist with no `entity_id`.
8. **Profile policy** (conditional, paired with Step 7):
   a. Add `unidentified_entity_fillers: Literal["allow", "reject"]` to the
      profile manifest schema and `LoadedProfile` (`loaders.py`).
   b. Make `_check_entity_ids` in `validation.py` conditional on the
      profile setting.
   c. Default `reject` so existing profiles are unaffected.
9. **Prompt policy rendering** (only if Steps 7-8 happen): Extend
   `_render_predicate_catalog` or add a new template variable to
   communicate the active unidentified-filler policy.
10. **Tests**: Cover the expanded benchmark fixture, prompt rendering, and
   any unidentified-filler policy path that is actually implemented.
11. **Phase B — Review-quality verification**: Using the best-performing
    variant from Phase A, extract 4-6 real documents with the strict
    profile. Run the permissive profile only if Steps 6-8 were justified by
    the evidence.

Steps 2, 4, 5, and 6 are now complete. The immediate next thin slice is
Step 3: dry review and taxonomy over the current expanded-fixture outputs so
the next prompt iteration is driven by the remaining semantic failures, not
by benchmark-contract ambiguity. Steps 7-9 are conditional, not automatic.
The point is still to prove whether unidentified fillers are a real blocker
before adding the policy dimension.

## Non-Goals

1. Do not redesign the extraction pipeline architecture.
2. Do not add new predicates or entity types to the psyop_seed pack.
3. Do not build new evaluation infrastructure — use the existing
   `ExtractionPromptExperimentService` and `LiveExtractionEvaluationService`.
4. Do not chase perfection — the review workflow handles residual errors.
5. Do not remove the opinion/sentiment predicates from the seed pack. Let
   the profile policy and review workflow sort them.

## Known Risks

1. Prompt negative guidance may be model-specific — what reduces errors
   for one model may not transfer to another. Keep guidance general.
2. The `unidentified_entity_fillers` policy adds a new profile dimension.
   The `reject` default avoids changing behavior for existing profiles.
3. The verification run uses the same corpus as Stage 1. Improvement on
   this corpus may not generalize. Acceptable for a baseline; broader
   benchmark is future work.
4. Downstream graph promotion needs typed entities — unidentified fillers
   can pass validation and review but cannot promote until identity is
   resolved. This is acceptable: promotion is already a separate explicit
   step.

## Relationship to Prior Work

- Driven by: `docs/runs/2026-03-18_psyop_stage1_friction_log.md` entries
  5 and 7
- Extends: Phase 4 (extraction), Phase 5 (evaluation), Phase 0 (ontology
  runtime validation)
- Does not reopen: Phase 15 (epistemic), Phase 13 (semantic stack), or
  broad parity work
