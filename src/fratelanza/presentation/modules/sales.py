"""Sales module UI."""

from __future__ import annotations

from decimal import Decimal
import logging

from PyQt6.QtWidgets import (
    QComboBox,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from fratelanza.application.sales_service import SalesService
from fratelanza.presentation.components.data_table import DataTable

logger = logging.getLogger(__name__)


class SalesView(QWidget):
    """Create sales invoices and review sales history."""

    def __init__(self, service: SalesService, user_id: int | None) -> None:
        super().__init__()
        self._service = service
        self._user_id = user_id
        self._lines: list[dict[str, object]] = []
        self._products: list[dict[str, object]] = []
        self._build()
        self._load_options()

    def _build(self) -> None:
        self._invoice_table = DataTable(
            title="Sales Invoices",
            columns=[
                ("SalesInvoiceId", "ID"),
                ("InvoiceNumber", "Invoice"),
                ("CustomerName", "Customer"),
                ("InvoiceStatus", "Status"),
                ("GrandTotal", "Total"),
                ("PaidTotal", "Paid"),
                ("CreatedAt", "Created"),
            ],
            load_rows=lambda search: self._service.invoices(),
            searchable=False,
        )
        creator = self._invoice_creator()
        layout = QHBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.addWidget(self._invoice_table, stretch=3)
        layout.addWidget(creator, stretch=2)

    def _invoice_creator(self) -> QFrame:
        frame = QFrame()
        frame.setObjectName("Card")
        title = QLabel("Create Invoice")
        title.setObjectName("SectionTitle")
        self._customer = QComboBox()
        self._product = QComboBox()
        self._quantity = QLineEdit("1")
        self._discount = QLineEdit("0")
        self._tax = QLineEdit("0")
        self._paid = QLineEdit("0")
        self._payment = QComboBox()
        self._payment.addItems(["cash", "card", "bank_transfer", "mobile_wallet", "credit"])
        self._notes = QLineEdit()
        self._lines_table = QTableWidget()
        self._lines_table.setColumnCount(5)
        self._lines_table.setHorizontalHeaderLabels(["Product ID", "Product", "Qty", "Price", "Total"])
        self._total = QLabel("Total: 0.00")

        add_line = QPushButton("Add Line")
        add_line.clicked.connect(self._add_line)
        save = QPushButton("Save Invoice")
        save.setObjectName("PrimaryButton")
        save.clicked.connect(self._save_invoice)

        form = QFormLayout()
        form.addRow("Customer", self._customer)
        form.addRow("Product", self._product)
        form.addRow("Quantity", self._quantity)
        form.addRow("Invoice Discount", self._discount)
        form.addRow("Line Tax", self._tax)
        form.addRow("Paid", self._paid)
        form.addRow("Payment", self._payment)
        form.addRow("Notes", self._notes)

        layout = QVBoxLayout(frame)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.addWidget(title)
        layout.addLayout(form)
        layout.addWidget(add_line)
        layout.addWidget(self._lines_table)
        layout.addWidget(self._total)
        layout.addWidget(save)
        return frame

    def _load_options(self) -> None:
        try:
            customers = self._service.customers()
            self._products = self._service.products()
        except Exception as exc:
            logger.exception("Failed to load sales options.")
            QMessageBox.critical(self, "Database error", str(exc))
            return
        self._customer.clear()
        self._customer.addItem("Walk-in customer", None)
        for customer in customers:
            self._customer.addItem(
                f"{customer['CustomerCode']} - {customer['FullName']}",
                customer["CustomerId"],
            )
        self._product.clear()
        for product in self._products:
            self._product.addItem(
                f"{product['Sku']} - {product['ProductName']} ({product['SalePrice']})",
                product["ProductId"],
            )

    def _add_line(self) -> None:
        product_id = self._product.currentData()
        product = next((item for item in self._products if item["ProductId"] == product_id), None)
        if product is None:
            QMessageBox.warning(self, "No product", "Add products before creating invoices.")
            return
        quantity = Decimal(self._quantity.text() or "1")
        unit_price = Decimal(str(product["SalePrice"] or "0"))
        tax_amount = Decimal(self._tax.text() or "0")
        line_total = quantity * unit_price + tax_amount
        self._lines.append(
            {
                "product_id": product_id,
                "product_name": product["ProductName"],
                "quantity": quantity,
                "unit_price": unit_price,
                "discount_amount": Decimal("0"),
                "tax_amount": tax_amount,
                "line_total": line_total,
            }
        )
        self._refresh_lines()

    def _refresh_lines(self) -> None:
        self._lines_table.setRowCount(len(self._lines))
        total = Decimal("0")
        for row_index, line in enumerate(self._lines):
            total += Decimal(str(line["line_total"]))
            values = [
                line["product_id"],
                line["product_name"],
                line["quantity"],
                line["unit_price"],
                line["line_total"],
            ]
            for column_index, value in enumerate(values):
                self._lines_table.setItem(row_index, column_index, QTableWidgetItem(str(value)))
        total_after_discount = total - Decimal(self._discount.text() or "0")
        self._total.setText(f"Total: {total_after_discount:,.2f}")

    def _save_invoice(self) -> None:
        if not self._lines:
            QMessageBox.warning(self, "No lines", "Add at least one invoice line.")
            return
        try:
            invoice_id = self._service.create_invoice(
                customer_id=self._customer.currentData(),
                payment_method=self._payment.currentText(),
                discount_total=Decimal(self._discount.text() or "0"),
                paid_total=Decimal(self._paid.text() or "0"),
                notes=self._notes.text(),
                user_id=self._user_id,
                lines=self._lines,
            )
        except Exception as exc:
            logger.exception("Failed to save invoice.")
            QMessageBox.critical(self, "Save failed", str(exc))
            return
        self._lines.clear()
        self._refresh_lines()
        self._invoice_table.refresh()
        self._load_options()
        QMessageBox.information(self, "Invoice saved", f"Invoice #{invoice_id} saved.")
