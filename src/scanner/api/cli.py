"""Command-line interface for running Scanner ingestion workflows."""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path
from typing import Sequence

from .. import (
    VIDEO_METADATA_JSON_STRUCTURE,
    JsonFileSourceAdapter,
    JsonLinesPersistenceBackend,
    LoggingConfig,
    NormalizedMetadataTransformer,
    ProcessingEngine,
    ProcessingRequest,
    VideoMetadataNormalizer,
)
from ..domain.engine import NormalizerRegistry, OutputRegistry, PersistenceRegistry, SourceRegistry
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
        required=True,
        help="Path to the JSON Lines file where normalized metadata should be written.",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        help="Logging level (default: INFO).",
    )
    return parser


def create_processing_request(metadata_file: Path, output_file: Path) -> ProcessingRequest:
    source_descriptor = SourceDescriptor(
        identifier="local-json-file",
        source_type=SourceType.FILE,
        structure_id=VIDEO_METADATA_JSON_STRUCTURE,
        configuration={"path": str(metadata_file)},
    )
    output_descriptor = OutputDescriptor(format=OutputFormat.NORMALIZED_METADATA)
    persistence_descriptor = PersistenceDescriptor(
        backend=PersistenceBackendType.FILE_SYSTEM,
        configuration={"path": str(output_file)},
    )
    return ProcessingRequest(
        source=source_descriptor,
        output=output_descriptor,
        persistence=persistence_descriptor,
    )


def create_engine(logger: logging.Logger | None = None) -> ProcessingEngine:
    return ProcessingEngine(
        source_registry=SourceRegistry(adapters=[JsonFileSourceAdapter()]),
        normalizer_registry=NormalizerRegistry(normalizers=[VideoMetadataNormalizer()]),
        output_registry=OutputRegistry(transformers=[NormalizedMetadataTransformer()]),
        persistence_registry=PersistenceRegistry(backends=[JsonLinesPersistenceBackend()]),
        logger=logger,
    )


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    metadata_path = Path(args.metadata_file).expanduser()
    output_path = Path(args.output_file).expanduser()

    logger = configure_stdout_logger(
        "scanner.cli",
        LoggingConfig(level=getattr(logging, str(args.log_level).upper(), logging.INFO)),
    )

    engine = create_engine(logger=logger)
    request = create_processing_request(metadata_path, output_path)
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
