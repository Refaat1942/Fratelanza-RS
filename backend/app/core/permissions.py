"""Permission catalog: modules × actions, sensitive field groups and default role templates.

Three independent layers decide every request (see docs/ROLES_AND_PERMISSIONS.md):

1. Tenant feature flags  — ``companies.enabled_modules`` (what the company bought / the demo shows)
2. User permissions      — roles (custom or default template) → module/action, data scope, fields
3. Demo restrictions     — ``demo_environments.allowed_actions`` + expiry / revocation

All three are enforced server-side in ``app.middleware.module_guard.AccessGuardMiddleware``.
"""

from app.core.platform_modules import ALL_MODULE_KEYS
from app.models.users import SystemRole

ACTIONS: list[dict] = [
    {"key": "view", "name_ar": "عرض", "name_en": "View"},
    {"key": "create", "name_ar": "إضافة", "name_en": "Create"},
    {"key": "edit", "name_ar": "تعديل", "name_en": "Edit"},
    {"key": "delete", "name_ar": "حذف", "name_en": "Delete"},
    {"key": "approve", "name_ar": "اعتماد", "name_en": "Approve"},
    {"key": "cancel", "name_ar": "إلغاء", "name_en": "Cancel"},
    {"key": "export", "name_ar": "تصدير", "name_en": "Export"},
    {"key": "print", "name_ar": "طباعة", "name_en": "Print"},
    {"key": "collect", "name_ar": "تحصيل", "name_en": "Collect payments"},
    {"key": "refund", "name_ar": "استرداد", "name_en": "Record refunds"},
    {"key": "terminate", "name_ar": "إنهاء العقود", "name_en": "Terminate contracts"},
    {"key": "manage_permissions", "name_ar": "إدارة الصلاحيات", "name_en": "Manage permissions"},
    {"key": "view_sensitive", "name_ar": "عرض البيانات المالية الحساسة", "name_en": "View sensitive financials"},
]
ACTION_KEYS: list[str] = [a["key"] for a in ACTIONS]

# Sensitive field groups — hidden (masked) in API responses unless the user's role grants the group.
FIELD_GROUPS: list[dict] = [
    {"key": "identity", "name_ar": "الرقم القومي وجواز السفر", "name_en": "National ID & passport"},
    {"key": "owner_financials", "name_ar": "البيانات المالية للملاك", "name_en": "Owner financial details"},
    {"key": "salaries", "name_ar": "الرواتب والأجور", "name_en": "Salaries & payroll"},
    {"key": "commissions", "name_ar": "العمولات وهوامش الربح", "name_en": "Commissions & margins"},
    {"key": "bank_accounts", "name_ar": "الحسابات البنكية", "name_en": "Bank account details"},
    {"key": "internal_notes", "name_ar": "الملاحظات الداخلية", "name_en": "Internal notes"},
]
FIELD_GROUP_KEYS: list[str] = [g["key"] for g in FIELD_GROUPS]

DATA_SCOPES: list[dict] = [
    {"key": "all", "name_ar": "كل سجلات الشركة", "name_en": "All company records"},
    {"key": "branch", "name_ar": "سجلات الفرع", "name_en": "Branch / team records"},
    {"key": "own", "name_ar": "السجلات المسندة لي فقط", "name_en": "Only records assigned to me"},
]
DATA_SCOPE_KEYS = [d["key"] for d in DATA_SCOPES]
_SCOPE_RANK = {"own": 0, "branch": 1, "all": 2}


def broadest_scope(scopes: list[str]) -> str:
    if not scopes:
        return "own"
    return max(scopes, key=lambda s: _SCOPE_RANK.get(s, 0))


# Pages/tabs inside modules that can be hidden independently (page access dimension).
MODULE_PAGES: dict[str, list[dict]] = {
    "rentals": [
        {"key": "rentals.contracts", "name_ar": "عقود الإيجار", "name_en": "Rental contracts"},
        {"key": "rentals.receivables", "name_ar": "مستحقات الإيجار", "name_en": "Rent receivables"},
    ],
    "owners": [
        {"key": "owners.list", "name_ar": "الملاك", "name_en": "Owners"},
        {"key": "owners.settlements", "name_ar": "تسويات الملاك", "name_en": "Owner settlements"},
    ],
    "reports": [
        {"key": "reports.financial", "name_ar": "التقارير المالية", "name_en": "Financial reports"},
        {"key": "reports.operational", "name_ar": "التقارير التشغيلية", "name_en": "Operational reports"},
    ],
}

