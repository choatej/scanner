"""Infrastructure and integration components."""

from .json_codec import (
    DataclassJSONEncoder,
    decode_dataclass,
    dump_dataclass_list,
    load_dataclass_list,
)
from .logging_config import (
    LoggingConfig,
    configure_file_logger,
    configure_stdout_and_file_logger,
    configure_stdout_logger,
    get_function_logger,
)
from .persistence.jsonl import JsonLinesPersistenceBackend
from .persistence.postgres import (
    PostgresPersistenceBackend,
    ensure_schema as ensure_pg_schema,
    reset_schema as reset_pg_schema,
)
from .sources.html_page import HtmlPageSourceAdapter
from .sources.json_file import JsonFileSourceAdapter

__all__ = [
    "LoggingConfig",
    "configure_stdout_logger",
    "configure_file_logger",
    "configure_stdout_and_file_logger",
    "get_function_logger",
    "DataclassJSONEncoder",
    "decode_dataclass",
    "dump_dataclass_list",
    "load_dataclass_list",
    "JsonFileSourceAdapter",
    "HtmlPageSourceAdapter",
    "JsonLinesPersistenceBackend",
    "PostgresPersistenceBackend",
    "ensure_pg_schema",
    "reset_pg_schema",
]
