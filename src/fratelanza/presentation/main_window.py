"""Main application shell."""

from __future__ import annotations

from PyQt6.QtCore import QEasingCurve, QPropertyAnimation
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from fratelanza.application.dashboard_service import DashboardService
from fratelanza.application.module_catalog import MODULE_CATALOG, ModuleDefinition
from fratelanza.application.session import UserSession
from fratelanza.core.permissions import has_permission
from fratelanza.presentation.components.sidebar import Sidebar
from fratelanza.presentation.modules.dashboard import DashboardView
from fratelanza.presentation.modules.placeholders import ModulePlaceholderView


class MainWindow(QMainWindow):
    """Responsive desktop shell with sidebar navigation and top search."""

    def __init__(
        self,
        *,
        session: UserSession,
        brand_name: str,
        dashboard_service: DashboardService,
    ) -> None:
        super().__init__()
        self._session = session
        self._dashboard_service = dashboard_service
        self._module_indexes: dict[str, int] = {}
        self._fade_animation: QPropertyAnimation | None = None

        self.setWindowTitle(f"{brand_name} Business Suite")
        self.resize(1360, 820)
        self.setMinimumSize(1100, 700)
        self._build(brand_name)

    def _build(self, brand_name: str) -> None:
        modules = self._allowed_modules()
        self._stack = QStackedWidget()

        for module in modules:
            view = (
                DashboardView(self._dashboard_service)
                if module.key == "dashboard"
                else ModulePlaceholderView(module)
            )
            self._module_indexes[module.key] = self._stack.addWidget(view)

        sidebar = Sidebar(modules, brand_name)
        sidebar.navigation_requested.connect(self.navigate)

        top_bar = QFrame()
        top_bar.setObjectName("TopBar")
        search = QLineEdit()
        search.setPlaceholderText("Search products, invoices, customers, suppliers...")
        user_label = QLabel(f"{self._session.user.display_name} ({self._session.user.role.name})")
        user_label.setObjectName("Muted")

        top_layout = QHBoxLayout(top_bar)
        top_layout.setContentsMargins(16, 12, 16, 12)
        top_layout.addWidget(search, stretch=1)
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
