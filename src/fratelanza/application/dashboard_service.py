"""Dashboard use cases."""

from __future__ import annotations

from fratelanza.domain.entities import DashboardMetric
from fratelanza.infrastructure.repositories.dashboard_repository import DashboardRepository


class DashboardService:
    """Provide dashboard view models."""

    def __init__(self, dashboard_repository: DashboardRepository, currency: str) -> None:
        self._dashboard_repository = dashboard_repository
        self._currency = currency

    def metrics(self) -> list[DashboardMetric]:
        """Return dashboard metrics."""
        return self._dashboard_repository.get_metrics(self._currency)
