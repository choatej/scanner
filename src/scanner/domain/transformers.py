"""Output transformers for the processing engine."""

from __future__ import annotations

from dataclasses import asdict
from typing import Iterable

from .interfaces import OutputTransformer
from .models import IngestionRecord, OutputDescriptor, OutputFormat, OutputPayload


class NormalizedMetadataTransformer(OutputTransformer):
    """Convert ingestion records into normalized metadata payloads."""

    def supports(self, descriptor: OutputDescriptor) -> bool:
        return descriptor.format == OutputFormat.NORMALIZED_METADATA

    def transform(
        self,
        records: Iterable[IngestionRecord],
        descriptor: OutputDescriptor,
    ) -> Iterable[OutputPayload]:
        for record in records:
            yield OutputPayload(descriptor=descriptor, content=asdict(record.metadata))


__all__ = ["NormalizedMetadataTransformer"]
