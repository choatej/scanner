"""Asynchronous processing engine built on top of domain registries."""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Iterable, Sequence
from typing import Callable

from ..domain.engine import (
    ListFailureAggregator,
    NormalizerRegistry,
    OutputRegistry,
    PersistenceRegistry,
    SourceRegistry,
)
from ..domain.interfaces import FailureAggregator, Normalizer, OutputTransformer, PersistenceBackend, SourceAdapter
from ..domain.models import (
    IngestionRecord,
    OutputDescriptor,
    OutputPayload,
    PersistenceDescriptor,
    PersistenceResult,
    ProcessingReport,
    ProcessingRequest,
    SourceDescriptor,
    SourceRecord,
)


class AsyncProcessingEngine:
    """Coordinate ingestion asynchronously using asyncio primitives."""

    def __init__(
        self,
        source_registry: SourceRegistry,
        normalizer_registry: NormalizerRegistry,
        output_registry: OutputRegistry,
        persistence_registry: PersistenceRegistry,
        failure_aggregator_factory: Callable[[], FailureAggregator] | None = None,
        logger: logging.Logger | None = None,
    ) -> None:
        self._source_registry = source_registry
        self._normalizer_registry = normalizer_registry
        self._output_registry = output_registry
        self._persistence_registry = persistence_registry
        self._failure_factory = failure_aggregator_factory or ListFailureAggregator
        self._logger = logger or logging.getLogger(__name__)

    async def process_async(self, request: ProcessingRequest) -> ProcessingReport:
        """Process a single request asynchronously."""

        self._logger.info(
            "Starting async processing request",
            extra={
                "source": request.source.identifier,
                "output_format": request.output.format.name,
                "persistence_target": request.persistence.target,
            },
        )

        adapter = self._source_registry.resolve(request.source)
        normalizer = self._normalizer_registry.resolve(request.source)
        transformer = self._output_registry.resolve(request.output)
        backend = self._persistence_registry.resolve(request.persistence)

        aggregator = self._failure_factory()

        raw_records = await self._read_async(adapter, request.source, aggregator)
        ingestion_records = await self._normalize_async(raw_records, normalizer, aggregator)
        self._logger.debug(
            "Async normalization complete",
            extra={"count": len(ingestion_records)},
        )

        output_payloads = await self._transform_async(
            ingestion_records,
            transformer,
            request.output,
            aggregator,
        )
        persistence_result = await self._persist_async(
            backend,
            output_payloads,
            request.persistence,
        )

        failures = aggregator.snapshot()
        self._logger.info(
            "Async processing completed",
            extra={
                "ingested": len(ingestion_records),
                "persisted": persistence_result.stored_count,
                "failures": len(failures),
            },
        )
        return ProcessingReport(
            ingested=len(ingestion_records),
            persisted=persistence_result.stored_count,
            failures=failures,
            persistence_result=persistence_result,
        )

    async def process_many_async(
        self,
        requests: Sequence[ProcessingRequest],
        concurrency: int | None = None,
    ) -> list[ProcessingReport]:
        """Process multiple requests concurrently with optional concurrency control."""

        if concurrency is not None:
            if concurrency <= 0:
                raise ValueError("concurrency must be a positive integer")
            semaphore = asyncio.Semaphore(concurrency)
        else:
            semaphore = None

        async def _run(req: ProcessingRequest) -> ProcessingReport:
            if semaphore:
                async with semaphore:
                    return await self.process_async(req)
            return await self.process_async(req)

        tasks = [asyncio.create_task(_run(req)) for req in requests]
        return await asyncio.gather(*tasks)

    async def _read_async(
        self,
        adapter: SourceAdapter,
        descriptor: SourceDescriptor,
        aggregator: FailureAggregator,
    ) -> list[SourceRecord]:
        def _read() -> list[SourceRecord]:
            records: list[SourceRecord] = []
            for record in adapter.read(descriptor):
                if isinstance(record, SourceRecord):
                    records.append(record)
                else:
                    aggregator.record("Invalid source record encountered")
            return records

        return await asyncio.to_thread(_read)

    async def _normalize_async(
        self,
        records: Iterable[SourceRecord],
        normalizer: Normalizer,
        aggregator: FailureAggregator,
    ) -> list[IngestionRecord]:
        def _normalize() -> list[IngestionRecord]:
            normalized: list[IngestionRecord] = []
            for record in records:
                try:
                    normalized.append(normalizer.normalize(record))
                except Exception as exc:  # noqa: BLE001
                    aggregator.record(f"Normalization failure: {exc}")
            return normalized

        return await asyncio.to_thread(_normalize)

    async def _transform_async(
        self,
        records: Iterable[IngestionRecord],
        transformer: OutputTransformer,
        descriptor: OutputDescriptor,
        aggregator: FailureAggregator,
    ) -> list[OutputPayload]:
        def _transform() -> list[OutputPayload]:
            try:
                return list(transformer.transform(records, descriptor))
            except Exception as exc:  # noqa: BLE001
                aggregator.record(f"Transformation failure: {exc}")
                self._logger.exception(
                    "Transformation error",
                    extra={"output_format": descriptor.format.name},
                )
                return []

        return await asyncio.to_thread(_transform)

    async def _persist_async(
        self,
        backend: PersistenceBackend,
        payloads: Iterable[OutputPayload],
        descriptor: PersistenceDescriptor,
    ) -> PersistenceResult:
        return await asyncio.to_thread(backend.persist, payloads, descriptor)


async def run_pipeline(
    engine: AsyncProcessingEngine,
    requests: Sequence[ProcessingRequest],
    concurrency: int | None = None,
) -> list[ProcessingReport]:
    """Convenience helper to process multiple requests in parallel."""

    return await engine.process_many_async(requests, concurrency=concurrency)
