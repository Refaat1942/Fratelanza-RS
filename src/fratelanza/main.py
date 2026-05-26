"""Application entry point."""

from fratelanza.core.config import load_settings
from fratelanza.core.logging import configure_logging
from fratelanza.presentation.app import run_desktop_app


def main() -> int:
    """Start the desktop application."""
    settings = load_settings()
    configure_logging(settings)
    return run_desktop_app(settings)


if __name__ == "__main__":
    raise SystemExit(main())
