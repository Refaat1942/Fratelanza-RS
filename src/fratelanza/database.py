"""Database command-line helpers."""

from __future__ import annotations

import argparse

from fratelanza.core.config import load_settings
from fratelanza.core.logging import configure_logging
from fratelanza.infrastructure.database.schema_manager import SchemaManager


def main(argv: list[str] | None = None) -> int:
    """Run database maintenance commands."""
    parser = argparse.ArgumentParser(prog="python -m fratelanza.database")
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("bootstrap", help="Create the SQL Server database and schema.")
    args = parser.parse_args(argv)

    settings = load_settings()
    configure_logging(settings)

    if args.command == "bootstrap":
        SchemaManager(settings.database).bootstrap()
        print(f"Database '{settings.database.database}' is ready.")
        return 0

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
