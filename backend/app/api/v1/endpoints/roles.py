"""Tenant role & permission administration (module ``users``; writes need ``manage_permissions``).

Changes take effect on the next request of every affected user: each write bumps
``companies.permissions_version`` which keys the permission cache.
"""

import json
import re
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import company_id_of, get_access, get_company_user, log_audit
from app.core.database import get_db
from app.core.permissions import (
    ACTION_KEYS,
    ACTIONS,
    AUDITOR_TEMPLATE,
    DATA_SCOPE_KEYS,
    DATA_SCOPES,
    FIELD_GROUP_KEYS,
    FIELD_GROUPS,
    MODULE_PAGES,
    ROLE_TEMPLATES,
)
from app.core.platform_modules import ALL_MODULE_KEYS, PLATFORM_MODULES
from app.core.tenant import get_owned
from app.models.users import Permission, Role, RolePermission, SystemRole, User, UserRole
from app.services.access_service import AccessContext, AccessService

router = APIRouter()


class RoleIn(BaseModel):
    name_ar: str = Field(min_length=2, max_length=255)
    name_en: str = Field(min_length=2, max_length=255)
    code: Optional[str] = Field(default=None, max_length=100)
    description: Optional[str] = None
    data_scope: str = "all"
    field_access: list[str] = []
    permissions: dict[str, list[str]] = {}
    is_active: bool = True


class RoleFromTemplate(BaseModel):
    template: str
    name_ar: Optional[str] = None
    name_en: Optional[str] = None


class AssignmentIn(BaseModel):
    role_ids: list[int]


async def ensure_permission_rows(db: AsyncSession) -> dict[tuple[str, str], int]:
    rows = (await db.execute(select(Permission))).scalars().all()
    mapping = {(p.module, p.action): p.id for p in rows}
    names = {a["key"]: a for a in ACTIONS}
    created = False
    for module in ALL_MODULE_KEYS:
        for action in ACTION_KEYS:
            if (module, action) not in mapping:
                p = Permission(module=module, action=action, code=f"{module}.{action}",
                               name_ar=names[action]["name_ar"], name_en=names[action]["name_en"])
                db.add(p)
                created = True
    if created:
        await db.flush()
        rows = (await db.execute(select(Permission))).scalars().all()
        mapping = {(p.module, p.action): p.id for p in rows}
    return mapping


def _validate(data: RoleIn, access: AccessContext) -> None:
    if data.data_scope not in DATA_SCOPE_KEYS:
        raise HTTPException(status_code=400, detail="Invalid data scope")
    bad_fields = set(data.field_access) - set(FIELD_GROUP_KEYS)
    if bad_fields:
        raise HTTPException(status_code=400, detail=f"Unknown field groups: {sorted(bad_fields)}")
    for module, actions in data.permissions.items():
        if module not in ALL_MODULE_KEYS:
            raise HTTPException(status_code=400, detail=f"Unknown module: {module}")
        unknown = set(actions) - set(ACTION_KEYS)
        if unknown:
            raise HTTPException(status_code=400, detail=f"Unknown actions for {module}: {sorted(unknown)}")
        # No privilege escalation: an administrator can only grant what they hold themselves.
        for action in actions:
            if not access.can(module, action):
                raise HTTPException(status_code=403, detail=f"Cannot grant {module}.{action} — you do not hold it")
    for group in data.field_access:
        if not access.sees(group):
            raise HTTPException(status_code=403, detail=f"Cannot grant field group {group} — you do not hold it")


async def _save_permissions(db: AsyncSession, role: Role, permissions: dict[str, list[str]]) -> None:
    mapping = await ensure_permission_rows(db)
    await db.execute(delete(RolePermission).where(RolePermission.role_id == role.id))
    for module, actions in permissions.items():
        for action in sorted(set(actions)):
            db.add(RolePermission(role_id=role.id, permission_id=mapping[(module, action)]))
    await db.flush()


