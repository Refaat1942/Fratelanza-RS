"""Daily tenant jobs: receivable generation, contract expiry, reminders.

Every job runs with an explicit ``company_id`` and the tenant's own timezone. All writes are
idempotent (unique receivable periods, unique notification dedupe keys), so a retried or
concurrently-started run never duplicates anything. Only one worker runs the loop at a time
(``pg_try_advisory_lock``).
"""

import asyncio
import logging
from datetime import date
from typing import Optional

from sqlalchemy import select, text
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import AsyncSessionLocal, engine
from app.models.real_estate import Unit
from app.models.rentals import PropertyOwner, RentalContract, RentReceivable
from app.models.system import Notification
from app.models.tenant import Company, CompanyStatus
from app.models.users import User, UserStatus
from app.services.access_service import AccessService
from app.services.outbound_service import OutboundService
from app.services.rental_service import RentalService, company_today, outstanding
from app.services.settlement_service import next_settlement

logger = logging.getLogger(__name__)
SCHEDULER_LOCK_ID = 814203

RENT_REMINDER_DAYS = 3
SETTLEMENT_REMINDER_DAYS = 7
CONTRACT_EXPIRY_REMINDER_DAYS = 30
OVERDUE_BUCKETS = (1, 7, 30)


async def _recipients(db: AsyncSession, company: Company, module: str, action: str = "view") -> list[User]:
    users = (
        await db.execute(
            select(User).where(
                User.company_id == company.id, User.is_deleted == False, User.status == UserStatus.ACTIVE  # noqa: E712
            )
        )
    ).scalars().all()
    result = []
    for u in users:
        ctx = await AccessService.build(db, u, company)
        if ctx.can(module, action):
            result.append(u)
    return result


async def _notify(
    db: AsyncSession, company: Company, users: list[User], *, key: str, title_ar: str, title_en: str,
    message_ar: str, message_en: str, ref_type: str, ref_id: int,
) -> int:
    created = 0
    for u in users:
        stmt = (
            pg_insert(Notification)
            .values(
                company_id=company.id, user_id=u.id, title_ar=title_ar, title_en=title_en, message_ar=message_ar,
                message_en=message_en, notification_type="reminder", channel="in_app", is_read=False,
                reference_type=ref_type, reference_id=ref_id, dedupe_key=key,
            )
            .on_conflict_do_nothing(constraint="uq_notification_user_dedupe")
        )
        result = await db.execute(stmt)
        created += result.rowcount or 0
    return created


