# ADR-0004: Keep text-derived candidate assertions grounded in source evidence and route LLM work through llm_client

Status: Accepted
Note: ADR-0017 (2026-03-19) modifies this ADR — validation is now annotation, not gate. See ADR-0017 for details.
Date: 2026-03-17

## Context

The next planned `onto-canon6` slice is now clearer than the earlier phrase
"external consumer integration" suggested.

The intended direction is:

1. raw text or another source artifact is the input;
2. an upstream extractor proposes ontology-shaped candidate assertions;
3. those candidate assertions enter the same review, proposal, and overlay
   flow already proved locally.

Two ambiguities needed to be resolved explicitly.

The first ambiguity was conceptual:

1. candidate assertions are not the ontology itself;
2. candidate assertions are not final accepted facts;
3. candidate assertions must stay grounded in the source text or artifact that
   supported them.

The second ambiguity was prompt and extraction governance:

1. if an LLM is used to derive candidate assertions from raw text, it should
   route through the shared `llm_client` boundary rather than direct provider
   SDK calls;
2. prompt guidance should follow the project rule of "goals over rules";
3. the "no examples without approval" rule should not be misread as forbidding
   an explicit structured output schema.

## Decision

`onto-canon6` adopts the following rules for text-derived candidate
assertions.

### 1. Candidate assertions remain reviewable proposals

Text-derived assertions enter the system as candidate assertions.

That means:

1. they are not auto-approved facts;
2. they remain subject to ontology validation, candidate review, proposal
   review, and overlay application policy;
3. the current review-first posture is preserved even when an LLM produced the
   initial candidate.

### 2. Source text remains primary; assertions are grounded by evidence

Raw text or another source artifact remains the primary input and reference
point.

Text-derived candidate assertions should carry, as first-class data:

1. source artifact provenance;
2. one or more evidence spans grounding the assertion in the source;
3. an optional natural-language gloss or claim text for review ergonomics.

Evidence spans exist to support:

1. human review;
2. better evaluation of whether an assertion is supported;
3. inspection when an assertion depends on multiple non-adjacent spans.

### 3. Any LLM-backed extraction path uses llm_client

If an LLM is used to derive candidate assertions or evidence spans from raw
text, the call must route through `llm_client`.

That includes:

1. model selection;
2. structured output;
3. observability and tracing;
4. retry and policy behavior.

Direct provider SDK calls should not be introduced into `onto-canon6`.

### 4. Prompts are goal-oriented; schema remains part of the contract

Prompt design for text-derived extraction should follow the local rule:

1. tell the model what is being built and why;
2. avoid long brittle rule lists that invite gaming;
3. keep prompt templates in `prompts/` and load them through `llm_client`.

The "no examples without approval" rule means:

1. no few-shot or illustrative worked examples should be added casually;
2. the explicit structured output schema is still allowed and expected;
3. the schema is part of the input/output contract, not the kind of example
   being prohibited.

### 5. Evidence grounding should be checked deterministically

The extractor may propose evidence spans, but the system should verify them
against the source text rather than treating them as trusted without checking.

## Consequences

### Positive

- The next integration phase now has a much clearer target.
- Candidate assertions remain auditable instead of becoming detached from the
  text that justified them.
- Prompt policy is now aligned with the project-wide `llm_client` and
  prompt-as-data rules.
- Evaluation can reason about support from specific spans rather than only
  abstract assertion reasonableness.

### Negative

- The next phase is slightly larger because it now needs first-class evidence
  modeling rather than only a generic provenance blob.
- Span verification and evidence modeling introduce more implementation detail
  than a bare importer would.

### Neutral

- This ADR does not require the first producer to solve every future evidence
  case on day one.
- It does require the first producer to treat evidence grounding as a core part
  of the contract rather than as optional metadata.
