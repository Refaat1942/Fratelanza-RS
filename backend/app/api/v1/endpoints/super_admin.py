import os
import subprocess
from datetime import datetime
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_super_admin
from app.core.config import settings
from app.core.database import get_db
from app.models.system import AuditLog, SystemSetting
from app.models.tenant import SubscriptionPlan
from app.models.users import User
from app.schemas.common import PaginatedResponse
from app.schemas.company import CompanyCreate, CompanyResponse, CompanyUpdate
from app.services.company_service import CompanyService

router = APIRouter()


@router.get("/companies", response_model=PaginatedResponse[CompanyResponse])
async def list_all_companies(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_super_admin)],
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    items, total = await CompanyService.list_companies(db, page, page_size)
    pages = (total + page_size - 1) // page_size
    return PaginatedResponse(
        items=[CompanyResponse.model_validate(c) for c in items],
        total=total,
        page=page,
        page_size=page_size,
        pages=pages,
    )


@router.post("/companies", response_model=CompanyResponse)
async def create_company(
    data: CompanyCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_super_admin)],
):
    company = await CompanyService.create_company(db, data)
    return CompanyResponse.model_validate(company)


@router.put("/companies/{company_id}", response_model=CompanyResponse)
async def update_company(
    company_id: int,
    data: CompanyUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_super_admin)],
):
    company = await CompanyService.update_company(db, company_id, data)
    return CompanyResponse.model_validate(company)


@router.post("/companies/{company_id}/suspend", response_model=CompanyResponse)
async def suspend_company(
    company_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_super_admin)],
):
    company = await CompanyService.suspend_company(db, company_id)
    return CompanyResponse.model_validate(company)


@router.get("/subscription-plans")
async def list_subscription_plans(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_super_admin)],
):
    result = await db.execute(select(SubscriptionPlan).where(SubscriptionPlan.is_active == True))
    plans = result.scalars().all()
    return [{"id": p.id, "name_ar": p.name_ar, "name_en": p.name_en, "code": p.code} for p in plans]


@router.get("/audit-logs")
async def list_audit_logs(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_super_admin)],
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    company_id: Optional[int] = None,
):
    query = select(AuditLog).order_by(AuditLog.id.desc())
    if company_id:
        query = query.where(AuditLog.company_id == company_id)
    total = (await db.execute(select(func.count()).select_from(query.subquery()))).scalar() or 0
    result = await db.execute(query.offset((page - 1) * page_size).limit(page_size))
    logs = result.scalars().all()
    return {
        "items": [
            {
                "id": log.id,
                "action": log.action,
                "module": log.module,
                "user_id": log.user_id,
                "company_id": log.company_id,
                "created_at": str(log.created_at),
            }
            for log in logs
        ],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.get("/settings")
async def list_settings(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_super_admin)],
):
    result = await db.execute(select(SystemSetting).order_by(SystemSetting.key))
    settings_list = result.scalars().all()
    return [{"key": s.key, "value": s.value, "description_ar": s.description_ar} for s in settings_list]


@router.post("/backup")
async def backup_database(
    _: Annotated[User, Depends(get_super_admin)],
):
    os.makedirs("/app/backups", exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"/app/backups/fratelanza_{timestamp}.sql"
    db_url = settings.DATABASE_URL_SYNC
    try:
        subprocess.run(
            ["pg_dump", db_url, "-f", filename],
            check=True,
            capture_output=True,
            timeout=120,
        )
        return {"success": True, "file": filename, "message": "Backup created"}
    except Exception as e:
        return {"success": False, "message": str(e)}


@router.get("/system-stats")
async def system_stats(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_super_admin)],
):
    from app.models.customers import Customer
    from app.models.real_estate import Project
    from app.models.sales import Contract
    from app.models.tenant import Company

    stats = {
        "companies": (await db.execute(select(func.count(Company.id)))).scalar(),
        "users": (await db.execute(select(func.count(User.id)))).scalar(),
        "customers": (await db.execute(select(func.count(Customer.id)))).scalar(),
        "projects": (await db.execute(select(func.count(Project.id)))).scalar(),
        "contracts": (await db.execute(select(func.count(Contract.id)))).scalar(),
    }
    return stats
