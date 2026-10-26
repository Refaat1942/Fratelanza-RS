from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_company_user
from app.core.database import get_db
from app.models.customers import Customer
from app.models.real_estate import Unit
from app.models.sales import Reservation, ReservationStatus
from app.models.users import User
from app.schemas.project import ReservationCreate, ReservationUpdate
from app.services.reservation_service import ReservationService

router = APIRouter()


def _reservation_dict(r: Reservation, customer: Customer | None = None, unit: Unit | None = None) -> dict:
    return {
        "id": r.id,
        "reservation_number": r.reservation_number,
        "customer_id": r.customer_id,
        "customer_name": (customer.full_name_ar if customer else None),
        "unit_id": r.unit_id,
        "unit_code": (unit.unit_code if unit else None),
        "deposit_amount": float(r.deposit_amount),
        "status": r.status.value,
        "reservation_date": r.reservation_date,
        "expiry_date": r.expiry_date,
        "notes": r.notes,
    }


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
    reservation = await ReservationService.approve_reservation(
        db, reservation_id, current_user.id, None if current_user.is_super_admin else current_user.company_id
    )
    return {"id": reservation.id, "status": reservation.status.value}


@router.get("")
async def list_reservations(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_company_user)],
):
    query = (
        select(Reservation, Customer, Unit)
        .join(Customer, Reservation.customer_id == Customer.id)
        .join(Unit, Reservation.unit_id == Unit.id)
        .where(Reservation.is_deleted == False)
    )
    if not current_user.is_super_admin:
        query = query.where(Reservation.company_id == current_user.company_id)
    result = await db.execute(query.order_by(Reservation.id.desc()))
    return [_reservation_dict(r, c, u) for r, c, u in result.all()]


@router.put("/{reservation_id}")
async def update_reservation(
    reservation_id: int,
    data: ReservationUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_company_user)],
):
    result = await db.execute(
        select(Reservation).where(Reservation.id == reservation_id, Reservation.is_deleted == False)
    )
    reservation = result.scalar_one_or_none()
    if not reservation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Reservation not found")
    if not current_user.is_super_admin and reservation.company_id != current_user.company_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    from app.core.tenant import ensure_refs

    await ensure_refs(db, reservation.company_id, [(Customer, data.customer_id, "Customer")])
    for field, value in data.model_dump(exclude_unset=True).items():
        if field == "status" and value:
            setattr(reservation, field, ReservationStatus(value))
        else:
            setattr(reservation, field, value)
    await db.flush()
    cust = (await db.execute(select(Customer).where(Customer.id == reservation.customer_id))).scalar_one_or_none()
    unit = (await db.execute(select(Unit).where(Unit.id == reservation.unit_id))).scalar_one_or_none()
    return _reservation_dict(reservation, cust, unit)


@router.delete("/{reservation_id}")
async def delete_reservation(
    reservation_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_company_user)],
):
    result = await db.execute(
        select(Reservation).where(Reservation.id == reservation_id, Reservation.is_deleted == False)
    )
    reservation = result.scalar_one_or_none()
    if not reservation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Reservation not found")
    if not current_user.is_super_admin and reservation.company_id != current_user.company_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    if reservation.status == ReservationStatus.CONVERTED:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot delete converted reservation")
    unit = (await db.execute(select(Unit).where(Unit.id == reservation.unit_id))).scalar_one_or_none()
    if unit and reservation.status in (ReservationStatus.APPROVED, ReservationStatus.PENDING_APPROVAL, ReservationStatus.DRAFT):
        from app.models.real_estate import UnitStatus
        unit.is_locked = False
        unit.status = UnitStatus.AVAILABLE
    reservation.soft_delete()
    await db.flush()
    return {"message": "Reservation deleted", "success": True}
