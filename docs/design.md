# Scanner Design Overview

_Last updated: 2025-11-08_

## Goals
- Provide a modular system for scanning and cataloging video metadata from multiple sources.
- Support extensibility for new data sources, page formats, and backend integrations.
- Maintain clear separation of concerns between API, domain logic, and infrastructure.

## Initial Architecture
- **API Layer (`src/scanner/api`)**: Exposes interfaces for external consumers (REST, GraphQL, CLI, future REPL).
- **Domain Layer (`src/scanner/domain`)**: Houses core business logic, metadata models, and workflows.
- **Infrastructure Layer (`src/scanner/infrastructure`)**: Manages integrations such as databases, web scrapers, and external services.

### Processing Engine
- **Source abstraction**: `SourceType` enum captures high-level categories (web pages, files, databases, APIs).
- **Structure descriptors**: `SourceDescriptor` and `SourceStructure` describe specific integrations such as YouTube pages or CSV files.
- **Normalization step**: `SourceRecord` and `IngestionRecord` form the boundary between raw data and normalized `VideoMetadata`.
- **Output configuration**: `OutputDescriptor` and `OutputPayload` shape how normalized data is emitted (normalized metadata, raw payloads, summaries).
- **Persistence backend**: `PersistenceDescriptor` paired with `PersistenceBackend` interfaces route payloads to storage layers (files, databases, queues, remote APIs).
- **Processing engine orchestration**: `ProcessingEngine` coordinates registries for source adapters, normalizers, transformers, and persistence backends, capturing failures via a pluggable aggregator.
- **Logging strategy**: `scanner.infrastructure.logging_config` provides consistent stdout/file logger setup mirroring lessons from earlier projects; the engine accepts a logger for observability.
- **Local JSON ingestion**: `JsonFileSourceAdapter` and `VideoMetadataNormalizer` load structured metadata from disk using dataclass-aware codecs.
- **File persistence**: `JsonLinesPersistenceBackend` appends normalized payloads to JSON Lines files for inspection or downstream ingestion.
- **Relational persistence**: `PostgresPersistenceBackend` stores metadata in PostgreSQL tables (`sites`, `videos`) with automatic schema management.
- **HTML ingestion**: `HtmlPageSourceAdapter` orchestrates fetchers (requests/Selenium) and DOM parsing (BeautifulSoup) with configurable CSS selectors and field mappings.
- **Configuration management**: `scanner.config` loads TOML configuration defaults (default `/etc/scanner/config.toml`) with CLI/env overrides for deployment flexibility.
- **CLI workflow**: `scanner.api.cli` offers a simple command for executing the ingestion pipeline end-to-end.
- **Async pipeline**: `AsyncProcessingEngine` enables concurrent ingestion with asyncio semantics, with `run_pipeline` for multi-request orchestration.

## Tooling and Standards
- Python 3.12 base runtime with virtual environment managed locally at `.venv/`.
- Development tooling stack: uv, pytest, mypy, import-linter, black, bandit, flake8.
- Import architecture enforced via `importlinter.ini` layered contract (`api -> domain -> infrastructure`).

## Data Flow (Planned)
1. Source connectors ingest metadata from web pages, local files, or other scanner instances.
2. Domain services normalize and enrich metadata, resolving conflicts and deduplicating records.
3. Persistence layer writes to a relational database with full-text indexing support.
4. Query interfaces expose aggregated metadata through REST/GraphQL APIs and programmatic clients.

Further detail will be added as components are implemented.
