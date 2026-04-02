"""Narrow transformation of research-agent relationship output into WhyGame facts.

This module deliberately does not invent a broad cross-project contract layer.
It only knows how to read the current `research-agent` `entities.json` shape
that contains entity records with embedded relationship summaries and convert
those summaries into WhyGame `RELATIONSHIP` facts for the existing adapter.
"""

from __future__ import annotations

import json
from pathlib import Path
import re
from typing import Mapping, Sequence

from pydantic import BaseModel, ConfigDict, Field, JsonValue, TypeAdapter

from ..config import get_config
from .whygame_models import WhyGameRelationshipFact, WhyGameRelationshipRoles

_JSON_OBJECT_ADAPTER = TypeAdapter(dict[str, JsonValue])


class ResearchAgentRelationship(BaseModel):
    """One relationship summary embedded inside a research-agent entity record."""

    model_config = ConfigDict(extra="ignore", frozen=True)

    entity: str = Field(min_length=1)
    type: str = Field(min_length=1)
    detail: str | None = None


class ResearchAgentEntityRecord(BaseModel):
    """Minimal producer entity shape used by the Shield AI investigation output."""

    model_config = ConfigDict(extra="ignore", frozen=True)

    name: str = Field(min_length=1)
    type: str | None = None
    relationships: tuple[ResearchAgentRelationship, ...] = ()


class ResearchAgentWhyGameTransformResult(BaseModel):
    """Deterministic output of one research-agent to WhyGame transformation."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    input_path: str = Field(min_length=1)
    output_path: str = Field(min_length=1)
    fact_count: int = Field(ge=1)
    investigation_id: str | None = None
    facts: tuple[WhyGameRelationshipFact, ...] = ()


class ResearchAgentWhyGameTransformService:
    """Convert current research-agent relationship output into WhyGame facts."""

    def __init__(self) -> None:
        """Load repo-configured defaults for producer-side transformation."""

        self._config = get_config().adapters.research_agent

    def transform_entities(
        self,
        *,
        entities: Sequence[Mapping[str, object]],
        investigation_id: str | None = None,
        source_file_label: str = "entities.json",
    ) -> tuple[WhyGameRelationshipFact, ...]:
        """Convert entity relationship summaries into WhyGame relationship facts.

        The transformation is intentionally mechanical:

        1. every source entity with embedded relationships becomes the `from`
           side of one or more WhyGame facts;
        2. the producer relationship `type` becomes the WhyGame
           `relationship_label`;
        3. any producer `detail` is preserved in fact metadata instead of being
           dropped or force-fit into the ontology.
        """

        facts: list[WhyGameRelationshipFact] = []
        for entity_record in (
            ResearchAgentEntityRecord.model_validate(entity_mapping) for entity_mapping in entities
        ):
            for relationship in entity_record.relationships:
                metadata: dict[str, JsonValue] = {
                    "producer_project": "research-agent",
                    "source_file": source_file_label,
                }
                if relationship.detail is not None and relationship.detail.strip():
                    metadata["detail"] = relationship.detail.strip()
                fact = WhyGameRelationshipFact(
                    id=f"{_fact_prefix(entity_record.name)}_{len(facts) + 1:03d}",
                    fact_type="RELATIONSHIP",
                    roles=WhyGameRelationshipRoles(
                        **{
                            "from": entity_record.name.strip(),
                            "to": relationship.entity.strip(),
                            "relationship": relationship.type.strip(),
                        }
                    ),
                    context=_JSON_OBJECT_ADAPTER.validate_python(
                        {
                            "investigation": investigation_id,
                            "producer_entity_type": entity_record.type,
                        }
                    ),
                    confidence=self._config.default_relationship_confidence,
                    metadata=metadata,
                )
                facts.append(fact)
        if not facts:
            raise ValueError("research-agent entity input produced no WhyGame relationship facts")
        return tuple(facts)

    def write_transformed_facts(
        self,
        *,
        input_path: Path,
        output_path: Path,
        investigation_id: str | None = None,
    ) -> ResearchAgentWhyGameTransformResult:
        """Load one producer file, write transformed WhyGame facts, and report the result."""

        entities_adapter = TypeAdapter(list[dict[str, object]])
        loaded = entities_adapter.validate_json(input_path.read_text(encoding="utf-8"))
        facts = self.transform_entities(
            entities=loaded,
            investigation_id=investigation_id,
            source_file_label=input_path.name,
        )
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(
            json.dumps([fact.model_dump(mode="json", by_alias=True) for fact in facts], indent=2),
            encoding="utf-8",
        )
        return ResearchAgentWhyGameTransformResult(
            input_path=str(input_path),
            output_path=str(output_path),
            fact_count=len(facts),
            investigation_id=investigation_id,
            facts=facts,
        )


def _fact_prefix(entity_name: str) -> str:
    """Create a stable fact-id prefix from the producer entity name."""

    slug = re.sub(r"[^a-z0-9]+", "_", entity_name.lower()).strip("_")
    if not slug:
        return "research_agent_rel"
    return f"ra_{slug}"


__all__ = [
    "ResearchAgentEntityRecord",
    "ResearchAgentRelationship",
    "ResearchAgentWhyGameTransformResult",
    "ResearchAgentWhyGameTransformService",
]
