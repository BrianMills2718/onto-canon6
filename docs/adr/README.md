# onto-canon6 ADRs

This repo starts by adopting the successor ADR set developed in `onto-canon5`
during the restart review and planning phase.

## Accepted

1. [0001 - Adopt the onto-canon5 successor ADR set at bootstrap](0001-adopt-the-onto-canon5-successor-adr-set-at-bootstrap.md)
2. [0002 - Set the next proving slice and keep mixed-mode governance configurable](0002-set-the-next-proving-slice-and-configurable-mixed-mode-policy.md)
3. [0003 - Prefer configurable policies and narrow extension seams over a general plugin framework](0003-prefer-configurable-policies-and-narrow-extension-seams-over-a-general-plugin-framework.md)
4. [0004 - Keep text-derived candidate assertions grounded in source evidence and route LLM work through llm_client](0004-keep-text-derived-candidate-assertions-grounded-in-source-evidence-and-route-llm-work-through-llm_client.md)
5. [0005 - Separate live extraction reasonableness from structural validation and canonicalization fidelity](0005-separate-live-extraction-reasonableness-from-structural-validation-and-canonicalization-fidelity.md)

## Notes

1. The detailed source ADRs currently live in `../onto-canon5/docs/adr/`.
2. As `onto-canon6` grows, repo-local ADRs should be added here rather than
   pushing new architecture decisions back into the donor repo.
3. `../SUCCESSOR_CHARTER.md` is the local strategic summary that explains why
   this repo exists, what it borrows from the lineage, and how to read the
   current plan.
