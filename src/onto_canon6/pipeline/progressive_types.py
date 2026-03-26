"""Shared data models for the progressive disclosure extraction pipeline.

These Pydantic models define the contract for each extraction pass in
the multi-pass progressive disclosure pipeline (Plan 0018).  Pass 1
produces coarse-grained entity/relationship triples seeded by ~50
top-level SUMO types.  Later passes (Pass 2, Pass 3) will refine
predicates and entity types using narrowed subtree information.

All models use ``frozen=True`` and ``extra="forbid"`` so downstream
consumers can trust the schema boundary.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class Pass1Entity(BaseModel):
    """An entity extracted in Pass 1 with a coarse SUMO type.

    The ``coarse_type`` should ideally come from the ~50 top-level SUMO
    type list, but the pipeline is permissive: the LLM may pick
    something reasonable that is not in the curated list, and that is
    accepted rather than discarded.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    name: str = Field(min_length=1)
    coarse_type: str = Field(
        min_length=1,
        description="Coarse SUMO type, ideally from the top-level list.",
    )
    context: str = Field(
        default="",
        description="Brief description of the entity drawn from the source text.",
    )


class Pass1Triple(BaseModel):
    """A relationship triple extracted in Pass 1.

    Links two entities via a raw relationship verb with an optional
    evidence span from the source text.  The ``confidence`` field is
    the LLM's self-assessed confidence and should be treated as
    advisory, not authoritative.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    entity_a: Pass1Entity
    entity_b: Pass1Entity
    relationship_verb: str = Field(
        min_length=1,
        description="Raw verb or action phrase describing the relationship.",
    )
    evidence_span: str = Field(
        default="",
        description="Source text excerpt supporting this triple.",
    )
    confidence: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="LLM self-assessed confidence (0-1).",
    )
    claim_level: str = Field(
        default="instance",
        description=(
            "Whether this triple is about a specific instance/event "
            "or about a general type/category. 'type' or 'instance'."
        ),
    )


class Pass1Result(BaseModel):
    """Complete result of a Pass 1 extraction run.

    Contains the extracted triples, a deduplicated entity list, and
    provenance metadata (source text hash, model, cost, trace ID) for
    downstream traceability.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    triples: list[Pass1Triple]
    entities: list[Pass1Entity]
    source_text_hash: str = Field(
        min_length=1,
        description="SHA-256 hash of the input text for traceability.",
    )
    model: str = Field(
        min_length=1,
        description="The LLM model used for extraction.",
    )
    cost: float = Field(
        default=0.0,
        ge=0.0,
        description="Total cost in USD for the LLM call(s).",
    )
    trace_id: str = Field(
        min_length=1,
        description="Trace ID used for the LLM call.",
    )


class Pass2MappedAssertion(BaseModel):
    """A triple with its predicate mapping from Pass 2.

    Links a Pass 1 triple to a specific predicate sense from the Predicate
    Canon, including the PropBank sense ID, SUMO process type, role mappings,
    and how the mapping was determined (single-sense early exit vs. LLM
    disambiguation).
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    triple: Pass1Triple
    predicate_id: str = Field(
        min_length=1,
        description="Predicate Canon name, e.g. 'abandon_leave_behind'.",
    )
    propbank_sense_id: str = Field(
        min_length=1,
        description="PropBank sense ID, e.g. 'abandon-01'.",
    )
    process_type: str = Field(
        description="SUMO process type, e.g. 'Leaving'. Empty if unmapped.",
    )
    mapped_roles: dict[str, str] = Field(
        description=(
            "Mapping from arg position to entity name, "
            "e.g. {'ARG0': 'CIA', 'ARG1': 'agents'}."
        ),
    )
    disambiguation_method: str = Field(
        description="How the predicate was selected: 'single_sense', 'llm_pick', or 'unresolved'.",
    )
    mapping_confidence: float = Field(
        ge=0.0,
        le=1.0,
        description="Confidence in the predicate mapping (0-1).",
    )


class Pass2Result(BaseModel):
    """Complete result of Pass 2 predicate mapping.

    Contains successfully mapped assertions, unresolved triples (no predicate
    found), provenance back to the Pass 1 result, and counts for each
    disambiguation path (single-sense early exit, LLM disambiguation,
    unresolved).
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    mapped: list[Pass2MappedAssertion] = Field(
        description="Triples successfully mapped to predicates.",
    )
    unresolved: list[Pass1Triple] = Field(
        description="Triples with no predicate match (stored permissively).",
    )
    source_pass1: Pass1Result = Field(
        description="The Pass 1 result this mapping was derived from.",
    )
    model: str = Field(
        min_length=1,
        description="The LLM model used for disambiguation calls.",
    )
    cost: float = Field(
        default=0.0,
        ge=0.0,
        description="Total cost in USD for LLM disambiguation calls.",
    )
    trace_id: str = Field(
        min_length=1,
        description="Trace ID for observability.",
    )
    single_sense_count: int = Field(
        default=0,
        ge=0,
        description="How many triples used the single-sense early exit path.",
    )
    llm_disambiguated_count: int = Field(
        default=0,
        ge=0,
        description="How many triples required LLM disambiguation.",
    )
    unresolved_count: int = Field(
        default=0,
        ge=0,
        description="How many triples had no predicate match.",
    )


