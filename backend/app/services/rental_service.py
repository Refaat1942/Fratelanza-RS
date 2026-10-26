"""Rental contract lifecycle and rent collection.

Rules
* ``rent_amount`` is the monthly rent. Receivables are generated per billing period
  (monthly / quarterly / semiannual / annual) starting at ``start_date``; a final partial period
  is pro-rated by days. Generation is idempotent (unique contract+period, ON CONFLICT DO NOTHING).
* Renewal creates a *new* contract linked by ``renewed_from_id``; the old contract keeps its
  dates, rent and receivables and is marked ``renewed``.
* Termination keeps history; unpaid receivables for periods starting after the termination date
  are cancelled (``status = cancelled``), never deleted.
* Collections on owner-managed units are a liability to the owner (Cr 2100), never company revenue.
"""

import calendar
import uuid
from datetime import date, datetime, timedelta, timezone
from decimal import ROUND_HALF_UP, Decimal
from typing import Optional
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.tenant import get_owned
from app.models.customers import Customer
from app.models.real_estate import Unit
from app.models.rentals import (
    RENT_FREQUENCIES,
    PropertyOwner,
    RentAdjustment,
    RentalContract,
    RentPayment,
    RentReceivable,
)
from app.models.tenant import Company
from app.services import accounting_service as acc
from app.services.accounting_service import AccountingService

ZERO = Decimal("0")
CENT = Decimal("0.01")
EXPIRING_WINDOW_DAYS = 60


def money(value) -> Decimal:
    return Decimal(str(value or 0)).quantize(CENT, rounding=ROUND_HALF_UP)


def add_months(d: date, months: int) -> date:
    month_index = d.month - 1 + months
    year = d.year + month_index // 12
    month = month_index % 12 + 1
    day = min(d.day, calendar.monthrange(year, month)[1])
    return date(year, month, day)


def company_today(company: Optional[Company]) -> date:
    """'Today' in the tenant's timezone — schedules must not drift around midnight UTC."""
    tz_name = getattr(company, "timezone", None) or "Africa/Cairo"
    try:
        tz = ZoneInfo(tz_name)
    except (ZoneInfoNotFoundError, ValueError):
        tz = ZoneInfo("UTC")
    return datetime.now(timezone.utc).astimezone(tz).date()


def outstanding(r: RentReceivable) -> Decimal:
    return money(r.amount_due) - money(r.adjustment_amount) - money(r.amount_paid)


def receivable_status(r: RentReceivable, today: date) -> str:
    """Display status (stored status + derived overdue)."""
    if r.status in ("cancelled", "waived", "paid"):
        return r.status
    if outstanding(r) > 0 and r.due_date < today:
        return "overdue"
    return r.status


def contract_display_status(c: RentalContract, today: date) -> str:
    if c.status == "active":
        if c.end_date < today:
            return "expired"
        if (c.end_date - today).days <= EXPIRING_WINDOW_DAYS:
            return "expiring"
    return c.status


def build_periods(start: date, end: date, frequency: str, monthly_rent: Decimal) -> list[dict]:
    months = RENT_FREQUENCIES.get(frequency)
    if not months:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid payment frequency")
    periods = []
    full_amount = money(monthly_rent * months)
    index = 0
    cursor = start
    while cursor <= end:
        # Anchor every period on the original start so the due day never drifts (31 → 28 → 28 ...)
        nominal_end = add_months(start, (index + 1) * months) - timedelta(days=1)
        period_end = min(nominal_end, end)
        if period_end == nominal_end:
            amount = full_amount
        else:
            nominal_days = (nominal_end - cursor).days + 1
            actual_days = (period_end - cursor).days + 1
            amount = money(full_amount * Decimal(actual_days) / Decimal(nominal_days))
        periods.append({"period_start": cursor, "period_end": period_end, "due_date": cursor, "amount_due": amount})
        index += 1
        cursor = period_end + timedelta(days=1)
    return periods


