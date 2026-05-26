"""Base repository abstractions."""

from __future__ import annotations

from collections.abc import Iterator, Sequence
from contextlib import contextmanager
from typing import Any

from fratelanza.infrastructure.database.connection import SqlServerConnectionFactory


class SqlServerRepository:
    """Base class for repositories backed by SQL Server."""

    def __init__(self, connection_factory: SqlServerConnectionFactory) -> None:
        self._connection_factory = connection_factory

    @contextmanager
    def cursor(self) -> Iterator[Any]:
        """Yield a database cursor inside a managed transaction."""
        with self._connection_factory.connect() as connection:
            yield connection.cursor()

    def fetch_all(self, sql: str, *params: object) -> list[dict[str, object]]:
        """Execute a SELECT statement and return dictionaries."""
        with self.cursor() as cursor:
            cursor.execute(sql, *params)
            columns = [column[0] for column in cursor.description]
            return [dict(zip(columns, row, strict=False)) for row in cursor.fetchall()]

    def fetch_one(self, sql: str, *params: object) -> dict[str, object] | None:
        """Execute a SELECT statement and return one dictionary."""
        with self.cursor() as cursor:
            cursor.execute(sql, *params)
            row = cursor.fetchone()
            if row is None:
                return None
            columns = [column[0] for column in cursor.description]
            return dict(zip(columns, row, strict=False))

    def execute(self, sql: str, *params: object) -> None:
        """Execute a non-query statement."""
        with self.cursor() as cursor:
            cursor.execute(sql, *params)

    def insert_and_get_id(self, sql: str, params: Sequence[object]) -> int:
        """Execute an INSERT followed by ``SELECT SCOPE_IDENTITY()``."""
        with self.cursor() as cursor:
            cursor.execute(f"{sql}; SELECT CAST(SCOPE_IDENTITY() AS int);", *params)
            row = cursor.fetchone()
            return int(row[0])
