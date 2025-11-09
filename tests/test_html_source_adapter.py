from __future__ import annotations

from pathlib import Path

from scanner.domain.constants import HTML_PAGE_STRUCTURE
from scanner.domain.models import SourceDescriptor, SourceType
from scanner.infrastructure.sources.html_page import HtmlPageSourceAdapter


def build_descriptor(sample_page: Path, overrides: dict | None = None) -> SourceDescriptor:
    configuration: dict = {
        "start_urls": [str(sample_page)],
        "fetcher": {"type": "local"},
        "parser": {"type": "beautifulsoup", "parser": "html.parser"},
        "item_selector": ".video",
        "fields": {
            "source_site": {"value": "videos.example.com"},
            "title": {"selector": ".title"},
            "description": {"selector": ".description"},
            "length_seconds": {"selector": ".length"},
            "tags": {"selector": ".tags li", "all": True},
            "actors": {"selector": ".actors li", "all": True},
        },
        "extra_fields": {
            "watch_url": {"selector": ".watch", "attr": "href"},
        },
    }
    if overrides:
        configuration.update(overrides)
    return SourceDescriptor(
        identifier="html-local",
        source_type=SourceType.WEB_PAGE,
        structure_id=HTML_PAGE_STRUCTURE,
        configuration=configuration,
    )


def test_html_source_adapter_parses_records() -> None:
    sample_page = Path(__file__).parent / "fixtures" / "sample_page.html"
    descriptor = build_descriptor(sample_page)

    adapter = HtmlPageSourceAdapter()
    records = list(adapter.read(descriptor))

    assert len(records) == 2
    first = records[0]
    assert first.payload["title"] == "Sample Video One"
    assert first.payload["length_seconds"] == 83
    assert first.payload["tags"] == ["example", "demo"]
    assert first.payload["extra"]["watch_url"] == "https://videos.example.com/watch/1"

    second = records[1]
    assert second.payload["actors"] == ["Actor One", "Actor Two"]
    assert second.payload["length_seconds"] == 7510


def test_html_source_adapter_infers_site() -> None:
    sample_page = Path(__file__).parent / "fixtures" / "sample_page.html"
    descriptor = build_descriptor(
        sample_page,
        overrides={
            "start_urls": ["https://videos.example.com/sample"],
            "fetcher": {
                "type": "local",
                "path_map": {"https://videos.example.com/sample": str(sample_page)},
            },
            "fields": {"source_site": {}},
        },
    )

    adapter = HtmlPageSourceAdapter()
    record = next(iter(adapter.read(descriptor)))

    assert record.payload["source_site"] == "videos.example.com"