class EntityRefinement(BaseModel):
    """Refined type for one entity from Pass 3.

    Records the result of narrowing an entity's coarse Pass 1 type using
    the role constraint from the predicate's argument slot and the SUMO
    subtree under the coarse type.  The ``refinement_method`` field
    indicates which code path produced the result:

    - ``leaf_early_exit``: the coarse type was already a SUMO leaf, so no
      LLM call was needed.
    - ``subtree_pick``: the LLM picked from a narrowed candidate list.
    - ``no_constraint``: no meaningful role constraint existed (constraint
      was ``Entity`` or absent), so the full coarse-type subtree was shown.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    entity_name: str = Field(min_length=1)
    coarse_type: str = Field(
        min_length=1,
        description="The coarse SUMO type assigned in Pass 1.",
    )
    refined_type: str = Field(
        min_length=1,
        description="The refined SUMO type from Pass 3 (more specific or same).",
    )
    role_constraint: str = Field(
        description="The type constraint from the predicate role slot, or empty if none.",
    )
    refinement_method: str = Field(
        description="How the refined type was determined: 'subtree_pick', 'leaf_early_exit', or 'no_constraint'.",
    )
    candidate_count: int = Field(
        ge=0,
        description="How many candidate types were shown to the LLM (0 for early exit).",
    )


class Pass3TypedAssertion(BaseModel):
    """Fully typed assertion from Pass 3.

    Combines a Pass 2 mapped assertion with entity refinement results for
    each entity that fills a role in the predicate's argument schema.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    assertion: Pass2MappedAssertion
    entity_refinements: list[EntityRefinement]


class Pass3Result(BaseModel):
    """Complete result of Pass 3 entity refinement.

    Contains the typed assertions, a provenance reference back to the
    Pass 2 result, and diagnostic counts for each refinement code path
    (leaf early exit, subtree pick via LLM, no constraint).
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    typed_assertions: list[Pass3TypedAssertion]
    source_pass2: Pass2Result = Field(
        description="The Pass 2 result this refinement was derived from.",
    )
    model: str = Field(
        min_length=1,
        description="The LLM model used for refinement calls.",
    )
    cost: float = Field(
        default=0.0,
        ge=0.0,
        description="Total cost in USD for LLM refinement calls.",
    )
    trace_id: str = Field(
        min_length=1,
        description="Trace ID for observability.",
    )
    leaf_early_exit_count: int = Field(
        default=0,
        ge=0,
        description="How many entities were already SUMO leaves (no LLM call).",
    )
    subtree_pick_count: int = Field(
        default=0,
        ge=0,
        description="How many entities required an LLM subtree pick.",
    )
    no_constraint_count: int = Field(
        default=0,
        ge=0,
        description="How many entities had no meaningful role constraint.",
    )


class ProgressiveExtractionReport(BaseModel):
    """Full report from a progressive extraction run (all three passes).

    Aggregates the Pass 1, Pass 2, and Pass 3 results together with
    total cost, provenance metadata, and summary statistics for the
    entire pipeline run.  Produced by :func:`run_progressive_extraction`.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    pass1: Pass1Result
    pass2: Pass2Result
    pass3: Pass3Result
    total_cost: float = Field(
        ge=0.0,
        description="Aggregate cost in USD across all three passes.",
    )
    trace_id: str = Field(
        min_length=1,
        description="Trace ID shared across all passes for observability.",
    )
    model: str = Field(
        min_length=1,
        description="The LLM model used (same for all passes).",
    )
    triples_extracted: int = Field(
        ge=0,
        description="Number of triples extracted in Pass 1.",
    )
    predicates_mapped: int = Field(
        ge=0,
        description="Number of triples successfully mapped to predicates in Pass 2.",
    )
    predicates_unresolved: int = Field(
        ge=0,
        description="Number of triples with no predicate match in Pass 2.",
    )
    entities_refined: int = Field(
        ge=0,
        description="Number of unique entities refined in Pass 3.",
    )
    single_sense_early_exits: int = Field(
        ge=0,
        description="Pass 2 triples resolved via single-sense deterministic mapping.",
    )
    leaf_type_early_exits: int = Field(
        ge=0,
        description="Pass 3 entities skipped because their coarse type was already a SUMO leaf.",
    )
