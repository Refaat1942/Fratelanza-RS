"""Cloud repository adapter for EXE-only VPS deployments.

The application services use repository-like objects. This adapter implements
the same method names as the SQL repositories but forwards calls to the VPS API.
"""

from __future__ import annotations

from collections.abc import Sequence
from decimal import Decimal

from fratelanza.application.cloud_api_client import CloudApiClient


class CloudBusinessRepository:
    """Repository facade backed by the Fratelanza VPS API."""

    def __init__(self, client: CloudApiClient) -> None:
        self._client = client

    # Dashboard / reports
    def get_metrics(self, currency: str) -> list[object]:
        from fratelanza.domain.entities import DashboardMetric

        summary = self.summary()
        return [
            DashboardMetric("Today Sales", f"{summary.get('TodaySales', 0):,.2f} {currency}", "Revenue today", "#55d6be"),
            DashboardMetric("Invoices", str(summary.get("TodayInvoices", 0)), "Invoices created today", "#8ab4ff"),
            DashboardMetric("Low Stock", str(summary.get("LowStockCount", 0)), "Products requiring attention", "#ffbd59"),
            DashboardMetric("Profit", f"{summary.get('Profit', 0):,.2f} {currency}", "Estimated profit", "#ff6f91"),
        ]

    def summary(self) -> dict[str, object]:
        return self._client.request("GET", "/business/reports/summary")

    def top_products(self) -> list[dict[str, object]]:
        return self._client.request("GET", "/business/reports/top-products")

    def low_stock(self) -> list[dict[str, object]]:
        return self._client.request("GET", "/business/reports/low-stock")

    # Inventory
    def list_categories(self) -> list[dict[str, object]]:
        return self._client.request("GET", "/business/categories")

    def add_category(self, name: str, description: str = "") -> None:
        self._client.request("POST", "/business/categories", {"name": name, "description": description})

    def list_brands(self) -> list[dict[str, object]]:
        return self._client.request("GET", "/business/brands")

    def add_brand(self, name: str) -> None:
        self._client.request("POST", "/business/brands", {"name": name})

    def list_units(self) -> list[dict[str, object]]:
        return self._client.request("GET", "/business/units")

    def add_unit(self, name: str, symbol: str, allows_decimals: bool = False) -> None:
        self._client.request(
            "POST",
            "/business/units",
            {"name": name, "symbol": symbol, "allows_decimals": allows_decimals},
        )

    def list_products(self, search: str = "") -> list[dict[str, object]]:
        return self._client.request("GET", "/business/products", query={"search": search})

    def next_product_sequence(self) -> int:
        payload = self._client.request("GET", "/business/products/next-sequence")
        return int(payload["next_sequence"])

    def add_product(self, **values: object) -> None:
        self._client.request("POST", "/business/products", _json_ready(values))

    def adjust_stock(self, product_id: int, quantity_delta: Decimal, notes: str) -> None:
        self._client.request(
            "POST",
            "/business/stock-adjustments",
            {"product_id": product_id, "quantity_delta": str(quantity_delta), "notes": notes},
        )

    def set_barcode(self, product_id: int, barcode: str) -> None:
        self._client.request("POST", f"/business/products/{product_id}/barcode", {"barcode": barcode})

    # Partners
    def list_customers(self, search: str = "") -> list[dict[str, object]]:
        return self._client.request("GET", "/business/customers", query={"search": search})

    def add_customer(self, **values: object) -> None:
        self._client.request("POST", "/business/customers", _json_ready(values))

    def list_suppliers(self, search: str = "") -> list[dict[str, object]]:
        return self._client.request("GET", "/business/suppliers", query={"search": search})

    def add_supplier(self, **values: object) -> None:
        self._client.request("POST", "/business/suppliers", _json_ready(values))

    # Finance
    def list_cashboxes(self) -> list[dict[str, object]]:
        return self._client.request("GET", "/business/cashboxes")

    def list_expense_categories(self) -> list[dict[str, object]]:
        return self._client.request("GET", "/business/expense-categories")

    def add_expense_category(self, name: str) -> None:
        self._client.request("POST", "/business/expense-categories", {"name": name})

    def list_expenses(self) -> list[dict[str, object]]:
        return self._client.request("GET", "/business/expenses")

    def add_expense(self, **values: object) -> None:
        self._client.request("POST", "/business/expenses", _json_ready(values))

    def list_revenues(self) -> list[dict[str, object]]:
        return self._client.request("GET", "/business/revenues")

    def add_revenue(self, **values: object) -> None:
        self._client.request("POST", "/business/revenues", _json_ready(values))

    # Sales
    def list_invoices(self) -> list[dict[str, object]]:
        return self._client.request("GET", "/business/invoices")

    def next_invoice_number(self) -> str:
        payload = self._client.request("GET", "/business/invoices/next-number")
        return str(payload["invoice_number"])

    def create_invoice(self, **values: object) -> int:
        payload = self._client.request("POST", "/business/invoices", _json_ready(values))
        return int(payload["invoice_id"])

    # Settings
    def company_profile(self) -> dict[str, object] | None:
        return self._client.request("GET", "/business/settings/company-profile")

    def update_company_profile(self, **values: object) -> None:
        self._client.request("PUT", "/business/settings/company-profile", _json_ready(values))

    def tax_settings(self) -> list[dict[str, object]]:
        return self._client.request("GET", "/business/settings/taxes")

    def add_tax(self, name: str, rate: str, is_default: bool) -> None:
        self._client.request(
            "POST",
            "/business/settings/taxes",
            {"name": name, "rate": rate, "is_default": is_default},
        )


def _json_ready(values: dict[str, object] | Sequence[object]) -> object:
    """Convert Decimals and nested values to JSON-safe primitives."""
    if isinstance(values, dict):
        return {key: _json_ready(value) for key, value in values.items()}
    if isinstance(values, list | tuple):
        return [_json_ready(value) for value in values]
    if isinstance(values, Decimal):
        return str(values)
    return values
