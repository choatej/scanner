"""HTML processing helpers (fetchers, DOM adapters)."""

from .dom import BeautifulSoupDom
from .fetchers import (
    FetcherConfig,
    HtmlFetcher,
    LocalFileFetcher,
    RequestsFetcher,
    SeleniumFetcher,
    build_fetcher,
    fetcher_context,
    infer_site_from_url,
)

__all__ = [
    "FetcherConfig",
    "HtmlFetcher",
    "LocalFileFetcher",
    "RequestsFetcher",
    "SeleniumFetcher",
    "build_fetcher",
    "fetcher_context",
    "infer_site_from_url",
    "BeautifulSoupDom",
]
