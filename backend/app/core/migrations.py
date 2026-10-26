"""Run Alembic migrations programmatically at startup (inside a Postgres advisory lock)."""

from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[2]


def run_migrations(connection) -> None:
    from alembic import command
    from alembic.config import Config

    cfg = Config(str(BACKEND_DIR / "alembic.ini"))
    cfg.set_main_option("script_location", str(BACKEND_DIR / "alembic"))
    cfg.attributes["connection"] = connection
    command.upgrade(cfg, "head")
