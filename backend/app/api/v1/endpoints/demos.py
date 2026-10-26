"""Platform super-admin management of customer demo environments."""

import json
from datetime import datetime
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_super_admin, log_audit
from app.core.database import get_db
from app.core.permissions import ACTIONS
from app.core.platform_modules import PLATFORM_MODULES
from app.models.system import AuditLog
from app.models.users import User
from app.services.access_service import DEFAULT_DEMO_ACTIONS
from app.services.demo_service import PROFILES, DemoService
from app.services.re_dashboard_service import CARDS

router = APIRouter()


class DemoUserIn(BaseModel):
    role: str = "company_admin"
    full_name: Optional[str] = None


class DemoCreate(BaseModel):
    prospect_name: str = Field(min_length=2, max_length=255)
    company_name_ar: str = Field(min_length=2, max_length=255)
    company_name_en: str = Field(min_length=2, max_length=255)
    logo_url: Optional[str] = None
    profile: str = "full_erp"
    enabled_modules: Optional[list[str]] = None
    allowed_actions: Optional[list[str]] = None
    dashboard_cards: Optional[list[str]] = None
    valid_days: int = Field(default=14, ge=1, le=365)
    expires_at: Optional[datetime] = None
    users: list[DemoUserIn] = [DemoUserIn()]
    notes: Optional[str] = None
    seed: bool = True


class DemoUpdate(BaseModel):
    prospect_name: Optional[str] = None
    company_name_ar: Optional[str] = None
    company_name_en: Optional[str] = None
    logo_url: Optional[str] = None
    profile: Optional[str] = None
    enabled_modules: Optional[list[str]] = None
    allowed_actions: Optional[list[str]] = None
    dashboard_cards: Optional[list[str]] = None
    expires_at: Optional[datetime] = None
    valid_days: Optional[int] = Field(default=None, ge=1, le=365)
    is_enabled: Optional[bool] = None
    notes: Optional[str] = None


@router.get("/options")
async def demo_options(_: Annotated[User, Depends(get_super_admin)]):
    return {
        "profiles": [{"key": k, "name_ar": v["name_ar"], "name_en": v["name_en"], "modules": v["modules"], "cards": v["cards"]}
                     for k, v in PROFILES.items()],
        "modules": [{"key": m["key"], "name_ar": m["name_ar"], "name_en": m["name_en"]} for m in PLATFORM_MODULES],
        "actions": [a for a in ACTIONS if a["key"] != "manage_permissions"],
        "default_actions": DEFAULT_DEMO_ACTIONS,
        "cards": [{"key": k, "name_ar": v[0], "name_en": v[1], "module": v[2]} for k, v in CARDS.items()],
        "roles": ["company_admin", "ceo", "sales_manager", "sales_agent", "collection_officer", "accountant",
                  "finance_manager", "project_manager", "engineer", "hr_manager", "customer_service"],
    }


@router.get("")
async def list_demos(db: Annotated[AsyncSession, Depends(get_db)], _: Annotated[User, Depends(get_super_admin)]):
    return await DemoService.list_all(db)


@router.post("")
async def create_demo(
    data: DemoCreate, request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    actor: Annotated[User, Depends(get_super_admin)],
):
    company, demo, _credentials = await DemoService.create(db, data.model_dump(), actor)
    await log_audit(db, request, actor, "demo_created", "demos", "demo", demo.id, company_id=company.id,
                    after={"prospect": demo.prospect_name, "profile": demo.profile, "expires_at": demo.expires_at})
    # Prospects enter through the link only — demo user passwords are random and never returned.
    return await DemoService.describe(db, company, demo)


@router.get("/{demo_id}")
async def get_demo(demo_id: int, db: Annotated[AsyncSession, Depends(get_db)], _: Annotated[User, Depends(get_super_admin)]):
    company, demo = await DemoService.get(db, demo_id)
    return await DemoService.describe(db, company, demo)


