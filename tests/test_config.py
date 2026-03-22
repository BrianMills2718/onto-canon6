"""Configuration contract tests for onto-canon6 repository defaults."""

from __future__ import annotations

from pathlib import Path

from onto_canon6.config import clear_config_cache, get_config, repo_root


def test_default_sumo_db_path_uses_donor_repo() -> None:
    """The default SUMO DB path should align with the donor repo contract.

    onto-canon6 evaluation and progressive extraction use the donor
    ``sumo_plus.db`` asset by default. Keeping that path explicit prevents a
    copied local SQLite file from becoming an accidental required repo asset.
    """

    clear_config_cache()
    config = get_config()

    assert config.evaluation.sumo_db_path == "../onto-canon/data/sumo_plus.db"
    resolved = config.resolve_repo_path(config.evaluation.sumo_db_path)
    expected = (repo_root() / ".." / "onto-canon" / "data" / "sumo_plus.db").resolve()
    assert resolved == expected
    assert resolved.name == "sumo_plus.db"
    assert resolved.parent == Path(expected).parent
