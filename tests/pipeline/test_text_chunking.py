"""Unit tests for deterministic long-document chunking."""

from __future__ import annotations

from onto_canon6.pipeline import TextChunkingService


def test_chunking_prefers_markdown_heading_boundaries() -> None:
    """Heading-delimited sections should become separate chunks when practical."""

    source_text = (
        "# Introduction\n"
        + ("Alpha " * 120)
        + "\n\n## Analysis\n"
        + ("Bravo " * 120)
        + "\n\n## Conclusion\n"
        + ("Charlie " * 80)
    )
    service = TextChunkingService(
        target_max_chars=900,
        min_chunk_chars=250,
        max_chunk_chars=1000,
    )

    chunks = service.chunk_source_text(
        source_text=source_text,
        source_ref="doc://psyo/report-1",
        source_label="report-1",
    )

    assert len(chunks) >= 2
    assert chunks[0].heading_path == ("Introduction",)
    assert chunks[1].heading_path[-1] in {"Analysis", "Conclusion"}
    for chunk in chunks:
        assert source_text[chunk.char_start : chunk.char_end] == chunk.content_text
        assert len(chunk.content_text) <= 1000


def test_chunking_splits_oversized_sections_by_paragraph_or_window() -> None:
    """Oversized sections should still split under the configured hard maximum."""

    source_text = (
        "# Long Section\n"
        + ("Paragraph one. " * 110)
        + "\n\n"
        + ("Paragraph two. " * 110)
        + "\n\n"
        + ("Paragraph three. " * 110)
    )
    service = TextChunkingService(
        target_max_chars=700,
        min_chunk_chars=250,
        max_chunk_chars=900,
    )

    chunks = service.chunk_source_text(
        source_text=source_text,
        source_ref="doc://psyo/report-2",
        source_label="report-2",
    )

    assert len(chunks) >= 2
    assert all(len(chunk.content_text) <= 900 for chunk in chunks)
    assert chunks[0].heading_path == ("Long Section",)
