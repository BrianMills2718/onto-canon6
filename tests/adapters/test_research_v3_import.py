"""Tests for the research_v3 KnowledgeGraph import adapter."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml

from onto_canon6.adapters.research_v3_import import (
    FTM_TO_OC_TYPE,
    import_research_v3_graph,
    map_corroboration_to_confidence,
    map_ftm_entity_type,
)


def _write_graph_yaml(tmp_path: Path, graph_data: dict) -> Path:
    """Write a test graph.yaml file."""
    graph_path = tmp_path / "graph.yaml"
    with graph_path.open("w") as f:
        yaml.dump(graph_data, f)
    return graph_path


MINIMAL_GRAPH = {
    "goal": {"question": "test question"},
    "entities": {
        "ent_1": {
            "id": "ent_1",
            "schema": "Company",
            "properties": {"name": ["Acme Corp"]},
        },
        "ent_2": {
            "id": "ent_2",
            "schema": "PublicBody",
            "properties": {"name": ["Department of Defense"]},
        },
        "ent_3": {
            "id": "ent_3",
            "schema": "Person",
            "properties": {"name": ["John Smith"]},
        },
    },
    "claims": [
        {
            "id": "C-001",
            "statement": "Acme Corp lobbied the Department of Defense on cybersecurity.",
            "entity_refs": ["ent_1", "ent_2"],
            "claim_type": "relationship_claim",
            "source": {
                "id": "src_1",
                "url": "https://example.com/report",
                "source_type": "government_db",
                "retrieved_at": "2026-03-15T12:00:00Z",
            },
            "corroboration_status": "corroborated",
            "confidence": "high",
        },
        {
            "id": "C-002",
            "statement": "John Smith is the CEO of Acme Corp.",
            "entity_refs": ["ent_3", "ent_1"],
            "claim_type": "fact_claim",
            "source": {
                "id": "src_2",
                "url": "https://example.com/bio",
                "source_type": "news",
                "retrieved_at": "2026-03-15T13:00:00Z",
            },
            "corroboration_status": "unverified",
            "confidence": "medium",
        },
    ],
}


class TestMapFtmEntityType:
    """Test FtM schema → onto-canon6 entity type mapping."""

    def test_person(self) -> None:
        assert map_ftm_entity_type("Person") == "oc:person"

    def test_company(self) -> None:
        assert map_ftm_entity_type("Company") == "oc:company"

    def test_public_body(self) -> None:
        assert map_ftm_entity_type("PublicBody") == "oc:government_organization"

    def test_unknown_schema(self) -> None:
        assert map_ftm_entity_type("CustomThing") == "oc:customthing"

    def test_all_mapped_schemas(self) -> None:
        """Every schema in the map produces a non-empty result."""
        for schema, oc_type in FTM_TO_OC_TYPE.items():
            assert oc_type.startswith("oc:"), f"{schema} → {oc_type} missing oc: prefix"


class TestMapCorroborationToConfidence:
    """Test corroboration status → confidence score mapping."""

    def test_corroborated(self) -> None:
        score = map_corroboration_to_confidence("corroborated")
        assert score == 0.90

    def test_unverified(self) -> None:
        score = map_corroboration_to_confidence("unverified")
        assert score == 0.50

    def test_contradicted(self) -> None:
        score = map_corroboration_to_confidence("contradicted")
        assert score == 0.20

    def test_with_confidence_label(self) -> None:
        score = map_corroboration_to_confidence("corroborated", confidence_label="high")
        # Average of high=0.85 and corroborated=0.90
        assert score == pytest.approx(0.875)

    def test_explicit_score_overrides(self) -> None:
        score = map_corroboration_to_confidence(
            "unverified", confidence_label="high", confidence_score=0.99
        )
        assert score == 0.99


class TestImportResearchV3Graph:
    """Test the full import pipeline."""

    def test_basic_import(self, tmp_path: Path) -> None:
        """Basic import produces candidate imports."""
        graph_path = _write_graph_yaml(tmp_path, MINIMAL_GRAPH)
        imports = import_research_v3_graph(graph_path=graph_path)
        assert len(imports) == 2

    def test_claim_to_predicate_mapping(self, tmp_path: Path) -> None:
        """Claim types map to rv3: predicates."""
        graph_path = _write_graph_yaml(tmp_path, MINIMAL_GRAPH)
        imports = import_research_v3_graph(graph_path=graph_path)
        predicates = [imp.payload["predicate"] for imp in imports]
        assert "rv3:asserts_relationship" in predicates
        assert "rv3:asserts_fact" in predicates

    def test_entity_type_mapping(self, tmp_path: Path) -> None:
        """FtM entity types map to oc: types in role fillers."""
        graph_path = _write_graph_yaml(tmp_path, MINIMAL_GRAPH)
        imports = import_research_v3_graph(graph_path=graph_path)
        # First claim: Company + PublicBody
        roles = imports[0].payload["roles"]
        arg0_type = roles["ARG0"][0]["entity_type"]
        arg1_type = roles["ARG1"][0]["entity_type"]
        assert arg0_type == "oc:company"
        assert arg1_type == "oc:government_organization"

    def test_entity_names(self, tmp_path: Path) -> None:
        """Entity names are extracted from FtM properties."""
        graph_path = _write_graph_yaml(tmp_path, MINIMAL_GRAPH)
        imports = import_research_v3_graph(graph_path=graph_path)
        roles = imports[0].payload["roles"]
        assert roles["ARG0"][0]["name"] == "Acme Corp"
        assert roles["ARG1"][0]["name"] == "Department of Defense"

    def test_confidence_in_payload(self, tmp_path: Path) -> None:
        """Confidence score is derived and stored in payload."""
        graph_path = _write_graph_yaml(tmp_path, MINIMAL_GRAPH)
        imports = import_research_v3_graph(graph_path=graph_path)
        # First claim: corroborated + high = 0.875
        assert imports[0].payload["confidence"] == pytest.approx(0.875)
        # Second claim: unverified + medium
        assert 0.0 < imports[1].payload["confidence"] < 1.0

    def test_provenance_preserved(self, tmp_path: Path) -> None:
        """Source URLs and metadata survive import."""
        graph_path = _write_graph_yaml(tmp_path, MINIMAL_GRAPH)
        imports = import_research_v3_graph(graph_path=graph_path)
        src = imports[0].source_artifact
        assert "example.com/report" in src.source_ref
        assert src.source_metadata["source_type"] == "government_db"
        assert src.source_metadata["retrieved_at"] == "2026-03-15T12:00:00Z"

    def test_claim_text(self, tmp_path: Path) -> None:
        """Claim statement becomes claim_text."""
        graph_path = _write_graph_yaml(tmp_path, MINIMAL_GRAPH)
        imports = import_research_v3_graph(graph_path=graph_path)
        assert "Acme Corp lobbied" in imports[0].claim_text

    def test_empty_graph(self, tmp_path: Path) -> None:
        """Empty graph produces empty imports."""
        graph_path = _write_graph_yaml(tmp_path, {"claims": [], "entities": {}})
        imports = import_research_v3_graph(graph_path=graph_path)
        assert len(imports) == 0

    def test_claim_without_entities(self, tmp_path: Path) -> None:
        """Claim with no entity_refs still imports (empty roles)."""
        graph_data = {
            "claims": [
                {
                    "id": "C-orphan",
                    "statement": "An important fact.",
                    "entity_refs": [],
                    "claim_type": "fact_claim",
                    "source": {"id": "s1", "url": "", "source_type": "unknown"},
                    "corroboration_status": "unverified",
                }
            ],
            "entities": {},
        }
        graph_path = _write_graph_yaml(tmp_path, graph_data)
        imports = import_research_v3_graph(graph_path=graph_path)
        assert len(imports) == 1
        assert imports[0].payload["roles"] == {}

    def test_custom_profile(self, tmp_path: Path) -> None:
        """Custom profile_id and version are passed through."""
        graph_path = _write_graph_yaml(tmp_path, MINIMAL_GRAPH)
        imports = import_research_v3_graph(
            graph_path=graph_path,
            profile_id="custom_profile",
            profile_version="2.0.0",
        )
        assert imports[0].profile.profile_id == "custom_profile"
        assert imports[0].profile.profile_version == "2.0.0"

    def test_research_v3_metadata_in_payload(self, tmp_path: Path) -> None:
        """research_v3 claim_id and corroboration status are in payload."""
        graph_path = _write_graph_yaml(tmp_path, MINIMAL_GRAPH)
        imports = import_research_v3_graph(graph_path=graph_path)
        assert imports[0].payload["research_v3_claim_id"] == "C-001"
        assert imports[0].payload["research_v3_corroboration"] == "corroborated"
