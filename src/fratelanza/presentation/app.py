"""PyQt6 application composition root."""

from __future__ import annotations

import sys
import platform

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication, QDialog, QMessageBox

from fratelanza import __version__
from fratelanza.application.auth_service import AuthService
from fratelanza.application.barcode_service import BarcodeService
from fratelanza.application.branding_service import BrandingService
from fratelanza.application.dashboard_service import DashboardService
from fratelanza.application.finance_service import FinanceService
from fratelanza.application.inventory_service import InventoryService
from fratelanza.application.offline_license_cache import OfflineLicenseCache
from fratelanza.application.partner_service import PartnerService
from fratelanza.application.remote_admin_service import RemoteAdminService
from fratelanza.application.reports_service import ReportsService
from fratelanza.application.sales_service import SalesService
from fratelanza.application.settings_service import SettingsService
from fratelanza.core.config import ApplicationSettings
from fratelanza.core.i18n import Localizer
from fratelanza.infrastructure.database.connection import SqlServerConnectionFactory
from fratelanza.infrastructure.repositories.dashboard_repository import DashboardRepository
from fratelanza.infrastructure.repositories.finance_repository import FinanceRepository
from fratelanza.infrastructure.repositories.inventory_repository import InventoryRepository
from fratelanza.infrastructure.repositories.partner_repository import PartnerRepository
from fratelanza.infrastructure.repositories.reports_repository import ReportsRepository
from fratelanza.infrastructure.repositories.sales_repository import SalesRepository
from fratelanza.infrastructure.repositories.settings_repository import SettingsRepository
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
    inventory_repository = InventoryRepository(connection_factory)
    partner_repository = PartnerRepository(connection_factory)
    finance_repository = FinanceRepository(connection_factory)
    sales_repository = SalesRepository(connection_factory)
    reports_repository = ReportsRepository(connection_factory)
    settings_repository = SettingsRepository(connection_factory)
    barcode_service = BarcodeService()
    auth_service = AuthService(user_repository)
    dashboard_service = DashboardService(dashboard_repository, settings.currency)
    inventory_service = InventoryService(inventory_repository, barcode_service)
    partner_service = PartnerService(partner_repository)
    finance_service = FinanceService(finance_repository)
    sales_service = SalesService(sales_repository, inventory_repository, partner_repository)
    reports_service = ReportsService(reports_repository)
    settings_service = SettingsService(settings_repository)
    license_cache = (
        OfflineLicenseCache(settings.remote_admin.offline_license_cache_path)
        if settings.remote_admin.offline_license_cache_path is not None
        else None
    )
    remote_admin_service = RemoteAdminService(settings.remote_admin, license_cache=license_cache)
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
        settings=settings,
        dashboard_service=dashboard_service,
        inventory_service=inventory_service,
        partner_service=partner_service,
        finance_service=finance_service,
        sales_service=sales_service,
        reports_service=reports_service,
        settings_service=settings_service,
        barcode_service=barcode_service,
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
