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

from .adapters import (
    ResearchAgentWhyGameTransformResult,
    ResearchAgentWhyGameTransformService,
    WhyGameImportResult,
    WhyGameImportService,
)
from .config import CLIOutputFormatValue, ConfigError, get_config
from .core import (
    CanonicalGraphPromotionError,
    CanonicalGraphPromotionResult,
    CanonicalGraphService,
    GraphExternalReferenceRecord,
    GraphIdentityMembershipRecord,
    IdentityBundleRecord,
    IdentityError,
    IdentityService,
    PromotedGraphRecanonicalizationEventRecord,
    PromotedGraphAssertionRecord,
    SemanticCanonicalizationError,
    SemanticCanonicalizationResult,
    SemanticCanonicalizationService,
)
from .extensions.epistemic import (
    AssertionDispositionRecord,
    EpistemicService,
    EpistemicStoreError,
    PromotedAssertionEpistemicCollectionReport,
)
from .evaluation import (
    ExtractionPromptExperimentError,
    ExtractionPromptExperimentReport,
    ExtractionPromptExperimentService,
)
from .pipeline import (
    CandidateAssertionRecord,
    CandidateSubmissionResult,
    OverlayApplicationRecord,
    OverlayApplicationService,
    ProposalRecord,
    ReviewService,
    ReviewStoreError,
    TextChunkFileRecord,
    TextChunkManifest,
    TextChunkingService,
    TextExtractionService,
)
from .surfaces import (
    EpistemicReportService,
    GovernedWorkflowBundle,
    GovernedWorkflowBundleService,
    IdentityReport,
    IdentityReportService,
    PromotedGraphReport,
    PromotedGraphReportService,
    SemanticCanonicalizationReport,
    SemanticCanonicalizationReportService,
)


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
    except (
        CanonicalGraphPromotionError,
        ConfigError,
        EpistemicStoreError,
        ExtractionPromptExperimentError,
        IdentityError,
        ReviewStoreError,
        SemanticCanonicalizationError,
        ValueError,
        FileNotFoundError,
    ) as exc:
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

    split_parser = subparsers.add_parser(
        "split-text",
        help="Split one long text file into deterministic chunk files for later extraction.",
    )
    split_parser.add_argument("--input", required=True, type=Path, help="Path to the source text file.")
    split_parser.add_argument(
        "--output-dir",
        required=True,
        type=Path,
        help="Directory where chunk files and the manifest will be written.",
    )
    split_parser.add_argument(
        "--source-ref",
        help="Stable source reference recorded in the manifest. Defaults to the input path string.",
    )
    split_parser.add_argument(
        "--source-label",
        help="Optional human-readable source label. Defaults to the input file name.",
    )
    split_parser.add_argument(
        "--target-max-chars",
        type=int,
        help="Optional soft chunk target. Defaults to config.",
    )
    split_parser.add_argument(
        "--min-chunk-chars",
        type=int,
        help="Optional minimum useful chunk size. Defaults to config.",
    )
    split_parser.add_argument(
        "--max-chunk-chars",
        type=int,
        help="Optional hard maximum chunk size. Defaults to config.",
    )
    _add_output_arg(split_parser, default_output=config.cli.default_output_format)
    split_parser.set_defaults(handler=_handle_split_text)

    prompt_experiment_parser = subparsers.add_parser(
        "run-extraction-prompt-experiment",
        help="Run the configured prompt_eval extraction prompt comparison over the benchmark fixture.",
    )
    prompt_experiment_parser.add_argument(
        "--fixture-path",
        type=Path,
        help="Optional benchmark fixture override. Defaults to config.",
    )
    prompt_experiment_parser.add_argument(
        "--case-limit",
        type=int,
        help="Optional case limit for a smaller experiment slice.",
    )
    prompt_experiment_parser.add_argument(
        "--n-runs",
        type=int,
        help="Optional replicate override. Defaults to config.",
    )
    prompt_experiment_parser.add_argument(
        "--comparison-method",
        choices=("bootstrap", "welch"),
        help="Optional comparison-method override. Defaults to config.",
    )
    prompt_experiment_parser.add_argument(
        "--selection-task",
        help="Optional llm_client selection-task override. Defaults to config.",
    )
    _add_output_arg(prompt_experiment_parser, default_output=config.cli.default_output_format)
    prompt_experiment_parser.set_defaults(handler=_handle_run_extraction_prompt_experiment)

    import_whygame_parser = subparsers.add_parser(
        "import-whygame-relationships",
        help="Import one JSON array of WhyGame relationship facts into the review workflow.",
    )
    _add_store_args(import_whygame_parser, include_overlay_root=True)
    import_whygame_parser.add_argument(
        "--input",
        required=True,
        type=Path,
        help="Path to the JSON file containing WhyGame relationship facts.",
    )
    import_whygame_parser.add_argument(
        "--submitted-by",
        required=True,
        help="Actor id recorded for the imported candidates.",
    )
    import_whygame_parser.add_argument(
        "--source-ref",
        help="Stable source reference recorded on imported candidates. Defaults to the input path string.",
    )
    import_whygame_parser.add_argument(
        "--source-label",
        help="Optional human-readable source label. Defaults to the input file name.",
    )
    import_whygame_parser.add_argument(
        "--artifact-uri",
        help="Optional artifact URI recorded when artifact registration is enabled.",
    )
    import_whygame_parser.add_argument(
        "--artifact-label",
        help="Optional artifact label recorded when artifact registration is enabled.",
    )
    import_whygame_parser.add_argument(
        "--no-register-artifact",
        action="store_true",
        help="Disable the adapter's default artifact registration for this import.",
    )
    _add_output_arg(import_whygame_parser, default_output=config.cli.default_output_format)
    import_whygame_parser.set_defaults(handler=_handle_import_whygame_relationships)

    convert_research_agent_parser = subparsers.add_parser(
        "convert-research-agent-entities-to-whygame",
        help="Convert one research-agent entities.json file into WhyGame relationship facts.",
    )
    convert_research_agent_parser.add_argument(
        "--input",
        required=True,
        type=Path,
        help="Path to the research-agent entities.json file.",
    )
    convert_research_agent_parser.add_argument(
        "--output-file",
        required=True,
        type=Path,
        help="Path where the WhyGame relationship facts JSON file will be written.",
    )
    convert_research_agent_parser.add_argument(
        "--investigation-id",
        help="Optional investigation identifier recorded in the fact context.",
    )
    _add_output_arg(convert_research_agent_parser, default_output=config.cli.default_output_format)
    convert_research_agent_parser.set_defaults(handler=_handle_convert_research_agent_entities)

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

    promote_candidate_parser = subparsers.add_parser(
        "promote-candidate",
        help="Promote one accepted candidate into the durable graph slice.",
    )
    _add_store_args(promote_candidate_parser, include_overlay_root=False)
    promote_candidate_parser.add_argument(
        "--candidate-id",
        required=True,
        help="Accepted candidate identifier to promote.",
    )
    promote_candidate_parser.add_argument(
        "--actor-id",
        required=True,
        help="Actor id recorded for the promotion.",
    )
    _add_output_arg(promote_candidate_parser, default_output=config.cli.default_output_format)
    promote_candidate_parser.set_defaults(handler=_handle_promote_candidate)

    list_promoted_parser = subparsers.add_parser(
        "list-promoted-assertions",
        help="List promoted graph assertions.",
    )
    _add_store_args(list_promoted_parser, include_overlay_root=False)
    _add_output_arg(list_promoted_parser, default_output=config.cli.default_output_format)
    list_promoted_parser.set_defaults(handler=_handle_list_promoted_assertions)

    export_promoted_report_parser = subparsers.add_parser(
        "export-promoted-graph-report",
        help="Export promoted graph assertions with candidate-backed governance context.",
    )
    _add_store_args(export_promoted_report_parser, include_overlay_root=False)
    _add_output_arg(
        export_promoted_report_parser,
        default_output=config.cli.default_output_format,
    )
    export_promoted_report_parser.set_defaults(handler=_handle_export_promoted_graph_report)

    recanonicalize_parser = subparsers.add_parser(
        "recanonicalize-promoted-assertion",
        help="Repair one promoted assertion through pack-driven semantic canonicalization.",
    )
    _add_store_args(recanonicalize_parser, include_overlay_root=True)
    recanonicalize_parser.add_argument(
        "--assertion-id",
        required=True,
        help="Promoted assertion identifier to recanonicalize.",
    )
    recanonicalize_parser.add_argument(
        "--actor-id",
        required=True,
        help="Actor id recorded for the repair event.",
    )
    recanonicalize_parser.add_argument(
        "--reason",
        help="Optional repair rationale recorded on the recanonicalization event.",
    )
    _add_output_arg(recanonicalize_parser, default_output=config.cli.default_output_format)
    recanonicalize_parser.set_defaults(handler=_handle_recanonicalize_promoted_assertion)

    list_recanonicalization_events_parser = subparsers.add_parser(
        "list-recanonicalization-events",
        help="List persisted promoted-assertion recanonicalization events.",
    )
    _add_store_args(list_recanonicalization_events_parser, include_overlay_root=False)
    list_recanonicalization_events_parser.add_argument(
        "--assertion-id",
        help="Optional promoted assertion filter.",
    )
    _add_output_arg(
        list_recanonicalization_events_parser,
        default_output=config.cli.default_output_format,
    )
    list_recanonicalization_events_parser.set_defaults(handler=_handle_list_recanonicalization_events)

    export_semantic_report_parser = subparsers.add_parser(
        "export-semantic-canonicalization-report",
        help="Export promoted assertions with their semantic repair history.",
    )
    _add_store_args(export_semantic_report_parser, include_overlay_root=True)
    _add_output_arg(
        export_semantic_report_parser,
        default_output=config.cli.default_output_format,
    )
    export_semantic_report_parser.set_defaults(handler=_handle_export_semantic_canonicalization_report)

    disposition_parser = subparsers.add_parser(
        "record-assertion-disposition",
        help="Record one explicit epistemic disposition over a promoted assertion.",
    )
    _add_store_args(disposition_parser, include_overlay_root=False)
    disposition_parser.add_argument(
        "--assertion-id",
        required=True,
        help="Promoted assertion identifier.",
    )
    disposition_parser.add_argument(
        "--target-status",
        required=True,
        choices=("active", "weakened", "retracted"),
        help="Explicit promoted-assertion target status.",
    )
    disposition_parser.add_argument(
        "--actor-id",
        required=True,
        help="Actor id recorded for the disposition event.",
    )
    disposition_parser.add_argument(
        "--reason",
        help="Optional rationale recorded on the disposition event.",
    )
    _add_output_arg(disposition_parser, default_output=config.cli.default_output_format)
    disposition_parser.set_defaults(handler=_handle_record_assertion_disposition)

    export_epistemic_report_parser = subparsers.add_parser(
        "export-assertion-epistemic-report",
        help="Export promoted assertions with assertion-level epistemic, corroboration, and tension state.",
    )
    _add_store_args(export_epistemic_report_parser, include_overlay_root=False)
    _add_output_arg(
        export_epistemic_report_parser,
        default_output=config.cli.default_output_format,
    )
    export_epistemic_report_parser.set_defaults(handler=_handle_export_assertion_epistemic_report)

    create_identity_parser = subparsers.add_parser(
        "create-identity-for-entity",
        help="Create or reuse the stable identity for one promoted entity.",
    )
    _add_store_args(create_identity_parser, include_overlay_root=False)
    create_identity_parser.add_argument("--entity-id", required=True, help="Promoted entity identifier.")
    create_identity_parser.add_argument("--actor-id", required=True, help="Actor id recorded for identity creation.")
    create_identity_parser.add_argument(
        "--display-label",
        help="Optional display label recorded on first identity creation.",
    )
    _add_output_arg(create_identity_parser, default_output=config.cli.default_output_format)
    create_identity_parser.set_defaults(handler=_handle_create_identity_for_entity)

    attach_identity_alias_parser = subparsers.add_parser(
        "attach-identity-alias",
        help="Attach another promoted entity id as an explicit alias membership.",
    )
    _add_store_args(attach_identity_alias_parser, include_overlay_root=False)
    attach_identity_alias_parser.add_argument("--identity-id", required=True, help="Stable identity identifier.")
    attach_identity_alias_parser.add_argument("--entity-id", required=True, help="Promoted entity identifier.")
    attach_identity_alias_parser.add_argument("--actor-id", required=True, help="Actor id recorded for the alias attachment.")
    _add_output_arg(attach_identity_alias_parser, default_output=config.cli.default_output_format)
    attach_identity_alias_parser.set_defaults(handler=_handle_attach_identity_alias)

    attach_external_ref_parser = subparsers.add_parser(
        "attach-external-ref",
        help="Attach one explicit external reference to an identity.",
    )
    _add_store_args(attach_external_ref_parser, include_overlay_root=False)
    attach_external_ref_parser.add_argument("--identity-id", required=True, help="Stable identity identifier.")
    attach_external_ref_parser.add_argument("--provider", required=True, help="External reference provider.")
    attach_external_ref_parser.add_argument("--external-id", required=True, help="Concrete external identifier.")
    attach_external_ref_parser.add_argument("--actor-id", required=True, help="Actor id recorded for the attachment.")
    attach_external_ref_parser.add_argument("--reference-label", help="Optional human-readable external label.")
    _add_output_arg(attach_external_ref_parser, default_output=config.cli.default_output_format)
    attach_external_ref_parser.set_defaults(handler=_handle_attach_external_ref)

    unresolved_external_ref_parser = subparsers.add_parser(
        "record-unresolved-external-ref",
        help="Persist explicit unresolved external-reference work for an identity.",
    )
    _add_store_args(unresolved_external_ref_parser, include_overlay_root=False)
    unresolved_external_ref_parser.add_argument("--identity-id", required=True, help="Stable identity identifier.")
    unresolved_external_ref_parser.add_argument("--provider", required=True, help="External reference provider.")
    unresolved_external_ref_parser.add_argument(
        "--unresolved-note",
        required=True,
        help="Explicit note describing the unresolved reference work.",
    )
    unresolved_external_ref_parser.add_argument("--actor-id", required=True, help="Actor id recorded for the unresolved record.")
    _add_output_arg(unresolved_external_ref_parser, default_output=config.cli.default_output_format)
    unresolved_external_ref_parser.set_defaults(handler=_handle_record_unresolved_external_ref)

    list_identities_parser = subparsers.add_parser(
        "list-identities",
        help="List stable identity bundles.",
    )
    _add_store_args(list_identities_parser, include_overlay_root=False)
    _add_output_arg(list_identities_parser, default_output=config.cli.default_output_format)
    list_identities_parser.set_defaults(handler=_handle_list_identities)

    export_identity_report_parser = subparsers.add_parser(
        "export-identity-report",
        help="Export the stable identity report over the current identity slice.",
    )
    _add_store_args(export_identity_report_parser, include_overlay_root=False)
    _add_output_arg(export_identity_report_parser, default_output=config.cli.default_output_format)
    export_identity_report_parser.set_defaults(handler=_handle_export_identity_report)

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