async def _role_dict(db: AsyncSession, role: Role) -> dict:
    perms = (
        await db.execute(
            select(Permission.module, Permission.action)
            .join(RolePermission, RolePermission.permission_id == Permission.id)
            .where(RolePermission.role_id == role.id)
        )
    ).all()
    grouped: dict[str, list[str]] = {}
    for module, action in perms:
        grouped.setdefault(module, []).append(action)
    users = (await db.execute(select(func.count(UserRole.id)).where(UserRole.role_id == role.id))).scalar() or 0
    return {
        "id": role.id, "name_ar": role.name_ar, "name_en": role.name_en, "code": role.code, "description": role.description,
        "data_scope": role.data_scope, "field_access": json.loads(role.field_access) if role.field_access else [],
        "permissions": {m: sorted(a) for m, a in grouped.items()}, "is_active": role.is_active,
        "base_system_role": role.base_system_role, "users_count": users,
    }


def _slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")[:80] or "role"


@router.get("/catalog")
async def permission_catalog(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_company_user)],
    access: Annotated[AccessContext, Depends(get_access)],
):
    return {
        "modules": [
            {"key": m["key"], "name_ar": m["name_ar"], "name_en": m["name_en"], "category_ar": m["category_ar"],
             "category_en": m["category_en"], "enabled": m["key"] in access.enabled_modules,
             "pages": MODULE_PAGES.get(m["key"], [])}
            for m in PLATFORM_MODULES
        ],
        "actions": ACTIONS,
        "field_groups": FIELD_GROUPS,
        "data_scopes": DATA_SCOPES,
        "templates": [
            {"key": k, "name_ar": v["name_ar"], "name_en": v["name_en"]}
            for k, v in ROLE_TEMPLATES.items() if v["permissions"]
        ] + [{"key": AUDITOR_TEMPLATE["code"], "name_ar": AUDITOR_TEMPLATE["name_ar"], "name_en": AUDITOR_TEMPLATE["name_en"]}],
    }


@router.get("")
async def list_roles(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_company_user)],
):
    roles = (
        await db.execute(select(Role).where(Role.company_id == company_id_of(current_user)).order_by(Role.id))
    ).scalars().all()
    return [await _role_dict(db, r) for r in roles]


@router.post("")
async def create_role(
    data: RoleIn, request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_company_user)],
    access: Annotated[AccessContext, Depends(get_access)],
):
    cid = company_id_of(current_user)
    _validate(data, access)
    code = data.code or _slug(data.name_en)
    if (await db.execute(select(Role.id).where(Role.company_id == cid, Role.code == code))).first():
        raise HTTPException(status_code=409, detail="Role code already exists")
    role = Role(company_id=cid, name_ar=data.name_ar, name_en=data.name_en, code=code, description=data.description,
                data_scope=data.data_scope, field_access=json.dumps(sorted(set(data.field_access))), is_active=data.is_active)
    db.add(role)
    await db.flush()
    await _save_permissions(db, role, data.permissions)
    await AccessService.bump_version(db, cid)
    await log_audit(db, request, current_user, "role_created", "users", "role", role.id,
                    after={"code": code, "permissions": data.permissions, "data_scope": data.data_scope, "field_access": data.field_access})
    return await _role_dict(db, role)


@router.post("/from-template")
async def create_role_from_template(
    data: RoleFromTemplate, request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_company_user)],
    access: Annotated[AccessContext, Depends(get_access)],
):
    tpl = AUDITOR_TEMPLATE if data.template == AUDITOR_TEMPLATE["code"] else ROLE_TEMPLATES.get(data.template)
    if not tpl:
        raise HTTPException(status_code=404, detail="Template not found")
    perms = {m: [a for a in acts] for m, acts in tpl["permissions"].items() if m in access.enabled_modules}
    role_in = RoleIn(name_ar=data.name_ar or tpl["name_ar"], name_en=data.name_en or tpl["name_en"],
                     code=f"{data.template}_custom", data_scope=tpl["data_scope"], field_access=list(tpl["field_access"]),
                     permissions=perms)
    return await create_role(role_in, request, db, current_user, access)


@router.get("/assignments/{user_id}")
async def get_user_roles(
    user_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_company_user)],
):
    cid = company_id_of(current_user)
    user = await get_owned(db, User, user_id, cid, entity_name="User")
    role_ids = (await db.execute(select(UserRole.role_id).where(UserRole.user_id == user.id))).scalars().all()
    ctx = await AccessService.build(db, user)
    return {"user_id": user.id, "system_role": user.system_role.value, "role_ids": list(role_ids), "effective": ctx.to_dict()}


