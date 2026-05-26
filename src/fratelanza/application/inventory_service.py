"""Inventory use cases."""

from __future__ import annotations

from decimal import Decimal

from fratelanza.application.barcode_service import BarcodeService
from fratelanza.infrastructure.repositories.inventory_repository import InventoryRepository


class InventoryService:
    """Coordinate product, lookup, and stock operations."""

    def __init__(self, repository: InventoryRepository, barcode_service: BarcodeService) -> None:
        self._repository = repository
        self._barcode_service = barcode_service

    def categories(self) -> list[dict[str, object]]:
        return self._repository.list_categories()

    def add_category(self, name: str, description: str = "") -> None:
        self._repository.add_category(name.strip(), description.strip())

    def brands(self) -> list[dict[str, object]]:
        return self._repository.list_brands()

    def add_brand(self, name: str) -> None:
        self._repository.add_brand(name.strip())

    def units(self) -> list[dict[str, object]]:
        return self._repository.list_units()

    def add_unit(self, name: str, symbol: str, allows_decimals: bool = False) -> None:
        self._repository.add_unit(name.strip(), symbol.strip(), allows_decimals)

    def products(self, search: str = "") -> list[dict[str, object]]:
        return self._repository.list_products(search.strip())

    def add_product(self, values: dict[str, object]) -> None:
        product_id_seed = int(values.get("product_id_seed") or 1)
        category_id = int(values.get("category_id") or 1)
        product_code = str(values.get("product_code") or "").strip()
        if not product_code:
            product_code = self._barcode_service.generate_product_code("GEN", product_id_seed)
        barcode = str(values.get("barcode") or "").strip() or None
        if not barcode:
            barcode = self._barcode_service.generate_ean13(product_id_seed)
        self._repository.add_product(
            category_id=category_id,
            brand_id=_optional_int(values.get("brand_id")),
            unit_id=int(values.get("unit_id") or 1),
            sku=str(values.get("sku") or "").strip(),
            product_name=str(values.get("product_name") or "").strip(),
            product_code=product_code,
            barcode=barcode,
            cost_price=_decimal(values.get("cost_price")),
            sale_price=_decimal(values.get("sale_price")),
            tax_rate=_decimal(values.get("tax_rate")),
            quantity_on_hand=_decimal(values.get("quantity_on_hand")),
            reorder_level=_decimal(values.get("reorder_level")),
            expiry_date=str(values.get("expiry_date") or "").strip() or None,
        )

    def adjust_stock(self, product_id: int, quantity_delta: Decimal, notes: str) -> None:
        self._repository.adjust_stock(product_id, quantity_delta, notes)

    def set_barcode(self, product_id: int, barcode: str) -> None:
        self._repository.set_barcode(product_id, barcode)


def _decimal(value: object) -> Decimal:
    return Decimal(str(value or "0"))


def _optional_int(value: object) -> int | None:
    text = str(value or "").strip()
    return int(text) if text else None
