from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_company_user
from app.core.database import get_db
from app.models.customers import Customer
from app.models.property import HandoverRecord, MaintenanceRequest
from app.models.real_estate import Unit
from app.models.users import User

router = APIRouter()


class MaintenanceCreate(BaseModel):
    unit_id: int
    customer_id: Optional[int] = None
    title: str
    description: Optional[str] = None
    priority: str = "medium"


class MaintenanceUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    priority: Optional[str] = None
    status: Optional[str] = None


@router.get("/summary")
async def property_summary(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_company_user)],
):
    query = select(MaintenanceRequest)
    if not current_user.is_super_admin:
        if not current_user.company_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Company required")
        query = query.where(MaintenanceRequest.company_id == current_user.company_id)
    requests = (await db.execute(query)).scalars().all()
    by_status: dict[str, int] = {}
    for r in requests:
        by_status[r.status] = by_status.get(r.status, 0) + 1
    return {
        "total": len(requests),
        "open": by_status.get("open", 0),
        "in_progress": by_status.get("in_progress", 0),
        "completed": by_status.get("completed", 0),
    }


@router.get("/maintenance")
async def list_maintenance(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_company_user)],
):
    query = (
        select(MaintenanceRequest, Unit, Customer)
        .join(Unit, MaintenanceRequest.unit_id == Unit.id)
        .outerjoin(Customer, MaintenanceRequest.customer_id == Customer.id)
        .order_by(MaintenanceRequest.id.desc())
    )
    if not current_user.is_super_admin:
        query = query.where(MaintenanceRequest.company_id == current_user.company_id)
    result = await db.execute(query)
    return [
        {
            "id": r.id,
            "unit_id": r.unit_id,
            "unit_code": u.unit_code,
            "customer_id": r.customer_id,
            "customer_name": c.full_name_ar if c else None,
            "title": r.title,
            "description": r.description,
            "priority": r.priority,
            "status": r.status,
        }
        for r, u, c in result.all()
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


@router.put("/maintenance/{request_id}")
async def update_maintenance(
    request_id: int,
    data: MaintenanceUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_company_user)],
):
    result = await db.execute(select(MaintenanceRequest).where(MaintenanceRequest.id == request_id))
    req = result.scalar_one_or_none()
    if not req:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Request not found")
    if not current_user.is_super_admin and req.company_id != current_user.company_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(req, field, value)
    await db.flush()
    return {"id": req.id, "success": True}


@router.delete("/maintenance/{request_id}")
async def delete_maintenance(
    request_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_company_user)],
):
    result = await db.execute(select(MaintenanceRequest).where(MaintenanceRequest.id == request_id))
    req = result.scalar_one_or_none()
    if not req:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Request not found")
    if not current_user.is_super_admin and req.company_id != current_user.company_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    await db.delete(req)
    await db.flush()
    return {"message": "Deleted", "success": True}


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
