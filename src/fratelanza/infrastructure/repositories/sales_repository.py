"""Sales repositories."""

from __future__ import annotations

from decimal import Decimal

from fratelanza.infrastructure.repositories.base import SqlServerRepository


class SalesRepository(SqlServerRepository):
    """Sales invoice operations."""

    def list_invoices(self) -> list[dict[str, object]]:
        return self.fetch_all(
            """
            SELECT TOP 200 i.SalesInvoiceId, i.InvoiceNumber, c.FullName AS CustomerName,
                   i.InvoiceStatus, i.Subtotal, i.DiscountTotal, i.TaxTotal,
                   i.GrandTotal, i.PaidTotal, i.CreatedAt
            FROM sales.SalesInvoices i
            LEFT JOIN crm.Customers c ON c.CustomerId = i.CustomerId
            ORDER BY i.CreatedAt DESC
            """
        )

    def next_invoice_number(self) -> str:
        row = self.fetch_one(
            """
            SELECT COUNT(*) + 1 AS NextNumber
            FROM sales.SalesInvoices
            WHERE CAST(CreatedAt AS date) = CAST(sysutcdatetime() AS date)
            """
        )
        return f"INV-{int(row['NextNumber']):06d}" if row else "INV-000001"

    def create_invoice(
        self,
        *,
        invoice_number: str,
        customer_id: int | None,
        user_id: int | None,
        payment_method: str,
        subtotal: Decimal,
        discount_total: Decimal,
        tax_total: Decimal,
        grand_total: Decimal,
        paid_total: Decimal,
        notes: str,
        lines: list[dict[str, object]],
    ) -> int:
        with self._connection_factory.connect() as connection:
            cursor = connection.cursor()
            cursor.execute(
                """
                INSERT INTO sales.SalesInvoices
                    (InvoiceNumber, CustomerId, InvoiceStatus, Subtotal, DiscountTotal,
                     TaxTotal, GrandTotal, PaidTotal, Notes, CreatedByUserId)
                OUTPUT INSERTED.SalesInvoiceId
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                """,
                invoice_number,
                customer_id,
                "paid" if paid_total >= grand_total else "partially_paid",
                subtotal,
                discount_total,
                tax_total,
                grand_total,
                paid_total,
                notes,
                user_id,
            )
            invoice_id = int(cursor.fetchone()[0])
            for line in lines:
                cursor.execute(
                    """
                    INSERT INTO sales.SalesInvoiceItems
                        (SalesInvoiceId, ProductId, Quantity, UnitPrice, DiscountAmount,
                         TaxAmount, LineTotal)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    invoice_id,
                    line["product_id"],
                    line["quantity"],
                    line["unit_price"],
                    line["discount_amount"],
                    line["tax_amount"],
                    line["line_total"],
                )
                cursor.execute(
                    """
                    UPDATE inventory.Products
                    SET QuantityOnHand = QuantityOnHand - ?, UpdatedAt = sysutcdatetime()
                    WHERE ProductId = ?
                    """,
                    line["quantity"],
                    line["product_id"],
                )
                cursor.execute(
                    """
                    INSERT INTO inventory.StockMovements
                        (ProductId, MovementType, Quantity, ReferenceType, ReferenceId, Notes)
                    VALUES (?, 'sale', ?, 'sales_invoice', ?, ?)
                    """,
                    line["product_id"],
                    line["quantity"],
                    invoice_id,
                    invoice_number,
                )

            cursor.execute(
                """
                INSERT INTO sales.SalesPayments
                    (SalesInvoiceId, PaymentMethod, Amount)
                VALUES (?, ?, ?)
                """,
                invoice_id,
                payment_method,
                paid_total,
            )
            return invoice_id
