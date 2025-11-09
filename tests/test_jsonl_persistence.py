from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable

from scanner.domain.models import (
    OutputDescriptor,
    OutputFormat,
    OutputPayload,
    PersistenceBackendType,
    PersistenceDescriptor,
)
from scanner.infrastructure.persistence.jsonl import JsonLinesPersistenceBackend


def _make_payloads(count: int) -> Iterable[OutputPayload]:
    descriptor = OutputDescriptor(format=OutputFormat.NORMALIZED_METADATA)
    for index in range(count):
        yield OutputPayload(descriptor=descriptor, content={"index": index})


def test_jsonl_persistence_writes_lines(tmp_path: Path) -> None:
    path = tmp_path / "output.jsonl"
    backend = JsonLinesPersistenceBackend()
    descriptor = PersistenceDescriptor(
        backend=PersistenceBackendType.FILE_SYSTEM,
        configuration={"path": str(path)},
    )

    result = backend.persist(_make_payloads(3), descriptor)

    assert result.stored_count == 3
    lines = path.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 3
    assert json.loads(lines[0]) == {"index": 0}
