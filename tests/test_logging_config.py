from __future__ import annotations

import io
import logging
from pathlib import Path

from scanner.infrastructure.logging_config import (
    LoggingConfig,
    configure_file_logger,
    configure_stdout_and_file_logger,
    configure_stdout_logger,
    get_function_logger,
)


def test_configure_stdout_logger_uses_stream() -> None:
    buffer = io.StringIO()
    logger = configure_stdout_logger("scanner.test.stdout", stream=buffer)
    logger.info("hello world")
    contents = buffer.getvalue()
    assert "hello world" in contents
    assert "scanner.test.stdout" in contents


def test_configure_file_logger_creates_file(tmp_path: Path) -> None:
    log_file = tmp_path / "scanner.log"
    logger = configure_file_logger("scanner.test.file", log_file)
    logger.warning("persisted message")
    assert log_file.exists()
    assert "persisted message" in log_file.read_text()


def test_configure_stdout_and_file_logger_emits_both(tmp_path: Path) -> None:
    buf = io.StringIO()
    log_file = tmp_path / "combined.log"
    logger = configure_stdout_and_file_logger(
        "scanner.test.combined",
        log_file,
        stream=buf,
    )
    logger.debug("debug message")
    logger.info("info message")

    file_contents = log_file.read_text()
    buffer_contents = buf.getvalue()
    assert "info message" in file_contents
    assert "info message" in buffer_contents
    assert "debug message" in buffer_contents


def test_get_function_logger_uses_caller_name() -> None:
    def helper() -> logging.Logger:
        return get_function_logger()

    logger = helper()
    assert logger.name.endswith("helper")


def test_logging_config_builds_custom_formatter() -> None:
    config = LoggingConfig(level=logging.ERROR, fmt="%(levelname)s:%(message)s")
    formatter = config.build_formatter()
    record = logging.LogRecord(
        name="scanner.test",
        level=logging.ERROR,
        pathname=__file__,
        lineno=10,
        msg="boom",
        args=(),
        exc_info=None,
    )
    assert formatter.format(record) == "ERROR:boom"
