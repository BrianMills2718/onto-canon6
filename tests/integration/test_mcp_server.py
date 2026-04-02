"""Integration tests for the thin Phase 14 MCP surface."""

from __future__ import annotations

from pathlib import Path

from pydantic import TypeAdapter

from onto_canon6 import mcp_server


EXPECTED_TOOLS = {
    "canon6_import_whygame_relationships",
    "canon6_list_candidates",
    "canon6_list_proposals",
    "canon6_review_candidate",
    "canon6_review_proposal",
    "canon6_apply_overlay",
    "canon6_promote_candidate",
    "canon6_export_governed_bundle",
}

_WHYGAME_FIXTURE_ADAPTER = TypeAdapter(list[dict[str, object]])


def _load_fixture() -> list[dict[str, object]]:
    """Load the shared WhyGame relationship fixture used for MCP tests."""

    fixture_path = Path("tests/fixtures/whygame_relationship_facts.json")
    return _WHYGAME_FIXTURE_ADAPTER.validate_json(fixture_path.read_text(encoding="utf-8"))


def test_phase14_mcp_tools_are_registered() -> None:
    """The thin MCP server should register the expected small tool set."""
    import asyncio

    tools_dict = asyncio.run(mcp_server.mcp.get_tools())
    registered = set(tools_dict.keys())
    assert EXPECTED_TOOLS.issubset(registered)
    assert len(registered & EXPECTED_TOOLS) == len(EXPECTED_TOOLS)


def test_mcp_whygame_import_review_and_bundle_flow(tmp_path: Path) -> None:
    """The MCP surface should drive WhyGame import and governed export end to end."""

    review_db_path = tmp_path / "review.sqlite3"

    import_result = mcp_server.canon6_import_whygame_relationships(
        facts=_load_fixture()[:1],
        submitted_by="analyst:mcp-test",
        source_ref="whygame://fixture/mcp",
        source_label="WhyGame MCP fixture",
        artifact_uri="artifact://whygame/mcp",
        review_db_path=str(review_db_path),
    )

    candidate_id = str(import_result["submissions"][0]["candidate"]["candidate_id"])
    assert import_result["artifact"]["artifact_kind"] == "analysis_result"
    assert import_result["submissions"][0]["candidate"]["validation_status"] == "valid"

    listed_candidates = mcp_server.canon6_list_candidates(review_db_path=str(review_db_path))
    assert [candidate["candidate_id"] for candidate in listed_candidates] == [candidate_id]

    reviewed_candidate = mcp_server.canon6_review_candidate(
        candidate_id=candidate_id,
        decision="accepted",
        actor_id="analyst:reviewer",
        review_db_path=str(review_db_path),
    )
    assert reviewed_candidate["review_status"] == "accepted"

    promoted = mcp_server.canon6_promote_candidate(
        candidate_id=candidate_id,
        actor_id="analyst:reviewer",
        review_db_path=str(review_db_path),
    )
    assert promoted["assertion"]["source_candidate_id"] == candidate_id

    bundle = mcp_server.canon6_export_governed_bundle(
        candidate_ids=[candidate_id],
        review_db_path=str(review_db_path),
    )
    assert bundle["summary"]["total_candidates"] == 1
    assert bundle["candidate_bundles"][0]["candidate"]["candidate_id"] == candidate_id
    assert bundle["candidate_bundles"][0]["artifacts"][0]["uri"] == "artifact://whygame/mcp"