@router.put("/{demo_id}")
async def update_demo(
    demo_id: int, data: DemoUpdate, request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    actor: Annotated[User, Depends(get_super_admin)],
):
    company, demo = await DemoService.get(db, demo_id)
    before = await DemoService.describe(db, company, demo)
    await DemoService.update(db, company, demo, data.model_dump(exclude_unset=True))
    after = await DemoService.describe(db, company, demo)
    keys = ("enabled_modules", "allowed_actions", "dashboard_cards", "expires_at", "is_enabled", "profile")
    await log_audit(db, request, actor, "demo_updated", "demos", "demo", demo.id, company_id=company.id,
                    before={k: before[k] for k in keys}, after={k: after[k] for k in keys})
    return after


@router.post("/{demo_id}/reset")
async def reset_demo(
    demo_id: int, request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    actor: Annotated[User, Depends(get_super_admin)],
):
    company, demo = await DemoService.get(db, demo_id)
    deleted = await DemoService.reset(db, company, demo)
    await log_audit(db, request, actor, "demo_reset", "demos", "demo", demo.id, company_id=company.id, details=f"rows removed: {deleted}")
    return {**(await DemoService.describe(db, company, demo)), "rows_removed": deleted}


@router.post("/{demo_id}/revoke")
async def revoke_demo(
    demo_id: int, request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    actor: Annotated[User, Depends(get_super_admin)],
):
    from datetime import timezone

    company, demo = await DemoService.get(db, demo_id)
    demo.revoked_at = datetime.now(timezone.utc)
    demo.is_enabled = False
    demo.updated_at = datetime.now(timezone.utc)
    await db.flush()
    await log_audit(db, request, actor, "demo_revoked", "demos", "demo", demo.id, company_id=company.id)
    return await DemoService.describe(db, company, demo)


@router.post("/{demo_id}/restore")
async def restore_demo(
    demo_id: int, request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    actor: Annotated[User, Depends(get_super_admin)],
):
    from datetime import timezone

    company, demo = await DemoService.get(db, demo_id)
    demo.revoked_at = None
    demo.is_enabled = True
    demo.updated_at = datetime.now(timezone.utc)
    await db.flush()
    await log_audit(db, request, actor, "demo_restored", "demos", "demo", demo.id, company_id=company.id)
    return await DemoService.describe(db, company, demo)


@router.post("/{demo_id}/link")
async def regenerate_demo_link(
    demo_id: int, request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    actor: Annotated[User, Depends(get_super_admin)],
):
    """Issue a new sign-in link; the previous link stops working immediately."""
    company, demo = await DemoService.get(db, demo_id)
    if not demo.link_user_id:
        users = await DemoService.users_of(db, company.id)
        if not users:
            raise HTTPException(status_code=400, detail="Demo has no user")
        demo.link_user_id = users[0].id
    DemoService.new_link(demo)
    await db.flush()
    await log_audit(db, request, actor, "demo_link_regenerated", "demos", "demo", demo.id, company_id=company.id)
    return await DemoService.describe(db, company, demo)


@router.post("/{demo_id}/users")
async def add_demo_user(
    demo_id: int, data: DemoUserIn, request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    actor: Annotated[User, Depends(get_super_admin)],
):
    company, demo = await DemoService.get(db, demo_id)
    credentials = await DemoService.add_user(db, company, data.role, data.full_name)
    await log_audit(db, request, actor, "demo_user_created", "demos", "user", credentials["user_id"], company_id=company.id,
                    after={"role": data.role})
    return credentials


@router.get("/{demo_id}/audit")
async def demo_audit(
    demo_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_super_admin)],
    limit: int = 200,
):
    company, _demo = await DemoService.get(db, demo_id)
    rows = (
        await db.execute(
            select(AuditLog, User).outerjoin(User, AuditLog.user_id == User.id)
            .where(AuditLog.company_id == company.id).order_by(AuditLog.id.desc()).limit(min(max(limit, 1), 1000))
        )
    ).all()
    return [
        {"id": a.id, "action": a.action, "module": a.module, "entity_type": a.entity_type, "entity_id": a.entity_id,
         "user": u.username if u else None, "ip_address": a.ip_address, "created_at": str(a.created_at), "details": a.details,
         "changes": json.loads(a.changes) if a.changes else None}
        for a, u in rows
    ]
