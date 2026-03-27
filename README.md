# onto-canon6

`onto-canon6` is the successor bootstrap for the `onto-canon` lineage and the
current governed-assertion middleware for the ecosystem.

Its core job is to take candidate assertions from text or external producers,
keep provenance and review in the loop, and only then promote durable graph
state for downstream consumers.

Phases 0-15 completed the bootstrap roadmap, not the full successor-parity
goal. The full long-term capability vision remains authoritative in
`docs/plans/0005_v1_capability_parity_matrix.md`. Post-bootstrap work is now
sequenced around the active bottlenecks rather than broad phase expansion:

1. extraction quality and evaluation hardening;
2. reproducibility / bootstrap independence from donor repos and hidden setup;
3. consumer adoption of the proved outputs.

This is sequencing, not retreat. Deferred capabilities remain part of the
successor vision and must stay architecturally protected even when they are not
the current implementation frontier.

## What This Repo Owns

The durable core is:

- ontology runtime contracts, packs, profiles, and policy semantics
- reviewable candidate assertion and ontology-proposal state
- provenance-aware submissions with source text, claim text, and evidence spans
- overlay application for accepted ontology additions
- promotion into durable graph assertions
- stable identity, alias membership, and external-reference state
- semantic canonicalization and recanonicalization over promoted graph state
- extension-local epistemic reporting over promoted assertions
- governed export surfaces for downstream consumers

The producer side is intentionally replaceable:

- raw-text extraction through `llm_client`
- progressive extraction
- WhyGame, research_v3, and other import adapters

## Current Maturity

The repo is beyond pure design/bootstrap work. It has:

1. a maintained local test surface;
2. two real non-fixture runs (PSYOP Stage 1 and Shield AI WhyGame);
3. a proved E2E text -> review -> promotion path;
4. proved downstream artifact exports and consumer-facing adapter slices.

Current emphasis is not "recover every capability now." It is "keep the full
vision visible while making the proved workflow stronger and more usable."

## Canonical Workflow

The canonical journey today is:

1. ingest candidate assertions from raw text or an adapter;
2. validate against the active profile and proposal/overlay rules;
3. preserve provenance and evidence spans;
4. review candidates explicitly;
5. promote accepted candidates into durable graph state;
6. export governed outputs for downstream consumers.

The canonical notebook for that path is:

- `notebooks/00_master_governed_text_to_reviewed_assertions.ipynb`

## Canonical Proof Artifacts

The highest-signal local proof artifacts today are:

- `var/e2e_test_2026_03_25/review_combined.sqlite3`
  first complete text -> review -> promotion proof
- `var/gap9_dodaf_test/review.sqlite3`
  second-pack composability proof
- `var/real_runs/2026-03-18_research_agent_shield_ai_whygame/`
  first real adapter-facing WhyGame proof

These are more important than the broader historical run debris under `var/`.

## Setup Expectations

The supported local setup today is:

1. install repo dev dependencies into your active interpreter:
   `make dev-setup`
2. ensure the donor repos are available as siblings of this repo:
   - `../onto-canon5` for donor profiles and ontology packs
   - `../onto-canon` for `data/sumo_plus.db`
   - `../research_v3` if you want the research_v3 portion of the smoke path
3. if you are not using this repo's own `.venv`, pass `PYTHON=...` explicitly to
   `make` targets

The current bootstrap is not yet fully self-contained. The donor-asset
assumptions are explicit here so the proved workflow is reproducible rather than
hidden.

## Canonical Smoke Path

The canonical smoke path is a no-LLM end-to-end verification over the proved
local artifacts. It exercises:

1. promoted assertions -> identity auto-resolution -> Digimon export
2. research_v3 graph -> import -> review pipeline
3. promoted assertions -> Foundation IR export

Run it with:

```bash
make smoke
```

If your interpreter is not the repo-local `.venv`, run:

```bash
make smoke PYTHON=/path/to/python
```

The smoke path uses:

- `scripts/e2e_integration_test.py`
- `var/e2e_test_2026_03_25/review_combined.sqlite3`

It does not make LLM calls. If `../research_v3/output` is not available, the
research_v3 portion is skipped and the rest of the smoke path still runs.

The governing architectural rationale lives in the local successor charter and
the adopted ADR set.

High-signal reading order:

