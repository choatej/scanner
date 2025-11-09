"""Utilities for encoding and decoding dataclasses to and from JSON."""

from __future__ import annotations

import json
from dataclasses import asdict, fields, is_dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence, Type, TypeVar

T = TypeVar("T")


class DataclassJSONEncoder(json.JSONEncoder):
    """JSON encoder that can serialize dataclass instances."""

    def default(self, obj: Any) -> Any:  # noqa: D401
        if is_dataclass(obj) and not isinstance(obj, type):
            return asdict(obj)
        return super().default(obj)


def decode_dataclass(data: Mapping[str, Any], cls: Type[T]) -> T:
    """Instantiate ``cls`` using values from ``data``."""

    if not isinstance(data, Mapping):
        raise TypeError(f"Expected mapping to decode {cls.__name__}, got {type(data).__name__}")
    if not is_dataclass(cls):
        raise TypeError(f"{cls!r} is not a dataclass type")

    valid_fields = {field.name for field in fields(cls)}
    init_kwargs = {name: data[name] for name in valid_fields if name in data}
    return cls(**init_kwargs)


def load_dataclass_list(path: Path, cls: Type[T]) -> list[T]:
    """Read a list of dataclasses from ``path``."""

    raw = _read_json(path)
    if not isinstance(raw, list):
        raise ValueError(f"Expected list of items in {path}, found {type(raw).__name__}")
    return [decode_dataclass(item, cls) for item in raw]


def dump_dataclass_list(path: Path, items: Sequence[T]) -> None:
    """Write a list of dataclasses to ``path``."""

    serializable: list[Any] = []
    for item in items:
        if is_dataclass(item) and not isinstance(item, type):
            serializable.append(asdict(item))
        else:
            serializable.append(item)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(serializable, indent=2, cls=DataclassJSONEncoder), encoding="utf-8")


def _read_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


__all__ = [
    "DataclassJSONEncoder",
    "decode_dataclass",
    "dump_dataclass_list",
    "load_dataclass_list",
]
