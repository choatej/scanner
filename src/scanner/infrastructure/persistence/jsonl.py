"""Persistence backend for writing output payloads to JSON Lines files."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable

from ...domain.interfaces import PersistenceBackend
from ...domain.models import OutputPayload, PersistenceBackendType, PersistenceDescriptor, PersistenceResult


class JsonLinesPersistenceBackend(PersistenceBackend):
    """Store output payloads as JSON lines on the local filesystem."""

    CONFIG_PATH_KEY = "path"

    def supports(self, descriptor: PersistenceDescriptor) -> bool:
        if descriptor.backend != PersistenceBackendType.FILE_SYSTEM:
            return False
        path = self._resolve_path(descriptor)
        return path is not None

    def persist(
        self,
        payloads: Iterable[OutputPayload],
        descriptor: PersistenceDescriptor,
    ) -> PersistenceResult:
        path = self._resolve_path(descriptor)
        if path is None:
            raise ValueError("JsonLinesPersistenceBackend requires a 'path' in descriptor configuration or target")

        path.parent.mkdir(parents=True, exist_ok=True)
        stored = 0
        with path.open("a", encoding="utf-8") as handle:
            for payload in payloads:
                handle.write(json.dumps(payload.content))
                handle.write("\n")
                stored += 1

        return PersistenceResult(stored_count=stored)

    def _resolve_path(self, descriptor: PersistenceDescriptor) -> Path | None:
        configured = descriptor.get(self.CONFIG_PATH_KEY)
        target = descriptor.target
        value = configured or target
        if value is None:
            return None
        return Path(value).expanduser().resolve()


__all__ = ["JsonLinesPersistenceBackend"]
