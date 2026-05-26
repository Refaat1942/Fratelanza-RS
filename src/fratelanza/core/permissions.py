"""Role and permission definitions used by the UI and services."""

from __future__ import annotations

from enum import StrEnum


class Permission(StrEnum):
    """Named permissions for commercial modules."""

    DASHBOARD_VIEW = "dashboard.view"
    USERS_MANAGE = "users.manage"
    SALES_VIEW = "sales.view"
    SALES_CREATE = "sales.create"
    SALES_RETURN = "sales.return"
    INVENTORY_VIEW = "inventory.view"
    INVENTORY_MANAGE = "inventory.manage"
    FINANCE_VIEW = "finance.view"
    FINANCE_MANAGE = "finance.manage"
    CRM_VIEW = "crm.view"
    CRM_MANAGE = "crm.manage"
    REPORTS_VIEW = "reports.view"
    SETTINGS_MANAGE = "settings.manage"
    BARCODE_MANAGE = "barcode.manage"


class RoleName(StrEnum):
    """Default reusable role names."""

    ADMIN = "Admin"
    MANAGER = "Manager"
    CASHIER = "Cashier"
    INVENTORY_CLERK = "Inventory Clerk"
    ACCOUNTANT = "Accountant"


DEFAULT_ROLE_PERMISSIONS: dict[RoleName, set[Permission]] = {
    RoleName.ADMIN: set(Permission),
    RoleName.MANAGER: {
        Permission.DASHBOARD_VIEW,
        Permission.SALES_VIEW,
        Permission.SALES_CREATE,
        Permission.SALES_RETURN,
        Permission.INVENTORY_VIEW,
        Permission.INVENTORY_MANAGE,
        Permission.FINANCE_VIEW,
        Permission.CRM_VIEW,
        Permission.CRM_MANAGE,
        Permission.REPORTS_VIEW,
        Permission.BARCODE_MANAGE,
    },
    RoleName.CASHIER: {
        Permission.DASHBOARD_VIEW,
        Permission.SALES_VIEW,
        Permission.SALES_CREATE,
        Permission.SALES_RETURN,
        Permission.CRM_VIEW,
    },
    RoleName.INVENTORY_CLERK: {
        Permission.DASHBOARD_VIEW,
        Permission.INVENTORY_VIEW,
        Permission.INVENTORY_MANAGE,
        Permission.BARCODE_MANAGE,
    },
    RoleName.ACCOUNTANT: {
        Permission.DASHBOARD_VIEW,
        Permission.FINANCE_VIEW,
        Permission.FINANCE_MANAGE,
        Permission.REPORTS_VIEW,
    },
}


def has_permission(assigned_permissions: set[str], required: Permission) -> bool:
    """Check whether a user permission set contains a required permission."""
    return required.value in assigned_permissions
