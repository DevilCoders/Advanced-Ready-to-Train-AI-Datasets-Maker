"""Repository metadata extraction helpers."""
from __future__ import annotations

from pathlib import Path
from typing import Dict, Sequence
import json

from .scraping import MaterializedSource

CI_FILENAMES = {
    ".github/workflows",
    ".gitlab-ci.yml",
    "azure-pipelines.yml",
    "circle.yml",
    "Jenkinsfile",
    "appveyor.yml",
    "bitrise.yml",
}

DEPENDENCY_FILES = {
    "requirements.txt": "python",
    "pyproject.toml": "python",
    "package.json": "node",
    "Cargo.toml": "rust",
    "go.mod": "go",
    "pom.xml": "java",
    "build.gradle": "java",
    "composer.json": "php",
}


def collect_dependency_files(root: Path) -> Dict[str, str]:
    """Return a mapping of dependency manifest paths to ecosystem name."""
    manifests: Dict[str, str] = {}
    for path, ecosystem in DEPENDENCY_FILES.items():
        candidate = root / path
        if candidate.exists():
            manifests[str(candidate.relative_to(root))] = ecosystem
    return manifests


def collect_ci_configs(root: Path) -> Dict[str, str]:
    """Find CI/CD configuration files."""
    ci_files: Dict[str, str] = {}
    for entry in CI_FILENAMES:
        candidate = root / entry
        if candidate.is_dir():
            for workflow in candidate.glob("**/*.yml"):
                ci_files[str(workflow.relative_to(root))] = "workflow"
        elif candidate.exists():
            ci_files[str(candidate.relative_to(root))] = "workflow"
    return ci_files


def write_repository_metadata(sources: Sequence[MaterializedSource], output_dir: Path) -> None:
    """Persist high-level repository metadata next to the dataset for each source."""

    metadata_sources = []
    for source in sources:
        root = source.metadata_root
        if root is None or not root.exists():
            continue
        metadata_sources.append(
            {
                "name": source.name,
                "kind": source.kind,
                "origin": source.origin,
                "path": str(root),
                "dependency_manifests": collect_dependency_files(root),
                "ci_cd": collect_ci_configs(root),
            }
        )

    document = {"sources": metadata_sources}
    output_dir.mkdir(parents=True, exist_ok=True)
    metadata_path = output_dir / "repository_metadata.json"
    metadata_path.write_text(json.dumps(document, indent=2, sort_keys=True), encoding="utf-8")
