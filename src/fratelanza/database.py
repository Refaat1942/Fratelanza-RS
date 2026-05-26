"""Database command-line helpers."""

from __future__ import annotations

import argparse

from fratelanza.core.config import ApplicationSettings, load_settings
from fratelanza.core.logging import configure_logging
from fratelanza.infrastructure.database.schema_manager import SchemaManager


def main(argv: list[str] | None = None) -> int:
    """Run database maintenance commands."""
    parser = argparse.ArgumentParser(prog="python -m fratelanza.database")
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("bootstrap", help="Create the SQL Server database and schema.")
    subparsers.add_parser("doctor", help="Show SQL Server connection settings and drivers.")
    args = parser.parse_args(argv)

    settings = load_settings()
    configure_logging(settings)

    if args.command == "bootstrap":
        SchemaManager(settings.database).bootstrap()
        print(f"Database '{settings.database.database}' is ready.")
        return 0

    if args.command == "doctor":
        _print_database_doctor(settings)
        return 0

    return 1


def _print_database_doctor(settings: ApplicationSettings) -> None:
    database = settings.database
    print("Fratelanza database settings")
    print("-----------------------------")
    print(f"Driver   : {database.driver}")
    print(f"Server   : {database.server}")
    print(f"Database : {database.database}")
    print(f"Trusted  : {database.trusted_connection}")
    print(f"Encrypt  : {database.encrypt}")
    try:
        import pyodbc
    except ImportError:
        print("pyodbc   : not installed")
        return
    print("Installed ODBC drivers:")
    for driver in pyodbc.drivers():
        print(f" - {driver}")


if __name__ == "__main__":
    raise SystemExit(main())
