"""Deterministic source-text chunking for real long-document runs.

The first non-fixture investigation showed that whole-report extraction can
overflow the structured-output budget even when the rest of the workflow is
sound. This module provides the smallest useful fix:

1. split markdown-like analyst documents on heading boundaries when possible;
2. fall back to paragraph or fixed-window chunking when a section is still too
   large; and
3. emit explicit chunk files plus a manifest so later extraction runs stay
   observable and reproducible.
"""

from __future__ import annotations

from dataclasses import dataclass
import re
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ..config import get_config

_HEADING_PATTERN = re.compile(r"(?m)^(#{1,6})[ \t]+(.+?)\s*$")
_PARAGRAPH_BREAK_PATTERN = re.compile(r"\n[ \t]*\n+")


@dataclass(frozen=True)
class _TextSlice:
    """One exact source-text slice with heading context."""

    char_start: int
    char_end: int
    heading_path: tuple[str, ...]


class TextChunkRecord(BaseModel):
    """One deterministic chunk over the original source text."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    chunk_id: str = Field(min_length=1)
    source_ref: str = Field(min_length=1)
    source_label: str | None = None
    char_start: int = Field(ge=0)
    char_end: int = Field(ge=1)
    heading_path: tuple[str, ...] = ()
    content_text: str = Field(min_length=1)

    @model_validator(mode="after")
    def _validate_bounds(self) -> "TextChunkRecord":
        """Require the chunk bounds to describe the content text truthfully."""

        if self.char_end <= self.char_start:
            raise ValueError("char_end must be greater than char_start")
        if len(self.content_text) != self.char_end - self.char_start:
            raise ValueError("content_text length must equal the slice width")
        return self


class TextChunkFileRecord(BaseModel):
    """One persisted chunk file plus the original-source slice it represents."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    chunk_id: str = Field(min_length=1)
    file_name: str = Field(min_length=1)
    output_path: str = Field(min_length=1)
    char_start: int = Field(ge=0)
    char_end: int = Field(ge=1)
    heading_path: tuple[str, ...] = ()
    text_length: int = Field(ge=1)


