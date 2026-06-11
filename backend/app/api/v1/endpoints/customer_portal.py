from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.customers import Customer
from app.models.tenant import Company
from app.models.users import User
from app.services.company_service import CompanyService
from app.services.customer_portal_feature_service import CustomerPortalFeatureService
from app.services.customer_portal_service import CustomerPortalService

router = APIRouter()


async def _portal_company(db: AsyncSession, customer: Customer) -> Company:
    company = await CompanyService.get_company(db, customer.company_id)
    plan = company.subscription.plan if company.subscription else None
    CustomerPortalFeatureService.assert_portal_module(company, plan)
    return company


@router.get("/me")
async def customer_portal_me(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    customer = await CustomerPortalService.resolve_customer(db, current_user)
    company = await _portal_company(db, customer)
    enabled = CustomerPortalFeatureService.parse_enabled(company)
    return {
        "enabled": enabled,
        "catalog": CustomerPortalFeatureService.catalog(),
    }


@router.get("/dashboard")
async def customer_dashboard(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    customer = await CustomerPortalService.resolve_customer(db, current_user)
    company = await _portal_company(db, customer)
    CustomerPortalFeatureService.assert_feature(company, "dashboard")
    data = await CustomerPortalService.get_dashboard(db, customer)
    enabled = set(CustomerPortalFeatureService.parse_enabled(company))
    return CustomerPortalFeatureService.filter_dashboard(data, enabled)


@router.get("/installments")
async def customer_installments(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    customer = await CustomerPortalService.resolve_customer(db, current_user)
    company = await _portal_company(db, customer)
    CustomerPortalFeatureService.assert_feature(company, "installments")
    return await CustomerPortalService.list_installments(db, customer)


@router.get("/payments")
async def customer_payments(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    customer = await CustomerPortalService.resolve_customer(db, current_user)
    company = await _portal_company(db, customer)
    CustomerPortalFeatureService.assert_feature(company, "receipts")
    return await CustomerPortalService.list_payments(db, customer)


@router.get("/construction-updates")
async def customer_construction_updates(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    customer = await CustomerPortalService.resolve_customer(db, current_user)
    company = await _portal_company(db, customer)
    CustomerPortalFeatureService.assert_feature(company, "progress")
    return await CustomerPortalService.list_progress_updates(db, customer)
