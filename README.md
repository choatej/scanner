# Scanner - A tool for scanning and cataloging videos on video sites.

## Current Status

The project is at an early prototype stage:

- ✅ Python package scaffolding with processing engine, registries, and domain models.
- ✅ JSON ingestion pipeline with CLI (`scanner-ingest`) that reads structured metadata files and writes JSON Lines output.
- ✅ PostgreSQL persistence backend (2-table schema) for normalized video metadata.
- ✅ HTML ingestion adapter (requests/BeautifulSoup with optional Selenium) driven by configuration.
- ✅ Async ingestion pipeline capable of processing multiple locators concurrently.
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
- PostgreSQL 17 (for relational persistence)

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

To ingest HTML pages, prepare a source configuration (see `HtmlPageSourceAdapter`) and choose a persistence backend:

```bash
scanner-ingest \
  --metadata-file /path/to/page.html \
  --persistence-backend jsonl \
  --output-file /tmp/videos.jsonl

scanner-ingest \
  --metadata-file https://example.com/videos \
  --persistence-backend postgres \
  --database-url postgresql+psycopg://scanner:scanner@localhost:5432/scanner
```

### Async Pipeline

The ingestion engine now runs asynchronously. The CLI leverages this under the hood, but you can also orchestrate multiple requests programmatically:

```python
import asyncio

from scanner import (
    AsyncProcessingEngine,
    JsonFileSourceAdapter,
    JsonLinesPersistenceBackend,
    NormalizedMetadataTransformer,
    ProcessingRequest,
    VIDEO_METADATA_JSON_STRUCTURE,
    SourceDescriptor,
    SourceRegistry,
    PersistenceRegistry,
    NormalizerRegistry,
    OutputRegistry,
    VideoMetadataNormalizer,
)
from scanner.pipeline import run_pipeline
from scanner.domain.models import (
    OutputDescriptor,
    OutputFormat,
    PersistenceBackendType,
    PersistenceDescriptor,
    SourceType,
)

engine = AsyncProcessingEngine(
    source_registry=SourceRegistry(adapters=[JsonFileSourceAdapter()]),
    normalizer_registry=NormalizerRegistry(normalizers=[VideoMetadataNormalizer()]),
    output_registry=OutputRegistry(transformers=[NormalizedMetadataTransformer()]),
    persistence_registry=PersistenceRegistry(backends=[JsonLinesPersistenceBackend()]),
)

requests = [
    ProcessingRequest(
        source=SourceDescriptor(
            identifier="example",
            source_type=SourceType.FILE,
            structure_id=VIDEO_METADATA_JSON_STRUCTURE,
            configuration={"path": "/data/one.json"},
        ),
        output=OutputDescriptor(format=OutputFormat.NORMALIZED_METADATA),
        persistence=PersistenceDescriptor(
            backend=PersistenceBackendType.FILE_SYSTEM,
            configuration={"path": "/tmp/out.jsonl"},
        ),
    )
]

asyncio.run(run_pipeline(engine, requests))
```

### Running with Docker Compose

Docker resources live at the repository root (`Dockerfile`, `docker-compose.yml`). The default compose stack includes:

- `postgres`: PostgreSQL 17 instance.
- `scanner`: containerized CLI that ingests the sample metadata in `tests/fixtures/video_metadata.json` into Postgres.

```bash
docker compose up --build scanner
```

To ingest different metadata files, mount them and override the command:

```bash
docker compose run --rm \
  -v "$(pwd)/my_data:/data" \
  scanner \
  --metadata-file /data/custom.json \
  --persistence-backend postgres
```

### Continuous Integration

GitHub Actions run linting and tests on pull requests and merges to `main`. Branch protection requires passing CI, at least one review (including Copilot suggestions), and all conversations resolved before merging.

## License

This software is released under the MIT License. See [LICENSE](LICENSE) for details.
