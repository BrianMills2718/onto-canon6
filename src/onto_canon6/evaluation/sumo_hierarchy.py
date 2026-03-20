"""Read-only interface to the SUMO type hierarchy from onto-canon v1.

Wraps the ``sumo_plus.db`` materialized ancestor closure table to provide
O(1) ancestor checks and depth queries. Used by the ancestor-aware evaluator
to score type picks against the ontology hierarchy.

The database is a read-only external dependency — this module never writes
to it.
"""

from __future__ import annotations

import sqlite3
from functools import lru_cache
from pathlib import Path


class SUMOHierarchyError(RuntimeError):
    """Raised when the SUMO hierarchy database is missing or malformed."""


class SUMOHierarchy:
    """Read-only interface to v1's SUMO type hierarchy.

    Backed by the ``type_ancestors`` materialized closure table in
    ``sumo_plus.db``. Every type has all its ancestors pre-computed with
    depth values, making ancestor checks O(1) lookups.

    Parameters
    ----------
    db_path:
        Absolute or relative path to the ``sumo_plus.db`` file.

    Raises
    ------
    SUMOHierarchyError:
        If the database file does not exist or lacks the expected tables.
    """

    def __init__(self, db_path: Path) -> None:
        """Open a read-only connection to the SUMO hierarchy database."""
        if not db_path.exists():
            msg = f"SUMO database not found: {db_path}"
            raise SUMOHierarchyError(msg)
        self._db_path = db_path
        self._conn = sqlite3.connect(
            f"file:{db_path}?mode=ro",
            uri=True,
            check_same_thread=False,
        )
        self._conn.row_factory = sqlite3.Row
        self._validate_schema()

    def _validate_schema(self) -> None:
        """Verify the database has the required tables and columns."""
        cursor = self._conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name IN ('types', 'type_ancestors')"
        )
        tables = {row["name"] for row in cursor.fetchall()}
        missing = {"types", "type_ancestors"} - tables
        if missing:
            msg = f"SUMO database missing tables: {missing}"
            raise SUMOHierarchyError(msg)

    def is_ancestor_or_equal(self, candidate: str, reference: str) -> bool:
        """Check if *candidate* is an ancestor-or-equal of *reference*.

        Returns ``True`` when *candidate* equals *reference* or when
        *candidate* appears in the ancestor closure of *reference*.
        """
        if candidate == reference:
            return True
        cursor = self._conn.execute(
            "SELECT 1 FROM type_ancestors WHERE type_id = ? AND ancestor_id = ?",
            (reference, candidate),
        )
        return cursor.fetchone() is not None

    def is_descendant_or_equal(self, candidate: str, reference: str) -> bool:
        """Check if *candidate* is a descendant-or-equal of *reference*.

        Equivalent to ``is_ancestor_or_equal(reference, candidate)``.
        """
        return self.is_ancestor_or_equal(reference, candidate)

    @lru_cache(maxsize=2048)  # noqa: B019
    def depth(self, type_name: str) -> int:
        """Return the maximum depth of *type_name* in the hierarchy.

        Depth is the longest ancestor chain length. Root types (``Entity``,
        ``Physical``, etc.) have depth 0 if they have no ancestors in the
        closure table. Returns -1 if the type is not found.
        """
        cursor = self._conn.execute(
            "SELECT MAX(depth) as max_depth FROM type_ancestors WHERE type_id = ?",
            (type_name,),
        )
        row = cursor.fetchone()
        if row is None or row["max_depth"] is None:
            # Check if the type exists at all (root types have no ancestors).
            exists = self._conn.execute(
                "SELECT 1 FROM types WHERE id = ?", (type_name,)
            ).fetchone()
            return 0 if exists else -1
        return int(row["max_depth"])

    def type_exists(self, type_name: str) -> bool:
        """Check whether *type_name* exists in the types table."""
        cursor = self._conn.execute(
            "SELECT 1 FROM types WHERE id = ?", (type_name,)
        )
        return cursor.fetchone() is not None

    def ancestors(self, type_name: str) -> list[str]:
        """Return all ancestors of *type_name*, ordered by depth (nearest first)."""
        cursor = self._conn.execute(
            "SELECT ancestor_id FROM type_ancestors WHERE type_id = ? ORDER BY depth ASC",
            (type_name,),
        )
        return [row["ancestor_id"] for row in cursor.fetchall()]

    def subtypes(
        self, type_name: str, *, max_depth: int | None = None
    ) -> list[str]:
        """Return all descendants of *type_name*.

        Parameters
        ----------
        max_depth:
            If set, only return descendants within this many levels below
            *type_name*. ``None`` means all descendants.
        """
        if max_depth is not None:
            cursor = self._conn.execute(
                "SELECT type_id FROM type_ancestors WHERE ancestor_id = ? AND depth <= ? ORDER BY depth ASC",
                (type_name, max_depth),
            )
        else:
            cursor = self._conn.execute(
                "SELECT type_id FROM type_ancestors WHERE ancestor_id = ? ORDER BY depth ASC",
                (type_name,),
            )
        return [row["type_id"] for row in cursor.fetchall()]

    def type_count(self) -> int:
        """Return the total number of types in the hierarchy."""
        cursor = self._conn.execute("SELECT COUNT(*) as cnt FROM types")
        row = cursor.fetchone()
        return int(row["cnt"]) if row else 0

    def close(self) -> None:
        """Close the database connection."""
        self._conn.close()

    def __enter__(self) -> SUMOHierarchy:
        """Enter context manager, returning self."""
        return self

    def __exit__(self, *exc: object) -> None:
        """Exit context manager, closing the database connection."""
        self.close()
