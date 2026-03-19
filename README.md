# onto-canon6

`onto-canon6` is the successor bootstrap for the `onto-canon` lineage.

Phase 10 completed the bootstrap roadmap, not the full successor-parity goal.
The explicit parity ledger now lives in `docs/plans/0005_v1_capability_parity_matrix.md`.
The current strategic priority is to put the proved bounded core through at
least one real investigation or consumer workflow before reopening broad
parity-chasing or another roadmap extension.

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
- a thin operational CLI over extract, list, review, proposal, and overlay
  actions
- one canonical end-to-end journey notebook plus a machine-readable notebook
  registry and validator
- one local second-pack proof with `dodaf_minimal` strict and mixed profiles
- one narrow artifact-lineage recovery slice with candidate-centered support
  links and a typed lineage report
- one extension-local epistemic subsystem with candidate confidence /
  supersession plus promoted-assertion `weakened` / `retracted` dispositions
  and derived corroboration / tension reporting
- one first product-facing workflow that exports a CLI-driven governed bundle
  over accepted reviewed assertions
- one first canonical-graph recovery slice with explicit promotion from
  accepted candidates into durable promoted assertions and graph reports
- one first stable-identity slice with explicit alias membership and explicit
  attached or unresolved external-reference state over promoted entities
- one first semantic canonicalization slice that replaces the v1 hard semantic
  stack with pack-driven predicate/role canonicalization plus explicit
  recanonicalization over promoted graph state
- one thin FastMCP agent surface over the proved successor services
- one narrow WhyGame relationship adapter plus local `whygame_minimal` pack
  and strict profile

The governing architectural rationale lives in the local successor charter and
the adopted ADR set.

Repo-local strategic and planning docs now live in:

- `docs/SUCCESSOR_CHARTER.md`
- `docs/STATUS.md`
- `docs/plans/0001_successor_roadmap.md`
- `docs/plans/0005_v1_capability_parity_matrix.md`
- `notebooks/README.md`
- `notebooks/notebook_registry.yaml`
- `notebooks/00_master_governed_text_to_reviewed_assertions.ipynb`
- `notebooks/09_successor_long_term_plan.ipynb`
- `notebooks/11_future_phase_breakdown.ipynb`
- `notebooks/12_cli_surface.ipynb`
- `notebooks/13_dodaf_minimal_second_pack.ipynb`
- `notebooks/14_artifact_lineage_slice.ipynb`
- `notebooks/15_epistemic_extension_slice.ipynb`
- `notebooks/16_governed_bundle_workflow.ipynb`
- `notebooks/17_canonical_graph_recovery_slice.ipynb`
- `notebooks/18_stable_identity_slice.ipynb`
- `notebooks/19_semantic_canonicalization_slice.ipynb`
- `notebooks/20_whygame_mcp_slice.ipynb`
- `notebooks/21_phase15_epistemic_corroboration_slice.ipynb`

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
- richer external producer integrations
- broader MCP surface expansion
- DIGIMON recovery
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
