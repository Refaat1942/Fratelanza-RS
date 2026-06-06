from decimal import Decimal
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_company_user
from app.core.database import get_db
from app.models.brokers import Broker, BrokerCommission, CommissionStatus
from app.models.users import User

router = APIRouter()


class BrokerCreate(BaseModel):
    name_ar: str
    name_en: str
    mobile: str
    email: Optional[str] = None
    license_number: Optional[str] = None
    commission_rate: Decimal = Decimal("2.5")


class BrokerUpdate(BaseModel):
    name_ar: Optional[str] = None
    name_en: Optional[str] = None
    mobile: Optional[str] = None
    email: Optional[str] = None
    license_number: Optional[str] = None
    commission_rate: Optional[Decimal] = None
    is_active: Optional[bool] = None


@router.get("")
async def list_brokers(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_company_user)],
):
    query = select(Broker).where(Broker.is_deleted == False)
    if not current_user.is_super_admin:
        query = query.where(Broker.company_id == current_user.company_id)
    result = await db.execute(query.order_by(Broker.rank_score.desc()))
    brokers = result.scalars().all()
    return [
        {
            "id": b.id,
            "name_ar": b.name_ar,
            "name_en": b.name_en,
            "mobile": b.mobile,
            "email": b.email,
            "commission_rate": float(b.commission_rate),
            "total_sales": float(b.total_sales),
            "rank_score": b.rank_score,
            "is_active": b.is_active,
        }
        for b in brokers
    ]


@router.post("")
async def create_broker(
    data: BrokerCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_company_user)],
):
    if not current_user.company_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Company required")
    broker = Broker(company_id=current_user.company_id, **data.model_dump())
    db.add(broker)
    await db.flush()
    return {"id": broker.id, "name_ar": broker.name_ar}


@router.put("/{broker_id}")
async def update_broker(
    broker_id: int,
    data: BrokerUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_company_user)],
):
    result = await db.execute(select(Broker).where(Broker.id == broker_id, Broker.is_deleted == False))
    broker = result.scalar_one_or_none()
    if not broker:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Broker not found")
    if not current_user.is_super_admin and broker.company_id != current_user.company_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(broker, field, value)
    await db.flush()
    return {"id": broker.id, "name_ar": broker.name_ar, "success": True}


@router.delete("/{broker_id}")
async def delete_broker(
    broker_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_company_user)],
):
    result = await db.execute(select(Broker).where(Broker.id == broker_id, Broker.is_deleted == False))
    broker = result.scalar_one_or_none()
    if not broker:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Broker not found")
    if not current_user.is_super_admin and broker.company_id != current_user.company_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    broker.soft_delete()
    await db.flush()
    return {"message": "Broker deleted", "success": True}


@router.get("/commissions")
async def list_commissions(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_company_user)],
):
    query = (
        select(BrokerCommission, Broker)
        .join(Broker, BrokerCommission.broker_id == Broker.id)
        .order_by(BrokerCommission.id.desc())
    )
    if not current_user.is_super_admin:
        query = query.where(Broker.company_id == current_user.company_id)
    result = await db.execute(query)
    return [
        {
            "id": c.id,
            "broker_id": c.broker_id,
            "broker_name": b.name_ar,
            "amount": float(c.amount),
            "status": c.status.value,
            "contract_id": c.contract_id,
        }
        for c, b in result.all()
    ]


@router.post("/commissions/{commission_id}/approve")
async def approve_commission(
    commission_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_company_user)],
):
    result = await db.execute(select(BrokerCommission).where(BrokerCommission.id == commission_id))
    commission = result.scalar_one_or_none()
    if not commission:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Commission not found")
    commission.status = CommissionStatus.APPROVED
    commission.approved_by_id = current_user.id
    await db.flush()
    return {"id": commission.id, "status": commission.status.value}
