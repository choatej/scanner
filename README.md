# Scanner - A tool for scanning and cataloging videos on video sites.

## Current Status

The project is at an early prototype stage:

- ✅ Python package scaffolding with processing engine, registries, and domain models.
- ✅ JSON ingestion pipeline with CLI (`scanner-ingest`) that reads structured metadata files and writes JSON Lines output.
- ✅ PostgreSQL persistence backend (2-table schema) for normalized video metadata.
- ✅ Tooling, tests, pre-commit hooks, and CI workflows.
- 🚧 Upcoming milestones are tracked in `docs/roadmap.md`.

## Overview

Scanner aims to ingest video metadata from multiple sources (web, local files, other scanners), normalize the data, and expose it through flexible APIs. The architecture is designed to be modular:

- Source adapters parse specific input formats.
- Normalizers produce a canonical `VideoMetadata` representation.
- Persistence backends store normalized records.
- Output transformers and APIs present the data to consumers.

## Development

### Requirements
- Python 3.12+
- uv (preferred for dependency management)
- Postgres 17 (planned persistence backend)

Development tooling is configured via `pyproject.toml` and includes `black`, `isort`, `flake8`, `mypy`, `pytest`, `bandit`, and `import-linter`.

### Quick Start
```bash
scripts/bootstrap.sh         # create .venv and install deps
scripts/format.sh            # run black/isort
scripts/lint.sh              # black/isort/flake8/mypy/bandit/import-linter
pytest                       # run tests
scanner-ingest --help        # CLI for ingesting JSON metadata into JSONL
```

To exercise the PostgreSQL backend locally:
```bash
export TEST_PG_DATABASE_URL="postgresql+psycopg://user:password@localhost:5432/scanner"
pytest tests/test_postgres_persistence.py
```

### Continuous Integration

GitHub Actions run linting and tests on pull requests and merges to `main`. Branch protection requires passing CI, at least one review (including Copilot suggestions), and all conversations resolved before merging.

## License

This software is released under the MIT License. See [LICENSE](LICENSE) for details.
