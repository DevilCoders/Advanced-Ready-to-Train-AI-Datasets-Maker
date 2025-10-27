# Pipeline Internals

This document is aimed at engineers extending the dataset builder. It explains how the core
modules interact so you can slot in new behaviour (e.g. additional preprocessors, new
quality heuristics, or alternative output formats) without breaking existing workflows.

## Core orchestration

[`build_pipeline`](../src/art_dataset_maker/pipeline.py) is the entrypoint used by the CLI,
GUI, and tests. It performs the following steps:

1. Calls `PipelineConfig.validate()` to ensure paths exist, ratios are sane, and source
   definitions are coherent.
2. Determines a workspace directory (`config.workspace` or `output_dir / "_workspace"`).
3. Invokes [`materialize_sources`](../src/art_dataset_maker/scraping.py) which returns a list
   of [`MaterializedSource`](../src/art_dataset_maker/scraping.py#L18) objects. Each entry
   includes `name`, `path`, `type`, and `languages` metadata.
4. Instantiates [`PipelineStats`](../src/art_dataset_maker/stats.py) to gather runtime
   metrics.
5. Creates a [`DatasetWriter`](../src/art_dataset_maker/writer.py) configured with
   `DatasetSplitConfig`.
6. Streams records produced by `_generate_chunks`, which stitches together ingestion,
   preprocessing, deduplication, and chunking.
7. Writes metadata and stats files, then returns the populated `PipelineStats` instance.

## Extending ingestion

`iter_source_files` yields `SourceRecord` dataclasses. To support a new source type:

1. Add a new `SourceType` enum value in [`config.py`](../src/art_dataset_maker/config.py).
2. Teach [`materialize_sources`](../src/art_dataset_maker/scraping.py) how to recognise and
   materialise the type.
3. Update [`iter_source_files`](../src/art_dataset_maker/ingestion.py) to detect the new type
   and emit records accordingly.
4. Optionally adjust [`preprocess_record`](../src/art_dataset_maker/preprocess.py) if the raw
   text needs custom normalisation.

Because ingestion is generator-based, it scales to trillions of bytes without loading the
entire corpus into memory.

## Preprocessing plugins

`preprocess_record` accepts a `PreprocessConfig` and a `SourceRecord`. To add a new rule:

- Extend `PreprocessConfig` with additional flags or thresholds.
- Update the `PipelineConfig.validate()` method to set defaults or constraints.
- Modify `preprocess_record` to apply your transformation before returning the processed
  record. Keep transformations pure whenever possible so unit tests can be deterministic.

## Quality heuristics

[`QualityEnforcer`](../src/art_dataset_maker/quality.py) acts as a gatekeeper. It maintains
content hashes using `hashlib.blake2b` by default so deduplication remains fast even on
billions of records. To change behaviour:

- Adjust `QualityConfig` fields.
- Override `is_duplicate_file`, `is_duplicate_chunk`, or `passes_content_gates` with new
  strategies. For example, plug in SimHash or MinHash for near-duplicate detection.
- Update `PipelineStats` to track any new counters you introduce.

## Chunking strategies

`chunk_record` is implemented as a generator so you can yield arbitrarily complex chunk
structures. For models that require token-based windows, this is the hook to add tokenisers.
Any new fields on the chunk objects should be serialisable by `DatasetWriter`.

## Writing outputs

`DatasetWriter.write` consumes an iterator of chunk objects and fans them out into train and
eval files. Key extension points:

- Override `DatasetWriter._open_file` to customise compression codecs.
- Adjust `DatasetWriter._emit_record` if you need columnar formats (e.g. Parquet).
- Modify `DatasetWriter.write` to insert callbacks or metrics sinks for monitoring systems.

## Metadata capture

[`write_repository_metadata`](../src/art_dataset_maker/metadata.py) persists a consolidated
view of every materialised source, including Git SHAs and checkout options. Extend this file
if you need to capture licence data, dependency manifests, or security scan fingerprints.

## Testing hooks

- The CLI exposes `--discover-config` and GUI autoloaders so you can write integration tests
  that rely on fixture configurations.
- `PipelineStats.format_summary()` produces concise human-readable summaries; re-use this in
  logging or monitoring integrations.

By following these extension contracts, you can evolve the pipeline without forking the core
architecture.
