"""Concrete normalizers for processing engine."""

from __future__ import annotations

from typing import Any

from .constants import VIDEO_METADATA_JSON_STRUCTURE
from .interfaces import Normalizer
from .models import IngestionRecord, SourceDescriptor, SourceRecord, VideoMetadata


class VideoMetadataNormalizer(Normalizer):
    """Normalize raw source records into ``VideoMetadata`` instances."""

    def supports(self, descriptor: SourceDescriptor) -> bool:
        return descriptor.structure_id == VIDEO_METADATA_JSON_STRUCTURE

    def normalize(self, record: SourceRecord) -> IngestionRecord:
        metadata = _build_metadata(record)
        return IngestionRecord(metadata=metadata, source_record=record)


def _build_metadata(record: SourceRecord) -> VideoMetadata:
    context_value: Any | None = record.context.get("metadata")
    if isinstance(context_value, VideoMetadata):
        return context_value

    try:
        return VideoMetadata(**record.payload)
    except TypeError as exc:  # noqa: BLE001
        raise ValueError("Record payload is not compatible with VideoMetadata") from exc


__all__ = ["VideoMetadataNormalizer"]
