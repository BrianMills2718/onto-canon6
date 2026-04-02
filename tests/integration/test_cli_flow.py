"""Integration tests for the Phase 6 CLI surface."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
from typing import Literal

import pytest

from onto_canon6 import cli as cli_module
from onto_canon6.pipeline import CandidateAssertionImport, EvidenceSpan, ProfileRef, ReviewService, SourceArtifactRef


class _FakeTextExtractionService:
    """Deterministic stand-in for the remote extraction boundary.

    The CLI integration flow needs to prove the wired command surface without
    depending on a live `llm_client` network call. This fake service still uses
    the real `ReviewService` so proposal generation, persistence, review
    transitions, and overlay application all remain real.
    """

    def __init__(
        self,
        *,
        review_service: ReviewService,
        selection_task: str | None = None,
        prompt_template: Path | None = None,
        prompt_ref: str | None = None,
        max_candidates_per_call: int | None = None,
        max_evidence_spans_per_candidate: int | None = None,
    ) -> None:
        """Capture the real review service used by the CLI handler."""

        self._review_service = review_service
        self.selection_task = selection_task
        self.prompt_template = prompt_template
        self.prompt_ref = prompt_ref
        self.max_candidates_per_call = max_candidates_per_call
        self.max_evidence_spans_per_candidate = max_evidence_spans_per_candidate

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
        """Submit one deterministic mixed-mode candidate through the real review flow."""

        del source_metadata
        phrase = "aligned messaging"
        start_char = source_text.index(phrase)
        end_char = start_char + len(phrase)
        candidate_import = CandidateAssertionImport(
            profile=ProfileRef(profile_id=profile_id, profile_version=profile_version),
            payload={
                "predicate": "oc:signals_alignment",
                "roles": {
                    "subject": [
                        {
                            "kind": "value",
                            "value_kind": "string",
                            "value": "Campaign Alpha",
                        }
                    ],
                    "object": [
                        {
                            "kind": "value",
                            "value_kind": "string",
                            "value": phrase,
                        }
                    ],
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
                EvidenceSpan(
                    start_char=start_char,
                    end_char=end_char,
                    text=phrase,
                ),
            ),
            claim_text="Campaign Alpha used aligned messaging.",
        )
        return (self._review_service.submit_candidate_import(candidate_import=candidate_import),)


def test_cli_help_works_through_module_entrypoint() -> None:
    """The package entrypoint should expose the CLI help text."""

    result = subprocess.run(
        [sys.executable, "-m", "onto_canon6", "--help"],
        capture_output=True,
        check=False,
        text=True,
    )

    assert result.returncode == 0
    assert "extract-text" in result.stdout
    assert "review-candidate" in result.stdout
    assert "export-governed-bundle" in result.stdout


def test_cli_extract_review_and_apply_flow_json_output(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """The CLI should drive the reviewed proposal flow end to end."""

    source_path = tmp_path / "source.txt"
    source_path.write_text(
        "Campaign Alpha used aligned messaging across channels.",
        encoding="utf-8",
    )
    review_db_path = tmp_path / "review.sqlite3"
    overlay_root = tmp_path / "ontology_overlays"

    # mock-ok: this test needs a deterministic stand-in for the remote
    # llm_client extraction boundary, but the persisted review/proposal/overlay
    # flow remains real.
    monkeypatch.setattr(cli_module, "TextExtractionService", _FakeTextExtractionService)

    exit_code = cli_module.main(
        [
            "extract-text",
            "--input",
            str(source_path),
            "--profile-id",
            "psyop_seed",
            "--profile-version",
            "0.1.0",
            "--submitted-by",
            "analyst:cli-test",
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
    assert extract_output[0]["proposals"][0]["status"] == "pending"

    exit_code = cli_module.main(
        [
            "list-candidates",
            "--review-db-path",
            str(review_db_path),
            "--output",
            "json",
        ]
    )
    assert exit_code == 0
    candidates_output = json.loads(capsys.readouterr().out)
    assert len(candidates_output) == 1
    assert candidates_output[0]["candidate_id"] == candidate_id

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
    reviewed_candidate = json.loads(capsys.readouterr().out)
    assert reviewed_candidate["review_status"] == "accepted"

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
    reviewed_proposal = json.loads(capsys.readouterr().out)
    assert reviewed_proposal["status"] == "accepted"
    assert reviewed_proposal["application_status"] == "pending_overlay_apply"

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
    assert overlay_output["proposal_id"] == proposal_id
    assert Path(overlay_output["content_path"]).exists()

    exit_code = cli_module.main(
        [
            "list-proposals",
            "--review-db-path",
            str(review_db_path),
            "--status",
            "accepted",
            "--output",
            "json",
        ]
    )
    assert exit_code == 0
    proposals_output = json.loads(capsys.readouterr().out)
    assert len(proposals_output) == 1
    assert proposals_output[0]["proposal_id"] == proposal_id
    assert proposals_output[0]["overlay_application"] is not None

    exit_code = cli_module.main(
        [
            "export-governed-bundle",
            "--review-db-path",
            str(review_db_path),
            "--output",
            "json",
        ]
    )
    assert exit_code == 0
    bundle_output = json.loads(capsys.readouterr().out)
    assert bundle_output["summary"]["total_candidates"] == 1
    assert bundle_output["summary"]["total_linked_proposals"] == 1
    assert bundle_output["candidate_bundles"][0]["candidate"]["candidate_id"] == candidate_id
    assert bundle_output["candidate_bundles"][0]["linked_proposals"][0]["proposal_id"] == proposal_id
    assert (
        bundle_output["candidate_bundles"][0]["linked_overlay_applications"][0]["proposal_id"]
        == proposal_id
    )
    assert bundle_output["candidate_bundles"][0]["epistemic_status"] == "active"


def test_cli_export_chunk_transfer_report_json_output(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """The CLI should export one reviewed chunk transfer report."""

    review_db_path = tmp_path / "review.sqlite3"
    review_service = ReviewService(
        db_path=review_db_path,
        permissive_review=True,
    )
    source_ref = "chunk://cli-positive"
    for predicate in (
        "oc:predicate_a",
        "oc:predicate_b",
        "oc:predicate_c",
        "oc:predicate_d",
        "oc:predicate_e",
    ):
        submission = review_service.submit_candidate_assertion(
            payload={"predicate": predicate, "roles": {}},
            profile_id="default",
            profile_version="1.0.0",
            submitted_by="analyst:test",
            source_kind="text_file",
            source_ref=source_ref,
            source_label="cli positive chunk",
            source_text=f"{predicate} evidence text",
        )
        decision: Literal["accepted", "rejected"] = (
            "accepted" if predicate != "oc:predicate_e" else "rejected"
        )
        review_service.review_candidate(
            candidate_id=submission.candidate.candidate_id,
            decision=decision,
            actor_id="analyst:reviewer",
        )

    exit_code = cli_module.main(
        [
            "export-chunk-transfer-report",
            "--review-db-path",
            str(review_db_path),
            "--source-ref",
            source_ref,
            "--prompt-ref",
            "onto_canon6.extraction.text_to_candidate_assertions_compact_v2@2",
            "--selection-task",
            "budget_extraction",
            "--output",
            "json",
        ]
    )

    assert exit_code == 0
    report = json.loads(capsys.readouterr().out)
    assert report["source_ref"] == source_ref
    assert report["prompt_ref"] == "onto_canon6.extraction.text_to_candidate_assertions_compact_v2@2"
    assert report["selection_task"] == "budget_extraction"
    assert report["summary"]["verdict"] == "positive"
    assert report["summary"]["accepted_candidates"] == 4
    assert report["summary"]["rejected_candidates"] == 1


def test_cli_extract_text_forwards_selection_task_override(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """The CLI should forward a task override into the extraction service."""

    source_path = tmp_path / "source.txt"
    source_path.write_text(
        "Campaign Alpha used aligned messaging across channels.",
        encoding="utf-8",
    )
    review_db_path = tmp_path / "review.sqlite3"
    overlay_root = tmp_path / "ontology_overlays"
    recorded: dict[str, object] = {}

    class _RecordingExtractionService(_FakeTextExtractionService):
        """Capture the forwarded selection-task override."""

        def __init__(
            self,
            *,
            review_service: ReviewService,
            selection_task: str | None = None,
            prompt_template: Path | None = None,
            prompt_ref: str | None = None,
            max_candidates_per_call: int | None = None,
            max_evidence_spans_per_candidate: int | None = None,
        ) -> None:
            recorded["selection_task"] = selection_task
            super().__init__(
                review_service=review_service,
                selection_task=selection_task,
                prompt_template=prompt_template,
                prompt_ref=prompt_ref,
                max_candidates_per_call=max_candidates_per_call,
                max_evidence_spans_per_candidate=max_evidence_spans_per_candidate,
            )

    # mock-ok: this test only verifies CLI wiring of the override.
    monkeypatch.setattr(cli_module, "TextExtractionService", _RecordingExtractionService)

    exit_code = cli_module.main(
        [
            "extract-text",
            "--input",
            str(source_path),
            "--profile-id",
            "psyop_seed",
            "--profile-version",
            "0.1.0",
            "--submitted-by",
            "analyst:cli-test",
            "--review-db-path",
            str(review_db_path),
            "--overlay-root",
            str(overlay_root),
            "--selection-task",
            "budget_extraction",
            "--output",
            "json",
        ]
    )

    assert exit_code == 0
    _ = json.loads(capsys.readouterr().out)
    assert recorded["selection_task"] == "budget_extraction"


def test_cli_extract_text_forwards_prompt_override_pair(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """The CLI should forward bounded prompt overrides into the extraction service."""

    source_path = tmp_path / "source.txt"
    source_path.write_text(
        "Campaign Alpha used aligned messaging across channels.",
        encoding="utf-8",
    )
    prompt_path = tmp_path / "override_prompt.yaml"
    prompt_path.write_text(
        "\n".join(
            [
                'name: test_override',
                'version: "1.0"',
                'description: "test"',
                "messages:",
                "  - role: system",
                "    content: |",
                "      Override prompt.",
                "  - role: user",
                "    content: |",
                "      Source: {{ source_text }}",
            ]
        ),
        encoding="utf-8",
    )
    review_db_path = tmp_path / "review.sqlite3"
    overlay_root = tmp_path / "ontology_overlays"
    recorded: dict[str, object] = {}

    class _RecordingExtractionService(_FakeTextExtractionService):
        """Capture the forwarded prompt override pair."""

        def __init__(
            self,
            *,
            review_service: ReviewService,
            selection_task: str | None = None,
            prompt_template: Path | None = None,
            prompt_ref: str | None = None,
            max_candidates_per_call: int | None = None,
            max_evidence_spans_per_candidate: int | None = None,
        ) -> None:
            recorded["prompt_template"] = prompt_template
            recorded["prompt_ref"] = prompt_ref
            recorded["max_candidates_per_call"] = max_candidates_per_call
            recorded["max_evidence_spans_per_candidate"] = max_evidence_spans_per_candidate
            super().__init__(
                review_service=review_service,
                selection_task=selection_task,
                prompt_template=prompt_template,
                prompt_ref=prompt_ref,
                max_candidates_per_call=max_candidates_per_call,
                max_evidence_spans_per_candidate=max_evidence_spans_per_candidate,
            )

    monkeypatch.setattr(cli_module, "TextExtractionService", _RecordingExtractionService)

    exit_code = cli_module.main(
        [
            "extract-text",
            "--input",
            str(source_path),
            "--profile-id",
            "psyop_seed",
            "--profile-version",
            "0.1.0",
            "--submitted-by",
            "analyst:cli-test",
            "--review-db-path",
            str(review_db_path),
            "--overlay-root",
            str(overlay_root),
            "--prompt-template",
            str(prompt_path),
            "--prompt-ref",
            "onto_canon6.extraction.test_override@1",
            "--max-candidates-per-call",
            "1",
            "--max-evidence-spans-per-candidate",
            "1",
            "--output",
            "json",
        ]
    )

    assert exit_code == 0
    _ = json.loads(capsys.readouterr().out)
    assert recorded["prompt_template"] == prompt_path
    assert recorded["prompt_ref"] == "onto_canon6.extraction.test_override@1"
    assert recorded["max_candidates_per_call"] == 1
    assert recorded["max_evidence_spans_per_candidate"] == 1


def test_cli_fails_loud_on_invalid_candidate_acceptance(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """The CLI should fail loudly on an invalid candidate review transition."""

    review_db_path = tmp_path / "review.sqlite3"
    overlay_root = tmp_path / "ontology_overlays"
    review_service = ReviewService(db_path=review_db_path, overlay_root=overlay_root)
    submission = review_service.submit_candidate_assertion(
        payload={"predicate": "oc:broken_candidate", "roles": {}},
        profile_id="default",
        profile_version="1.0.0",
        submitted_by="analyst:seed",
        source_kind="text_file",
        source_ref="seed.txt",
    )

    exit_code = cli_module.main(
        [
            "review-candidate",
            "--candidate-id",
            submission.candidate.candidate_id,
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

    captured = capsys.readouterr()
    assert exit_code == 1
    assert "invalid candidates cannot transition to accepted review status" in captured.err
