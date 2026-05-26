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
SQL_SERVER_DRIVER_PREFERENCE = (
    "ODBC Driver 18 for SQL Server",
    "ODBC Driver 17 for SQL Server",
    "SQL Server Native Client 11.0",
    "SQL Server",
)


def _to_bool(value: object) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    return str(value).strip().lower() in {"1", "true", "yes", "y", "on"}


def resolve_sql_server_driver(configured_driver: str) -> str:
    """Return a usable SQL Server ODBC driver when pyodbc can list installed drivers."""
    try:
        import pyodbc
    except ImportError:
        return configured_driver

    installed_drivers = set(pyodbc.drivers())
    if configured_driver in installed_drivers:
        return configured_driver
    for preferred_driver in SQL_SERVER_DRIVER_PREFERENCE:
        if preferred_driver in installed_drivers:
            return preferred_driver
    return configured_driver


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
class BrandingSettings:
    """Client-facing branding and white-label settings."""

    client_display_name: str
    logo_path: Path | None
    primary_color: str
    allow_client_branding: bool = True


@dataclass(frozen=True)
class RemoteAdminSettings:
    """VPS control-plane settings for sold customer installations."""

    enabled: bool
    api_base_url: str
    api_key: str
    client_id: str
    installation_id: str
    allow_remote_support: bool
    allow_remote_disable: bool
    heartbeat_interval_seconds: int = 900

    @property
    def is_configured(self) -> bool:
        """Return True when enough settings exist to contact the VPS API."""
        return bool(self.enabled and self.api_base_url and self.api_key and self.installation_id)


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
    branding: BrandingSettings
    remote_admin: RemoteAdminSettings


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
    branding = data.get("branding", {})
    remote_admin = data.get("remote_admin", {})
    db = data.get("database", {})

    configured_driver = os.getenv("FRATELANZA_DB_DRIVER", db.get("driver", ""))
    database_settings = DatabaseSettings(
        driver=resolve_sql_server_driver(configured_driver),
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

    logo_path_value = os.getenv("FRATELANZA_LOGO_PATH", branding.get("logo_path", "")).strip()
    logo_path = Path(logo_path_value).expanduser() if logo_path_value else None
    if logo_path is not None and not logo_path.is_absolute():
        logo_path = PROJECT_ROOT / logo_path

    return ApplicationSettings(
        brand_name=app.get("brand_name", "Fratelanza"),
        product_name=app.get("product_name", "Fratelanza Business Suite"),
        environment=os.getenv("FRATELANZA_ENVIRONMENT", app.get("environment", "production")),
        default_locale=os.getenv("FRATELANZA_LOCALE", app.get("default_locale", "en")),
        currency=app.get("currency", "USD"),
        theme=app.get("theme", "dark"),
        auto_backup_enabled=_to_bool(app.get("auto_backup_enabled", True)),
        backup_directory=PROJECT_ROOT / app.get("backup_directory", "backups"),
        log_level=os.getenv("FRATELANZA_LOG_LEVEL", "INFO"),
        database=database_settings,
        branding=BrandingSettings(
            client_display_name=os.getenv(
                "FRATELANZA_CLIENT_DISPLAY_NAME",
                branding.get("client_display_name", app.get("brand_name", "Fratelanza")),
            ),
            logo_path=logo_path,
            primary_color=os.getenv(
                "FRATELANZA_PRIMARY_COLOR",
                branding.get("primary_color", "#55d6be"),
            ),
            allow_client_branding=_to_bool(branding.get("allow_client_branding", True)),
        ),
        remote_admin=RemoteAdminSettings(
            enabled=_to_bool(
                os.getenv("FRATELANZA_REMOTE_ENABLED", remote_admin.get("enabled", False))
            ),
            api_base_url=os.getenv(
                "FRATELANZA_REMOTE_API_BASE_URL",
                remote_admin.get("api_base_url", ""),
            ).rstrip("/"),
            api_key=os.getenv("FRATELANZA_REMOTE_API_KEY", remote_admin.get("api_key", "")),
            client_id=os.getenv("FRATELANZA_REMOTE_CLIENT_ID", remote_admin.get("client_id", "")),
            installation_id=os.getenv(
                "FRATELANZA_REMOTE_INSTALLATION_ID",
                remote_admin.get("installation_id", ""),
            ),
            allow_remote_support=_to_bool(
                os.getenv(
                    "FRATELANZA_REMOTE_SUPPORT",
                    remote_admin.get("allow_remote_support", False),
                )
            ),
            allow_remote_disable=_to_bool(
                os.getenv(
                    "FRATELANZA_REMOTE_DISABLE",
                    remote_admin.get("allow_remote_disable", True),
                )
            ),
            heartbeat_interval_seconds=int(
                os.getenv(
                    "FRATELANZA_REMOTE_HEARTBEAT_SECONDS",
                    remote_admin.get("heartbeat_interval_seconds", 900),
                )
            ),
        ),
    )