def _handle_split_text(args: argparse.Namespace) -> int:
    """Split one source text file into deterministic chunk files."""

    input_path = args.input
    output_dir = args.output_dir
    source_ref = args.source_ref if args.source_ref is not None else str(input_path)
    source_label = args.source_label if args.source_label is not None else input_path.name
    service = TextChunkingService(
        target_max_chars=args.target_max_chars,
        min_chunk_chars=args.min_chunk_chars,
        max_chunk_chars=args.max_chunk_chars,
    )
    manifest = service.write_chunk_files(
        input_path=input_path,
        output_dir=output_dir,
        source_ref=source_ref,
        source_label=source_label,
    )
    manifest_path = output_dir / "manifest.json"
    manifest_path.write_text(
        json.dumps(manifest.model_dump(mode="json"), indent=2, sort_keys=True),
        encoding="utf-8",
    )
    _emit_output(manifest, output_format=args.output)
    return 0


def _handle_run_extraction_prompt_experiment(args: argparse.Namespace) -> int:
    """Run the configured prompt_eval extraction prompt experiment."""

    report = ExtractionPromptExperimentService().run_prompt_experiment(
        fixture_path=args.fixture_path,
        case_limit=args.case_limit,
        n_runs=args.n_runs,
        comparison_method=args.comparison_method,
        selection_task=args.selection_task,
    )
    _emit_output(report, output_format=args.output)
    return 0


