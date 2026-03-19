"""Tests for the narrow research-agent to WhyGame transformation helper."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from onto_canon6.adapters import ResearchAgentWhyGameTransformService


def test_research_agent_transform_converts_relationships_into_whygame_facts() -> None:
    """Producer entity relationships should become WhyGame relationship facts."""

    service = ResearchAgentWhyGameTransformService()

    facts = service.transform_entities(
        entities=[
            {
                "name": "Shield AI",
                "type": "organization",
                "relationships": [
                    {
                        "entity": "Booz Allen Hamilton",
                        "type": "strategic_partner",
                        "detail": "Largest venture investment.",
                    }
                ],
            }
        ],
        investigation_id="shield_ai_full",
        source_file_label="entities.json",
    )

    assert len(facts) == 1
    fact = facts[0]
    assert fact.roles.from_ == "Shield AI"
    assert fact.roles.to == "Booz Allen Hamilton"
    assert fact.roles.relationship == "strategic_partner"
    assert fact.context["investigation"] == "shield_ai_full"
    assert fact.metadata["detail"] == "Largest venture investment."


def test_research_agent_transform_fails_loudly_when_no_relationships_exist() -> None:
    """The helper should reject producer input that cannot yield any relationship facts."""

    service = ResearchAgentWhyGameTransformService()

    with pytest.raises(
        ValueError,
        match="produced no WhyGame relationship facts",
    ):
        service.transform_entities(
            entities=[{"name": "Shield AI", "type": "organization", "relationships": []}],
            investigation_id="shield_ai_full",
        )


def test_research_agent_transform_writes_json_file(tmp_path: Path) -> None:
    """The helper should write a reusable WhyGame relationship file for later import."""

    input_path = tmp_path / "entities.json"
    output_path = tmp_path / "whygame_relationships.json"
    input_path.write_text(
        json.dumps(
            [
                {
                    "name": "Shield AI",
                    "type": "organization",
                    "relationships": [
                        {
                            "entity": "Palantir Technologies",
                            "type": "partner",
                            "detail": "C2 for autonomous systems.",
                        }
                    ],
                }
            ],
            indent=2,
        ),
        encoding="utf-8",
    )

    result = ResearchAgentWhyGameTransformService().write_transformed_facts(
        input_path=input_path,
        output_path=output_path,
        investigation_id="shield_ai_full",
    )

    assert result.fact_count == 1
    assert output_path.exists()
    loaded = json.loads(output_path.read_text(encoding="utf-8"))
    assert loaded[0]["roles"]["relationship"] == "partner"
