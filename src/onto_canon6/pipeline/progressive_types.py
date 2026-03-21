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
