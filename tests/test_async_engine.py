from __future__ import annotations

from pathlib import Path

import pytest

from scanner import (
    VIDEO_METADATA_JSON_STRUCTURE,
    AsyncProcessingEngine,
    JsonFileSourceAdapter,
    JsonLinesPersistenceBackend,
    NormalizedMetadataTransformer,
    ProcessingRequest,
    VideoMetadataNormalizer,
)
from scanner.domain.engine import NormalizerRegistry, OutputRegistry, PersistenceRegistry, SourceRegistry
from scanner.domain.models import (
    OutputDescriptor,
    OutputFormat,
    PersistenceBackendType,
    PersistenceDescriptor,
    ProcessingReport,
    SourceDescriptor,
    SourceType,
)
from scanner.pipeline import run_pipeline


def build_engine(tmp_path: Path) -> AsyncProcessingEngine:
    source_registry = SourceRegistry(adapters=[JsonFileSourceAdapter()])
    normalizer_registry = NormalizerRegistry(normalizers=[VideoMetadataNormalizer()])
    output_registry = OutputRegistry(transformers=[NormalizedMetadataTransformer()])
    persistence_registry = PersistenceRegistry(backends=[JsonLinesPersistenceBackend()])
    return AsyncProcessingEngine(
        source_registry=source_registry,
        normalizer_registry=normalizer_registry,
        output_registry=output_registry,
        persistence_registry=persistence_registry,
    )


def build_request(metadata_path: Path, output_path: Path) -> ProcessingRequest:
    source_descriptor = SourceDescriptor(
        identifier="async-json",
        source_type=SourceType.FILE,
        structure_id=VIDEO_METADATA_JSON_STRUCTURE,
        configuration={"path": str(metadata_path)},
    )
    output_descriptor = OutputDescriptor(format=OutputFormat.NORMALIZED_METADATA)
    persistence_descriptor = PersistenceDescriptor(
        backend=PersistenceBackendType.FILE_SYSTEM,
        configuration={"path": str(output_path)},
    )
    return ProcessingRequest(source=source_descriptor, output=output_descriptor, persistence=persistence_descriptor)


@pytest.mark.asyncio
async def test_async_engine_processes_request(tmp_path: Path) -> None:
    fixture = Path(__file__).parent / "fixtures" / "video_metadata.json"
    output = tmp_path / "result.jsonl"

    engine = build_engine(tmp_path)
    request = build_request(fixture, output)

    report = await engine.process_async(request)

    assert isinstance(report, ProcessingReport)
    assert report.failures == ()
    assert report.ingested == 2
    assert report.persisted == 2
    assert output.exists()
    contents = output.read_text(encoding="utf-8").strip().splitlines()
    assert len(contents) == 2


@pytest.mark.asyncio
async def test_async_pipeline_runs_requests_in_parallel(tmp_path: Path) -> None:
    fixture = Path(__file__).parent / "fixtures" / "video_metadata.json"
    output_a = tmp_path / "a.jsonl"
    output_b = tmp_path / "b.jsonl"

    engine = build_engine(tmp_path)
    requests = [
        build_request(fixture, output_a),
        build_request(fixture, output_b),
    ]

    reports = await run_pipeline(engine, requests, concurrency=2)

    assert len(reports) == 2
    assert all(report.ingested == 2 for report in reports)
    assert output_a.exists()
    assert output_b.exists()