class RentalService:
    # ------------------------------------------------------------------ contracts
    @staticmethod
    async def _active_contract_for_unit(
        db: AsyncSession, unit_id: int, exclude_id: Optional[int] = None
    ) -> Optional[RentalContract]:
        query = select(RentalContract).where(
            RentalContract.unit_id == unit_id,
            RentalContract.status == "active",
            RentalContract.is_deleted == False,  # noqa: E712
        )
        if exclude_id:
            query = query.where(RentalContract.id != exclude_id)
        return (await db.execute(query)).scalars().first()

    @staticmethod
    async def create_contract(db: AsyncSession, company_id: int, data: dict, user_id: Optional[int]) -> RentalContract:
        unit = await get_owned(db, Unit, data["unit_id"], company_id, entity_name="Unit")
        owner_id = data.get("owner_id") or unit.owner_id
        if owner_id:
            await get_owned(db, PropertyOwner, owner_id, company_id, entity_name="Owner")
        tenant_customer_id = data.get("tenant_customer_id")
        if tenant_customer_id:
            customer = await get_owned(db, Customer, tenant_customer_id, company_id, entity_name="Customer")
            data["tenant_name"] = data.get("tenant_name") or customer.full_name_ar
            data["tenant_mobile"] = data.get("tenant_mobile") or customer.mobile
        if not data.get("tenant_name"):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Tenant name required")
        if data["end_date"] <= data["start_date"]:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="End date must be after start date")
        if money(data["rent_amount"]) <= 0:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Rent must be positive")
        if data.get("payment_frequency", "monthly") not in RENT_FREQUENCIES:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid payment frequency")
        assigned_to_id = data.get("assigned_to_id")
        if assigned_to_id:
            from app.models.users import User

            await get_owned(db, User, assigned_to_id, company_id, entity_name="User")
        activate = bool(data.pop("activate", False))
        contract_number = data.pop("contract_number", None) or f"RC-{uuid.uuid4().hex[:8].upper()}"
        exists = (
            await db.execute(
                select(RentalContract.id).where(
                    RentalContract.company_id == company_id, RentalContract.contract_number == contract_number
                )
            )
        ).first()
        if exists:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Contract number already exists")
        contract = RentalContract(
            company_id=company_id,
            contract_number=contract_number,
            owner_id=owner_id,
            status="draft",
            created_by_id=user_id,
            assigned_to_id=assigned_to_id or user_id,
            **{k: v for k, v in data.items() if k not in ("owner_id", "assigned_to_id")},
        )
        db.add(contract)
        await db.flush()
        if activate:
            await RentalService.activate(db, contract)
        return contract

    @staticmethod
    async def activate(db: AsyncSession, contract: RentalContract) -> RentalContract:
        if contract.status != "draft":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only draft contracts can be activated")
        conflict = await RentalService._active_contract_for_unit(db, contract.unit_id, exclude_id=contract.id)
        if conflict:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Unit already has an active lease ({conflict.contract_number})",
            )
        contract.status = "active"
        unit = (await db.execute(select(Unit).where(Unit.id == contract.unit_id))).scalar_one()
        unit.occupancy_status = "occupied"
        await db.flush()
        await RentalService.generate_receivables(db, contract)
        if money(contract.deposit_amount) > 0:
            await AccountingService.post(
                db,
                contract.company_id,
                source_type="rental_deposit",
                source_id=contract.id,
                entry_date=contract.start_date,
                description=f"Security deposit — {contract.contract_number}",
                lines=[(acc.CASH, money(contract.deposit_amount), ZERO), (acc.DEPOSITS, ZERO, money(contract.deposit_amount))],
            )
        return contract

    @staticmethod
    async def generate_receivables(db: AsyncSession, contract: RentalContract, up_to: Optional[date] = None) -> int:
        """Insert missing receivables for the contract. Safe to call any number of times."""
        if contract.status != "active":
            return 0
        periods = build_periods(contract.start_date, contract.end_date, contract.payment_frequency, contract.rent_amount)
        if up_to:
            periods = [p for p in periods if p["period_start"] <= up_to]
        if not periods:
            return 0
        rows = [
            {
                "company_id": contract.company_id,
                "rental_contract_id": contract.id,
                "amount_paid": ZERO,
                "adjustment_amount": ZERO,
                "status": "pending",
                **p,
            }
            for p in periods
        ]
        stmt = pg_insert(RentReceivable).values(rows).on_conflict_do_nothing(
            index_elements=["rental_contract_id", "period_start"]
        )
        result = await db.execute(stmt)
        await db.flush()
        return result.rowcount or 0

    @staticmethod
    async def terminate(
        db: AsyncSession, contract: RentalContract, termination_date: date, reason: str
    ) -> RentalContract:
        if contract.status not in ("active", "draft"):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Contract is not active")
        if termination_date < contract.start_date:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Termination before start date")
        contract.status = "terminated"
        contract.termination_date = termination_date
        contract.termination_reason = reason
        future = (
            await db.execute(
                select(RentReceivable).where(
                    RentReceivable.rental_contract_id == contract.id,
                    RentReceivable.period_start > termination_date,
                    RentReceivable.status.in_(["pending"]),
                )
            )
        ).scalars().all()
        for r in future:
            if money(r.amount_paid) == 0:
                r.status = "cancelled"
        unit = (await db.execute(select(Unit).where(Unit.id == contract.unit_id))).scalar_one()
        unit.occupancy_status = "vacant"
        await db.flush()
        return contract

    @staticmethod
    async def renew(
        db: AsyncSession,
        contract: RentalContract,
        *,
        new_end_date: date,
        new_rent_amount: Optional[Decimal],
        payment_frequency: Optional[str],
        user_id: Optional[int],
        notes: Optional[str] = None,
    ) -> RentalContract:
        if contract.status != "active":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only active contracts can be renewed")
        new_start = contract.end_date + timedelta(days=1)
        if new_end_date <= new_start:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="New end date must be after renewal start")
        # Old contract keeps its dates and rent untouched — only its status changes.
        contract.status = "renewed"
        await db.flush()
        renewed = RentalContract(
            company_id=contract.company_id,
            contract_number=f"{contract.contract_number}-R{uuid.uuid4().hex[:4].upper()}",
            unit_id=contract.unit_id,
            owner_id=contract.owner_id,
            tenant_customer_id=contract.tenant_customer_id,
            tenant_name=contract.tenant_name,
            tenant_mobile=contract.tenant_mobile,
            tenant_id_number=contract.tenant_id_number,
            start_date=new_start,
            end_date=new_end_date,
            rent_amount=money(new_rent_amount) if new_rent_amount else contract.rent_amount,
            payment_frequency=payment_frequency or contract.payment_frequency,
            due_day=contract.due_day,
            deposit_amount=ZERO,  # deposit carries over; it is not collected twice
            other_charges=contract.other_charges,
            payment_terms=contract.payment_terms,
            commission_rate=contract.commission_rate,
            status="draft",
            renewed_from_id=contract.id,
            notes=notes,
            assigned_to_id=contract.assigned_to_id,
            created_by_id=user_id,
        )
        db.add(renewed)
        await db.flush()
        await RentalService.activate(db, renewed)
        return renewed

    # ------------------------------------------------------------------ collections
    @staticmethod
    async def _locked_receivable(db: AsyncSession, receivable_id: int, company_id: int) -> RentReceivable:
        r = (
            await db.execute(
                select(RentReceivable)
                .where(RentReceivable.id == receivable_id, RentReceivable.company_id == company_id)
                .with_for_update()
            )
        ).scalar_one_or_none()
        if not r:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Receivable not found")
        return r

    @staticmethod
    def _refresh_status(r: RentReceivable) -> None:
        if r.status == "cancelled":
            return
        remaining = outstanding(r)
        if remaining <= 0:
            r.status = "waived" if money(r.amount_paid) == 0 and money(r.adjustment_amount) > 0 else "paid"
        elif money(r.amount_paid) > 0:
            r.status = "partial"
        else:
            r.status = "pending"

    @staticmethod
    async def record_payment(
        db: AsyncSession,
        company_id: int,
        receivable_id: int,
        *,
        amount: Decimal,
        paid_on: date,
        method: str,
        receipt_reference: Optional[str],
        notes: Optional[str],
        user_id: Optional[int],
    ) -> RentPayment:
        amount = money(amount)
        r = await RentalService._locked_receivable(db, receivable_id, company_id)
        if r.status == "cancelled":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Receivable is cancelled")
        if amount <= 0:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Amount must be positive")
        remaining = outstanding(r)
        if amount > remaining:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Amount exceeds outstanding balance ({remaining})",
            )
        contract = (await db.execute(select(RentalContract).where(RentalContract.id == r.rental_contract_id))).scalar_one()
        r.amount_paid = money(r.amount_paid) + amount
        RentalService._refresh_status(r)
        payment = RentPayment(
            company_id=company_id,
            receivable_id=r.id,
            rental_contract_id=contract.id,
            kind="payment",
            amount=amount,
            paid_on=paid_on,
            method=method,
            receipt_reference=receipt_reference or f"RCPT-{uuid.uuid4().hex[:8].upper()}",
            notes=notes,
            received_by_id=user_id,
        )
        db.add(payment)
        await db.flush()
        credit = acc.OWNER_PAYABLE if contract.owner_id else acc.RENTAL_INCOME
        await AccountingService.post(
            db,
            company_id,
            source_type="rent_payment",
            source_id=payment.id,
            entry_date=paid_on,
            description=f"Rent collected — {contract.contract_number} ({r.period_start}..{r.period_end})",
            lines=[(acc.CASH, amount, ZERO), (credit, ZERO, amount)],
            created_by_id=user_id,
        )
        return payment

    @staticmethod
    async def record_refund(
        db: AsyncSession,
        company_id: int,
        receivable_id: int,
        *,
        amount: Decimal,
        paid_on: date,
        method: str,
        notes: Optional[str],
        user_id: Optional[int],
    ) -> RentPayment:
        amount = money(amount)
        r = await RentalService._locked_receivable(db, receivable_id, company_id)
        if amount <= 0 or amount > money(r.amount_paid):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Refund exceeds amount paid")
        contract = (await db.execute(select(RentalContract).where(RentalContract.id == r.rental_contract_id))).scalar_one()
        r.amount_paid = money(r.amount_paid) - amount
        RentalService._refresh_status(r)
        refund = RentPayment(
            company_id=company_id,
            receivable_id=r.id,
            rental_contract_id=contract.id,
            kind="refund",
            amount=amount,
            paid_on=paid_on,
            method=method,
            receipt_reference=f"RFND-{uuid.uuid4().hex[:8].upper()}",
            notes=notes,
            received_by_id=user_id,
        )
        db.add(refund)
        await db.flush()
        debit = acc.OWNER_PAYABLE if contract.owner_id else acc.RENTAL_INCOME
        await AccountingService.post(
            db,
            company_id,
            source_type="rent_refund",
            source_id=refund.id,
            entry_date=paid_on,
            description=f"Rent refund — {contract.contract_number}",
            lines=[(debit, amount, ZERO), (acc.CASH, ZERO, amount)],
            created_by_id=user_id,
        )
        return refund

    @staticmethod
    async def adjust(
        db: AsyncSession, company_id: int, receivable_id: int, *, amount: Decimal, reason: str, user_id: Optional[int]
    ) -> RentAdjustment:
        amount = money(amount)
        r = await RentalService._locked_receivable(db, receivable_id, company_id)
        if amount <= 0 or amount > outstanding(r):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Waiver must be within outstanding balance")
        if not reason or len(reason.strip()) < 3:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="A reason is required")
        r.adjustment_amount = money(r.adjustment_amount) + amount
        RentalService._refresh_status(r)
        adjustment = RentAdjustment(
            company_id=company_id, receivable_id=r.id, amount=amount, reason=reason.strip(), approved_by_id=user_id
        )
        db.add(adjustment)
        await db.flush()
        return adjustment

    # ------------------------------------------------------------------ queries
    @staticmethod
    async def contract_balances(db: AsyncSession, company_id: int, contract_ids: list[int]) -> dict[int, dict]:
        if not contract_ids:
            return {}
        rows = (
            await db.execute(
                select(RentReceivable).where(
                    RentReceivable.company_id == company_id,
                    RentReceivable.rental_contract_id.in_(contract_ids),
                    RentReceivable.status != "cancelled",
                )
            )
        ).scalars().all()
        result: dict[int, dict] = {}
        for r in rows:
            b = result.setdefault(r.rental_contract_id, {"billed": ZERO, "paid": ZERO, "waived": ZERO, "outstanding": ZERO, "overdue": ZERO})
            b["billed"] += money(r.amount_due)
            b["paid"] += money(r.amount_paid)
            b["waived"] += money(r.adjustment_amount)
            b["outstanding"] += outstanding(r)
        return result

    @staticmethod
    async def overdue_total(db: AsyncSession, company_id: int, today: date) -> Decimal:
        value = (
            await db.execute(
                select(
                    func.coalesce(
                        func.sum(RentReceivable.amount_due - RentReceivable.adjustment_amount - RentReceivable.amount_paid), 0
                    )
                ).where(
                    RentReceivable.company_id == company_id,
                    RentReceivable.status.in_(["pending", "partial"]),
                    RentReceivable.due_date < today,
                )
            )
        ).scalar()
        return money(value)

    @staticmethod
    def receivable_dict(r: RentReceivable, contract: Optional[RentalContract], unit: Optional[Unit], today: date) -> dict:
        remaining = outstanding(r)
        disp = receivable_status(r, today)
        return {
            "id": r.id,
            "rental_contract_id": r.rental_contract_id,
            "contract_number": contract.contract_number if contract else None,
            "tenant_name": contract.tenant_name if contract else None,
            "tenant_mobile": contract.tenant_mobile if contract else None,
            "unit_id": unit.id if unit else None,
            "unit_code": unit.unit_code if unit else None,
            "period_start": r.period_start.isoformat(),
            "period_end": r.period_end.isoformat(),
            "due_date": r.due_date.isoformat(),
            "amount_due": float(money(r.amount_due)),
            "amount_paid": float(money(r.amount_paid)),
            "adjustment_amount": float(money(r.adjustment_amount)),
            "outstanding": float(remaining),
            "status": disp,
            "overdue_days": (today - r.due_date).days if disp == "overdue" else 0,
        }
