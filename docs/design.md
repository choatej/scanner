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


