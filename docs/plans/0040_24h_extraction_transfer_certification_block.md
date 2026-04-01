# 24h Extraction Transfer Certification Block

Status: active
Phase status:
- Phase 1 completed
- Phase 2 in progress
- Phase 3 completed
- Phase 4 in progress
- Phase 5 pending

Last updated: 2026-04-01
Workstream: convert Plan `0014` from diffuse transfer-gap tracking into one
decision-grade certification pass

## Purpose

Plan `0014` already has a promotion policy, named chunks, and a narrowed live
transfer gap. What it does not yet have is one bounded execution block that
forces a concrete decision on the current candidate extraction lane.

This block exists to answer exactly one question:

Can the current compact operational-parity candidate be certified honestly for
promotion consideration, or does the chunk-transfer gap still fail in a way the
repo can localize precisely?

## Scope

This block intentionally covers only:

1. the current compact operational-parity extraction lane under Plan `0014`;
2. the named real chunks already central to the transfer gate:
   - chunk `002` as the positive transfer case
   - chunk `003` as the prose-heavy negative/mixed transfer case
3. direct live-vs-parity operational comparison for those chunks;
4. the minimum harness or replay aid needed to make that comparison
   certification-grade;
5. a written decision on whether the current candidate is promotable,
   blocked on transfer, or blocked on runtime/path differences.

Out of scope:

1. broad new prompt rewrites before the current transfer gap is localized;
2. new ontology/runtime features;
3. DIGIMON or query-surface work;
4. wider corpus verification beyond the two named chunks until this block
   finishes.

## Pre-Made Decisions

1. Work stays in the isolated `codex/onto-canon6-integration-planning`
   worktree.
2. The current candidate under test is the compact operational-parity lane
   already named in Plan `0014`; this block does not open a second competing
   candidate family.
   - live extraction candidate asset:
     `prompts/extraction/text_to_candidate_assertions_compact_v4.yaml`
   - prompt-eval operational-parity asset:
     `prompts/extraction/prompt_eval_text_to_candidate_assertions_compact_operational_parity_v2.yaml`
3. The certification decision must be based on:
   - prompt-eval artifact evidence,
   - live extract-text artifact evidence, and
   - real review outcomes,
   not on prompt text inspection alone.
4. Chunk `002` and chunk `003` remain the canonical transfer chunks for this
   block. No additional chunks are added unless one of those becomes unusable.
5. If the current candidate still fails chunk `003`, the block must decide
   whether the blocker is:
   - prompt/content behavior,
   - live-vs-parity runtime-path difference, or
   - longer-context transfer that requires a different certification harness.
6. Every verified phase gets its own commit.

## Gate

This block succeeds only if:

1. the exact candidate lane under test is frozen in the docs;
2. the repo has one certification-grade comparison path for live vs parity
   chunk outputs;
3. chunk `002` and chunk `003` both have explicit live/parity comparison
   artifacts under `docs/runs/` or `investigations/`;
4. the closeout note states one of the following unambiguously:
   - the candidate is promotable for further consideration;
   - the candidate is not promotable because the transfer gap is still real;
   - the candidate cannot be judged yet because runtime/path parity is still
     unproven, with the missing proof named exactly.

## Phase Order

### Phase 1: Freeze The Certification Contract

#### Tasks

1. name the exact compact candidate lane, prompt asset, and model/task path
   currently under test;
2. freeze the canonical chunk pair (`002`, `003`);
3. freeze the existing incoming evidence from Plan `0014` that this block will
   use.

#### Success criteria

1. the candidate under test is explicit enough that no mid-block choice remains
   about "which compact variant" is being certified;
2. the repo has one canonical source list for the incoming transfer artifacts.

Incoming artifacts frozen for this block:

1. `docs/runs/2026-03-21_chunk_transfer_gate_compact2.md`
2. `docs/runs/2026-03-22_chunk003_full_operational_parity_prompt_eval.md`
3. `docs/runs/2026-03-22_chunk003_compact_v4_candidate_prompt_eval.md`
4. `docs/runs/2026-03-22_compact4_real_chunk_verification_chunk003.md`

Progress note:

1. the live certification candidate is now frozen as:
   - task: `budget_extraction`
   - prompt template:
     `prompts/extraction/text_to_candidate_assertions_compact_v4.yaml`
   - prompt ref:
     `onto_canon6.extraction.text_to_candidate_assertions_compact_v4@1`
   - live extraction model path:
     `config.config.yaml -> extraction.model_override = gemini/gemini-2.5-flash`
2. the prompt-eval operational-parity comparison lane is now frozen as:
   - variant: `compact_operational_parity`
   - prompt template:
     `prompts/extraction/prompt_eval_text_to_candidate_assertions_compact_operational_parity_v2.yaml`
   - prompt ref:
     `onto_canon6.extraction.prompt_eval_text_to_candidate_assertions_compact_operational_parity@2`
   - prompt-eval model path used in the canonical full-chunk run:
     `openrouter/deepseek/deepseek-chat`
   - task: `budget_extraction`
