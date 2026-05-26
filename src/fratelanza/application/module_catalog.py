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
    title_key: str
    description_key: str


MODULE_CATALOG: tuple[ModuleDefinition, ...] = (
    ModuleDefinition(
        "dashboard",
        "Dashboard",
        "HOME",
        Permission.DASHBOARD_VIEW,
        "Executive overview with sales, stock, cashbox, and alerts.",
        "module.dashboard.title",
        "module.dashboard.description",
    ),
    ModuleDefinition(
        "sales",
        "Sales",
        "POS",
        Permission.SALES_VIEW,
        "Invoices, returns, discounts, taxes, payment methods, and daily reports.",
        "module.sales.title",
        "module.sales.description",
    ),
    ModuleDefinition(
        "inventory",
        "Inventory",
        "BOX",
        Permission.INVENTORY_VIEW,
        "Products, categories, brands, units, stock movement, expiry, and alerts.",
        "module.inventory.title",
        "module.inventory.description",
    ),
    ModuleDefinition(
        "finance",
        "Finance",
        "FIN",
        Permission.FINANCE_VIEW,
        "Expenses, revenues, cashbox, accounts, profit reporting, and dashboards.",
        "module.finance.title",
        "module.finance.description",
    ),
    ModuleDefinition(
        "partners",
        "Customers & Suppliers",
        "CRM",
        Permission.CRM_VIEW,
        "Customer and supplier database, account statements, search, and filters.",
        "module.partners.title",
        "module.partners.description",
    ),
    ModuleDefinition(
        "reports",
        "Reports",
        "RPT",
        Permission.REPORTS_VIEW,
        "Sales, inventory, profit, top products, PDF, and Excel exports.",
        "module.reports.title",
        "module.reports.description",
    ),
    ModuleDefinition(
        "barcodes",
        "Barcodes",
        "BAR",
        Permission.BARCODE_MANAGE,
        "Automatic generation, scanner support, and printable barcode labels.",
        "module.barcodes.title",
        "module.barcodes.description",
    ),
    ModuleDefinition(
        "settings",
        "Settings",
        "SET",
        Permission.SETTINGS_MANAGE,
        "Company, taxes, currency, backup, restore, language, and customization.",
        "module.settings.title",
        "module.settings.description",
    ),
    ModuleDefinition(
        "admin_panel",
        "Admin Panel",
        "ADM",
        Permission.ADMIN_PANEL_MANAGE,
        "VPS connection, licensing, branding, remote control, support, and deployment settings.",
        "module.admin_panel.title",
        "module.admin_panel.description",
    ),
)
