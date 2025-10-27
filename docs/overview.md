# Dataset Maker Overview

The **Advanced Ready-to-Train AI Datasets Maker** consumes massive hybrid codebases and
terminal histories and turns them into machine learning ready corpora. The project is
organised into modular stages so that you can scale each concern independently and swap
components without rewriting the entire pipeline.

## High level workflow

1. **Configuration loading** – [`PipelineConfig`](../src/art_dataset_maker/config.py)
   resolves paths, validates options, and persists the effective configuration for
   reproducibility.
2. **Source materialisation** – [`materialize_sources`](../src/art_dataset_maker/scraping.py)
   checks out remote Git repositories, mirrors local trees, and discovers command history
   archives in a workspace designed to host multi-terabyte datasets.
3. **Ingestion** – [`iter_source_files`](../src/art_dataset_maker/ingestion.py) streams
   content lazily, skipping excluded patterns and very large binaries while tagging each
   record with language hints for downstream filtering.
4. **Preprocessing** – [`preprocess_record`](../src/art_dataset_maker/preprocess.py) applies
   whitespace normalisation, line length enforcement, and shell specific clean-ups to keep
   textual data consistent.
5. **Quality gates** – [`QualityEnforcer`](../src/art_dataset_maker/quality.py) filters short
   or low-information files, deduplicates files and chunks, and tracks compliance metrics.
6. **Chunking** – [`chunk_record`](../src/art_dataset_maker/chunking.py) slices files into
   overlapping windows tuned for transformer context sizes while preserving language
   metadata.
7. **Dataset writing** – [`DatasetWriter`](../src/art_dataset_maker/writer.py) emits JSONL
   shards for train/eval splits, optionally gzipping the payload and creating index files.
8. **Metadata + stats** – [`write_repository_metadata`](../src/art_dataset_maker/metadata.py)
   and [`PipelineStats`](../src/art_dataset_maker/stats.py) capture provenance, per-language
   counts, deduplication ratios, and run summaries for audits.

Each stage communicates with the others through data classes defined in
[`config.py`](../src/art_dataset_maker/config.py), allowing you to construct new tooling on
top of the same primitives.

## Execution surfaces

- **CLI** – [`art_dataset_maker.cli`](../src/art_dataset_maker/cli.py) exposes quickstart
  defaults, configuration discovery, and optional GUI launching.
- **GUI** – [`DatasetMakerGUI`](../src/art_dataset_maker/gui.py) provides an operator friendly
  desktop workflow for billion scale scraping runs.
- **Library** – You can import `build_pipeline` from
  [`pipeline.py`](../src/art_dataset_maker/pipeline.py) to orchestrate datasets from your own
  Python scripts or notebooks.

## Output artefacts

Every pipeline run produces a consistent set of files inside the `output_dir`:

| File | Description |
| ---- | ----------- |
| `train.jsonl[.gz]` | Chunked training records with metadata headers. |
| `eval.jsonl[.gz]` | Evaluation split generated with a deterministic seed. |
| `pipeline_config.json` | Snapshot of the effective configuration used for the run. |
| `repository_metadata.json` | Sources, branches, commit SHAs, and language coverage. |
| `dataset_stats.json` | Aggregated metrics from `PipelineStats`. |

Use these artefacts to audit datasets, reproduce experiments, and feed your own training
pipelines.
