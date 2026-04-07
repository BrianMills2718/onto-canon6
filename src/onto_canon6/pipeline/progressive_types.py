"""Shared data models for the progressive disclosure extraction pipeline.

These Pydantic models define the contract for each extraction pass in
the multi-pass progressive disclosure pipeline (Plan 0018).  Pass 1
produces coarse-grained entity/relationship event frames seeded by ~50
top-level SUMO types.  Later passes (Pass 2, Pass 3) will refine
predicates and entity types using narrowed subtree information.  Pass 4
normalizes entity names: resolving anaphors, dropping descriptive phrases,
and merging near-duplicates to canonical forms.

All models use ``frozen=True`` and ``extra="forbid"`` so downstream
consumers can trust the schema boundary.
"""

from __future__ import annotations

from typing import Literal

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


class Pass1Participant(BaseModel):
    """One participant in a Pass 1 event with their semantic proto-role.

    Each participant carries an entity and the semantic role that entity
    plays in the event (Agent, Theme, Recipient, etc.).  This maps
    naturally to PropBank and FrameNet argument structures which are
    fundamentally n-ary.

    The ``resolution_status`` and ``resolved_from`` fields are populated
    by Pass 4 normalization.  Before Pass 4 runs they default to
    ``"canonical"`` and ``None`` respectively.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    proto_role: str = Field(
        description=(
            "Semantic role of this participant. One of: "
            "Agent (performs the action willfully), "
            "Theme (undergoes or is affected by the action), "
            "Recipient (receives or benefits from the action), "
            "Instrument (tool or means used), "
            "Location (where the action happens), "
            "Source (origin of movement or information), "
            "Experiencer (perceives or feels something), "
            "Cause (non-volitional cause or reason), "
            "Attribute (property being described), "
            "Unspecified (role not clearly categorized)."
        ),
    )
    entity: Pass1Entity
    resolution_status: Literal["canonical", "resolved", "dropped", "uncertain"] = Field(
        default="canonical",
        description=(
            "Pass 4 normalization outcome for this participant. "
            "'canonical' = already a proper name, no change needed. "
            "'resolved' = was an anaphor/alias, resolved to a canonical name. "
            "'dropped' = descriptive phrase or unresolvable anaphor, removed from event. "
            "'uncertain' = budget exhausted, kept as-is."
        ),
    )
    resolved_from: str | None = Field(
        default=None,
        description="Original entity name before Pass 4 resolution, or None if not resolved.",
    )


class Pass1Event(BaseModel):
    """An n-ary event frame extracted in Pass 1 with all participants.

    Unlike binary triples, an event frame captures all participants of a
    single action — agent, theme, recipient, instrument, etc. — in one
    structured record.  This maps naturally to PropBank and FrameNet frames
    which are fundamentally n-ary structures.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    relationship_verb: str = Field(
        min_length=1,
        description="Bare verb infinitive describing the core action (e.g. 'deploy', 'invest').",
    )
    participants: list[Pass1Participant] = Field(
        default_factory=list,
        description=(
            "All participants in this event with their semantic roles. "
            "Most events have 2–4 participants. Include all that are clearly "
            "supported by the text."
        ),
    )
    evidence_span: str = Field(
        default="",
        description="Short excerpt from the source text supporting this event.",
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
            "Whether this event is about a specific instance/event "
            "or a general type/category. 'type' or 'instance'."
        ),
    )


