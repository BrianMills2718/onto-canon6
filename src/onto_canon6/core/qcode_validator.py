"""Validate Wikidata Q-codes via the Wikidata API.

Prevents hallucinated Q-codes from corrupting entity resolution.
A wrong Q-code is worse than no Q-code — the default behavior is to
drop invalid Q-codes (return None) rather than keep them.

Uses stdlib urllib to avoid adding httpx as a dependency.
"""

from __future__ import annotations

import json
import logging
import urllib.error
import urllib.parse
import urllib.request
from functools import lru_cache

logger = logging.getLogger(__name__)

WIKIDATA_API = "https://www.wikidata.org/w/api.php"
_TIMEOUT_SECONDS = 5.0


@lru_cache(maxsize=1024)
def validate_qcode(qid: str, expected_label: str | None = None) -> bool:
    """Check if a Q-code exists on Wikidata and optionally matches an expected label.

    Returns False (invalid) on network errors — drop rather than keep a
    potentially hallucinated QID.
    """

    if not qid or not qid.startswith("Q"):
        return False
    # Basic format check: Q followed by digits only
    if not qid[1:].isdigit():
        return False

    params = urllib.parse.urlencode({
        "action": "wbgetentities",
        "ids": qid,
        "props": "labels",
        "languages": "en",
        "format": "json",
    })
    url = f"{WIKIDATA_API}?{params}"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "onto-canon6/0.1.0"})
        with urllib.request.urlopen(req, timeout=_TIMEOUT_SECONDS) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except (urllib.error.URLError, OSError, json.JSONDecodeError, TimeoutError) as exc:
        logger.warning("Q-code validation network error for %s: %s", qid, exc)
        return False

    entity = data.get("entities", {}).get(qid, {})
    if "missing" in entity:
        logger.info("Q-code %s does not exist on Wikidata", qid)
        return False

    if expected_label:
        label = entity.get("labels", {}).get("en", {}).get("value", "")
        if not _fuzzy_match(label, expected_label):
            logger.info(
                "Q-code %s label mismatch: wikidata=%r expected=%r",
                qid, label, expected_label,
            )
            return False

    return True


def _fuzzy_match(label: str, expected: str) -> bool:
    """Check if label and expected have significant word overlap.

    Compares lowercase word sets. Requires >30% overlap relative to the
    shorter set, so "The Pentagon" matches "Pentagon" and "United States
    Department of Defense" partially matches "Department of Defense".
    """

    label_words = set(label.lower().split())
    expected_words = set(expected.lower().split())
    if not label_words or not expected_words:
        return False
    overlap = len(label_words & expected_words)
    return overlap / min(len(label_words), len(expected_words)) > 0.3


def sanitize_qcode(
    qid: str | None,
    entity_name: str | None = None,
) -> str | None:
    """Return qid if it passes Wikidata validation, None otherwise.

    This is the primary entry point for callers who want a clean
    validate-or-drop semantic.
    """

    if not qid:
        return None
    if validate_qcode(qid, entity_name):
        return qid
    logger.info("Dropping invalid Q-code %s for entity %r", qid, entity_name)
    return None



__all__ = [
    "sanitize_qcode",
    "validate_qcode",
]
