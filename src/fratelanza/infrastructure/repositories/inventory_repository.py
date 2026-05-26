"""Inventory repositories."""

from __future__ import annotations

from decimal import Decimal

from fratelanza.infrastructure.repositories.base import SqlServerRepository


class InventoryRepository(SqlServerRepository):
    """CRUD operations for products and inventory setup tables."""

    def list_categories(self) -> list[dict[str, object]]:
        return self.fetch_all(
            """
            SELECT CategoryId, CategoryName, Description, IsActive
            FROM inventory.Categories
            ORDER BY CategoryName
            """
        )

    def add_category(self, name: str, description: str = "") -> None:
        self.execute(
            "INSERT INTO inventory.Categories (CategoryName, Description) VALUES (?, ?)",
            name,
            description,
        )

    def list_brands(self) -> list[dict[str, object]]:
        return self.fetch_all(
            "SELECT BrandId, BrandName, IsActive FROM inventory.Brands ORDER BY BrandName"
        )

    def add_brand(self, name: str) -> None:
        self.execute("INSERT INTO inventory.Brands (BrandName) VALUES (?)", name)

    def list_units(self) -> list[dict[str, object]]:
        return self.fetch_all(
            """
            SELECT UnitId, UnitName, Symbol, AllowsDecimals
            FROM inventory.Units
            ORDER BY UnitName
            """
        )

    def add_unit(self, name: str, symbol: str, allows_decimals: bool = False) -> None:
        self.execute(
            "INSERT INTO inventory.Units (UnitName, Symbol, AllowsDecimals) VALUES (?, ?, ?)",
            name,
            symbol,
            allows_decimals,
        )

    def list_products(self, search: str = "") -> list[dict[str, object]]:
        like = f"%{search}%"
        return self.fetch_all(
            """
            SELECT
                p.ProductId,
                p.Sku,
                p.ProductName,
                p.ProductCode,
                p.Barcode,
                c.CategoryName,
                b.BrandName,
                u.UnitName,
                p.CostPrice,
                p.SalePrice,
                p.TaxRate,
                p.QuantityOnHand,
                p.ReorderLevel,
                p.ExpiryDate,
                p.IsActive
            FROM inventory.Products p
            INNER JOIN inventory.Categories c ON c.CategoryId = p.CategoryId
            LEFT JOIN inventory.Brands b ON b.BrandId = p.BrandId
            INNER JOIN inventory.Units u ON u.UnitId = p.UnitId
            WHERE p.IsActive = 1
              AND (? = '' OR p.ProductName LIKE ? OR p.Sku LIKE ? OR p.Barcode LIKE ?)
            ORDER BY p.ProductName
            """,
            search,
            like,
            like,
            like,
        )

    def next_product_sequence(self) -> int:
        row = self.fetch_one("SELECT COUNT(*) + 1 AS NextNumber FROM inventory.Products")
        return int(row["NextNumber"]) if row else 1

    def add_product(
        self,
        *,
        category_id: int,
        brand_id: int | None,
        unit_id: int,
        sku: str,
        product_name: str,
        product_code: str,
        barcode: str | None,
        cost_price: Decimal,
        sale_price: Decimal,
        tax_rate: Decimal,
        quantity_on_hand: Decimal,
        reorder_level: Decimal,
        expiry_date: str | None,
    ) -> None:
        self.execute(
            """
            INSERT INTO inventory.Products
                (CategoryId, BrandId, UnitId, Sku, ProductName, ProductCode, Barcode,
                 CostPrice, SalePrice, TaxRate, QuantityOnHand, ReorderLevel, ExpiryDate)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            category_id,
            brand_id,
            unit_id,
            sku,
            product_name,
            product_code,
            barcode,
            cost_price,
            sale_price,
            tax_rate,
            quantity_on_hand,
            reorder_level,
            expiry_date or None,
        )

    def adjust_stock(self, product_id: int, quantity_delta: Decimal, notes: str) -> None:
        movement_type = "adjustment_in" if quantity_delta >= 0 else "adjustment_out"
        with self._connection_factory.connect() as connection:
            cursor = connection.cursor()
            cursor.execute(
                """
                UPDATE inventory.Products
                SET QuantityOnHand = QuantityOnHand + ?, UpdatedAt = sysutcdatetime()
                WHERE ProductId = ?
                """,
                quantity_delta,
                product_id,
            )
            cursor.execute(
                """
                INSERT INTO inventory.StockMovements
                    (ProductId, MovementType, Quantity, Notes)
                VALUES (?, ?, ?, ?)
                """,
                product_id,
                movement_type,
                abs(quantity_delta),
                notes,
            )

    def set_barcode(self, product_id: int, barcode: str) -> None:
        self.execute(
            "UPDATE inventory.Products SET Barcode = ?, UpdatedAt = sysutcdatetime() WHERE ProductId = ?",
            barcode,
            product_id,
        )
