# onto-canon6 ADRs

This repo starts by adopting the successor ADR set developed in `onto-canon5`
during the restart review and planning phase.

## Accepted

1. [0001 - Adopt the onto-canon5 successor ADR set at bootstrap](0001-adopt-the-onto-canon5-successor-adr-set-at-bootstrap.md)
2. [0002 - Set the next proving slice and keep mixed-mode governance configurable](0002-set-the-next-proving-slice-and-configurable-mixed-mode-policy.md)
3. [0003 - Prefer configurable policies and narrow extension seams over a general plugin framework](0003-prefer-configurable-policies-and-narrow-extension-seams-over-a-general-plugin-framework.md)
4. [0004 - Keep text-derived candidate assertions grounded in source evidence and route LLM work through llm_client](0004-keep-text-derived-candidate-assertions-grounded-in-source-evidence-and-route-llm-work-through-llm_client.md)
5. [0005 - Separate live extraction reasonableness from structural validation and canonicalization fidelity](0005-separate-live-extraction-reasonableness-from-structural-validation-and-canonicalization-fidelity.md)
6. [0006 - Prefer CLI as the first operational surface before MCP or UI](0006-prefer-cli-as-the-first-operational-surface-before-mcp-or-ui.md)
7. [0007 - Adopt canonical journey notebooks with an explicit registry](0007-adopt-canonical-journey-notebooks-with-an-explicit-registry.md)
8. [0008 - Start artifact lineage with a narrow three-kind model and candidate-centered links](0008-start-artifact-lineage-with-a-narrow-three-kind-model-and-candidate-centered-links.md)
9. [0009 - Start epistemic extension with confidence and supersession over accepted candidates](0009-start-epistemic-extension-with-confidence-and-supersession-over-accepted-candidates.md)
10. [0010 - Choose CLI-driven governed bundle export as the first product-facing workflow](0010-choose-cli-driven-governed-bundle-export-as-the-first-product-facing-workflow.md)
11. [0011 - Treat Phase 10 as bootstrap completion and track v1 capability parity explicitly](0011-treat-phase-10-as-bootstrap-completion-and-track-v1-capability-parity-explicitly.md)
12. [0012 - Start canonical graph recovery with explicit promotion from accepted candidates](0012-start-canonical-graph-recovery-with-explicit-promotion-from-accepted-candidates.md)
13. [0013 - Start stable identity with promoted-entity identities, alias membership, and explicit external reference state](0013-start-stable-identity-with-promoted-entity-identities-alias-membership-and-explicit-external-reference-state.md)
14. [0014 - Replace the v1 semantic stack with pack-driven canonicalization and explicit recanonicalization](0014-replace-the-v1-semantic-stack-with-pack-driven-canonicalization-and-explicit-recanonicalization.md)
15. [0015 - Recover Phase 14 through a thin MCP surface and a WhyGame relationship adapter](0015-recover-phase-14-through-a-thin-mcp-surface-and-a-whygame-relationship-adapter.md)
16. [0016 - Recover Phase 15 through extension-local promoted-assertion dispositions and derived corroboration](0016-recover-phase-15-through-extension-local-promoted-assertion-dispositions-and-derived-corroboration.md)
17. [0017 - Adopt permissive extraction with downstream governance](0017-adopt-permissive-extraction-with-downstream-governance.md)
18. [0018 - Adopt multi-pass progressive disclosure extraction](0018-adopt-multi-pass-progressive-disclosure-extraction.md)
19. [0019 - Adopt ancestor-aware evaluation with growing acceptable sets](0019-adopt-ancestor-aware-evaluation-with-growing-acceptable-sets.md)
20. [0020 - Align Phase A prompt-eval exact scoring to extraction-boundary semantics](0020-align-phase-a-prompt-eval-exact-scoring-to-extraction-boundary-semantics.md)
21. [0021 - Keep chunk extraction directly grounded and defer document-level synthesis](0021-keep-chunk-extraction-directly-grounded-and-defer-document-level-synthesis.md)
22. [0022 - Classify post-bootstrap extraction work as an explicit R&D workstream](0022-classify-post-bootstrap-extraction-work-as-an-explicit-r-and-d-workstream.md)
23. [0023 - Require a chunk-level transfer evaluation slice before live prompt promotion](0023-require-a-chunk-level-transfer-evaluation-slice-before-live-prompt-promotion.md)

## Notes

1. The detailed source ADRs currently live in `../onto-canon5/docs/adr/`.
2. As `onto-canon6` grows, repo-local ADRs should be added here rather than
   pushing new architecture decisions back into the donor repo.
3. `../SUCCESSOR_CHARTER.md` is the local strategic summary that explains why
   this repo exists, what it borrows from the lineage, and how to read the
   current plan.
4. `../plans/0005_v1_capability_parity_matrix.md` is the explicit ledger for
   what happened to each major `onto-canon` capability after the current
   Phase 0-15 successor-core bootstrap.
5. ADRs 0017-0023 describe the active post-bootstrap extraction R&D
   workstream. They are real repo-local decisions, but they do not silently
   replace the canonical successor-core roadmap.
