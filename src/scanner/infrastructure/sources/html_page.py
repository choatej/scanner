"""Source adapter for HTML pages."""

from __future__ import annotations

import re
from collections.abc import Iterable
from dataclasses import dataclass
from typing import Any, Dict, List, Mapping, Optional

from ...domain.constants import HTML_PAGE_STRUCTURE
from ...domain.interfaces import SourceAdapter
from ...domain.models import SourceDescriptor, SourceRecord, SourceStructure, SourceType
from ..html import BeautifulSoupDom, fetcher_context, infer_site_from_url
from ..html.dom import PageNode


@dataclass
class FieldSpec:
    selector: Optional[str] = None
    attr: str = "text"
    all: bool = False
    value: Any = None
    regex: Optional[str] = None
    default: Any = None


DEFAULT_FIELD_MAP = {
    "title": FieldSpec(selector=".title"),
    "description": FieldSpec(selector=".description"),
    "length_seconds": FieldSpec(selector=".length"),
    "tags": FieldSpec(selector=".tags li", all=True),
    "categories": FieldSpec(selector=".categories li", all=True),
    "actors": FieldSpec(selector=".actors li", all=True),
    "source_site": FieldSpec(),
}


class HtmlPageSourceAdapter(SourceAdapter):
    """Parse HTML pages into SourceRecord payloads using CSS selectors."""

    def supports(self, descriptor: SourceDescriptor) -> bool:
        return descriptor.source_type == SourceType.WEB_PAGE and descriptor.structure_id == HTML_PAGE_STRUCTURE

    def describe_structure(
        self,
        descriptor: SourceDescriptor,
    ) -> SourceStructure:
        return SourceStructure(
            structure_id=HTML_PAGE_STRUCTURE,
            name="HTML Page",
            description="HTML pages parsed using CSS selectors configured per source.",
            metadata={
                "configuration_keys": [
                    "start_urls",
                    "item_selector",
                    "fields",
                    "extra_fields",
                    "site",
                    "fetcher",
                    "parser",
                ]
            },
        )

    def read(self, descriptor: SourceDescriptor) -> Iterable[SourceRecord]:
        config = descriptor.configuration
        start_urls: List[str] = list(config.get("start_urls", []))
        if not start_urls:
            raise ValueError("HtmlPageSourceAdapter requires 'start_urls' in configuration")

        item_selector = config.get("item_selector")
        if not item_selector:
            raise ValueError("HtmlPageSourceAdapter requires 'item_selector' in configuration")

        fetcher_conf = config.get("fetcher") or {}
        parser_conf = config.get("parser") or {}
        parser_name = parser_conf.get("type", "beautifulsoup").lower()
        parser_engine = parser_conf.get("parser", "lxml")

        field_specs = _build_field_specs(config.get("fields") or {})
        extra_specs = _build_field_specs(config.get("extra_fields") or {})
        default_site = config.get("site")

        with fetcher_context(fetcher_conf) as fetcher:
            for url in start_urls:
                html = fetcher.fetch(url)
                if not html:
                    continue

                dom = _build_dom(parser_name, html, parser_engine)
                site = default_site or infer_site_from_url(url)

                for node in dom.select(item_selector):
                    payload = _extract_payload(node, field_specs, extra_specs, site)
                    if not payload.get("title"):
                        continue
                    yield SourceRecord(
                        source=descriptor,
                        payload=payload,
                        context={"source_url": url},
                    )


def _build_dom(parser_name: str, html: str, parser_engine: str) -> BeautifulSoupDom:
    if parser_name != "beautifulsoup":
        raise ValueError(f"Unsupported parser type '{parser_name}'. Only 'beautifulsoup' is supported.")
    return BeautifulSoupDom.from_html(html, parser=parser_engine)


def _build_field_specs(config: Mapping[str, Mapping[str, Any]]) -> Dict[str, FieldSpec]:
    specs: Dict[str, FieldSpec] = {}
    for name, raw in config.items():
        specs[name] = FieldSpec(
            selector=raw.get("selector"),
            attr=raw.get("attr", "text"),
            all=raw.get("all", False),
            value=raw.get("value"),
            regex=raw.get("regex"),
            default=raw.get("default"),
        )
    return specs


def _extract_payload(
    node: PageNode, field_specs: Dict[str, FieldSpec], extra_specs: Dict[str, FieldSpec], site: str | None
) -> Dict[str, Any]:
    payload: Dict[str, Any] = {}
    for field, spec in {**DEFAULT_FIELD_MAP, **field_specs}.items():
        value = _extract_field(node, spec)
        if field == "source_site":
            payload[field] = value or site
        elif field in {"tags", "categories", "actors"}:
            payload[field] = value or []
        elif field == "length_seconds" and value:
            parsed = _parse_length(value)
            if parsed is not None:
                payload[field] = parsed
        else:
            if value is not None:
                payload[field] = value

    if extra_specs:
        extra: Dict[str, Any] = {}
        for field, spec in extra_specs.items():
            value = _extract_field(node, spec)
            if value is not None:
                extra[field] = value
        if extra:
            payload["extra"] = extra

    payload.setdefault("tags", [])
    payload.setdefault("categories", [])
    payload.setdefault("actors", [])
    payload.setdefault("extra", {})
    return payload


def _extract_field(node: PageNode, spec: FieldSpec) -> Any:
    if spec.value is not None:
        return spec.value

    if not spec.selector:
        return spec.default

    if spec.all:
        elements = node.select(spec.selector)
        values = [_get_attribute(el, spec.attr) for el in elements]
        values = [v for v in values if v]
        return values or spec.default

    element = node.select_one(spec.selector)
    if not element:
        return spec.default

    value = _get_attribute(element, spec.attr)
    if value and spec.regex:
        match = re.search(spec.regex, value)
        if match:
            value = match.group(1) if match.groups() else match.group(0)
        else:
            value = spec.default
    return value or spec.default


def _get_attribute(node: PageNode, attr: str) -> Any:
    if attr == "text":
        return node.text.strip()
    value = node.get(attr)
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list):
        return [v.strip() if isinstance(v, str) else v for v in value]
    return value


def _parse_length(value: Any) -> Optional[int]:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return int(value)
    text = str(value).strip()
    if text.isdigit():
        return int(text)
    match = re.match(r"(?:(\d+):)?(\d{1,2}):(\d{2})", text)
    if match:
        hours = int(match.group(1) or 0)
        minutes = int(match.group(2))
        seconds = int(match.group(3))
        return hours * 3600 + minutes * 60 + seconds
    return None


__all__ = ["HtmlPageSourceAdapter"]
