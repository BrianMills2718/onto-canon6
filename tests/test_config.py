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
