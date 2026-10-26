"""Property-level expenses (module ``property_expenses``)."""

from collections import defaultdict
from datetime import date
from decimal import Decimal
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import company_id_of, get_company_user, log_audit
from app.core.database import get_db
from app.core.tenant import get_owned
from app.models.property import MaintenanceRequest
from app.models.real_estate import Unit
from app.models.rentals import PropertyExpense, PropertyOwner
from app.models.users import User
from app.services.expense_service import ExpenseService

router = APIRouter()

CATEGORIES = ["maintenance", "plumbing", "electrical", "painting", "cleaning", "security", "utilities", "taxes", "insurance", "other"]


class ExpenseIn(BaseModel):
    unit_id: int
    owner_id: Optional[int] = None
    expense_date: date
    category: str = Field(max_length=50)
    description: Optional[str] = None
    amount: Decimal = Field(gt=0)
    vendor: Optional[str] = None
    attachment_url: Optional[str] = None
    charged_to: str = Field(default="owner", pattern="^(owner|company)$")


class ExpenseUpdate(BaseModel):
    expense_date: Optional[date] = None
    category: Optional[str] = None
    description: Optional[str] = None
    amount: Optional[Decimal] = Field(default=None, gt=0)
    vendor: Optional[str] = None
    attachment_url: Optional[str] = None
    charged_to: Optional[str] = Field(default=None, pattern="^(owner|company)$")


class FromMaintenanceIn(BaseModel):
    amount: Decimal = Field(gt=0)
    expense_date: date
    vendor: Optional[str] = None
    charged_to: str = Field(default="owner", pattern="^(owner|company)$")
    attachment_url: Optional[str] = None


class PaidIn(BaseModel):
    paid_on: date


def _attachment_ok(url: Optional[str], company_id: int) -> None:
    # Only files uploaded to this tenant's own storage may be attached
    if url and not url.startswith(f"/uploads/tenants/{company_id}/"):
        raise HTTPException(status_code=400, detail="Attachment must be uploaded via /api/v1/files")


def _dict(e: PropertyExpense, unit: Optional[Unit], owner: Optional[PropertyOwner]) -> dict:
    return {
        "id": e.id, "unit_id": e.unit_id, "unit_code": unit.unit_code if unit else None, "owner_id": e.owner_id,
        "owner_name": owner.full_name if owner else None, "maintenance_request_id": e.maintenance_request_id,
        "expense_date": e.expense_date.isoformat(), "category": e.category, "description": e.description,
        "amount": float(e.amount), "vendor": e.vendor, "attachment_url": e.attachment_url, "charged_to": e.charged_to,
        "payment_status": e.payment_status, "approval_status": e.approval_status, "settlement_id": e.settlement_id,
    }


@router.get("/categories")
async def categories():
    return CATEGORIES


@router.get("")
async def list_expenses(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_company_user)],
    unit_id: Optional[int] = None,
    owner_id: Optional[int] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    approval_status: Optional[str] = None,
):
    cid = company_id_of(current_user)
    query = (
        select(PropertyExpense, Unit, PropertyOwner)
        .join(Unit, PropertyExpense.unit_id == Unit.id)
        .outerjoin(PropertyOwner, PropertyExpense.owner_id == PropertyOwner.id)
        .where(PropertyExpense.company_id == cid, PropertyExpense.is_deleted == False)  # noqa: E712
        .order_by(PropertyExpense.expense_date.desc())
    )
    if unit_id:
        query = query.where(PropertyExpense.unit_id == unit_id)
    if owner_id:
        query = query.where(PropertyExpense.owner_id == owner_id)
    if date_from:
        query = query.where(PropertyExpense.expense_date >= date_from)
    if date_to:
        query = query.where(PropertyExpense.expense_date <= date_to)
    if approval_status:
        query = query.where(PropertyExpense.approval_status == approval_status)
    return [_dict(e, u, o) for e, u, o in (await db.execute(query)).all()]


@router.get("/summary")
async def expense_summary(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_company_user)],
    group_by: str = Query("unit", pattern="^(unit|owner|month|category)$"),
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
):
    cid = company_id_of(current_user)
    rows = (
        await db.execute(
            select(PropertyExpense, Unit, PropertyOwner)
            .join(Unit, PropertyExpense.unit_id == Unit.id)
            .outerjoin(PropertyOwner, PropertyExpense.owner_id == PropertyOwner.id)
            .where(PropertyExpense.company_id == cid, PropertyExpense.is_deleted == False, PropertyExpense.approval_status != "rejected")  # noqa: E712
        )
    ).all()
    totals: dict[str, Decimal] = defaultdict(lambda: Decimal("0"))
    counts: dict[str, int] = defaultdict(int)
    for e, u, o in rows:
        if (date_from and e.expense_date < date_from) or (date_to and e.expense_date > date_to):
            continue
        key = {"unit": u.unit_code, "owner": o.full_name if o else "—", "month": e.expense_date.strftime("%Y-%m"),
               "category": e.category}[group_by]
        totals[key] += Decimal(str(e.amount))
        counts[key] += 1
    return [{"group": k, "count": counts[k], "total": float(v)} for k, v in sorted(totals.items())]


