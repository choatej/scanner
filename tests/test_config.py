from __future__ import annotations

from pathlib import Path

import pytest

from scanner.config import AppConfig, ConfigError, load_config, load_mapping_file


def write_toml(tmp_path: Path, content: str) -> Path:
    path = tmp_path / "config.toml"
    path.write_text(content, encoding="utf-8")
    return path


def test_load_config_defaults_when_missing(tmp_path: Path) -> None:
    path = tmp_path / "missing.toml"
    config, found = load_config(path)
    assert not found
    assert isinstance(config, AppConfig)
    assert config.source.adapter == "json_file"
    assert config.persistence.adapter == "jsonl"


def test_load_config_parses_sections(tmp_path: Path) -> None:
    path = write_toml(
        tmp_path,
        """
        [source]
        adapter = "html_page"
        [source.configuration]
        start_urls = ["https://example.com"]
        item_selector = ".video"

        [persistence]
        adapter = "postgres"
        [persistence.configuration]
        database_url = "postgresql://scanner:scanner@localhost:5432/scanner"
        """,
    )
    config, found = load_config(path)
    assert found
    assert config.source.adapter == "html_page"
    assert config.source.configuration["start_urls"] == ["https://example.com"]
    assert config.persistence.adapter == "postgres"
    assert "database_url" in config.persistence.configuration


def test_load_mapping_file_supports_json(tmp_path: Path) -> None:
    path = tmp_path / "override.json"
    path.write_text('{"path": "/tmp/output.jsonl"}', encoding="utf-8")
    data = load_mapping_file(path)
    assert data["path"] == "/tmp/output.jsonl"


def test_load_mapping_file_missing(tmp_path: Path) -> None:
    with pytest.raises(ConfigError):
        load_mapping_file(tmp_path / "missing.json")
