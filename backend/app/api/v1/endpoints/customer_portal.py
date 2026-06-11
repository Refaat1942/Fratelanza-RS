from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.users import User
from app.services.customer_portal_service import CustomerPortalService

router = APIRouter()


@router.get("/dashboard")
async def customer_dashboard(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    customer = await CustomerPortalService.resolve_customer(db, current_user)
    return await CustomerPortalService.get_dashboard(db, customer)


@router.get("/installments")
async def customer_installments(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    customer = await CustomerPortalService.resolve_customer(db, current_user)
    return await CustomerPortalService.list_installments(db, customer)


@router.get("/payments")
async def customer_payments(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    customer = await CustomerPortalService.resolve_customer(db, current_user)
    return await CustomerPortalService.list_payments(db, customer)


@router.get("/construction-updates")
async def customer_construction_updates(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    customer = await CustomerPortalService.resolve_customer(db, current_user)
    return await CustomerPortalService.list_progress_updates(db, customer)
