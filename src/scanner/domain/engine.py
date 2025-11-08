"""Processing engine orchestrating source ingestion and persistence."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Sequence

from .interfaces import (
    FailureAggregator,
    Normalizer,
    OutputTransformer,
    PersistenceBackend,
    SourceAdapter,
)
from .models import (
    IngestionRecord,
    OutputDescriptor,
    OutputPayload,
    PersistenceDescriptor,
    ProcessingReport,
    ProcessingRequest,
    SourceDescriptor,
    SourceRecord,
)


class RegistryError(RuntimeError):
    """Raised when a registry cannot provide a required component."""


@dataclass(frozen=True)
class SourceRegistry:
    """Stores and resolves source adapters."""

    adapters: Sequence[SourceAdapter]

    def resolve(self, descriptor: SourceDescriptor) -> SourceAdapter:
        for adapter in self.adapters:
            if adapter.supports(descriptor):
                return adapter
        message = f"No source adapter found for descriptor {descriptor!r}"
        raise RegistryError(message)


@dataclass(frozen=True)
class NormalizerRegistry:
    """Stores and resolves normalizers for converting raw records."""

    normalizers: Sequence[Normalizer]

    def resolve(self, descriptor: SourceDescriptor) -> Normalizer:
        for normalizer in self.normalizers:
            # Normalizers may choose to inspect the descriptor for routing
            normalized = getattr(normalizer, "supports", None)
            if callable(normalized) and normalized(descriptor):
                return normalizer
            if normalized is None:
                return normalizer
        message = f"No normalizer available for descriptor {descriptor!r}"
        raise RegistryError(message)


@dataclass(frozen=True)
class OutputRegistry:
    """Stores and resolves output transformers."""

    transformers: Sequence[OutputTransformer]

    def resolve(self, descriptor: OutputDescriptor) -> OutputTransformer:
        for transformer in self.transformers:
            if transformer.supports(descriptor):
                return transformer
        message = f"No output transformer found for descriptor {descriptor!r}"
        raise RegistryError(message)


@dataclass(frozen=True)
class PersistenceRegistry:
    """Stores and resolves persistence backends."""

    backends: Sequence[PersistenceBackend]

    def resolve(self, descriptor: PersistenceDescriptor) -> PersistenceBackend:
        for backend in self.backends:
            if backend.supports(descriptor):
                return backend
        message = f"No persistence backend found for descriptor {descriptor!r}"
        raise RegistryError(message)


class ListFailureAggregator(FailureAggregator):
    """Simple failure aggregator storing reasons in memory."""

    def __init__(self) -> None:
        self._reasons: list[str] = []

    def record(self, reason: str) -> None:
        self._reasons.append(reason)

    def snapshot(self) -> Sequence[str]:
        return tuple(self._reasons)


class ProcessingEngine:
    """Coordinate ingestion through normalization and persistence."""

    def __init__(
        self,
        source_registry: SourceRegistry,
        normalizer_registry: NormalizerRegistry,
        output_registry: OutputRegistry,
        persistence_registry: PersistenceRegistry,
        failure_aggregator: FailureAggregator | None = None,
    ) -> None:
        self._source_registry = source_registry
        self._normalizer_registry = normalizer_registry
        self._output_registry = output_registry
        self._persistence_registry = persistence_registry
        self._failure_aggregator = failure_aggregator or ListFailureAggregator()

    def process(self, request: ProcessingRequest) -> ProcessingReport:
        adapter = self._source_registry.resolve(request.source)
        normalizer = self._normalizer_registry.resolve(request.source)
        transformer = self._output_registry.resolve(request.output)
        backend = self._persistence_registry.resolve(request.persistence)

        raw_records = list(self._safe_read(adapter, request.source))
        ingestion_records = list(self._normalize(raw_records, normalizer))
        output_payloads = self._transform(
            ingestion_records,
            transformer,
            request.output,
        )
        persistence_result = backend.persist(
            output_payloads,
            request.persistence,
        )

        failures = self._failure_aggregator.snapshot()
        return ProcessingReport(
            ingested=len(ingestion_records),
            persisted=persistence_result.stored_count,
            failures=failures,
            persistence_result=persistence_result,
        )

    def _safe_read(self, adapter: SourceAdapter, descriptor: SourceDescriptor) -> Iterable[SourceRecord]:
        for record in adapter.read(descriptor):
            if isinstance(record, SourceRecord):
                yield record
            else:
                self._failure_aggregator.record(
                    "Invalid source record encountered",
                )

    def _normalize(self, records: Iterable[SourceRecord], normalizer: Normalizer) -> Iterable[IngestionRecord]:
        for record in records:
            try:
                yield normalizer.normalize(record)
            except Exception as exc:  # noqa: BLE001
                self._failure_aggregator.record(f"Normalization failure: {exc}")

    def _transform(
        self,
        records: Iterable[IngestionRecord],
        transformer: OutputTransformer,
        descriptor: OutputDescriptor,
    ) -> list[OutputPayload]:
        try:
            return list(
                transformer.transform(
                    records,
                    descriptor,
                )
            )
        except Exception as exc:  # noqa: BLE001
            self._failure_aggregator.record(
                f"Transformation failure: {exc}",
            )
            return []
