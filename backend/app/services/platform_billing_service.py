from datetime import date, datetime, timedelta
from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.tenant import (
    BillingCycle,
    Company,
    CompanySubscription,
    SubscriptionPaymentStatus,
    SubscriptionPlan,
)
from app.schemas.billing import (
    CompanyBillingSummary,
    RecordSubscriptionPayment,
    SubscriptionBillingUpdate,
)


class PlatformBillingService:
    @staticmethod
    def _today() -> str:
        return date.today().isoformat()

    @staticmethod
    def _amount_for_plan(plan: SubscriptionPlan, billing_cycle: str) -> Decimal:
        if billing_cycle == BillingCycle.YEARLY.value:
            return Decimal(plan.price_yearly or 0)
        return Decimal(plan.price_monthly or 0)

    @staticmethod
    def _refresh_payment_status(sub: CompanySubscription) -> None:
        if sub.payment_status == SubscriptionPaymentStatus.TRIAL.value:
            return
        if not sub.next_billing_date:
            return
        due = date.fromisoformat(sub.next_billing_date)
        grace_end = due + timedelta(days=sub.payment_terms_days or 0)
        if date.today() > grace_end and sub.payment_status != SubscriptionPaymentStatus.PAID.value:
            sub.payment_status = SubscriptionPaymentStatus.OVERDUE.value
        elif sub.payment_status == SubscriptionPaymentStatus.OVERDUE.value and date.today() <= grace_end:
            sub.payment_status = SubscriptionPaymentStatus.PENDING.value

    @staticmethod
    def subscription_to_summary(sub: CompanySubscription | None) -> CompanyBillingSummary | None:
        if not sub:
            return None
        PlatformBillingService._refresh_payment_status(sub)
        plan = sub.plan
        amount = sub.amount_due
        if amount is None and plan:
            amount = PlatformBillingService._amount_for_plan(plan, sub.billing_cycle)
        return CompanyBillingSummary(
            plan_id=sub.plan_id,
            plan_name_ar=plan.name_ar if plan else None,
            plan_name_en=plan.name_en if plan else None,
            plan_code=plan.code if plan else None,
            billing_cycle=sub.billing_cycle,
            payment_terms_days=sub.payment_terms_days,
            next_billing_date=sub.next_billing_date,
            payment_status=sub.payment_status,
            amount_due=amount,
            last_payment_date=sub.last_payment_date,
            last_reminder_sent_at=sub.last_reminder_sent_at,
        )

    @staticmethod
    async def get_subscription(db: AsyncSession, company_id: int) -> CompanySubscription | None:
        result = await db.execute(
            select(CompanySubscription)
            .options(selectinload(CompanySubscription.plan))
            .where(CompanySubscription.company_id == company_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def ensure_subscription_defaults(
        db: AsyncSession,
        company: Company,
        plan: SubscriptionPlan | None = None,
        *,
        trial: bool = False,
    ) -> CompanySubscription:
        sub = await PlatformBillingService.get_subscription(db, company.id)
        if not sub:
            if not plan:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Plan required for new subscription")
            sub = CompanySubscription(company_id=company.id, plan_id=plan.id, is_active=True)
            db.add(sub)
            await db.flush()
            sub.plan = plan

        if plan and sub.plan_id != plan.id:
            sub.plan_id = plan.id
            sub.plan = plan

        if not sub.start_date:
            sub.start_date = PlatformBillingService._today()
        if not sub.next_billing_date:
            sub.next_billing_date = (date.today() + timedelta(days=30)).isoformat()
        if sub.amount_due is None and sub.plan:
            sub.amount_due = PlatformBillingService._amount_for_plan(sub.plan, sub.billing_cycle)
        if trial and sub.payment_status == SubscriptionPaymentStatus.PENDING.value:
            sub.payment_status = SubscriptionPaymentStatus.TRIAL.value
        PlatformBillingService._refresh_payment_status(sub)
        await db.flush()
        return sub

    @staticmethod
    async def update_billing(
        db: AsyncSession,
        company_id: int,
        data: SubscriptionBillingUpdate,
    ) -> CompanyBillingSummary:
        sub = await PlatformBillingService.get_subscription(db, company_id)
        if not sub:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subscription not found")

        payload = data.model_dump(exclude_unset=True)
        plan_id = payload.pop("plan_id", None)
        if plan_id:
            plan_result = await db.execute(select(SubscriptionPlan).where(SubscriptionPlan.id == plan_id))
            plan = plan_result.scalar_one_or_none()
            if not plan:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plan not found")
            sub.plan_id = plan.id
            sub.plan = plan
            sub.amount_due = PlatformBillingService._amount_for_plan(plan, sub.billing_cycle)

        for field, value in payload.items():
            setattr(sub, field, value)

        if data.billing_cycle and sub.plan:
            sub.amount_due = PlatformBillingService._amount_for_plan(sub.plan, sub.billing_cycle)

        PlatformBillingService._refresh_payment_status(sub)
        await db.flush()
        return PlatformBillingService.subscription_to_summary(sub)  # type: ignore[return-value]

    @staticmethod
    async def record_payment(
        db: AsyncSession,
        company_id: int,
        data: RecordSubscriptionPayment,
    ) -> CompanyBillingSummary:
        sub = await PlatformBillingService.get_subscription(db, company_id)
        if not sub:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subscription not found")

        paid_on = data.payment_date or PlatformBillingService._today()
        sub.last_payment_date = paid_on
        sub.payment_status = SubscriptionPaymentStatus.PAID.value

        cycle_days = 365 if sub.billing_cycle == BillingCycle.YEARLY.value else 30
        sub.next_billing_date = (date.fromisoformat(paid_on) + timedelta(days=cycle_days)).isoformat()
        if sub.plan:
            sub.amount_due = PlatformBillingService._amount_for_plan(sub.plan, sub.billing_cycle)

        await db.flush()
        return PlatformBillingService.subscription_to_summary(sub)  # type: ignore[return-value]

    @staticmethod
    async def send_payment_reminder(db: AsyncSession, company_id: int) -> dict:
        company_result = await db.execute(select(Company).where(Company.id == company_id))
        company = company_result.scalar_one_or_none()
        if not company:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found")

        sub = await PlatformBillingService.get_subscription(db, company_id)
        if not sub:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subscription not found")

        PlatformBillingService._refresh_payment_status(sub)
        now = datetime.utcnow().isoformat(timespec="seconds")
        sub.last_reminder_sent_at = now
        await db.flush()

        summary = PlatformBillingService.subscription_to_summary(sub)
        recipient = company.email or "billing contact"
        status_label = sub.payment_status
        return {
            "success": True,
            "message": f"Payment reminder queued for {recipient}",
            "company": company.name_en,
            "payment_status": status_label,
            "next_billing_date": sub.next_billing_date,
            "amount_due": float(summary.amount_due or 0) if summary else 0,
            "sent_at": now,
        }