@router.post("")
async def create_expense(
    data: ExpenseIn,
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_company_user)],
):
    cid = company_id_of(current_user)
    _attachment_ok(data.attachment_url, cid)
    expense = await ExpenseService.create_property_expense(db, cid, data.model_dump(), current_user.id)
    await log_audit(db, request, current_user, "property_expense_created", "property_expenses", "property_expense", expense.id,
                    after={"amount": expense.amount, "unit_id": expense.unit_id, "charged_to": expense.charged_to})
    return {"id": expense.id}


@router.post("/from-maintenance/{request_id}")
async def expense_from_maintenance(
    request_id: int,
    data: FromMaintenanceIn,
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_company_user)],
):
    """Link an approved maintenance cost to exactly one expense (no duplicate accounting)."""
    cid = company_id_of(current_user)
    _attachment_ok(data.attachment_url, cid)
    mr = await get_owned(db, MaintenanceRequest, request_id, cid, entity_name="Maintenance request")
    expense = await ExpenseService.create_property_expense(
        db, cid,
        {"unit_id": mr.unit_id, "maintenance_request_id": mr.id, "expense_date": data.expense_date, "category": "maintenance",
         "description": mr.title, "amount": data.amount, "vendor": data.vendor, "charged_to": data.charged_to,
         "attachment_url": data.attachment_url},
        current_user.id,
    )
    await log_audit(db, request, current_user, "property_expense_from_maintenance", "property_expenses", "property_expense",
                    expense.id, after={"maintenance_request_id": mr.id, "amount": expense.amount})
    return {"id": expense.id}


async def _expense(db: AsyncSession, expense_id: int, user: User) -> PropertyExpense:
    return await get_owned(db, PropertyExpense, expense_id, company_id_of(user), entity_name="Expense")


@router.put("/{expense_id}")
async def update_expense(
    expense_id: int,
    data: ExpenseUpdate,
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_company_user)],
):
    expense = await _expense(db, expense_id, current_user)
    if expense.approval_status != "pending":
        raise HTTPException(status_code=400, detail="Approved/rejected expenses cannot be edited")
    changes = data.model_dump(exclude_unset=True)
    _attachment_ok(changes.get("attachment_url"), expense.company_id)
    before = {k: getattr(expense, k) for k in changes}
    for k, v in changes.items():
        setattr(expense, k, v)
    await db.flush()
    await log_audit(db, request, current_user, "property_expense_updated", "property_expenses", "property_expense", expense.id,
                    before=before, after=changes)
    return {"id": expense.id, "success": True}


@router.post("/{expense_id}/approve")
async def approve_expense(
    expense_id: int, request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_company_user)],
):
    expense = await _expense(db, expense_id, current_user)
    await ExpenseService.approve(db, expense, current_user.id)
    await log_audit(db, request, current_user, "property_expense_approved", "property_expenses", "property_expense", expense.id)
    return {"id": expense.id, "approval_status": expense.approval_status}


@router.post("/{expense_id}/reject")
async def reject_expense(
    expense_id: int, request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_company_user)],
):
    expense = await _expense(db, expense_id, current_user)
    if expense.approval_status != "pending":
        raise HTTPException(status_code=400, detail="Expense already decided")
    expense.approval_status = "rejected"
    expense.approved_by_id = current_user.id
    await db.flush()
    await log_audit(db, request, current_user, "property_expense_rejected", "property_expenses", "property_expense", expense.id)
    return {"id": expense.id, "approval_status": expense.approval_status}


@router.post("/{expense_id}/mark-paid")
async def mark_expense_paid(
    expense_id: int, data: PaidIn, request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_company_user)],
):
    expense = await _expense(db, expense_id, current_user)
    await ExpenseService.mark_paid(db, expense, data.paid_on, current_user.id)
    await log_audit(db, request, current_user, "property_expense_paid", "property_expenses", "property_expense", expense.id)
    return {"id": expense.id, "payment_status": expense.payment_status}


@router.delete("/{expense_id}")
async def delete_expense(
    expense_id: int, request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_company_user)],
):
    expense = await _expense(db, expense_id, current_user)
    if expense.approval_status == "approved":
        raise HTTPException(status_code=400, detail="Approved expenses are posted to accounting and cannot be deleted")
    expense.soft_delete()
    await db.flush()
    await log_audit(db, request, current_user, "property_expense_deleted", "property_expenses", "property_expense", expense.id)
    return {"success": True}
