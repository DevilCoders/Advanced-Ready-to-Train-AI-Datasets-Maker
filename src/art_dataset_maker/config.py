"""Configuration data structures and utilities for the dataset maker."""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Iterable, Optional, Sequence
import json
import os

try:
    import yaml  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    yaml = None  # type: ignore


def _as_tuple(value: Optional[Sequence[str]]) -> tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, tuple):
        return value
    return tuple(value)


@dataclass(slots=True)
class CodeSourceConfig:
    """Configuration describing an external code source to materialise."""

    name: str
    type: str
    location: str
    branch: Optional[str] = None
    languages: tuple[str, ...] = ()
    shallow: bool = True
    depth: int = 1
    sparse_paths: tuple[str, ...] = ()
    keep_checkout: bool = False

    def __post_init__(self) -> None:
        self.type = self.type.lower()
        self.languages = tuple(lang.lower() for lang in self.languages)
        self.sparse_paths = tuple(path.strip() for path in self.sparse_paths)

    @classmethod
    def from_mapping(cls, payload: dict) -> "CodeSourceConfig":
        return cls(
            name=payload.get("name") or payload.get("id") or payload.get("location", "source"),
            type=payload.get("type", "github"),
            location=payload.get("location", ""),
            branch=payload.get("branch"),
            languages=_as_tuple(payload.get("languages")),
            shallow=payload.get("shallow", True),
            depth=payload.get("depth", 1),
            sparse_paths=_as_tuple(payload.get("sparse_paths")),
            keep_checkout=payload.get("keep_checkout", False),
        )

    def as_dict(self) -> dict:
        return {
            "name": self.name,
            "type": self.type,
            "location": self.location,
            "branch": self.branch,
            "languages": list(self.languages),
            "shallow": self.shallow,
            "depth": self.depth,
            "sparse_paths": list(self.sparse_paths),
            "keep_checkout": self.keep_checkout,
        }


@dataclass(slots=True)
class CommandSourceConfig:
    """Configuration describing where terminal command corpora originate."""

    name: str
    type: str
    location: str
    shells: tuple[str, ...] = (
        "bash",
        "zsh",
        "fish",
        "powershell",
        "cmd",
        "sh",
        "ksh",
        "csh",
        "pwsh",
        "nushell",
        "xonsh",
        "busybox",
    )
    include_patterns: tuple[str, ...] = (
        "*.sh",
        "*.bash",
        "*.zsh",
        "*.fish",
        "*.ps1",
        "*.psm1",
        "*.cmd",
        "*.bat",
        "*.ksh",
        "*.csh",
        "*.history",
        "*commands.txt",
        "*history.txt",
        "*.md",
    )
    ignore_patterns: tuple[str, ...] = ("*.png", "*.jpg", "*.jpeg", "*.gif", "*.pdf")
    max_lines: Optional[int] = None

    def __post_init__(self) -> None:
        self.type = self.type.lower()
        self.shells = tuple(shell.lower() for shell in self.shells)
        self.include_patterns = tuple(pattern.lower() for pattern in self.include_patterns)
        self.ignore_patterns = tuple(pattern.lower() for pattern in self.ignore_patterns)

    @classmethod
    def from_mapping(cls, payload: dict) -> "CommandSourceConfig":
        shells = _as_tuple(payload.get("shells")) or cls.shells
        include_patterns = _as_tuple(payload.get("include_patterns")) or cls.include_patterns
        ignore_patterns = _as_tuple(payload.get("ignore_patterns")) or cls.ignore_patterns
        return cls(
            name=payload.get("name") or payload.get("id") or payload.get("location", "commands"),
            type=payload.get("type", "github"),
            location=payload.get("location", ""),
            shells=tuple(shells),
            include_patterns=tuple(include_patterns),
            ignore_patterns=tuple(ignore_patterns),
            max_lines=payload.get("max_lines"),
        )

    def as_dict(self) -> dict:
        return {
            "name": self.name,
            "type": self.type,
            "location": self.location,
            "shells": list(self.shells),
            "include_patterns": list(self.include_patterns),
            "ignore_patterns": list(self.ignore_patterns),
            "max_lines": self.max_lines,
        }


