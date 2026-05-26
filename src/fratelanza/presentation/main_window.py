"""Main application shell."""

from __future__ import annotations

from PyQt6.QtCore import QEasingCurve, QPropertyAnimation
from PyQt6.QtWidgets import (
    QApplication,
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from fratelanza.application.branding_service import BrandingProfile
from fratelanza.application.barcode_service import BarcodeService
from fratelanza.application.dashboard_service import DashboardService
from fratelanza.application.finance_service import FinanceService
from fratelanza.application.inventory_service import InventoryService
from fratelanza.application.module_catalog import MODULE_CATALOG, ModuleDefinition
from fratelanza.application.partner_service import PartnerService
from fratelanza.application.reports_service import ReportsService
from fratelanza.application.sales_service import SalesService
from fratelanza.application.session import UserSession
from fratelanza.application.settings_service import SettingsService
from fratelanza.core.config import ApplicationSettings
from fratelanza.core.i18n import Localizer
from fratelanza.core.permissions import has_permission
from fratelanza.presentation.components.sidebar import Sidebar
from fratelanza.presentation.modules.barcodes import BarcodesView
from fratelanza.presentation.modules.dashboard import DashboardView
from fratelanza.presentation.modules.finance import FinanceView
from fratelanza.presentation.modules.inventory import InventoryView
from fratelanza.presentation.modules.partners import PartnersView
from fratelanza.presentation.modules.placeholders import ModulePlaceholderView
from fratelanza.presentation.modules.reports import ReportsView
from fratelanza.presentation.modules.sales import SalesView
from fratelanza.presentation.modules.settings import SettingsView
from fratelanza.presentation.theme import build_stylesheet, get_theme


class MainWindow(QMainWindow):
    """Responsive desktop shell with sidebar navigation and top search."""

    def __init__(
        self,
        *,
        session: UserSession,
        branding: BrandingProfile,
        localizer: Localizer,
        settings: ApplicationSettings,
        dashboard_service: DashboardService,
        inventory_service: InventoryService,
        partner_service: PartnerService,
        finance_service: FinanceService,
        sales_service: SalesService,
        reports_service: ReportsService,
        settings_service: SettingsService,
        barcode_service: BarcodeService,
    ) -> None:
        super().__init__()
        self._session = session
        self._branding = branding
        self._localizer = localizer
        self._settings = settings
        self._dashboard_service = dashboard_service
        self._inventory_service = inventory_service
        self._partner_service = partner_service
        self._finance_service = finance_service
        self._sales_service = sales_service
        self._reports_service = reports_service
        self._settings_service = settings_service
        self._barcode_service = barcode_service
        self._module_indexes: dict[str, int] = {}
        self._fade_animation: QPropertyAnimation | None = None

        self.setWindowTitle(f"{branding.display_name} - {branding.product_name}")
        self.resize(1360, 820)
        self.setMinimumSize(1100, 700)
        self._build()

    def _build(self) -> None:
        modules = self._allowed_modules()
        self._stack = QStackedWidget()

        for module in modules:
            view = self._create_module_view(module)
            self._module_indexes[module.key] = self._stack.addWidget(view)

        sidebar = Sidebar(modules, self._branding, self._localizer)
        sidebar.navigation_requested.connect(self.navigate)

        top_bar = QFrame()
        top_bar.setObjectName("TopBar")
        search = QLineEdit()
        search.setPlaceholderText(self._localizer.gettext("app.search_placeholder"))
        theme_selector = QComboBox()
        theme_selector.addItem("Dark", "dark")
        theme_selector.addItem("Light", "light")
        theme_selector.setCurrentIndex(max(0, theme_selector.findData(self._settings.theme)))
        theme_selector.currentIndexChanged.connect(
            lambda: self._apply_theme(str(theme_selector.currentData()))
        )
        user_label = QLabel(
            f"{self._session.user.display_name} ({self._session.user.role.name})"
        )
        user_label.setObjectName("Muted")

        top_layout = QHBoxLayout(top_bar)
        top_layout.setContentsMargins(16, 12, 16, 12)
        top_layout.addWidget(search, stretch=1)
        top_layout.addWidget(theme_selector)
        top_layout.addWidget(user_label)

        content_layout = QVBoxLayout()
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(14)
        content_layout.addWidget(top_bar)
        content_layout.addWidget(self._stack, stretch=1)

        content = QWidget()
        content.setLayout(content_layout)

        root_layout = QHBoxLayout()
        root_layout.setContentsMargins(16, 16, 16, 16)
        root_layout.setSpacing(16)
        root_layout.addWidget(sidebar)
        root_layout.addWidget(content, stretch=1)

        root = QWidget()
        root.setLayout(root_layout)
        self.setCentralWidget(root)

        if "dashboard" in self._module_indexes:
            self.navigate("dashboard")

    def _create_module_view(self, module: ModuleDefinition) -> QWidget:
        if module.key == "dashboard":
            return DashboardView(self._dashboard_service, self._localizer)
        if module.key == "sales":
            return SalesView(self._sales_service, self._session.user.id)
        if module.key == "inventory":
            return InventoryView(self._inventory_service)
        if module.key == "finance":
            return FinanceView(self._finance_service, self._session.user.id)
        if module.key == "partners":
            return PartnersView(self._partner_service)
        if module.key == "reports":
            return ReportsView(self._reports_service, self._settings.currency)
        if module.key == "barcodes":
            return BarcodesView(self._barcode_service, self._inventory_service)
        if module.key == "settings":
            return SettingsView(self._settings_service, self._settings)
        return ModulePlaceholderView(module, self._localizer)

    def _allowed_modules(self) -> list[ModuleDefinition]:
        permissions = self._session.permissions
        return [
            module
            for module in MODULE_CATALOG
            if has_permission(permissions, module.permission)
        ]

    def navigate(self, module_key: str) -> None:
        """Switch visible module and animate the stack opacity."""
        index = self._module_indexes.get(module_key)
        if index is None:
            return
        self._stack.setCurrentIndex(index)
        self._fade_animation = QPropertyAnimation(self._stack, b"windowOpacity", self)
        self._fade_animation.setDuration(160)
        self._fade_animation.setStartValue(0.85)
        self._fade_animation.setEndValue(1.0)
        self._fade_animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._fade_animation.start()

    def _apply_theme(self, theme_name: str) -> None:
        """Apply dark or light theme at runtime."""
        app = QApplication.instance()
        if app is None:
            return
        app.setStyleSheet(
            build_stylesheet(get_theme(theme_name), primary_color=self._branding.primary_color)
        )
