"""SQL Server connection factory."""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
import logging
from typing import Any

from fratelanza.core.config import DatabaseSettings
from fratelanza.core.exceptions import DatabaseConnectionError

logger = logging.getLogger(__name__)


class SqlServerConnectionFactory:
    """Create short-lived pyodbc connections for repositories."""

    def __init__(self, settings: DatabaseSettings) -> None:
        self._settings = settings

    @contextmanager
    def connect(self, *, database: str | None = None, autocommit: bool = False) -> Iterator[Any]:
        """Yield a pyodbc connection and close it safely."""
        try:
            import pyodbc
        except ImportError as exc:  # pragma: no cover - depends on optional runtime
            raise DatabaseConnectionError(
                "pyodbc is required for SQL Server connectivity. Install project dependencies."
            ) from exc

        connection_string = self._settings.connection_string(database=database)
        connection = None
        try:
            connection = pyodbc.connect(connection_string, autocommit=autocommit)
            yield connection
            if not autocommit:
                connection.commit()
        except Exception as exc:  # pragma: no cover - integration behavior
            if connection is not None and not autocommit:
                connection.rollback()
            logger.exception("SQL Server operation failed.")
            raise DatabaseConnectionError(str(exc)) from exc
        finally:
            if connection is not None:
                connection.close()

    def health_check(self) -> bool:
        """Return True when SQL Server responds to a simple query."""
        with self.connect() as connection:
            cursor = connection.cursor()
            cursor.execute("SELECT 1")
            row = cursor.fetchone()
            return bool(row and row[0] == 1)