async def run_company_jobs(db: AsyncSession, company_id: int, today: Optional[date] = None) -> dict:
    company = await AccessService.load_company(db, company_id)
    if company is None:
        return {}
    if company.is_demo and AccessService.demo_state(await AccessService.load_demo(db, company.id)):
        return {"skipped": "demo_inactive"}
    today = today or company_today(company)
    stats = {"receivables_created": 0, "contracts_expired": 0, "notifications": 0, "outbound": 0}

    contracts = (
        await db.execute(
            select(RentalContract).where(
                RentalContract.company_id == company.id,
                RentalContract.status == "active",
                RentalContract.is_deleted == False,  # noqa: E712
            )
        )
    ).scalars().all()
    for c in contracts:
        stats["receivables_created"] += await RentalService.generate_receivables(db, c)
        if c.end_date < today:
            c.status = "expired"
            unit = (await db.execute(select(Unit).where(Unit.id == c.unit_id, Unit.company_id == company.id))).scalar_one()
            unit.occupancy_status = "vacant"
            stats["contracts_expired"] += 1
    await db.flush()

    collectors = await _recipients(db, company, "rentals", "view")
    rows = (
        await db.execute(
            select(RentReceivable, RentalContract)
            .join(RentalContract, RentReceivable.rental_contract_id == RentalContract.id)
            .where(RentReceivable.company_id == company.id, RentReceivable.status.in_(["pending", "partial"]))
        )
    ).all()
    for r, c in rows:
        remaining = outstanding(r)
        if remaining <= 0:
            continue
        days_to_due = (r.due_date - today).days
        if days_to_due == RENT_REMINDER_DAYS:
            key = f"rent_due:{r.id}"
            stats["notifications"] += await _notify(
                db, company, collectors, key=key,
                title_ar="إيجار مستحق خلال 3 أيام", title_en="Rent due in 3 days",
                message_ar=f"{c.tenant_name} — عقد {c.contract_number}: {remaining} مستحق في {r.due_date}",
                message_en=f"{c.tenant_name} — contract {c.contract_number}: {remaining} due on {r.due_date}",
                ref_type="rent_receivable", ref_id=r.id,
            )
            if c.tenant_mobile:
                await OutboundService.send(
                    db, company, channel="whatsapp", recipient=c.tenant_mobile, dedupe_key=key,
                    body=f"تذكير: قيمة الإيجار {remaining} مستحقة بتاريخ {r.due_date} — عقد {c.contract_number}",
                )
                stats["outbound"] += 1
        overdue_days = (today - r.due_date).days
        if overdue_days in OVERDUE_BUCKETS:
            stats["notifications"] += await _notify(
                db, company, collectors, key=f"rent_overdue:{r.id}:{overdue_days}",
                title_ar=f"إيجار متأخر {overdue_days} يوم", title_en=f"Rent overdue {overdue_days} day(s)",
                message_ar=f"{c.tenant_name} — عقد {c.contract_number}: متبقي {remaining}",
                message_en=f"{c.tenant_name} — contract {c.contract_number}: {remaining} outstanding",
                ref_type="rent_receivable", ref_id=r.id,
            )

    property_managers = await _recipients(db, company, "rentals", "edit")
    for c in contracts:
        if c.status == "active" and (c.end_date - today).days == CONTRACT_EXPIRY_REMINDER_DAYS:
            stats["notifications"] += await _notify(
                db, company, property_managers, key=f"contract_expiring:{c.id}",
                title_ar="عقد إيجار ينتهي خلال 30 يوماً", title_en="Lease expires in 30 days",
                message_ar=f"عقد {c.contract_number} — {c.tenant_name} ينتهي في {c.end_date}",
                message_en=f"Contract {c.contract_number} — {c.tenant_name} ends on {c.end_date}",
                ref_type="rental_contract", ref_id=c.id,
            )

    settlement_users = await _recipients(db, company, "owners", "view")
    owners = (
        await db.execute(select(PropertyOwner).where(PropertyOwner.company_id == company.id, PropertyOwner.is_deleted == False))  # noqa: E712
    ).scalars().all()
    for o in owners:
        _, end, due = next_settlement(o, today)
        if (due - today).days == SETTLEMENT_REMINDER_DAYS:
            stats["notifications"] += await _notify(
                db, company, settlement_users, key=f"settlement_due:{o.id}:{end.isoformat()}",
                title_ar="تسوية مالك مستحقة خلال أسبوع", title_en="Owner settlement due in one week",
                message_ar=f"تسوية المالك {o.full_name} عن الفترة المنتهية {end} مستحقة في {due}",
                message_en=f"Settlement for {o.full_name} (period ending {end}) is due on {due}",
                ref_type="property_owner", ref_id=o.id,
            )
    await db.flush()
    return stats


async def run_all_tenants() -> dict:
    results = {}
    async with AsyncSessionLocal() as db:
        company_ids = (
            await db.execute(
                select(Company.id).where(
                    Company.is_deleted == False,  # noqa: E712
                    Company.status.in_([CompanyStatus.ACTIVE, CompanyStatus.TRIAL]),
                )
            )
        ).scalars().all()
    for cid in company_ids:
        async with AsyncSessionLocal() as db:
            try:
                results[cid] = await run_company_jobs(db, cid)
                await db.commit()
            except Exception:  # one tenant's failure must not stop the others
                await db.rollback()
                logger.exception("Scheduled jobs failed for company %s", cid)
    return results


async def scheduler_loop() -> None:
    await asyncio.sleep(5)
    while True:
        try:
            async with engine.connect() as conn:
                locked = (await conn.execute(text("SELECT pg_try_advisory_lock(:id)"), {"id": SCHEDULER_LOCK_ID})).scalar()
                if locked:
                    try:
                        await run_all_tenants()
                    finally:
                        await conn.execute(text("SELECT pg_advisory_unlock(:id)"), {"id": SCHEDULER_LOCK_ID})
                        await conn.commit()
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception("Scheduler iteration failed")
        await asyncio.sleep(max(settings.SCHEDULER_INTERVAL_SECONDS, 60))
