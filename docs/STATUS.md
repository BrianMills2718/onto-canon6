# onto-canon6 Status

Updated: 2026-03-17

## What Is Proven

`onto-canon6` currently proves a narrow review-and-governance slice built on a
typed ontology runtime:

1. typed ontology policy contracts;
2. deterministic `open|closed|mixed` unknown-item handling;
3. donor profile and ontology-pack loading from `onto-canon5`;
4. local assertion validation against donor predicate rules;
5. persisted candidate assertion records;
6. persisted ontology proposal records with deduplicated links from candidates;
7. explicit proposal review decisions with configurable acceptance policy;
8. candidate-level review decisions with loud transition rules;
9. provenance-aware candidate submissions;
10. a typed report surface for filtered candidate and proposal views;
11. explicit overlay application records with deterministic idempotent writeback;
12. overlay-aware validation after accepted predicate additions are applied;
13. typed text-grounded candidate-import contracts;
14. persisted optional source text, optional claim text, and first-class
    evidence spans on candidate assertions;
15. deterministic evidence-span verification before persistence;
16. one `llm_client`-backed raw-text extraction service that uses a prompt
    asset plus structured output to produce candidate assertions;
17. deterministic end-to-end extraction into the existing review workflow
    without bypassing proposal or overlay logic;
18. notebook probes that make the current behavior inspectable;
19. a typed live extraction-evaluation harness that separates reasonableness,
    structural validation, and exact canonicalization fidelity;
20. a first real-model benchmark proof over the local PSYOP evaluation slice.

Concrete assets:

1. `notebooks/01_policy_contracts.ipynb`
2. `notebooks/02_donor_profile_loading.ipynb`
3. `notebooks/03_validation_slice.ipynb`
4. `notebooks/04_review_slice.ipynb`
5. `notebooks/05_review_reporting_slice.ipynb`
6. `notebooks/06_overlay_application_slice.ipynb`
7. `notebooks/07_text_grounded_import_contract.ipynb`
8. `notebooks/08_text_extraction_slice.ipynb`
9. `notebooks/10_live_extraction_evaluation.ipynb`
10. `prompts/extraction/text_to_candidate_assertions.yaml`
11. `prompts/evaluation/judge_candidate_reasonableness.yaml`
12. `src/onto_canon6/pipeline/text_extraction.py`
13. `src/onto_canon6/evaluation/`
14. tests in `tests/ontology_runtime/`
15. tests in `tests/pipeline/`
16. tests in `tests/evaluation/`
17. `src/onto_canon6/surfaces/review_report.py`
18. `src/onto_canon6/pipeline/overlay_service.py`
19. `src/onto_canon6/ontology_runtime/overlays.py`

Planning companion:

1. `notebooks/09_successor_long_term_plan.ipynb`
2. `notebooks/11_future_phase_breakdown.ipynb`

## What Is Not Proven Yet

Still missing:

1. broader benchmark coverage and calibration beyond the first local live slice;
2. a first operational surface outside notebooks and direct Python calls;
3. second-pack generalization beyond the current donor packs;
4. artifact-lineage recovery;
5. epistemic extension;
6. product-facing end-to-end workflow beyond notebook and Python API use.

## Current Donor Dependencies

`onto-canon6` still depends on donor material from `onto-canon5` for:

1. detailed successor ADR source records;
2. first-slice planning history;
3. donor validation profiles;
4. donor ontology packs.

This is acceptable for bootstrap, but it should shrink over time.

The local strategic summary now lives in `docs/SUCCESSOR_CHARTER.md`, so the
repo no longer depends on donor docs for the basic explanation of why the
successor exists and what it is trying to preserve.

## Current Architectural Guardrails

The current direction is:

1. capability-preserving refactor, not kernel-only restart;
2. explicit subsystem boundaries;
3. packs separate from profiles;
4. domain packages outside core;
5. thin-slice proof before broader expansion.

The current locked strategic decisions are:

1. the first regained user-visible capability is governed review of candidate
   assertions;
2. live extraction evaluation is now explicit and the next phase is the first
   operational surface;
3. text-derived candidate assertions should carry first-class evidence spans
   and may also carry an optional natural-language gloss;
4. any LLM-backed extraction path must route through `llm_client` with
   goal-oriented prompts and schema-enforced structured output;
5. DoDAF is deferred and treated as a later exemplar domain pack;
6. mixed-mode routing and proposal acceptance policy must stay configurable.

The authoritative phase exit criteria and remaining explicit unknowns now live
in `docs/plans/0001_successor_roadmap.md`.

## Current Risks

1. Detailed donor evidence still lives partly in `onto-canon5`.
2. `onto-canon6` now proves a text-grounded import workflow structurally, but
   it still exposes that workflow mainly through notebooks and Python APIs.
3. The extraction boundary now has a real live benchmark slice, but the
   benchmark corpus is still small and not yet calibrated for broader claims.

## Immediate Next Step

Start Phase 6 with one narrow operational proof that makes the existing
workflow usable without direct Python calls:

1. add a thin CLI over extraction, review, proposal, and overlay actions;
2. keep business logic in the existing services rather than in CLI handlers;
3. prove the end-to-end workflow through CLI tests plus one notebook or shell
   transcript.