@dataclass(slots=True)
class IngestionConfig:
    """Configuration controlling which files are ingested from a repository."""

    include_extensions: tuple[str, ...] = (
        ".py",
        ".js",
        ".ts",
        ".tsx",
        ".java",
        ".go",
        ".rs",
        ".cpp",
        ".c",
        ".cs",
        ".rb",
        ".php",
        ".swift",
        ".m",
        ".mm",
        ".pl",
        ".pm",
        ".sh",
        ".ps1",
        ".psm1",
        ".cmd",
        ".bat",
        ".scala",
        ".kt",
        ".dart",
        ".lua",
        ".r",
        ".jl",
        ".yaml",
        ".yml",
        ".json",
        ".toml",
        ".ini",
        ".cfg",
        ".md",
        ".txt",
        ".terminal",
        ".cmdlog",
    )
    exclude_dirs: tuple[str, ...] = (".git", "node_modules", "vendor", "dist", "build", "__pycache__")
    max_file_size_mb: int = 5
    follow_symlinks: bool = False


@dataclass(slots=True)
class PreprocessConfig:
    """Configuration for content preprocessing."""

    normalize_whitespace: bool = True
    strip_empty_lines: bool = True
    max_line_length: Optional[int] = 2000


@dataclass(slots=True)
class ChunkConfig:
    """Configuration for chunk generation."""

    target_chunk_size: int = 2048
    overlap: int = 200


@dataclass(slots=True)
class DatasetConfig:
    """Configuration for dataset writing."""

    train_ratio: float = 0.9
    seed: int = 13
    compress: bool = False


@dataclass(slots=True)
class QualityConfig:
    """Quality gates applied after preprocessing and before chunking."""

    min_characters: int = 0
    max_characters: Optional[int] = None
    min_lines: int = 0
    max_lines: Optional[int] = None
    deduplicate_files: bool = True
    deduplicate_chunks: bool = True


