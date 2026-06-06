from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_company_user
from app.core.database import get_db
from app.models.sales import Reservation
from app.models.users import User
from app.schemas.project import ReservationCreate
from app.services.reservation_service import ReservationService

router = APIRouter()


@router.post("")
async def create_reservation(
    data: ReservationCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_company_user)],
):
    if not current_user.company_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Company required")
    reservation = await ReservationService.create_reservation(
        db, current_user.company_id, data, current_user.id
    )
    return {
        "id": reservation.id,
        "reservation_number": reservation.reservation_number,
        "status": reservation.status.value,
    }


@router.post("/{reservation_id}/approve")
async def approve_reservation(
    reservation_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_company_user)],
):
    reservation = await ReservationService.approve_reservation(db, reservation_id, current_user.id)
    return {"id": reservation.id, "status": reservation.status.value}


@router.get("")
async def list_reservations(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_company_user)],
):
    query = select(Reservation).where(Reservation.is_deleted == False)
    if not current_user.is_super_admin:
        query = query.where(Reservation.company_id == current_user.company_id)
    result = await db.execute(query.order_by(Reservation.id.desc()))
    reservations = result.scalars().all()
    return [
        {
            "id": r.id,
            "reservation_number": r.reservation_number,
            "customer_id": r.customer_id,
            "unit_id": r.unit_id,
            "status": r.status.value,
            "expiry_date": r.expiry_date,
        }
        for r in reservations
    ]
