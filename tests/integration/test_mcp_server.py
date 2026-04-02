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
    "canon6_list_entities",
    "canon6_search_entities",
    "canon6_get_entity",
    "canon6_list_promoted_assertions",
    "canon6_search_promoted_assertions",
    "canon6_get_promoted_assertion",
    "canon6_get_evidence",
}

_WHYGAME_FIXTURE_ADAPTER = TypeAdapter(list[dict[str, object]])


def _load_fixture() -> list[dict[str, object]]:
    """Load the shared WhyGame relationship fixture used for MCP tests."""

    fixture_path = Path("tests/fixtures/whygame_relationship_facts.json")
    return _WHYGAME_FIXTURE_ADAPTER.validate_json(fixture_path.read_text(encoding="utf-8"))


def test_phase14_mcp_tools_are_registered() -> None:
    """The thin MCP server should register the expected small tool set."""
    import asyncio
    import inspect

    get_tools = getattr(mcp_server.mcp, "get_tools", None)
    if get_tools is None:
        tool_manager = getattr(mcp_server.mcp, "_tool_manager", None)
        get_tools = getattr(tool_manager, "get_tools", None)
    assert get_tools is not None, "FastMCP surface no longer exposes a tool registry API"

    tools = get_tools()
    if inspect.isawaitable(tools):
        tools = asyncio.run(tools)
    if isinstance(tools, dict):
        registered = {tool.name for tool in tools.values()}
    else:
        registered = {tool.name for tool in tools}
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


def test_mcp_query_surface_tools_cover_first_read_only_slice(tmp_path: Path) -> None:
    """The MCP surface should expose browse, search, and lookup query operations."""

    review_db_path = tmp_path / "review.sqlite3"
    _first_assertion_id, second_assertion_id = _seed_query_state(review_db_path)

    listed_entities = mcp_server.canon6_list_entities(
        entity_type="oc:person",
        review_db_path=str(review_db_path),
    )
    assert [result["entity_id"] for result in listed_entities] == [
        "ent:person:admiral_eric_olson",
        "ent:person:eric_olson",
    ]

    entity_results = mcp_server.canon6_search_entities(
        query="Admiral Eric Olson",
        review_db_path=str(review_db_path),
    )
    assert entity_results[0]["entity_id"] == "ent:person:admiral_eric_olson"
    assert entity_results[0]["match_reason"] == "alias_exact"

    entity_detail = mcp_server.canon6_get_entity(
        entity_id="ent:person:eric_olson",
        review_db_path=str(review_db_path),
    )
    assert entity_detail["identity_bundle"]["identity"]["display_label"] == "Eric Olson"
    assert len(entity_detail["linked_assertions"]) == 2

    listed_assertions = mcp_server.canon6_list_promoted_assertions(
        source_ref="notes/admiral_eric_olson.txt",
        review_db_path=str(review_db_path),
    )
    assert [result["assertion_id"] for result in listed_assertions] == [second_assertion_id]
    assert listed_assertions[0]["source_kind"] == "text_file"

    assertion_results = mcp_server.canon6_search_promoted_assertions(
        entity_id="ent:person:admiral_eric_olson",
        source_kind="text_file",
        review_db_path=str(review_db_path),
    )
    assert [result["assertion_id"] for result in assertion_results] == [second_assertion_id]

    assertion_detail = mcp_server.canon6_get_promoted_assertion(
        assertion_id=second_assertion_id,
        review_db_path=str(review_db_path),
    )
    assert assertion_detail["promotion"]["assertion"]["assertion_id"] == second_assertion_id
    assert assertion_detail["epistemic_report"]["epistemic_status"] == "active"

    evidence = mcp_server.canon6_get_evidence(
        assertion_id=second_assertion_id,
        review_db_path=str(review_db_path),
    )
    assert evidence["evidence_spans"][0]["text"] == "Admiral Eric Olson"
    assert evidence["source_artifact"]["source_ref"] == "notes/admiral_eric_olson.txt"


