"""Tests for the Phase 13 semantic canonicalization and repair slice."""

from __future__ import annotations

import json
from pathlib import Path
import sqlite3

import pytest

from onto_canon6.core import (
    CanonicalGraphService,
    SemanticCanonicalizationConflictError,
    SemanticCanonicalizationService,
)
from onto_canon6.pipeline import ReviewService
from onto_canon6.surfaces import SemanticCanonicalizationReportService


def _seed_review_service(tmp_path: Path) -> ReviewService:
    """Create one isolated review service for semantic canonicalization tests."""

    review_db_path = tmp_path / "review.sqlite3"
    overlay_root = tmp_path / "ontology_overlays"
    return ReviewService(
        db_path=review_db_path,
        overlay_root=overlay_root,
        default_acceptance_policy="record_only",
    )


def _submit_and_promote_dodaf_candidate(review_service: ReviewService) -> str:
    """Submit, accept, and promote one canonical DoDAF minimal candidate."""

    submission = review_service.submit_candidate_assertion(
        payload={
            "predicate": "dodaf:operational_node_exchanges_information",
            "roles": {
                "source_node": [
                    {
                        "entity_id": "ent:node:source",
                        "entity_type": "dm2:OperationalNode",
                    }
                ],
                "target_node": [
                    {
                        "entity_id": "ent:node:target",
                        "entity_type": "dm2:OperationalNode",
                    }
                ],
                "information_element": [
                    {
                        "entity_id": "ent:info:message",
                        "entity_type": "dm2:InformationElement",
                    }
                ],
            },
        },
        profile_id="dodaf_minimal_strict",
        profile_version="0.1.0",
        submitted_by="analyst:semantic-seed",
        source_kind="text_file",
        source_ref="notes/dodaf_semantic.txt",
        source_text="Node A exchanges Message M with Node B.",
        claim_text="Node A exchanges Message M with Node B.",
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


def _force_legacy_alias_state(db_path: Path, *, assertion_id: str) -> None:
    """Mutate one promoted assertion into a legacy noncanonical alias form."""

    normalized_body = {
        "predicate": "OperationalNodeExchangesInformation",
        "roles": {
            "source": [
                {
                    "kind": "entity",
                    "entity_id": "ent:node:source",
                    "entity_type": "dm2:OperationalNode",
                }
            ],
            "target": [
                {
                    "kind": "entity",
                    "entity_id": "ent:node:target",
                    "entity_type": "dm2:OperationalNode",
                }
            ],
            "information": [
                {
                    "kind": "entity",
                    "entity_id": "ent:info:message",
                    "entity_type": "dm2:InformationElement",
                }
            ],
        },
    }
    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        conn.execute(
            """
            UPDATE promoted_graph_assertions
            SET predicate = ?,
                normalized_body_json = ?
            WHERE assertion_id = ?
            """,
            (
                "OperationalNodeExchangesInformation",
                json.dumps(normalized_body, sort_keys=True),
                assertion_id,
            ),
        )
        conn.execute(
            """
            UPDATE promoted_graph_role_fillers
            SET role_id = CASE role_id
                WHEN 'source_node' THEN 'source'
                WHEN 'target_node' THEN 'target'
                WHEN 'information_element' THEN 'information'
                ELSE role_id
            END
            WHERE assertion_id = ?
            """,
            (assertion_id,),
        )


def test_recanonicalize_promoted_assertion_rewrites_alias_predicate_and_roles(
    tmp_path: Path,
) -> None:
    """Legacy alias ids should rewrite to the pack-canonical predicate and roles."""

    review_service = _seed_review_service(tmp_path)
    assertion_id = _submit_and_promote_dodaf_candidate(review_service)
    _force_legacy_alias_state(review_service.store.db_path, assertion_id=assertion_id)
    semantic_service = SemanticCanonicalizationService(db_path=review_service.store.db_path)

    result = semantic_service.recanonicalize_promoted_assertion(
        assertion_id=assertion_id,
        actor_id="analyst:semantic-repair",
        reason="Normalize legacy DoDAF alias ids.",
    )

    assert result.status == "rewritten"
    assert result.assertion.predicate == "dodaf:operational_node_exchanges_information"
    assert {filler.role_id for filler in result.role_fillers} == {
        "source_node",
        "target_node",
        "information_element",
    }
    assert result.event is not None
    assert result.event.before_predicate == "OperationalNodeExchangesInformation"
    assert result.event.after_predicate == "dodaf:operational_node_exchanges_information"
    assert result.validation_outcome.hard_errors == ()

    report = SemanticCanonicalizationReportService(
        semantic_service=semantic_service
    ).build_report()
    assert report.summary.total_recanonicalization_events == 1
    assert report.summary.total_rewritten_assertions == 1
    assert report.assertion_bundles[0].assertion.assertion_id == assertion_id
    assert report.assertion_bundles[0].latest_event is not None


def test_recanonicalize_promoted_assertion_returns_typed_noop_for_canonical_state(
    tmp_path: Path,
) -> None:
    """Already-canonical promoted assertions should not invent repair events."""

    review_service = _seed_review_service(tmp_path)
    assertion_id = _submit_and_promote_dodaf_candidate(review_service)
    semantic_service = SemanticCanonicalizationService(db_path=review_service.store.db_path)

    result = semantic_service.recanonicalize_promoted_assertion(
        assertion_id=assertion_id,
        actor_id="analyst:semantic-repair",
        reason="No-op check.",
    )

    assert result.status == "already_canonical"
    assert result.event is None
    assert result.assertion.assertion_id == assertion_id
    assert semantic_service.list_recanonicalization_events() == []


def test_recanonicalize_promoted_assertion_fails_loud_when_mapping_is_unknown(
    tmp_path: Path,
) -> None:
    """Unknown predicate aliases should fail instead of silently persisting bad state."""

    review_service = _seed_review_service(tmp_path)
    assertion_id = _submit_and_promote_dodaf_candidate(review_service)
    with sqlite3.connect(review_service.store.db_path) as conn:
        conn.execute(
            """
            UPDATE promoted_graph_assertions
            SET predicate = ?,
                normalized_body_json = ?
            WHERE assertion_id = ?
            """,
            (
                "LegacyUnknownPredicate",
                json.dumps(
                    {
                        "predicate": "LegacyUnknownPredicate",
                        "roles": {
                            "source": [
                                {
                                    "kind": "entity",
                                    "entity_id": "ent:node:source",
                                    "entity_type": "dm2:OperationalNode",
                                }
                            ],
                            "target": [
                                {
                                    "kind": "entity",
                                    "entity_id": "ent:node:target",
                                    "entity_type": "dm2:OperationalNode",
                                }
                            ],
                            "information": [
                                {
                                    "kind": "entity",
                                    "entity_id": "ent:info:message",
                                    "entity_type": "dm2:InformationElement",
                                }
                            ],
                        },
                    },
                    sort_keys=True,
                ),
                assertion_id,
            ),
        )
        conn.execute(
            """
            UPDATE promoted_graph_role_fillers
            SET role_id = CASE role_id
                WHEN 'source_node' THEN 'source'
                WHEN 'target_node' THEN 'target'
                WHEN 'information_element' THEN 'information'
                ELSE role_id
            END
            WHERE assertion_id = ?
            """,
            (assertion_id,),
        )
    semantic_service = SemanticCanonicalizationService(db_path=review_service.store.db_path)

    with pytest.raises(
        SemanticCanonicalizationConflictError,
        match="cannot canonicalize predicate",
    ):
        semantic_service.recanonicalize_promoted_assertion(
            assertion_id=assertion_id,
            actor_id="analyst:semantic-repair",
            reason="Should fail loudly.",
        )
