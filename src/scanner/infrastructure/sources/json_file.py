"""Source adapter for reading video metadata from local JSON files."""

from __future__ import annotations

from dataclasses import asdict
from pathlib import Path
from typing import Iterable

from ...domain.constants import VIDEO_METADATA_JSON_STRUCTURE
from ...domain.interfaces import SourceAdapter
from ...domain.models import SourceDescriptor, SourceRecord, SourceStructure, SourceType, VideoMetadata
from ..json_codec import load_dataclass_list


class JsonFileSourceAdapter(SourceAdapter):
    """Stream ``VideoMetadata`` records from a structured JSON file."""

    CONFIG_PATH_KEY = "path"

    def supports(self, descriptor: SourceDescriptor) -> bool:
        return descriptor.source_type == SourceType.FILE and descriptor.structure_id == VIDEO_METADATA_JSON_STRUCTURE

    def describe_structure(self, descriptor: SourceDescriptor) -> SourceStructure:
        return SourceStructure(
            structure_id=VIDEO_METADATA_JSON_STRUCTURE,
            name="Video metadata JSON file",
            description="Each entry is a JSON object compatible with VideoMetadata dataclass fields.",
            metadata={"config_keys": [self.CONFIG_PATH_KEY]},
        )

    def read(self, descriptor: SourceDescriptor) -> Iterable[SourceRecord]:
        file_path = descriptor.get(self.CONFIG_PATH_KEY)
        if not file_path:
            raise ValueError(
                f"Source descriptor {descriptor.identifier!r} missing '{self.CONFIG_PATH_KEY}' configuration"
            )

        path = Path(file_path).expanduser().resolve()
        records = load_dataclass_list(path, VideoMetadata)
        for metadata in records:
            yield SourceRecord(
                source=descriptor,
                payload=asdict(metadata),
                context={"metadata": metadata},
            )


__all__ = ["JsonFileSourceAdapter"]