def _handle_import_whygame_relationships(args: argparse.Namespace) -> int:
    """Import one file of WhyGame relationship facts through the existing adapter."""

    review_service = _build_review_service(args)
    input_path = args.input
    loaded = json.loads(input_path.read_text(encoding="utf-8"))
    if not isinstance(loaded, list):
        raise ValueError("WhyGame import input must be a JSON array of relationship facts")
    source_ref = args.source_ref if args.source_ref is not None else str(input_path)
    source_label = args.source_label if args.source_label is not None else input_path.name
    service = WhyGameImportService(review_service=review_service)
    request = service.build_default_request(
        facts=loaded,
        submitted_by=args.submitted_by,
        source_ref=source_ref,
        source_label=source_label,
        register_artifact=False if args.no_register_artifact else None,
        artifact_uri=args.artifact_uri,
        artifact_label=args.artifact_label,
    )
    result = service.import_request(request=request)
    _emit_output(result, output_format=args.output)
    return 0


def _handle_convert_research_agent_entities(args: argparse.Namespace) -> int:
    """Convert one research-agent entities file into a WhyGame relationship fact file."""

    result = ResearchAgentWhyGameTransformService().write_transformed_facts(
        input_path=args.input,
        output_path=args.output_file,
        investigation_id=args.investigation_id,
    )
    _emit_output(result, output_format=args.output)
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


