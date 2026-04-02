"""Deterministic tests for the scale-test extraction harness."""

from __future__ import annotations

from importlib import import_module
from pathlib import Path
from types import SimpleNamespace

import pytest


def _write_doc(tmp_path: Path, doc_id: str, text: str) -> None:
    """Create one synthetic corpus document for the harness tests."""

    (tmp_path / f"{doc_id}.txt").write_text(text, encoding="utf-8")


def test_extract_all_documents_retries_failed_docs_once(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A bounded retry pass should recover transient doc failures loudly."""

    run_scale_test = import_module("scripts.run_scale_test")
    text_extraction = import_module("onto_canon6.pipeline.text_extraction")

    _write_doc(tmp_path, "doc_01", "alpha")
    _write_doc(tmp_path, "doc_02", "beta")
    _write_doc(tmp_path, "doc_03", "gamma")

    attempts: dict[str, int] = {}

    class FakeTextExtractionService:
        """Scripted extraction boundary for retry bookkeeping tests."""

        def __init__(self, **_: object) -> None:
            pass

        def extract_and_submit(self, **kwargs: object) -> list[SimpleNamespace]:
            source_ref = str(kwargs["source_ref"])
            attempts[source_ref] = attempts.get(source_ref, 0) + 1
            if source_ref == "doc_02" and attempts[source_ref] == 1:
                raise RuntimeError("transient failure")
            if source_ref == "doc_03":
                raise RuntimeError("persistent failure")
            return [
                SimpleNamespace(
                    candidate=SimpleNamespace(review_status="accepted")
                )
            ]

    monkeypatch.setattr(
        text_extraction,
        "TextExtractionService",
        FakeTextExtractionService,
    )

    summary = run_scale_test.extract_all_documents(
        review_svc=SimpleNamespace(),
        corpus_dir=tmp_path,
        selection_task="fast_extraction",
        model_override=None,
        judge_model_override=None,
        retry_failed_docs=1,
        retry_delay_seconds=0.0,
    )

    assert summary.extracted == 2
    assert summary.accepted == 2
    assert summary.errors == 1
    assert summary.transient_failures == 1
    assert summary.retry_passes_used == 1
    assert summary.failed_docs == ("doc_03",)
    assert summary.recovered_docs == ("doc_02",)
    assert attempts == {"doc_01": 1, "doc_02": 2, "doc_03": 2}


def test_extract_all_documents_reports_clean_first_pass(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Clean extraction should not report retries or transient failures."""

    run_scale_test = import_module("scripts.run_scale_test")
    text_extraction = import_module("onto_canon6.pipeline.text_extraction")

    _write_doc(tmp_path, "doc_01", "alpha")
    _write_doc(tmp_path, "doc_02", "beta")

    class FakeTextExtractionService:
        """Always-succeed extraction boundary for summary-shape tests."""

        def __init__(self, **_: object) -> None:
            pass

        def extract_and_submit(self, **kwargs: object) -> list[SimpleNamespace]:
            del kwargs
            return [
                SimpleNamespace(
                    candidate=SimpleNamespace(review_status="accepted")
                )
            ]

    monkeypatch.setattr(
        text_extraction,
        "TextExtractionService",
        FakeTextExtractionService,
    )

    summary = run_scale_test.extract_all_documents(
        review_svc=SimpleNamespace(),
        corpus_dir=tmp_path,
        selection_task="fast_extraction",
        model_override=None,
        judge_model_override=None,
        retry_failed_docs=1,
        retry_delay_seconds=0.0,
    )

    assert summary.extracted == 2
    assert summary.accepted == 2
    assert summary.errors == 0
    assert summary.transient_failures == 0
    assert summary.retry_passes_used == 0
    assert summary.failed_docs == ()
    assert summary.recovered_docs == ()
