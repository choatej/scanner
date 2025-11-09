"""Source adapters available in the infrastructure layer."""

from .html_page import HtmlPageSourceAdapter
from .json_file import JsonFileSourceAdapter

__all__ = [
    "JsonFileSourceAdapter",
    "HtmlPageSourceAdapter",
]
