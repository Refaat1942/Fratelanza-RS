from datetime import date, datetime, timedelta
from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.system import SystemSetting
from app.models.tenant import (
    BillingCycle,
    Company,
    CompanyStatus,
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
    async def get_trial_days(db: AsyncSession) -> int:
        result = await db.execute(select(SystemSetting).where(SystemSetting.key == "trial_days"))
        setting = result.scalar_one_or_none()
        if setting and str(setting.value).isdigit():
            return max(1, int(setting.value))
        return 14

    @staticmethod
    def _amount_for_plan(plan: SubscriptionPlan, billing_cycle: str) -> Decimal:
        billing_type = getattr(plan, "billing_type", "recurring") or "recurring"
        if billing_type == "one_time":
            if billing_cycle == BillingCycle.MONTHLY.value and Decimal(plan.hosting_fee_monthly or 0) > 0:
                return Decimal(plan.hosting_fee_monthly or 0)
            return Decimal(plan.price_one_time or 0)
        if billing_cycle == BillingCycle.YEARLY.value:
            return Decimal(plan.price_yearly or 0)
        return Decimal(plan.price_monthly or 0)

    @staticmethod
    def apply_trial(sub: CompanySubscription, company: Company, days: int) -> None:
        today = date.today()
        end = today + timedelta(days=days)
        sub.start_date = today.isoformat()
        sub.end_date = end.isoformat()
        sub.next_billing_date = end.isoformat()
        sub.payment_status = SubscriptionPaymentStatus.TRIAL.value
        sub.amount_due = Decimal(0)
        sub.is_active = True
        company.status = CompanyStatus.TRIAL

    @staticmethod
    def trial_days_remaining(sub: CompanySubscription) -> int | None:
        if sub.payment_status != SubscriptionPaymentStatus.TRIAL.value or not sub.end_date:
            return None
        remaining = (date.fromisoformat(sub.end_date) - date.today()).days
        return max(0, remaining)

    @staticmethod
    def sync_trial_expiry(sub: CompanySubscription, company: Company) -> bool:
        if sub.payment_status != SubscriptionPaymentStatus.TRIAL.value:
            return False
        if not sub.end_date:
            return False
        if date.today() > date.fromisoformat(sub.end_date):
            company.status = CompanyStatus.EXPIRED
            sub.is_active = False
            sub.payment_status = SubscriptionPaymentStatus.EXPIRED.value
            return True
        return False

    @staticmethod
    async def expire_all_due_trials(db: AsyncSession) -> int:
        """Close companies whose 14-day (or configured) trial has ended."""
        from sqlalchemy.orm import selectinload

        result = await db.execute(
            select(Company)
            .options(selectinload(Company.subscription))
            .where(Company.is_deleted == False, Company.status == CompanyStatus.TRIAL)
        )
        expired_count = 0
        for company in result.scalars().all():
            sub = company.subscription
            if sub and PlatformBillingService.sync_trial_expiry(sub, company):
                expired_count += 1
        if expired_count:
            await db.flush()
        return expired_count

    @staticmethod
    def _refresh_payment_status(sub: CompanySubscription, company: Company | None = None) -> None:
        if company:
            PlatformBillingService.sync_trial_expiry(sub, company)
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
    def subscription_to_summary(
        sub: CompanySubscription | None,
        company: Company | None = None,
    ) -> CompanyBillingSummary | None:
        if not sub:
            return None
        PlatformBillingService._refresh_payment_status(sub, company)
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
            start_date=sub.start_date,
            end_date=sub.end_date,
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
    async def ensure_company_accessible(db: AsyncSession, company: Company) -> None:
        sub = company.subscription
        if sub:
            PlatformBillingService.sync_trial_expiry(sub, company)
            await db.flush()
        if company.status == CompanyStatus.SUSPENDED:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Company suspended")
        if company.status == CompanyStatus.EXPIRED:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="trial_expired",
            )

    @staticmethod
    async def ensure_subscription_defaults(
        db: AsyncSession,
        company: Company,
        plan: SubscriptionPlan | None = None,
        *,
        trial: bool = False,
        trial_days: int | None = None,
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

        if trial:
            days = trial_days if trial_days is not None else await PlatformBillingService.get_trial_days(db)
            PlatformBillingService.apply_trial(sub, company, days)
        else:
            if not sub.start_date:
                sub.start_date = PlatformBillingService._today()
            if not sub.next_billing_date:
                sub.next_billing_date = (date.today() + timedelta(days=30)).isoformat()
            if sub.amount_due is None and sub.plan:
                sub.amount_due = PlatformBillingService._amount_for_plan(sub.plan, sub.billing_cycle)
            if sub.payment_status == SubscriptionPaymentStatus.PENDING.value:
                pass

        PlatformBillingService._refresh_payment_status(sub, company)
        await db.flush()
        return sub

    @staticmethod
    async def update_billing(
        db: AsyncSession,
        company_id: int,
        data: SubscriptionBillingUpdate,
    ) -> CompanyBillingSummary:
        company_result = await db.execute(
            select(Company).options(selectinload(Company.subscription)).where(Company.id == company_id)
        )
        company = company_result.scalar_one_or_none()
        if not company:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found")

        sub = company.subscription or await PlatformBillingService.get_subscription(db, company_id)
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

        if data.payment_status == SubscriptionPaymentStatus.PAID.value:
            company.status = CompanyStatus.ACTIVE
            sub.is_active = True

        PlatformBillingService._refresh_payment_status(sub, company)
        await db.flush()
        return PlatformBillingService.subscription_to_summary(sub, company)  # type: ignore[return-value]

    @staticmethod
    async def record_payment(
        db: AsyncSession,
        company_id: int,
        data: RecordSubscriptionPayment,
    ) -> CompanyBillingSummary:
        company_result = await db.execute(
            select(Company).options(selectinload(Company.subscription)).where(Company.id == company_id)
        )
        company = company_result.scalar_one_or_none()
        if not company:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found")

        sub = company.subscription or await PlatformBillingService.get_subscription(db, company_id)
        if not sub:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subscription not found")

        paid_on = data.payment_date or PlatformBillingService._today()
        sub.last_payment_date = paid_on
        sub.payment_status = SubscriptionPaymentStatus.PAID.value
        sub.end_date = None
        company.status = CompanyStatus.ACTIVE
        sub.is_active = True

        plan = sub.plan
        billing_type = getattr(plan, "billing_type", "recurring") if plan else "recurring"
        if plan and billing_type == "one_time":
            hosting = Decimal(plan.hosting_fee_monthly or 0)
            if hosting > 0 and sub.billing_cycle == BillingCycle.ONE_TIME.value:
                sub.billing_cycle = BillingCycle.MONTHLY.value
                sub.amount_due = hosting
                sub.next_billing_date = (date.fromisoformat(paid_on) + timedelta(days=30)).isoformat()
            elif hosting > 0:
                sub.amount_due = hosting
                sub.next_billing_date = (date.fromisoformat(paid_on) + timedelta(days=30)).isoformat()
            else:
                sub.amount_due = Decimal(0)
                sub.next_billing_date = None
        else:
            cycle_days = 365 if sub.billing_cycle == BillingCycle.YEARLY.value else 30
            sub.next_billing_date = (date.fromisoformat(paid_on) + timedelta(days=cycle_days)).isoformat()
            if plan:
                sub.amount_due = PlatformBillingService._amount_for_plan(plan, sub.billing_cycle)

        await db.flush()
        return PlatformBillingService.subscription_to_summary(sub, company)  # type: ignore[return-value]

    @staticmethod
    async def send_payment_reminder(db: AsyncSession, company_id: int) -> dict:
        company_result = await db.execute(
            select(Company).options(selectinload(Company.subscription)).where(Company.id == company_id)
        )
        company = company_result.scalar_one_or_none()
        if not company:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found")

        sub = company.subscription or await PlatformBillingService.get_subscription(db, company_id)
        if not sub:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subscription not found")

        PlatformBillingService._refresh_payment_status(sub, company)
        now = datetime.utcnow().isoformat(timespec="seconds")
        sub.last_reminder_sent_at = now
        await db.flush()

        summary = PlatformBillingService.subscription_to_summary(sub, company)
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
