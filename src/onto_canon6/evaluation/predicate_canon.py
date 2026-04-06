"""Read-only interface to the Predicate Canon from onto-canon v1.

Wraps the ``predicates`` and ``role_slots`` tables in ``sumo_plus.db`` to
provide lemma lookup, single-sense detection, role constraint resolution,
and candidate listing for the progressive disclosure extraction pipeline
(Plan 0018, Slice A).

The database is a read-only external dependency -- this module never writes
to it.  The same ``sumo_plus.db`` used by :class:`SUMOHierarchy` is reused
here; no new config fields are required.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

from pydantic import BaseModel, ConfigDict


class PredicateCanonError(RuntimeError):
    """Raised when the Predicate Canon database is missing or malformed."""


class RoleSlotInfo(BaseModel):
    """One argument slot for a predicate sense.

    Captures the named label (e.g. ``Agent``), PropBank arg position
    (e.g. ``ARG0``), optional abstract role and SUMO type constraint,
    and whether the slot is required.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    named_label: str
    arg_position: str
    abstract_role: str | None
    type_constraint: str | None
    required: bool


class PredicateInfo(BaseModel):
    """Core metadata for a single predicate sense.

    Maps a PropBank sense to a SUMO process type, with provenance
    fields for the frame mapping and confidence score.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    predicate_id: str
    propbank_sense_id: str | None
    process_type: str | None
    lemma: str | None
    sense_num: int | None
    description: str | None
    frame_id: str | None
    mapping_confidence: float | None
    is_static: bool


class PredicateMatch(BaseModel):
    """A predicate sense together with its role slots.

    Returned by :meth:`PredicateCanon.lookup_by_lemma` so that callers
    get the full predicate metadata and its argument schema in one object.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    predicate_id: str
    propbank_sense_id: str | None
    process_type: str | None
    description: str | None
    frame_id: str | None
    mapping_confidence: float | None
    role_slots: tuple[RoleSlotInfo, ...]


