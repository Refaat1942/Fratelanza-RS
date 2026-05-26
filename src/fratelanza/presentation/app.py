"""PyQt6 application composition root."""

from __future__ import annotations

import sys
import platform

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication, QDialog, QMessageBox

from fratelanza import __version__
from fratelanza.application.auth_service import AuthService
from fratelanza.application.branding_service import BrandingService
from fratelanza.application.dashboard_service import DashboardService
from fratelanza.application.remote_admin_service import RemoteAdminService
from fratelanza.core.config import ApplicationSettings
from fratelanza.core.i18n import Localizer
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
    branding = BrandingService(settings).current_profile()
    localizer = Localizer(settings.default_locale)
    _apply_layout_direction(qt_app, localizer)
    qt_app.setStyleSheet(
        build_stylesheet(get_theme(settings.theme), primary_color=branding.primary_color)
    )

    connection_factory = SqlServerConnectionFactory(settings.database)
    user_repository = UserRepository(connection_factory)
    dashboard_repository = DashboardRepository(connection_factory)
    auth_service = AuthService(user_repository)
    dashboard_service = DashboardService(dashboard_repository, settings.currency)
    remote_admin_service = RemoteAdminService(settings.remote_admin)
    remote_admin_service.sync_installation(
        app_version=__version__,
        machine_name=platform.node(),
    )
    remote_status = remote_admin_service.current_status()
    if settings.remote_admin.allow_remote_disable and not remote_status.can_run:
        QMessageBox.critical(
            None,
            "License disabled",
            remote_status.message or f"Installation state: {remote_status.state.value}",
        )
        return 1

    login_dialog = LoginDialog(auth_service, localizer, branding)
    if login_dialog.exec() != QDialog.DialogCode.Accepted or login_dialog.session is None:
        return 0

    _apply_layout_direction(qt_app, localizer)
    window = MainWindow(
        session=login_dialog.session,
        branding=branding,
        localizer=localizer,
        dashboard_service=dashboard_service,
        remote_admin_service=remote_admin_service,
    )
    window.show()
    return qt_app.exec()


def _apply_layout_direction(qt_app: QApplication, localizer: Localizer) -> None:
    qt_app.setLayoutDirection(
        Qt.LayoutDirection.RightToLeft
        if localizer.locale.is_rtl
        else Qt.LayoutDirection.LeftToRight
    )
