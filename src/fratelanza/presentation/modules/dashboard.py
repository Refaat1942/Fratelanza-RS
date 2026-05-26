"""Dashboard module view."""

from __future__ import annotations

import logging

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QFrame, QGridLayout, QLabel, QVBoxLayout, QWidget

from fratelanza.application.dashboard_service import DashboardService
from fratelanza.domain.entities import DashboardMetric
from fratelanza.presentation.components.metric_card import MetricCard

logger = logging.getLogger(__name__)


class DashboardView(QWidget):
    """Executive dashboard with reusable KPI cards."""

    def __init__(self, dashboard_service: DashboardService) -> None:
        super().__init__()
        self._dashboard_service = dashboard_service
        self._build()

    def _build(self) -> None:
        title = QLabel("Business Dashboard")
        title.setObjectName("Title")

        subtitle = QLabel(
            "Sales, inventory, finance, customer, supplier, and alert analytics in one place."
        )
        subtitle.setObjectName("Muted")
        subtitle.setWordWrap(True)

        grid = QGridLayout()
        grid.setSpacing(16)
        for index, metric in enumerate(self._load_metrics()):
            grid.addWidget(MetricCard(metric), index // 2, index % 2)

        chart_card = QFrame()
        chart_card.setObjectName("Card")
        chart_card.setMinimumHeight(260)
        chart_title = QLabel("Analytics Workspace")
        chart_title.setObjectName("SectionTitle")
        chart_hint = QLabel(
            "Charts are wired through the dashboard service and ready for sales trends, "
            "top products, cashbox movement, and profit visualization."
        )
        chart_hint.setObjectName("Muted")
        chart_hint.setWordWrap(True)
        chart_hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        chart_layout = QVBoxLayout(chart_card)
        chart_layout.setContentsMargins(24, 24, 24, 24)
        chart_layout.addWidget(chart_title)
        chart_layout.addStretch()
        chart_layout.addWidget(chart_hint)
        chart_layout.addStretch()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(18)
        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addLayout(grid)
        layout.addWidget(chart_card)

    def _load_metrics(self) -> list[DashboardMetric]:
        try:
            return self._dashboard_service.metrics()
        except Exception:
            logger.exception("Failed to load dashboard metrics.")
            return [
                DashboardMetric("Today Sales", "Offline", "Connect SQL Server to load sales.", "#55d6be"),
                DashboardMetric("Invoices", "Offline", "Invoice analytics pending connection.", "#8ab4ff"),
                DashboardMetric("Low Stock", "Offline", "Inventory alerts pending connection.", "#ffbd59"),
                DashboardMetric("Profit", "Offline", "Profit dashboard pending connection.", "#ff6f91"),
            ]
