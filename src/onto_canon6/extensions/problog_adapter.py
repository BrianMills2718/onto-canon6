"""ProbLog fact-store adapter for onto-canon6 promoted assertions.

Loads promoted assertions from SQLite, converts to ProbLog terms,
evaluates rules, and returns derived facts with probability propagation.

Architecture decision (Gap 8 spike): Use ProbLog, not custom Datalog.
Placement: onto-canon6 owns the fact-store adapter (facts are here).
Rule engine integration with llm_client deferred until a consumer needs it.
"""

from __future__ import annotations

import json
import logging
import re
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class DerivedFact:
    """One fact derived by ProbLog rule evaluation."""
    term: str
    probability: float


@dataclass(frozen=True)
class RuleEvaluationResult:
    """Summary of one ProbLog rule evaluation run."""
    input_facts: int
    rules_applied: int
    derived_facts: list[DerivedFact]
    errors: list[str]


def _sanitize_atom(name: str) -> str:
    """Convert entity name to a valid Prolog atom."""
    s = name.lower().replace("'", "").replace('"', '').replace(' ', '_')
    s = re.sub(r'[^a-z0-9_]', '', s)
    if s and s[0].isdigit():
        s = 'e_' + s
    return s or 'unknown'


def load_facts_from_db(
    db_path: Path,
    predicate_mapping: dict[str, str] | None = None,
) -> list[str]:
    """Load promoted assertions as ProbLog fact terms.

    Each promoted assertion with entity role fillers becomes a ProbLog fact.
    Confidence from epistemic assessments is used as probability annotation.

    ``predicate_mapping`` maps onto-canon6 predicate IDs to ProbLog functor
    names. Unmapped predicates use a sanitized version of the predicate ID.
    """
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row

    try:
        assertions = conn.execute(
            "SELECT assertion_id, predicate, normalized_body_json, source_candidate_id "
            "FROM promoted_graph_assertions"
        ).fetchall()
    except sqlite3.OperationalError:
        conn.close()
        return []  # Table doesn't exist yet

    # Load confidence scores if available
    confidences: dict[str, float] = {}
    try:
        for row in conn.execute(
            "SELECT candidate_id, confidence_score FROM epistemic_confidence_assessments"
        ):
            confidences[row['candidate_id']] = row['confidence_score']
    except sqlite3.OperationalError:
        pass  # Table doesn't exist yet

    conn.close()

    if predicate_mapping is None:
        predicate_mapping = {}

    facts: list[str] = []
    for a in assertions:
        body = json.loads(a['normalized_body_json'])
        roles = body.get('roles', {})
        conf = confidences.get(a['source_candidate_id'], 1.0)

        # Extract entity names from roles
        entity_args: list[str] = []
        for role_name in sorted(roles.keys()):
            fillers = roles[role_name]
            for filler in fillers:
                if filler.get('kind') == 'entity' and filler.get('name'):
                    entity_args.append(_sanitize_atom(filler['name']))

        if not entity_args:
            continue

        pred_id = a['predicate']
        functor = predicate_mapping.get(pred_id, _sanitize_atom(pred_id.replace(':', '_')))
        args = ', '.join(entity_args)
        facts.append(f"{conf}::{functor}({args}).")

    return facts


def evaluate_rules(
    *,
    db_path: Path,
    rules: str,
    predicate_mapping: dict[str, str] | None = None,
) -> RuleEvaluationResult:
    """Load facts from DB, combine with rules, evaluate with ProbLog.

    ``rules`` is a ProbLog program string containing rule definitions
    and ``query(...)`` directives.
    """
    facts = load_facts_from_db(db_path, predicate_mapping)
    if not facts:
        return RuleEvaluationResult(
            input_facts=0,
            rules_applied=0,
            derived_facts=[],
            errors=["No facts loaded from database"],
        )

    full_program = "\n".join(facts) + "\n" + rules
    errors: list[str] = []

    try:
        from problog.program import PrologString
        from problog import get_evaluatable

        result = get_evaluatable().create_from(PrologString(full_program)).evaluate()
        derived = [
            DerivedFact(term=str(fact), probability=prob)
            for fact, prob in sorted(result.items(), key=lambda x: -x[1])
        ]
        rule_count = rules.count(':-')
        return RuleEvaluationResult(
            input_facts=len(facts),
            rules_applied=rule_count,
            derived_facts=derived,
            errors=errors,
        )
    except ImportError:
        errors.append("problog not installed: pip install problog")
        return RuleEvaluationResult(
            input_facts=len(facts),
            rules_applied=0,
            derived_facts=[],
            errors=errors,
        )
    except Exception as e:
        errors.append(str(e))
        return RuleEvaluationResult(
            input_facts=len(facts),
            rules_applied=0,
            derived_facts=[],
            errors=errors,
        )


__all__ = [
    "DerivedFact",
    "RuleEvaluationResult",
    "evaluate_rules",
    "load_facts_from_db",
]
