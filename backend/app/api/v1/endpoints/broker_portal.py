from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.brokers import Broker, BrokerCommission
from app.models.crm import Lead
from app.models.sales import Contract, Reservation
from app.models.users import SystemRole, User

router = APIRouter()


@router.get("/dashboard")
async def broker_dashboard(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    if current_user.system_role != SystemRole.BROKER and not current_user.is_super_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Broker access only")
    broker_result = await db.execute(select(Broker).where(Broker.user_id == current_user.id))
    broker = broker_result.scalar_one_or_none()
    if not broker and not current_user.is_super_admin:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Broker profile not found")

    broker_id = broker.id if broker else 0
    leads_count = (await db.execute(select(func.count(Lead.id)).where(Lead.broker_id == broker_id))).scalar() or 0
    commissions = (
        await db.execute(select(BrokerCommission).where(BrokerCommission.broker_id == broker_id))
    ).scalars().all()

    return {
        "broker": {
            "name_ar": broker.name_ar if broker else "Demo",
            "rank_score": broker.rank_score if broker else 0,
            "total_sales": float(broker.total_sales) if broker else 0,
        },
        "leads_count": leads_count,
        "commissions": [
            {"id": c.id, "amount": float(c.amount), "status": c.status.value}
            for c in commissions
        ],
    }
