"""Helpers for retrieving HTML content."""

from __future__ import annotations

import contextlib
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterator, Optional, Protocol
from urllib.parse import urlparse

import requests

try:
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options as ChromeOptions
    from selenium.webdriver.chrome.service import Service as ChromeService
    from selenium.webdriver.firefox.options import Options as FirefoxOptions
    from selenium.webdriver.firefox.service import Service as FirefoxService
    from webdriver_manager.chrome import ChromeDriverManager
    from webdriver_manager.firefox import GeckoDriverManager

    _SELENIUM_AVAILABLE = True
except ImportError:  # pragma: no cover - selenium optional
    _SELENIUM_AVAILABLE = False


class HtmlFetcher(Protocol):
    def fetch(self, url: str) -> str | None: ...

    def close(self) -> None: ...


@dataclass
class FetcherConfig:
    type: str = "requests"
    headers: Optional[Dict[str, str]] = None
    timeout: float = 30.0
    max_retries: int = 2
    backoff_seconds: float = 0.5
    wait_seconds: float = 0.0  # selenium only
    driver: str = "chrome"  # selenium only
    path_map: Optional[Dict[str, str]] = None


class RequestsFetcher(HtmlFetcher):
    def __init__(self, config: FetcherConfig):
        self._session = requests.Session()
        headers = {"User-Agent": "ScannerBot/0.1 (+https://example.com)"}
        if config.headers:
            headers.update(config.headers)
        self._session.headers.update(headers)
        self._timeout = config.timeout
        self._max_retries = config.max_retries
        self._backoff_seconds = config.backoff_seconds

    def fetch(self, url: str) -> str | None:
        delay = self._backoff_seconds
        for attempt in range(self._max_retries + 1):
            try:
                response = self._session.get(url, timeout=self._timeout)
                if response.ok:
                    return response.text
            except requests.RequestException:
                pass
            if attempt < self._max_retries:
                time.sleep(delay)
                delay *= 2
        return None

    def close(self) -> None:
        self._session.close()


class LocalFileFetcher(HtmlFetcher):
    def __init__(self, path_map: Optional[Dict[str, str]] = None) -> None:
        self._cache: dict[str, str] = {}
        self._path_map = path_map or {}

    def fetch(self, url: str) -> str | None:
        mapped = self._path_map.get(url, url)
        path = Path(mapped)
        if not path.exists():
            return None
        if mapped not in self._cache:
            self._cache[mapped] = path.read_text(encoding="utf-8")
        return self._cache[mapped]

    def close(self) -> None:
        self._cache.clear()


class SeleniumFetcher(HtmlFetcher):  # pragma: no cover - requires selenium setup
    def __init__(self, config: FetcherConfig):
        if not _SELENIUM_AVAILABLE:
            raise RuntimeError("selenium extra not installed. Install with scanner[selenium]")

        self._wait_seconds = config.wait_seconds
        driver_name = config.driver.lower()
        self._driver: Any
        if driver_name == "firefox":
            firefox_options = FirefoxOptions()
            firefox_options.add_argument("--headless")
            firefox_service = FirefoxService(executable_path=GeckoDriverManager().install())
            self._driver = webdriver.Firefox(service=firefox_service, options=firefox_options)
        else:
            chrome_options = ChromeOptions()
            chrome_options.add_argument("--headless=new")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_service = ChromeService(executable_path=ChromeDriverManager().install())
            self._driver = webdriver.Chrome(service=chrome_service, options=chrome_options)

    def fetch(self, url: str) -> str | None:
        self._driver.get(url)
        if self._wait_seconds:
            time.sleep(self._wait_seconds)
        return self._driver.page_source

    def close(self) -> None:
        self._driver.quit()


def build_fetcher(config: Optional[Dict[str, object]] = None) -> HtmlFetcher:
    cfg = _parse_fetcher_config(config or {})
    fetcher_type = cfg.type.lower()

    if fetcher_type == "local":
        return LocalFileFetcher(cfg.path_map)
    if fetcher_type == "selenium":
        return SeleniumFetcher(cfg)
    return RequestsFetcher(cfg)


@contextlib.contextmanager
def fetcher_context(config: Optional[Dict[str, object]] = None) -> Iterator[HtmlFetcher]:
    fetcher = build_fetcher(config)
    try:
        yield fetcher
    finally:
        fetcher.close()


def infer_site_from_url(url: str | None) -> str | None:
    if not url:
        return None
    parsed = urlparse(url)
    return parsed.netloc or None


def _parse_fetcher_config(config: Dict[str, object]) -> FetcherConfig:
    headers = config.get("headers")
    header_map: Optional[Dict[str, str]] = None
    if isinstance(headers, dict):
        header_map = {str(k): str(v) for k, v in headers.items()}

    return FetcherConfig(
        type=str(config.get("type", "requests")),
        headers=header_map,
        timeout=_coerce_float(config.get("timeout"), 30.0),
        max_retries=_coerce_int(config.get("max_retries"), 2),
        backoff_seconds=_coerce_float(config.get("backoff_seconds"), 0.5),
        wait_seconds=_coerce_float(config.get("wait_seconds"), 0.0),
        driver=str(config.get("driver", "chrome")),
        path_map=_coerce_str_dict(config.get("path_map")),
    )


def _coerce_float(value: object, default: float) -> float:
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value)
        except ValueError:
            return default
    return default


def _coerce_int(value: object, default: int) -> int:
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    if isinstance(value, str):
        try:
            return int(value)
        except ValueError:
            return default
    return default


def _coerce_str_dict(value: object) -> Optional[Dict[str, str]]:
    if isinstance(value, dict):
        return {str(k): str(v) for k, v in value.items()}
    return None
