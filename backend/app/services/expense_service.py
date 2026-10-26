"""Property expenses and administrative expenses (accrual on approval, cash on payment)."""

from datetime import date
from decimal import Decimal
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.tenant import get_owned
from app.models.property import MaintenanceRequest
from app.models.real_estate import Unit
from app.models.rentals import AdminExpense, PropertyExpense, PropertyOwner
from app.services import accounting_service as acc
from app.services.accounting_service import AccountingService
from app.services.rental_service import ZERO, money


class ExpenseService:
    @staticmethod
    async def create_property_expense(
        db: AsyncSession, company_id: int, data: dict, user_id: Optional[int]
    ) -> PropertyExpense:
        unit = await get_owned(db, Unit, data["unit_id"], company_id, entity_name="Unit")
        owner_id = data.get("owner_id") or unit.owner_id
        if owner_id:
            await get_owned(db, PropertyOwner, owner_id, company_id, entity_name="Owner")
        if data.get("charged_to", "owner") == "owner" and not owner_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unit has no owner — charge to company")
        mr_id = data.get("maintenance_request_id")
        if mr_id:
            await get_owned(db, MaintenanceRequest, mr_id, company_id, entity_name="Maintenance request")
            exists = (
                await db.execute(select(PropertyExpense.id).where(PropertyExpense.maintenance_request_id == mr_id))
            ).first()
            if exists:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT, detail="An expense already exists for this maintenance request"
                )
        if money(data["amount"]) <= 0:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Amount must be positive")
        expense = PropertyExpense(
            company_id=company_id,
            created_by_id=user_id,
            owner_id=owner_id,
            approval_status="pending",
            payment_status="unpaid",
            **{k: v for k, v in data.items() if k != "owner_id"},
        )
        db.add(expense)
        await db.flush()
        return expense

    @staticmethod
    async def approve(db: AsyncSession, expense: PropertyExpense, user_id: Optional[int]) -> PropertyExpense:
        if expense.approval_status != "pending":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Expense already decided")
        expense.approval_status = "approved"
        expense.approved_by_id = user_id
        await db.flush()
        debit = acc.OWNER_PAYABLE if expense.charged_to == "owner" else acc.MAINTENANCE_EXPENSE
        await AccountingService.post(
            db,
            expense.company_id,
            source_type="property_expense",
            source_id=expense.id,
            entry_date=expense.expense_date,
            description=f"Property expense #{expense.id} — {expense.category}",
            lines=[(debit, money(expense.amount), ZERO), (acc.ACCOUNTS_PAYABLE, ZERO, money(expense.amount))],
            created_by_id=user_id,
        )
        return expense

    @staticmethod
    async def mark_paid(db: AsyncSession, expense: PropertyExpense, paid_on: date, user_id: Optional[int]) -> PropertyExpense:
        if expense.approval_status != "approved":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only approved expenses can be paid")
        if expense.payment_status == "paid":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Expense already paid")
        expense.payment_status = "paid"
        await db.flush()
        await AccountingService.post(
            db,
            expense.company_id,
            source_type="property_expense_payment",
            source_id=expense.id,
            entry_date=paid_on,
            description=f"Payment of property expense #{expense.id}",
            lines=[(acc.ACCOUNTS_PAYABLE, money(expense.amount), ZERO), (acc.CASH, ZERO, money(expense.amount))],
            created_by_id=user_id,
        )
        return expense

    @staticmethod
    async def create_admin_expense(db: AsyncSession, company_id: int, data: dict, user_id: Optional[int]) -> AdminExpense:
        if money(data["amount"]) <= 0:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Amount must be positive")
        expense = AdminExpense(company_id=company_id, created_by_id=user_id, amount_paid=ZERO, payment_status="unpaid", **data)
        db.add(expense)
        await db.flush()
        await AccountingService.post(
            db,
            company_id,
            source_type="admin_expense",
            source_id=expense.id,
            entry_date=expense.expense_date,
            description=f"Administrative expense #{expense.id} — {expense.category}",
            lines=[(acc.ADMIN_EXPENSE, money(expense.amount), ZERO), (acc.ACCOUNTS_PAYABLE, ZERO, money(expense.amount))],
            created_by_id=user_id,
        )
        return expense

    @staticmethod
    async def pay_admin_expense(
        db: AsyncSession, expense: AdminExpense, amount: Decimal, paid_on: date, user_id: Optional[int]
    ) -> AdminExpense:
        amount = money(amount)
        remaining = money(expense.amount) - money(expense.amount_paid)
        if amount <= 0 or amount > remaining:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Amount must be within remaining balance ({remaining})")
        expense.amount_paid = money(expense.amount_paid) + amount
        expense.payment_status = "paid" if money(expense.amount_paid) >= money(expense.amount) else "partial"
        await db.flush()
        await AccountingService.post(
            db,
            expense.company_id,
            source_type="admin_expense_payment",
            source_id=None,
            entry_date=paid_on,
            description=f"Payment of administrative expense #{expense.id}",
            lines=[(acc.ACCOUNTS_PAYABLE, amount, ZERO), (acc.CASH, ZERO, amount)],
            created_by_id=user_id,
        )
        return expense
