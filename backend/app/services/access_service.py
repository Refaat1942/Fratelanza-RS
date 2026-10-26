"""Effective-permission resolution for a user inside their tenant.

effective(module, action) = module enabled for tenant (feature flag, incl. per-user allowlist)
                            AND role grants module/action (custom roles, else system-role template)
                            AND (tenant is not a demo OR action allowed by the demo configuration)

Results are cached per process, keyed by ``companies.permissions_version``. Any role, assignment,
feature-flag or demo change bumps that version in the database, so every worker sees the change
on the next request — no redeploy or restart needed.
"""

import json
import threading
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.permissions import (
    ACTION_KEYS,
    FIELD_GROUP_KEYS,
    broadest_scope,
    template_for,
)
from app.core.platform_modules import ALL_MODULE_KEYS, CORE_MODULE_KEYS
from app.models.rentals import DemoEnvironment
from app.models.tenant import Company, CompanySubscription
from app.models.users import Permission, Role, RolePermission, User, UserRole, UserStatus
from app.services.module_service import ModuleService

# Fictional data, so sensitive financial views are on; exports, deletes, refunds and permission
# management are off unless the platform admin enables them for a specific demo.
DEFAULT_DEMO_ACTIONS = ["view", "create", "edit", "approve", "cancel", "print", "collect", "terminate", "view_sensitive"]


@dataclass(frozen=True)
class AccessContext:
    user_id: int
    company_id: Optional[int]
    branch_id: Optional[int]
    is_super_admin: bool
    is_demo: bool
    enabled_modules: tuple[str, ...]
    permissions: dict[str, frozenset[str]] = field(default_factory=dict)
    data_scope: str = "all"
    field_access: frozenset[str] = frozenset()
    has_custom_roles: bool = False
    dashboard_cards: Optional[tuple[str, ...]] = None

    def can(self, module: str, action: str = "view") -> bool:
        if self.is_super_admin:
            return True
        return action in self.permissions.get(module, frozenset())

    def sees(self, field_group: str) -> bool:
        return self.is_super_admin or field_group in self.field_access

    def to_dict(self) -> dict:
        return {
            "user_id": self.user_id,
            "company_id": self.company_id,
            "is_super_admin": self.is_super_admin,
            "is_demo": self.is_demo,
            "enabled_modules": list(self.enabled_modules),
            "permissions": {m: sorted(a) for m, a in self.permissions.items()},
            "data_scope": self.data_scope,
            "field_access": sorted(self.field_access),
            "has_custom_roles": self.has_custom_roles,
            "dashboard_cards": list(self.dashboard_cards) if self.dashboard_cards is not None else None,
        }


_cache: dict[tuple, AccessContext] = {}
_cache_lock = threading.Lock()
_CACHE_MAX = 5000


def _parse_json_list(raw: Optional[str]) -> Optional[list[str]]:
    if not raw:
        return None
    try:
        parsed = json.loads(raw)
        return [str(x) for x in parsed] if isinstance(parsed, list) else None
    except (json.JSONDecodeError, TypeError):
        return None