@router.put("/assignments/{user_id}")
async def set_user_roles(
    user_id: int, data: AssignmentIn, request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_company_user)],
):
    cid = company_id_of(current_user)
    user = await get_owned(db, User, user_id, cid, entity_name="User")
    if user.system_role in (SystemRole.BROKER, SystemRole.CUSTOMER):
        raise HTTPException(status_code=400, detail="Portal users cannot receive staff roles")
    for rid in data.role_ids:
        await get_owned(db, Role, rid, cid, entity_name="Role")  # roles of another tenant are "not found"
    before = list((await db.execute(select(UserRole.role_id).where(UserRole.user_id == user.id))).scalars().all())
    await db.execute(delete(UserRole).where(UserRole.user_id == user.id))
    for rid in sorted(set(data.role_ids)):
        db.add(UserRole(user_id=user.id, role_id=rid))
    await db.flush()
    await AccessService.ensure_admin_remains(db, cid)
    await log_audit(db, request, current_user, "user_roles_changed", "users", "user", user.id,
                    before={"role_ids": before}, after={"role_ids": sorted(set(data.role_ids))})
    return {"user_id": user.id, "role_ids": sorted(set(data.role_ids))}


@router.get("/{role_id}")
async def get_role(
    role_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_company_user)],
):
    role = await get_owned(db, Role, role_id, company_id_of(current_user), entity_name="Role")
    return await _role_dict(db, role)


@router.put("/{role_id}")
async def update_role(
    role_id: int, data: RoleIn, request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_company_user)],
    access: Annotated[AccessContext, Depends(get_access)],
):
    cid = company_id_of(current_user)
    role = await get_owned(db, Role, role_id, cid, entity_name="Role")
    _validate(data, access)
    before = await _role_dict(db, role)
    role.name_ar, role.name_en, role.description = data.name_ar, data.name_en, data.description
    role.data_scope = data.data_scope
    role.field_access = json.dumps(sorted(set(data.field_access)))
    role.is_active = data.is_active
    await db.flush()
    await _save_permissions(db, role, data.permissions)
    await AccessService.ensure_admin_remains(db, cid)
    await log_audit(db, request, current_user, "role_updated", "users", "role", role.id,
                    before={"permissions": before["permissions"], "data_scope": before["data_scope"], "field_access": before["field_access"]},
                    after={"permissions": data.permissions, "data_scope": data.data_scope, "field_access": data.field_access})
    return await _role_dict(db, role)


@router.delete("/{role_id}")
async def delete_role(
    role_id: int, request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_company_user)],
):
    cid = company_id_of(current_user)
    role = await get_owned(db, Role, role_id, cid, entity_name="Role")
    await db.execute(delete(UserRole).where(UserRole.role_id == role.id))
    await db.execute(delete(RolePermission).where(RolePermission.role_id == role.id))
    await db.delete(role)
    await db.flush()
    await AccessService.ensure_admin_remains(db, cid)
    await log_audit(db, request, current_user, "role_deleted", "users", "role", role_id)
    return {"success": True}


@router.get("/audit/log")
async def permission_audit_log(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_company_user)],
    access: Annotated[AccessContext, Depends(get_access)],
    limit: int = 100,
):
    """Tenant-scoped audit trail (admins with manage_permissions only)."""
    from app.models.system import AuditLog

    if not access.can("users", "manage_permissions"):
        raise HTTPException(status_code=403, detail="permission_denied")
    logs = (
        await db.execute(
            select(AuditLog, User)
            .outerjoin(User, AuditLog.user_id == User.id)
            .where(AuditLog.company_id == company_id_of(current_user))
            .order_by(AuditLog.id.desc())
            .limit(min(max(limit, 1), 500))
        )
    ).all()
    return [
        {"id": a.id, "action": a.action, "module": a.module, "entity_type": a.entity_type, "entity_id": a.entity_id,
         "user": u.full_name_ar if u else None, "created_at": str(a.created_at), "details": a.details,
         "changes": json.loads(a.changes) if a.changes else None}
        for a, u in logs
    ]