def _handle_promote_candidate(args: argparse.Namespace) -> int:
    """Promote one accepted candidate and print the resulting graph bundle."""

    graph_service = _build_graph_service(args)
    promotion = graph_service.promote_candidate(
        candidate_id=args.candidate_id,
        promoted_by=args.actor_id,
    )
    _emit_output(promotion, output_format=args.output)
    return 0


def _handle_list_promoted_assertions(args: argparse.Namespace) -> int:
    """List promoted graph assertions in deterministic order."""

    graph_service = _build_graph_service(args)
    assertions = tuple(graph_service.list_promoted_assertions())
    _emit_output(assertions, output_format=args.output)
    return 0


def _handle_export_promoted_graph_report(args: argparse.Namespace) -> int:
    """Export the promoted-graph report over the current graph slice."""

    graph_service = _build_graph_service(args)
    review_service = _build_review_service(args)
    report = PromotedGraphReportService(
        graph_service=graph_service,
        review_service=review_service,
    ).build_report()
    _emit_output(report, output_format=args.output)
    return 0


def _handle_recanonicalize_promoted_assertion(args: argparse.Namespace) -> int:
    """Repair one promoted assertion through the semantic canonicalization seam."""

    semantic_service = _build_semantic_service(args)
    result = semantic_service.recanonicalize_promoted_assertion(
        assertion_id=args.assertion_id,
        actor_id=args.actor_id,
        reason=args.reason,
    )
    _emit_output(result, output_format=args.output)
    return 0


