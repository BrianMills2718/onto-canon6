# 24-Hour Successor Ownership Execution Block

Status: completed

Last updated: 2026-03-28
Workstream: continuous implementation block

## Purpose

Define the next 24 hours of work as one explicit execution block and remove
ambiguity about what "done" means for that block.

This plan exists so agents do not stop after partial cleanup or ask for routine
next-step confirmation while the successor-ownership work is still in flight.

## Result

Completed on 2026-03-28.

Delivered:

1. stronger autonomous-execution guidance in `CLAUDE.md`;
2. Tier A donor assets absorbed locally;
3. canonical `sumo_plus.db` cut over to `data/sumo_plus.db`;
4. config, setup verification, tests, and docs updated to the local-first
   contract;
5. provenance notes added for imported profiles, packs, and data assets;
6. verification passed in both the main repo and an isolated temp copy with no
   donor sibling repos available.

## Execution Rule

Execute phases in order and continue without pausing between them unless one of
the following happens:

1. a concrete blocker prevents further safe progress;
2. a real uncertainty appears that the current docs/plans do not resolve;
3. the full acceptance criteria for this plan are met.

## Scope

This 24-hour block covers:

1. Tier A donor absorption;
2. successor-local ownership cutover;
3. `sumo_plus.db` ownership finalization;
4. verification in normal and donor-isolated conditions;
5. plan/doc alignment after implementation.

This block does not cover:

1. extraction-quality prompt iteration;
2. consumer adoption work beyond keeping current integrations working;
3. dormant parity capabilities not required for archive readiness.

## Acceptance Criteria

This block is complete only when all of the following are true:

1. `default@1.0.0`, `dodaf@0.1.0`, `psyop_seed@0.1.0`, and
   `onto_canon_psyop_seed@0.1.0` are owned locally by `onto-canon6`;
2. the canonical `sumo_plus.db` path is local to this repo;
3. `config/config.yaml`, `README.md`, `scripts/verify_setup.py`, and the tests
   describe the same successor-local ownership contract;
4. the supported verification surface passes without needing sibling
   `../onto-canon5` or `../onto-canon`;
5. imported donor assets have explicit provenance notes;
6. the repo ends clean, committed, and with updated plans/docs reflecting the
   new state.

## Phase Breakdown

### Phase 1. Guidance And Planning Lock

Deliverables:

1. strengthen `CLAUDE.md` for continuous autonomous execution;
2. record the 24-hour execution block in this plan.

Pass condition:

The repo guidance makes it explicit that agents should keep running through the
active plan unless blocked.

### Phase 2. Tier A Donor Asset Absorption

Deliverables:

1. local copies of:
   - `profiles/default/1.0.0`
   - `profiles/dodaf/0.1.0`
   - `profiles/psyop_seed/0.1.0`
   - `ontology_packs/onto_canon_psyop_seed/0.1.0`
2. provenance notes for imported profiles and packs

Pass condition:

The assets exist locally and can be resolved through the current local-first
loader search order.

### Phase 3. SUMO Ownership Cutover

Pre-made decision:

`onto-canon6/data/sumo_plus.db` becomes the canonical owned DB for this repo.
The current local file already matches the donor DB byte-for-byte, so this
phase is a contract cutover, not a speculative rebuild project.

Deliverables:

1. config default switched to local `data/sumo_plus.db`;
2. provenance note for the DB;
3. scripts stop pretending two DB copies are canonical.

Pass condition:

The repo has one canonical `sumo_plus.db` path.

### Phase 4. Contract Cutover

Deliverables:

1. config/tests/setup verification updated to local-first successor ownership;
2. docs updated so the current contract is no longer "requires donor repos";
3. loader tests rewritten to protect the successor contract instead of the
   bootstrap donor contract.

Pass condition:

Normal development flows no longer require `../onto-canon5` or `../onto-canon`.

### Phase 5. Verification

Deliverables:

1. supported checks pass in the normal repo location;
2. an isolation verification run proves the repo works without donor-repo
   siblings.

Required verification:

1. `make verify-setup`
2. `make smoke`
3. `make check`
4. targeted runtime tests if anything fails during migration
5. isolated run from a temporary location with no donor repos available

Pass condition:

The successor is operational without donor siblings.

### Phase 6. Post-Cutover Alignment

Deliverables:

1. plans updated if implementation answered any recorded uncertainties;
2. docs/STATUS wording corrected where it still describes donor loading as the
   present contract;
3. repo ends clean and committed.

Pass condition:

The repo state, docs, and plans are aligned.

## Failure Modes

### Failure Mode 1. Local Assets Exist But Runtime Still Reaches Donor Paths

Diagnosis:

1. search for `../onto-canon5` and `../onto-canon`;
2. run isolation verification.

### Failure Mode 2. `sumo_plus.db` Ownership Is Ambiguous

Diagnosis:

1. inspect config default;
2. inspect scripts that write to the DB;
3. compare provenance notes.

### Failure Mode 3. Asset Absorption Breaks Compatibility

Diagnosis:

1. run loader/runtime tests around `default`, `dodaf`, and `psyop_seed`;
2. inspect profile ids, pack ids, and overlay targets for accidental changes.

## Stop Conditions

Do not stop for routine progress reporting. Stop only if:

1. a blocker prevents safe continuation;
2. a new uncertainty requires a decision not already covered by Plans 0022/0023;
3. the acceptance criteria are fully satisfied.
