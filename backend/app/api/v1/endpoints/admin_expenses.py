"""Administrative (company) expenses (module ``admin_expenses``)."""

from collections import defaultdict
from datetime import date
from decimal import Decimal
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import company_id_of, get_company_user, log_audit
from app.core.database import get_db
from app.core.tenant import get_owned
from app.models.rentals import AdminExpense
from app.models.users import User
from app.services.expense_service import ExpenseService

router = APIRouter()

CATEGORIES = ["rent", "utilities", "salaries_other", "marketing", "office_supplies", "transport", "government_fees",
              "professional_fees", "software", "other"]


class AdminExpenseIn(BaseModel):
    category: str = Field(max_length=50)
    expense_date: date
    amount: Decimal = Field(gt=0)
    description: Optional[str] = None
    vendor: Optional[str] = None
    document_url: Optional[str] = None


class PaymentIn(BaseModel):
    amount: Decimal = Field(gt=0)
    paid_on: date


def _dict(a: AdminExpense) -> dict:
    return {
        "id": a.id, "category": a.category, "expense_date": a.expense_date.isoformat(), "amount": float(a.amount),
        "amount_paid": float(a.amount_paid), "remaining": float(Decimal(str(a.amount)) - Decimal(str(a.amount_paid))),
        "payment_status": a.payment_status, "description": a.description, "vendor": a.vendor, "document_url": a.document_url,
    }


@router.get("/categories")
async def categories():
    return CATEGORIES


@router.get("")
async def list_admin_expenses(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_company_user)],
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    category: Optional[str] = None,
):
    cid = company_id_of(current_user)
    query = select(AdminExpense).where(AdminExpense.company_id == cid, AdminExpense.is_deleted == False).order_by(AdminExpense.expense_date.desc())  # noqa: E712
    if date_from:
        query = query.where(AdminExpense.expense_date >= date_from)
    if date_to:
        query = query.where(AdminExpense.expense_date <= date_to)
    if category:
        query = query.where(AdminExpense.category == category)
    return [_dict(a) for a in (await db.execute(query)).scalars().all()]


@router.get("/summary")
async def admin_expense_summary(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_company_user)],
):
    cid = company_id_of(current_user)
    items = (await db.execute(select(AdminExpense).where(AdminExpense.company_id == cid, AdminExpense.is_deleted == False))).scalars().all()  # noqa: E712
    by_month: dict[str, Decimal] = defaultdict(lambda: Decimal("0"))
    by_category: dict[str, Decimal] = defaultdict(lambda: Decimal("0"))
    unpaid = Decimal("0")
    for a in items:
        by_month[a.expense_date.strftime("%Y-%m")] += Decimal(str(a.amount))
        by_category[a.category] += Decimal(str(a.amount))
        unpaid += Decimal(str(a.amount)) - Decimal(str(a.amount_paid))
    return {
        "by_month": [{"month": k, "total": float(v)} for k, v in sorted(by_month.items())],
        "by_category": [{"category": k, "total": float(v)} for k, v in sorted(by_category.items())],
        "unpaid": float(unpaid),
    }


@router.post("")
async def create_admin_expense(
    data: AdminExpenseIn, request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_company_user)],
):
    cid = company_id_of(current_user)
    if data.document_url and not data.document_url.startswith(f"/uploads/tenants/{cid}/"):
        raise HTTPException(status_code=400, detail="Document must be uploaded via /api/v1/files")
    expense = await ExpenseService.create_admin_expense(db, cid, data.model_dump(), current_user.id)
    await log_audit(db, request, current_user, "admin_expense_created", "admin_expenses", "admin_expense", expense.id,
                    after={"amount": expense.amount, "category": expense.category})
    return _dict(expense)


@router.post("/{expense_id}/payments")
async def pay_admin_expense(
    expense_id: int, data: PaymentIn, request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_company_user)],
):
    expense = await get_owned(db, AdminExpense, expense_id, company_id_of(current_user), entity_name="Expense")
    await ExpenseService.pay_admin_expense(db, expense, data.amount, data.paid_on, current_user.id)
    await log_audit(db, request, current_user, "admin_expense_paid", "admin_expenses", "admin_expense", expense.id,
                    after={"amount": data.amount, "status": expense.payment_status})
    return _dict(expense)


@router.put("/{expense_id}")
async def update_admin_expense(
    expense_id: int, data: AdminExpenseIn, request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_company_user)],
):
    expense = await get_owned(db, AdminExpense, expense_id, company_id_of(current_user), entity_name="Expense")
    if expense.amount != data.amount:
        raise HTTPException(status_code=400, detail="Posted amounts cannot be changed — delete and re-enter instead")
    before = {"category": expense.category, "description": expense.description}
    for k in ("category", "expense_date", "description", "vendor", "document_url"):
        setattr(expense, k, getattr(data, k))
    await db.flush()
    await log_audit(db, request, current_user, "admin_expense_updated", "admin_expenses", "admin_expense", expense.id,
                    before=before, after={"category": expense.category, "description": expense.description})
    return _dict(expense)


@router.delete("/{expense_id}")
async def delete_admin_expense(
    expense_id: int, request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_company_user)],
):
    expense = await get_owned(db, AdminExpense, expense_id, company_id_of(current_user), entity_name="Expense")
    if Decimal(str(expense.amount_paid)) > 0:
        raise HTTPException(status_code=400, detail="Paid expenses cannot be deleted")
    expense.soft_delete()
    await db.flush()
    # Reverse the accrual posted on creation (kept in the ledger for audit, never deleted)
    from app.services import accounting_service as acc
    from app.services.accounting_service import AccountingService

    amount = Decimal(str(expense.amount))
    await AccountingService.post(
        db, expense.company_id, source_type="admin_expense_reversal", source_id=expense.id, entry_date=expense.expense_date,
        description=f"Reversal of administrative expense #{expense.id}",
        lines=[(acc.ACCOUNTS_PAYABLE, amount, Decimal("0")), (acc.ADMIN_EXPENSE, Decimal("0"), amount)],
        created_by_id=current_user.id,
    )
    await log_audit(db, request, current_user, "admin_expense_deleted", "admin_expenses", "admin_expense", expense.id)
    return {"success": True}
