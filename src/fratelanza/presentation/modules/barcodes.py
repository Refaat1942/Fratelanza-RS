"""Barcode module UI."""

from __future__ import annotations

import logging

from PyQt6.QtWidgets import QFormLayout, QLabel, QLineEdit, QMessageBox, QPushButton, QVBoxLayout, QWidget

from fratelanza.application.barcode_service import BarcodeService
from fratelanza.application.inventory_service import InventoryService

logger = logging.getLogger(__name__)


class BarcodesView(QWidget):
    """Generate and assign product barcodes."""

    def __init__(self, barcode_service: BarcodeService, inventory_service: InventoryService) -> None:
        super().__init__()
        self._barcode_service = barcode_service
        self._inventory_service = inventory_service
        self._build()

    def _build(self) -> None:
        title = QLabel("Barcode System")
        title.setObjectName("Title")
        self._product_id = QLineEdit()
        self._product_id.setPlaceholderText("Product ID")
        self._category_code = QLineEdit("GEN")
        self._sequence = QLineEdit("1")
        self._result = QLineEdit()
        self._result.setReadOnly(True)

        generate_ean = QPushButton("Generate EAN-13")
        generate_ean.clicked.connect(self._generate_ean)
        generate_code = QPushButton("Generate Product Code")
        generate_code.clicked.connect(self._generate_code)
        assign = QPushButton("Assign Barcode To Product")
        assign.setObjectName("PrimaryButton")
        assign.clicked.connect(self._assign)

        form = QFormLayout()
        form.addRow("Product ID", self._product_id)
        form.addRow("Category Code", self._category_code)
        form.addRow("Sequence", self._sequence)
        form.addRow("Result", self._result)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.addWidget(title)
        layout.addLayout(form)
        layout.addWidget(generate_ean)
        layout.addWidget(generate_code)
        layout.addWidget(assign)
        layout.addStretch()

    def _generate_ean(self) -> None:
        product_id = int(self._product_id.text() or self._sequence.text() or "1")
        self._result.setText(self._barcode_service.generate_ean13(product_id))

    def _generate_code(self) -> None:
        self._result.setText(
            self._barcode_service.generate_product_code(
                self._category_code.text() or "GEN",
                int(self._sequence.text() or "1"),
            )
        )

    def _assign(self) -> None:
        try:
            self._inventory_service.set_barcode(int(self._product_id.text()), self._result.text())
        except Exception as exc:
            logger.exception("Failed to assign barcode.")
            QMessageBox.critical(self, "Save failed", str(exc))
            return
        QMessageBox.information(self, "Saved", "Barcode assigned to product.")
