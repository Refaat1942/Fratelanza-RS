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


# ---------------------------------------------------------------------------
# Generic tenant-scoped helpers used by the property-management modules and
# the hardened legacy endpoints.
# ---------------------------------------------------------------------------
from typing import Any, Optional, TypeVar  # noqa: E402

from sqlalchemy import select  # noqa: E402
from sqlalchemy.ext.asyncio import AsyncSession  # noqa: E402

T = TypeVar("T")


async def get_owned(
    db: AsyncSession,
    model: type[T],
    entity_id: Optional[int],
    company_id: int,
    *,
    entity_name: str = "Resource",
    allow_deleted: bool = False,
) -> T:
    """Load a tenant-owned row or raise 404.

    A row belonging to another tenant is reported exactly like a missing row so record ids
    cannot be probed across tenants.
    """
    if entity_id is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"{entity_name} not found")
    query = select(model).where(model.id == entity_id, model.company_id == company_id)  # type: ignore[attr-defined]
    if not allow_deleted and hasattr(model, "is_deleted"):
        query = query.where(model.is_deleted == False)  # type: ignore[attr-defined]  # noqa: E712
    entity = (await db.execute(query)).scalar_one_or_none()
    if entity is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"{entity_name} not found")
    return entity


async def get_owned_optional(
    db: AsyncSession, model: type[T], entity_id: Optional[int], company_id: int, *, entity_name: str = "Resource"
) -> Optional[T]:
    if entity_id is None:
        return None
    return await get_owned(db, model, entity_id, company_id, entity_name=entity_name)


def apply_data_scope(query, assigned_column, access: Any, user: User):
    """Restrict a query to the records the caller may see according to the role's data scope."""
    scope = getattr(access, "data_scope", "all")
    if getattr(access, "is_super_admin", False) or scope == "all":
        return query
    if scope == "branch" and user.branch_id:
        team = select(User.id).where(User.branch_id == user.branch_id, User.company_id == user.company_id)
        return query.where(assigned_column.in_(team))
    return query.where(assigned_column == user.id)


def in_data_scope(assigned_to_id: Optional[int], access: Any, user: User, team_ids: Optional[set[int]] = None) -> bool:
    scope = getattr(access, "data_scope", "all")
    if getattr(access, "is_super_admin", False) or scope == "all":
        return True
    if scope == "branch" and team_ids is not None:
        return assigned_to_id in team_ids
    return assigned_to_id == user.id


def mask(value: Optional[str], visible: bool) -> Optional[str]:
    """Mask a sensitive string unless the caller's role grants the field group."""
    if value is None or visible:
        return value
    tail = str(value)[-2:] if len(str(value)) > 4 else ""
    return f"••••{tail}"


async def ensure_refs(db: AsyncSession, company_id: int, refs: list[tuple[type, Optional[int], str]]) -> None:
    """Validate that every referenced record belongs to ``company_id`` (cross-tenant link guard)."""
    for model, ref_id, name in refs:
        if ref_id is not None:
            await get_owned(db, model, ref_id, company_id, entity_name=name)
