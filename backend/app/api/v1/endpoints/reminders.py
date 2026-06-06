from datetime import date, timedelta
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
from app.services.follow_up_service import FollowUpService

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


class CompleteCallRequest(BaseModel):
    outcome: str
    outcome_notes: Optional[str] = None
    next_call_date: Optional[str] = None
    next_call_time: Optional[str] = "10:00"
    new_lead_stage: Optional[str] = None


class RescheduleRequest(BaseModel):
    due_date: str
    due_time: Optional[str] = "10:00"


async def _list_enriched(db: AsyncSession, reminders: list[CustomerReminder]) -> list[dict]:
    rows = []
    for r in reminders:
        rows.append(await FollowUpService.enrich_reminder(db, r))
    return rows


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


@router.get("/queue")
async def call_queue(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_company_user)],
):
    """Actionable calls: overdue first, then today, sorted by time."""
    if not current_user.company_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Company required")
    today = date.today().isoformat()
    week_end = (date.today() + timedelta(days=7)).isoformat()
    result = await db.execute(
        select(CustomerReminder).where(
            CustomerReminder.company_id == current_user.company_id,
            CustomerReminder.status == ReminderStatus.PENDING,
        )
    )
    pending = list(result.scalars().all())
    due_now = [r for r in pending if r.due_date <= today]
    due_now.sort(key=lambda r: (r.due_date, r.due_time or "99:99"))
    upcoming = [r for r in pending if today < r.due_date <= week_end]
    upcoming.sort(key=lambda r: (r.due_date, r.due_time or "99:99"))
    due_items = await _list_enriched(db, due_now[:50])
    upcoming_items = await _list_enriched(db, upcoming[:20])
    return {
        "today_and_overdue": due_items,
        "upcoming_week": upcoming_items,
        "counts": {
            "overdue": sum(1 for i in due_items if i.get("status") == "overdue"),
            "due_today": sum(1 for i in due_items if i.get("status") == "pending"),
            "upcoming": len(upcoming_items),
        },
    }


@router.get("/history")
async def call_history(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_company_user)],
    limit: int = Query(50, ge=1, le=200),
):
    if not current_user.company_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Company required")
    result = await db.execute(
        select(CustomerReminder)
        .where(
            CustomerReminder.company_id == current_user.company_id,
            CustomerReminder.status == ReminderStatus.COMPLETED,
        )
        .order_by(CustomerReminder.id.desc())
        .limit(limit)
    )
    return await _list_enriched(db, list(result.scalars().all()))


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
    return await _list_enriched(db, list(result.scalars().all()))


@router.get("/{reminder_id}")
async def get_reminder(
    reminder_id: int,
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
    data = await FollowUpService.enrich_reminder(db, reminder)
    # Customer timeline
    if reminder.customer_id:
        from app.models.customers import CustomerActivity
        acts = (
            await db.execute(
                select(CustomerActivity)
                .where(CustomerActivity.customer_id == reminder.customer_id)
                .order_by(CustomerActivity.id.desc())
                .limit(10)
            )
        ).scalars().all()
        data["activity_timeline"] = [
            {"title": a.title, "description": a.description, "type": a.activity_type.value, "date": str(a.created_at)}
            for a in acts
        ]
    return data


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
    if data.lead_id:
        lead = (await db.execute(select(Lead).where(Lead.id == data.lead_id))).scalar_one_or_none()
        if lead:
            lead.next_follow_up = data.due_date
    return {"id": reminder.id, "status": reminder.status.value}


@router.post("/{reminder_id}/complete")
async def complete_call(
    reminder_id: int,
    data: CompleteCallRequest,
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
    return await FollowUpService.complete_call(
        db,
        reminder,
        current_user,
        data.outcome,
        data.outcome_notes,
        data.next_call_date,
        data.next_call_time,
        data.new_lead_stage,
    )


@router.post("/{reminder_id}/reschedule")
async def reschedule_call(
    reminder_id: int,
    data: RescheduleRequest,
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
    reminder.due_date = data.due_date
    reminder.due_time = data.due_time
    reminder.status = ReminderStatus.PENDING
    if reminder.lead_id:
        lead = (await db.execute(select(Lead).where(Lead.id == reminder.lead_id))).scalar_one_or_none()
        if lead:
            lead.next_follow_up = data.due_date
    await db.flush()
    return {"id": reminder.id, "due_date": data.due_date, "due_time": data.due_time}


@router.delete("/{reminder_id}")
async def delete_reminder(
    reminder_id: int,
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
    await db.delete(reminder)
    await db.flush()
    return {"message": "Reminder deleted", "success": True}


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
