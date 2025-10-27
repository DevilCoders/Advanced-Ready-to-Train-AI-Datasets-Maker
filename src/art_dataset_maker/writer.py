"""Dataset writer utilities."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable
import gzip
import json
import random

from .chunking import Chunk
from .config import DatasetConfig


@dataclass(slots=True)
class DatasetItem:
    """Single training sample."""

    content: str
    language: str
    metadata: dict


class DatasetWriter:
    """Stream dataset items to disk in JSONL format."""

    def __init__(self, output_dir: Path, config: DatasetConfig) -> None:
        self.output_dir = output_dir
        self.config = config
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.train_path = self.output_dir / ("train.jsonl.gz" if config.compress else "train.jsonl")
        self.eval_path = self.output_dir / ("eval.jsonl.gz" if config.compress else "eval.jsonl")

    def _open(self, path: Path):
        if path.suffix == ".gz":
            return gzip.open(path, "wt", encoding="utf-8")
        return path.open("w", encoding="utf-8")

    def write(self, chunks: Iterable[Chunk]) -> None:
        train_ratio = self.config.train_ratio
        rng = random.Random(self.config.seed)
        train_fp = self._open(self.train_path)
        eval_fp = self._open(self.eval_path)
        try:
            for chunk in chunks:
                item = DatasetItem(
                    content=chunk.content,
                    language=chunk.language,
                    metadata={
                        "source_path": chunk.source_path,
                        "start_line": chunk.start_line,
                        "end_line": chunk.end_line,
                        "hash": chunk.hash,
                    },
                )
                target = train_fp if rng.random() < train_ratio else eval_fp
                json.dump(asdict(item), target, ensure_ascii=False)
                target.write("\n")
        finally:
            train_fp.close()
            eval_fp.close()
