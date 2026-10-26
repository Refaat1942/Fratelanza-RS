"""Canonical platform modules — each key maps to a sidebar feature and API prefix."""

from typing import TypedDict


class PlatformModule(TypedDict):
    key: str
    name_en: str
    name_ar: str
    category_en: str
    category_ar: str
    api_prefixes: list[str]
    route: str
    core: bool


PLATFORM_MODULES: list[PlatformModule] = [
    {"key": "dashboard", "name_en": "Dashboard", "name_ar": "لوحة التحكم", "category_en": "Core", "category_ar": "أساسي", "api_prefixes": ["/dashboard", "/re-dashboard"], "route": "/dashboard", "core": True},
    {"key": "customers", "name_en": "Customers", "name_ar": "العملاء", "category_en": "CRM", "category_ar": "إدارة العملاء", "api_prefixes": ["/customers"], "route": "/customers", "core": False},
    {"key": "leads", "name_en": "Leads & CRM", "name_ar": "العملاء المحتملون", "category_en": "CRM", "category_ar": "إدارة العملاء", "api_prefixes": ["/leads"], "route": "/leads", "core": False},
    {"key": "follow_ups", "name_en": "Follow-ups & Calls", "name_ar": "المتابعات والمكالمات", "category_en": "CRM", "category_ar": "إدارة العملاء", "api_prefixes": ["/reminders"], "route": "/follow-ups", "core": False},
    {"key": "projects", "name_en": "Projects & Units", "name_ar": "المشاريع والوحدات", "category_en": "Real Estate", "category_ar": "العقارات", "api_prefixes": ["/projects", "/pricing"], "route": "/projects", "core": False},
    {"key": "reservations", "name_en": "Reservations", "name_ar": "الحجوزات", "category_en": "Sales", "category_ar": "المبيعات", "api_prefixes": ["/reservations"], "route": "/reservations", "core": False},
    {"key": "contracts", "name_en": "Contracts", "name_ar": "العقود", "category_en": "Sales", "category_ar": "المبيعات", "api_prefixes": ["/contracts"], "route": "/contracts", "core": False},
    {"key": "collections", "name_en": "Collections", "name_ar": "التحصيل", "category_en": "Sales", "category_ar": "المبيعات", "api_prefixes": ["/collections"], "route": "/collections", "core": False},
    {"key": "brokers", "name_en": "Brokers", "name_ar": "الوسطاء", "category_en": "Sales", "category_ar": "المبيعات", "api_prefixes": ["/brokers", "/broker-portal"], "route": "/brokers", "core": False},
    {"key": "finance", "name_en": "Finance", "name_ar": "المالية", "category_en": "Finance", "category_ar": "المالية", "api_prefixes": ["/finance"], "route": "/finance", "core": False},
    {"key": "hr", "name_en": "HR & Payroll", "name_ar": "الموارد البشرية", "category_en": "HR", "category_ar": "الموارد البشرية", "api_prefixes": ["/hr"], "route": "/hr", "core": False},
    {"key": "construction", "name_en": "Construction", "name_ar": "المقاولات", "category_en": "Operations", "category_ar": "العمليات", "api_prefixes": ["/construction"], "route": "/construction", "core": False},
    {"key": "procurement", "name_en": "Procurement", "name_ar": "المشتريات", "category_en": "Operations", "category_ar": "العمليات", "api_prefixes": ["/procurement"], "route": "/procurement", "core": False},
    {"key": "warehouse", "name_en": "Warehouse", "name_ar": "المستودع", "category_en": "Operations", "category_ar": "العمليات", "api_prefixes": ["/warehouse"], "route": "/warehouse", "core": False},
    {"key": "property", "name_en": "Property Management", "name_ar": "إدارة الممتلكات", "category_en": "Operations", "category_ar": "العمليات", "api_prefixes": ["/property"], "route": "/property", "core": False},
    {"key": "customer_service", "name_en": "Customer Service", "name_ar": "خدمة العملاء", "category_en": "Support", "category_ar": "الدعم", "api_prefixes": ["/tickets"], "route": "/customer-service", "core": False},
    {"key": "real_estate_requests", "name_en": "Property Requests & Offers", "name_ar": "طلبات وعروض العقارات", "category_en": "Sales", "category_ar": "المبيعات", "api_prefixes": ["/re-requests"], "route": "/property-requests", "core": False},
    {"key": "rentals", "name_en": "Rental Contracts & Rent", "name_ar": "عقود الإيجار والتحصيل", "category_en": "Property Management", "category_ar": "إدارة الأملاك", "api_prefixes": ["/rentals"], "route": "/rentals", "core": False},
    {"key": "owners", "name_en": "Owners & Settlements", "name_ar": "الملاك والتسويات", "category_en": "Property Management", "category_ar": "إدارة الأملاك", "api_prefixes": ["/owners"], "route": "/owners", "core": False},
    {"key": "property_expenses", "name_en": "Property Expenses", "name_ar": "مصروفات العقارات", "category_en": "Property Management", "category_ar": "إدارة الأملاك", "api_prefixes": ["/property-expenses"], "route": "/property-expenses", "core": False},
    {"key": "admin_expenses", "name_en": "Administrative Expenses", "name_ar": "المصروفات الإدارية", "category_en": "Finance", "category_ar": "المالية", "api_prefixes": ["/admin-expenses"], "route": "/admin-expenses", "core": False},
    {"key": "users", "name_en": "Users, Roles & Permissions", "name_ar": "المستخدمون والأدوار والصلاحيات", "category_en": "Admin", "category_ar": "الإدارة", "api_prefixes": ["/users", "/roles"], "route": "/users", "core": False},
    {"key": "customer_portal", "name_en": "Buyer Portal", "name_ar": "بوابة المشتري", "category_en": "Admin", "category_ar": "الإدارة", "api_prefixes": ["/customer-portal"], "route": "/portal-settings", "core": False},
    {"key": "reports", "name_en": "Reports", "name_ar": "التقارير", "category_en": "Analytics", "category_ar": "التحليلات", "api_prefixes": ["/reports", "/exports", "/re-reports"], "route": "/reports", "core": False},
    {"key": "branding", "name_en": "Branding", "name_ar": "الهوية البصرية", "category_en": "Admin", "category_ar": "الإدارة", "api_prefixes": ["/companies/me/branding", "/companies/me/logo"], "route": "/branding", "core": False},
    {"key": "ai_assistant", "name_en": "AI Assistant", "name_ar": "المساعد الذكي", "category_en": "Analytics", "category_ar": "التحليلات", "api_prefixes": ["/ai"], "route": "/ai-assistant", "core": False},
]

ALL_MODULE_KEYS: list[str] = [m["key"] for m in PLATFORM_MODULES]

PLAN_MODULE_DEFAULTS: dict[str, list[str]] = {
    "basic": [
        "dashboard", "customers", "leads", "follow_ups", "projects",
        "reservations", "contracts", "collections", "users", "customer_portal", "branding", "reports",
    ],
    "professional": [
        "dashboard", "customers", "leads", "follow_ups", "projects",
        "reservations", "contracts", "collections", "brokers", "finance", "hr",
        "construction", "procurement", "warehouse", "property", "customer_service",
        "users", "customer_portal", "reports", "branding",
        "real_estate_requests", "rentals", "owners", "property_expenses", "admin_expenses",
    ],
    "enterprise": ALL_MODULE_KEYS,
    "full": ALL_MODULE_KEYS,
    "full_hosted": ALL_MODULE_KEYS,
}

CORE_MODULE_KEYS: list[str] = [m["key"] for m in PLATFORM_MODULES if m["core"]]
