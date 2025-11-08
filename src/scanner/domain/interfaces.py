"""Interfaces defining the processing engine boundaries."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Iterable, Sequence

from .models import (
    IngestionRecord,
    OutputDescriptor,
    OutputPayload,
    PersistenceDescriptor,
    PersistenceResult,
    SourceDescriptor,
    SourceRecord,
    SourceStructure,
)


class SourceAdapter(ABC):
    """Reads raw records from a configured source."""

    @abstractmethod
    def supports(self, descriptor: SourceDescriptor) -> bool:
        """Return True if this adapter can handle the source descriptor."""

    @abstractmethod
    def describe_structure(
        self,
        descriptor: SourceDescriptor,
    ) -> SourceStructure:
        """Return details about the source structure."""

    @abstractmethod
    def read(self, descriptor: SourceDescriptor) -> Iterable[SourceRecord]:
        """Stream raw records from the source."""


class OutputTransformer(ABC):
    """Transforms source records into the configured output structure."""

    @abstractmethod
    def supports(self, descriptor: OutputDescriptor) -> bool:
        """Return True if this transformer can produce the requested format."""

    @abstractmethod
    def transform(self, records: Iterable[IngestionRecord], descriptor: OutputDescriptor) -> Iterable[OutputPayload]:
        """Convert normalized records into output payloads."""


class Normalizer(ABC):
    """Converts raw source records into normalized ingestion records."""

    @abstractmethod
    def normalize(self, record: SourceRecord) -> IngestionRecord:
        """Transform a raw source record into a normalized ingestion record."""


class PersistenceBackend(ABC):
    """Persists output payloads to a target backend."""

    @abstractmethod
    def supports(self, descriptor: PersistenceDescriptor) -> bool:
        """Return True if this backend supports the descriptor."""

    @abstractmethod
    def persist(
        self,
        payloads: Iterable[OutputPayload],
        descriptor: PersistenceDescriptor,
    ) -> PersistenceResult:
        """Persist the payloads and return a result summary."""


class FailureAggregator(ABC):
    """Collects failure details during a processing run."""

    @abstractmethod
    def record(self, reason: str) -> None:
        """Record a failure reason."""

    @abstractmethod
    def snapshot(self) -> Sequence[str]:
        """Return collected failure reasons."""
