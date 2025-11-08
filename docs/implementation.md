# Implementation Notes

_Last updated: 2025-11-08_

## Repository Layout
- `src/scanner/`: Python package root.
  - `api/`, `domain/`, `infrastructure/`: Layered module placeholders.
- `src/scanner/domain/models.py`: Dataclasses and enums defining metadata, source descriptors, output payloads, and persistence descriptors.
- `src/scanner/domain/interfaces.py`: Abstract base classes for source adapters, normalizers, output transformers, persistence backends, and failure aggregators.
- `src/scanner/domain/engine.py`: Processing engine coordinating registries and orchestration logic.
- `src/scanner/domain/constants.py`: Shared identifiers used across source and normalizer implementations.
- `src/scanner/domain/normalizers.py`: Concrete normalizers, including `VideoMetadataNormalizer`.
- `src/scanner/infrastructure/logging_config.py`: Reusable logging utilities enabling stdout, file, or combined handlers.
- `src/scanner/infrastructure/json_codec.py`: Dataclass-friendly JSON encoder/decoder helpers.
- `src/scanner/infrastructure/sources/json_file.py`: Source adapter that reads local JSON files of `VideoMetadata`.
- `tests/`: Test suite root with package initialization.
- `tests/test_processing_engine.py`: Validates registry resolution, orchestration flow, and error handling.
- `tests/test_logging_config.py`: Exercises logging helper utilities.
- `tests/test_json_codec.py`: Exercises JSON serialization helpers.
- `tests/test_json_file_source.py`: Verifies the JSON file source adapter and end-to-end engine integration.
- `scripts/`: Development helper scripts (`bootstrap.sh`, `activate.sh`, `lint.sh`, `format.sh`).
- `.venv/`: Local virtual environment (ignored by git).

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
- Add additional source adapters (HTML, API) alongside persistence backends, reusing the JSON utilities for fixture-based testing.

This document will capture implementation progress and decisions as the project evolves.