@dataclass(slots=True)
class PipelineConfig:
    """Top level pipeline configuration."""

    root: Path
    output_dir: Path
    ingestion: IngestionConfig = field(default_factory=IngestionConfig)
    preprocess: PreprocessConfig = field(default_factory=PreprocessConfig)
    chunk: ChunkConfig = field(default_factory=ChunkConfig)
    dataset: DatasetConfig = field(default_factory=DatasetConfig)
    quality: QualityConfig = field(default_factory=QualityConfig)
    code_sources: tuple[CodeSourceConfig, ...] = ()
    command_sources: tuple[CommandSourceConfig, ...] = ()
    workspace: Optional[Path] = None
    include_primary_root: bool = True

    def __post_init__(self) -> None:
        self.root = Path(self.root).expanduser().resolve()
        self.output_dir = Path(self.output_dir).expanduser().resolve()
        if self.workspace is not None:
            self.workspace = Path(self.workspace).expanduser().resolve()

    @classmethod
    def from_mapping(cls, mapping: dict, root: Optional[Path] = None) -> "PipelineConfig":
        """Create a pipeline config from a mapping object."""

        def build(dataclass_type, payload: dict, defaults):
            data = {**defaults.__dict__, **payload}
            for key, value in list(data.items()):
                if isinstance(value, list):
                    data[key] = tuple(value)
            return dataclass_type(**data)

        ingestion = build(IngestionConfig, mapping.get("ingestion", {}), IngestionConfig())
        preprocess = build(PreprocessConfig, mapping.get("preprocess", {}), PreprocessConfig())
        chunk = build(ChunkConfig, mapping.get("chunk", {}), ChunkConfig())
        dataset = build(DatasetConfig, mapping.get("dataset", {}), DatasetConfig())
        quality = build(QualityConfig, mapping.get("quality", {}), QualityConfig())
        root_path = Path(mapping.get("root", root or os.curdir)).expanduser().resolve()
        output_path = Path(mapping.get("output_dir", mapping.get("output", "dataset"))).expanduser().resolve()
        code_sources = tuple(
            CodeSourceConfig.from_mapping(item) for item in mapping.get("code_sources", [])
        )
        command_sources = tuple(
            CommandSourceConfig.from_mapping(item) for item in mapping.get("command_sources", [])
        )
        workspace = mapping.get("workspace")
        workspace_path = Path(workspace).expanduser().resolve() if workspace else None
        include_primary_root = mapping.get("include_primary_root", True)
        return cls(
            root=root_path,
            output_dir=output_path,
            ingestion=ingestion,
            preprocess=preprocess,
            chunk=chunk,
            dataset=dataset,
            quality=quality,
            code_sources=code_sources,
            command_sources=command_sources,
            workspace=workspace_path,
            include_primary_root=include_primary_root,
        )

    @classmethod
    def load(cls, path: Path) -> "PipelineConfig":
        """Load configuration from a JSON or YAML file."""
        data: dict
        text = path.read_text(encoding="utf-8")
        try:
            data = json.loads(text)
        except json.JSONDecodeError:
            if yaml is None:
                raise RuntimeError("YAML configuration requires PyYAML to be installed") from None
            data = yaml.safe_load(text)
        return cls.from_mapping(data, root=path.parent)

    def validate(self) -> None:
        """Validate configuration values."""
        if not 0 < self.dataset.train_ratio < 1:
            raise ValueError("train_ratio must be between 0 and 1")
        if self.chunk.overlap >= self.chunk.target_chunk_size:
            raise ValueError("overlap must be smaller than target chunk size")
        if self.ingestion.max_file_size_mb <= 0:
            raise ValueError("max_file_size_mb must be positive")
        if self.quality.max_characters is not None and self.quality.max_characters <= 0:
            raise ValueError("max_characters must be positive when provided")
        if self.quality.max_lines is not None and self.quality.max_lines <= 0:
            raise ValueError("max_lines must be positive when provided")
        if self.quality.max_characters is not None and self.quality.max_characters < self.quality.min_characters:
            raise ValueError("max_characters must be greater than min_characters")
        if self.quality.max_lines is not None and self.quality.max_lines < self.quality.min_lines:
            raise ValueError("max_lines must be greater than min_lines")
        for source in self.code_sources:
            if not source.location:
                raise ValueError("code source location cannot be empty")
        for source in self.command_sources:
            if not source.location:
                raise ValueError("command source location cannot be empty")
        if self.workspace is not None and self.workspace == self.output_dir:
            raise ValueError("workspace must differ from output directory")

    def as_dict(self) -> dict:
        """Return the configuration as a serialisable dictionary."""
        return {
            "root": str(self.root),
            "output_dir": str(self.output_dir),
            "workspace": str(self.workspace) if self.workspace else None,
            "include_primary_root": self.include_primary_root,
            "ingestion": asdict(self.ingestion),
            "preprocess": asdict(self.preprocess),
            "chunk": asdict(self.chunk),
            "dataset": asdict(self.dataset),
            "quality": asdict(self.quality),
            "code_sources": [source.as_dict() for source in self.code_sources],
            "command_sources": [source.as_dict() for source in self.command_sources],
        }

    def dump(self, path: Path) -> None:
        """Persist the effective configuration as JSON."""
        serialisable = {k: v for k, v in self.as_dict().items() if v is not None}
        path.write_text(json.dumps(serialisable, indent=2, sort_keys=True), encoding="utf-8")


def discover_config(paths: Iterable[Path]) -> Optional[Path]:
    """Discover a configuration file from a collection of candidate paths."""
    for candidate in paths:
        expanded = candidate.expanduser()
        if expanded.exists():
            return expanded
    return None
