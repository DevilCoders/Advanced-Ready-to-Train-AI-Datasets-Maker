"""Utilities for extracting terminal command corpora from repositories."""
from __future__ import annotations

from pathlib import Path
from typing import Sequence
import fnmatch

from .config import CommandSourceConfig

PROMPT_PREFIXES = (
    "$",
    "#",
    "%",
    ">",
    "PS ",
    "PS>",
    "PS C:\\",
    "C:\\",
    "λ",
)

COMMENT_PREFIXES = ("#", "//", "rem ", "REM ", "::", ";")


def _strip_prompt(line: str) -> str:
    for prefix in PROMPT_PREFIXES:
        if line.startswith(prefix):
            return line[len(prefix) :].lstrip()
    return line


def _line_is_comment(line: str) -> bool:
    lowered = line.lower()
    return any(lowered.startswith(prefix.lower()) for prefix in COMMENT_PREFIXES)


def _matches_patterns(path: Path, patterns: Sequence[str]) -> bool:
    candidate = str(path).lower()
    for pattern in patterns:
        if fnmatch.fnmatch(candidate, pattern.lower()) or fnmatch.fnmatch(path.name.lower(), pattern.lower()):
            return True
    return False


def extract_commands(path: Path, config: CommandSourceConfig) -> list[str]:
    """Extract terminal commands from *path* based on heuristics."""

    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        text = path.read_text(encoding="latin-1", errors="ignore")
    except OSError:
        return []

    commands: list[str] = []
    seen: set[str] = set()
    shell_aliases = {shell.lower() for shell in config.shells}
    for raw_line in text.splitlines():
        stripped = raw_line.strip()
        if not stripped:
            continue
        if _line_is_comment(stripped):
            continue
        cleaned = _strip_prompt(stripped)
        if not cleaned:
            continue
        normalized = " ".join(cleaned.split())
        if normalized.lower() in shell_aliases:
            continue
        if normalized in seen:
            continue
        seen.add(normalized)
        commands.append(normalized)
        if config.max_lines is not None and len(commands) >= config.max_lines:
            break
    return commands


def collect_command_corpus(source_root: Path, destination: Path, config: CommandSourceConfig) -> Path | None:
    """Collect commands from *source_root* and write them to *destination*.

    Returns the path to the generated `.terminal` file or ``None`` if no commands were found.
    """

    if not source_root.exists():
        return None

    aggregated: list[str] = []
    seen_global: set[str] = set()
    for file_path in source_root.rglob("*"):
        if not file_path.is_file():
            continue
        if not _matches_patterns(file_path, config.include_patterns):
            continue
        if _matches_patterns(file_path, config.ignore_patterns):
            continue
        commands = extract_commands(file_path, config)
        if commands:
            for command in commands:
                if command in seen_global:
                    continue
                seen_global.add(command)
                aggregated.append(command)
                if config.max_lines is not None and len(aggregated) >= config.max_lines:
                    aggregated = aggregated[: config.max_lines]
                    break
            if config.max_lines is not None and len(aggregated) >= config.max_lines:
                break

    if not aggregated:
        return None

    destination.mkdir(parents=True, exist_ok=True)
    slug = _slugify(config.name)
    output_file = destination / f"{slug}.terminal"
    output_file.write_text("\n".join(aggregated), encoding="utf-8")
    return output_file


def _slugify(value: str) -> str:
    safe = [ch if ch.isalnum() or ch in {"-", "_"} else "-" for ch in value.strip().lower()]
    slug = "".join(safe).strip("-")
    return slug or "commands"
