"""Command-line interface for running Scanner ingestion workflows."""

from __future__ import annotations

import argparse
import logging
import os
import sys
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping, Sequence

from .. import (
    HTML_PAGE_STRUCTURE,
    VIDEO_METADATA_JSON_STRUCTURE,
    HtmlPageSourceAdapter,
    JsonFileSourceAdapter,
    JsonLinesPersistenceBackend,
    LoggingConfig,
    NormalizedMetadataTransformer,
    PostgresPersistenceBackend,
    ProcessingEngine,
    ProcessingRequest,
    VideoMetadataNormalizer,
)
from ..config import (
    DEFAULT_CONFIG_PATH,
    AppConfig,
    ConfigError,
    load_config,
    load_mapping_file,
)
from ..domain.engine import NormalizerRegistry, OutputRegistry, PersistenceRegistry, SourceRegistry
from ..domain.models import (
    OutputDescriptor,
    OutputFormat,
    PersistenceBackendType,
    PersistenceDescriptor,
    ProcessingReport,
    SourceDescriptor,
    SourceType,
)
from ..infrastructure.logging_config import configure_stdout_logger


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run Scanner ingestion.")
    parser.add_argument(
        "--config",
        default=str(DEFAULT_CONFIG_PATH),
        help=f"Path to configuration file (default: {DEFAULT_CONFIG_PATH})",
    )
    parser.add_argument(
        "--metadata-file",
        help="Path to metadata file (overrides configuration for json_file adapter).",
    )
    parser.add_argument(
        "--source-adapter",
        choices=["json_file", "html_page"],
        help="Source adapter to use (overrides configuration).",
    )
    parser.add_argument(
        "--source-config",
        help="Path to adapter configuration override (TOML or JSON).",
    )
    parser.add_argument(
        "--output-file",
        help="Path to JSON Lines output (overrides configuration for jsonl backend).",
    )
    parser.add_argument(
        "--database-url",
        help="Database URL for PostgreSQL backend (overrides configuration or DATABASE_URL).",
    )
    parser.add_argument(
        "--persistence-backend",
        choices=["jsonl", "postgres"],
        help="Persistence backend to use (overrides configuration).",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        help="Logging level (default: INFO).",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    config_path = Path(args.config).expanduser()

    try:
        config, found = load_config(config_path)
    except ConfigError as exc:
        print(f"Configuration error: {exc}", file=sys.stderr)
        return 1

    try:
        merged = _merge_config(config, found, args, os.environ)
    except ConfigError as exc:
        print(f"Configuration error: {exc}", file=sys.stderr)
        return 1

    logger = configure_stdout_logger(
        "scanner.cli",
        LoggingConfig(level=getattr(logging, str(args.log_level).upper(), logging.INFO)),
    )

    engine = _create_engine(logger=logger)
    request = create_processing_request(merged.source_descriptor, merged.persistence_descriptor)
    report = engine.process(request)
    return _report(logger, report)


@dataclass
class LoadedConfig:
    source_descriptor: SourceDescriptor
    persistence_descriptor: PersistenceDescriptor


def _merge_config(
    config: AppConfig,
    config_found: bool,
    args: argparse.Namespace,
    env: Mapping[str, str],
) -> LoadedConfig:
    source_adapter = args.source_adapter or config.source.adapter
    source_conf = dict(config.source.configuration)

    if args.source_config:
        override_mapping = load_mapping_file(Path(args.source_config).expanduser())
        source_conf.update(override_mapping)
    if args.metadata_file:
        source_conf["path"] = str(Path(args.metadata_file).expanduser())

    source_descriptor = _build_source_descriptor(source_adapter, source_conf)

    persistence_backend = args.persistence_backend or config.persistence.adapter
    persistence_conf = dict(config.persistence.configuration)
    if args.output_file:
        persistence_conf["path"] = str(Path(args.output_file).expanduser())
    database_url = args.database_url or env.get("DATABASE_URL")
    if database_url:
        persistence_conf["database_url"] = database_url

    persistence_descriptor = _build_persistence_descriptor(persistence_backend, persistence_conf)

    if source_descriptor is None or persistence_descriptor is None:
        missing = []
        if source_descriptor is None:
            missing.append("source configuration")
        if persistence_descriptor is None:
            missing.append("persistence configuration")
        message = f"Missing required {' and '.join(missing)}"
        if not config_found and args.config == str(DEFAULT_CONFIG_PATH):
            message += f"; configuration file not found at {DEFAULT_CONFIG_PATH}"
        raise ConfigError(message)

    return LoadedConfig(source_descriptor, persistence_descriptor)


def _build_source_descriptor(adapter: str, configuration: Mapping[str, object]) -> SourceDescriptor | None:
    adapter_key = adapter.lower()

    if adapter_key == "json_file":
        path = configuration.get("path")
        if not path:
            return None
        return SourceDescriptor(
            identifier="json-file",
            source_type=SourceType.FILE,
            structure_id=VIDEO_METADATA_JSON_STRUCTURE,
            configuration={"path": str(path)},
        )

    if adapter_key == "html_page":
        start_urls = configuration.get("start_urls")
        item_selector = configuration.get("item_selector")
        if not start_urls or not item_selector:
            return None
        if isinstance(start_urls, str):
            normalized_urls = [start_urls]
        elif isinstance(start_urls, Iterable):
            normalized_urls = [str(url) for url in start_urls]
        else:
            return None
        config_copy = dict(configuration)
        config_copy["start_urls"] = normalized_urls
        return SourceDescriptor(
            identifier="html-page",
            source_type=SourceType.WEB_PAGE,
            structure_id=HTML_PAGE_STRUCTURE,
            configuration=config_copy,
        )

    raise ConfigError(f"Unknown source adapter '{adapter}'")


def _build_persistence_descriptor(backend: str, configuration: Mapping[str, object]) -> PersistenceDescriptor | None:
    backend_key = backend.lower()

    if backend_key == "jsonl":
        path = configuration.get("path")
        if not path:
            return None
        return PersistenceDescriptor(
            backend=PersistenceBackendType.FILE_SYSTEM,
            configuration={"path": str(path)},
        )

    if backend_key == "postgres":
        url = configuration.get("database_url")
        if not url:
            return None
        return PersistenceDescriptor(
            backend=PersistenceBackendType.DATABASE,
            configuration={"database_url": str(url)},
        )

    raise ConfigError(f"Unknown persistence backend '{backend}'")


def _create_engine(logger: logging.Logger | None = None) -> ProcessingEngine:
    return ProcessingEngine(
        source_registry=SourceRegistry(adapters=[JsonFileSourceAdapter(), HtmlPageSourceAdapter()]),
        normalizer_registry=NormalizerRegistry(normalizers=[VideoMetadataNormalizer()]),
        output_registry=OutputRegistry(transformers=[NormalizedMetadataTransformer()]),
        persistence_registry=PersistenceRegistry(
            backends=[JsonLinesPersistenceBackend(), PostgresPersistenceBackend()]
        ),
        logger=logger,
    )


def create_processing_request(
    source_descriptor: SourceDescriptor,
    persistence_descriptor: PersistenceDescriptor,
) -> ProcessingRequest:
    output_descriptor = OutputDescriptor(format=OutputFormat.NORMALIZED_METADATA)
    return ProcessingRequest(
        source=source_descriptor,
        output=output_descriptor,
        persistence=persistence_descriptor,
    )


def _report(logger: logging.Logger, report: ProcessingReport) -> int:
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
