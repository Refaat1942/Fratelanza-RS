from datetime import date
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_company_user
from app.core.database import get_db
from app.models.crm import CustomerReminder, Lead, ReminderStatus, ReminderType
from app.models.customers import Customer
from app.models.users import User

router = APIRouter()


class ReminderCreate(BaseModel):
    title: str
    reminder_type: ReminderType = ReminderType.CALL
    due_date: str
    due_time: Optional[str] = None
    customer_id: Optional[int] = None
    lead_id: Optional[int] = None
    notes: Optional[str] = None


class ReminderUpdate(BaseModel):
    status: Optional[ReminderStatus] = None
    notes: Optional[str] = None
    due_date: Optional[str] = None
    due_time: Optional[str] = None


@router.get("/summary")
async def reminders_summary(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_company_user)],
):
    if not current_user.company_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Company required")
    today = date.today().isoformat()
    result = await db.execute(
        select(CustomerReminder).where(CustomerReminder.company_id == current_user.company_id)
    )
    reminders = result.scalars().all()
    today_count = sum(1 for r in reminders if r.due_date == today and r.status == ReminderStatus.PENDING)
    overdue_count = sum(
        1 for r in reminders
        if r.status == ReminderStatus.PENDING and r.due_date < today
    )
    pending_count = sum(1 for r in reminders if r.status == ReminderStatus.PENDING)
    return {
        "today": today_count,
        "overdue": overdue_count,
        "pending": pending_count,
        "total": len(reminders),
    }


@router.get("")
async def list_reminders(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_company_user)],
    status_filter: Optional[str] = Query(None, alias="status"),
    due_today: bool = False,
):
    if not current_user.company_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Company required")
    query = select(CustomerReminder).where(CustomerReminder.company_id == current_user.company_id)
    if status_filter:
        query = query.where(CustomerReminder.status == status_filter)
    if due_today:
        query = query.where(CustomerReminder.due_date == date.today().isoformat())
    result = await db.execute(query.order_by(CustomerReminder.due_date))
    reminders = result.scalars().all()
    today = date.today().isoformat()
    rows = []
    customer_ids = {r.customer_id for r in reminders if r.customer_id}
    lead_ids = {r.lead_id for r in reminders if r.lead_id}
    customers_map: dict[int, str] = {}
    leads_map: dict[int, str] = {}
    if customer_ids:
        cr = await db.execute(select(Customer).where(Customer.id.in_(customer_ids)))
        customers_map = {c.id: c.full_name_en for c in cr.scalars().all()}
    if lead_ids:
        lr = await db.execute(select(Lead).where(Lead.id.in_(lead_ids)))
        leads_map = {l.id: l.full_name for l in lr.scalars().all()}

    for r in reminders:
        st = r.status.value
        if st == "pending" and r.due_date < today:
            st = "overdue"
        linked = customers_map.get(r.customer_id) or leads_map.get(r.lead_id) or ""
        rows.append({
            "id": r.id,
            "title": r.title,
            "linked_to": linked,
            "reminder_type": r.reminder_type.value,
            "due_date": r.due_date,
            "due_time": r.due_time or "",
            "status": st,
            "notes": r.notes or "",
            "customer_id": r.customer_id,
            "lead_id": r.lead_id,
            "assigned_to_id": r.assigned_to_id,
        })
    return rows


@router.post("")
async def create_reminder(
    data: ReminderCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_company_user)],
):
    if not current_user.company_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Company required")
    reminder = CustomerReminder(
        company_id=current_user.company_id,
        assigned_to_id=current_user.id,
        **data.model_dump(),
    )
    db.add(reminder)
    await db.flush()
    return {"id": reminder.id, "status": reminder.status.value}


@router.patch("/{reminder_id}")
async def update_reminder(
    reminder_id: int,
    data: ReminderUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_company_user)],
):
    result = await db.execute(
        select(CustomerReminder).where(
            CustomerReminder.id == reminder_id,
            CustomerReminder.company_id == current_user.company_id,
        )
    )
    reminder = result.scalar_one_or_none()
    if not reminder:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Reminder not found")
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(reminder, field, value)
    await db.flush()
    return {"id": reminder.id, "status": reminder.status.value}