class Pass1Result(BaseModel):
    """Complete result of a Pass 1 extraction run.

    Contains the extracted events, a deduplicated entity list, and
    provenance metadata (source text hash, model, cost, trace ID) for
    downstream traceability.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    events: list[Pass1Event]
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
    """An event with its predicate mapping from Pass 2.

    Links a Pass 1 event to a specific predicate sense from the Predicate
    Canon, including the PropBank sense ID, SUMO process type, role mappings,
    and how the mapping was determined (single-sense early exit vs. LLM
    disambiguation).
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    event: Pass1Event
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

    Contains successfully mapped assertions, unresolved events (no predicate
    found), provenance back to the Pass 1 result, and counts for each
    disambiguation path (single-sense early exit, LLM disambiguation,
    unresolved).
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    mapped: list[Pass2MappedAssertion] = Field(
        description="Events successfully mapped to predicates.",
    )
    unresolved: list[Pass1Event] = Field(
        description="Events with no predicate match (stored permissively).",
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


class AnaphorResolution(BaseModel):
    """Resolution decision for one anaphor or descriptive-phrase entity.

    Produced by Pass 4 for every entity name flagged as an anaphor or
    non-entity descriptive phrase.  ``resolved_to`` is ``None`` when
    the entity should be dropped outright (no referent can be determined).
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    original_name: str = Field(
        description="Entity name as it appeared in the Pass 1 output.",
    )
    resolved_to: str | None = Field(
        description=(
            "Canonical entity name this anaphor resolves to, or None to drop. "
            "Must be an exact match to a canonical name in the run."
        ),
    )
    confidence: float = Field(
        ge=0.0,
        le=1.0,
        description="LLM self-assessed confidence in the resolution decision (0-1).",
    )
    evidence: str = Field(
        description="One-sentence justification for the resolution decision.",
    )


class AliasPair(BaseModel):
    """A text-declared alias relationship between two entity name forms.

    Extracted from parenthetical patterns in source text ("Full Name (ABBREV)").
    No LLM verification is required — text-declared equivalences are accepted
    deterministically.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    short_form: str = Field(description="The abbreviated or acronym form.")
    long_form: str = Field(description="The expanded or full form (canonical).")
    source_pattern: str = Field(
        description="The raw text span that contained the alias declaration."
    )


class MergeDecision(BaseModel):
    """Decision to merge near-duplicate entity names into one canonical form.

    Produced by Pass 4 when two or more entity names refer to the same
    real-world entity.  All ``aliases`` are rewritten to ``canonical_name``
    in the event stream.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    canonical_name: str = Field(
        description="The authoritative name to use for this entity going forward.",
    )
    aliases: list[str] = Field(
        description="All names that should be rewritten to canonical_name.",
    )
    confidence: float = Field(
        ge=0.0,
        le=1.0,
        description="LLM self-assessed confidence that these names refer to the same entity (0-1).",
    )
    evidence: str = Field(
        description="One-sentence justification for the merge decision.",
    )


class Pass4NormalizationResult(BaseModel):
    """Complete result of Pass 4 entity normalization.

    Contains all anaphor resolutions, merge decisions, the consolidated
    normalization map (used to rewrite events), and provenance metadata.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    anaphor_resolutions: list[AnaphorResolution] = Field(
        description="Resolution decisions for flagged anaphors and descriptive phrases.",
    )
    merge_decisions: list[MergeDecision] = Field(
        description="Merge decisions for near-duplicate entity name pairs.",
    )
    alias_pairs: list[AliasPair] = Field(
        default_factory=list,
        description=(
            "Alias pairs extracted deterministically from source text parenthetical patterns. "
            "Short forms are rewritten to long forms in the normalization_map without LLM verification."
        ),
    )
    normalization_map: dict[str, str | None] = Field(
        description=(
            "Consolidated name → canonical mapping. "
            "None value means drop the participant. "
            "Keys not present in this map are kept unchanged."
        ),
    )
    cost_usd: float = Field(
        ge=0.0,
        description="Total LLM cost in USD for all Pass 4 resolution calls.",
    )
    model: str = Field(
        min_length=1,
        description="The LLM model used for normalization calls.",
    )


class ProgressiveExtractionReport(BaseModel):
    """Full report from a progressive extraction run (all four passes).

    Aggregates the Pass 1, Pass 2, Pass 3, and optional Pass 4 results
    together with total cost, provenance metadata, and summary statistics
    for the entire pipeline run.  Produced by
    :func:`run_progressive_extraction`.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    pass1: Pass1Result
    pass2: Pass2Result
    pass3: Pass3Result
    pass4: Pass4NormalizationResult | None = Field(
        default=None,
        description=(
            "Pass 4 entity normalization result, or None if Pass 4 was not run "
            "(e.g. budget exhausted before normalization)."
        ),
    )
    total_cost: float = Field(
        ge=0.0,
        description="Aggregate cost in USD across all passes (1-4).",
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