def _handle_list_recanonicalization_events(args: argparse.Namespace) -> int:
    """List persisted recanonicalization events in deterministic order."""

    semantic_service = _build_semantic_service(args)
    events = tuple(
        semantic_service.list_recanonicalization_events(assertion_id=args.assertion_id)
    )
    _emit_output(events, output_format=args.output)
    return 0


def _handle_export_semantic_canonicalization_report(args: argparse.Namespace) -> int:
    """Export the semantic repair report over the current promoted graph."""

    graph_service = _build_graph_service(args)
    semantic_service = _build_semantic_service(args)
    report = SemanticCanonicalizationReportService(
        graph_service=graph_service,
        semantic_service=semantic_service,
    ).build_report()
    _emit_output(report, output_format=args.output)
    return 0


def _handle_record_assertion_disposition(args: argparse.Namespace) -> int:
    """Record one explicit epistemic disposition over a promoted assertion."""

    epistemic_service = _build_epistemic_service(args)
    record = epistemic_service.record_assertion_disposition(
        assertion_id=args.assertion_id,
        target_status=args.target_status,
        actor_id=args.actor_id,
        rationale=args.reason,
    )
    _emit_output(record, output_format=args.output)
    return 0


def _handle_export_assertion_epistemic_report(args: argparse.Namespace) -> int:
    """Export the promoted-assertion epistemic report for the current graph state."""

    epistemic_service = _build_epistemic_service(args)
    report = EpistemicReportService(epistemic_service=epistemic_service).build_promoted_assertion_collection_report()
    _emit_output(report, output_format=args.output)
    return 0


