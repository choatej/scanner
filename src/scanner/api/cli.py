"""Command-line interface for running Scanner ingestion workflows."""

from __future__ import annotations

import argparse
import logging
import os
import sys
from pathlib import Path
from typing import Sequence

from .. import (
    VIDEO_METADATA_JSON_STRUCTURE,
    JsonFileSourceAdapter,
    JsonLinesPersistenceBackend,
    LoggingConfig,
    NormalizedMetadataTransformer,
    PostgresPersistenceBackend,
    ProcessingEngine,
    ProcessingRequest,
    VideoMetadataNormalizer,
)
from ..domain.engine import NormalizerRegistry, OutputRegistry, PersistenceRegistry, SourceRegistry
from ..domain.interfaces import PersistenceBackend as PersistenceBackendInterface
from ..domain.models import (
    OutputDescriptor,
    OutputFormat,
    PersistenceBackendType,
    PersistenceDescriptor,
    SourceDescriptor,
    SourceType,
)
from ..infrastructure.logging_config import configure_stdout_logger


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run Scanner ingestion for local JSON metadata files.")
    parser.add_argument(
        "--metadata-file",
        required=True,
        help="Path to the JSON file containing an array of video metadata objects.",
    )
    parser.add_argument(
        "--output-file",
        help="Path to the JSON Lines file where normalized metadata should be written (required for jsonl backend).",
    )
    parser.add_argument(
        "--database-url",
        help="Database URL for PostgreSQL persistence backend (default: DATABASE_URL env variable).",
    )
    parser.add_argument(
        "--persistence-backend",
        choices=["jsonl", "postgres"],
        default="jsonl",
        help="Persistence backend to use (default: jsonl).",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        help="Logging level (default: INFO).",
    )
    return parser


def create_processing_request(
    metadata_file: Path,
    backend: str,
    output_file: Path | None,
    database_url: str | None,
) -> ProcessingRequest:
    source_descriptor = SourceDescriptor(
        identifier="local-json-file",
        source_type=SourceType.FILE,
        structure_id=VIDEO_METADATA_JSON_STRUCTURE,
        configuration={"path": str(metadata_file)},
    )
    output_descriptor = OutputDescriptor(format=OutputFormat.NORMALIZED_METADATA)

    if backend == "postgres":
        if not database_url:
            raise ValueError("PostgreSQL backend requires --database-url or DATABASE_URL environment variable")
        persistence_descriptor = PersistenceDescriptor(
            backend=PersistenceBackendType.DATABASE,
            configuration={"database_url": database_url},
        )
    else:
        if output_file is None:
            raise ValueError("JSONL backend requires --output-file")
        persistence_descriptor = PersistenceDescriptor(
            backend=PersistenceBackendType.FILE_SYSTEM,
            configuration={"path": str(output_file)},
        )

    return ProcessingRequest(
        source=source_descriptor,
        output=output_descriptor,
        persistence=persistence_descriptor,
    )


def create_engine(
    backend: str,
    database_url: str | None,
    logger: logging.Logger | None = None,
) -> ProcessingEngine:
    persistence_backends: list[PersistenceBackendInterface] = [JsonLinesPersistenceBackend()]
    if backend == "postgres":
        if not database_url:
            raise ValueError("PostgreSQL backend requires --database-url or DATABASE_URL environment variable")
        persistence_backends.append(PostgresPersistenceBackend())

    return ProcessingEngine(
        source_registry=SourceRegistry(adapters=[JsonFileSourceAdapter()]),
        normalizer_registry=NormalizerRegistry(normalizers=[VideoMetadataNormalizer()]),
        output_registry=OutputRegistry(transformers=[NormalizedMetadataTransformer()]),
        persistence_registry=PersistenceRegistry(backends=persistence_backends),
        logger=logger,
    )


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    metadata_path = Path(args.metadata_file).expanduser()
    output_path = Path(args.output_file).expanduser() if args.output_file else None
    database_url = args.database_url or os.environ.get("DATABASE_URL")

    logger = configure_stdout_logger(
        "scanner.cli",
        LoggingConfig(level=getattr(logging, str(args.log_level).upper(), logging.INFO)),
    )

    try:
        engine = create_engine(args.persistence_backend, database_url, logger=logger)
        request = create_processing_request(metadata_path, args.persistence_backend, output_path, database_url)
    except ValueError as exc:
        logger.error("%s", exc)
        return 1
    report = engine.process(request)
    logger.info(
        "Ingestion complete",
        extra={
            "ingested": report.ingested,
            "persisted": report.persisted,
            "failures": len(report.failures),
        },
    )
    if report.failures:
        for reason in report.failures:
            logger.error("Failure: %s", reason)
        return 1
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
