"""DOM adapter abstractions using BeautifulSoup."""

from __future__ import annotations

from typing import Any, Iterable, Mapping, Optional, Protocol

from bs4 import BeautifulSoup, Tag


class PageNode(Protocol):
    def select(self, css: str) -> list["PageNode"]: ...

    def select_one(self, css: str) -> Optional["PageNode"]: ...

    def find(
        self, name: Optional[str] = None, *, class_: Optional[str] = None, **attrs: Any
    ) -> Optional["PageNode"]: ...

    def find_all(
        self, name: Optional[str] = None, *, class_: Optional[str] = None, **attrs: Any
    ) -> list["PageNode"]: ...

    @property
    def text(self) -> str: ...

    def get(self, attr: str, default: Any = None) -> Any: ...

    @property
    def attrs(self) -> Mapping[str, Any]: ...

    @property
    def parent(self) -> Optional["PageNode"]: ...

    @property
    def children(self) -> Iterable["PageNode"]: ...

    def itertext(self) -> Iterable[str]: ...


class _SoupNode(PageNode):
    __slots__ = ("_node",)

    def __init__(self, node: Tag | BeautifulSoup | str):
        if isinstance(node, str):
            node = BeautifulSoup(node, "html.parser")
        self._node = node

    def select(self, css: str) -> list["PageNode"]:
        return [_SoupNode(x) for x in self._node.select(css)]

    def select_one(self, css: str) -> "PageNode | None":
        node = self._node.select_one(css)
        return _SoupNode(node) if node is not None else None

    def find(self, name: Optional[str] = None, *, class_: Optional[str] = None, **attrs: Any) -> Optional["PageNode"]:
        node = self._node.find(name, class_=class_, **attrs)  # type: ignore[arg-type]
        return _SoupNode(node) if node is not None else None

    def find_all(self, name: Optional[str] = None, *, class_: Optional[str] = None, **attrs: Any) -> list["PageNode"]:
        return [_SoupNode(node) for node in self._node.find_all(name, class_=class_, **attrs)]  # type: ignore[arg-type]

    @property
    def text(self) -> str:
        return getattr(self._node, "get_text", lambda: str(self._node))()

    def get(self, attr: str, default: Any = None) -> Any:
        return getattr(self._node, "get", lambda *_: default)(attr, default)

    @property
    def attrs(self) -> Mapping[str, Any]:
        return getattr(self._node, "attrs", {})

    @property
    def parent(self) -> Optional["PageNode"]:
        parent = getattr(self._node, "parent", None)
        if isinstance(parent, (Tag, BeautifulSoup)):
            return _SoupNode(parent)
        return None

    @property
    def children(self) -> Iterable["PageNode"]:
        for child in getattr(self._node, "children", []):
            if isinstance(child, (Tag, BeautifulSoup)):
                yield _SoupNode(child)

    def itertext(self) -> Iterable[str]:
        yield from getattr(self._node, "stripped_strings", [])


class BeautifulSoupDom:
    """Wrapper around BeautifulSoup providing a common API."""

    __slots__ = ("_soup",)

    def __init__(self, soup: BeautifulSoup | str, parser: str = "lxml"):
        if isinstance(soup, str):
            soup = BeautifulSoup(soup, parser)
        self._soup = soup

    @classmethod
    def from_html(cls, html: str, parser: str = "lxml") -> "BeautifulSoupDom":
        return cls(html, parser=parser)

    def _root(self) -> _SoupNode:
        return _SoupNode(self._soup)

    def select(self, css: str) -> list[PageNode]:
        return self._root().select(css)

    def select_one(self, css: str) -> PageNode | None:
        return self._root().select_one(css)

    def find(self, name: Optional[str] = None, *, class_: Optional[str] = None, **attrs: Any) -> PageNode | None:
        return self._root().find(name, class_=class_, **attrs)

    def find_all(self, name: Optional[str] = None, *, class_: Optional[str] = None, **attrs: Any) -> list[PageNode]:
        return self._root().find_all(name, class_=class_, **attrs)
