"""Scanner configuration loading and validation."""

from __future__ import annotations

import json
import tomllib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Mapping


class ConfigError(Exception):
    """Raised when configuration cannot be loaded or is invalid."""


@dataclass
class SectionConfig:
    adapter: str = "json_file"
    configuration: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AppConfig:
    source: SectionConfig = field(default_factory=SectionConfig)
    persistence: SectionConfig = field(default_factory=lambda: SectionConfig(adapter="jsonl"))


DEFAULT_CONFIG_PATH = Path("/etc/scanner/config.toml")


def load_config(path: Path) -> tuple[AppConfig, bool]:
    """Load configuration from TOML file.

    Returns (config, found). Raises ConfigError on parsing issues.
    """

    if not path.exists():
        return AppConfig(), False

    try:
        with path.open("rb") as handle:
            data = tomllib.load(handle)
    except (OSError, tomllib.TOMLDecodeError) as exc:  # pragma: no cover
        raise ConfigError(f"Failed to read configuration: {exc}") from exc

    return _parse_app_config(data), True


def load_mapping_file(path: Path) -> Dict[str, Any]:
    """Load an arbitrary mapping (TOML or JSON)."""

    if not path.exists():
        raise ConfigError(f"Configuration override file not found: {path}")

    suffix = path.suffix.lower()
    try:
        if suffix in {".toml", ".tml"}:
            with path.open("rb") as handle:
                return tomllib.load(handle)
        with path.open("r", encoding="utf-8") as handle:
            return json.load(handle)
    except (OSError, ValueError, tomllib.TOMLDecodeError) as exc:  # pragma: no cover
        raise ConfigError(f"Failed to read configuration override {path}: {exc}") from exc


def _parse_app_config(data: Mapping[str, Any]) -> AppConfig:
    source_section = SectionConfig()
    persistence_section = SectionConfig(adapter="jsonl")

    if "source" in data and isinstance(data["source"], Mapping):
        source_section = _parse_section(data["source"], default_adapter="json_file")

    if "persistence" in data and isinstance(data["persistence"], Mapping):
        persistence_section = _parse_section(data["persistence"], default_adapter="jsonl")

    return AppConfig(source=source_section, persistence=persistence_section)


def _parse_section(data: Mapping[str, Any], default_adapter: str) -> SectionConfig:
    adapter = str(data.get("adapter", default_adapter))
    configuration_obj = data.get("configuration") or {}
    configuration: Dict[str, Any]
    if isinstance(configuration_obj, Mapping):
        configuration = dict(configuration_obj)
    else:
        raise ConfigError("Configuration section must be a mapping")
    return SectionConfig(adapter=adapter, configuration=configuration)


__all__ = [
    "AppConfig",
    "SectionConfig",
    "ConfigError",
    "DEFAULT_CONFIG_PATH",
    "load_config",
    "load_mapping_file",
]
