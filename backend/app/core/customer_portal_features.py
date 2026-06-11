"""Buyer portal sections — company admins control which sections customers see."""

from typing import TypedDict


class PortalFeature(TypedDict):
    key: str
    name_en: str
    name_ar: str
    description_en: str
    description_ar: str
    core: bool


PORTAL_FEATURES: list[PortalFeature] = [
    {
        "key": "dashboard",
        "name_en": "Overview dashboard",
        "name_ar": "لوحة النظرة العامة",
        "description_en": "Summary cards and account overview",
        "description_ar": "بطاقات الملخص ونظرة عامة على الحساب",
        "core": True,
    },
    {
        "key": "contracts",
        "name_en": "My contracts",
        "name_ar": "عقودي",
        "description_en": "Contract list and unit details on the overview",
        "description_ar": "قائمة العقود وتفاصيل الوحدة في النظرة العامة",
        "core": False,
    },
    {
        "key": "phases",
        "name_en": "Construction phases",
        "name_ar": "مراحل البناء",
        "description_en": "Phase progress bars on the overview",
        "description_ar": "أشرطة تقدم المراحل في النظرة العامة",
        "core": False,
    },
    {
        "key": "installments",
        "name_en": "Installment schedule",
        "name_ar": "جدول الأقساط",
        "description_en": "Full payment schedule and upcoming dues",
        "description_ar": "جدول الدفع الكامل والأقساط القادمة",
        "core": False,
    },
    {
        "key": "receipts",
        "name_en": "Payment receipts",
        "name_ar": "إيصالات الدفع",
        "description_en": "Recorded payments and receipt references",
        "description_ar": "المدفوعات المسجلة ومراجع الإيصالات",
        "core": False,
    },
    {
        "key": "progress",
        "name_en": "Site photos & videos",
        "name_ar": "صور وفيديو الموقع",
        "description_en": "Construction updates published by your developer",
        "description_ar": "تحديثات البناء التي ينشرها المطور",
        "core": False,
    },
]

ALL_PORTAL_FEATURE_KEYS: list[str] = [f["key"] for f in PORTAL_FEATURES]
CORE_PORTAL_FEATURE_KEYS: list[str] = [f["key"] for f in PORTAL_FEATURES if f["core"]]
