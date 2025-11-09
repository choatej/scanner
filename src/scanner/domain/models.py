"""Domain models for the Scanner processing engine."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Mapping, Optional, Sequence


class SourceType(Enum):
    """Broad categories of ingestion sources."""

    WEB_PAGE = auto()
    FILE = auto()
    DATABASE = auto()
    API = auto()


@dataclass(frozen=True)
class SourceDescriptor:
    """Configuration for a specific source to ingest from."""

    identifier: str
    source_type: SourceType
    structure_id: str
    configuration: Mapping[str, Any] = field(default_factory=dict)

    def get(self, key: str, default: Optional[Any] = None) -> Any:
        return self.configuration.get(key, default)


@dataclass(frozen=True)
class SourceStructure:
    """Represents a specific layout or integration target for a source type."""

    structure_id: str
    name: str
    description: Optional[str] = None
    metadata: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class SourceRecord:
    """The raw content produced by a source before normalization."""

    source: SourceDescriptor
    payload: Mapping[str, Any]
    context: Mapping[str, Any] = field(default_factory=dict)


class OutputFormat(Enum):
    """Supported output formats emitted by the processing engine."""

    NORMALIZED_METADATA = auto()
    RAW = auto()
    SUMMARY = auto()


@dataclass(frozen=True)
class OutputDescriptor:
    """Configuration describing how processed output should be produced."""

    format: OutputFormat
    configuration: Mapping[str, Any] = field(default_factory=dict)

    def get(self, key: str, default: Optional[Any] = None) -> Any:
        return self.configuration.get(key, default)


@dataclass(frozen=True)
class OutputPayload:
    """A processed output record ready for persistence."""

    descriptor: OutputDescriptor
    content: Mapping[str, Any]


class PersistenceBackendType(Enum):
    """Types of persistence targets supported by the platform."""

    FILE_SYSTEM = auto()
    DATABASE = auto()
    MESSAGE_QUEUE = auto()
    REMOTE_API = auto()


@dataclass(frozen=True)
class PersistenceDescriptor:
    """Configuration describing where processed output should be stored."""

    backend: PersistenceBackendType
    target: str | None = None
    configuration: Mapping[str, Any] = field(default_factory=dict)

    def get(self, key: str, default: Optional[Any] = None) -> Any:
        return self.configuration.get(key, default)


@dataclass(frozen=True)
class VideoMetadata:
    """Normalized metadata describing a video."""

    title: str
    description: Optional[str]
    length_seconds: Optional[int]
    tags: Sequence[str] = field(default_factory=list)
    categories: Sequence[str] = field(default_factory=list)
    actors: Sequence[str] = field(default_factory=list)
    source_site: Optional[str] = None
    extra: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class IngestionRecord:
    """A normalized record produced from a raw source record."""

    metadata: VideoMetadata
    source_record: SourceRecord


@dataclass(frozen=True)
class ProcessingRequest:
    """Processing workflow linking source, output, and persistence."""

    source: SourceDescriptor
    output: OutputDescriptor
    persistence: PersistenceDescriptor


@dataclass(frozen=True)
class PersistenceResult:
    """Outcome reported by a persistence backend."""

    stored_count: int
    failed_count: int = 0
    details: Optional[Mapping[str, Any]] = None


@dataclass(frozen=True)
class ProcessingReport:
    """Summary of a processing run."""

    ingested: int
    persisted: int
    failures: Sequence[str] = field(default_factory=list)
    persistence_result: Optional[PersistenceResult] = None
