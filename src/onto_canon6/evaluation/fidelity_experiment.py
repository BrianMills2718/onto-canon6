"""Fidelity experiment infrastructure for SUMO type assignment accuracy.

Prepares experiment inputs that compare LLM type-picking accuracy across
three fidelity levels of SUMO type lists: top-level (~50 broad types),
mid-level (~30 subtypes per relevant branch), and full-subtree (all
descendants of the constraint type).

This module does NOT call any LLMs. It constructs the experiment inputs
(entity sets, type lists, prompt variables) and returns them ready for
``prompt_eval`` or manual execution.

Implements Plan 0017, Component 5 (baseline measurement infrastructure).
"""

from __future__ import annotations

from enum import Enum
from pathlib import Path
from typing import Sequence

from pydantic import BaseModel, ConfigDict, Field

from onto_canon6.evaluation.sumo_hierarchy import SUMOHierarchy


class FidelityLevel(str, Enum):
    """The three fidelity levels for SUMO type list seeding.

    Each level controls how many candidate types are presented to the LLM
    when asking it to classify an entity.
    """

    TOP_LEVEL = "top_level"
    MID_LEVEL = "mid_level"
    FULL_SUBTREE = "full_subtree"


class EntityFixture(BaseModel):
    """One entity to be typed in the fidelity experiment.

    Attributes
    ----------
    entity_name:
        Display name of the entity (e.g. "CIA", "V-BAT").
    entity_context:
        Optional short context string to help the LLM disambiguate.
    reference_type:
        The known-correct SUMO type for evaluation scoring.
    constraint_type:
        The SUMO branch root used for mid-level and full-subtree type
        list generation. Typically the nearest well-known ancestor of
        the reference type (e.g. "Organization" for org entities).
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    entity_name: str = Field(min_length=1)
    entity_context: str = ""
    reference_type: str = Field(min_length=1)
    constraint_type: str = Field(min_length=1)


class ExperimentItem(BaseModel):
    """One prepared experiment input: entity + fidelity level + type list + prompt vars.

    Ready to be rendered into a prompt template and sent to an LLM.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    entity_name: str = Field(min_length=1)
    entity_context: str = ""
    reference_type: str = Field(min_length=1)
    fidelity_level: FidelityLevel
    type_list: tuple[str, ...] = Field(min_length=1)
    prompt_variables: dict[str, str]


class ExperimentResult(BaseModel):
    """Scored result for one experiment item after LLM execution.

    This model is for downstream consumers that run the LLM and record
    the pick. The ``fidelity_experiment`` module itself does not populate
    this — it only prepares ``ExperimentItem`` inputs.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    entity_name: str = Field(min_length=1)
    fidelity_level: FidelityLevel
    pick: str = Field(min_length=1)
    reference_type: str = Field(min_length=1)
    ancestor_eval_score: float = Field(ge=0.0, le=1.0)
    exact_match: bool
    ancestor_match: bool
    specificity: float = Field(ge=0.0)


class PreparedExperiment(BaseModel):
    """Complete prepared experiment ready for execution.

    Contains all items across all requested fidelity levels for a given
    entity set. Serializable to JSON for CLI output or ``prompt_eval``
    consumption.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    entity_count: int = Field(ge=1)
    fidelity_levels: tuple[FidelityLevel, ...]
    items: tuple[ExperimentItem, ...]
    prompt_template: str = Field(min_length=1)


# ---------------------------------------------------------------------------
# Stable top-level type list (~50 types)
# ---------------------------------------------------------------------------
# Curated from SUMO's upper hierarchy. These are the broadest categories
# an LLM might reasonably pick from without domain-specific context.
# This list is committed and stable — it should not be dynamically generated.

