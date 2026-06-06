from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_company_user, get_super_admin
from app.core.database import get_db
from app.models.users import User
from app.schemas.dashboard import DashboardResponse
from app.services.dashboard_service import DashboardService

router = APIRouter()


@router.get("/super-admin", response_model=DashboardResponse)
async def super_admin_dashboard(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_super_admin)],
):
    return await DashboardService.super_admin_dashboard(db)


@router.get("/company", response_model=DashboardResponse)
async def company_dashboard(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_company_user)],
):
    if not current_user.company_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Company required")
    return await DashboardService.company_dashboard(db, current_user.company_id)


@router.post("/reseed-demo")
async def reseed_demo_data(
    current_user: Annotated[User, Depends(get_company_user)],
):
    """Backfill missing demo records (reservations, brokers, warehouse, etc.) for the company."""
    if not current_user.company_id and not current_user.is_super_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Company required")
    from app.utils.seed import seed_database

    await seed_database()
    return {"success": True, "message": "Demo data backfill completed"}
