"""Dashboard data repository.

The initial implementation returns KPI placeholders if the database is empty;
future modules can replace the aggregate queries without changing the dashboard
view.
"""

from __future__ import annotations

from fratelanza.domain.entities import DashboardMetric
from fratelanza.infrastructure.repositories.base import SqlServerRepository


class DashboardRepository(SqlServerRepository):
    """Read high-level operational metrics."""

    def get_metrics(self, currency: str) -> list[DashboardMetric]:
        """Return dashboard metrics for the current business day."""
        with self.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    COALESCE(SUM(CASE WHEN CAST(CreatedAt AS date) = CAST(sysutcdatetime() AS date)
                                      THEN GrandTotal ELSE 0 END), 0) AS TodaySales,
                    COUNT(CASE WHEN CAST(CreatedAt AS date) = CAST(sysutcdatetime() AS date)
                               THEN 1 END) AS TodayInvoices
                FROM sales.SalesInvoices
                """
            )
            sales_row = cursor.fetchone()

            cursor.execute(
                """
                SELECT COUNT(*) AS LowStockCount
                FROM inventory.Products
                WHERE IsActive = 1 AND QuantityOnHand <= ReorderLevel
                """
            )
            inventory_row = cursor.fetchone()

        today_sales = sales_row.TodaySales if sales_row else 0
        today_invoices = sales_row.TodayInvoices if sales_row else 0
        low_stock = inventory_row.LowStockCount if inventory_row else 0
        return [
            DashboardMetric("Today Sales", f"{today_sales:,.2f} {currency}", "Revenue today", "#55d6be"),
            DashboardMetric("Invoices", str(today_invoices), "Invoices created today", "#8ab4ff"),
            DashboardMetric("Low Stock", str(low_stock), "Products requiring attention", "#ffbd59"),
            DashboardMetric("Profit", "Ready", "Profit analytics module", "#ff6f91"),
        ]
