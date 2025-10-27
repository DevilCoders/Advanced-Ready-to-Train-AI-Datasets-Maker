"""Quality gates and deduplication helpers for the dataset pipeline."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Set
import hashlib

from .chunking import Chunk
from .config import QualityConfig
from .ingestion import FileRecord


def _line_count(content: str) -> int:
    if not content:
        return 0
    return content.count("\n") + 1


@dataclass(slots=True)
class QualityEnforcer:
    """Applies deduplication and heuristic gates to records and chunks."""

    config: QualityConfig
    _file_hashes: Set[str] = field(default_factory=set)
    _chunk_hashes: Set[str] = field(default_factory=set)

    def is_duplicate_file(self, record: FileRecord) -> bool:
        """Return ``True`` if the file has already been seen."""

        if not self.config.deduplicate_files:
            return False
        file_hash = record.hash
        if file_hash in self._file_hashes:
            return True
        self._file_hashes.add(file_hash)
        return False

    def passes_content_gates(self, record: FileRecord) -> bool:
        """Return ``True`` if the file content satisfies quality gates."""

        content = record.content
        char_count = len(content)
        line_count = _line_count(content)
        cfg = self.config
        if char_count < cfg.min_characters:
            return False
        if cfg.max_characters is not None and char_count > cfg.max_characters:
            return False
        if line_count < cfg.min_lines:
            return False
        if cfg.max_lines is not None and line_count > cfg.max_lines:
            return False
        return True

    def is_duplicate_chunk(self, chunk: Chunk) -> bool:
        """Return ``True`` if the chunk has already been emitted."""

        if not self.config.deduplicate_chunks:
            return False
        chunk_hash = hashlib.sha1(chunk.content.encode("utf-8")).hexdigest()
        if chunk_hash in self._chunk_hashes:
            return True
        self._chunk_hashes.add(chunk_hash)
        return False
