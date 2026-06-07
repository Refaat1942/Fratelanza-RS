"""Tenant isolation helpers — enforce company-scoped data access."""

from fastapi import HTTPException, status

from app.models.users import User


def ensure_company_access(entity, user: User, *, entity_name: str = "Resource") -> None:
    """Raise 403 if a non-super-admin user tries to access another company's data."""
    if user.is_super_admin:
        return
    entity_company_id = getattr(entity, "company_id", None)
    if entity_company_id is None:
        return
    if not user.company_id or entity_company_id != user.company_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"{entity_name} access denied — tenant isolation",
        )


def company_filter_value(user: User) -> int | None:
    """Return company_id for query filtering, or None for super admin (no filter)."""
    if user.is_super_admin:
        return None
    if not user.company_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Company access required",
        )
    return user.company_id
