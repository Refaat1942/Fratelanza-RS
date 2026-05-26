"""Reports use cases."""

from __future__ import annotations

from fratelanza.infrastructure.repositories.reports_repository import ReportsRepository


class ReportsService:
    """Read operational report data."""

    def __init__(self, repository: ReportsRepository) -> None:
        self._repository = repository

    def summary(self) -> dict[str, object]:
        return self._repository.summary()

    def top_products(self) -> list[dict[str, object]]:
        return self._repository.top_products()

    def low_stock(self) -> list[dict[str, object]]:
        return self._repository.low_stock()
