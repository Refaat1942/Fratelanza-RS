"""Dashboard metric card widget."""

from __future__ import annotations

from PyQt6.QtWidgets import QFrame, QLabel, QVBoxLayout

from fratelanza.domain.entities import DashboardMetric


class MetricCard(QFrame):
    """Reusable KPI card for dashboards."""

    def __init__(self, metric: DashboardMetric) -> None:
        super().__init__()
        self.setObjectName("Card")
        self.setMinimumHeight(130)

        accent = QFrame()
        accent.setFixedHeight(4)
        accent.setStyleSheet(f"background-color: {metric.accent}; border-radius: 2px;")

        title = QLabel(metric.title)
        title.setObjectName("Muted")

        value = QLabel(metric.value)
        value.setStyleSheet("font-size: 26px; font-weight: 800;")

        subtitle = QLabel(metric.subtitle)
        subtitle.setObjectName("Muted")
        subtitle.setWordWrap(True)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(8)
        layout.addWidget(accent)
        layout.addWidget(title)
        layout.addWidget(value)
        layout.addWidget(subtitle)
        layout.addStretch()
