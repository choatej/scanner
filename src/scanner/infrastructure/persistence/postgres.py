"""PostgreSQL persistence backend for normalized metadata."""

from __future__ import annotations

from typing import Iterable

from sqlalchemy import Column, ForeignKey, Integer, MetaData, String, Table, create_engine
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.engine import Connection, Engine
from sqlalchemy.sql import Insert, Select, select

from ...domain.interfaces import PersistenceBackend
from ...domain.models import (
    OutputPayload,
    PersistenceBackendType,
    PersistenceDescriptor,
    PersistenceResult,
    VideoMetadata,
)

_metadata = MetaData()

sites_table = Table(
    "sites",
    _metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("name", String(255), unique=True, nullable=False),
)

videos_table = Table(
    "videos",
    _metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("site_id", Integer, ForeignKey("sites.id", ondelete="CASCADE"), nullable=False),
    Column("title", String(1024), nullable=False),
    Column("description", String, nullable=True),
    Column("length_seconds", Integer, nullable=True),
    Column("tags", ARRAY(String), nullable=False, server_default="{}"),
    Column("categories", ARRAY(String), nullable=False, server_default="{}"),
    Column("actors", ARRAY(String), nullable=False, server_default="{}"),
    Column("extra", JSONB, nullable=False, server_default="{}"),
)


class PostgresPersistenceBackend(PersistenceBackend):
    """Persist normalized metadata to PostgreSQL."""

    CONFIG_URL_KEY = "database_url"

    def supports(self, descriptor: PersistenceDescriptor) -> bool:
        url = self._resolve_url(descriptor)
        return descriptor.backend == PersistenceBackendType.DATABASE and bool(url)

    def persist(
        self,
        payloads: Iterable[OutputPayload],
        descriptor: PersistenceDescriptor,
    ) -> PersistenceResult:
        url = self._resolve_url(descriptor)
        if not url:
            raise ValueError("PostgresPersistenceBackend requires a database URL in configuration or target")

        engine = _get_engine(url)
        ensure_schema(engine)

        stored = 0
        with engine.begin() as conn:
            for payload in payloads:
                metadata = _coerce_metadata(payload)
                site_id = _upsert_site(conn, metadata.source_site or "unknown")
                conn.execute(
                    videos_table.insert().values(
                        site_id=site_id,
                        title=metadata.title,
                        description=metadata.description,
                        length_seconds=metadata.length_seconds,
                        tags=metadata.tags,
                        categories=metadata.categories,
                        actors=metadata.actors,
                        extra=metadata.extra,
                    )
                )
                stored += 1

        return PersistenceResult(stored_count=stored)

    def _resolve_url(self, descriptor: PersistenceDescriptor) -> str | None:
        configured = descriptor.get(self.CONFIG_URL_KEY)
        target = descriptor.target
        return configured or target


def ensure_schema(engine: Engine) -> None:
    """Create tables if they do not exist."""

    _metadata.create_all(engine, checkfirst=True)


def reset_schema(url: str) -> None:
    """Utility for tests to drop and recreate schema."""

    engine = _get_engine(url)
    _metadata.drop_all(engine, checkfirst=True)
    ensure_schema(engine)


_ENGINE_CACHE: dict[str, Engine] = {}


def _get_engine(url: str) -> Engine:
    if url not in _ENGINE_CACHE:
        _ENGINE_CACHE[url] = create_engine(url, pool_pre_ping=True)
    return _ENGINE_CACHE[url]


def _upsert_site(conn: Connection, name: str) -> int:
    stmt: Select = select(sites_table.c.id).where(sites_table.c.name == name)
    result = conn.execute(stmt).scalar_one_or_none()
    if result is not None:
        return result

    insert_stmt: Insert = sites_table.insert().values(name=name).returning(sites_table.c.id)
    return conn.execute(insert_stmt).scalar_one()


def _coerce_metadata(payload: OutputPayload) -> VideoMetadata:
    if isinstance(payload.content, VideoMetadata):
        return payload.content
    if isinstance(payload.content, dict):
        return VideoMetadata(**payload.content)
    raise TypeError("Unsupported payload type for PostgreSQL persistence")


__all__ = ["PostgresPersistenceBackend", "ensure_schema", "reset_schema"]
