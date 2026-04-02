# 24h Live Review Alignment Block

Status: active
Phase status:
- Phase 1 pending
- Phase 2 pending
- Phase 3 pending
- Phase 4 pending
- Phase 5 pending

Last updated: 2026-04-02
Workstream: corrected-fixture transfer recovery through live review-contract alignment

## Purpose

Plan `0057` proved that the current chunk-transfer report can produce a false
positive on chunk `003`: the report is driven by accepted/rejected review
counts, and the live `review_mode: llm` path currently accepts candidates that
the corrected benchmark contract now treats as omit cases.

This block exists to align the live LLM review gate with corrected fixture `v6`
semantics, rerun the two named transfer chunks under that aligned contract, and
state the promotion posture truthfully.

## Scope

This block intentionally covers only:

1. the live LLM judge acceptance contract;
2. the judge prompt wording needed to encode corrected omit semantics for the
   active chunk-003 failure family;
3. targeted tests for the live review path; and
4. one fresh rerun of the two named transfer chunks under the aligned review
   contract.

Out of scope:

1. new benchmark cases unrelated to the active chunk-003 family;
2. broad prompt-family redesign beyond the current compact prompt;
3. transfer-report surface redesign; and
4. changing the named transfer chunks.

## Pre-Made Decisions

1. Work stays in the isolated `codex/onto-canon6-integration-planning`
   worktree.
2. Chunk `002` remains the positive control and chunk `003` remains the
   prose-heavy stress case.
3. The extraction prompt remains:
   - template:
     `prompts/extraction/text_to_candidate_assertions_compact_v5.yaml`
   - prompt ref:
     `onto_canon6.extraction.text_to_candidate_assertions_compact_v5@2`
4. The review contract for `review_mode: llm` is now frozen as:
   - `supported` -> auto-accept and promote
   - `partially_supported` -> leave pending review
   - `unsupported` -> auto-reject
5. The live judge prompt remains the same file path but may be revised in place
   to encode corrected omit semantics:
   - `prompts/evaluation/judge_candidate_reasonableness.yaml`
6. The fresh rerun root for this block is:
   - `var/real_runs/2026-04-02_live_review_alignment/`
7. The block may end either with:
   - chunk `003` no longer producing a false-positive transfer result; or
   - a truthful statement that even with aligned review semantics the compact
     prompt still emits too many chunk-003 candidates.

## Gate

This block succeeds only if:

1. the live review contract is explicit in code, tests, and docs;
2. the judge prompt explicitly covers the corrected analytical-prose omit
   family;
3. chunk `002` is rerun and still behaves as a positive control under the
   aligned contract;
4. chunk `003` is rerun under the aligned contract; and
5. the repo states clearly whether the lane is still blocked by prompt
   semantics or whether the review-contract mismatch was the dominant issue.

## Phase Order

### Phase 1: Freeze The Live Review Contract

#### Tasks

1. close Plan `0057` truthfully with the false-positive transfer finding;
2. activate this block in the authority docs;
3. record the supported/partial/unsupported acceptance policy explicitly.

#### Success criteria

1. the active block is truthful everywhere;
2. the live review contract is explicit before code changes begin.

### Phase 2: Align Review Behavior In Code

#### Tasks

1. change `review_mode: llm` so only `supported` candidates auto-accept;
2. leave `partially_supported` candidates pending review;
3. keep `unsupported` candidates auto-rejected;
4. add or update targeted tests for those transitions.

#### Success criteria

1. code, config language, and tests all agree on the contract;
2. no accepted candidate can come from a merely `partially_supported` label.

### Phase 3: Harden The Judge Prompt Against The Active Omit Family

#### Tasks

1. encode the corrected chunk-003 omit semantics in the judge prompt;
2. make the prompt distinguish concrete supported facts from abstract
   evaluative narration and generic ethical/legal commentary;
3. add or update prompt-adjacent regression tests if the repo has a narrow seam
   for them.

#### Success criteria

1. the active omit family is described explicitly in the judge prompt;
2. the prompt changes are verified by targeted tests or narrow replay evidence.

### Phase 4: Rerun The Named Transfer Chunks

#### Tasks

1. rerun chunk `002` under a fresh aligned-review DB;
2. rerun chunk `003` under the same aligned-review DB;
3. export both chunk-transfer reports; and
4. inspect whether chunk `003` still produces accepted candidates from the
   corrected strict-omit family.

#### Success criteria

1. fresh chunk-002 and chunk-003 artifacts exist;
2. chunk `003` no longer produces an unexamined false-positive transfer
   verdict.

### Phase 5: Classify Promotion Posture And Close Out

#### Tasks

1. write the decision note for the rerun block;
2. classify the lane as:
   - still transfer-blocked by prompt semantics; or
   - newly clear on the review-contract side;
3. refresh `CLAUDE.md`, `TODO.md`, `HANDOFF.md`, `docs/STATUS.md`,
   `docs/plans/CLAUDE.md`, `docs/plans/0014_extraction_quality_baseline.md`,
   and `KNOWLEDGE.md`;
4. mark the block complete only when the worktree is clean.

#### Success criteria

1. the promotion posture is explicit and decision-grade;
2. the next blocker is named precisely;
3. the worktree is clean.
