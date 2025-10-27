"""Source materialisation utilities for large scale dataset scraping."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import subprocess

from .commands import collect_command_corpus
from .config import CodeSourceConfig, CommandSourceConfig, PipelineConfig


@dataclass(slots=True)
class MaterializedSource:
    """A resolved source ready to be processed by the pipeline."""

    name: str
    kind: str
    path: Path
    origin: str
    languages: tuple[str, ...] = ()
    metadata_root: Path | None = None


def _slugify(value: str) -> str:
    safe = [ch if ch.isalnum() or ch in {"-", "_"} else "-" for ch in value.strip().lower()]
    slug = "".join(safe).strip("-")
    return slug or "source"


def _ensure_workspace(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def _clone_repository(config: CodeSourceConfig | CommandSourceConfig, destination: Path) -> Path:
    if destination.exists() and any(destination.iterdir()):
        return destination
    destination.parent.mkdir(parents=True, exist_ok=True)
    args = ["git", "clone"]
    if getattr(config, "branch", None):
        args.extend(["--branch", getattr(config, "branch")])
    depth = getattr(config, "depth", 1)
    shallow = getattr(config, "shallow", True)
    if shallow and depth:
        args.extend(["--depth", str(depth)])
    args.extend([config.location, str(destination)])
    try:
        subprocess.run(args, check=True)
    except FileNotFoundError as exc:
        raise RuntimeError("git executable is required to materialise remote sources") from exc
    except subprocess.CalledProcessError as exc:
        raise RuntimeError(f"failed to clone {config.location}: {exc}") from exc
    sparse_paths = getattr(config, "sparse_paths", ())
    if sparse_paths:
        try:
            subprocess.run(["git", "-C", str(destination), "sparse-checkout", "init", "--cone"], check=True)
            subprocess.run(["git", "-C", str(destination), "sparse-checkout", "set", *sparse_paths], check=True)
        except subprocess.CalledProcessError as exc:
            raise RuntimeError(f"failed to configure sparse checkout for {config.location}: {exc}") from exc
    return destination


def _materialize_code_source(config: CodeSourceConfig, workspace: Path) -> MaterializedSource:
    if config.type == "local":
        path = Path(config.location).expanduser().resolve()
        origin = "local"
        metadata_root = path
    else:
        slug = _slugify(config.name or config.location)
        checkout_dir = workspace / "code" / slug
        path = _clone_repository(config, checkout_dir)
        origin = config.type
        metadata_root = path
    return MaterializedSource(
        name=config.name,
        kind="code",
        path=path,
        origin=origin,
        languages=config.languages,
        metadata_root=metadata_root,
    )


def _materialize_command_source(config: CommandSourceConfig, workspace: Path) -> MaterializedSource | None:
    if config.type == "local":
        source_root = Path(config.location).expanduser().resolve()
        origin = "local"
        metadata_root = source_root
    else:
        slug = _slugify(config.name or config.location)
        checkout_dir = workspace / "commands" / slug / "repository"
        source_root = _clone_repository(config, checkout_dir)
        origin = config.type
        metadata_root = source_root

    extracted_dir = workspace / "commands" / _slugify(config.name) / "extracted"
    corpus_file = collect_command_corpus(source_root, extracted_dir, config)
    if corpus_file is None:
        return None
    return MaterializedSource(
        name=f"{config.name}-commands",
        kind="commands",
        path=extracted_dir,
        origin=origin,
        languages=("terminal",),
        metadata_root=metadata_root,
    )


def materialize_sources(config: PipelineConfig, workspace: Path) -> list[MaterializedSource]:
    """Materialise all sources defined in *config* into *workspace*."""

    resolved: list[MaterializedSource] = []
    workspace = _ensure_workspace(workspace)

    if config.include_primary_root:
        root_path = Path(config.root)
        if root_path.exists():
            resolved.append(
                MaterializedSource(
                    name="primary-root",
                    kind="code",
                    path=root_path,
                    origin="local",
                    languages=(),
                    metadata_root=root_path,
                )
            )

    for code_source in config.code_sources:
        resolved.append(_materialize_code_source(code_source, workspace))

    for command_source in config.command_sources:
        materialized = _materialize_command_source(command_source, workspace)
        if materialized:
            resolved.append(materialized)

    return resolved