_ALL = list(ACTION_KEYS)
_RW = ["view", "create", "edit"]
_RWD = ["view", "create", "edit", "delete"]
_FULL_OPS = ["view", "create", "edit", "delete", "approve", "cancel", "export", "print"]


def _grant(modules: list[str], actions: list[str]) -> dict[str, list[str]]:
    return {m: list(actions) for m in modules}


def _merge(*parts: dict[str, list[str]]) -> dict[str, list[str]]:
    merged: dict[str, set[str]] = {}
    for part in parts:
        for module, actions in part.items():
            merged.setdefault(module, set()).update(actions)
    return {m: sorted(a) for m, a in merged.items()}


# Default templates keyed by SystemRole. Users without explicit role assignments get these,
# so existing accounts keep working after the upgrade. Tenants override them with custom roles.
ROLE_TEMPLATES: dict[str, dict] = {
    SystemRole.COMPANY_ADMIN.value: {
        "name_ar": "مدير الشركة", "name_en": "Company Admin",
        "permissions": _grant(ALL_MODULE_KEYS, _ALL), "data_scope": "all", "field_access": FIELD_GROUP_KEYS,
    },
    SystemRole.CEO.value: {
        "name_ar": "المدير العام", "name_en": "General Manager",
        "permissions": _grant(ALL_MODULE_KEYS, _ALL), "data_scope": "all", "field_access": FIELD_GROUP_KEYS,
    },
    SystemRole.MANAGING_DIRECTOR.value: {
        "name_ar": "العضو المنتدب", "name_en": "Managing Director",
        "permissions": _grant(ALL_MODULE_KEYS, _ALL), "data_scope": "all", "field_access": FIELD_GROUP_KEYS,
    },
    SystemRole.SALES_DIRECTOR.value: {
        "name_ar": "مدير المبيعات", "name_en": "Sales Director",
        "permissions": _merge(
            _grant(["dashboard"], ["view"]),
            _grant(["customers", "leads", "follow_ups", "real_estate_requests", "reservations", "contracts", "brokers"], _FULL_OPS),
            _grant(["projects"], ["view", "export", "print"]),
            _grant(["reports"], ["view", "export"]),
        ),
        "data_scope": "all", "field_access": ["identity", "commissions"],
    },
    SystemRole.SALES_MANAGER.value: {
        "name_ar": "مدير مبيعات", "name_en": "Sales Manager",
        "permissions": _merge(
            _grant(["dashboard"], ["view"]),
            _grant(["customers", "leads", "follow_ups", "real_estate_requests", "reservations"], _FULL_OPS),
            _grant(["contracts"], ["view", "create", "edit", "print"]),
            _grant(["projects", "brokers"], ["view"]),
            _grant(["reports"], ["view"]),
        ),
        "data_scope": "branch", "field_access": ["identity"],
    },
    SystemRole.SALES_AGENT.value: {
        "name_ar": "مندوب مبيعات", "name_en": "Sales Agent",
        "permissions": _merge(
            _grant(["dashboard"], ["view"]),
            _grant(["customers", "leads", "follow_ups", "real_estate_requests"], _RW),
            _grant(["reservations"], ["view", "create"]),
            _grant(["projects"], ["view"]),
        ),
        "data_scope": "own", "field_access": [],
    },
    SystemRole.CUSTOMER_SERVICE.value: {
        "name_ar": "خدمة العملاء", "name_en": "Customer Service",
        "permissions": _merge(
            _grant(["dashboard"], ["view"]),
            _grant(["customers"], ["view", "edit"]),
            _grant(["customer_service"], _RWD),
            _grant(["leads", "follow_ups"], _RW),
            _grant(["property"], ["view", "create"]),
        ),
        "data_scope": "all", "field_access": [],
    },
    SystemRole.COLLECTION_OFFICER.value: {
        "name_ar": "مسؤول التحصيل", "name_en": "Collections Officer",
        "permissions": _merge(
            _grant(["dashboard"], ["view"]),
            _grant(["collections", "rentals"], ["view", "collect", "print"]),
            _grant(["customers", "contracts"], ["view"]),
        ),
        "data_scope": "all", "field_access": [],
    },
    SystemRole.ACCOUNTANT.value: {
        "name_ar": "محاسب", "name_en": "Accountant",
        "permissions": _merge(
            _grant(["dashboard"], ["view", "view_sensitive"]),
            _grant(["finance", "property_expenses", "admin_expenses"], ["view", "create", "edit", "export", "print", "collect"]),
            _grant(["collections", "rentals"], ["view", "collect", "refund", "export", "print"]),
            _grant(["owners"], ["view", "create", "edit", "export", "print"]),
            _grant(["reports"], ["view", "export", "view_sensitive"]),
            _grant(["contracts", "customers"], ["view"]),
        ),
        "data_scope": "all", "field_access": ["owner_financials", "commissions", "bank_accounts"],
    },
    SystemRole.FINANCE_MANAGER.value: {
        "name_ar": "المدير المالي", "name_en": "Finance Manager",
        "permissions": _merge(
            _grant(["dashboard"], ["view", "view_sensitive"]),
            _grant(["finance", "property_expenses", "admin_expenses", "owners"], _FULL_OPS + ["collect", "view_sensitive"]),
            _grant(["collections", "rentals"], _FULL_OPS + ["collect", "refund"]),
            _grant(["reports"], ["view", "export", "print", "view_sensitive"]),
            _grant(["hr"], ["view"]),
            _grant(["contracts", "customers"], ["view"]),
        ),
        "data_scope": "all", "field_access": ["owner_financials", "commissions", "bank_accounts", "identity"],
    },
    SystemRole.PROCUREMENT_OFFICER.value: {
        "name_ar": "مسؤول المشتريات", "name_en": "Procurement Officer",
        "permissions": _merge(_grant(["dashboard"], ["view"]), _grant(["procurement", "warehouse"], _FULL_OPS)),
        "data_scope": "all", "field_access": [],
    },
    SystemRole.PROJECT_MANAGER.value: {
        "name_ar": "مدير العقارات", "name_en": "Property Manager",
        "permissions": _merge(
            _grant(["dashboard"], ["view"]),
            _grant(["projects", "construction", "property"], _FULL_OPS),
            _grant(["rentals"], ["view", "create", "edit", "approve", "terminate", "print"]),
            _grant(["owners"], ["view"]),
            _grant(["property_expenses"], ["view", "create", "edit"]),
            _grant(["real_estate_requests"], ["view"]),
        ),
        "data_scope": "all", "field_access": [],
    },
    SystemRole.ENGINEER.value: {
        "name_ar": "مسؤول الصيانة", "name_en": "Maintenance Officer",
        "permissions": _merge(
            _grant(["dashboard"], ["view"]),
            _grant(["construction", "property"], _RW),
            _grant(["property_expenses"], ["view", "create"]),
            _grant(["projects"], ["view"]),
        ),
        "data_scope": "all", "field_access": [],
    },
    SystemRole.HR_MANAGER.value: {
        "name_ar": "مسؤول الموارد البشرية والرواتب", "name_en": "HR / Payroll Officer",
        "permissions": _merge(
            _grant(["dashboard"], ["view"]),
            _grant(["hr"], _FULL_OPS + ["collect", "view_sensitive"]),
            _grant(["reports"], ["view"]),
        ),
        "data_scope": "all", "field_access": ["salaries"],
    },
    # Portal users authenticate against their own self-service endpoints only.
    SystemRole.BROKER.value: {
        "name_ar": "وسيط", "name_en": "Broker", "permissions": {}, "data_scope": "own", "field_access": [],
    },
    SystemRole.CUSTOMER.value: {
        "name_ar": "عميل", "name_en": "Customer", "permissions": {}, "data_scope": "own", "field_access": [],
    },
}

AUDITOR_TEMPLATE = {
    "code": "auditor",
    "name_ar": "مدقق (قراءة فقط)",
    "name_en": "Read-only Auditor",
    "permissions": _grant(ALL_MODULE_KEYS, ["view", "export", "view_sensitive"]),
    "data_scope": "all",
    "field_access": ["owner_financials", "commissions", "bank_accounts"],
}

# Roles allowed to hold the company-admin system role (protected from lock-out)
ADMIN_SYSTEM_ROLES = {SystemRole.COMPANY_ADMIN, SystemRole.CEO, SystemRole.MANAGING_DIRECTOR}


def template_for(system_role: str) -> dict:
    return ROLE_TEMPLATES.get(system_role, {"permissions": {}, "data_scope": "own", "field_access": []})