def _seed_query_state(review_db_path: Path) -> tuple[str, str]:
    """Seed a small promoted-state slice for MCP query tests."""

    from onto_canon6.artifacts import ArtifactLineageService
    from onto_canon6.core import CanonicalGraphService, IdentityService
    from onto_canon6.pipeline import ReviewService

    review_service = ReviewService(
        db_path=review_db_path,
        overlay_root=review_db_path.parent / "ontology_overlays",
        default_acceptance_policy="record_only",
    )
    first_assertion_id = _submit_accept_and_promote(
        review_service,
        predicate="oc:hold_command_role",
        person_entity_id="ent:person:eric_olson",
        person_name="Eric Olson",
        source_ref="notes/eric_olson.txt",
        claim_text="Eric Olson held the commander role at USSOCOM.",
    )
    second_assertion_id = _submit_accept_and_promote(
        review_service,
        predicate="oc:hold_command_role",
        person_entity_id="ent:person:admiral_eric_olson",
        person_name="Admiral Eric Olson",
        source_ref="notes/admiral_eric_olson.txt",
        claim_text="Admiral Eric Olson held the commander role at USSOCOM.",
    )

    identity_service = IdentityService(db_path=review_db_path)
    created = identity_service.create_identity_for_entity(
        entity_id="ent:person:eric_olson",
        created_by="analyst:identity",
        display_label="Eric Olson",
    )
    identity_service.attach_entity_alias(
        identity_id=created.identity.identity_id,
        entity_id="ent:person:admiral_eric_olson",
        attached_by="analyst:identity",
    )
    identity_service.attach_external_reference(
        identity_id=created.identity.identity_id,
        provider="analyst_registry",
        external_id="eric-olson-profile",
        attached_by="analyst:identity",
        reference_label="Eric Olson",
    )

    graph_service = CanonicalGraphService(db_path=review_db_path)
    artifact_service = ArtifactLineageService(db_path=review_db_path)
    artifact = artifact_service.register_artifact(
        artifact_kind="source",
        uri="notes/eric_olson.txt",
        label="Eric Olson note",
    )
    first_candidate_id = graph_service.get_promoted_assertion(
        assertion_id=first_assertion_id
    ).source_candidate_id
    artifact_service.link_candidate_artifact(
        candidate_id=first_candidate_id,
        artifact_id=artifact.artifact_id,
        support_kind="quoted_from",
        reference_detail="opening sentence",
    )
    return first_assertion_id, second_assertion_id


def _submit_accept_and_promote(
    review_service: object,
    *,
    predicate: str,
    person_entity_id: str,
    person_name: str,
    source_ref: str,
    claim_text: str,
) -> str:
    """Seed one accepted and promoted assertion with explicit entity names."""

    from onto_canon6.core import CanonicalGraphService

    source_text = f"{person_name} served as commander of USSOCOM."
    submission = review_service.submit_candidate_assertion(
        payload={
            "predicate": predicate,
            "roles": {
                "commander": [
                    {
                        "entity_id": person_entity_id,
                        "entity_type": "oc:person",
                        "name": person_name,
                    }
                ],
                "organization": [
                    {
                        "entity_id": "ent:org:ussocom",
                        "entity_type": "oc:organization",
                        "name": "USSOCOM",
                    }
                ],
            },
        },
        profile_id="default",
        profile_version="1.0.0",
        submitted_by="analyst:query-seed",
        source_kind="text_file",
        source_ref=source_ref,
        source_text=source_text,
        claim_text=claim_text,
        evidence_spans=(
            {
                "start_char": 0,
                "end_char": len(person_name),
                "text": person_name,
            },
        ),
    )
    accepted = review_service.review_candidate(
        candidate_id=submission.candidate.candidate_id,
        decision="accepted",
        actor_id="analyst:reviewer",
    )
    promotion = CanonicalGraphService(db_path=review_service.store.db_path).promote_candidate(
        candidate_id=accepted.candidate_id,
        promoted_by="analyst:graph-promoter",
    )
    return promotion.assertion.assertion_id
