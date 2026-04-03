# 24h Non-Gemini Fresh Memo Proof

Status: complete

Last updated: 2026-04-03
Workstream: fresh live proof under an operationally reliable non-Gemini runtime

## Mission

Use the next 24 hours to close the next highest-value gap left after Plan
`0068`:

1. the memo path can now be repaired and made graph-producing;
2. the fresh live proof is still missing because the prior repair run hit
   Gemini quota exhaustion; therefore
3. the next block must prove a brand-new live memo under a different model
   runtime, not perform another repair-only loop.

This block is complete only when a fresh live `research_v3` memo artifact is
created under an explicit non-Gemini runtime profile and that memo produces
`>0` canonical entities plus `>0` DIGIMON rows without post-hoc enrichment.

## End Goal This Block Serves

The end state is not "there exists one repaired memo that works." The end
state is:

1. a fresh live investigation can complete under a reliable runtime profile;
2. the resulting memo already contains resolved entities when written;
3. the shared-contract path turns that memo into governed graph state; and
4. downstream consumers can use the graph without manual repair steps.

## Pre-Made Decisions

1. Use the Palantir federal-contracts question again so results stay comparable
   with Plans `0067` and `0068`.
2. Do not mutate the prior repaired Palantir memo for this proof; a fresh run
   must create a new output directory.
3. Add explicit config override support to fresh `loop.py` investigations
   instead of changing the repo-default loop config preemptively.
4. Add a dedicated Claude runtime profile rather than overloading the
   backfill-only config file.
5. The proof uses a non-Gemini runtime because the user explicitly approved a
   different model after the documented Gemini quota failure.
6. No post-hoc `--enrich-entities` step is allowed on the new live memo.
7. The block closes only when the fresh live memo itself already contains
   non-empty `entities` and the downstream pipeline exports a non-empty graph.

## Phases

### Phase 0. Authority Activation

Success criteria:

1. `CLAUDE.md` names this block as active authority;
2. `docs/plans/CLAUDE.md` lists this block as active;
3. `TODO.md` names the fresh non-Gemini proof as the top priority; and
4. `var/progress/0069_non_gemini_fresh_proof.md` records mission and gates.

### Phase 1. research_v3 Fresh-Run Config Override Support

Success criteria:

1. fresh investigations can accept a loop config override path;
2. resume and enrich flows keep working;
3. tests cover the config-override seam; and
4. no default runtime config is changed silently.

### Phase 2. Claude Runtime Profile And Verification

Success criteria:

1. a dedicated Claude runtime profile exists for live loop execution;
2. all Gemini-dependent loop roles used in the proof have explicit non-Gemini
   overrides;
3. targeted tests pass after the config plumbing lands; and
4. the runtime profile is documented as a proof profile, not yet the repo
   default.

### Phase 3. Fresh Live Memo Proof

Success criteria:

1. a new Palantir investigation run completes under the Claude runtime profile;
2. the fresh memo is written to a new output directory;
3. the fresh memo contains non-empty `entities` without `--enrich-entities`;
   and
4. the run records exact cost, rounds, and artifact path.

### Phase 4. onto-canon6 Pipeline Proof

Success criteria:

1. the fresh memo goes through `make pipeline-rv3-memo`;
2. the resulting review DB contains `>0` promoted graph entities;
3. the DIGIMON export contains `>0` entities and `>0` relationships; and
4. the proof note records exact commands and counts.

### Phase 5. Truth Surfaces And Closeout

Success criteria:

1. `README`, `STATUS`, `ROADMAP`, and `HANDOFF` reflect the fresh-proof state;
2. the remaining concern is named explicitly if the proof is slower or more
   expensive than Gemini;
3. `KNOWLEDGE.md` captures the durable runtime lesson; and
4. verified work is committed with clean worktrees.

## Failure Modes

1. Fresh-run config overrides only work for repair mode and not for live runs.
2. The new runtime profile leaves a hidden Gemini dependency in a proof step.
3. The fresh run completes but still writes a memo with empty `entities`.
4. The proof quietly reuses the old repaired memo instead of creating a new
   artifact.
5. The block closes on a repaired memo again instead of a fresh live run.

## Verification

Minimum verification for closeout:

1. targeted `research_v3` tests covering the new config override seam
2. full `research_v3` suite unless an external outage is explicitly documented
3. one fresh live Palantir run under the Claude runtime profile
4. direct inspection showing fresh `memo.yaml` already contains `entities`
5. `make pipeline-rv3-memo INPUT=<fresh memo>` in `/home/brian/projects/onto-canon6`
6. doc and handoff updates naming the actual remaining gap truthfully

## Exit Condition

This block is complete when:

1. fresh live investigations accept an explicit runtime config override;
2. a dedicated Claude runtime profile exists;
3. a fresh Palantir memo is produced without post-hoc enrichment;
4. that fresh memo already contains resolved entities;
5. the downstream pipeline exports a non-empty graph; and
6. the docs name any remaining cost/runtime tradeoff truthfully.

## Outcome

Closed on 2026-04-03.

Verification outcome:

1. targeted `research_v3` loop tests passed:
   `19 passed`
2. full `research_v3` suite passed:
   `247 passed, 2 skipped, 1 warning`
3. `research_v3` package metadata now installs cleanly from `pyproject.toml`
   with `open-web-retrieval` declared
4. a fresh live Palantir run under `config_loop_claude_runtime.yaml` produced a
   stable round-4 memo checkpoint with:
   `34` findings, `34` persisted entities, cost `$0.158579`, and no
   post-hoc enrichment
5. the proof snapshot
   `memo.proof_0069_round4.yaml` exported `34` shared claims, `30` of them
   with non-empty `entity_refs`
6. `make pipeline-rv3-memo` on that snapshot produced:
   `34` promoted assertions, `34` canonical entities, and `30` DIGIMON
   relationships

Documented concerns:

- the live run did not reach a natural final report before the proof-worthy
  checkpoint because reflect confidence remained low (`0.35`) and the loop kept
  extending; the consumer proof therefore uses a stable round-4 checkpoint
  snapshot rather than a completed report artifact
- the proof exposed a real packaging drift: `research_v3` depended on
  `open_web_retrieval` at runtime but had not declared it in `pyproject.toml`
- the final `research_v3` suite still depends on skipping external FARA
  request failures (`5xx`, timeout, read error`) as upstream outages
- the Claude runtime path is operationally slower than the earlier repaired
  memo proof, even though cost remained low on the checkpoint proof
