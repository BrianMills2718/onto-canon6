# Extraction Quality Baseline

Status: planned

## Purpose

Get extraction quality to a reasonable baseline before moving to new
features or consumers. The Stage 1 real run showed 37.5% acceptance (6/16),
but the failures split into distinct fixable categories. This plan
addresses them without inventing new architecture.

Driven by Stage 1 friction log entries 5 and 7, not by parity pressure.

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

Category 3 is the most interesting semantic failure because the current
prompt hardcodes a policy: "omit any candidate whose roles would require
unnamed entities." This closes off a legitimate use case (sentiment/
thematic analysis where *what* is said matters more than *who* said it).
Sometimes the content of a claim matters more than who made it.

## Design Decisions

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
   these. After applying D2 changes to the baseline prompt, update the
   `baseline` variant asset and run the experiment service to compare all
   four variants.

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
statistical power. The implementing agent should bump this in config
before running Phase A.

## Acceptance Criteria

1. The main extraction prompt and baseline variant include D2
   error-check rules (ported from the existing `hardened` variant).
2. `ExtractedFiller._validate_shape` accepts entity fillers with
   `entity_type` but no `name` or `entity_id`.
3. The validation pipeline checks the active profile's
   `unidentified_entity_fillers` setting and either accepts or rejects
   candidates accordingly.
4. The prompt rendering pipeline communicates the active policy to the
   model.
5. The benchmark fixture includes cases that exercise all three targeted
   failure modes (alias expansion, subordinate-unit predicate,
   unattributed opinion).
6. Phase A (prompt experiment via `ExtractionPromptExperimentService`)
   shows 0 structural failures and no exact_f1 regression on the
   baseline variant.
7. Phase B (review-quality verification) shows measurable improvement
   on the strict profile (see Verification section).
8. All existing tests continue to pass.
9. New tests cover: unidentified filler validation by profile policy,
   prompt negative guidance rendering, and both strict/permissive paths.
10. Each rejected candidate in Phase B is labeled with a D4 semantic
    failure taxonomy label.

## Verification

### Experiment design

Run verification in two phases:

**Phase A — Prompt experiment (automated, uses existing infrastructure):**

Use `ExtractionPromptExperimentService` with the benchmark fixture. After
applying D2 changes to the baseline prompt asset, run all 4 existing
variants (`baseline`, `hardened`, `compact`, `single_response_hardened`)
with `n_runs: 3` per config. The service handles:

- multi-run execution with failure classification
- 3-dimensional scoring (exact_f1, structural_usable_rate, count_alignment)
- statistical comparison across variants (Welch or bootstrap per config)
- experiment logging to llm_client observability (SQLite + JSONL)

Compare results with `python -m llm_client experiments compare`.

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
| `schema_validation_error` trials | 0 |
| `multiple_tool_calls` trials | 0 |
| `length_truncated` trials | 0 |

These are already tracked by `ExtractionPromptExperimentService`. If any
guard fails, fix the structural issue before measuring semantic quality.

### Phase A targets (benchmark)

| Metric | Target |
|---|---|
| structural_usable_rate (baseline variant) | >0.80 |
| exact_f1 does not regress from pre-change baseline | yes |
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

### Phase B targets (permissive profile — unidentified-filler mechanism)

| Metric | Stage 1 baseline | Target |
|---|---|---|
| Opinion candidates reaching review | 0 (all omitted or rejected) | >2 |
| Opinion candidates with typed unidentified fillers | 0 | >0 |

The permissive run is a separate signal about whether the
unidentified-filler mechanism works, not about overall acceptance rate.

### Measurement notes

The target is a reasonable baseline, not perfection. The review workflow
handles residual errors.

Before Phase B (which costs money), do a dry review: compare the new
prompt against the 10 rejected Stage 1 candidate payloads to confirm the
changes would have prevented the observed errors.

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

1. **Prompt hardening**: Apply the D2 error-check rules from the
   existing `hardened` variant to the **main** extraction prompt
   (`prompts/extraction/text_to_candidate_assertions.yaml`). Do NOT
   update the `baseline` variant — it serves as the pre-D2 control for
   Phase A. Phase A compares: baseline (no D2, control) vs hardened
   (has D2) vs compact vs single_response_hardened. If hardened wins,
   the implementing agent can promote it to the new operational default
   after Phase A.
2. **Filler contract** (two changes in `text_extraction.py`):
   a. Relax `ExtractedFiller._validate_shape` to allow entity fillers with
      `entity_type` but no `name`/`entity_id`.
   b. Update `_pipeline_filler_from_extracted` so unidentified fillers
      bypass `_derive_local_entity_id` and persist with no `entity_id`.
3. **Profile policy** (three files):
   a. Add `unidentified_entity_fillers: Literal["allow", "reject"]` to the
      profile manifest schema and `LoadedProfile` (`loaders.py`).
   b. Make `_check_entity_ids` in `validation.py` conditional on the
      profile setting.
   c. Default `reject` so existing profiles are unaffected.
4. **Prompt policy rendering**: Extend `_render_predicate_catalog` or add
   a new template variable to communicate the active unidentified-filler
   policy. When `reject`: keep the existing "omit candidates requiring
   unnamed entities" guidance. When `allow`: tell the model it may produce
   entity fillers with `entity_type` only.
5. **Tests**: Cover both strict and permissive validation paths,
   unidentified filler handling at the extraction boundary, and prompt
   rendering of the policy.
6. **Benchmark fixture expansion** (D6): Add 2-3 cases to
   `tests/fixtures/psyop_eval_slice.json` that exercise the targeted
   failure modes (alias expansion, subordinate-unit predicate, unattributed
   opinion). Bump `n_runs` to 3 in `config/config.yaml`.
7. **Dry review**: Compare the new prompt against the 10 rejected Stage 1
   candidates. Confirm the prompt changes would have prevented alias
   self-references and wrong predicate choices.
8. **Phase A — Prompt experiment**: Run
   `ExtractionPromptExperimentService` with all 4 variants over the
   expanded fixture. Compare with
   `python -m llm_client experiments compare`. Check structural guards
   and Phase A targets.
9. **Phase B — Review-quality verification**: Using the best-performing
   variant from Phase A, extract 4-6 real documents with both strict and
   permissive profiles. Review candidates, label rejections with D4
   semantic taxonomy. Measure against Phase B targets.

Steps 1-2 can be done together. Steps 3-4 can be done together. Step 5
covers both. Step 6 prepares the fixture. Step 7 is cheap (no LLM
calls). Steps 8-9 are the proof.

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
