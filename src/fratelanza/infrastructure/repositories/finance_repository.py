"""Finance repositories."""

from __future__ import annotations

from decimal import Decimal

from fratelanza.infrastructure.repositories.base import SqlServerRepository


class FinanceRepository(SqlServerRepository):
    """CRUD operations for expenses, revenues, and cashboxes."""

    def list_cashboxes(self) -> list[dict[str, object]]:
        return self.fetch_all(
            """
            SELECT CashboxId, CashboxName, OpeningBalance, CurrentBalance, IsActive
            FROM finance.Cashboxes
            WHERE IsActive = 1
            ORDER BY CashboxName
            """
        )

    def list_expense_categories(self) -> list[dict[str, object]]:
        return self.fetch_all(
            """
            SELECT ExpenseCategoryId, CategoryName
            FROM finance.ExpenseCategories
            ORDER BY CategoryName
            """
        )

    def add_expense_category(self, name: str) -> None:
        self.execute("INSERT INTO finance.ExpenseCategories (CategoryName) VALUES (?)", name)

    def list_expenses(self) -> list[dict[str, object]]:
        return self.fetch_all(
            """
            SELECT e.ExpenseId, ec.CategoryName, c.CashboxName, e.Amount,
                   e.ExpenseDate, e.Description, e.CreatedAt
            FROM finance.Expenses e
            INNER JOIN finance.ExpenseCategories ec
                ON ec.ExpenseCategoryId = e.ExpenseCategoryId
            LEFT JOIN finance.Cashboxes c ON c.CashboxId = e.CashboxId
            ORDER BY e.ExpenseDate DESC, e.ExpenseId DESC
            """
        )

    def add_expense(
        self,
        *,
        category_id: int,
        cashbox_id: int | None,
        amount: Decimal,
        expense_date: str,
        description: str,
        user_id: int | None,
    ) -> None:
        with self._connection_factory.connect() as connection:
            cursor = connection.cursor()
            cursor.execute(
                """
                INSERT INTO finance.Expenses
                    (ExpenseCategoryId, CashboxId, Amount, ExpenseDate, Description, CreatedByUserId)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                category_id,
                cashbox_id,
                amount,
                expense_date,
                description,
                user_id,
            )
            if cashbox_id is not None:
                cursor.execute(
                    """
                    UPDATE finance.Cashboxes
                    SET CurrentBalance = CurrentBalance - ?
                    WHERE CashboxId = ?
                    """,
                    amount,
                    cashbox_id,
                )

    def list_revenues(self) -> list[dict[str, object]]:
        return self.fetch_all(
            """
            SELECT r.RevenueId, c.CashboxName, r.Amount, r.RevenueDate,
                   r.SourceName, r.Description, r.CreatedAt
            FROM finance.Revenues r
            LEFT JOIN finance.Cashboxes c ON c.CashboxId = r.CashboxId
            ORDER BY r.RevenueDate DESC, r.RevenueId DESC
            """
        )

    def add_revenue(
        self,
        *,
        cashbox_id: int | None,
        amount: Decimal,
        revenue_date: str,
        source_name: str,
        description: str,
        user_id: int | None,
    ) -> None:
        with self._connection_factory.connect() as connection:
            cursor = connection.cursor()
            cursor.execute(
                """
                INSERT INTO finance.Revenues
                    (CashboxId, Amount, RevenueDate, SourceName, Description, CreatedByUserId)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                cashbox_id,
                amount,
                revenue_date,
                source_name,
                description,
                user_id,
            )
            if cashbox_id is not None:
                cursor.execute(
                    """
                    UPDATE finance.Cashboxes
                    SET CurrentBalance = CurrentBalance + ?
                    WHERE CashboxId = ?
                    """,
                    amount,
                    cashbox_id,
                )