class AccessService:
    @staticmethod
    async def bump_version(db: AsyncSession, company_id: int) -> None:
        """Invalidate cached permission sets for every user of the tenant (all workers)."""
        await db.execute(
            update(Company)
            .where(Company.id == company_id)
            .values(permissions_version=Company.permissions_version + 1)
        )

    @staticmethod
    def demo_state(demo: Optional[DemoEnvironment]) -> Optional[str]:
        """Return None when the demo is usable, else a machine-readable reason."""
        if demo is None:
            return "demo_not_configured"
        if demo.revoked_at is not None:
            return "demo_revoked"
        if not demo.is_enabled:
            return "demo_disabled"
        if demo.expires_at is not None:
            expires = demo.expires_at
            if expires.tzinfo is None:
                expires = expires.replace(tzinfo=timezone.utc)
            if expires <= datetime.now(timezone.utc):
                return "demo_expired"
        return None

    @staticmethod
    def ensure_demo_usable(demo: Optional[DemoEnvironment]) -> None:
        reason = AccessService.demo_state(demo)
        if reason:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=reason)

    @staticmethod
    async def load_company(db: AsyncSession, company_id: int) -> Optional[Company]:
        return (
            await db.execute(
                select(Company)
                .options(selectinload(Company.subscription).selectinload(CompanySubscription.plan))
                .where(Company.id == company_id, Company.is_deleted == False)  # noqa: E712
                .execution_options(populate_existing=True)
            )
        ).scalar_one_or_none()

    @staticmethod
    async def load_demo(db: AsyncSession, company_id: int) -> Optional[DemoEnvironment]:
        return (
            await db.execute(select(DemoEnvironment).where(DemoEnvironment.company_id == company_id))
        ).scalar_one_or_none()

    @staticmethod
    async def role_grants(db: AsyncSession, user: User) -> Optional[tuple[dict[str, set[str]], str, set[str]]]:
        """Union of the user's custom roles in their own tenant, or None if none assigned."""
        if not user.company_id:
            return None
        roles = (
            await db.execute(
                select(Role)
                .join(UserRole, UserRole.role_id == Role.id)
                .where(
                    UserRole.user_id == user.id,
                    Role.company_id == user.company_id,  # never honour a role from another tenant
                    Role.is_active == True,  # noqa: E712
                )
            )
        ).scalars().all()
        if not roles:
            return None
        role_ids = [r.id for r in roles]
        rows = (
            await db.execute(
                select(Permission.module, Permission.action)
                .join(RolePermission, RolePermission.permission_id == Permission.id)
                .where(RolePermission.role_id.in_(role_ids))
            )
        ).all()
        perms: dict[str, set[str]] = {}
        for module, action in rows:
            perms.setdefault(module, set()).add(action)
        scope = broadest_scope([r.data_scope or "own" for r in roles])
        fields: set[str] = set()
        for r in roles:
            fields.update(_parse_json_list(r.field_access) or [])
        return perms, scope, fields

    @staticmethod
    async def build(
        db: AsyncSession,
        user: User,
        company: Optional[Company] = None,
        demo: Optional[DemoEnvironment] = None,
    ) -> AccessContext:
        if user.is_super_admin:
            return AccessContext(
                user_id=user.id,
                company_id=user.company_id,
                branch_id=user.branch_id,
                is_super_admin=True,
                is_demo=False,
                enabled_modules=tuple(ALL_MODULE_KEYS),
                permissions={m: frozenset(ACTION_KEYS) for m in ALL_MODULE_KEYS},
                data_scope="all",
                field_access=frozenset(FIELD_GROUP_KEYS),
            )
        if not user.company_id:
            return AccessContext(user.id, None, None, False, False, ())

        if company is None:
            company = await AccessService.load_company(db, user.company_id)
        if company is None:
            return AccessContext(user.id, user.company_id, user.branch_id, False, False, ())
        if company.is_demo and demo is None:
            demo = await AccessService.load_demo(db, company.id)

        demo_stamp = (demo.updated_at.isoformat() if demo and demo.updated_at else None)
        key = (
            user.id,
            company.id,
            company.permissions_version,
            company.enabled_modules,
            user.system_role.value,
            user.allowed_modules,
            user.branch_id,
            demo_stamp,
        )
        with _cache_lock:
            cached = _cache.get(key)
        if cached is not None:
            return cached

        plan = company.subscription.plan if company.subscription else None
        enabled = ModuleService.parse_effective(company, plan, user)

        grants = await AccessService.role_grants(db, user)
        has_custom = grants is not None
        if grants is None:
            tpl = template_for(user.system_role.value)
            role_perms = {m: set(a) for m, a in tpl["permissions"].items()}
            scope = tpl["data_scope"]
            fields = set(tpl["field_access"])
        else:
            role_perms, scope, fields = grants

        demo_actions: Optional[set[str]] = None
        dashboard_cards: Optional[tuple[str, ...]] = None
        if company.is_demo:
            demo_actions = set(_parse_json_list(demo.allowed_actions if demo else None) or DEFAULT_DEMO_ACTIONS)
            # Demo users can never manage platform-level permissions or see sensitive financial rows
            # beyond what the demo explicitly enables.
            cards = _parse_json_list(demo.dashboard_cards if demo else None)
            dashboard_cards = tuple(cards) if cards is not None else None

        permissions: dict[str, frozenset[str]] = {}
        for module in enabled:
            actions = set(role_perms.get(module, set()))
            if module in CORE_MODULE_KEYS:
                actions.add("view")
            if demo_actions is not None:
                actions &= demo_actions | {"view"}
            if actions:
                permissions[module] = frozenset(actions)

        ctx = AccessContext(
            user_id=user.id,
            company_id=company.id,
            branch_id=user.branch_id,
            is_super_admin=False,
            is_demo=bool(company.is_demo),
            enabled_modules=tuple(enabled),
            permissions=permissions,
            data_scope=scope,
            field_access=frozenset(fields),
            has_custom_roles=has_custom,
            dashboard_cards=dashboard_cards,
        )
        with _cache_lock:
            if len(_cache) > _CACHE_MAX:
                _cache.clear()
            _cache[key] = ctx
        return ctx

    @staticmethod
    async def ensure_admin_remains(db: AsyncSession, company_id: int) -> None:
        """Lock-out guard: after a permission change at least one active user of the tenant must
        still be able to manage permissions. Call after flushing the change; raising rolls it back."""
        await AccessService.bump_version(db, company_id)
        await db.flush()
        company = await AccessService.load_company(db, company_id)
        if company is None or company.is_demo:
            return
        plan = company.subscription.plan if company.subscription else None
        if "users" not in ModuleService.parse_enabled(company, plan):
            return  # user management is not part of this tenant's product — nothing to lock out of
        users = (
            await db.execute(
                select(User)
                .where(User.company_id == company_id, User.is_deleted == False, User.status == UserStatus.ACTIVE)  # noqa: E712
                .execution_options(populate_existing=True)
            )
        ).scalars().all()
        for u in users:
            ctx = await AccessService.build(db, u, company)
            if ctx.can("users", "manage_permissions"):
                return
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="lockout_prevented: at least one active administrator must keep permission management",
        )

    @staticmethod
    def clear_cache() -> None:
        with _cache_lock:
            _cache.clear()
