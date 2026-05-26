"""Database bootstrap helpers."""

from __future__ import annotations

from pathlib import Path
import re

from fratelanza.core.config import DatabaseSettings, PROJECT_ROOT
from fratelanza.infrastructure.database.connection import SqlServerConnectionFactory


DEFAULT_SCHEMA_SCRIPT = PROJECT_ROOT / "database" / "sqlserver" / "001_create_schema.sql"


class SchemaManager:
    """Execute SQL Server schema scripts in deployment order."""

    def __init__(
        self,
        settings: DatabaseSettings,
        connection_factory: SqlServerConnectionFactory | None = None,
    ) -> None:
        self._settings = settings
        self._connection_factory = connection_factory or SqlServerConnectionFactory(settings)

    def bootstrap(self, script_path: Path = DEFAULT_SCHEMA_SCRIPT) -> None:
        """Create the configured database and initial schema."""
        sql = script_path.read_text(encoding="utf-8").replace(
            "__DATABASE_NAME__", self._settings.database
        )
        batches = split_sql_batches(sql)
        with self._connection_factory.connect(database="master", autocommit=True) as connection:
            cursor = connection.cursor()
            for batch in batches:
                cursor.execute(batch)


def split_sql_batches(sql: str) -> list[str]:
    """Split SQL Server scripts by GO batch separators."""
    batches = re.split(r"^\s*GO\s*;?\s*$", sql, flags=re.IGNORECASE | re.MULTILINE)
    return [batch.strip() for batch in batches if batch.strip()]