- `docs/SUCCESSOR_CHARTER.md`
- `docs/STATUS.md`
- `docs/plans/0005_v1_capability_parity_matrix.md`
- `docs/plans/0020_vision_gap_closure.md`
- `docs/plans/0001_successor_roadmap.md` (historical bootstrap baseline)
- `docs/plans/0013_llm_observability_and_prompt_eval_adoption.md`
- `docs/plans/0014_extraction_quality_baseline.md`
- `docs/plans/0019_chunk_level_transfer_evaluation.md`
- `docs/AUDIT_2026_03_26.md`
- `docs/EXTRACTION_EXPERIMENT_RUNBOOK.md`
- `notebooks/README.md`
- `notebooks/notebook_registry.yaml`
- `notebooks/00_master_governed_text_to_reviewed_assertions.ipynb`

Detailed dated run history now lives under `docs/runs/`. Auxiliary proof and
planning notebooks stay cataloged in `notebooks/README.md` and
`notebooks/notebook_registry.yaml` rather than being repeated here.

## Local Evaluation Dependency

Ancestor-aware evaluation and progressive extraction use the donor
`sumo_plus.db` by default via `../onto-canon/data/sumo_plus.db`.

An optional local copy may exist under `data/sumo_plus.db`, but that is
operator convenience rather than the canonical repo default.

## Current Scope

Phases 0-15 are complete. The repo now proves:

1. model ontology pack references and ontology policy explicitly
2. load real donor profiles and ontology packs from `onto-canon5`
3. make unknown-item handling deterministic and inspectable
4. validate one assertion payload against donor rules locally
5. persist reviewable candidate assertions and ontology proposals
6. review candidates through explicit accept/reject state transitions
7. persist optional source text, optional claim text, and exact evidence spans
   alongside candidate assertions
8. apply accepted ontology proposals into explicit local overlays
9. expose a small query/report surface over candidate, proposal, and overlay state
10. extract candidate assertions from raw text through `llm_client` without
    bypassing the review, proposal, or overlay workflow
11. evaluate live extraction quality without collapsing support,
    structural validity, and exact preferred-form agreement into one score,
    while logging prompt provenance and shared experiment records
12. operate the proved workflow through a thin CLI instead of direct Python
    calls
13. keep the main user-visible workflow represented by one canonical journey
    notebook with explicit phase contracts outside the notebook
14. prove a second local ontology pack can use the same runtime, review,
    overlay, and CLI surfaces without core branching
15. recover a narrow artifact-lineage slice with explicit source, derived, and
    analysis artifacts linked to candidate assertions
16. recover a narrow extension-local epistemic slice with confidence and
    supersession over accepted candidate assertions
17. export one governed bundle through the CLI-backed workflow so the
    successor ends in a real downstream artifact
18. promote accepted candidates into deterministic durable graph assertions
    and inspect promoted graph state through a thin CLI-backed report surface
19. create stable identities over promoted entities, attach alias membership,
    and persist explicit attached or unresolved external-reference state
20. canonicalize promoted assertion predicates and roles through pack-declared
    aliases and explicit recanonicalization events instead of a hidden runtime
    mapping layer
21. broaden epistemics over promoted assertions through explicit weakened /
    retracted dispositions plus derived corroboration and tension reporting
22. keep temporal/inference recovery explicitly deferred rather than silently
    implying it already exists

Not in scope yet:

- broader live benchmark coverage and calibration beyond the first local slice
- the broader v1 concept/belief graph and system-belief layer beyond the first
  promoted-assertion slice
- broader identity recovery beyond the first promoted-entity identity slice
- broader producer-side semantic adapters beyond the first pack-driven
  canonicalization replacement slice
- domain-specific query helpers
- richer external producer integrations beyond the proved research_v3 and
  DIGIMON bridges
- broader MCP surface expansion
- consumer-side adoption of the proved DIGIMON and research_v3 integrations
- temporal/inference recovery beyond the explicit Phase 15 deferral

## Layout

```text
src/onto_canon6/
  adapters/
  artifacts/
  core/
  extensions/
  ontology_runtime/
  pipeline/
  domain_packs/
  surfaces/
tests/
docs/adr/
config/
```

## Bootstrap Rule

If the next change cannot be justified against the adopted ADR set, it should
not land as casual repo drift.
