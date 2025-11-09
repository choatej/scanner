# Implementation Notes

_Last updated: 2025-11-08_

## Repository Layout
- `src/scanner/`: Python package root.
  - `api/`, `domain/`, `infrastructure/`: Layered module placeholders.
- `src/scanner/domain/models.py`: Dataclasses and enums defining metadata, source descriptors, output payloads, and persistence descriptors.
- `src/scanner/domain/interfaces.py`: Abstract base classes for source adapters, normalizers, output transformers, persistence backends, and failure aggregators.
- `src/scanner/domain/engine.py`: Processing engine coordinating registries and orchestration logic.
- `src/scanner/domain/constants.py`: Shared identifiers used across adapters/normalizers.
- `src/scanner/domain/normalizers.py`: Concrete normalizers, including `VideoMetadataNormalizer`.
- `src/scanner/domain/transformers.py`: Output transformers such as `NormalizedMetadataTransformer`.
- `src/scanner/infrastructure/logging_config.py`: Reusable logging utilities enabling stdout, file, or combined handlers.
- `src/scanner/infrastructure/json_codec.py`: Dataclass-friendly JSON helpers.
- `src/scanner/infrastructure/html/`: HTML helpers (`fetchers`, BeautifulSoup DOM adapter).
- `src/scanner/infrastructure/sources/json_file.py`: Source adapter that reads local JSON metadata.
- `src/scanner/infrastructure/sources/html_page.py`: HTML page adapter configurable via CSS selectors.
- `src/scanner/infrastructure/persistence/jsonl.py`: Persistence backend writing JSON Lines output.
- `src/scanner/infrastructure/persistence/postgres.py`: PostgreSQL backend with `sites`/`videos` tables and schema helpers.
- `src/scanner/api/cli.py`: Lightweight CLI entrypoint for ingesting a JSON file into JSONL output.
- `src/scanner/config.py`: Facilities for loading TOML configuration defaults and overrides.
- `src/scanner/pipeline/async_engine.py`: Async orchestration layer and helpers for concurrent ingestion.
- `tests/`: Test suite root with package initialization.
- `tests/test_processing_engine.py`: Validates registry resolution, orchestration flow, and error handling.
- `tests/test_logging_config.py`: Exercises logging helper utilities.
- `tests/test_json_codec.py`: Exercises JSON serialization helpers.
- `tests/test_json_file_source.py`: Verifies the JSON file source adapter and engine integration.
- `tests/test_html_source_adapter.py`: Validates the HTML adapter against sample markup.
- `tests/test_config.py`: Sanity checks for configuration loading helpers.
- `tests/test_jsonl_persistence.py`: Ensures JSON Lines persistence backend writes expected data.
- `tests/test_cli.py`: Runs the CLI end-to-end against fixture metadata.
- `tests/test_postgres_persistence.py`: Integration test for the PostgreSQL backend (requires `TEST_PG_DATABASE_URL`).
- `tests/test_async_engine.py`: Validates the async processing engine and pipeline helper.
- `scripts/`: Development helper scripts (`bootstrap.sh`, `activate.sh`, `lint.sh`, `format.sh`).
- `.pre-commit-config.yaml`: Local hook configuration running `scripts/lint-fix.sh` alongside basic hygiene checks.
- `.github/workflows/ci.yml`: Continuous integration pipeline executing the full lint and test suite on PRs, pushes to `main`, and manual dispatch.
- `.venv/`: Local virtual environment (ignored by git).
- `config/example.toml`: Example configuration file demonstrating defaults for production deployments.
- `Dockerfile`, `docker-compose.yml`, `.dockerignore`: Containerized runtime and orchestration for Scanner + PostgreSQL.

## Tooling Configuration
- `pyproject.toml`: Central configuration for packaging and tooling.
- `importlinter.ini`: Contracts ensuring architecture layering.
- `.gitignore`: Standard Python, build, and editor artifacts.

## Next Steps
- Flesh out domain models for video metadata entities.
- Implement ingestion pipeline abstractions.
- Establish database schema and migration workflow.
- Scaffold REST/GraphQL API endpoints.
- Expand coverage for error scenarios (retry semantics, partial persistence) and introduce integration tests with concrete adapters.
- Wire structured logging through adapters and persistence backends, ensuring correlation IDs for multi-source ingestion.
- Extend CI jobs with caching and artifact publishing (coverage reports, mypy caches) for faster feedback loops.
- Add additional source adapters (HTML, API) alongside persistence backends, reusing the JSON utilities for fixture-based testing.

This document will capture implementation progress and decisions as the project evolves.
