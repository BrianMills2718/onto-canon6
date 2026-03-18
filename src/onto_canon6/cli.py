"""Thin operational CLI for the Phase 6 successor workflow.

This module deliberately does not create a second runtime around the services.
Each command:

1. parses explicit arguments;
2. instantiates the existing config-backed services, with optional path
   overrides for the mutable store locations;
3. delegates to the existing extraction, review, proposal, or overlay
   services;
4. renders either JSON-first machine output or a small human-readable view.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any, Sequence

from .config import CLIOutputFormatValue, ConfigError, get_config
from .pipeline import (
    CandidateAssertionRecord,
    CandidateSubmissionResult,
    OverlayApplicationRecord,
    OverlayApplicationService,
    ProposalRecord,
    ReviewService,
    ReviewStoreError,
    TextExtractionService,
)
from .surfaces import GovernedWorkflowBundle, GovernedWorkflowBundleService


def main(argv: Sequence[str] | None = None) -> int:
    """Run the operational CLI and return a process-style exit code."""

    parser = _build_parser()
    try:
        args = parser.parse_args(list(argv) if argv is not None else None)
        handler = getattr(args, "handler", None)
        if handler is None:
            parser.print_help()
            return 2
        return int(handler(args))
    except SystemExit as exc:
        return _coerce_exit_code(exc.code)
    except (ConfigError, ReviewStoreError, ValueError, FileNotFoundError) as exc:
        print(f"ERROR [{type(exc).__name__}] {exc}", file=sys.stderr)
        return 1


def _build_parser() -> argparse.ArgumentParser:
    """Build the argparse command tree for the operational surface."""

    config = get_config()
    parser = argparse.ArgumentParser(
        prog=config.project.name,
        description="Operational CLI for the onto-canon6 review workflow.",
    )
    subparsers = parser.add_subparsers(dest="command")

    extract_parser = subparsers.add_parser(
        "extract-text",
        help="Extract candidate assertions from one text file and persist them through review.",
    )
    _add_store_args(extract_parser, include_overlay_root=True)
    extract_parser.add_argument("--input", required=True, type=Path, help="Path to the source text file.")
    extract_parser.add_argument("--profile-id", required=True, help="Validation profile id.")
    extract_parser.add_argument("--profile-version", required=True, help="Validation profile version.")
    extract_parser.add_argument("--submitted-by", required=True, help="Actor id recorded for the submission.")
    extract_parser.add_argument(
        "--source-ref",
        help="Stable source reference. Defaults to the provided input path string.",
    )
    extract_parser.add_argument(
        "--source-label",
        help="Optional human-readable source label. Defaults to the input file name.",
    )
    _add_output_arg(extract_parser, default_output=config.cli.default_output_format)
    extract_parser.set_defaults(handler=_handle_extract_text)

    list_candidates_parser = subparsers.add_parser(
        "list-candidates",
        help="List persisted candidate assertions with optional filters.",
    )
    _add_store_args(list_candidates_parser, include_overlay_root=False)
    list_candidates_parser.add_argument(
        "--review-status",
        choices=("pending_review", "accepted", "rejected"),
        help="Filter by candidate review status.",
    )
    list_candidates_parser.add_argument(
        "--validation-status",
        choices=("valid", "needs_review", "invalid"),
        help="Filter by candidate validation status.",
    )
    list_candidates_parser.add_argument(
        "--proposal-status",
        choices=("pending", "accepted", "rejected"),
        help="Filter to candidates linked to proposals with this status.",
    )
    list_candidates_parser.add_argument("--profile-id", help="Optional profile-id filter.")
    list_candidates_parser.add_argument("--profile-version", help="Optional profile-version filter.")
    _add_output_arg(list_candidates_parser, default_output=config.cli.default_output_format)
    list_candidates_parser.set_defaults(handler=_handle_list_candidates)

    list_proposals_parser = subparsers.add_parser(
        "list-proposals",
        help="List persisted ontology proposals with optional filters.",
    )
    _add_store_args(list_proposals_parser, include_overlay_root=False)
    list_proposals_parser.add_argument(
        "--status",
        choices=("pending", "accepted", "rejected"),
        help="Filter by proposal review status.",
    )
    list_proposals_parser.add_argument("--profile-id", help="Optional profile-id filter.")
    list_proposals_parser.add_argument("--profile-version", help="Optional profile-version filter.")
    _add_output_arg(list_proposals_parser, default_output=config.cli.default_output_format)
    list_proposals_parser.set_defaults(handler=_handle_list_proposals)

    review_candidate_parser = subparsers.add_parser(
        "review-candidate",
        help="Record one candidate review decision.",
    )
    _add_store_args(review_candidate_parser, include_overlay_root=False)
    review_candidate_parser.add_argument("--candidate-id", required=True, help="Candidate identifier.")
    review_candidate_parser.add_argument(
        "--decision",
        required=True,
        choices=("accepted", "rejected"),
        help="Candidate review decision.",
    )
    review_candidate_parser.add_argument("--actor-id", required=True, help="Actor id for the review.")
    review_candidate_parser.add_argument("--note", help="Optional review note.")
    _add_output_arg(review_candidate_parser, default_output=config.cli.default_output_format)
    review_candidate_parser.set_defaults(handler=_handle_review_candidate)

    review_proposal_parser = subparsers.add_parser(
        "review-proposal",
        help="Record one proposal review decision.",
    )
    _add_store_args(review_proposal_parser, include_overlay_root=False)
    review_proposal_parser.add_argument("--proposal-id", required=True, help="Proposal identifier.")
    review_proposal_parser.add_argument(
        "--decision",
        required=True,
        choices=("accepted", "rejected"),
        help="Proposal review decision.",
    )
    review_proposal_parser.add_argument("--actor-id", required=True, help="Actor id for the review.")
    review_proposal_parser.add_argument("--note", help="Optional review note.")
    review_proposal_parser.add_argument(
        "--acceptance-policy",
        choices=("record_only", "apply_to_overlay"),
        help="Explicit acceptance policy override for accepted proposals.",
    )
    _add_output_arg(review_proposal_parser, default_output=config.cli.default_output_format)
    review_proposal_parser.set_defaults(handler=_handle_review_proposal)

    apply_overlay_parser = subparsers.add_parser(
        "apply-overlay",
        help="Apply one accepted proposal into its target overlay.",
    )
    _add_store_args(apply_overlay_parser, include_overlay_root=True)
    apply_overlay_parser.add_argument("--proposal-id", required=True, help="Proposal identifier.")
    apply_overlay_parser.add_argument("--actor-id", required=True, help="Actor id for the application.")
    _add_output_arg(apply_overlay_parser, default_output=config.cli.default_output_format)
    apply_overlay_parser.set_defaults(handler=_handle_apply_overlay)

    export_bundle_parser = subparsers.add_parser(
        "export-governed-bundle",
        help="Export accepted governed assertions with provenance, governance, and optional extension state.",
    )
    _add_store_args(export_bundle_parser, include_overlay_root=False)
    export_bundle_parser.add_argument(
        "--profile-id",
        help="Optional profile-id filter over accepted candidates.",
    )
    export_bundle_parser.add_argument(
        "--profile-version",
        help="Optional profile-version filter. Requires --profile-id.",
    )
    export_bundle_parser.add_argument(
        "--candidate-id",
        action="append",
        default=[],
        help="Optional accepted candidate-id filter. Can be repeated.",
    )
    _add_output_arg(export_bundle_parser, default_output=config.cli.default_output_format)
    export_bundle_parser.set_defaults(handler=_handle_export_governed_bundle)

    return parser


def _handle_extract_text(args: argparse.Namespace) -> int:
    """Extract candidate assertions from one text file and persist them."""

    config = get_config()
    review_service = _build_review_service(args)
    extractor = TextExtractionService(review_service=review_service)
    input_path = args.input
    source_text = input_path.read_text(encoding="utf-8")
    source_ref = args.source_ref if args.source_ref is not None else str(input_path)
    source_label = args.source_label if args.source_label is not None else input_path.name
    results = extractor.extract_and_submit(
        source_text=source_text,
        profile_id=args.profile_id,
        profile_version=args.profile_version,
        submitted_by=args.submitted_by,
        source_ref=source_ref,
        source_kind=config.cli.file_source_kind,
        source_label=source_label,
    )
    _emit_output(results, output_format=args.output)
    return 0


def _handle_list_candidates(args: argparse.Namespace) -> int:
    """List persisted candidate assertions with optional filters."""

    review_service = _build_review_service(args)
    candidates = tuple(
        review_service.list_candidate_assertions(
            review_status_filter=args.review_status,
            validation_status_filter=args.validation_status,
            proposal_status_filter=args.proposal_status,
            profile_id=args.profile_id,
            profile_version=args.profile_version,
        )
    )
    _emit_output(candidates, output_format=args.output)
    return 0


def _handle_list_proposals(args: argparse.Namespace) -> int:
    """List persisted ontology proposals with optional filters."""

    review_service = _build_review_service(args)
    proposals = tuple(
        review_service.list_proposals(
            status_filter=args.status,
            profile_id=args.profile_id,
            profile_version=args.profile_version,
        )
    )
    _emit_output(proposals, output_format=args.output)
    return 0


def _handle_review_candidate(args: argparse.Namespace) -> int:
    """Record one candidate review decision and print the resulting record."""

    review_service = _build_review_service(args)
    candidate = review_service.review_candidate(
        candidate_id=args.candidate_id,
        decision=args.decision,
        actor_id=args.actor_id,
        note_text=args.note,
    )
    _emit_output(candidate, output_format=args.output)
    return 0


def _handle_review_proposal(args: argparse.Namespace) -> int:
    """Record one proposal review decision and print the resulting record."""

    review_service = _build_review_service(args)
    proposal = review_service.review_proposal(
        proposal_id=args.proposal_id,
        decision=args.decision,
        actor_id=args.actor_id,
        note_text=args.note,
        acceptance_policy=args.acceptance_policy,
    )
    _emit_output(proposal, output_format=args.output)
    return 0


def _handle_apply_overlay(args: argparse.Namespace) -> int:
    """Apply one accepted proposal into its target overlay and print the audit row."""

    overlay_service = _build_overlay_service(args)
    application = overlay_service.apply_proposal_to_overlay(
        proposal_id=args.proposal_id,
        applied_by=args.actor_id,
    )
    _emit_output(application, output_format=args.output)
    return 0


def _handle_export_governed_bundle(args: argparse.Namespace) -> int:
    """Export one product-facing bundle over accepted governed assertions."""

    review_service = _build_review_service(args)
    bundle = GovernedWorkflowBundleService(review_service=review_service).build_bundle(
        profile_id=args.profile_id,
        profile_version=args.profile_version,
        candidate_ids=tuple(args.candidate_id),
    )
    _emit_output(bundle, output_format=args.output)
    return 0


def _build_review_service(args: argparse.Namespace) -> ReviewService:
    """Create a review service from config-backed defaults plus explicit overrides."""

    db_path = Path(args.review_db_path) if getattr(args, "review_db_path", None) else None
    overlay_root = Path(args.overlay_root) if getattr(args, "overlay_root", None) else None
    return ReviewService(db_path=db_path, overlay_root=overlay_root)


def _build_overlay_service(args: argparse.Namespace) -> OverlayApplicationService:
    """Create an overlay application service from config-backed defaults plus overrides."""

    db_path = Path(args.review_db_path) if getattr(args, "review_db_path", None) else None
    overlay_root = Path(args.overlay_root) if getattr(args, "overlay_root", None) else None
    return OverlayApplicationService(db_path=db_path, overlay_root=overlay_root)


def _add_store_args(parser: argparse.ArgumentParser, *, include_overlay_root: bool) -> None:
    """Add explicit mutable-store overrides to one subcommand parser."""

    parser.add_argument(
        "--review-db-path",
        help="Optional SQLite path override for review state. Defaults to config.",
    )
    if include_overlay_root:
        parser.add_argument(
            "--overlay-root",
            help="Optional overlay-root override. Defaults to config.",
        )


def _add_output_arg(parser: argparse.ArgumentParser, *, default_output: CLIOutputFormatValue) -> None:
    """Add the shared output-format argument to one subcommand parser."""

    parser.add_argument(
        "--output",
        choices=("json", "text"),
        default=default_output,
        help="Output format for command results.",
    )


def _emit_output(value: object, *, output_format: CLIOutputFormatValue) -> None:
    """Render one command result in either JSON or compact human text."""

    if output_format == "json":
        print(json.dumps(_to_jsonable(value), indent=2, sort_keys=True))
        return
    print(_to_text(value))


def _coerce_exit_code(code: object) -> int:
    """Normalize `argparse`/`SystemExit` codes into process-style integers."""

    if code is None:
        return 0
    if isinstance(code, int):
        return code
    return 1


def _to_jsonable(value: object) -> Any:
    """Normalize Pydantic-rich command results into JSON-serializable data."""

    if isinstance(
        value,
        (
            CandidateAssertionRecord,
            CandidateSubmissionResult,
            GovernedWorkflowBundle,
            ProposalRecord,
            OverlayApplicationRecord,
        ),
    ):
        return value.model_dump(mode="json")
    if isinstance(value, tuple):
        return [_to_jsonable(item) for item in value]
    if isinstance(value, list):
        return [_to_jsonable(item) for item in value]
    if isinstance(value, Path):
        return str(value)
    return value


def _to_text(value: object) -> str:
    """Render compact human-readable output for the current command result."""

    if isinstance(value, CandidateSubmissionResult):
        proposal_text = ", ".join(value.candidate.proposal_ids) if value.candidate.proposal_ids else "none"
        return (
            f"candidate_id={value.candidate.candidate_id} "
            f"validation_status={value.candidate.validation_status} "
            f"review_status={value.candidate.review_status} "
            f"proposals={proposal_text}"
        )
    if isinstance(value, CandidateAssertionRecord):
        predicate = str(value.payload.get("predicate", ""))
        return (
            f"candidate_id={value.candidate_id} "
            f"review_status={value.review_status} "
            f"validation_status={value.validation_status} "
            f"predicate={predicate}"
        )
    if isinstance(value, ProposalRecord):
        return (
            f"proposal_id={value.proposal_id} "
            f"status={value.status} "
            f"application_status={value.application_status} "
            f"value={value.proposed_value}"
        )
    if isinstance(value, OverlayApplicationRecord):
        return (
            f"proposal_id={value.proposal_id} "
            f"overlay_pack={value.overlay_pack.pack_id}@{value.overlay_pack.pack_version} "
            f"content_path={value.content_path}"
        )
    if isinstance(value, GovernedWorkflowBundle):
        candidate_ids = ",".join(
            candidate_bundle.candidate.candidate_id for candidate_bundle in value.candidate_bundles
        ) or "none"
        return (
            f"accepted_candidates={value.summary.total_candidates} "
            f"linked_proposals={value.summary.total_linked_proposals} "
            f"overlay_applications={value.summary.total_overlay_applications} "
            f"candidates_with_confidence={value.summary.total_candidates_with_confidence} "
            f"candidate_ids={candidate_ids}"
        )
    if isinstance(value, tuple):
        return "\n".join(_to_text(item) for item in value)
    if isinstance(value, list):
        return "\n".join(_to_text(item) for item in value)
    return str(value)


__all__ = ["main"]
