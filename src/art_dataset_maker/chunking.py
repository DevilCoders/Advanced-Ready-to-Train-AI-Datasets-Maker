"""Chunking utilities for splitting very large files into manageable samples."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterator

from .config import ChunkConfig
from .ingestion import FileRecord


@dataclass(slots=True)
class Chunk:
    """Represents a single chunk of code ready to be serialised."""

    content: str
    language: str
    source_path: str
    start_line: int
    end_line: int
    hash: str


def chunk_record(record: FileRecord, config: ChunkConfig) -> Iterator[Chunk]:
    """Yield :class:`Chunk` objects from a :class:`FileRecord`."""
    lines = record.content.splitlines()
    if not lines:
        return
    chunk_size = config.target_chunk_size
    overlap = config.overlap
    start = 0
    while start < len(lines):
        end = min(len(lines), start + chunk_size)
        chunk_lines = lines[start:end]
        content = "\n".join(chunk_lines)
        yield Chunk(
            content=content,
            language=record.language,
            source_path=record.relative_path,
            start_line=start + 1,
            end_line=end,
            hash=record.hash,
        )
        if end == len(lines):
            break
        start = end - overlap
        if start < 0:
            start = 0
