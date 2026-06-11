from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_company_admin, get_company_user, get_super_admin
from app.core.database import get_db
from app.models.users import User
from app.schemas.company import CompanyModulesUpdate, PortalFeaturesUpdate
from app.services.company_service import CompanyService
from app.services.customer_portal_feature_service import CustomerPortalFeatureService
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
        "enabled": ModuleService.parse_effective(company, plan, current_user),
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


@router.get("/company/me")
async def my_company_modules_admin(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_company_admin)],
):
    """Company admin view of modules enabled for their company (set by super admin)."""
    company = await CompanyService.get_company(db, current_user.company_id)  # type: ignore[arg-type]
    plan = company.subscription.plan if company.subscription else None
    return {
        "company_id": company.id,
        "enabled": ModuleService.parse_enabled(company, plan),
        "catalog": ModuleService.catalog(),
        "message": "Contact super admin to add or remove company-level features",
    }


@router.get("/company/me/portal-features")
async def my_company_portal_features(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_company_admin)],
):
    company = await CompanyService.get_company(db, current_user.company_id)  # type: ignore[arg-type]
    plan = company.subscription.plan if company.subscription else None
    company_modules = ModuleService.parse_enabled(company, plan)
    portal_module_on = "customer_portal" in company_modules
    return {
        "company_id": company.id,
        "portal_module_enabled": portal_module_on,
        "enabled": CustomerPortalFeatureService.parse_enabled(company) if portal_module_on else [],
        "catalog": CustomerPortalFeatureService.catalog(),
    }


@router.put("/company/me/portal-features")
async def update_my_company_portal_features(
    data: PortalFeaturesUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_company_admin)],
):
    company = await CompanyService.get_company(db, current_user.company_id)  # type: ignore[arg-type]
    plan = company.subscription.plan if company.subscription else None
    CustomerPortalFeatureService.assert_portal_module(company, plan)
    enabled = await CustomerPortalFeatureService.set_company_features(
        db, company, data.enabled_features
    )
    return {
        "company_id": company.id,
        "enabled": enabled,
        "message": "Buyer portal features updated",
    }


@router.get("/company/{company_id}/portal-features")
async def company_portal_features_admin(
    company_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_super_admin)],
):
    company = await CompanyService.get_company(db, company_id)
    return {
        "company_id": company.id,
        "enabled": CustomerPortalFeatureService.parse_enabled(company),
        "catalog": CustomerPortalFeatureService.catalog(),
    }


@router.put("/company/{company_id}/portal-features")
async def update_company_portal_features_admin(
    company_id: int,
    data: PortalFeaturesUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_super_admin)],
):
    company = await CompanyService.get_company(db, company_id)
    enabled = await CustomerPortalFeatureService.set_company_features(
        db, company, data.enabled_features
    )
    return {
        "company_id": company.id,
        "enabled": enabled,
        "message": "Buyer portal features updated",
    }
