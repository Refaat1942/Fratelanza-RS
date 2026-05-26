"""PyQt6 application composition root."""

from __future__ import annotations

import sys

from PyQt6.QtWidgets import QApplication, QDialog

from fratelanza.application.auth_service import AuthService
from fratelanza.application.dashboard_service import DashboardService
from fratelanza.core.config import ApplicationSettings
from fratelanza.infrastructure.database.connection import SqlServerConnectionFactory
from fratelanza.infrastructure.repositories.dashboard_repository import DashboardRepository
from fratelanza.infrastructure.repositories.user_repository import UserRepository
from fratelanza.presentation.login_dialog import LoginDialog
from fratelanza.presentation.main_window import MainWindow
from fratelanza.presentation.theme import build_stylesheet, get_theme


def run_desktop_app(settings: ApplicationSettings) -> int:
    """Create dependencies and start the Qt event loop."""
    qt_app = QApplication(sys.argv)
    qt_app.setApplicationName(settings.product_name)
    qt_app.setOrganizationName(settings.brand_name)
    qt_app.setStyleSheet(build_stylesheet(get_theme(settings.theme)))

    connection_factory = SqlServerConnectionFactory(settings.database)
    user_repository = UserRepository(connection_factory)
    dashboard_repository = DashboardRepository(connection_factory)
    auth_service = AuthService(user_repository)
    dashboard_service = DashboardService(dashboard_repository, settings.currency)

    login_dialog = LoginDialog(auth_service, settings.product_name, settings.brand_name)
    if login_dialog.exec() != QDialog.DialogCode.Accepted or login_dialog.session is None:
        return 0

    window = MainWindow(
        session=login_dialog.session,
        brand_name=settings.brand_name,
        dashboard_service=dashboard_service,
    )
    window.show()
    return qt_app.exec()
