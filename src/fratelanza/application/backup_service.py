"""Offline-first backup orchestration."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from fratelanza.core.config import DatabaseSettings


class BackupService:
    """Build safe SQL Server backup paths and commands.

    Execution is intentionally delegated to infrastructure or an operations
    runner because production clients differ in SQL Server permissions.
    """

    def __init__(self, database_settings: DatabaseSettings, backup_directory: Path) -> None:
        self._database_settings = database_settings
        self._backup_directory = backup_directory

    def next_backup_path(self) -> Path:
        """Return the next timestamped backup file path."""
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        return self._backup_directory / f"{self._database_settings.database}_{timestamp}.bak"

    def build_backup_sql(self, backup_path: Path) -> str:
        """Return the SQL statement used for a full database backup."""
        normalized_path = str(backup_path).replace("'", "''")
        database = self._database_settings.database.replace("]", "]]")
        return (
            f"BACKUP DATABASE [{database}] "
            f"TO DISK = N'{normalized_path}' "
            "WITH INIT, COMPRESSION, CHECKSUM;"
        )
