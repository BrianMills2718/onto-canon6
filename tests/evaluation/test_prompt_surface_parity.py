"""Tests for live vs prompt-eval prompt surface comparison."""

from __future__ import annotations

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
    assert comparison.system_equal is True
    assert comparison.user_equal is False
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
    assert any("Extract candidate assertions from this source material." in line for line in comparison.user_diff)
