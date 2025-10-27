"""High level orchestration for building release ready datasets from source trees."""
from __future__ import annotations

from pathlib import Path

from .chunking import chunk_record
from .config import PipelineConfig
from .ingestion import iter_source_files
from .metadata import write_repository_metadata
from .preprocess import preprocess_record
from .quality import QualityEnforcer
from .scraping import MaterializedSource, materialize_sources
from .stats import PipelineStats
from .writer import DatasetWriter


def _generate_chunks(
    config: PipelineConfig, stats: PipelineStats, sources: list[MaterializedSource]
):
    enforcer = QualityEnforcer(config.quality)
    for source in sources:
        for record in iter_source_files(source.path, config.ingestion):
            if source.languages and record.language not in source.languages:
                continue
            stats.record_source(source.name)
            stats.files_scanned += 1
            if enforcer.is_duplicate_file(record):
                stats.files_deduplicated += 1
                continue
            processed = preprocess_record(record, config.preprocess)
            if not enforcer.passes_content_gates(processed):
                stats.files_filtered += 1
                continue
            stats.files_emitted += 1
            for chunk in chunk_record(processed, config.chunk):
                stats.chunks_generated += 1
                if enforcer.is_duplicate_chunk(chunk):
                    stats.chunks_deduplicated += 1
                    continue
                stats.chunks_emitted += 1
                stats.record_language(chunk.language)
                yield chunk


def build_pipeline(config: PipelineConfig) -> PipelineStats:
    """Execute the entire pipeline based on *config* and return run statistics."""

    config.validate()
    workspace = config.workspace or (config.output_dir / "_workspace")
    sources = materialize_sources(config, workspace)
    stats = PipelineStats()
    writer = DatasetWriter(config.output_dir, config.dataset)
    chunks = _generate_chunks(config, stats, sources)
    writer.write(chunks)
    write_repository_metadata(sources, config.output_dir)
    config.dump(config.output_dir / "pipeline_config.json")
    stats.write(config.output_dir)
    return stats


def run_from_paths(root: Path, output: Path) -> None:
    """Run with default configuration for quick experiments."""
    config = PipelineConfig(root=root, output_dir=output)
    build_pipeline(config)
