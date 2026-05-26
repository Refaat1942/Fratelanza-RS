"""Customer and supplier repositories."""

from __future__ import annotations

from decimal import Decimal

from fratelanza.infrastructure.repositories.base import SqlServerRepository


class PartnerRepository(SqlServerRepository):
    """CRUD operations for customers and suppliers."""

    def list_customers(self, search: str = "") -> list[dict[str, object]]:
        like = f"%{search}%"
        return self.fetch_all(
            """
            SELECT CustomerId, CustomerCode, FullName, Phone, Email, AddressLine,
                   TaxNumber, CreditLimit, OpeningBalance, IsActive
            FROM crm.Customers
            WHERE IsActive = 1
              AND (? = '' OR CustomerCode LIKE ? OR FullName LIKE ? OR Phone LIKE ?)
            ORDER BY FullName
            """,
            search,
            like,
            like,
            like,
        )

    def add_customer(
        self,
        *,
        code: str,
        name: str,
        phone: str,
        email: str,
        address: str,
        tax_number: str,
        credit_limit: Decimal,
        opening_balance: Decimal,
    ) -> None:
        self.execute(
            """
            INSERT INTO crm.Customers
                (CustomerCode, FullName, Phone, Email, AddressLine, TaxNumber,
                 CreditLimit, OpeningBalance)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            code,
            name,
            phone,
            email,
            address,
            tax_number,
            credit_limit,
            opening_balance,
        )

    def list_suppliers(self, search: str = "") -> list[dict[str, object]]:
        like = f"%{search}%"
        return self.fetch_all(
            """
            SELECT SupplierId, SupplierCode, SupplierName, ContactPerson, Phone, Email,
                   AddressLine, TaxNumber, OpeningBalance, IsActive
            FROM crm.Suppliers
            WHERE IsActive = 1
              AND (? = '' OR SupplierCode LIKE ? OR SupplierName LIKE ? OR Phone LIKE ?)
            ORDER BY SupplierName
            """,
            search,
            like,
            like,
            like,
        )

    def add_supplier(
        self,
        *,
        code: str,
        name: str,
        contact_person: str,
        phone: str,
        email: str,
        address: str,
        tax_number: str,
        opening_balance: Decimal,
    ) -> None:
        self.execute(
            """
            INSERT INTO crm.Suppliers
                (SupplierCode, SupplierName, ContactPerson, Phone, Email,
                 AddressLine, TaxNumber, OpeningBalance)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            code,
            name,
            contact_person,
            phone,
            email,
            address,
            tax_number,
            opening_balance,
        )
