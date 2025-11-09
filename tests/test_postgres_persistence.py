from __future__ import annotations

import os
from pathlib import Path

import pytest

from scanner.domain.models import (
    OutputDescriptor,
    OutputFormat,
    OutputPayload,
    PersistenceBackendType,
    PersistenceDescriptor,
)
from scanner.infrastructure.persistence.postgres import (
    PostgresPersistenceBackend,
    ensure_schema,
    reset_schema,
)

DATABASE_URL_ENV = "TEST_PG_DATABASE_URL"


@pytest.fixture(scope="module")
def database_url() -> str:
    url = os.getenv(DATABASE_URL_ENV)
    if not url:
        pytest.skip(f"Set {DATABASE_URL_ENV} to run PostgreSQL persistence tests.")
    reset_schema(url)
    return url


def test_postgres_persistence_inserts_records(database_url: str, tmp_path: Path) -> None:
    backend = PostgresPersistenceBackend()
    descriptor = PersistenceDescriptor(
        backend=PersistenceBackendType.DATABASE,
        configuration={"database_url": database_url},
    )

    payloads = [
        OutputPayload(
            descriptor=OutputDescriptor(format=OutputFormat.NORMALIZED_METADATA),
            content={
                "title": "Persistence Test",
                "description": "Stored via Postgres backend",
                "length_seconds": 42,
                "tags": ["postgres"],
                "categories": ["tests"],
                "actors": ["Tester"],
                "source_site": "postgres.example",
                "extra": {"quality": "4k"},
            },
        )
    ]

    result = backend.persist(payloads, descriptor)

    assert result.stored_count == 1

    # Verify inserted row count
    from sqlalchemy import text

    engine = backend._get_engine(database_url)
    with engine.connect() as conn:
        count = conn.execute(text("SELECT COUNT(*) FROM videos")).scalar_one()
        assert count >= 1