TOP_LEVEL_TYPES: tuple[str, ...] = (
    # Root
    "Entity",
    # Physical branch
    "Physical",
    "Object",
    "Process",
    "Region",
    "Collection",
    # Abstract branch
    "Abstract",
    "Attribute",
    "Quantity",
    "Proposition",
    "Relation",
    # Object subtypes
    "Artifact",
    "Vehicle",
    "SelfConnectedObject",
    "ContentBearingObject",
    # Agent branch
    "AutonomousAgent",
    "Human",
    "Organism",
    "Group",
    "Organization",
    # Organization subtypes
    "GovernmentOrganization",
    "MilitaryOrganization",
    "Business",
    "Corporation",
    "EducationalOrganization",
    "ReligiousOrganization",
    "PoliticalOrganization",
    "InternationalOrganization",
    "NonprofitOrganization",
    # Military subtypes
    "MilitaryUnit",
    "MilitaryForce",
    "MilitaryService",
    # Device / weapon / platform
    "Device",
    "Weapon",
    "Aircraft",
    "MilitaryPlatform",
    "MilitaryAircraft",
    # Process subtypes
    "IntentionalProcess",
    "Motion",
    "MilitaryProcess",
    "ChemicalProcess",
    # Cognitive / sentient
    "CognitiveAgent",
    "SentientAgent",
    # Geographic / geopolitical
    "GeographicArea",
    "GeopoliticalArea",
    # Information bearing
    "ContentBearingPhysical",
    "Document",
    # System / facility
    "PhysicalSystem",
    "Facility",
    "CommunicationSystem",
)


def default_entity_fixtures() -> tuple[EntityFixture, ...]:
    """Return the default entity set for fidelity experiments.

    Includes a mix of military and non-military entities with known SUMO
    reference types, drawn from the PSYOP Stage 1 and Shield AI WhyGame
    runs.
    """
    return (
        EntityFixture(
            entity_name="CIA",
            entity_context="Central Intelligence Agency, US government intelligence agency",
            reference_type="GovernmentOrganization",
            constraint_type="Organization",
        ),
        EntityFixture(
            entity_name="Kratos Defense",
            entity_context="Kratos Defense & Security Solutions, US defense contractor",
            reference_type="Corporation",
            constraint_type="Organization",
        ),
        EntityFixture(
            entity_name="V-BAT",
            entity_context="Shield AI V-BAT, autonomous vertical takeoff and landing drone",
            reference_type="MilitaryAircraft",
            constraint_type="Aircraft",
        ),
        EntityFixture(
            entity_name="USSOCOM",
            entity_context="United States Special Operations Command",
            reference_type="MilitaryUnit",
            constraint_type="MilitaryOrganization",
        ),
        EntityFixture(
            entity_name="Brian",
            entity_context="A human person",
            reference_type="Human",
            constraint_type="CognitiveAgent",
        ),
        EntityFixture(
            entity_name="Shield AI",
            entity_context="Shield AI Inc., defense technology company building autonomous systems",
            reference_type="Corporation",
            constraint_type="Organization",
        ),
        EntityFixture(
            entity_name="Hivemind",
            entity_context="Shield AI Hivemind, autonomous AI pilot software",
            reference_type="ComputerProgram",
            constraint_type="Abstract",
        ),
        EntityFixture(
            entity_name="United States Army",
            entity_context="The land warfare service branch of the US Armed Forces",
            reference_type="Army",
            constraint_type="MilitaryOrganization",
        ),
    )


def generate_type_list(
    hierarchy: SUMOHierarchy,
    level: FidelityLevel,
    constraint_type: str,
    *,
    mid_level_max_depth: int = 3,
) -> tuple[str, ...]:
    """Generate a SUMO type list for the given fidelity level.

    Parameters
    ----------
    hierarchy:
        The SUMO hierarchy interface for type lookups.
    level:
        Which fidelity level to generate.
    constraint_type:
        The branch root used for mid-level and full-subtree generation.
        Ignored for top-level (which uses the static ``TOP_LEVEL_TYPES``).
    mid_level_max_depth:
        Maximum depth below *constraint_type* for mid-level lists.
        Default 3 produces roughly 20-40 types per branch.

    Returns
    -------
    Sorted tuple of SUMO type names.

    Raises
    ------
    ValueError:
        If *constraint_type* does not exist in the hierarchy (for
        mid-level and full-subtree levels).
    """
    if level == FidelityLevel.TOP_LEVEL:
        # Filter to types that actually exist in this DB.
        existing = [t for t in TOP_LEVEL_TYPES if hierarchy.type_exists(t)]
        return tuple(sorted(set(existing)))

    if not hierarchy.type_exists(constraint_type):
        msg = f"constraint_type {constraint_type!r} not found in SUMO hierarchy"
        raise ValueError(msg)

    if level == FidelityLevel.MID_LEVEL:
        subtypes = hierarchy.subtypes(constraint_type, max_depth=mid_level_max_depth)
        # Include the constraint type itself.
        all_types = sorted(set([constraint_type] + subtypes))
        return tuple(all_types)

    # level == FidelityLevel.FULL_SUBTREE (exhaustive — no other enum members).
    subtypes = hierarchy.subtypes(constraint_type)
    all_types = sorted(set([constraint_type] + subtypes))
    return tuple(all_types)


