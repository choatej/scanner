"""Concrete normalizers for converting source records into domain models."""

from __future__ import annotations

from typing import Any

from .constants import VIDEO_METADATA_JSON_STRUCTURE
from .interfaces import Normalizer
from .models import IngestionRecord, SourceDescriptor, SourceRecord, VideoMetadata


class VideoMetadataNormalizer(Normalizer):
    """Normalize raw records representing ``VideoMetadata``."""

    def supports(self, descriptor: SourceDescriptor) -> bool:
        return descriptor.structure_id == VIDEO_METADATA_JSON_STRUCTURE

    def normalize(self, record: SourceRecord) -> IngestionRecord:
        metadata = _extract_metadata(record)
        return IngestionRecord(metadata=metadata, source_record=record)


def _extract_metadata(record: SourceRecord) -> VideoMetadata:
    context_value: Any | None = record.context.get("metadata")
    if isinstance(context_value, VideoMetadata):
        return context_value

    try:
        return VideoMetadata(**record.payload)
    except TypeError as exc:
        raise ValueError("Record payload is not compatible with VideoMetadata") from exc


__all__ = ["VideoMetadataNormalizer"]