class PredicateCanon:
    """Read-only interface to v1's Predicate Canon.

    Backed by the ``predicates`` and ``role_slots`` tables in
    ``sumo_plus.db``.  Provides lemma-based lookup, single-sense
    detection, role constraint resolution, and process-type queries
    for the progressive disclosure extraction pipeline.

    Parameters
    ----------
    db_path:
        Absolute or relative path to the ``sumo_plus.db`` file.

    Raises
    ------
    PredicateCanonError:
        If the database file does not exist or lacks the expected tables.
    """

    def __init__(self, db_path: Path) -> None:
        """Open a read-only connection to the Predicate Canon database."""
        if not db_path.exists():
            msg = f"Predicate Canon database not found: {db_path}"
            raise PredicateCanonError(msg)
        self._db_path = db_path
        self._conn = sqlite3.connect(
            f"file:{db_path}?mode=ro",
            uri=True,
            check_same_thread=False,
        )
        self._conn.row_factory = sqlite3.Row
        self._validate_schema()

    def _validate_schema(self) -> None:
        """Verify the database has the required tables."""
        cursor = self._conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' "
            "AND name IN ('predicates', 'role_slots')"
        )
        tables = {row["name"] for row in cursor.fetchall()}
        missing = {"predicates", "role_slots"} - tables
        if missing:
            msg = f"Predicate Canon database missing tables: {missing}"
            raise PredicateCanonError(msg)

    def _fetch_role_slots(self, predicate_id: str) -> tuple[RoleSlotInfo, ...]:
        """Fetch all role slots for a predicate, ordered by arg position.

        Returns an empty tuple when the predicate has no role slots.
        """
        cursor = self._conn.execute(
            "SELECT named_label, arg_position, abstract_role, "
            "type_constraint, required "
            "FROM role_slots WHERE event_sense_id = ? "
            "ORDER BY arg_position",
            (predicate_id,),
        )
        return tuple(
            RoleSlotInfo(
                named_label=row["named_label"],
                arg_position=row["arg_position"],
                abstract_role=row["abstract_role"],
                type_constraint=row["type_constraint"],
                required=bool(row["required"]),
            )
            for row in cursor.fetchall()
        )

    def lookup_by_lemma(self, lemma: str) -> list[PredicateMatch]:
        """Find all predicate senses matching *lemma*.

        Returns a list of :class:`PredicateMatch` objects, each containing
        the predicate metadata and its full role-slot schema.  Returns an
        empty list when no predicates match the lemma.
        """
        cursor = self._conn.execute(
            "SELECT name, propbank_sense_id, process_type, description, "
            "frame_id, mapping_confidence "
            "FROM predicates WHERE lemma = ? ORDER BY sense_num",
            (lemma,),
        )
        results: list[PredicateMatch] = []
        for row in cursor.fetchall():
            pred_id: str = row["name"]
            results.append(
                PredicateMatch(
                    predicate_id=pred_id,
                    propbank_sense_id=row["propbank_sense_id"],
                    process_type=row["process_type"],
                    description=row["description"],
                    frame_id=row["frame_id"],
                    mapping_confidence=row["mapping_confidence"],
                    role_slots=self._fetch_role_slots(pred_id),
                )
            )
        return results

    def is_single_sense(self, lemma: str) -> bool:
        """Return True if *lemma* maps to exactly one predicate sense.

        This is the early-exit condition for Pass 2: single-sense lemmas
        can be assigned deterministically without an LLM disambiguation call.
        Returns False for unknown lemmas (zero senses).
        """
        return self.lemma_sense_count(lemma) == 1

    def lemma_sense_count(self, lemma: str) -> int:
        """Return the number of predicate senses for *lemma*."""
        cursor = self._conn.execute(
            "SELECT COUNT(*) AS cnt FROM predicates WHERE lemma = ?",
            (lemma,),
        )
        row = cursor.fetchone()
        return int(row["cnt"]) if row else 0

    def get_role_constraints(self, predicate_id: str) -> dict[str, str]:
        """Return ``{named_label: type_constraint}`` for *predicate_id*.

        Only includes slots that have a non-null type constraint.
        Returns an empty dict when the predicate has no constrained slots
        or does not exist.
        """
        cursor = self._conn.execute(
            "SELECT named_label, type_constraint FROM role_slots "
            "WHERE event_sense_id = ? AND type_constraint IS NOT NULL "
            "ORDER BY arg_position",
            (predicate_id,),
        )
        return {row["named_label"]: row["type_constraint"] for row in cursor.fetchall()}

    def get_role_slots(self, predicate_id: str) -> list[RoleSlotInfo]:
        """Return full role-slot info for *predicate_id*.

        Returns an empty list when the predicate has no role slots or
        does not exist.
        """
        return list(self._fetch_role_slots(predicate_id))

    def get_predicate(self, predicate_id: str) -> PredicateInfo | None:
        """Look up a predicate by its exact name (primary key).

        Returns ``None`` when the predicate does not exist.
        """
        cursor = self._conn.execute(
            "SELECT name, propbank_sense_id, process_type, lemma, "
            "sense_num, description, frame_id, mapping_confidence, is_static "
            "FROM predicates WHERE name = ?",
            (predicate_id,),
        )
        row = cursor.fetchone()
        if row is None:
            return None
        return PredicateInfo(
            predicate_id=row["name"],
            propbank_sense_id=row["propbank_sense_id"],
            process_type=row["process_type"],
            lemma=row["lemma"],
            sense_num=row["sense_num"],
            description=row["description"],
            frame_id=row["frame_id"],
            mapping_confidence=row["mapping_confidence"],
            is_static=bool(row["is_static"]),
        )

    def list_lemmas_for_process_type(self, process_type: str) -> list[str]:
        """Return distinct lemmas that map to a given SUMO *process_type*.

        Returns an empty list when no predicates match the process type.
        """
        cursor = self._conn.execute(
            "SELECT DISTINCT lemma FROM predicates "
            "WHERE process_type = ? ORDER BY lemma",
            (process_type,),
        )
        return [row["lemma"] for row in cursor.fetchall()]

    def close(self) -> None:
        """Close the database connection."""
        self._conn.close()

    def __enter__(self) -> PredicateCanon:
        """Enter context manager, returning self."""
        return self

    def __exit__(self, *exc: object) -> None:
        """Exit context manager, closing the database connection."""
        self.close()
