"""Finance use cases."""

from __future__ import annotations

from decimal import Decimal

from fratelanza.infrastructure.repositories.finance_repository import FinanceRepository


class FinanceService:
    """Coordinate cashbox, expense, and revenue workflows."""

    def __init__(self, repository: FinanceRepository) -> None:
        self._repository = repository

    def cashboxes(self) -> list[dict[str, object]]:
        return self._repository.list_cashboxes()

    def expense_categories(self) -> list[dict[str, object]]:
        categories = self._repository.list_expense_categories()
        if not categories:
            self._repository.add_expense_category("General")
            categories = self._repository.list_expense_categories()
        return categories

    def add_expense_category(self, name: str) -> None:
        self._repository.add_expense_category(name.strip())

    def expenses(self) -> list[dict[str, object]]:
        return self._repository.list_expenses()

    def add_expense(self, values: dict[str, object], user_id: int | None) -> None:
        self._repository.add_expense(
            category_id=int(values.get("category_id") or 1),
            cashbox_id=_optional_int(values.get("cashbox_id")),
            amount=Decimal(str(values.get("amount") or "0")),
            expense_date=str(values.get("date") or "").strip(),
            description=str(values.get("description") or "").strip(),
            user_id=user_id,
        )

    def revenues(self) -> list[dict[str, object]]:
        return self._repository.list_revenues()

    def add_revenue(self, values: dict[str, object], user_id: int | None) -> None:
        self._repository.add_revenue(
            cashbox_id=_optional_int(values.get("cashbox_id")),
            amount=Decimal(str(values.get("amount") or "0")),
            revenue_date=str(values.get("date") or "").strip(),
            source_name=str(values.get("source") or "").strip(),
            description=str(values.get("description") or "").strip(),
            user_id=user_id,
        )


def _optional_int(value: object) -> int | None:
    text = str(value or "").strip()
    return int(text) if text else None
