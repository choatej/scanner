"""Logging configuration helpers inspired by legacy projects."""

from __future__ import annotations

import inspect
import logging
import sys
from dataclasses import dataclass
from logging import Formatter, Handler, Logger, StreamHandler
from pathlib import Path
from typing import Iterable, Optional, TextIO

DEFAULT_FORMAT = "%(asctime)s %(levelname)s [%(name)s] %(message)s"
DEFAULT_DATE_FORMAT = "%Y-%m-%dT%H:%M:%S"


@dataclass(frozen=True)
class LoggingConfig:
    """Runtime configuration for logger creation."""

    level: int = logging.INFO
    fmt: str = DEFAULT_FORMAT
    datefmt: str = DEFAULT_DATE_FORMAT

    def build_formatter(self) -> Formatter:
        return logging.Formatter(self.fmt, self.datefmt)


def configure_stdout_logger(
    logger_name: str = "",
    config: LoggingConfig | None = None,
    *,
    stream: TextIO | None = None,
    clear_handlers: bool = True,
) -> Logger:
    """Configure a logger that emits structured messages to stdout."""

    config = config or LoggingConfig()
    stream = stream or sys.stdout
    logger = _get_named_logger(logger_name, clear_handlers)
    handler = _create_stream_handler(stream, config)
    _apply_configuration(logger, config, [handler])
    return logger


def configure_file_logger(
    logger_name: str,
    file_path: str | Path,
    config: LoggingConfig | None = None,
    *,
    clear_handlers: bool = True,
) -> Logger:
    """Configure a logger that writes to the given file."""

    config = config or LoggingConfig()
    logger = _get_named_logger(logger_name, clear_handlers)
    handler = _create_file_handler(file_path, config)
    _apply_configuration(logger, config, [handler])
    return logger


def configure_stdout_and_file_logger(
    logger_name: str,
    file_path: str | Path,
    config: LoggingConfig | None = None,
    *,
    stream: TextIO | None = None,
    clear_handlers: bool = True,
) -> Logger:
    """Configure a logger that emits to both stdout and file destinations."""

    config = config or LoggingConfig(level=logging.DEBUG)
    stream = stream or sys.stdout
    logger = _get_named_logger(logger_name, clear_handlers)
    handlers = [
        _create_stream_handler(stream, config, level=config.level),
        _create_file_handler(file_path, config),
    ]
    _apply_configuration(logger, config, handlers)
    logger.debug("Logger configured for stdout and file output", extra={"file_path": str(file_path)})
    return logger


def get_function_logger() -> Logger:
    """Return a logger named for the calling function."""

    frame = inspect.currentframe()
    if frame is None:
        return logging.getLogger(__name__)
    try:
        caller = frame.f_back
        if caller is None:
            return logging.getLogger(__name__)
        module = caller.f_globals.get("__name__", "__unknown__")
        function_name = caller.f_code.co_name
        return logging.getLogger(f"{module}.{function_name}")
    finally:
        del frame


def _get_named_logger(name: str, clear_handlers: bool) -> Logger:
    logger = logging.getLogger(name)
    if clear_handlers:
        logger.handlers.clear()
    logger.propagate = False
    return logger


def _apply_configuration(logger: Logger, config: LoggingConfig, handlers: Iterable[Handler]) -> None:
    logger.setLevel(config.level)
    for handler in handlers:
        logger.addHandler(handler)


def _create_stream_handler(
    stream: TextIO,
    config: LoggingConfig,
    *,
    level: Optional[int] = None,
) -> StreamHandler:
    handler = logging.StreamHandler(stream)
    handler.setLevel(level or config.level)
    handler.setFormatter(config.build_formatter())
    return handler


def _create_file_handler(file_path: str | Path, config: LoggingConfig) -> Handler:
    path = Path(file_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    handler = logging.FileHandler(path)
    handler.setLevel(config.level)
    handler.setFormatter(config.build_formatter())
    return handler
