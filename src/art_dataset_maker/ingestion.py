"""Facilities for reading code from massive repositories in a memory efficient way."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterator
import hashlib
import os

from .config import IngestionConfig


@dataclass(slots=True)
class FileRecord:
    """A lightweight representation of a file within the dataset."""

    path: Path
    relative_path: str
    content: str
    language: str
    hash: str
    size: int


LANGUAGE_EXTENSIONS = {
    ".py": "python",
    ".pyw": "python",
    ".pyi": "python",
    ".js": "javascript",
    ".mjs": "javascript",
    ".cjs": "javascript",
    ".ts": "typescript",
    ".tsx": "typescript",
    ".jsx": "javascript",
    ".java": "java",
    ".kt": "kotlin",
    ".kts": "kotlin",
    ".scala": "scala",
    ".go": "go",
    ".rs": "rust",
    ".swift": "swift",
    ".m": "objective-c",
    ".mm": "objective-c++",
    ".cpp": "cpp",
    ".cxx": "cpp",
    ".cc": "cpp",
    ".hpp": "cpp",
    ".hxx": "cpp",
    ".h": "c",
    ".c": "c",
    ".cs": "csharp",
    ".rb": "ruby",
    ".php": "php",
    ".pl": "perl",
    ".pm": "perl",
    ".sh": "shell",
    ".bash": "shell",
    ".zsh": "shell",
    ".fish": "shell",
    ".ksh": "shell",
    ".ps1": "powershell",
    ".psm1": "powershell",
    ".cmd": "cmd",
    ".bat": "cmd",
    ".lua": "lua",
    ".r": "r",
    ".jl": "julia",
    ".dart": "dart",
    ".sql": "sql",
    ".yml": "yaml",
    ".yaml": "yaml",
    ".json": "json",
    ".toml": "toml",
    ".ini": "ini",
    ".cfg": "ini",
    ".md": "markdown",
    ".txt": "text",
    ".terminal": "terminal",
    ".cmdlog": "terminal",
}


def is_binary_string(data: bytes) -> bool:
    """Heuristic check to determine if the byte sequence is binary."""
    if b"\0" in data:
        return True
    text_characters = bytes({7, 8, 9, 10, 12, 13, 27} | set(range(0x20, 0x100)))
    return bool(data.translate(None, text_characters))


def detect_language(path: Path) -> str:
    return LANGUAGE_EXTENSIONS.get(path.suffix.lower(), "unknown")


def iter_source_files(root: Path, config: IngestionConfig) -> Iterator[FileRecord]:
    """Yield :class:`FileRecord` instances for each file in *root*."""
    max_bytes = config.max_file_size_mb * 1024 * 1024
    for current_root, dirs, files in os.walk(root, followlinks=config.follow_symlinks):
        dirs[:] = [d for d in dirs if d not in config.exclude_dirs]
        for filename in files:
            path = Path(current_root, filename)
            rel = path.relative_to(root)
            if path.suffix and config.include_extensions and path.suffix.lower() not in config.include_extensions:
                continue
            size = path.stat().st_size
            if size > max_bytes:
                continue
            try:
                data = path.read_bytes()
            except OSError:
                continue
            if is_binary_string(data):
                continue
            try:
                text = data.decode("utf-8")
            except UnicodeDecodeError:
                try:
                    text = data.decode("latin-1")
                except UnicodeDecodeError:
                    continue
            file_hash = hashlib.sha1(data).hexdigest()
            language = detect_language(path)
            yield FileRecord(
                path=path,
                relative_path=str(rel).replace(os.sep, "/"),
                content=text,
                language=language,
                hash=file_hash,
                size=size,
            )
