"""Reporting repositories."""

from __future__ import annotations

from fratelanza.infrastructure.repositories.base import SqlServerRepository


class ReportsRepository(SqlServerRepository):
    """Read aggregate data for operational reports."""

    def summary(self) -> dict[str, object]:
        row = self.fetch_one(
            """
            SELECT
                (SELECT COALESCE(SUM(GrandTotal), 0) FROM sales.SalesInvoices) AS SalesTotal,
                (SELECT COALESCE(SUM(Amount), 0) FROM finance.Expenses) AS ExpenseTotal,
                (SELECT COALESCE(SUM(Amount), 0) FROM finance.Revenues) AS RevenueTotal,
                (SELECT COUNT(*) FROM inventory.Products WHERE IsActive = 1) AS ProductCount,
                (SELECT COUNT(*) FROM crm.Customers WHERE IsActive = 1) AS CustomerCount,
                (SELECT COUNT(*) FROM inventory.Products
                 WHERE IsActive = 1 AND QuantityOnHand <= ReorderLevel) AS LowStockCount
            """
        )
        return row or {}

    def top_products(self) -> list[dict[str, object]]:
        return self.fetch_all(
            """
            SELECT TOP 20 p.ProductName, SUM(i.Quantity) AS QuantitySold,
                   SUM(i.LineTotal) AS SalesTotal
            FROM sales.SalesInvoiceItems i
            INNER JOIN inventory.Products p ON p.ProductId = i.ProductId
            GROUP BY p.ProductName
            ORDER BY SUM(i.Quantity) DESC
            """
        )

    def low_stock(self) -> list[dict[str, object]]:
        return self.fetch_all(
            """
            SELECT ProductId, Sku, ProductName, QuantityOnHand, ReorderLevel
            FROM inventory.Products
            WHERE IsActive = 1 AND QuantityOnHand <= ReorderLevel
            ORDER BY QuantityOnHand ASC
            """
        )
