"""Base repository abstractions."""

from __future__ import annotations

from collections.abc import Iterator
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
