"""Cross-project contract boundary tests.

These tests verify that data flows correctly across project boundaries in the
research_v3 → epistemic-contracts → onto-canon6 → DIGIMON chain. They catch
silent contract breakage — format changes in one project that would corrupt
downstream consumers without raising an exception.

Each test exercises a specific boundary contract:

  B1: research_v3 memo format → ClaimRecord (via load_memo_claims)
  B2: research_v3 graph format → ClaimRecord (via load_graph_claims)
  B3: ClaimRecord.source_urls flows through to onto-canon6 source_metadata
  B4: ClaimRecord → CandidateAssertionImport (import_shared_claims)
  B5: onto-canon6 promoted graph → DIGIMON entities.jsonl + relationships.jsonl
  B6: Full chain E2E: memo → ClaimRecord → onto-canon6 → DIGIMON entities with source URLs
  B7: Missing/empty fields degrade gracefully, not silently
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

import pytest
import yaml

from tests.integration.conftest_research_v3 import load_shared_export


# ─── Fixtures ─────────────────────────────────────────────────────────────────

def _make_minimal_memo() -> dict[str, Any]:
    """Minimal research_v3 memo.yaml structure with two findings."""
    return {
        "question": "Test investigation question",
        "goal": "Test goal",
        "key_findings": [
            {
                "claim": "Company A lobbied Agency B for contract C.",
                "confidence": 0.85,
                "corroborated": True,
                "source_urls": [
                    "https://example.com/article1",
                    "https://example.com/article2",
                ],
                "tags": ["lobbying", "federal"],
            },
            {
                "claim": "Company A received $5M in federal contracts.",
                "confidence": 0.65,
                "corroborated": False,
                "source_urls": ["https://example.com/contracts"],
                "tags": [],
            },
        ],
        "entities": [
            {
                "canonical_name": "Company A",
                "entity_type": "Organization",
                "aliases": ["CompanyA Inc."],
                "finding_indices": [0, 1],
            },
            {
                "canonical_name": "Agency B",
                "entity_type": "GovernmentAgency",
                "aliases": [],
                "finding_indices": [0],
            },
        ],
    }


def _make_minimal_graph() -> dict[str, Any]:
    """Minimal research_v3 graph.yaml structure."""
    return {
        "goal": {"question": "Test graph question"},
        "entities": {
            "e1": {
                "id": "e1",
                "schema": "Company",
                "properties": {"name": ["TestCorp"]},
            },
            "e2": {
                "id": "e2",
                "schema": "Person",
                "properties": {"name": ["Jane Doe"]},
            },
        },
        "claims": [
            {
                "id": "C-test-001",
                "statement": "Jane Doe is CEO of TestCorp.",
                "entity_refs": ["e2", "e1"],
                "claim_type": "fact_claim",
                "source": {
                    "id": "s1",
                    "url": "https://example.com/news",
                    "source_type": "news",
                    "retrieved_at": "2026-03-26T00:00:00Z",
                },
                "corroboration_status": "corroborated",
                "confidence": "high",
            },
        ],
        "sources": {
            "s1": {
                "id": "s1",
                "url": "https://example.com/news",
                "source_type": "news",
                "credibility": "reliable",
                "retrieved_at": "2026-03-26T00:00:00Z",
            }
        },
    }


@pytest.fixture()
def memo_file(tmp_path: Path) -> Path:
    path = tmp_path / "memo.yaml"
    path.write_text(yaml.dump(_make_minimal_memo()))
    return path


@pytest.fixture()
def graph_file(tmp_path: Path) -> Path:
    path = tmp_path / "graph.yaml"
    path.write_text(yaml.dump(_make_minimal_graph()))
    return path


@pytest.fixture()
def full_pipeline_db(tmp_path: Path, memo_file: Path) -> Path:
    """Run full chain for one memo; return the pipeline SQLite db_path."""
    shared_export = load_shared_export()
    from onto_canon6.adapters.grounded_research_import import import_shared_claims
    from onto_canon6.core.graph_service import CanonicalGraphService
    from onto_canon6.pipeline.service import ReviewService

    claims = shared_export.load_memo_claims(memo_file)
    candidates = import_shared_claims(claims)

    db_path = tmp_path / "pipeline.sqlite3"
    svc = ReviewService(db_path=db_path)
    gs = CanonicalGraphService(db_path=db_path)

    for cand in candidates:
        sub = svc.submit_candidate_import(candidate_import=cand)
        svc.review_candidate(
            candidate_id=sub.candidate.candidate_id,
            decision="accepted",
            actor_id="test",
        )
        try:
            gs.promote_candidate(
                candidate_id=sub.candidate.candidate_id,
                promoted_by="test",
            )
        except Exception:
            pass  # role-free claims may not produce graph objects

    return db_path


# ─── B5/B6 shared helper ──────────────────────────────────────────────────────

def _run_digimon_export(db_path: Path, output_dir: Path) -> tuple[Path, Path]:
    """Export promoted graph to DIGIMON JSONL files; return (entities_path, rels_path)."""
    from onto_canon6.adapters.digimon_export import export_for_digimon, write_digimon_jsonl
    from onto_canon6.core.graph_service import CanonicalGraphService
    from onto_canon6.pipeline.service import ReviewService

    bundle = export_for_digimon(
        graph_service=CanonicalGraphService(db_path=db_path),
        review_service=ReviewService(db_path=db_path),
    )
    return write_digimon_jsonl(bundle, output_dir)


# ─── B1: research_v3 memo → ClaimRecord ──────────────────────────────────────

class TestB1MemoToClaimRecord:
    """Boundary 1: research_v3 memo.yaml → epistemic_contracts.ClaimRecord."""

    def test_produces_one_claim_per_finding(self, memo_file: Path) -> None:
        shared_export = load_shared_export()
        claims = shared_export.load_memo_claims(memo_file)
        assert len(claims) == 2

    def test_claim_statement_preserved(self, memo_file: Path) -> None:
        shared_export = load_shared_export()
        claims = shared_export.load_memo_claims(memo_file)
        statements = {c.statement for c in claims}
        assert "Company A lobbied Agency B for contract C." in statements

    def test_source_urls_populated(self, memo_file: Path) -> None:
        """Source URLs must flow from finding into ClaimRecord (three-layer fix 2026-04-05)."""
        shared_export = load_shared_export()
        claims = shared_export.load_memo_claims(memo_file)
        claim = next(c for c in claims if "lobbied" in c.statement)
        assert len(claim.source_urls) == 2
        assert "https://example.com/article1" in claim.source_urls

    def test_corroboration_status_reflected(self, memo_file: Path) -> None:
        shared_export = load_shared_export()
        claims = shared_export.load_memo_claims(memo_file)
        corroborated = [c for c in claims if c.corroboration_status == "corroborated"]
        unverified = [c for c in claims if c.corroboration_status == "unverified"]
        assert len(corroborated) == 1
        assert len(unverified) == 1

    def test_confidence_in_range(self, memo_file: Path) -> None:
        shared_export = load_shared_export()
        claims = shared_export.load_memo_claims(memo_file)
        for c in claims:
            assert c.confidence is not None
            assert 0.0 <= c.confidence.score <= 1.0

    def test_entity_refs_attached(self, memo_file: Path) -> None:
        shared_export = load_shared_export()
        claims = shared_export.load_memo_claims(memo_file)
        claim0 = next(c for c in claims if "lobbied" in c.statement)
        assert len(claim0.entity_refs) == 2
        names = {e.name for e in claim0.entity_refs}
        assert "Company A" in names
        assert "Agency B" in names

    def test_source_system_is_research_v3(self, memo_file: Path) -> None:
        shared_export = load_shared_export()
        claims = shared_export.load_memo_claims(memo_file)
        assert all(c.source_system == "research_v3" for c in claims)

    def test_empty_findings_produces_empty_list(self, tmp_path: Path) -> None:
        shared_export = load_shared_export()
        empty_memo = tmp_path / "empty.yaml"
        empty_memo.write_text(yaml.dump({"question": "q", "key_findings": []}))
        claims = shared_export.load_memo_claims(empty_memo)
        assert claims == []

    def test_finding_without_source_urls_produces_empty_list(self, tmp_path: Path) -> None:
        """Findings without source_urls must not crash — they produce empty source_urls."""
        shared_export = load_shared_export()
        memo = tmp_path / "nosrc.yaml"
        memo.write_text(yaml.dump({
            "question": "q",
            "key_findings": [{"claim": "No source finding.", "confidence": 0.5}],
        }))
        claims = shared_export.load_memo_claims(memo)
        assert len(claims) == 1
        assert claims[0].source_urls == []


# ─── B2: research_v3 graph → ClaimRecord ─────────────────────────────────────

class TestB2GraphToClaimRecord:
    """Boundary 2: research_v3 graph.yaml → epistemic_contracts.ClaimRecord."""

    def test_produces_one_claim_per_graph_claim(self, graph_file: Path) -> None:
        shared_export = load_shared_export()
        claims = shared_export.load_graph_claims(graph_file)
        assert len(claims) == 1

    def test_statement_preserved(self, graph_file: Path) -> None:
        shared_export = load_shared_export()
        claims = shared_export.load_graph_claims(graph_file)
        assert claims[0].statement == "Jane Doe is CEO of TestCorp."

    def test_entity_refs_populated_from_ftm(self, graph_file: Path) -> None:
        shared_export = load_shared_export()
        claims = shared_export.load_graph_claims(graph_file)
        assert len(claims[0].entity_refs) == 2
        entity_ids = {e.entity_id for e in claims[0].entity_refs}
        assert "rv3:e1" in entity_ids
        assert "rv3:e2" in entity_ids

    def test_entity_types_mapped_from_ftm(self, graph_file: Path) -> None:
        shared_export = load_shared_export()
        claims = shared_export.load_graph_claims(graph_file)
        types = {e.entity_type for e in claims[0].entity_refs}
        assert "oc:company" in types
        assert "oc:person" in types


# ─── B3: source_urls provenance flow ─────────────────────────────────────────

class TestB3SourceUrlsProvenance:
    """Boundary 3: source_urls flows ClaimRecord → onto-canon6 source_metadata_json."""

    def test_source_urls_in_candidate_source_metadata(
        self, tmp_path: Path, memo_file: Path
    ) -> None:
        shared_export = load_shared_export()
        from onto_canon6.adapters.grounded_research_import import import_shared_claims
        from onto_canon6.pipeline.service import ReviewService

        claims = shared_export.load_memo_claims(memo_file)
        candidates = import_shared_claims(claims)
        db = tmp_path / "provenance_test.sqlite3"
        svc = ReviewService(db_path=db)
        for cand in candidates:
            svc.submit_candidate_import(candidate_import=cand)

        conn = sqlite3.connect(str(db))
        rows = conn.execute(
            "SELECT source_metadata_json FROM candidate_assertions"
        ).fetchall()
        conn.close()

        all_source_urls: list[str] = []
        for (meta_json,) in rows:
            meta = json.loads(meta_json) if meta_json else {}
            all_source_urls.extend(meta.get("source_urls", []))

        assert "https://example.com/article1" in all_source_urls, (
            "source_urls from research_v3 finding must flow into onto-canon6 "
            "source_metadata_json (three-layer fix: ClaimRecord.source_urls → "
            "import_shared_claims → source_metadata)"
        )

    def test_claim_without_source_urls_does_not_crash(self, tmp_path: Path) -> None:
        from epistemic_contracts import ClaimRecord, ConfidenceScore
        from onto_canon6.adapters.grounded_research_import import import_shared_claims
        from onto_canon6.pipeline.service import ReviewService

        claims = [
            ClaimRecord(
                id="no-urls-c1",
                statement="A claim with no source URLs.",
                claim_type="assertion",
                status="unverified",
                confidence=ConfidenceScore(score=0.5, source="investigation"),
                source_urls=[],
                source_system="test",
            )
        ]
        candidates = import_shared_claims(claims)
        db = tmp_path / "nourltest.sqlite3"
        svc = ReviewService(db_path=db)
        result = svc.submit_candidate_import(candidate_import=candidates[0])
        assert result.candidate.candidate_id.startswith("cand_")

        conn = sqlite3.connect(str(db))
        meta_json = conn.execute(
            "SELECT source_metadata_json FROM candidate_assertions WHERE candidate_id = ?",
            (result.candidate.candidate_id,),
        ).fetchone()[0]
        conn.close()

        meta = json.loads(meta_json) if meta_json else {}
        assert meta.get("source_urls") == []


# ─── B4: ClaimRecord → CandidateAssertionImport ───────────────────────────────

class TestB4ClaimRecordToCandidate:
    """Boundary 4: import_shared_claims() contract."""

    def test_one_candidate_per_claim(self) -> None:
        from epistemic_contracts import ClaimRecord, ConfidenceScore
        from onto_canon6.adapters.grounded_research_import import import_shared_claims

        claims = [
            ClaimRecord(
                id=f"c{i}",
                statement=f"Claim {i}.",
                claim_type="assertion",
                status="unverified",
                confidence=ConfidenceScore(score=0.5, source="investigation"),
                source_system="test",
            )
            for i in range(5)
        ]
        candidates = import_shared_claims(claims)
        assert len(candidates) == 5

    def test_claim_text_preserved(self) -> None:
        from epistemic_contracts import ClaimRecord, ConfidenceScore
        from onto_canon6.adapters.grounded_research_import import import_shared_claims

        claims = [
            ClaimRecord(
                id="c1",
                statement="The quick brown fox.",
                claim_type="assertion",
                status="unverified",
                confidence=ConfidenceScore(score=0.7, source="investigation"),
                source_system="test",
            )
        ]
        candidates = import_shared_claims(claims)
        assert candidates[0].claim_text == "The quick brown fox."

    def test_confidence_preserved_in_payload(self) -> None:
        from epistemic_contracts import ClaimRecord, ConfidenceScore
        from onto_canon6.adapters.grounded_research_import import import_shared_claims

        claims = [
            ClaimRecord(
                id="c1",
                statement="High confidence claim.",
                claim_type="assertion",
                status="corroborated",
                confidence=ConfidenceScore(score=0.92, source="adjudication"),
                source_system="test",
            )
        ]
        candidates = import_shared_claims(claims)
        assert candidates[0].payload["confidence"] == pytest.approx(0.92)

    def test_source_urls_in_source_metadata(self) -> None:
        from epistemic_contracts import ClaimRecord, ConfidenceScore
        from onto_canon6.adapters.grounded_research_import import import_shared_claims

        claims = [
            ClaimRecord(
                id="c1",
                statement="Sourced claim.",
                claim_type="assertion",
                status="corroborated",
                confidence=ConfidenceScore(score=0.8, source="investigation"),
                source_urls=["https://real.example.com/source"],
                source_system="test",
            )
        ]
        candidates = import_shared_claims(claims)
        meta = candidates[0].source_artifact.source_metadata or {}
        assert meta.get("source_urls") == ["https://real.example.com/source"]

    def test_empty_claims_list_returns_empty(self) -> None:
        from onto_canon6.adapters.grounded_research_import import import_shared_claims
        candidates = import_shared_claims([])
        assert candidates == []


# ─── B5: onto-canon6 → DIGIMON export ────────────────────────────────────────

class TestB5DigimonExport:
    """Boundary 5: promoted graph → DIGIMON JSONL format."""

    def test_entities_jsonl_valid_json_lines(
        self, full_pipeline_db: Path, tmp_path: Path
    ) -> None:
        entities_path, _ = _run_digimon_export(full_pipeline_db, tmp_path / "out_b5a")
        assert entities_path.exists()
        rows = [
            json.loads(line)
            for line in entities_path.read_text().splitlines()
            if line.strip()
        ]
        assert len(rows) > 0

    def test_entities_have_required_fields(
        self, full_pipeline_db: Path, tmp_path: Path
    ) -> None:
        entities_path, _ = _run_digimon_export(full_pipeline_db, tmp_path / "out_b5b")
        for line in entities_path.read_text().splitlines():
            line = line.strip()
            if not line:
                continue
            row = json.loads(line)
            assert "entity_name" in row, f"entity_name missing: {row}"
            assert row["entity_name"], "entity_name must be non-empty"

    def test_relationships_jsonl_valid_json_lines(
        self, full_pipeline_db: Path, tmp_path: Path
    ) -> None:
        _, rels_path = _run_digimon_export(full_pipeline_db, tmp_path / "out_b5c")
        assert rels_path.exists()
        for line in rels_path.read_text().splitlines():
            if line.strip():
                json.loads(line)  # must not raise


# ─── B6: Full chain E2E ───────────────────────────────────────────────────────

class TestB6FullChainE2E:
    """Boundary 6: memo → ClaimRecord → onto-canon6 → DIGIMON entities with source URLs."""

    def test_source_urls_survive_full_pipeline(
        self, full_pipeline_db: Path, tmp_path: Path
    ) -> None:
        """Source URLs from research_v3 findings must appear in DIGIMON entities.jsonl."""
        entities_path, _ = _run_digimon_export(full_pipeline_db, tmp_path / "out_b6a")

        all_urls: list[str] = []
        for line in entities_path.read_text().splitlines():
            if not line.strip():
                continue
            row = json.loads(line)
            raw = row.get("source_urls", "[]")
            all_urls.extend(json.loads(raw) if isinstance(raw, str) else raw)

        assert "https://example.com/article1" in all_urls, (
            "Source URL must flow research_v3 finding → ClaimRecord.source_urls → "
            "import_shared_claims → source_metadata_json → DIGIMON entities.jsonl"
        )

    def test_entity_count_matches_memo_entities(
        self, full_pipeline_db: Path
    ) -> None:
        from onto_canon6.adapters.digimon_export import export_for_digimon
        from onto_canon6.core.graph_service import CanonicalGraphService
        from onto_canon6.pipeline.service import ReviewService

        bundle = export_for_digimon(
            graph_service=CanonicalGraphService(db_path=full_pipeline_db),
            review_service=ReviewService(db_path=full_pipeline_db),
        )
        # Memo has 2 entities: Company A and Agency B
        assert len(bundle.entities) >= 2

    def test_relationships_link_known_entities(
        self, full_pipeline_db: Path, tmp_path: Path
    ) -> None:
        entities_path, rels_path = _run_digimon_export(
            full_pipeline_db, tmp_path / "out_b6c"
        )

        entity_names = {
            json.loads(line)["entity_name"]
            for line in entities_path.read_text().splitlines()
            if line.strip()
        }

        orphaned = []
        for line in rels_path.read_text().splitlines():
            if not line.strip():
                continue
            row = json.loads(line)
            for key in ("src_id", "tgt_id"):
                val = row.get(key, "")
                if val and val not in entity_names:
                    orphaned.append(f"{key}={val!r}")

        assert not orphaned, f"Relationships reference unknown entities: {orphaned}"


# ─── B7: Failure mode tests ───────────────────────────────────────────────────

class TestB7FailureModes:
    """Boundary 7: Contract violations must fail loudly, not silently."""

    def test_malformed_memo_raises(self, tmp_path: Path) -> None:
        shared_export = load_shared_export()
        bad_memo = tmp_path / "bad.yaml"
        bad_memo.write_text(yaml.dump({
            "question": "q",
            "key_findings": "this should be a list, not a string",
        }))
        with pytest.raises((ValueError, TypeError)):
            shared_export.load_memo_claims(bad_memo)

    def test_claim_with_invalid_confidence_range(self) -> None:
        from epistemic_contracts import ClaimRecord, ConfidenceScore
        import pydantic

        with pytest.raises((pydantic.ValidationError, ValueError)):
            ClaimRecord(
                id="bad-conf",
                statement="Bad confidence.",
                claim_type="assertion",
                status="unverified",
                confidence=ConfidenceScore(score=1.5, source="investigation"),
                source_system="test",
            )

    def test_claim_with_unknown_source_system_accepted(self) -> None:
        """source_system is a free-form string — unknown values must be accepted."""
        from epistemic_contracts import ClaimRecord, ConfidenceScore
        claim = ClaimRecord(
            id="unknown-sys",
            statement="From an unknown system.",
            claim_type="assertion",
            status="unverified",
            confidence=ConfidenceScore(score=0.5, source="investigation"),
            source_system="my_custom_tool_v99",
        )
        assert claim.source_system == "my_custom_tool_v99"

    def test_import_shared_claims_with_empty_statement_does_not_crash(self) -> None:
        """Empty statement must not crash the import pipeline."""
        from epistemic_contracts import ClaimRecord, ConfidenceScore
        from onto_canon6.adapters.grounded_research_import import import_shared_claims

        claim = ClaimRecord(
            id="empty-stmt",
            statement="",
            claim_type="assertion",
            status="unverified",
            confidence=ConfidenceScore(score=0.5, source="investigation"),
            source_system="test",
        )
        candidates = import_shared_claims([claim])
        if candidates:
            assert candidates[0].claim_text == ""
