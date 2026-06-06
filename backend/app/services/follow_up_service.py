from datetime import date, datetime, timedelta, timezone
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.crm import CustomerReminder, Lead, LeadActivity, LeadStage, ReminderStatus, ReminderType
from app.models.customers import ActivityType, Customer, CustomerActivity
from app.models.users import User


class FollowUpService:
    @staticmethod
    async def enrich_reminder(db: AsyncSession, reminder: CustomerReminder) -> dict:
        mobile = ""
        whatsapp = ""
        linked_name = ""
        lead_stage = ""
        customer_id = reminder.customer_id
        lead_id = reminder.lead_id

        if reminder.customer_id:
            c = (await db.execute(select(Customer).where(Customer.id == reminder.customer_id))).scalar_one_or_none()
            if c:
                mobile = c.mobile
                whatsapp = c.whatsapp or c.mobile
                linked_name = c.full_name_en
        if reminder.lead_id:
            l = (await db.execute(select(Lead).where(Lead.id == reminder.lead_id))).scalar_one_or_none()
            if l:
                mobile = mobile or l.mobile
                linked_name = linked_name or l.full_name
                lead_stage = l.stage.value
                if not customer_id:
                    customer_id = l.customer_id
                lead_id = l.id

        today = date.today().isoformat()
        st = reminder.status.value
        if st == "pending" and reminder.due_date < today:
            st = "overdue"

        return {
            "id": reminder.id,
            "title": reminder.title,
            "linked_to": linked_name,
            "mobile": mobile,
            "whatsapp": whatsapp,
            "reminder_type": reminder.reminder_type.value,
            "due_date": reminder.due_date,
            "due_time": reminder.due_time or "",
            "status": st,
            "notes": reminder.notes or "",
            "customer_id": customer_id,
            "lead_id": lead_id,
            "lead_stage": lead_stage,
            "call_outcome": reminder.call_outcome or "",
            "outcome_notes": reminder.outcome_notes or "",
            "completed_at": str(reminder.completed_at) if reminder.completed_at else "",
        }

    @staticmethod
    async def complete_call(
        db: AsyncSession,
        reminder: CustomerReminder,
        current_user: User,
        outcome: str,
        outcome_notes: Optional[str] = None,
        next_call_date: Optional[str] = None,
        next_call_time: Optional[str] = None,
        new_lead_stage: Optional[str] = None,
    ) -> dict:
        reminder.status = ReminderStatus.COMPLETED
        reminder.call_outcome = outcome
        reminder.outcome_notes = outcome_notes
        reminder.completed_at = datetime.now(timezone.utc)

        title = f"Call completed — {outcome.replace('_', ' ')}"
        description = outcome_notes or reminder.notes or ""

        if reminder.customer_id:
            db.add(
                CustomerActivity(
                    customer_id=reminder.customer_id,
                    activity_type=ActivityType.CALL,
                    title=title,
                    description=description,
                    created_by_id=current_user.id,
                    reference_type="reminder",
                    reference_id=reminder.id,
                )
            )

        lead_id = reminder.lead_id
        if not lead_id and reminder.customer_id:
            lr = await db.execute(
                select(Lead).where(Lead.customer_id == reminder.customer_id, Lead.is_deleted == False).limit(1)
            )
            lead = lr.scalar_one_or_none()
            if lead:
                lead_id = lead.id

        if lead_id:
            lead = (await db.execute(select(Lead).where(Lead.id == lead_id))).scalar_one_or_none()
            if lead:
                db.add(
                    LeadActivity(
                        lead_id=lead.id,
                        activity_type="call",
                        description=f"{outcome}: {description}",
                        created_by_id=current_user.id,
                    )
                )
                if new_lead_stage:
                    try:
                        lead.stage = LeadStage(new_lead_stage)
                    except ValueError:
                        pass
                elif outcome == "answered_interested" and lead.stage == LeadStage.NEW:
                    lead.stage = LeadStage.CONTACTED
                elif outcome == "answered_interested":
                    lead.stage = LeadStage.INTERESTED
                if next_call_date:
                    lead.next_follow_up = next_call_date

        next_reminder_id = None
        if next_call_date and outcome in ("no_answer", "answered_callback", "answered_interested"):
            linked_name = ""
            if reminder.customer_id:
                c = (await db.execute(select(Customer).where(Customer.id == reminder.customer_id))).scalar_one_or_none()
                linked_name = c.full_name_en if c else ""
            elif lead_id:
                l = (await db.execute(select(Lead).where(Lead.id == lead_id))).scalar_one_or_none()
                linked_name = l.full_name if l else ""

            nxt = CustomerReminder(
                company_id=reminder.company_id,
                customer_id=reminder.customer_id,
                lead_id=lead_id or reminder.lead_id,
                title=f"Follow-up call — {linked_name or reminder.title}",
                reminder_type=ReminderType.CALL,
                due_date=next_call_date,
                due_time=next_call_time or "10:00",
                notes=f"Auto-scheduled after: {outcome}. {outcome_notes or ''}".strip(),
                assigned_to_id=current_user.id,
            )
            db.add(nxt)
            await db.flush()
            next_reminder_id = nxt.id

        await db.flush()
        return {"reminder_id": reminder.id, "next_reminder_id": next_reminder_id, "status": "completed"}

    @staticmethod
    async def auto_schedule_for_lead(
        db: AsyncSession,
        lead: Lead,
        user_id: int,
        days_ahead: int = 2,
    ) -> Optional[int]:
        due = (date.today() + timedelta(days=days_ahead)).isoformat()
        existing = await db.execute(
            select(CustomerReminder).where(
                CustomerReminder.lead_id == lead.id,
                CustomerReminder.status == ReminderStatus.PENDING,
            )
        )
        if existing.scalar_one_or_none():
            return None
        r = CustomerReminder(
            company_id=lead.company_id,
            lead_id=lead.id,
            customer_id=lead.customer_id,
            title=f"Follow up — {lead.full_name}",
            reminder_type=ReminderType.CALL,
            due_date=due,
            due_time="10:00",
            notes=f"Auto-scheduled when lead moved to {lead.stage.value}",
            assigned_to_id=user_id,
        )
        db.add(r)
        await db.flush()
        lead.next_follow_up = due
        return r.id
