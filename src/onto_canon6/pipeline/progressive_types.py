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
        min_length=1,
        description="SUMO process type, e.g. 'Leaving'.",
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