class TextChunkManifest(BaseModel):
    """Summary of chunk files written for one source document."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    input_path: str = Field(min_length=1)
    output_dir: str = Field(min_length=1)
    source_ref: str = Field(min_length=1)
    source_label: str | None = None
    input_char_count: int = Field(ge=1)
    total_chunks: int = Field(ge=1)
    chunks: tuple[TextChunkFileRecord, ...]


class TextChunkingService:
    """Split large analyst documents into deterministic extraction chunks."""

    def __init__(
        self,
        *,
        target_max_chars: int | None = None,
        min_chunk_chars: int | None = None,
        max_chunk_chars: int | None = None,
    ) -> None:
        """Use config-backed defaults unless an explicit override is provided."""

        config = get_config()
        self._target_max_chars = target_max_chars or config.chunking.target_max_chars
        self._min_chunk_chars = min_chunk_chars or config.chunking.min_chunk_chars
        self._max_chunk_chars = max_chunk_chars or config.chunking.max_chunk_chars
        if self._min_chunk_chars > self._target_max_chars:
            raise ValueError("min_chunk_chars must be less than or equal to target_max_chars")
        if self._target_max_chars > self._max_chunk_chars:
            raise ValueError("target_max_chars must be less than or equal to max_chunk_chars")

    @property
    def target_max_chars(self) -> int:
        """Return the configured soft chunk-size target."""

        return self._target_max_chars

    @property
    def min_chunk_chars(self) -> int:
        """Return the configured minimum useful chunk size."""

        return self._min_chunk_chars

    @property
    def max_chunk_chars(self) -> int:
        """Return the configured hard maximum chunk size."""

        return self._max_chunk_chars

    def chunk_source_text(
        self,
        *,
        source_text: str,
        source_ref: str,
        source_label: str | None = None,
    ) -> tuple[TextChunkRecord, ...]:
        """Split one source document into exact chunk records."""

        if not source_text.strip():
            raise ValueError("source_text must be non-empty")
        if not source_ref.strip():
            raise ValueError("source_ref must be non-empty")

        slices = _markdown_section_slices(source_text)
        chunk_slices: list[_TextSlice] = []
        pending_start: int | None = None
        pending_end: int | None = None
        pending_heading_path: tuple[str, ...] = ()

        for text_slice in slices:
            slice_length = text_slice.char_end - text_slice.char_start
            if slice_length > self._max_chunk_chars:
                if pending_start is not None:
                    chunk_slices.append(
                        _TextSlice(
                            char_start=pending_start,
                            char_end=pending_end or pending_start,
                            heading_path=pending_heading_path,
                        )
                    )
                    pending_start = None
                    pending_end = None
                    pending_heading_path = ()
                chunk_slices.extend(
                    _split_large_slice(
                        source_text=source_text,
                        text_slice=text_slice,
                        target_max_chars=self._target_max_chars,
                        min_chunk_chars=self._min_chunk_chars,
                        max_chunk_chars=self._max_chunk_chars,
                    )
                )
                continue

            if pending_start is None:
                pending_start = text_slice.char_start
                pending_end = text_slice.char_end
                pending_heading_path = text_slice.heading_path
                continue

            proposed_end = text_slice.char_end
            proposed_length = proposed_end - pending_start
            current_length = (pending_end or pending_start) - pending_start
            if proposed_length > self._max_chunk_chars:
                chunk_slices.append(
                    _TextSlice(
                        char_start=pending_start,
                        char_end=pending_end or pending_start,
                        heading_path=pending_heading_path,
                    )
                )
                pending_start = text_slice.char_start
                pending_end = text_slice.char_end
                pending_heading_path = text_slice.heading_path
                continue
            if proposed_length > self._target_max_chars and current_length >= self._min_chunk_chars:
                chunk_slices.append(
                    _TextSlice(
                        char_start=pending_start,
                        char_end=pending_end or pending_start,
                        heading_path=pending_heading_path,
                    )
                )
                pending_start = text_slice.char_start
                pending_end = text_slice.char_end
                pending_heading_path = text_slice.heading_path
                continue
            pending_end = text_slice.char_end

        if pending_start is not None:
            chunk_slices.append(
                _TextSlice(
                    char_start=pending_start,
                    char_end=pending_end or pending_start,
                    heading_path=pending_heading_path,
                )
            )

        return tuple(
            TextChunkRecord(
                chunk_id=f"chunk_{index:03d}",
                source_ref=source_ref.strip(),
                source_label=source_label.strip() if source_label is not None else None,
                char_start=text_slice.char_start,
                char_end=text_slice.char_end,
                heading_path=text_slice.heading_path,
                content_text=source_text[text_slice.char_start : text_slice.char_end],
            )
            for index, text_slice in enumerate(chunk_slices, start=1)
        )

    def write_chunk_files(
        self,
        *,
        input_path: Path,
        output_dir: Path,
        source_ref: str,
        source_label: str | None = None,
    ) -> TextChunkManifest:
        """Write chunk files and return a manifest for the current source."""

        source_text = input_path.read_text(encoding="utf-8")
        chunks = self.chunk_source_text(
            source_text=source_text,
            source_ref=source_ref,
            source_label=source_label,
        )
        if output_dir.exists() and any(output_dir.iterdir()):
            raise ValueError(f"output_dir must be empty before writing chunks: {output_dir}")
        output_dir.mkdir(parents=True, exist_ok=True)

        stem = input_path.stem
        persisted_chunks: list[TextChunkFileRecord] = []
        for chunk in chunks:
            file_name = f"{stem}__{chunk.chunk_id}.md"
            output_path = output_dir / file_name
            output_path.write_text(chunk.content_text, encoding="utf-8")
            persisted_chunks.append(
                TextChunkFileRecord(
                    chunk_id=chunk.chunk_id,
                    file_name=file_name,
                    output_path=str(output_path),
                    char_start=chunk.char_start,
                    char_end=chunk.char_end,
                    heading_path=chunk.heading_path,
                    text_length=len(chunk.content_text),
                )
            )

        return TextChunkManifest(
            input_path=str(input_path),
            output_dir=str(output_dir),
            source_ref=source_ref,
            source_label=source_label,
            input_char_count=len(source_text),
            total_chunks=len(persisted_chunks),
            chunks=tuple(persisted_chunks),
        )


def _markdown_section_slices(source_text: str) -> list[_TextSlice]:
    """Split the source into heading-scoped slices when markdown headings exist."""

    matches = list(_HEADING_PATTERN.finditer(source_text))
    if not matches:
        return [_TextSlice(char_start=0, char_end=len(source_text), heading_path=())]

    slices: list[_TextSlice] = []
    first_heading = matches[0]
    if first_heading.start() > 0:
        slices.append(_TextSlice(char_start=0, char_end=first_heading.start(), heading_path=()))

    heading_stack: list[tuple[int, str]] = []
    for index, match in enumerate(matches):
        level = len(match.group(1))
        title = match.group(2).strip()
        while heading_stack and heading_stack[-1][0] >= level:
            heading_stack.pop()
        heading_stack.append((level, title))
        next_start = matches[index + 1].start() if index + 1 < len(matches) else len(source_text)
        slices.append(
            _TextSlice(
                char_start=match.start(),
                char_end=next_start,
                heading_path=tuple(item[1] for item in heading_stack),
            )
        )
    return [text_slice for text_slice in slices if text_slice.char_end > text_slice.char_start]


def _split_large_slice(
    *,
    source_text: str,
    text_slice: _TextSlice,
    target_max_chars: int,
    min_chunk_chars: int,
    max_chunk_chars: int,
) -> list[_TextSlice]:
    """Split one oversized slice by paragraphs, then by fixed windows if needed."""

    paragraph_slices = _paragraph_slices(source_text, text_slice)
    chunks: list[_TextSlice] = []
    pending_start: int | None = None
    pending_end: int | None = None

    for paragraph_slice in paragraph_slices:
        paragraph_length = paragraph_slice.char_end - paragraph_slice.char_start
        if paragraph_length > max_chunk_chars:
            if pending_start is not None:
                chunks.append(
                    _TextSlice(
                        char_start=pending_start,
                        char_end=pending_end or pending_start,
                        heading_path=text_slice.heading_path,
                    )
                )
                pending_start = None
                pending_end = None
            chunks.extend(
                _window_split_slice(
                    source_text=source_text,
                    text_slice=paragraph_slice,
                    heading_path=text_slice.heading_path,
                    min_chunk_chars=min_chunk_chars,
                    max_chunk_chars=max_chunk_chars,
                )
            )
            continue

        if pending_start is None:
            pending_start = paragraph_slice.char_start
            pending_end = paragraph_slice.char_end
            continue

        proposed_end = paragraph_slice.char_end
        proposed_length = proposed_end - pending_start
        current_length = (pending_end or pending_start) - pending_start
        if proposed_length > max_chunk_chars:
            chunks.append(
                _TextSlice(
                    char_start=pending_start,
                    char_end=pending_end or pending_start,
                    heading_path=text_slice.heading_path,
                )
            )
            pending_start = paragraph_slice.char_start
            pending_end = paragraph_slice.char_end
            continue
        if proposed_length > target_max_chars and current_length >= min_chunk_chars:
            chunks.append(
                _TextSlice(
                    char_start=pending_start,
                    char_end=pending_end or pending_start,
                    heading_path=text_slice.heading_path,
                )
            )
            pending_start = paragraph_slice.char_start
            pending_end = paragraph_slice.char_end
            continue
        pending_end = paragraph_slice.char_end

    if pending_start is not None:
        chunks.append(
            _TextSlice(
                char_start=pending_start,
                char_end=pending_end or pending_start,
                heading_path=text_slice.heading_path,
            )
        )
    return chunks


def _paragraph_slices(source_text: str, text_slice: _TextSlice) -> list[_TextSlice]:
    """Split one section into paragraph slices while preserving exact offsets."""

    relative_text = source_text[text_slice.char_start : text_slice.char_end]
    breaks = list(_PARAGRAPH_BREAK_PATTERN.finditer(relative_text))
    if not breaks:
        return [text_slice]

    slices: list[_TextSlice] = []
    cursor = 0
    for match in breaks:
        start = cursor
        end = match.start()
        if end > start:
            slices.append(
                _TextSlice(
                    char_start=text_slice.char_start + start,
                    char_end=text_slice.char_start + end,
                    heading_path=text_slice.heading_path,
                )
            )
        cursor = match.end()
    if cursor < len(relative_text):
        slices.append(
            _TextSlice(
                char_start=text_slice.char_start + cursor,
                char_end=text_slice.char_end,
                heading_path=text_slice.heading_path,
            )
        )
    return [slice_ for slice_ in slices if slice_.char_end > slice_.char_start]


def _window_split_slice(
    *,
    source_text: str,
    text_slice: _TextSlice,
    heading_path: tuple[str, ...],
    min_chunk_chars: int,
    max_chunk_chars: int,
) -> list[_TextSlice]:
    """Split one oversized paragraph-like slice by fixed windows."""

    slices: list[_TextSlice] = []
    cursor = text_slice.char_start
    while cursor < text_slice.char_end:
        hard_end = min(cursor + max_chunk_chars, text_slice.char_end)
        if hard_end == text_slice.char_end:
            slices.append(_TextSlice(char_start=cursor, char_end=hard_end, heading_path=heading_path))
            break
        break_at = _preferred_break_index(
            source_text=source_text,
            start=cursor,
            hard_end=hard_end,
            min_chunk_chars=min_chunk_chars,
        )
        slices.append(_TextSlice(char_start=cursor, char_end=break_at, heading_path=heading_path))
        cursor = break_at
    return slices


def _preferred_break_index(
    *,
    source_text: str,
    start: int,
    hard_end: int,
    min_chunk_chars: int,
) -> int:
    """Prefer newline or space breaks before falling back to the hard limit."""

    search_start = min(start + min_chunk_chars, hard_end)
    preferred_newline = source_text.rfind("\n", search_start, hard_end)
    if preferred_newline > start:
        return preferred_newline
    preferred_space = source_text.rfind(" ", search_start, hard_end)
    if preferred_space > start:
        return preferred_space
    return hard_end


__all__ = [
    "TextChunkFileRecord",
    "TextChunkManifest",
    "TextChunkRecord",
    "TextChunkingService",
]
