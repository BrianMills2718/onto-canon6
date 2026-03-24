"""CLI integration proof for the local DoDAF minimal second-pack slice."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from onto_canon6 import cli as cli_module
from onto_canon6.pipeline import (
    CandidateAssertionImport,
    EvidenceSpan,
    ProfileRef,
    ReviewService,
    SourceArtifactRef,
)


class _FakeDodafMixedExtractionService:
    """Deterministic DoDAF extractor stand-in for CLI integration testing.

    The second-pack CLI proof should not depend on a live model call. This
    fake still drives the real review, proposal, and overlay services so the
    test proves the pack/profile/runtime boundaries rather than only a mock.
    """

    def __init__(
        self,
        *,
        review_service: ReviewService,
        selection_task: str | None = None,
    ) -> None:
        """Capture the real review service used by the CLI handler."""

        self._review_service = review_service
        self.selection_task = selection_task

    def extract_and_submit(
        self,
        *,
        source_text: str,
        profile_id: str,
        profile_version: str,
        submitted_by: str,
        source_ref: str,
        source_kind: str = "text_file",
        source_label: str | None = None,
        source_metadata: dict[str, object] | None = None,
        extraction_goal: str | None = None,
    ) -> tuple[object, ...]:
        """Submit one deterministic mixed-mode DoDAF candidate through the real flow."""

        del source_metadata, extraction_goal
        phrase = "supports activity"
        start_char = source_text.index(phrase)
        end_char = start_char + len(phrase)
        candidate_import = CandidateAssertionImport(
            profile=ProfileRef(profile_id=profile_id, profile_version=profile_version),
            payload={
                "predicate": "dodaf:operational_node_supports_activity",
                "roles": {
                    "source": [{"kind": "value", "value_kind": "string", "value": "Node A"}],
                    "target": [{"kind": "value", "value_kind": "string", "value": "Activity B"}],
                },
            },
            submitted_by=submitted_by,
            source_artifact=SourceArtifactRef(
                source_kind=source_kind,
                source_ref=source_ref,
                source_label=source_label,
                source_metadata={},
                content_text=source_text,
            ),
            evidence_spans=(
                EvidenceSpan(start_char=start_char, end_char=end_char, text=phrase),
            ),
            claim_text="Node A supports activity B.",
        )
        return (
            self._review_service.submit_candidate_import(candidate_import=candidate_import),
        )


def test_cli_dodaf_minimal_mixed_flow_json_output(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """The CLI should drive the same proposal workflow for the local DoDAF pack."""

    source_path = tmp_path / "dodaf_source.txt"
    source_path.write_text("Node A supports activity B through the exchange plan.", encoding="utf-8")
    review_db_path = tmp_path / "review.sqlite3"
    overlay_root = tmp_path / "ontology_overlays"

    # mock-ok: the test must avoid a live llm_client network call while still
    # proving the real DoDAF review/proposal/overlay workflow end to end.
    monkeypatch.setattr(cli_module, "TextExtractionService", _FakeDodafMixedExtractionService)

    exit_code = cli_module.main(
        [
            "extract-text",
            "--input",
            str(source_path),
            "--profile-id",
            "dodaf_minimal_mixed",
            "--profile-version",
            "0.1.0",
            "--submitted-by",
            "analyst:cli-dodaf",
            "--review-db-path",
            str(review_db_path),
            "--overlay-root",
            str(overlay_root),
            "--output",
            "json",
        ]
    )

    assert exit_code == 0
    extract_output = json.loads(capsys.readouterr().out)
    assert len(extract_output) == 1
    candidate_id = str(extract_output[0]["candidate"]["candidate_id"])
    proposal_id = str(extract_output[0]["proposals"][0]["proposal_id"])
    assert extract_output[0]["candidate"]["validation_status"] == "needs_review"
    assert extract_output[0]["proposals"][0]["profile"]["profile_id"] == "dodaf_minimal_mixed"

    exit_code = cli_module.main(
        [
            "review-candidate",
            "--candidate-id",
            candidate_id,
            "--decision",
            "accepted",
            "--actor-id",
            "analyst:reviewer",
            "--review-db-path",
            str(review_db_path),
            "--output",
            "json",
        ]
    )
    assert exit_code == 0
    candidate_output = json.loads(capsys.readouterr().out)
    assert candidate_output["review_status"] == "accepted"

    exit_code = cli_module.main(
        [
            "review-proposal",
            "--proposal-id",
            proposal_id,
            "--decision",
            "accepted",
            "--actor-id",
            "analyst:reviewer",
            "--acceptance-policy",
            "apply_to_overlay",
            "--review-db-path",
            str(review_db_path),
            "--output",
            "json",
        ]
    )
    assert exit_code == 0
    proposal_output = json.loads(capsys.readouterr().out)
    assert proposal_output["status"] == "accepted"
    assert proposal_output["target_pack"]["pack_id"] == "dodaf_minimal__overlay"

    exit_code = cli_module.main(
        [
            "apply-overlay",
            "--proposal-id",
            proposal_id,
            "--actor-id",
            "analyst:reviewer",
            "--review-db-path",
            str(review_db_path),
            "--overlay-root",
            str(overlay_root),
            "--output",
            "json",
        ]
    )
    assert exit_code == 0
    overlay_output = json.loads(capsys.readouterr().out)
    assert overlay_output["overlay_pack"]["pack_id"] == "dodaf_minimal__overlay"
    assert Path(overlay_output["content_path"]).exists()
