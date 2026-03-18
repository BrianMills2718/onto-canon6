# Phase 8 Artifact Lineage Shape

This note makes the Phase 8 slice explicit before implementation begins.

## Goal

Recover artifact-backed provenance from `onto-canon` v1 without rebuilding a
large artifact subsystem or pulling artifact logic into core runtime modules.

## Chosen First Slice

Artifact kinds:

1. `source`
2. `derived_dataset`
3. `analysis_result`

Link target:

1. `candidate_assertion` only in the first slice

Deduplication:

1. none, or exact-only through an optional fingerprint field

## Concrete Example

One small end-to-end lineage chain should look like:

1. source artifact:
   - `campaign_tweets.parquet`
2. derived dataset:
   - `retweet_graph.graphml`
3. analysis result:
   - `centrality_scores.json`
4. candidate assertion:
   - `Account X is central in the campaign network`
5. candidate-to-artifact links:
   - `quoted_from -> campaign_tweets.parquet`
   - `supported_by_analysis -> centrality_scores.json`

The lineage report should then show:

1. the candidate assertion;
2. the raw source artifact;
3. the derived dataset and analysis result, if present;
4. the review state that still governs whether the candidate becomes accepted.

## Why This Slice

This is the smallest shape that proves the real donor capability:

1. some claims are supported directly by text;
2. some claims are supported by computation over transformed data;
3. both support paths should be explicit and inspectable.

## What We Are Not Building Yet

Not part of the first slice:

1. full artifact taxonomy from v1;
2. artifact links copied onto accepted assertions;
3. aggressive deduplication or semantic merge logic;
4. blob storage, scheduling, or generalized research-platform artifact
   management.

## Path To The Fuller Version

The fuller version can grow in stages without changing the center of gravity:

1. add artifact kinds when real workflows need them:
   - `graph`
   - `query_result`
   - `embedding_index`
   - `model`
2. add additional link subjects when traversal becomes a real usability problem:
   - accepted-assertion projections
   - extension-local records such as epistemic judgments
3. add stronger registry ergonomics when repetition justifies them:
   - exact fingerprint reuse
   - lineage traversal helpers
   - richer report surfaces

The important constraint is unchanged: the artifact subsystem stays bounded and
does not become a new runtime hub.

## Acceptance Shape

Phase 8 should count as successful if:

1. artifacts are persisted as first-class records with explicit kinds;
2. candidate assertions can link to both raw-source and analysis artifacts;
3. the report surface can show the lineage chain without hidden metadata;
4. the notebook proof demonstrates a claim supported by an analysis artifact,
   not only quoted text.
