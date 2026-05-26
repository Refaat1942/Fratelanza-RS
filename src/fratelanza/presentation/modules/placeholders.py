"""Reusable module placeholder views."""

from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QFrame, QLabel, QVBoxLayout, QWidget

from fratelanza.application.module_catalog import ModuleDefinition


class ModulePlaceholderView(QWidget):
    """Professional placeholder for modules that will be expanded next."""

    def __init__(self, module: ModuleDefinition) -> None:
        super().__init__()

        card = QFrame()
        card.setObjectName("Card")
        card.setMinimumHeight(280)

        title = QLabel(module.title)
        title.setObjectName("Title")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        description = QLabel(module.description)
        description.setObjectName("Muted")
        description.setWordWrap(True)
        description.setAlignment(Qt.AlignmentFlag.AlignCenter)

        status = QLabel("Module shell is ready for client-specific workflows.")
        status.setObjectName("Muted")
        status.setAlignment(Qt.AlignmentFlag.AlignCenter)

        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(36, 36, 36, 36)
        card_layout.setSpacing(14)
        card_layout.addStretch()
        card_layout.addWidget(title)
        card_layout.addWidget(description)
        card_layout.addWidget(status)
        card_layout.addStretch()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.addWidget(card)
