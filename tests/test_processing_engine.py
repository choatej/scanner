from __future__ import annotations

from typing import Iterable, List

import pytest

from scanner.domain.engine import (
    ListFailureAggregator,
    NormalizerRegistry,
    OutputRegistry,
    PersistenceRegistry,
    ProcessingEngine,
    RegistryError,
    SourceRegistry,
)
from scanner.domain.interfaces import (
    Normalizer,
    OutputTransformer,
    PersistenceBackend,
    SourceAdapter,
)
from scanner.domain.models import (
    IngestionRecord,
    OutputDescriptor,
    OutputFormat,
    OutputPayload,
    PersistenceBackendType,
    PersistenceDescriptor,
    PersistenceResult,
    ProcessingRequest,
    SourceDescriptor,
    SourceRecord,
    SourceStructure,
    SourceType,
    VideoMetadata,
)


class StubSourceAdapter(SourceAdapter):
    def __init__(self) -> None:
        self.read_calls: List[SourceDescriptor] = []

    def supports(self, descriptor: SourceDescriptor) -> bool:
        return descriptor.source_type == SourceType.WEB_PAGE

    def describe_structure(self, descriptor: SourceDescriptor) -> SourceStructure:
        structure_id = descriptor.structure_id
        return SourceStructure(
            structure_id=structure_id,
            name="Stub Structure",
            description="Test structure",
        )

    def read(self, descriptor: SourceDescriptor) -> Iterable[SourceRecord]:
        self.read_calls.append(descriptor)
        yield SourceRecord(
            source=descriptor,
            payload={
                "title": "Example Video",
                "length_seconds": 120,
            },
        )


class StubNormalizer(Normalizer):
    def supports(self, descriptor: SourceDescriptor) -> bool:
        return True

    def normalize(self, record: SourceRecord) -> IngestionRecord:
        metadata = VideoMetadata(
            title=str(record.payload.get("title", "Untitled")),
            description=None,
            length_seconds=int(record.payload.get("length_seconds", 0)),
            source_site=record.source.structure_id,
        )
        return IngestionRecord(metadata=metadata, source_record=record)


class StubOutputTransformer(OutputTransformer):
    def supports(self, descriptor: OutputDescriptor) -> bool:
        return descriptor.format is OutputFormat.NORMALIZED_METADATA

    def transform(self, records: Iterable[IngestionRecord], descriptor: OutputDescriptor) -> Iterable[OutputPayload]:
        for record in records:
            yield OutputPayload(
                descriptor=descriptor,
                content={
                    "title": record.metadata.title,
                    "length_seconds": record.metadata.length_seconds,
                },
            )


class StubPersistenceBackend(PersistenceBackend):
    def __init__(self) -> None:
        self.persist_calls: List[List[OutputPayload]] = []

    def supports(self, descriptor: PersistenceDescriptor) -> bool:
        return descriptor.backend is PersistenceBackendType.FILE_SYSTEM

    def persist(self, payloads: Iterable[OutputPayload], descriptor: PersistenceDescriptor) -> PersistenceResult:
        batch = list(payloads)
        self.persist_calls.append(batch)
        return PersistenceResult(
            stored_count=len(batch),
        )


def build_engine() -> ProcessingEngine:
    source_registry = SourceRegistry(adapters=[StubSourceAdapter()])
    normalizer_registry = NormalizerRegistry(
        normalizers=[StubNormalizer()],
    )
    output_registry = OutputRegistry(
        transformers=[StubOutputTransformer()],
    )
    persistence_registry = PersistenceRegistry(
        backends=[StubPersistenceBackend()],
    )
    return ProcessingEngine(
        source_registry=source_registry,
        normalizer_registry=normalizer_registry,
        output_registry=output_registry,
        persistence_registry=persistence_registry,
        failure_aggregator=ListFailureAggregator(),
    )


def test_processing_engine_runs_end_to_end() -> None:
    engine = build_engine()
    source_descriptor = SourceDescriptor(
        identifier="stub-web",
        source_type=SourceType.WEB_PAGE,
        structure_id="youtube.com",
    )
    output_descriptor = OutputDescriptor(
        format=OutputFormat.NORMALIZED_METADATA,
    )
    persistence_descriptor = PersistenceDescriptor(
        backend=PersistenceBackendType.FILE_SYSTEM,
        target="memory://",
    )
    request = ProcessingRequest(
        source=source_descriptor,
        output=output_descriptor,
        persistence=persistence_descriptor,
    )

    report = engine.process(request)

    assert report.ingested == 1
    assert report.persisted == 1
    assert not report.failures
    assert report.persistence_result is not None
    assert report.persistence_result.stored_count == 1


def test_processing_engine_missing_adapter_raises() -> None:
    engine = build_engine()
    unsupported_descriptor = SourceDescriptor(
        identifier="unsupported",
        source_type=SourceType.DATABASE,
        structure_id="postgres",
    )
    request = ProcessingRequest(
        source=unsupported_descriptor,
        output=OutputDescriptor(format=OutputFormat.NORMALIZED_METADATA),
        persistence=PersistenceDescriptor(
            backend=PersistenceBackendType.FILE_SYSTEM,
            target="memory://",
        ),
    )

    with pytest.raises(RegistryError):
        engine.process(request)
