# Advanced-Ready-to-Train-AI-Datasets-Maker

An advanced toolchain that consumes extremely large, heterogeneous, locally hosted codebases (87GB–125GB+) and
transforms them into professionally curated, release-ready datasets that can be used directly for AI training.
It now includes a scraping orchestrator capable of staging billions of lines of source code and terminal command
transcripts from remote/public sources alongside private mirrors.

## Features

- **Massive scale ingestion** – stream source files from disk without loading the entire repository into memory.
- **Multi-source scraping** – materialise GitHub organisations, Git-based mirrors, and local monoliths into a single
  workspace, optionally using sparse/shallow clones to manage petabyte-class corpora.
- **Terminal command harvesting** – extract and deduplicate CLI histories across Windows, macOS, Linux, red-team
  toolkits, and penetration-testing playbooks to produce rich terminal-focused datasets.
- **Language-aware metadata** – automatically attach lightweight language annotations per file across a dozen+
  ecosystems including JavaScript, Go, Perl, PHP, Ruby, Swift, TypeScript, Shell, and more.
- **Configurable preprocessing** – normalise whitespace, limit extreme line lengths, and sanitise content.
- **Chunked dataset creation** – split large files into overlapping context windows optimised for transformer models.
- **Deterministic splitting** – reproducible train/eval splits with optional gzip compression.
- **Quality gates & deduplication** – configurable filters for short/long files and automatic file/chunk deduping.
- **Run artefacts** – persist the effective configuration, repository metadata, and rich build statistics per source.
- **CLI & advanced GUI** – launch from the terminal or drive scraping interactively with an operator-friendly desktop
  interface that tracks progress and manages huge workspace layouts.

## Installation

```bash
pip install .
```

This installs the `art-dataset-maker` CLI entrypoint and the companion `art-dataset-maker-gui` launcher.

## Quickstart (CLI)

```bash
art-dataset-maker /path/to/huge/repo /path/to/output
```

The command will print a concise summary to stdout and:

1. Materialise any configured remote sources into the workspace.
2. Walk the repository trees, skipping binary files and oversize assets.
3. Normalise source code text according to the default configuration.
4. Apply quality gates, deduplicate repeated files/chunks, and capture language statistics.
5. Produce overlapping chunks suitable for machine learning training.
6. Stream JSONL (optionally gzipped) datasets to the output directory.
7. Emit `repository_metadata.json`, `pipeline_config.json`, and `dataset_stats.json` for auditability.

## Quickstart (GUI)

```bash
art-dataset-maker-gui
```

The GUI provides:

- Workspace selection for primary/local repositories, output, and remote checkout caches.
- Guided forms to register GitHub or local code sources, select focus languages, and tune sparse/shallow clones.
- Parallel configuration of command history sources spanning diverse shells and tooling families.
- One-click pipeline execution with live logging, plus config import/export for reproducible runs.

## Configuration

Create a `dataset.yaml` (or `.yml`/`.json`) file in the repository you want to process. See
[`dataset.example.yaml`](dataset.example.yaml) for all available options.

```yaml
root: ./example-repo
output_dir: ./dataset-output
workspace: ./workspace-cache
ingestion:
  max_file_size_mb: 12
  include_extensions: [".py", ".js", ".ts", ".go", ".swift", ".php", ".rb", ".sh", ".terminal"]
preprocess:
  normalize_whitespace: true
  strip_empty_lines: true
  max_line_length: 1600
chunk:
  target_chunk_size: 1024
  overlap: 128
dataset:
  train_ratio: 0.92
  seed: 1337
  compress: true
quality:
  min_characters: 256
  min_lines: 6
  deduplicate_files: true
  deduplicate_chunks: true
code_sources:
  - name: awesome-public-repo
    type: github
    location: https://github.com/org/awesome-repo.git
    branch: main
    languages: [python, javascript, go, swift]
    shallow: true
    depth: 1
  - name: local-monolith
    type: local
    location: /mnt/big/local-monolith
    languages: [php, ruby, shell]
command_sources:
  - name: red-team-commands
    type: github
    location: https://github.com/org/red-team-playbooks.git
    shells: [bash, zsh, powershell, cmd]
    include_patterns: ["*.md", "*.sh", "*history.txt"]
  - name: internal-history
    type: local
    location: /srv/shared/histories
    shells: [bash, zsh, fish]
include_primary_root: true
```

Run with automatic discovery:

```bash
art-dataset-maker --discover-config /path/to/repo /path/to/output
```

### Code & Command Sources

- **`code_sources`** entries describe additional Git or local repositories to ingest alongside the primary root. Use
  `shallow`/`depth` for enormous public corpora and `languages` to prioritise language-specific filtering.
- **`command_sources`** entries extract terminal command corpora from public playbooks or local history dumps. Adjust
  `shells`, `include_patterns`, and `ignore_patterns` to target specific environments (Windows CMD, PowerShell,
  macOS/Linux shells, penetration testing suites, etc.).
- **`workspace`** points to a durable cache directory where massive remote checkouts and extracted command corpora are
  staged before ingestion.

## Extending the pipeline

The architecture is modular. Extend or customise by editing the modules in `src/art_dataset_maker/`:

- `ingestion.py` – file discovery and metadata extraction (now supporting dozens of language families and terminal corpora).
- `scraping.py` – orchestrates remote clones, sparse checkouts, and command corpus extraction.
- `commands.py` – heuristics for cleaning, deduplicating, and exporting terminal command histories.
- `preprocess.py` – content normalisation and sanitisation.
- `chunking.py` – sample segmentation strategy.
- `writer.py` – output serialisation and train/eval splitting.
- `pipeline.py` – orchestration glue that ties everything together.

Each component can be swapped or extended to support bespoke deduplication, static analysis, dependency graph
extraction, security filtering, or CI/CD metadata gathering as needed for your target AI training scenario.

### Outputs

Every pipeline execution produces the following artefacts in the output directory:

- `train.jsonl[.gz]` / `eval.jsonl[.gz]` – the dataset splits.
- `repository_metadata.json` – dependency manifests and CI/CD hints grouped per materialised source.
- `pipeline_config.json` – the fully resolved configuration used for the run.
- `dataset_stats.json` – aggregate counts, language distribution, and per-source file tallies emitted by the pipeline.

## Additional documentation

Explore the `docs/` directory for focused guides:

- [`docs/overview.md`](docs/overview.md) – architecture summary and artefact reference.
- [`docs/configuration.md`](docs/configuration.md) – exhaustive configuration field guide.
- [`docs/gui.md`](docs/gui.md) – operating the advanced Tkinter GUI at scale.
- [`docs/pipeline.md`](docs/pipeline.md) – extending pipeline internals safely.
- [`docs/scraping.md`](docs/scraping.md) – best practices for multi-source scraping.
