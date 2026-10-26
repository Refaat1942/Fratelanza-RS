"""Owner settlements.

net_payable = gross rent collected for the owner (payments − refunds not yet settled, paid on or
              before period_end)
            − management commission (per contract rate, else owner rate) on that gross
            − approved owner-charged property expenses not yet settled (expense_date ≤ period_end)
            + authorised adjustments

Included payments and expenses are stamped with ``settlement_id`` so they can never be counted
in two settlements. Cancelling a settlement releases them again.
"""

import json
from datetime import date, timedelta
from decimal import Decimal
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.tenant import get_owned
from app.models.rentals import (
    SETTLEMENT_FREQUENCIES,
    OwnerSettlement,
    OwnerSettlementPayment,
    PropertyExpense,
    PropertyOwner,
    RentalContract,
    RentPayment,
)
from app.services import accounting_service as acc
from app.services.accounting_service import AccountingService
from app.services.rental_service import ZERO, add_months, money


def frequency_block(day: date, frequency: str) -> tuple[date, date]:
    """Calendar-aligned settlement period containing ``day``."""
    months = SETTLEMENT_FREQUENCIES.get(frequency, 1)
    start_month = ((day.month - 1) // months) * months + 1
    start = date(day.year, start_month, 1)
    end = add_months(start, months) - timedelta(days=1)
    return start, end


def next_settlement(owner: PropertyOwner, today: date) -> tuple[date, date, date]:
    """Period that most recently ended (or ends today) and its due date."""
    start, end = frequency_block(today, owner.settlement_frequency)
    if end > today:
        start, end = frequency_block(start - timedelta(days=1), owner.settlement_frequency)
    due = end + timedelta(days=max(owner.settlement_day or 0, 0))
    if due < today:
        # previous block already due — look at the current block
        start, end = frequency_block(today, owner.settlement_frequency)
        due = end + timedelta(days=max(owner.settlement_day or 0, 0))
    return start, end, due


class SettlementService:
    @staticmethod
    async def calculate(
        db: AsyncSession, company_id: int, owner: PropertyOwner, period_end: date
    ) -> dict:
        rows = (
            await db.execute(
                select(RentPayment, RentalContract)
                .join(RentalContract, RentPayment.rental_contract_id == RentalContract.id)
                .where(
                    RentPayment.company_id == company_id,
                    RentalContract.company_id == company_id,
                    RentalContract.owner_id == owner.id,
                    RentPayment.settlement_id.is_(None),
                    RentPayment.paid_on <= period_end,
                )
            )
        ).all()
        gross = ZERO
        commission = ZERO
        per_contract: dict[int, dict] = {}
        payment_ids = []
        for payment, contract in rows:
            sign = Decimal("-1") if payment.kind == "refund" else Decimal("1")
            amount = money(payment.amount) * sign
            rate = Decimal(str(contract.commission_rate if contract.commission_rate is not None else owner.commission_rate or 0))
            line_commission = money(amount * rate / Decimal("100"))
            gross += amount
            commission += line_commission
            payment_ids.append(payment.id)
            pc = per_contract.setdefault(
                contract.id,
                {"contract_number": contract.contract_number, "collected": ZERO, "commission_rate": float(rate), "commission": ZERO},
            )
            pc["collected"] += amount
            pc["commission"] += line_commission
        expenses = (
            await db.execute(
                select(PropertyExpense).where(
                    PropertyExpense.company_id == company_id,
                    PropertyExpense.owner_id == owner.id,
                    PropertyExpense.charged_to == "owner",
                    PropertyExpense.approval_status == "approved",
                    PropertyExpense.settlement_id.is_(None),
                    PropertyExpense.is_deleted == False,  # noqa: E712
                    PropertyExpense.expense_date <= period_end,
                )
            )
        ).scalars().all()
        expenses_total = sum((money(e.amount) for e in expenses), ZERO)
        return {
            "gross_collected": money(gross),
            "commission_amount": money(commission),
            "expenses_total": money(expenses_total),
            "payment_ids": payment_ids,
            "expense_ids": [e.id for e in expenses],
            "contracts": [
                {**v, "contract_id": k, "collected": float(v["collected"]), "commission": float(v["commission"])}
                for k, v in per_contract.items()
            ],
            "expenses": [
                {"id": e.id, "date": e.expense_date.isoformat(), "category": e.category, "amount": float(e.amount)}
                for e in expenses
            ],
        }

    @staticmethod
    async def create(
        db: AsyncSession,
        company_id: int,
        *,
        owner_id: int,
        period_start: date,
        period_end: date,
        adjustments: Decimal,
        adjustments_note: Optional[str],
        user_id: Optional[int],
    ) -> OwnerSettlement:
        owner = await get_owned(db, PropertyOwner, owner_id, company_id, entity_name="Owner")
        if period_end < period_start:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid period")
        duplicate = (
            await db.execute(
                select(OwnerSettlement.id).where(
                    OwnerSettlement.owner_id == owner.id,
                    OwnerSettlement.period_start == period_start,
                    OwnerSettlement.period_end == period_end,
                    OwnerSettlement.status != "cancelled",
                )
            )
        ).first()
        if duplicate:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Settlement for this period already exists")
        calc = await SettlementService.calculate(db, company_id, owner, period_end)
        adjustments = money(adjustments)
        net = calc["gross_collected"] - calc["commission_amount"] - calc["expenses_total"] + adjustments
        settlement = OwnerSettlement(
            company_id=company_id,
            owner_id=owner.id,
            period_start=period_start,
            period_end=period_end,
            due_date=period_end + timedelta(days=max(owner.settlement_day or 0, 0)),
            gross_collected=calc["gross_collected"],
            expenses_total=calc["expenses_total"],
            commission_amount=calc["commission_amount"],
            adjustments=adjustments,
            adjustments_note=adjustments_note,
            net_payable=money(net),
            amount_paid=ZERO,
            status="draft",
            calculation=json.dumps(
                {"contracts": calc["contracts"], "expenses": calc["expenses"]}, ensure_ascii=False, default=str
            ),
            created_by_id=user_id,
        )
        db.add(settlement)
        await db.flush()
        if calc["payment_ids"]:
            await db.execute(
                update(RentPayment).where(RentPayment.id.in_(calc["payment_ids"])).values(settlement_id=settlement.id)
            )
        if calc["expense_ids"]:
            await db.execute(
                update(PropertyExpense)
                .where(PropertyExpense.id.in_(calc["expense_ids"]))
                .values(settlement_id=settlement.id)
            )
        await db.flush()
        return settlement

    @staticmethod
    async def approve(db: AsyncSession, settlement: OwnerSettlement, user_id: Optional[int]) -> OwnerSettlement:
        if settlement.status != "draft":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only draft settlements can be approved")
        settlement.status = "approved"
        settlement.approved_by_id = user_id
        await db.flush()
        commission = money(settlement.commission_amount)
        if commission > 0:
            # Commission becomes company revenue only when the settlement is approved
            await AccountingService.post(
                db,
                settlement.company_id,
                source_type="owner_settlement_commission",
                source_id=settlement.id,
                entry_date=settlement.period_end,
                description=f"Management commission — settlement #{settlement.id}",
                lines=[(acc.OWNER_PAYABLE, commission, ZERO), (acc.COMMISSION_INCOME, ZERO, commission)],
                created_by_id=user_id,
            )
        return settlement

    @staticmethod
    async def cancel(db: AsyncSession, settlement: OwnerSettlement) -> OwnerSettlement:
        if settlement.status != "draft":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only draft settlements can be cancelled")
        settlement.status = "cancelled"
        await db.execute(update(RentPayment).where(RentPayment.settlement_id == settlement.id).values(settlement_id=None))
        await db.execute(
            update(PropertyExpense).where(PropertyExpense.settlement_id == settlement.id).values(settlement_id=None)
        )
        await db.flush()
        return settlement

    @staticmethod
    async def pay(
        db: AsyncSession,
        settlement: OwnerSettlement,
        *,
        amount: Decimal,
        paid_on: date,
        method: str,
        reference: Optional[str],
        user_id: Optional[int],
    ) -> OwnerSettlementPayment:
        amount = money(amount)
        if settlement.status not in ("approved", "partial"):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Settlement must be approved before payment")
        remaining = money(settlement.net_payable) - money(settlement.amount_paid)
        if amount <= 0 or amount > remaining:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Amount must be within remaining balance ({remaining})")
        payment = OwnerSettlementPayment(
            company_id=settlement.company_id,
            settlement_id=settlement.id,
            amount=amount,
            paid_on=paid_on,
            method=method,
            reference=reference,
            paid_by_id=user_id,
        )
        db.add(payment)
        settlement.amount_paid = money(settlement.amount_paid) + amount
        settlement.status = "paid" if money(settlement.amount_paid) >= money(settlement.net_payable) else "partial"
        await db.flush()
        await AccountingService.post(
            db,
            settlement.company_id,
            source_type="owner_settlement_payment",
            source_id=payment.id,
            entry_date=paid_on,
            description=f"Owner payout — settlement #{settlement.id}",
            lines=[(acc.OWNER_PAYABLE, amount, ZERO), (acc.CASH, ZERO, amount)],
            created_by_id=user_id,
        )
        return payment

    @staticmethod
    def to_dict(s: OwnerSettlement, owner: Optional[PropertyOwner] = None) -> dict:
        return {
            "id": s.id,
            "owner_id": s.owner_id,
            "owner_name": owner.full_name if owner else None,
            "period_start": s.period_start.isoformat(),
            "period_end": s.period_end.isoformat(),
            "due_date": s.due_date.isoformat(),
            "gross_collected": float(s.gross_collected),
            "commission_amount": float(s.commission_amount),
            "expenses_total": float(s.expenses_total),
            "adjustments": float(s.adjustments),
            "adjustments_note": s.adjustments_note,
            "net_payable": float(s.net_payable),
            "amount_paid": float(s.amount_paid),
            "remaining": float(money(s.net_payable) - money(s.amount_paid)),
            "status": s.status,
            "calculation": json.loads(s.calculation) if s.calculation else None,
        }
