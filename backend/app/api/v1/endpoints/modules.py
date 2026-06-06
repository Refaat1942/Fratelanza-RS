from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_company_user, get_super_admin
from app.core.database import get_db
from app.models.users import User
from app.schemas.company import CompanyModulesUpdate
from app.services.company_service import CompanyService
from app.services.module_service import ModuleService

router = APIRouter()


@router.get("/catalog")
async def modules_catalog():
    return {"modules": ModuleService.catalog()}


@router.get("/me")
async def my_company_modules(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_company_user)],
):
    if current_user.is_super_admin:
        from app.core.platform_modules import ALL_MODULE_KEYS
        return {
            "enabled": ALL_MODULE_KEYS,
            "catalog": ModuleService.catalog(),
        }
    if not current_user.company_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Company required")
    company = await CompanyService.get_company(db, current_user.company_id)
    plan = company.subscription.plan if company.subscription else None
    return {
        "enabled": ModuleService.parse_enabled(company, plan),
        "catalog": ModuleService.catalog(),
    }


@router.get("/company/{company_id}")
async def company_modules_admin(
    company_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_super_admin)],
):
    company = await CompanyService.get_company(db, company_id)
    plan = company.subscription.plan if company.subscription else None
    return {
        "company_id": company.id,
        "enabled": ModuleService.parse_enabled(company, plan),
        "catalog": ModuleService.catalog(),
    }


@router.put("/company/{company_id}")
async def update_company_modules_admin(
    company_id: int,
    data: CompanyModulesUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_super_admin)],
):
    company = await CompanyService.get_company(db, company_id)
    enabled = await ModuleService.set_company_modules(db, company, data.enabled_modules)
    return {
        "company_id": company.id,
        "enabled": enabled,
        "message": "Company modules updated",
    }