3. that live-vs-parity model mismatch is now an explicit part of the
   certification contract, not a hidden assumption.

### Phase 2: Localize The Live-vs-Parity Gap

#### Tasks

1. compare the current live extraction output against the prompt-eval
   operational-parity output on chunk `003`;
2. compare the same surfaces on chunk `002` so the positive control remains
   visible;
3. write down the exact candidate-level differences:
   added, omitted, or reshaped candidates plus review outcomes.

#### Success criteria

1. the repo can point to exact candidate/output differences, not just aggregate
   score differences;
2. the block no longer depends on vague "transfer gap" language.

Progress note:

1. Phase 2 evidence note:
   `docs/runs/2026-04-01_extraction_transfer_gap_localization.md`
2. chunk `003` is now localized exactly:
   - prompt-eval parity run `0f664c022900` returned `{"candidates":[]}`
   - live compact-v4 extraction still produced three rejected candidates
     (`oc:limit_capability`, `oc:express_concern`, `oc:hold_command_role`)
3. chunk `002` does not yet have the same current-generation parity/live
   artifact pair for the compact-v4 candidate lane. That missing positive
   control is now explicit and becomes Phase 3's reason to add the minimum
   certification helper.

### Phase 3: Land The Minimum Certification Aid

#### Tasks

1. implement the smallest helper needed to make the live-vs-parity comparison
   reproducible;
2. prefer a replay/comparison aid over another prompt rewrite;
3. add verification for that helper.

#### Success criteria

1. the comparison path is reproducible from the repo;
2. the helper is narrow and does not create a second extraction runtime.

Progress note:

1. landed helper module:
   `src/onto_canon6/evaluation/transfer_comparison.py`
2. landed thin wrapper:
   `scripts/compare_extraction_transfer.py`
3. landed verification:
   `tests/evaluation/test_transfer_comparison.py`
4. the helper reads one prompt-eval item from observability plus one live
   reviewed-candidate snapshot and emits a normalized diff over candidate
   signatures.

### Phase 4: Re-run The Certification Check

#### Tasks

1. run the certification comparison on chunk `002`;
2. run the certification comparison on chunk `003`;
3. verify whether the current candidate clears or fails the transfer gate.

#### Success criteria

1. both canonical chunks have fresh comparison artifacts;
2. the candidate's transfer status is evidence-backed.

Progress note:

1. first machine-generated comparison artifact:
   `docs/runs/2026-04-01_chunk003_live_vs_parity_diff.json`
2. chunk `003` is now reproducibly confirmed as:
   - prompt-eval parity candidates: `0`
   - live candidates: `3`
   - shared candidates: `0`
3. chunk `002` still needs current-generation compact-v4 comparison coverage
   before Phase 4 can close.
4. the remaining Phase 4 execution order is now frozen:
   - build one current-generation full-chunk prompt-eval parity artifact for
     chunk `002`;
   - build one current-generation live compact-v4 chunk `002` artifact if an
     equivalent reviewed snapshot does not already exist;
   - diff those artifacts with the transfer-comparison helper;
   - then decide whether the compact-v4 lane is promotable, still
     transfer-blocked, or still blocked on parity/runtime proof.

#### Phase 4 diagnostic rule

If chunk `002` cannot be certified on the same full-chunk parity/live contract
used for chunk `003`, the block must record exactly why:

1. missing parity artifact shape;
2. missing current-generation live reviewed chunk;
3. runtime-path mismatch;
4. or prompt/content behavior.

It must not collapse those into generic "more extraction work needed"
language.

### Phase 5: Closeout

#### Tasks

1. write the decision-grade certification note;
2. refresh Plan `0014`, `CLAUDE.md`, `docs/STATUS.md`, `HANDOFF.md`,
   `KNOWLEDGE.md`, `docs/plans/CLAUDE.md`, and `TODO.md`;
3. either close this block or activate the next bounded extraction block based
   on the result.

#### Success criteria

1. top-level docs describe the extraction-transfer decision truthfully;
2. the next extraction step, if any, is narrowed to one explicit blocker.

## Failure Modes

1. the block devolves into another broad prompt-rewrite campaign;
2. prompt-eval wins are treated as sufficient without live transfer evidence;
3. the live/parity comparison remains aggregate-only and cannot explain the
   current blocker;
4. a new helper silently mutates extraction behavior instead of only making the
   comparison path observable.

## Exit Criteria

This block is complete only when:

1. all five phases above meet their success criteria;
2. the worktree is clean;
3. the repo contains committed artifacts and docs for the certification
   decision.
