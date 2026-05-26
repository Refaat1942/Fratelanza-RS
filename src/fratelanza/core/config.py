"""Runtime configuration loading.

Configuration is intentionally small and explicit so the desktop product can be
installed offline for a single shop or pointed to a managed SQL Server instance
for larger clients.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import os
import tomllib

from fratelanza.core.exceptions import ConfigurationError


PROJECT_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_CONFIG_PATH = PROJECT_ROOT / "config" / "app.toml"


def _to_bool(value: object) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    return str(value).strip().lower() in {"1", "true", "yes", "y", "on"}


@dataclass(frozen=True)
class DatabaseSettings:
    """SQL Server connection settings."""

    driver: str
    server: str
    database: str
    trusted_connection: bool = True
    username: str = ""
    password: str = ""
    encrypt: bool = True
    trust_server_certificate: bool = True
    timeout: int = 30

    def connection_string(self, *, database: str | None = None) -> str:
        """Build an ODBC connection string for pyodbc."""
        target_database = database or self.database
        parts = [
            f"DRIVER={{{self.driver}}}",
            f"SERVER={self.server}",
            f"DATABASE={target_database}",
            f"Encrypt={'yes' if self.encrypt else 'no'}",
            "TrustServerCertificate="
            f"{'yes' if self.trust_server_certificate else 'no'}",
            f"Connection Timeout={self.timeout}",
        ]
        if self.trusted_connection:
            parts.append("Trusted_Connection=yes")
        else:
            if not self.username:
                raise ConfigurationError("Database username is required when trusted auth is off.")
            parts.extend([f"UID={self.username}", f"PWD={self.password}"])
        return ";".join(parts) + ";"


@dataclass(frozen=True)
class ApplicationSettings:
    """Top-level application settings."""

    brand_name: str
    product_name: str
    environment: str
    default_locale: str
    currency: str
    theme: str
    auto_backup_enabled: bool
    backup_directory: Path
    log_level: str
    database: DatabaseSettings


def load_settings(config_path: Path | None = None) -> ApplicationSettings:
    """Load settings from TOML and environment variables."""
    try:
        from dotenv import load_dotenv
    except ImportError:  # pragma: no cover - dependency exists in packaged installs
        load_dotenv = None
    if load_dotenv is not None:
        load_dotenv(PROJECT_ROOT / ".env")
    path = config_path or DEFAULT_CONFIG_PATH
    if not path.exists():
        raise ConfigurationError(f"Configuration file not found: {path}")

    data = tomllib.loads(path.read_text(encoding="utf-8"))
    app = data.get("application", {})
    db = data.get("database", {})

    database_settings = DatabaseSettings(
        driver=os.getenv("FRATELANZA_DB_DRIVER", db.get("driver", "")),
        server=os.getenv("FRATELANZA_DB_SERVER", db.get("server", "")),
        database=os.getenv("FRATELANZA_DB_NAME", db.get("database", "")),
        trusted_connection=_to_bool(
            os.getenv("FRATELANZA_DB_TRUSTED_CONNECTION", db.get("trusted_connection", True))
        ),
        username=os.getenv("FRATELANZA_DB_USERNAME", db.get("username", "")),
        password=os.getenv("FRATELANZA_DB_PASSWORD", db.get("password", "")),
        encrypt=_to_bool(os.getenv("FRATELANZA_DB_ENCRYPT", db.get("encrypt", True))),
        trust_server_certificate=_to_bool(
            os.getenv(
                "FRATELANZA_DB_TRUST_SERVER_CERTIFICATE",
                db.get("trust_server_certificate", True),
            )
        ),
        timeout=int(os.getenv("FRATELANZA_DB_TIMEOUT", db.get("timeout", 30))),
    )

    if not database_settings.driver or not database_settings.server or not database_settings.database:
        raise ConfigurationError("Database driver, server, and database are required.")

    return ApplicationSettings(
        brand_name=app.get("brand_name", "Fratelanza"),
        product_name=app.get("product_name", "Fratelanza Business Suite"),
        environment=os.getenv("FRATELANZA_ENVIRONMENT", app.get("environment", "production")),
        default_locale=app.get("default_locale", "en"),
        currency=app.get("currency", "USD"),
        theme=app.get("theme", "dark"),
        auto_backup_enabled=_to_bool(app.get("auto_backup_enabled", True)),
        backup_directory=PROJECT_ROOT / app.get("backup_directory", "backups"),
        log_level=os.getenv("FRATELANZA_LOG_LEVEL", "INFO"),
        database=database_settings,
    )