def build_prompt_variables(
    entity: EntityFixture,
    type_list: tuple[str, ...],
) -> dict[str, str]:
    """Build the Jinja2 template variables for a fidelity type-assignment prompt.

    Returns a dict ready for ``llm_client.render_prompt()`` kwargs.
    """
    return {
        "entity_name": entity.entity_name,
        "entity_context": entity.entity_context,
        "type_list": "\n".join(f"- {t}" for t in type_list),
    }


def prepare_experiment(
    hierarchy: SUMOHierarchy,
    entities: Sequence[EntityFixture],
    levels: Sequence[FidelityLevel],
    *,
    prompt_template: str = "prompts/evaluation/fidelity_type_assignment.yaml",
    mid_level_max_depth: int = 3,
) -> PreparedExperiment:
    """Construct all experiment inputs for the given entities and fidelity levels.

    This function does NOT call any LLMs. It generates type lists, builds
    prompt variables, and packages everything into a ``PreparedExperiment``
    ready for downstream execution.

    Parameters
    ----------
    hierarchy:
        The SUMO hierarchy interface for type lookups.
    entities:
        The entity fixtures to type.
    levels:
        Which fidelity levels to prepare.
    prompt_template:
        Repo-relative path to the prompt YAML template.
    mid_level_max_depth:
        Maximum depth for mid-level type list generation.

    Returns
    -------
    A ``PreparedExperiment`` containing one ``ExperimentItem`` per
    (entity, level) combination.

    Raises
    ------
    ValueError:
        If entities or levels are empty, or if a constraint type is
        not found in the hierarchy.
    """
    if not entities:
        msg = "entities must not be empty"
        raise ValueError(msg)
    if not levels:
        msg = "levels must not be empty"
        raise ValueError(msg)

    items: list[ExperimentItem] = []
    for entity in entities:
        for level in levels:
            type_list = generate_type_list(
                hierarchy,
                level,
                entity.constraint_type,
                mid_level_max_depth=mid_level_max_depth,
            )
            prompt_vars = build_prompt_variables(entity, type_list)
            items.append(
                ExperimentItem(
                    entity_name=entity.entity_name,
                    entity_context=entity.entity_context,
                    reference_type=entity.reference_type,
                    fidelity_level=level,
                    type_list=type_list,
                    prompt_variables=prompt_vars,
                )
            )

    return PreparedExperiment(
        entity_count=len(entities),
        fidelity_levels=tuple(dict.fromkeys(levels)),
        items=tuple(items),
        prompt_template=prompt_template,
    )


def prepare_experiment_from_config(
    sumo_db_path: Path,
    entities: Sequence[EntityFixture] | None = None,
    levels: Sequence[FidelityLevel] | None = None,
    *,
    prompt_template: str = "prompts/evaluation/fidelity_type_assignment.yaml",
    mid_level_max_depth: int = 3,
) -> PreparedExperiment:
    """Convenience wrapper that opens the hierarchy and prepares the experiment.

    Parameters
    ----------
    sumo_db_path:
        Path to the ``sumo_plus.db`` file.
    entities:
        Entity fixtures. Defaults to ``default_entity_fixtures()``.
    levels:
        Fidelity levels. Defaults to all three.
    prompt_template:
        Repo-relative path to the prompt template.
    mid_level_max_depth:
        Maximum depth for mid-level type list generation.
    """
    if entities is None:
        entities = list(default_entity_fixtures())
    if levels is None:
        levels = [FidelityLevel.TOP_LEVEL, FidelityLevel.MID_LEVEL, FidelityLevel.FULL_SUBTREE]

    with SUMOHierarchy(sumo_db_path) as hierarchy:
        return prepare_experiment(
            hierarchy,
            entities,
            levels,
            prompt_template=prompt_template,
            mid_level_max_depth=mid_level_max_depth,
        )
