"""Reports module UI."""

from __future__ import annotations

from PyQt6.QtWidgets import QGridLayout, QLabel, QPushButton, QTabWidget, QVBoxLayout, QWidget

from fratelanza.application.reports_service import ReportsService
from fratelanza.domain.entities import DashboardMetric
from fratelanza.presentation.components.data_table import DataTable
from fratelanza.presentation.components.metric_card import MetricCard


class ReportsView(QWidget):
    """Operational reports and analytics."""

    def __init__(self, service: ReportsService, currency: str) -> None:
        super().__init__()
        self._service = service
        self._currency = currency
        self._cards = QGridLayout()
        self._build()
        self.refresh()

    def _build(self) -> None:
        title = QLabel("Reports & Analytics")
        title.setObjectName("Title")
        refresh = QPushButton("Refresh Reports")
        refresh.clicked.connect(self.refresh)

        tabs = QTabWidget()
        tabs.addTab(
            DataTable(
                title="Top Selling Products",
                columns=[
                    ("ProductName", "Product"),
                    ("QuantitySold", "Quantity Sold"),
                    ("SalesTotal", "Sales Total"),
                ],
                load_rows=lambda search: self._service.top_products(),
                searchable=False,
            ),
            "Top Products",
        )
        tabs.addTab(
            DataTable(
                title="Inventory Alerts",
                columns=[
                    ("ProductId", "ID"),
                    ("Sku", "SKU"),
                    ("ProductName", "Product"),
                    ("QuantityOnHand", "Stock"),
                    ("ReorderLevel", "Alert Level"),
                ],
                load_rows=lambda search: self._service.low_stock(),
                searchable=False,
            ),
            "Low Stock",
        )

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.addWidget(title)
        layout.addWidget(refresh)
        layout.addLayout(self._cards)
        layout.addWidget(tabs)

    def refresh(self) -> None:
        """Refresh summary cards."""
        while self._cards.count():
            item = self._cards.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        summary = self._service.summary()
        metrics = [
            DashboardMetric(
                "Sales",
                f"{summary.get('SalesTotal', 0):,.2f} {self._currency}",
                "Total sales invoices",
                "#55d6be",
            ),
            DashboardMetric(
                "Expenses",
                f"{summary.get('ExpenseTotal', 0):,.2f} {self._currency}",
                "Total expenses",
                "#ff6f91",
            ),
            DashboardMetric(
                "Products",
                str(summary.get("ProductCount", 0)),
                "Active products",
                "#8ab4ff",
            ),
            DashboardMetric(
                "Low Stock",
                str(summary.get("LowStockCount", 0)),
                "Products below alert level",
                "#ffbd59",
            ),
        ]
        for index, metric in enumerate(metrics):
            self._cards.addWidget(MetricCard(metric), index // 2, index % 2)
