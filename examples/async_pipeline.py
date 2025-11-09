"""Asynchronous ingestion example."""

import asyncio
from pathlib import Path

from scanner import (
    AsyncProcessingEngine,
    JsonFileSourceAdapter,
    JsonLinesPersistenceBackend,
    NormalizedMetadataTransformer,
    ProcessingRequest,
    VIDEO_METADATA_JSON_STRUCTURE,
    VideoMetadataNormalizer,
)
from scanner.domain.engine import NormalizerRegistry, OutputRegistry, PersistenceRegistry, SourceRegistry
from scanner.domain.models import (
    OutputDescriptor,
    OutputFormat,
    PersistenceBackendType,
    PersistenceDescriptor,
    SourceDescriptor,
    SourceType,
)
from scanner.pipeline import run_pipeline


def build_engine() -> AsyncProcessingEngine:
    return AsyncProcessingEngine(
        source_registry=SourceRegistry(adapters=[JsonFileSourceAdapter()]),
        normalizer_registry=NormalizerRegistry(normalizers=[VideoMetadataNormalizer()]),
        output_registry=OutputRegistry(transformers=[NormalizedMetadataTransformer()]),
        persistence_registry=PersistenceRegistry(backends=[JsonLinesPersistenceBackend()]),
    )


def build_request(metadata_path: Path, output_path: Path) -> ProcessingRequest:
    source_descriptor = SourceDescriptor(
        identifier="example",
        source_type=SourceType.FILE,
        structure_id=VIDEO_METADATA_JSON_STRUCTURE,
        configuration={"path": str(metadata_path)},
    )
    output_descriptor = OutputDescriptor(format=OutputFormat.NORMALIZED_METADATA)
    persistence_descriptor = PersistenceDescriptor(
        backend=PersistenceBackendType.FILE_SYSTEM,
        configuration={"path": str(output_path)},
    )
    return ProcessingRequest(
        source=source_descriptor,
        output=output_descriptor,
        persistence=persistence_descriptor,
    )


async def main() -> None:
    engine = build_engine()
    metadata_file = Path(__file__).parent.parent / "tests" / "fixtures" / "video_metadata.json"
    output_file = Path(__file__).parent / "async_pipeline_output.jsonl"
    requests = [build_request(metadata_file, output_file)]
    await run_pipeline(engine, requests)


if __name__ == "__main__":
    asyncio.run(main())

