from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from scanner.infrastructure.json_codec import (
    DataclassJSONEncoder,
    decode_dataclass,
    dump_dataclass_list,
    load_dataclass_list,
)


@dataclass
class Example:
    name: str
    value: int


def test_decode_dataclass_from_mapping() -> None:
    obj = decode_dataclass({"name": "item", "value": 3, "ignored": True}, Example)
    assert obj == Example(name="item", value=3)


def test_dump_and_load_round_trip(tmp_path: Path) -> None:
    path = tmp_path / "examples.json"
    dump_dataclass_list(path, [Example("one", 1), Example("two", 2)])
    loaded = load_dataclass_list(path, Example)
    assert loaded == [Example("one", 1), Example("two", 2)]


def test_encoder_serializes_dataclass() -> None:
    encoded = DataclassJSONEncoder().encode(Example("foo", 7))
    assert '"name": "foo"' in encoded
    assert '"value": 7' in encoded
