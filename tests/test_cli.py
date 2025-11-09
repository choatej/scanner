from __future__ import annotations

from pathlib import Path

from pytest import MonkeyPatch

from scanner.api.cli import main as cli_main
from scanner.domain.models import VideoMetadata
from scanner.infrastructure.json_codec import dump_dataclass_list


def create_metadata_file(path: Path) -> None:
    dump_dataclass_list(
        path,
        [
            VideoMetadata(
                title="CLI Video",
                description="CLI description",
                length_seconds=30,
                tags=["cli"],
                categories=[],
                actors=[],
                source_site="cli.example",
                extra={},
            )
        ],
    )


def test_cli_ingests_metadata(tmp_path: Path, monkeypatch: MonkeyPatch) -> None:
    metadata = tmp_path / "input.json"
    output = tmp_path / "output.jsonl"
    create_metadata_file(metadata)

    exit_code = cli_main(
        [
            "--metadata-file",
            str(metadata),
            "--output-file",
            str(output),
            "--log-level",
            "ERROR",
        ]
    )

    assert exit_code == 0
    assert output.exists()
    contents = output.read_text(encoding="utf-8").strip().splitlines()
    assert contents
    assert "CLI Video" in contents[0]


def test_cli_requires_output_for_json(tmp_path: Path) -> None:
    metadata = tmp_path / "input.json"
    create_metadata_file(metadata)

    exit_code = cli_main(
        [
            "--metadata-file",
            str(metadata),
            "--log-level",
            "ERROR",
        ]
    )

    assert exit_code == 1
