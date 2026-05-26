"""Sales use cases."""

from __future__ import annotations

from decimal import Decimal

from fratelanza.infrastructure.repositories.inventory_repository import InventoryRepository
from fratelanza.infrastructure.repositories.partner_repository import PartnerRepository
from fratelanza.infrastructure.repositories.sales_repository import SalesRepository


class SalesService:
    """Coordinate invoice creation and sales history."""

    def __init__(
        self,
        sales_repository: SalesRepository,
        inventory_repository: InventoryRepository,
        partner_repository: PartnerRepository,
    ) -> None:
        self._sales_repository = sales_repository
        self._inventory_repository = inventory_repository
        self._partner_repository = partner_repository

    def invoices(self) -> list[dict[str, object]]:
        return self._sales_repository.list_invoices()

    def products(self) -> list[dict[str, object]]:
        return self._inventory_repository.list_products()

    def customers(self) -> list[dict[str, object]]:
        return self._partner_repository.list_customers()

    def next_invoice_number(self) -> str:
        return self._sales_repository.next_invoice_number()

    def create_invoice(
        self,
        *,
        customer_id: int | None,
        payment_method: str,
        discount_total: Decimal,
        paid_total: Decimal,
        notes: str,
        user_id: int | None,
        lines: list[dict[str, object]],
    ) -> int:
        subtotal = sum(Decimal(str(line["quantity"])) * Decimal(str(line["unit_price"])) for line in lines)
        tax_total = sum(Decimal(str(line["tax_amount"])) for line in lines)
        grand_total = subtotal - discount_total + tax_total
        prepared_lines = []
        for line in lines:
            quantity = Decimal(str(line["quantity"]))
            unit_price = Decimal(str(line["unit_price"]))
            line_discount = Decimal(str(line.get("discount_amount") or "0"))
            tax_amount = Decimal(str(line.get("tax_amount") or "0"))
            prepared_lines.append(
                {
                    "product_id": int(line["product_id"]),
                    "quantity": quantity,
                    "unit_price": unit_price,
                    "discount_amount": line_discount,
                    "tax_amount": tax_amount,
                    "line_total": quantity * unit_price - line_discount + tax_amount,
                }
            )
        return self._sales_repository.create_invoice(
            invoice_number=self.next_invoice_number(),
            customer_id=customer_id,
            user_id=user_id,
            payment_method=payment_method,
            subtotal=subtotal,
            discount_total=discount_total,
            tax_total=tax_total,
            grand_total=grand_total,
            paid_total=paid_total,
            notes=notes,
            lines=prepared_lines,
        )