def _handle_create_identity_for_entity(args: argparse.Namespace) -> int:
    """Create or reuse the stable identity for one promoted entity."""

    identity_service = _build_identity_service(args)
    bundle = identity_service.create_identity_for_entity(
        entity_id=args.entity_id,
        created_by=args.actor_id,
        display_label=args.display_label,
    )
    _emit_output(bundle, output_format=args.output)
    return 0


def _handle_attach_identity_alias(args: argparse.Namespace) -> int:
    """Attach another promoted entity id as an alias to an identity."""

    identity_service = _build_identity_service(args)
    membership = identity_service.attach_entity_alias(
        identity_id=args.identity_id,
        entity_id=args.entity_id,
        attached_by=args.actor_id,
    )
    _emit_output(membership, output_format=args.output)
    return 0


def _handle_attach_external_ref(args: argparse.Namespace) -> int:
    """Attach one explicit external reference to an identity."""

    identity_service = _build_identity_service(args)
    reference = identity_service.attach_external_reference(
        identity_id=args.identity_id,
        provider=args.provider,
        external_id=args.external_id,
        attached_by=args.actor_id,
        reference_label=args.reference_label,
    )
    _emit_output(reference, output_format=args.output)
    return 0


def _handle_record_unresolved_external_ref(args: argparse.Namespace) -> int:
    """Persist one explicit unresolved external-reference record."""

    identity_service = _build_identity_service(args)
    reference = identity_service.record_unresolved_external_reference(
        identity_id=args.identity_id,
        provider=args.provider,
        unresolved_note=args.unresolved_note,
        attached_by=args.actor_id,
    )
    _emit_output(reference, output_format=args.output)
    return 0


def _handle_list_identities(args: argparse.Namespace) -> int:
    """List stable identity bundles in deterministic order."""

    identity_service = _build_identity_service(args)
    bundles = tuple(identity_service.list_identities())
    _emit_output(bundles, output_format=args.output)
    return 0


def _handle_export_identity_report(args: argparse.Namespace) -> int:
    """Export the stable identity report for the current identity slice."""

    identity_service = _build_identity_service(args)
    report = IdentityReportService(identity_service=identity_service).build_report()
    _emit_output(report, output_format=args.output)
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


