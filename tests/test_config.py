"""Configuration contract tests for onto-canon6 repository defaults."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml
from pydantic import ValidationError

from onto_canon6.config import AppConfig, clear_config_cache, get_config, repo_root


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


def test_config_rejects_unknown_top_level_key() -> None:
    """AppConfig extra='forbid' must raise ValidationError for unknown top-level keys."""
    config_path = repo_root() / "config" / "config.yaml"
    raw = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    raw["unknown_surprise"] = "should_fail"
    with pytest.raises(ValidationError, match="unknown_surprise"):
        AppConfig.model_validate(raw)


def test_config_rejects_negative_budget() -> None:
    """ExtractionConfig must reject max_budget_usd <= 0."""
    config_path = repo_root() / "config" / "config.yaml"
    raw = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    raw["extraction"]["max_budget_usd"] = -1.0
    with pytest.raises(ValidationError):
        AppConfig.model_validate(raw)


def test_config_rejects_invalid_review_mode() -> None:
    """PipelineConfig review_mode must be one of 'human', 'auto', 'llm'."""
    config_path = repo_root() / "config" / "config.yaml"
    raw = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    raw["pipeline"]["review_mode"] = "turbo_yolo"
    with pytest.raises(ValidationError):
        AppConfig.model_validate(raw)


def test_config_model_is_gemini_2_5_flash() -> None:
    """Verify the runtime default model is gemini/gemini-2.5-flash."""
    clear_config_cache()
    config = get_config()
    assert config.extraction.model_override == "gemini/gemini-2.5-flash"
    assert config.resolution.model_override == "gemini/gemini-2.5-flash"
