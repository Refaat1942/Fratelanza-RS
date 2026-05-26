"""Finance module UI."""

from __future__ import annotations

from PyQt6.QtWidgets import QHBoxLayout, QTabWidget, QVBoxLayout, QWidget

from fratelanza.application.finance_service import FinanceService
from fratelanza.presentation.components.data_table import DataEntryPanel, DataTable, FieldSpec


class FinanceView(QWidget):
    """Expenses, revenues, and cashbox overview."""

    def __init__(self, service: FinanceService, user_id: int | None) -> None:
        super().__init__()
        self._service = service
        self._user_id = user_id
        self._build()

    def _build(self) -> None:
        tabs = QTabWidget()
        tabs.addTab(self._expenses_page(), "Expenses")
        tabs.addTab(self._revenues_page(), "Revenues")
        tabs.addTab(self._cashboxes_page(), "Cashboxes")
        tabs.addTab(self._expense_categories_page(), "Expense Categories")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.addWidget(tabs)

    def _expenses_page(self) -> QWidget:
        page = QWidget()
        table = DataTable(
            title="Expenses",
            columns=[
                ("ExpenseId", "ID"),
                ("CategoryName", "Category"),
                ("CashboxName", "Cashbox"),
                ("Amount", "Amount"),
                ("ExpenseDate", "Date"),
                ("Description", "Description"),
            ],
            load_rows=lambda search: self._service.expenses(),
            searchable=False,
        )
        form = DataEntryPanel(
            title="Add Expense",
            fields=[
                FieldSpec("category_id", "Category ID", "1"),
                FieldSpec("cashbox_id", "Cashbox ID", "1"),
                FieldSpec("amount", "Amount", "0"),
                FieldSpec("date", "Date", "YYYY-MM-DD"),
                FieldSpec("description", "Description"),
            ],
            submit_label="Save Expense",
            on_submit=lambda values: self._service.add_expense(values, self._user_id),
            on_success=table.refresh,
        )
        layout = QHBoxLayout(page)
        layout.addWidget(table, stretch=3)
        layout.addWidget(form, stretch=1)
        return page

    def _revenues_page(self) -> QWidget:
        page = QWidget()
        table = DataTable(
            title="Revenues",
            columns=[
                ("RevenueId", "ID"),
                ("CashboxName", "Cashbox"),
                ("Amount", "Amount"),
                ("RevenueDate", "Date"),
                ("SourceName", "Source"),
                ("Description", "Description"),
            ],
            load_rows=lambda search: self._service.revenues(),
            searchable=False,
        )
        form = DataEntryPanel(
            title="Add Revenue",
            fields=[
                FieldSpec("cashbox_id", "Cashbox ID", "1"),
                FieldSpec("amount", "Amount", "0"),
                FieldSpec("date", "Date", "YYYY-MM-DD"),
                FieldSpec("source", "Source"),
                FieldSpec("description", "Description"),
            ],
            submit_label="Save Revenue",
            on_submit=lambda values: self._service.add_revenue(values, self._user_id),
            on_success=table.refresh,
        )
        layout = QHBoxLayout(page)
        layout.addWidget(table, stretch=3)
        layout.addWidget(form, stretch=1)
        return page

    def _cashboxes_page(self) -> QWidget:
        page = QWidget()
        table = DataTable(
            title="Cashboxes",
            columns=[
                ("CashboxId", "ID"),
                ("CashboxName", "Name"),
                ("OpeningBalance", "Opening"),
                ("CurrentBalance", "Current"),
            ],
            load_rows=lambda search: self._service.cashboxes(),
            searchable=False,
        )
        layout = QVBoxLayout(page)
        layout.addWidget(table)
        return page

    def _expense_categories_page(self) -> QWidget:
        page = QWidget()
        table = DataTable(
            title="Expense Categories",
            columns=[("ExpenseCategoryId", "ID"), ("CategoryName", "Name")],
            load_rows=lambda search: self._service.expense_categories(),
            searchable=False,
        )
        form = DataEntryPanel(
            title="Add Expense Category",
            fields=[FieldSpec("name", "Name")],
            submit_label="Save",
            on_submit=lambda values: self._service.add_expense_category(str(values.get("name") or "")),
            on_success=table.refresh,
        )
        layout = QHBoxLayout(page)
        layout.addWidget(table, stretch=3)
        layout.addWidget(form, stretch=1)
        return page
