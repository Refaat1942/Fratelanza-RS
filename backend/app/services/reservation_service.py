import uuid
from datetime import datetime

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.real_estate import Unit, UnitStatus
from app.models.sales import Reservation, ReservationStatus
from app.schemas.project import ReservationCreate


class ReservationService:
    @staticmethod
    async def create_reservation(
        db: AsyncSession, company_id: int, data: ReservationCreate, created_by_id: int
    ) -> Reservation:
        from app.core.tenant import ensure_refs
        from app.models.customers import Customer

        await ensure_refs(db, company_id, [(Customer, data.customer_id, "Customer")])
        unit_result = await db.execute(
            select(Unit).where(Unit.id == data.unit_id, Unit.is_deleted == False, Unit.company_id == company_id)
        )
        unit = unit_result.scalar_one_or_none()
        if not unit:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Unit not found")
        if unit.status != UnitStatus.AVAILABLE or unit.is_locked:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unit is not available")

        active_reservation = await db.execute(
            select(Reservation).where(
                Reservation.unit_id == data.unit_id,
                Reservation.status.in_([
                    ReservationStatus.DRAFT,
                    ReservationStatus.PENDING_APPROVAL,
                    ReservationStatus.APPROVED,
                ]),
                Reservation.is_deleted == False,
            )
        )
        if active_reservation.scalar_one_or_none():
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unit already reserved")

        reservation = Reservation(
            company_id=company_id,
            reservation_number=f"RES-{uuid.uuid4().hex[:8].upper()}",
            customer_id=data.customer_id,
            unit_id=data.unit_id,
            deposit_amount=data.deposit_amount,
            reservation_date=data.reservation_date,
            expiry_date=data.expiry_date,
            status=ReservationStatus.PENDING_APPROVAL,
            created_by_id=created_by_id,
            notes=data.notes,
        )
        unit.is_locked = True
        unit.status = UnitStatus.RESERVED
        db.add(reservation)
        await db.flush()
        return reservation

    @staticmethod
    async def approve_reservation(
        db: AsyncSession, reservation_id: int, approved_by_id: int, company_id: int | None = None
    ) -> Reservation:
        query = select(Reservation).where(Reservation.id == reservation_id, Reservation.is_deleted == False)
        if company_id is not None:
            query = query.where(Reservation.company_id == company_id)
        result = await db.execute(query)
        reservation = result.scalar_one_or_none()
        if not reservation:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Reservation not found")
        reservation.status = ReservationStatus.APPROVED
        reservation.approved_by_id = approved_by_id
        await db.flush()
        return reservation

    @staticmethod
    async def expire_reservations(db: AsyncSession) -> int:
        today = datetime.now().strftime("%Y-%m-%d")
        result = await db.execute(
            select(Reservation).where(
                Reservation.expiry_date < today,
                Reservation.status == ReservationStatus.APPROVED,
            )
        )
        count = 0
        for reservation in result.scalars().all():
            reservation.status = ReservationStatus.EXPIRED
            unit_result = await db.execute(select(Unit).where(Unit.id == reservation.unit_id))
            unit = unit_result.scalar_one_or_none()
            if unit:
                unit.is_locked = False
                unit.status = UnitStatus.AVAILABLE
            count += 1
        await db.flush()
        return count
