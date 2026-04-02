"""Configuration contract tests for onto-canon6 repository defaults."""

from __future__ import annotations

from pathlib import Path

from onto_canon6.config import clear_config_cache, get_config, repo_root


def test_default_sumo_db_path_uses_repo_local_asset() -> None:
    """The default SUMO DB path should align with the successor-local contract."""

    clear_config_cache()
    config = get_config()

    assert config.evaluation.sumo_db_path == "data/sumo_plus.db"
    resolved = config.resolve_repo_path(config.evaluation.sumo_db_path)
    expected = (repo_root() / "data" / "sumo_plus.db").resolve()
    assert resolved == expected
    assert resolved.name == "sumo_plus.db"
    assert resolved.parent == Path(expected).parent


def test_default_extraction_surface_points_to_promoted_compact_candidate() -> None:
    """The repo-default extraction config should match the promoted compact lane."""

    clear_config_cache()
    config = get_config()

    assert config.extraction.selection_task == "budget_extraction"
    assert (
        config.extraction.prompt_template
        == "prompts/extraction/text_to_candidate_assertions_compact_v5.yaml"
    )
    assert (
        config.extraction.prompt_ref
        == "onto_canon6.extraction.text_to_candidate_assertions_compact_v5@3"
    )
