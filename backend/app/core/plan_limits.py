"""Display helpers for subscription plan limits. 0 = unlimited."""

UNLIMITED = 0


def is_unlimited(value: int | None) -> bool:
    return value is not None and value <= UNLIMITED


def format_limit(value: int | None, *, unlimited_en: str = "Unlimited", unlimited_ar: str = "غير محدود") -> dict:
    if is_unlimited(value):
        return {"en": unlimited_en, "ar": unlimited_ar, "raw": 0}
    return {"en": str(value), "ar": str(value), "raw": value or 0}
