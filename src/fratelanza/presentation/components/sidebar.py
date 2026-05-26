"""Sidebar navigation widget."""

from __future__ import annotations

from collections.abc import Iterable

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import QFrame, QLabel, QPushButton, QVBoxLayout

from fratelanza.application.branding_service import BrandingProfile
from fratelanza.application.module_catalog import ModuleDefinition
from fratelanza.core.i18n import Localizer


class Sidebar(QFrame):
    """Left navigation menu for business modules."""

    navigation_requested = pyqtSignal(str)

    def __init__(
        self,
        modules: Iterable[ModuleDefinition],
        branding: BrandingProfile,
        localizer: Localizer,
    ) -> None:
        super().__init__()
        self.setObjectName("Sidebar")
        self.setFixedWidth(260)

        logo = QLabel(branding.display_name)
        logo.setStyleSheet("font-size: 22px; font-weight: 800; letter-spacing: 1px;")
        if branding.has_logo:
            pixmap = QPixmap(str(branding.logo_path))
            logo.setPixmap(pixmap.scaledToWidth(150))
        subtitle = QLabel(localizer.gettext("app.business_suite"))
        subtitle.setObjectName("Muted")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 22, 18, 18)
        layout.setSpacing(10)
        layout.addWidget(logo)
        layout.addWidget(subtitle)
        layout.addSpacing(18)

        for module in modules:
            title = localizer.gettext(module.title_key)
            button = QPushButton(f"{module.icon}  {title}")
            button.setToolTip(localizer.gettext(module.description_key))
            button.clicked.connect(
                lambda checked=False, key=module.key: self.navigation_requested.emit(key)
            )
            layout.addWidget(button)

        layout.addStretch()