def _build_graph_service(args: argparse.Namespace) -> CanonicalGraphService:
    """Create a graph service from config-backed defaults plus explicit overrides."""

    db_path = Path(args.review_db_path) if getattr(args, "review_db_path", None) else None
    return CanonicalGraphService(db_path=db_path)


def _build_epistemic_service(args: argparse.Namespace) -> EpistemicService:
    """Create an epistemic service from config-backed defaults plus overrides."""

    db_path = Path(args.review_db_path) if getattr(args, "review_db_path", None) else None
    return EpistemicService(db_path=db_path)


def _build_identity_service(args: argparse.Namespace) -> IdentityService:
    """Create an identity service from config-backed defaults plus overrides."""

    db_path = Path(args.review_db_path) if getattr(args, "review_db_path", None) else None
    return IdentityService(db_path=db_path)


def _build_semantic_service(args: argparse.Namespace) -> SemanticCanonicalizationService:
    """Create a semantic canonicalization service from config-backed defaults plus overrides."""

    db_path = Path(args.review_db_path) if getattr(args, "review_db_path", None) else None
    overlay_root = Path(args.overlay_root) if getattr(args, "overlay_root", None) else None
    return SemanticCanonicalizationService(db_path=db_path, overlay_root=overlay_root)


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
            AssertionDispositionRecord,
            CandidateAssertionRecord,
            CandidateSubmissionResult,
            CanonicalGraphPromotionResult,
            ExtractionPromptExperimentReport,
            GraphExternalReferenceRecord,
            GraphIdentityMembershipRecord,
            GovernedWorkflowBundle,
            IdentityBundleRecord,
            IdentityReport,
            PromotedAssertionEpistemicCollectionReport,
            ProposalRecord,
            PromotedGraphAssertionRecord,
            PromotedGraphReport,
            PromotedGraphRecanonicalizationEventRecord,
            OverlayApplicationRecord,
            SemanticCanonicalizationReport,
            SemanticCanonicalizationResult,
            TextChunkFileRecord,
            TextChunkManifest,
            ResearchAgentWhyGameTransformResult,
            WhyGameImportResult,
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
    if isinstance(value, TextChunkManifest):
        return (
            f"input_path={value.input_path} "
            f"total_chunks={value.total_chunks} "
            f"output_dir={value.output_dir}"
        )
    if isinstance(value, ExtractionPromptExperimentReport):
        return (
            f"execution_id={value.execution_id} "
            f"task={value.selection_task} "
            f"model={value.selected_model} "
            f"baseline_variant={value.baseline_variant_name} "
            f"variant_count={len(value.variant_summaries)} "
            f"case_count={value.case_count}"
        )
    if isinstance(value, TextChunkFileRecord):
        return (
            f"chunk_id={value.chunk_id} "
            f"text_length={value.text_length} "
            f"output_path={value.output_path}"
        )
    if isinstance(value, ResearchAgentWhyGameTransformResult):
        return (
            f"input_path={value.input_path} "
            f"output_path={value.output_path} "
            f"fact_count={value.fact_count}"
        )
    if isinstance(value, WhyGameImportResult):
        artifact_id = value.artifact.artifact_id if value.artifact is not None else "none"
        return (
            f"profile={value.profile.profile_id}@{value.profile.profile_version} "
            f"submissions={len(value.submissions)} "
            f"artifact={artifact_id}"
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
    if isinstance(value, CanonicalGraphPromotionResult):
        entity_ids = ",".join(entity.entity_id for entity in value.entities) or "none"
        return (
            f"assertion_id={value.assertion.assertion_id} "
            f"source_candidate_id={value.assertion.source_candidate_id} "
            f"predicate={value.assertion.predicate} "
            f"entity_ids={entity_ids}"
        )
    if isinstance(value, PromotedGraphAssertionRecord):
        return (
            f"assertion_id={value.assertion_id} "
            f"source_candidate_id={value.source_candidate_id} "
            f"predicate={value.predicate}"
        )
    if isinstance(value, PromotedGraphReport):
        assertion_ids = ",".join(
            bundle.assertion.assertion_id for bundle in value.assertion_bundles
        ) or "none"
        return (
            f"promoted_assertions={value.summary.total_assertions} "
            f"promoted_entities={value.summary.total_entities} "
            f"assertions_with_artifacts={value.summary.total_assertions_with_artifacts} "
            f"assertions_with_confidence={value.summary.total_assertions_with_confidence} "
            f"assertion_ids={assertion_ids}"
        )
    if isinstance(value, AssertionDispositionRecord):
        return (
            f"disposition_id={value.disposition_id} "
            f"assertion_id={value.assertion_id} "
            f"prior_status={value.prior_status} "
            f"target_status={value.target_status}"
        )
    if isinstance(value, PromotedAssertionEpistemicCollectionReport):
        assertion_ids = ",".join(
            report.assertion.assertion_id for report in value.assertion_reports
        ) or "none"
        return (
            f"promoted_assertions={value.summary.total_assertions} "
            f"active={value.summary.total_active} "
            f"weakened={value.summary.total_weakened} "
            f"superseded={value.summary.total_superseded} "
            f"retracted={value.summary.total_retracted} "
            f"corroboration_groups={value.summary.total_corroboration_groups} "
            f"tension_pairs={value.summary.total_tension_pairs} "
            f"assertion_ids={assertion_ids}"
        )
    if isinstance(value, SemanticCanonicalizationResult):
        event_id = value.event.event_id if value.event is not None else "none"
        return (
            f"status={value.status} "
            f"assertion_id={value.assertion.assertion_id} "
            f"predicate={value.assertion.predicate} "
            f"event_id={event_id}"
        )
    if isinstance(value, PromotedGraphRecanonicalizationEventRecord):
        return (
            f"event_id={value.event_id} "
            f"assertion_id={value.assertion_id} "
            f"before_predicate={value.before_predicate} "
            f"after_predicate={value.after_predicate}"
        )
    if isinstance(value, SemanticCanonicalizationReport):
        assertion_ids = ",".join(
            bundle.assertion.assertion_id for bundle in value.assertion_bundles
        ) or "none"
        return (
            f"promoted_assertions={value.summary.total_assertions} "
            f"recanonicalization_events={value.summary.total_recanonicalization_events} "
            f"rewritten_assertions={value.summary.total_rewritten_assertions} "
            f"assertion_ids={assertion_ids}"
        )
    if isinstance(value, IdentityBundleRecord):
        entity_ids = ",".join(
            membership.entity_id for membership in value.memberships
        ) or "none"
        return (
            f"identity_id={value.identity.identity_id} "
            f"identity_kind={value.identity.identity_kind} "
            f"entity_ids={entity_ids}"
        )
    if isinstance(value, GraphIdentityMembershipRecord):
        return (
            f"identity_id={value.identity_id} "
            f"entity_id={value.entity_id} "
            f"membership_kind={value.membership_kind}"
        )
    if isinstance(value, GraphExternalReferenceRecord):
        detail = value.external_id if value.external_id is not None else value.unresolved_note
        return (
            f"identity_id={value.identity_id} "
            f"provider={value.provider} "
            f"reference_status={value.reference_status} "
            f"detail={detail}"
        )
    if isinstance(value, IdentityReport):
        identity_ids = ",".join(
            bundle.identity.identity_id for bundle in value.identity_bundles
        ) or "none"
        return (
            f"identities={value.summary.total_identities} "
            f"memberships={value.summary.total_memberships} "
            f"external_references={value.summary.total_external_references} "
            f"identity_ids={identity_ids}"
        )
    if isinstance(value, tuple):
        return "\n".join(_to_text(item) for item in value)
    if isinstance(value, list):
        return "\n".join(_to_text(item) for item in value)
    return str(value)


__all__ = ["main"]
