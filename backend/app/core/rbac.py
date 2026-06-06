from enum import StrEnum


class SystemRole(StrEnum):
    SUPER_ADMIN = "super_admin"
    COMPANY_ADMIN = "company_admin"
    CEO = "ceo"
    MANAGING_DIRECTOR = "managing_director"
    SALES_DIRECTOR = "sales_director"
    SALES_MANAGER = "sales_manager"
    SALES_AGENT = "sales_agent"
    CUSTOMER_SERVICE = "customer_service"
    COLLECTION_OFFICER = "collection_officer"
    ACCOUNTANT = "accountant"
    FINANCE_MANAGER = "finance_manager"
    PROCUREMENT_OFFICER = "procurement_officer"
    PROJECT_MANAGER = "project_manager"
    ENGINEER = "engineer"
    HR_MANAGER = "hr_manager"
    BROKER = "broker"
    CUSTOMER = "customer"


class Permission(StrEnum):
    PLATFORM_ALL = "platform:all"
    COMPANIES_MANAGE = "companies:manage"
    SUBSCRIPTIONS_MANAGE = "subscriptions:manage"
    USERS_MANAGE = "users:manage"
    PERMISSIONS_MANAGE = "permissions:manage"
    CUSTOMERS_READ = "customers:read"
    CUSTOMERS_WRITE = "customers:write"
    CRM_MANAGE = "crm:manage"
    PROJECTS_MANAGE = "projects:manage"
    UNITS_MANAGE = "units:manage"
    RESERVATIONS_MANAGE = "reservations:manage"
    RESERVATIONS_APPROVE = "reservations:approve"
    CONTRACTS_MANAGE = "contracts:manage"
    CONTRACTS_APPROVE = "contracts:approve"
    COLLECTIONS_MANAGE = "collections:manage"
    BROKERS_MANAGE = "brokers:manage"
    PROPERTY_MANAGE = "property:manage"
    CONSTRUCTION_MANAGE = "construction:manage"
    PROCUREMENT_MANAGE = "procurement:manage"
    WAREHOUSE_MANAGE = "warehouse:manage"
    FINANCE_READ = "finance:read"
    FINANCE_WRITE = "finance:write"
    HR_MANAGE = "hr:manage"
    SERVICE_MANAGE = "service:manage"
    REPORTS_READ = "reports:read"
    EXPORTS_RUN = "exports:run"
    SETTINGS_MANAGE = "settings:manage"
    AUDIT_READ = "audit:read"


ROLE_PERMISSIONS: dict[SystemRole, set[Permission]] = {
    SystemRole.SUPER_ADMIN: set(Permission),
    SystemRole.COMPANY_ADMIN: {
        Permission.USERS_MANAGE,
        Permission.CUSTOMERS_READ,
        Permission.CUSTOMERS_WRITE,
        Permission.CRM_MANAGE,
        Permission.PROJECTS_MANAGE,
        Permission.UNITS_MANAGE,
        Permission.RESERVATIONS_MANAGE,
        Permission.RESERVATIONS_APPROVE,
        Permission.CONTRACTS_MANAGE,
        Permission.CONTRACTS_APPROVE,
        Permission.COLLECTIONS_MANAGE,
        Permission.BROKERS_MANAGE,
        Permission.PROPERTY_MANAGE,
        Permission.CONSTRUCTION_MANAGE,
        Permission.PROCUREMENT_MANAGE,
        Permission.WAREHOUSE_MANAGE,
        Permission.FINANCE_READ,
        Permission.HR_MANAGE,
        Permission.SERVICE_MANAGE,
        Permission.REPORTS_READ,
        Permission.EXPORTS_RUN,
    },
    SystemRole.CEO: {
        Permission.CUSTOMERS_READ,
        Permission.PROJECTS_MANAGE,
        Permission.FINANCE_READ,
        Permission.REPORTS_READ,
        Permission.EXPORTS_RUN,
    },
    SystemRole.MANAGING_DIRECTOR: {
        Permission.CUSTOMERS_READ,
        Permission.CRM_MANAGE,
        Permission.PROJECTS_MANAGE,
        Permission.FINANCE_READ,
        Permission.REPORTS_READ,
    },
    SystemRole.SALES_DIRECTOR: {
        Permission.CUSTOMERS_READ,
        Permission.CUSTOMERS_WRITE,
        Permission.CRM_MANAGE,
        Permission.RESERVATIONS_MANAGE,
        Permission.REPORTS_READ,
    },
    SystemRole.SALES_MANAGER: {
        Permission.CUSTOMERS_READ,
        Permission.CUSTOMERS_WRITE,
        Permission.CRM_MANAGE,
        Permission.RESERVATIONS_MANAGE,
        Permission.REPORTS_READ,
    },
    SystemRole.SALES_AGENT: {
        Permission.CUSTOMERS_READ,
        Permission.CUSTOMERS_WRITE,
        Permission.CRM_MANAGE,
        Permission.RESERVATIONS_MANAGE,
    },
    SystemRole.CUSTOMER_SERVICE: {
        Permission.CUSTOMERS_READ,
        Permission.CUSTOMERS_WRITE,
        Permission.SERVICE_MANAGE,
    },
    SystemRole.COLLECTION_OFFICER: {
        Permission.CUSTOMERS_READ,
        Permission.COLLECTIONS_MANAGE,
    },
    SystemRole.ACCOUNTANT: {
        Permission.FINANCE_READ,
        Permission.FINANCE_WRITE,
        Permission.COLLECTIONS_MANAGE,
    },
    SystemRole.FINANCE_MANAGER: {
        Permission.FINANCE_READ,
        Permission.FINANCE_WRITE,
        Permission.COLLECTIONS_MANAGE,
        Permission.REPORTS_READ,
    },
    SystemRole.PROCUREMENT_OFFICER: {
        Permission.PROCUREMENT_MANAGE,
        Permission.WAREHOUSE_MANAGE,
    },
    SystemRole.PROJECT_MANAGER: {
        Permission.PROJECTS_MANAGE,
        Permission.CONSTRUCTION_MANAGE,
        Permission.PROCUREMENT_MANAGE,
        Permission.WAREHOUSE_MANAGE,
    },
    SystemRole.ENGINEER: {
        Permission.CONSTRUCTION_MANAGE,
        Permission.PROPERTY_MANAGE,
    },
    SystemRole.HR_MANAGER: {Permission.HR_MANAGE},
    SystemRole.BROKER: {
        Permission.CRM_MANAGE,
        Permission.RESERVATIONS_MANAGE,
    },
    SystemRole.CUSTOMER: {
        Permission.CUSTOMERS_READ,
        Permission.SERVICE_MANAGE,
    },
}


def role_has_permission(role: SystemRole, permission: Permission) -> bool:
    return permission in ROLE_PERMISSIONS.get(role, set())
