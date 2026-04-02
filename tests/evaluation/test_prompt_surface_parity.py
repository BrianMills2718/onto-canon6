"""Tests for live vs prompt-eval prompt surface comparison."""

from __future__ import annotations

from pathlib import Path

from onto_canon6.evaluation.prompt_surface_parity import compare_prompt_surfaces


def test_compare_prompt_surfaces_exposes_user_wrapper_difference() -> None:
    """The helper should expose both template and effective prompt-eval surfaces."""

    comparison = compare_prompt_surfaces(
        source_text="Alpha operated in Bravo.",
        profile_id="psyop_seed",
        profile_version="0.1.0",
        source_kind="text_file",
        source_ref="text://test/chunk_001",
        source_label="chunk_001.md",
        case_id="case-001",
    )

    assert len(comparison.live_messages) == 2
    assert len(comparison.prompt_eval_template_messages) == 2
    assert len(comparison.prompt_eval_effective_messages) == 2
    assert comparison.system_equal is False
    assert comparison.user_equal is True
    live_user = comparison.live_messages[1]["content"]
    parity_template_user = comparison.prompt_eval_template_messages[1]["content"]
    parity_effective_user = comparison.prompt_eval_effective_messages[1]["content"]
    assert "Source text:" in live_user
    assert "Case input:" not in live_user
    assert "{input}" in parity_template_user
    assert "Case id: case-001" not in parity_template_user
    assert "Case input:" not in parity_effective_user
    assert "Case id: case-001" not in parity_effective_user
    assert comparison.prompt_eval_input_content in parity_effective_user
    assert comparison.user_diff == ()
    assert any("hold_command_role" in line for line in comparison.system_diff)


def test_live_compact_v5_surface_includes_chunk003_residual_guards() -> None:
    """The live compact-v5 surface should carry the late analytical-prose omission rules."""

    project_root = Path(__file__).resolve().parents[2]
    comparison = compare_prompt_surfaces(
        source_text="By 2013, a substantial proportion of personnel were dedicated to PSYOP.",
        profile_id="psyop_seed",
        profile_version="0.1.0",
        source_kind="text_file",
        source_ref="text://test/chunk_003",
        source_label="chunk_003.md",
        case_id="case-003",
        live_prompt_template=project_root / "prompts" / "extraction" / "text_to_candidate_assertions_compact_v5.yaml",
    )

    live_system = comparison.live_messages[0]["content"]
    assert "retrospective assessment prose such as `was limited`, `was hampered`" in live_system
    assert "aggregate resource or staffing summaries such as `total strength`" in live_system
