"""Inventory module UI."""

from __future__ import annotations

from decimal import Decimal

from PyQt6.QtWidgets import QHBoxLayout, QLabel, QLineEdit, QPushButton, QTabWidget, QVBoxLayout, QWidget

from fratelanza.application.inventory_service import InventoryService
from fratelanza.presentation.components.data_table import DataEntryPanel, DataTable, FieldSpec


class InventoryView(QWidget):
    """Products, setup tables, and stock adjustment."""

    def __init__(self, service: InventoryService) -> None:
        super().__init__()
        self._service = service
        self._build()

    def _build(self) -> None:
        tabs = QTabWidget()
        tabs.addTab(self._products_page(), "Products")
        tabs.addTab(self._stock_page(), "Stock In/Out")
        tabs.addTab(self._lookup_page("Categories", self._service.categories, self._service.add_category), "Categories")
        tabs.addTab(self._lookup_page("Brands", self._service.brands, lambda name, desc="": self._service.add_brand(name)), "Brands")
        tabs.addTab(self._units_page(), "Units")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.addWidget(tabs)

    def _products_page(self) -> QWidget:
        page = QWidget()
        table = DataTable(
            title="Products",
            columns=[
                ("ProductId", "ID"),
                ("Sku", "SKU"),
                ("ProductName", "Name"),
                ("ProductCode", "Code"),
                ("Barcode", "Barcode"),
                ("CategoryName", "Category"),
                ("BrandName", "Brand"),
                ("UnitName", "Unit"),
                ("QuantityOnHand", "Stock"),
                ("SalePrice", "Sale Price"),
                ("ReorderLevel", "Alert Level"),
            ],
            load_rows=self._service.products,
        )
        form = DataEntryPanel(
            title="Add Product",
            fields=[
                FieldSpec("sku", "SKU"),
                FieldSpec("product_name", "Name"),
                FieldSpec("category_id", "Category ID", "1"),
                FieldSpec("brand_id", "Brand ID", "optional"),
                FieldSpec("unit_id", "Unit ID", "1"),
                FieldSpec("product_code", "Product Code", "auto if empty"),
                FieldSpec("barcode", "Barcode", "auto if empty"),
                FieldSpec("cost_price", "Cost", "0"),
                FieldSpec("sale_price", "Sale Price", "0"),
                FieldSpec("tax_rate", "Tax %", "0"),
                FieldSpec("quantity_on_hand", "Opening Stock", "0"),
                FieldSpec("reorder_level", "Alert Level", "0"),
                FieldSpec("expiry_date", "Expiry Date", "YYYY-MM-DD"),
            ],
            submit_label="Save Product",
            on_submit=self._service.add_product,
            on_success=table.refresh,
        )
        layout = QHBoxLayout(page)
        layout.addWidget(table, stretch=3)
        layout.addWidget(form, stretch=1)
        return page

    def _stock_page(self) -> QWidget:
        page = QWidget()
        title = QLabel("Stock Adjustment")
        title.setObjectName("Title")
        product_id = QLineEdit()
        product_id.setPlaceholderText("Product ID")
        quantity = QLineEdit()
        quantity.setPlaceholderText("Quantity delta, e.g. 5 or -2")
        notes = QLineEdit()
        notes.setPlaceholderText("Reason / notes")
        save = QPushButton("Apply Stock Movement")
        save.setObjectName("PrimaryButton")
        save.clicked.connect(
            lambda: self._service.adjust_stock(
                int(product_id.text()),
                Decimal(quantity.text()),
                notes.text(),
            )
        )
        layout = QVBoxLayout(page)
        layout.addWidget(title)
        layout.addWidget(product_id)
        layout.addWidget(quantity)
        layout.addWidget(notes)
        layout.addWidget(save)
        layout.addStretch()
        return page

    def _lookup_page(self, title: str, load, add) -> QWidget:
        page = QWidget()
        table = DataTable(
            title=title,
            columns=[("CategoryId", "ID"), ("CategoryName", "Name"), ("Description", "Description")],
            load_rows=lambda search: load(),
            searchable=False,
        )
        if title == "Brands":
            table = DataTable(
                title=title,
                columns=[("BrandId", "ID"), ("BrandName", "Name")],
                load_rows=lambda search: load(),
                searchable=False,
            )
        form = DataEntryPanel(
            title=f"Add {title[:-1]}",
            fields=[FieldSpec("name", "Name"), FieldSpec("description", "Description")],
            submit_label="Save",
            on_submit=lambda values: add(str(values.get("name") or ""), str(values.get("description") or "")),
            on_success=table.refresh,
        )
        layout = QHBoxLayout(page)
        layout.addWidget(table, stretch=3)
        layout.addWidget(form, stretch=1)
        return page

    def _units_page(self) -> QWidget:
        page = QWidget()
        table = DataTable(
            title="Units",
            columns=[("UnitId", "ID"), ("UnitName", "Name"), ("Symbol", "Symbol"), ("AllowsDecimals", "Decimals")],
            load_rows=lambda search: self._service.units(),
            searchable=False,
        )
        form = DataEntryPanel(
            title="Add Unit",
            fields=[
                FieldSpec("name", "Name"),
                FieldSpec("symbol", "Symbol"),
                FieldSpec("allows_decimals", "Allows Decimals", field_type="bool"),
            ],
            submit_label="Save Unit",
            on_submit=lambda values: self._service.add_unit(
                str(values.get("name") or ""),
                str(values.get("symbol") or ""),
                bool(values.get("allows_decimals")),
            ),
            on_success=table.refresh,
        )
        layout = QHBoxLayout(page)
        layout.addWidget(table, stretch=3)
        layout.addWidget(form, stretch=1)
        return page
