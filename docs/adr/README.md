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

## Notes

1. The detailed source ADRs currently live in `../onto-canon5/docs/adr/`.
2. As `onto-canon6` grows, repo-local ADRs should be added here rather than
   pushing new architecture decisions back into the donor repo.
3. `../SUCCESSOR_CHARTER.md` is the local strategic summary that explains why
   this repo exists, what it borrows from the lineage, and how to read the
   current plan.
