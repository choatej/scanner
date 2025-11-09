from __future__ import annotations

from dataclasses import asdict
from pathlib import Path
from typing import Iterable, List

from scanner.domain.constants import VIDEO_METADATA_JSON_STRUCTURE
from scanner.domain.engine import (
    NormalizerRegistry,
    OutputRegistry,
    PersistenceRegistry,
    ProcessingEngine,
    SourceRegistry,
)
from scanner.domain.interfaces import OutputTransformer, PersistenceBackend
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
    SourceType,
    VideoMetadata,
)
from scanner.domain.normalizers import VideoMetadataNormalizer
from scanner.infrastructure.json_codec import dump_dataclass_list, load_dataclass_list
from scanner.infrastructure.sources.json_file import JsonFileSourceAdapter


class PassthroughTransformer(OutputTransformer):
    def supports(self, descriptor: OutputDescriptor) -> bool:
        return descriptor.format == OutputFormat.NORMALIZED_METADATA

    def transform(
        self,
        records: Iterable[IngestionRecord],
        descriptor: OutputDescriptor,
    ) -> Iterable[OutputPayload]:
        for record in records:
            yield OutputPayload(descriptor=descriptor, content=asdict(record.metadata))


class MemoryPersistenceBackend(PersistenceBackend):
    def __init__(self) -> None:
        self.payloads: List[OutputPayload] = []

    def supports(self, descriptor: PersistenceDescriptor) -> bool:
        return descriptor.backend == PersistenceBackendType.FILE_SYSTEM

    def persist(
        self,
        payloads: Iterable[OutputPayload],
        descriptor: PersistenceDescriptor,
    ) -> PersistenceResult:
        collected = list(payloads)
        self.payloads.extend(collected)
        return PersistenceResult(stored_count=len(collected))


def create_json_fixture(path: Path) -> None:
    dump_dataclass_list(
        path,
        [
            VideoMetadata(
                title="Fixture Video",
                description="Fixture description",
                length_seconds=90,
                tags=["fixture"],
                categories=["tests"],
                actors=["Tester"],
                source_site="fixture.example",
                extra={"quality": "720p"},
            ),
        ],
    )


def test_json_file_source_adapter_reads_metadata(tmp_path: Path) -> None:
    json_path = tmp_path / "videos.json"
    create_json_fixture(json_path)

    descriptor = SourceDescriptor(
        identifier="local-json",
        source_type=SourceType.FILE,
        structure_id=VIDEO_METADATA_JSON_STRUCTURE,
        configuration={"path": str(json_path)},
    )
    adapter = JsonFileSourceAdapter()
    records = list(adapter.read(descriptor))

    assert len(records) == 1
    record = records[0]
    assert record.payload["title"] == "Fixture Video"
    assert isinstance(record.context["metadata"], VideoMetadata)


def test_processing_engine_with_json_source(tmp_path: Path) -> None:
    json_path = tmp_path / "videos.json"
    create_json_fixture(json_path)

    source_descriptor = SourceDescriptor(
        identifier="json-source",
        source_type=SourceType.FILE,
        structure_id=VIDEO_METADATA_JSON_STRUCTURE,
        configuration={"path": str(json_path)},
    )
    output_descriptor = OutputDescriptor(format=OutputFormat.NORMALIZED_METADATA)
    persistence_descriptor = PersistenceDescriptor(
        backend=PersistenceBackendType.FILE_SYSTEM,
        target="memory",
    )

    persistence_backend = MemoryPersistenceBackend()

    engine = ProcessingEngine(
        source_registry=SourceRegistry(adapters=[JsonFileSourceAdapter()]),
        normalizer_registry=NormalizerRegistry(normalizers=[VideoMetadataNormalizer()]),
        output_registry=OutputRegistry(transformers=[PassthroughTransformer()]),
        persistence_registry=PersistenceRegistry(backends=[persistence_backend]),
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
    assert persistence_backend.payloads[0].content["title"] == "Fixture Video"


def test_load_dataclass_list_matches_fixture(tmp_path: Path) -> None:
    json_path = tmp_path / "videos.json"
    create_json_fixture(json_path)

    records = load_dataclass_list(json_path, VideoMetadata)
    assert records[0].title == "Fixture Video"
