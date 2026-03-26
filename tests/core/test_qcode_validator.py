"""Tests for Wikidata Q-code validation.

All tests mock the Wikidata API — no network calls in the test suite.
"""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest

from onto_canon6.core.qcode_validator import (
    _fuzzy_match,
    sanitize_qcode,
    validate_qcode,
)


def _make_wikidata_response(qid: str, label: str | None = None) -> bytes:
    """Build a minimal Wikidata wbgetentities JSON response."""

    entity: dict = {}
    if label is not None:
        entity = {
            "type": "item",
            "id": qid,
            "labels": {"en": {"language": "en", "value": label}},
        }
    else:
        # Missing entity
        entity = {"id": qid, "missing": ""}
    return json.dumps({"entities": {qid: entity}}).encode("utf-8")


@pytest.fixture(autouse=True)
def _clear_lru_cache() -> None:  # type: ignore[misc]
    """Clear the lru_cache between tests so mocked responses don't leak."""

    validate_qcode.cache_clear()


class TestValidateQcode:
    """Unit tests for validate_qcode."""

    def test_valid_qcode_exists(self) -> None:
        """A Q-code that exists on Wikidata should validate."""

        mock_resp = MagicMock()
        mock_resp.read.return_value = _make_wikidata_response("Q11208", "The Pentagon")
        mock_resp.__enter__ = lambda s: s
        mock_resp.__exit__ = MagicMock(return_value=False)

        with patch("onto_canon6.core.qcode_validator.urllib.request.urlopen", return_value=mock_resp):
            assert validate_qcode("Q11208") is True

    def test_valid_qcode_with_matching_label(self) -> None:
        """A Q-code with a label matching the expected name should validate."""

        mock_resp = MagicMock()
        mock_resp.read.return_value = _make_wikidata_response("Q11208", "The Pentagon")
        mock_resp.__enter__ = lambda s: s
        mock_resp.__exit__ = MagicMock(return_value=False)

        with patch("onto_canon6.core.qcode_validator.urllib.request.urlopen", return_value=mock_resp):
            assert validate_qcode("Q11208", "Pentagon") is True

    def test_valid_qcode_with_mismatched_label(self) -> None:
        """A Q-code whose Wikidata label doesn't match should be rejected."""

        mock_resp = MagicMock()
        mock_resp.read.return_value = _make_wikidata_response("Q11200", "Supercomputer")
        mock_resp.__enter__ = lambda s: s
        mock_resp.__exit__ = MagicMock(return_value=False)

        with patch("onto_canon6.core.qcode_validator.urllib.request.urlopen", return_value=mock_resp):
            assert validate_qcode("Q11200", "Pentagon") is False

    def test_missing_qcode(self) -> None:
        """A Q-code that doesn't exist on Wikidata should be rejected."""

        mock_resp = MagicMock()
        mock_resp.read.return_value = _make_wikidata_response("Q99999999")
        mock_resp.__enter__ = lambda s: s
        mock_resp.__exit__ = MagicMock(return_value=False)

        with patch("onto_canon6.core.qcode_validator.urllib.request.urlopen", return_value=mock_resp):
            assert validate_qcode("Q99999999") is False

    def test_none_input(self) -> None:
        """None or empty string should be invalid without hitting the API."""

        assert validate_qcode("") is False
        assert validate_qcode("not_a_qcode") is False

    def test_malformed_qcode_no_digits(self) -> None:
        """Q-codes without trailing digits should be rejected."""

        assert validate_qcode("Qabc") is False
        assert validate_qcode("Q") is False

    def test_network_error_returns_false(self) -> None:
        """Network failures should treat the Q-code as invalid (drop, not keep)."""

        import urllib.error

        with patch(
            "onto_canon6.core.qcode_validator.urllib.request.urlopen",
            side_effect=urllib.error.URLError("Connection refused"),
        ):
            assert validate_qcode("Q12345") is False


class TestFuzzyMatch:
    """Unit tests for the fuzzy label matching helper."""

    def test_exact_match(self) -> None:
        assert _fuzzy_match("The Pentagon", "The Pentagon") is True

    def test_partial_overlap(self) -> None:
        assert _fuzzy_match("The Pentagon", "Pentagon") is True

    def test_no_overlap(self) -> None:
        assert _fuzzy_match("Supercomputer", "Pentagon") is False

    def test_empty_strings(self) -> None:
        assert _fuzzy_match("", "Pentagon") is False
        assert _fuzzy_match("Pentagon", "") is False

    def test_case_insensitive(self) -> None:
        assert _fuzzy_match("the pentagon", "THE PENTAGON") is True

    def test_multi_word_partial(self) -> None:
        """'Department of Defense' should match 'United States Department of Defense'."""

        assert _fuzzy_match(
            "United States Department of Defense",
            "Department of Defense",
        ) is True


class TestSanitizeQcode:
    """Unit tests for the sanitize_qcode convenience function."""

    def test_none_input_returns_none(self) -> None:
        assert sanitize_qcode(None) is None

    def test_empty_string_returns_none(self) -> None:
        assert sanitize_qcode("") is None

    def test_valid_qcode_passes_through(self) -> None:
        """A valid Q-code should be returned as-is."""

        mock_resp = MagicMock()
        mock_resp.read.return_value = _make_wikidata_response("Q11208", "The Pentagon")
        mock_resp.__enter__ = lambda s: s
        mock_resp.__exit__ = MagicMock(return_value=False)

        with patch("onto_canon6.core.qcode_validator.urllib.request.urlopen", return_value=mock_resp):
            assert sanitize_qcode("Q11208", "Pentagon") == "Q11208"

    def test_invalid_qcode_returns_none(self) -> None:
        """An invalid Q-code should be dropped to None."""

        mock_resp = MagicMock()
        mock_resp.read.return_value = _make_wikidata_response("Q99999999")
        mock_resp.__enter__ = lambda s: s
        mock_resp.__exit__ = MagicMock(return_value=False)

        with patch("onto_canon6.core.qcode_validator.urllib.request.urlopen", return_value=mock_resp):
            assert sanitize_qcode("Q99999999", "Pentagon") is None
