# Configuration Deep Dive

`PipelineConfig` consolidates every knob required to construct a dataset that spans
billions of lines of code and terminal transcripts. Configurations can be expressed as
YAML, JSON, or instantiated programmatically. This guide expands on the fields surfaced in
[`dataset.example.yaml`](../dataset.example.yaml) and maps them to the classes defined in
[`src/art_dataset_maker/config.py`](../src/art_dataset_maker/config.py).

## Top level fields

| Field | Type | Description |
| ----- | ---- | ----------- |
| `root` | path | Primary repository to scan. Required unless every source is remote. |
| `output_dir` | path | Directory receiving JSONL shards, metadata, and statistics. |
| `workspace` | path (optional) | Overrides the default `_workspace` folder when cloning remote sources. |
| `include_primary_root` | bool | When `false`, only materialised sources will be processed. |

## Ingestion

`ingestion` maps to `IngestionConfig`.

- `max_file_size_mb`: Hard limit that skips oversize assets early.
- `include_extensions` / `exclude_extensions`: Whitelists or blacklists file suffixes.
- `exclude_globs`: Shell-style patterns useful for large vendor folders.
- `follow_symlinks`: Enable when you trust the workspace layout.

Records yielded by [`iter_source_files`](../src/art_dataset_maker/ingestion.py) carry
`language` annotations derived from file extension heuristics; downstream stages can still
filter by custom language sets per source.

## Preprocessing

`preprocess` -> `PreprocessConfig` in [`preprocess.py`](../src/art_dataset_maker/preprocess.py).

- `normalize_whitespace`: Collapses mixed indentation and converts tabs to spaces.
- `strip_empty_lines`: Removes leading/trailing blank lines that waste tokens.
- `max_line_length`: Soft-wraps extremely long lines; essential for Markdown/JSON dumps.
- `canonicalize_shell`: Optional shell aware clean-up (set automatically when source type is
  `command`).

## Chunking

`chunk` -> `ChunkConfig` in [`chunking.py`](../src/art_dataset_maker/chunking.py).

- `target_chunk_size`: Desired number of characters per chunk.
- `overlap`: Characters reused between adjacent chunks to preserve context.
- `max_chunks_per_file`: Safety valve to avoid infinitely splitting generated logs.

## Dataset emission

`dataset` -> `DatasetSplitConfig` in [`writer.py`](../src/art_dataset_maker/writer.py).

- `train_ratio`: Fraction of emitted chunks routed to the training split.
- `seed`: Controls deterministic shuffling in `DatasetWriter`.
- `compress`: When `true`, JSONL output is gzipped automatically.
- `max_records_per_shard`: Enables sharded outputs for gigantic corpora.

## Quality enforcement

`quality` -> `QualityConfig` in [`quality.py`](../src/art_dataset_maker/quality.py).

- `min_characters` / `max_characters`: Guardrails for useful snippets.
- `min_lines` / `max_lines`: Additional signal for filtering stub or giant files.
- `deduplicate_files` / `deduplicate_chunks`: Toggle locality-sensitive hashing caches.
- `forbidden_patterns`: Reject records containing sensitive markers.

## Code sources

Each entry in `code_sources` is a `CodeSourceConfig` handled by
[`scraping.py`](../src/art_dataset_maker/scraping.py).

| Field | Notes |
| ----- | ----- |
| `name` | Display name used in stats and metadata. |
| `type` | `github`, `git`, or `local`. Determines checkout strategy. |
| `location` | URL or filesystem path. |
| `branch` / `tag` / `rev` | Mutually exclusive selectors. Default: default branch. |
| `depth` | Depth for shallow clones; pair with `shallow: true`. |
| `languages` | Restrict emission to specific languages for this source only. |
| `sparse_paths` | List of directories/files to fetch when dealing with enormous monorepos. |
| `auth_token_env` | Environment variable name containing credentials for private repos. |

## Command sources

`command_sources` entries materialise shell histories or curated command corpora. They share
the same base schema as `code_sources` with additional knobs:

- `shells`: One or more of `bash`, `zsh`, `fish`, `powershell`, `cmd`, etc.
- `include_patterns`: Glob patterns that select which files inside the repository count as
  terminal data (e.g. `*history.txt`).
- `exclude_patterns`: Optional glob patterns to avoid README files when scraping command
  repos.

During ingestion, the source type informs [`iter_source_files`](../src/art_dataset_maker/ingestion.py)
so that command oriented records can be normalised with shell aware heuristics.

## Discovery and overrides

- Use the CLI flag `--discover-config` to search for `dataset.yaml`, `dataset.yml`, or
  `dataset.json` within the root directory. [`discover_config`](../src/art_dataset_maker/config.py)
  returns the first match.
- Any CLI `--root`, `--output`, or `--workspace` arguments override the corresponding values
  from disk-based configurations before validation runs.
- Programmatic consumers can mutate the `PipelineConfig` instance prior to calling
  `build_pipeline` if they need dynamic adjustments.
