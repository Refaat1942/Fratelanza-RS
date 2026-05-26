"""Sidebar navigation widget."""

from __future__ import annotations

from collections.abc import Iterable

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import QFrame, QLabel, QPushButton, QVBoxLayout

from fratelanza.application.module_catalog import ModuleDefinition


class Sidebar(QFrame):
    """Left navigation menu for business modules."""

    navigation_requested = pyqtSignal(str)

    def __init__(self, modules: Iterable[ModuleDefinition], brand_name: str) -> None:
        super().__init__()
        self.setObjectName("Sidebar")
        self.setFixedWidth(260)

        logo = QLabel(brand_name)
        logo.setStyleSheet("font-size: 24px; font-weight: 800; letter-spacing: 1px;")
        subtitle = QLabel("Business Suite")
        subtitle.setObjectName("Muted")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 22, 18, 18)
        layout.setSpacing(10)
        layout.addWidget(logo)
        layout.addWidget(subtitle)
        layout.addSpacing(18)

        for module in modules:
            button = QPushButton(f"{module.icon}  {module.title}")
            button.setToolTip(module.description)
            button.clicked.connect(lambda checked=False, key=module.key: self.navigation_requested.emit(key))
            layout.addWidget(button)

        layout.addStretch()
