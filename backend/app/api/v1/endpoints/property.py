from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_company_user
from app.core.database import get_db
from app.models.property import HandoverRecord, MaintenanceRequest
from app.models.users import User

router = APIRouter()


class MaintenanceCreate(BaseModel):
    unit_id: int
    customer_id: Optional[int] = None
    title: str
    description: Optional[str] = None
    priority: str = "medium"


@router.get("/maintenance")
async def list_maintenance(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_company_user)],
):
    query = select(MaintenanceRequest).order_by(MaintenanceRequest.id.desc())
    if not current_user.is_super_admin:
        query = query.where(MaintenanceRequest.company_id == current_user.company_id)
    result = await db.execute(query)
    requests = result.scalars().all()
    return [
        {"id": r.id, "unit_id": r.unit_id, "title": r.title, "priority": r.priority, "status": r.status}
        for r in requests
    ]


@router.post("/maintenance")
async def create_maintenance(
    data: MaintenanceCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_company_user)],
):
    if not current_user.company_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Company required")
    req = MaintenanceRequest(company_id=current_user.company_id, **data.model_dump())
    db.add(req)
    await db.flush()
    return {"id": req.id, "status": req.status}


@router.get("/handovers")
async def list_handovers(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_company_user)],
):
    query = select(HandoverRecord).order_by(HandoverRecord.id.desc())
    if not current_user.is_super_admin:
        query = query.where(HandoverRecord.company_id == current_user.company_id)
    result = await db.execute(query)
    handovers = result.scalars().all()
    return [
        {"id": h.id, "unit_id": h.unit_id, "customer_id": h.customer_id, "handover_date": h.handover_date, "status": h.status}
        for h in handovers
    ]
