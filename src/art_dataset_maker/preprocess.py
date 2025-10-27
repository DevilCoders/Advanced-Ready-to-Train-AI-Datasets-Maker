"""Text preprocessing utilities tailored for large code corpora."""
from __future__ import annotations

import re

from .config import PreprocessConfig
from .ingestion import FileRecord


WHITESPACE_RE = re.compile(r"[\t\x0b\x0c\r]+")
MULTI_NEWLINE_RE = re.compile(r"\n{3,}")


def normalise_content(content: str, config: PreprocessConfig) -> str:
    """Apply text normalisation."""
    if config.normalize_whitespace:
        content = WHITESPACE_RE.sub(" ", content)
    if config.strip_empty_lines:
        content = content.strip()
        content = MULTI_NEWLINE_RE.sub("\n\n", content)
    if config.max_line_length:
        content = _truncate_lines(content, config.max_line_length)
    return content


def _truncate_lines(content: str, max_length: int) -> str:
    lines = content.splitlines()
    truncated = [line[:max_length] for line in lines]
    return "\n".join(truncated)


def preprocess_record(record: FileRecord, config: PreprocessConfig) -> FileRecord:
    """Return a new :class:`FileRecord` with normalised content."""
    normalised = normalise_content(record.content, config)
    return FileRecord(
        path=record.path,
        relative_path=record.relative_path,
        content=normalised,
        language=record.language,
        hash=record.hash,
        size=record.size,
    )
