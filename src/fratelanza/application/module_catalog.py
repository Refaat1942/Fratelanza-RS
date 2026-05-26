"""Navigation catalog for the commercial modules."""

from __future__ import annotations

from dataclasses import dataclass

from fratelanza.core.permissions import Permission


@dataclass(frozen=True)
class ModuleDefinition:
    key: str
    title: str
    icon: str
    permission: Permission
    description: str


MODULE_CATALOG: tuple[ModuleDefinition, ...] = (
    ModuleDefinition(
        "dashboard",
        "Dashboard",
        "HOME",
        Permission.DASHBOARD_VIEW,
        "Executive overview with sales, stock, cashbox, and alerts.",
    ),
    ModuleDefinition(
        "sales",
        "Sales",
        "POS",
        Permission.SALES_VIEW,
        "Invoices, returns, discounts, taxes, payment methods, and daily reports.",
    ),
    ModuleDefinition(
        "inventory",
        "Inventory",
        "BOX",
        Permission.INVENTORY_VIEW,
        "Products, categories, brands, units, stock movement, expiry, and alerts.",
    ),
    ModuleDefinition(
        "finance",
        "Finance",
        "FIN",
        Permission.FINANCE_VIEW,
        "Expenses, revenues, cashbox, accounts, profit reporting, and dashboards.",
    ),
    ModuleDefinition(
        "partners",
        "Customers & Suppliers",
        "CRM",
        Permission.CRM_VIEW,
        "Customer and supplier database, account statements, search, and filters.",
    ),
    ModuleDefinition(
        "reports",
        "Reports",
        "RPT",
        Permission.REPORTS_VIEW,
        "Sales, inventory, profit, top products, PDF, and Excel exports.",
    ),
    ModuleDefinition(
        "barcodes",
        "Barcodes",
        "BAR",
        Permission.BARCODE_MANAGE,
        "Automatic generation, scanner support, and printable barcode labels.",
    ),
    ModuleDefinition(
        "settings",
        "Settings",
        "SET",
        Permission.SETTINGS_MANAGE,
        "Company, taxes, currency, backup, restore, language, and customization.",
    ),
)
