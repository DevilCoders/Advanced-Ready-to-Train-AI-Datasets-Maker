# Scraping at Scale

This guide focuses on the scraping subsystem defined in
[`src/art_dataset_maker/scraping.py`](../src/art_dataset_maker/scraping.py) and how to operate
it reliably when targeting billions of files across public and private sources.

## Workspace hygiene

- Choose a workspace mounted on high-throughput storage (NVMe, RAID, or distributed FS).
- The scraper isolates each source in `workspace / <source-name>` to avoid path collisions.
- Temporary clones use `git clone --depth` and sparse checkouts when configured, drastically
  reducing data transfer for gigantic monorepos.

## Source types

| Type | Materialisation strategy |
| ---- | ------------------------ |
| `github` | Uses the GitHub HTTPS remote. Optional `auth_token_env` header ensures API rate limits are not exceeded. |
| `git` | Mirrors arbitrary Git remotes; respects `branch`, `tag`, or `rev`. |
| `local` | Creates a pointer to an existing on-disk directory without copying data. |

Command-oriented sources share these types but additionally record the shells and glob
patterns specified in the configuration so downstream stages can treat the data differently.

## Authentication

When scraping private repositories or enterprise GitHub instances:

1. Store a personal access token in an environment variable (e.g. `ART_DATASET_GITHUB_TOKEN`).
2. Reference the variable name via `auth_token_env` in your `code_sources` entry.
3. `materialize_sources` automatically injects the token into clone commands without
   persisting it to disk, protecting secrets during audits.

## Failure recovery

- The scraper retries transient network errors using exponential backoff.
- Partial clones are cleaned before re-attempting to avoid corrupted worktrees.
- You can safely re-run the pipeline; existing directories are fast-forwarded or reset to the
  requested revision instead of recloned from scratch.

## Bandwidth optimisation

- Use `sparse_paths` when only a subset of directories is needed.
- Combine `shallow: true` with `depth: N` to avoid downloading the full history.
- For Git LFS heavy repositories, set `skip_lfs: true` (configurable via `CodeSourceConfig`).

## Monitoring and logging

`materialize_sources` emits progress events consumed by the GUI and CLI logs. Important
fields captured in [`repository_metadata.json`](../src/art_dataset_maker/metadata.py) include:

- Source name, type, and checkout location.
- Commit SHA (for Git-based sources).
- Languages requested and discovered.
- Ingestion statistics supplied by `PipelineStats`.

These artefacts make compliance reviews possible even when handling sensitive or mixed
licence codebases.

## Integrating new scrapers

To add support for another hosting provider (e.g. Azure DevOps):

1. Extend the `SourceType` enum.
2. Implement a new helper inside `scraping.py` that performs the checkout.
3. Wire the helper into `materialize_sources` and update documentation in
   [`docs/configuration.md`](./configuration.md).
4. Capture any additional metadata so audit trails remain comprehensive.

By following these patterns, you can scale scraping to billions of files while maintaining
traceability and reproducibility.
