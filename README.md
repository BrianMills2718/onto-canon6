# onto-canon6

`onto-canon6` is the successor bootstrap for the `onto-canon` lineage.

This repo starts from the first proved slice instead of trying to port an
entire prior runtime. The current scope is intentionally narrow:

- ontology runtime contracts
- unknown-item policy semantics
- donor pack/profile loading
- local assertion validation against donor rules
- persisted candidate/proposal review state
- candidate-level review state transitions
- provenance-aware candidate submissions
- typed text-grounded import contracts with source text, claim text, and
  evidence spans
- `llm_client`-backed raw-text extraction into candidate assertions via prompt
  templates and structured output
- live extraction evaluation that separates reasonableness, structural
  validation, and exact canonicalization fidelity
- explicit overlay application for accepted ontology proposals
- overlay-aware validation against local additions
- minimal report surface over persisted review and overlay state

The governing architectural rationale lives in the local successor charter and
the adopted ADR set.

Repo-local strategic and planning docs now live in:

- `docs/SUCCESSOR_CHARTER.md`
- `docs/STATUS.md`
- `docs/plans/0001_successor_roadmap.md`
- `notebooks/09_successor_long_term_plan.ipynb`

## Current Scope

Today this repo proves only one thin slice:

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
    structural validity, and exact preferred-form agreement into one score

Not in scope yet:

- broader live benchmark coverage and calibration beyond the first local slice
- epistemic extension
- domain-specific query helpers
- richer external producer integrations
- UI or MCP surfaces

## Layout

```text
src/onto_canon6/
  core/
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
