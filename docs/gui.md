# Advanced GUI Operations Guide

The Tkinter-based GUI (`DatasetMakerGUI`) provides an interactive surface for curating
multi-source scraping runs. This guide walks through major panels and power features
implemented in [`src/art_dataset_maker/gui.py`](../src/art_dataset_maker/gui.py).

## Launching the application

Run either command:

```bash
art-dataset-maker --gui
# or
art-dataset-maker gui --config /path/to/dataset.yaml
# or the dedicated console script installed via setuptools
art-dataset-maker-gui
```

The optional `--config` flag pre-loads an existing configuration, while `--workspace`
pre-seeds the checkout cache path used when cloning remote repositories.

## Workspace planner

The landing view prompts you to select:

- **Primary root** – Local repository to scan. Can be left empty if you rely entirely on
  remote code sources.
- **Output directory** – Destination for JSONL shards and metadata.
- **Workspace** – Disk location where remote repositories are materialised. This is critical
  when staging petabyte-class mirrors and should point to a high-throughput volume.

Selections are persisted in memory and written back to the configuration file when you
export the run plan.

## Source registries

Two dedicated tabs manage data sources:

1. **Code Sources** – Add GitHub organisations, raw Git remotes, or local mirrors.
   - Configure authentication via environment variables for private repositories.
   - Control sparse checkouts and depth when cloning enormous monorepos.
   - Assign language focus lists to limit downstream chunking costs.
2. **Command Sources** – Register shell history archives, curated command corpora, and
   security playbooks.
   - Choose supported shells so preprocessing can apply shell-aware normalisation.
   - Provide include/exclude glob patterns to target history files without noise.

Each entry is validated using the same logic as `PipelineConfig`. Errors surface inline so
operators can correct typos before a run starts.

## Quality & chunking dashboards

The **Quality** tab mirrors `QualityConfig` toggles, enabling you to adjust
minimum/maximum thresholds and deduplication behaviour with live feedback. The **Chunking**
section lets you preview how chunk size and overlap affect estimated shard counts for the
current source mix.

## Run control & monitoring

- **Dry run** – Simulates the pipeline to estimate record counts without writing to disk.
- **Start run** – Invokes `build_pipeline` and streams log output into an embedded console
  widget so you can monitor ingestion, deduplication, and chunking progress in real time.
- **Abort** – Gracefully stops the active run, ensuring partially written shards are closed.

Progress bars update with `PipelineStats` data (files scanned, chunks emitted, dedupe ratios)
in near real time, giving operators early visibility into anomalies.

## Configuration import/export

Use the toolbar buttons to:

- **Import** – Load a YAML/JSON configuration and repopulate all widgets.
- **Export** – Persist the current state to disk, enabling reproducible schedules and CI/CD
  automation around the GUI.

All generated configs remain compatible with the CLI and programmatic APIs documented in
[`docs/configuration.md`](./configuration.md).
