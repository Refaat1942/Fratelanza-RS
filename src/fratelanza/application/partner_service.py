"""Customer and supplier use cases."""

from __future__ import annotations

from decimal import Decimal

from fratelanza.infrastructure.repositories.partner_repository import PartnerRepository


class PartnerService:
    """Manage customers and suppliers."""

    def __init__(self, repository: PartnerRepository) -> None:
        self._repository = repository

    def customers(self, search: str = "") -> list[dict[str, object]]:
        return self._repository.list_customers(search.strip())

    def add_customer(self, values: dict[str, object]) -> None:
        self._repository.add_customer(
            code=str(values.get("code") or "").strip(),
            name=str(values.get("name") or "").strip(),
            phone=str(values.get("phone") or "").strip(),
            email=str(values.get("email") or "").strip(),
            address=str(values.get("address") or "").strip(),
            tax_number=str(values.get("tax_number") or "").strip(),
            credit_limit=Decimal(str(values.get("credit_limit") or "0")),
            opening_balance=Decimal(str(values.get("opening_balance") or "0")),
        )

    def suppliers(self, search: str = "") -> list[dict[str, object]]:
        return self._repository.list_suppliers(search.strip())

    def add_supplier(self, values: dict[str, object]) -> None:
        self._repository.add_supplier(
            code=str(values.get("code") or "").strip(),
            name=str(values.get("name") or "").strip(),
            contact_person=str(values.get("contact_person") or "").strip(),
            phone=str(values.get("phone") or "").strip(),
            email=str(values.get("email") or "").strip(),
            address=str(values.get("address") or "").strip(),
            tax_number=str(values.get("tax_number") or "").strip(),
            opening_balance=Decimal(str(values.get("opening_balance") or "0")),
        )
