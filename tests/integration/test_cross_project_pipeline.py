"""Integration tests for the cross-project pipeline and source query surface.

These tests exercise the integration adapters and query surface without
making real LLM calls.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from onto_canon6.adapters.grounded_research_import import import_shared_claims
from onto_canon6.core.graph_service import CanonicalGraphService
from onto_canon6.pipeline.service import ReviewService
from onto_canon6.surfaces.query_surface import QuerySurfaceService


def _make_test_claims():
    """Create minimal shared ClaimRecords without importing epistemic_contracts."""
    from epistemic_contracts import ClaimRecord, ConfidenceScore, EntityReference

    return [
        ClaimRecord(
            id="test-c1",
            statement="Company A lobbied Agency B for contract C.",
            claim_type="relationship_claim",
            status="corroborated",
            confidence=ConfidenceScore(score=0.85, source="adjudication"),
            source_ids=["src-1"],
            entity_refs=[
                EntityReference(
                    entity_id="ent:company_a",
                    name="Company A",
                    entity_type="oc:company",
                ),
                EntityReference(
                    entity_id="ent:agency_b",
                    name="Agency B",
                    entity_type="oc:government_organization",
                ),
            ],
            source_system="test",
        ),
        ClaimRecord(
            id="test-c2",
            statement="Company A received $5M in federal contracts.",
            claim_type="financial_claim",
            status="unverified",
            confidence=ConfidenceScore(score=0.5, source="investigation"),
            source_ids=["src-2"],
            entity_refs=[
                EntityReference(
                    entity_id="ent:company_a",
                    name="Company A",
                    entity_type="oc:company",
                ),
            ],
            source_system="test",
        ),
        ClaimRecord(
            id="test-c3",
            statement="Sanctions are imperfectly binding.",
            claim_type="fact_claim",
            status="initial",
            confidence=ConfidenceScore(score=0.8, source="adjudication"),
            source_ids=[],
            source_system="test",
        ),
    ]


class TestCrossProjectPipeline:
    """Test the shared-contracts import → review → promote chain."""

    @pytest.fixture()
    def pipeline_db(self, tmp_path: Path) -> Path:
        db = tmp_path / "test_pipeline.sqlite3"
        claims = _make_test_claims()
        candidates = import_shared_claims(claims)
        svc = ReviewService(db_path=db)
        gs = CanonicalGraphService(db_path=db)

        for c in candidates:
            result = svc.submit_candidate_import(candidate_import=c)
            svc.review_candidate(
                candidate_id=result.candidate.candidate_id,
                decision="accepted",
                actor_id="test",
            )
            try:
                gs.promote_candidate(
                    candidate_id=result.candidate.candidate_id,
                    promoted_by="test",
                )
            except Exception:
                pass  # role-free claims may not produce entities
        return db

    def test_all_claims_submitted(self, pipeline_db: Path) -> None:
        svc = ReviewService(db_path=pipeline_db)
        candidates = svc.list_candidate_assertions()
        assert len(candidates) == 3

    def test_role_bearing_claims_produce_entities(self, pipeline_db: Path) -> None:
        gs = CanonicalGraphService(db_path=pipeline_db)
        assertions = gs.list_promoted_assertions()
        # Claims with entity_refs should produce assertions with role fillers
        assert len(assertions) >= 2

    def test_role_free_claim_promotes(self, pipeline_db: Path) -> None:
        gs = CanonicalGraphService(db_path=pipeline_db)
        assertions = gs.list_promoted_assertions()
        predicates = {a.predicate for a in assertions}
        # All 3 claims should promote (including role-free claim 3)
        assert "shared:fact_claim" in predicates

    def test_confidence_preserved_in_payload(self, pipeline_db: Path) -> None:
        import sqlite3
        conn = sqlite3.connect(str(pipeline_db))
        rows = conn.execute("SELECT payload_json FROM candidate_assertions").fetchall()
        confidences = []
        for row in rows:
            payload = json.loads(row[0])
            conf = payload.get("confidence")
            if conf is not None:
                confidences.append(conf)
        assert 0.85 in confidences


class TestSourceQuerySurface:
    """Test the source browse/search/get surface."""

    @pytest.fixture()
    def query_db(self, tmp_path: Path) -> Path:
        db = tmp_path / "test_query.sqlite3"
        claims = _make_test_claims()
        candidates = import_shared_claims(claims)
        svc = ReviewService(db_path=db)
        for c in candidates:
            svc.submit_candidate_import(candidate_import=c)
        return db

    def test_list_sources(self, query_db: Path) -> None:
        from onto_canon6.surfaces.query_models import SourceBrowseRequest
        svc = QuerySurfaceService(
            review_service=ReviewService(db_path=query_db),
            graph_service=CanonicalGraphService(db_path=query_db),
        )
        results = svc.list_sources(SourceBrowseRequest())
        assert len(results) >= 1

    def test_search_sources(self, query_db: Path) -> None:
        from onto_canon6.surfaces.query_models import SourceSearchRequest
        svc = QuerySurfaceService(
            review_service=ReviewService(db_path=query_db),
            graph_service=CanonicalGraphService(db_path=query_db),
        )
        results = svc.search_sources(SourceSearchRequest(query="test"))
        assert len(results) >= 1

    def test_get_source(self, query_db: Path) -> None:
        from onto_canon6.surfaces.query_models import GetSourceRequest, SourceBrowseRequest
        svc = QuerySurfaceService(
            review_service=ReviewService(db_path=query_db),
            graph_service=CanonicalGraphService(db_path=query_db),
        )
        sources = svc.list_sources(SourceBrowseRequest())
        assert len(sources) > 0
        detail = svc.get_source(GetSourceRequest(source_ref=sources[0].source_ref))
        assert detail.source_ref == sources[0].source_ref
