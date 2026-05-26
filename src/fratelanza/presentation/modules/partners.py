"""Customers and suppliers module UI."""

from __future__ import annotations

from PyQt6.QtWidgets import QHBoxLayout, QTabWidget, QVBoxLayout, QWidget

from fratelanza.application.partner_service import PartnerService
from fratelanza.presentation.components.data_table import DataEntryPanel, DataTable, FieldSpec


class PartnersView(QWidget):
    """Customer and supplier management."""

    def __init__(self, service: PartnerService) -> None:
        super().__init__()
        self._service = service
        self._build()

    def _build(self) -> None:
        tabs = QTabWidget()
        tabs.addTab(self._customers_page(), "Customers")
        tabs.addTab(self._suppliers_page(), "Suppliers")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.addWidget(tabs)

    def _customers_page(self) -> QWidget:
        page = QWidget()
        table = DataTable(
            title="Customers",
            columns=[
                ("CustomerId", "ID"),
                ("CustomerCode", "Code"),
                ("FullName", "Name"),
                ("Phone", "Phone"),
                ("Email", "Email"),
                ("CreditLimit", "Credit Limit"),
                ("OpeningBalance", "Opening Balance"),
            ],
            load_rows=self._service.customers,
        )
        form = DataEntryPanel(
            title="Add Customer",
            fields=[
                FieldSpec("code", "Code"),
                FieldSpec("name", "Name"),
                FieldSpec("phone", "Phone"),
                FieldSpec("email", "Email"),
                FieldSpec("address", "Address"),
                FieldSpec("tax_number", "Tax Number"),
                FieldSpec("credit_limit", "Credit Limit", "0"),
                FieldSpec("opening_balance", "Opening Balance", "0"),
            ],
            submit_label="Save Customer",
            on_submit=self._service.add_customer,
            on_success=table.refresh,
        )
        layout = QHBoxLayout(page)
        layout.addWidget(table, stretch=3)
        layout.addWidget(form, stretch=1)
        return page

    def _suppliers_page(self) -> QWidget:
        page = QWidget()
        table = DataTable(
            title="Suppliers",
            columns=[
                ("SupplierId", "ID"),
                ("SupplierCode", "Code"),
                ("SupplierName", "Name"),
                ("ContactPerson", "Contact"),
                ("Phone", "Phone"),
                ("Email", "Email"),
                ("OpeningBalance", "Opening Balance"),
            ],
            load_rows=self._service.suppliers,
        )
        form = DataEntryPanel(
            title="Add Supplier",
            fields=[
                FieldSpec("code", "Code"),
                FieldSpec("name", "Name"),
                FieldSpec("contact_person", "Contact Person"),
                FieldSpec("phone", "Phone"),
                FieldSpec("email", "Email"),
                FieldSpec("address", "Address"),
                FieldSpec("tax_number", "Tax Number"),
                FieldSpec("opening_balance", "Opening Balance", "0"),
            ],
            submit_label="Save Supplier",
            on_submit=self._service.add_supplier,
            on_success=table.refresh,
        )
        layout = QHBoxLayout(page)
        layout.addWidget(table, stretch=3)
        layout.addWidget(form, stretch=1)
        return page
