"""Pipeline statistics utilities."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict
import json


@dataclass(slots=True)
class PipelineStats:
    """Aggregated counts collected while building a dataset."""

    files_scanned: int = 0
    files_emitted: int = 0
    files_deduplicated: int = 0
    files_filtered: int = 0
    chunks_generated: int = 0
    chunks_emitted: int = 0
    chunks_deduplicated: int = 0
    language_distribution: Dict[str, int] = field(default_factory=dict)
    source_file_counts: Dict[str, int] = field(default_factory=dict)

    def record_language(self, language: str) -> None:
        self.language_distribution[language] = self.language_distribution.get(language, 0) + 1

    def record_source(self, source: str) -> None:
        self.source_file_counts[source] = self.source_file_counts.get(source, 0) + 1

    def as_dict(self) -> dict:
        return {
            "files_scanned": self.files_scanned,
            "files_emitted": self.files_emitted,
            "files_deduplicated": self.files_deduplicated,
            "files_filtered": self.files_filtered,
            "chunks_generated": self.chunks_generated,
            "chunks_emitted": self.chunks_emitted,
            "chunks_deduplicated": self.chunks_deduplicated,
            "language_distribution": dict(sorted(self.language_distribution.items())),
            "source_file_counts": dict(sorted(self.source_file_counts.items())),
        }

    def write(self, output_dir: Path) -> Path:
        """Persist statistics to ``dataset_stats.json`` and return the path."""

        output_dir.mkdir(parents=True, exist_ok=True)
        path = output_dir / "dataset_stats.json"
        path.write_text(json.dumps(self.as_dict(), indent=2, sort_keys=True), encoding="utf-8")
        return path

    def format_summary(self) -> str:
        """Return a concise human readable summary string."""

        return (
            f"files: {self.files_emitted}/{self.files_scanned} emitted, "
            f"deduped: {self.files_deduplicated}, filtered: {self.files_filtered} | "
            f"chunks: {self.chunks_emitted}/{self.chunks_generated} emitted, "
            f"deduped: {self.chunks_deduplicated} | sources: {len(self.source_file_counts)}"
        )
